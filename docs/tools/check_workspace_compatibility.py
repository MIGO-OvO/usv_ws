"""Read-only whole-vessel contract check and candidate snapshot.

Run from any directory. Does not fetch, checkout, build, flash or deploy.
Snapshots are candidates, never automatic evidence of field acceptance.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 2
SOURCE_HASH_FORMAT = 'sha256-text-lf'
REPOS = {
    'ros': ('src/usv_ros', ['scripts/pump_control_node.py', 'scripts/mavlink_trigger_node.py',
                           'scripts/usv_mavlink_router_bridge.py', 'scripts/web_config_server.py',
                           'scripts/lib/web_access.py', 'launch/usv_bringup.launch']),
    'fcu': ('ardupilot-usv', ['Rover/mode_auto.cpp', 'Rover/GCS_MAVLink_Rover.cpp', 'Rover/sensors.cpp']),
    'qgc': ('WQ-USV-QGroundControl', ['custom/src/USVPayloadFactGroup.cc', 'src/MissionManager/MavCmdInfoRover.json']),
    'detector': ('DetFirmware', ['src/main.cpp', 'src/protocol_packets.h', 'src/control_watchdog.h', 'platformio.ini']),
    'desktop': ('MotorControlApp_Pyside6', ['src/hardware/serial_reader.py', 'src/core/serial_manager.py',
                                          'src/ui/mixins/serial_mixin.py']),
}
FIELDS = ('USV_VOLT USV_ABS PUMP_X PUMP_Y PUMP_Z PUMP_A USV_STAT USV_PKT USV_STEP USV_STOT '
          'USV_SCNT USV_PERR USV_PMOD USV_BSET USV_REF USV_BASE USV_VLD USV_JTMP USV_ETMP '
          'USV_JCPU USV_JMEM USV_EHEAP').split()
RELEASE_ARTIFACTS = ('pixhawk6c_firmware', 'detector_firmware', 'qgc_application', 'ros_bundle', 'desktop_application')


def git(directory, *args):
    return subprocess.check_output(['git', '-c', 'core.safecrlf=false', '-C', str(directory), *args], encoding='utf-8').strip()


def snapshot(root=ROOT):
    result = {'schema_version': SCHEMA_VERSION, 'source_hash_format': SOURCE_HASH_FORMAT,
              'contract': 'usv-safety1', 'field_verified': False, 'repositories': {}}
    for name, (relative, files) in REPOS.items():
        directory = root / relative
        result['repositories'][name] = {
            'path': relative,
            'commit': git(directory, 'rev-parse', 'HEAD'),
            'dirty': bool(git(directory, 'status', '--porcelain')),
            'working_diff_sha256': hashlib.sha256(subprocess.check_output(
                ['git', '-c', 'core.safecrlf=false', '-C', str(directory), 'diff', '--binary', 'HEAD'])).hexdigest(),
            'contract_files': {file: hashlib.sha256((directory / file).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                               for file in files},
        }
    return result


def check_contract(root=ROOT):
    errors = []

    def contains(path, tokens):
        source = (root / path).read_text(encoding='utf-8')
        for token in tokens:
            if token not in source:
                errors.append('%s: missing %s' % (path, token))

    for path in ('src/usv_ros/scripts/usv_mavlink_router_bridge.py', 'ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp',
                 'ardupilot-usv/Rover/sensors.cpp', 'WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc'):
        contains(path, FIELDS)
    for path in ('DetFirmware/src/main.cpp', 'src/usv_ros/scripts/pump_control_node.py',
                 'MotorControlApp_Pyside6/src/core/serial_manager.py',
                 'MotorControlApp_Pyside6/src/ui/mixins/serial_mixin.py'):
        contains(path, ['CAP=WATCHDOG1', 'WATCHDOG:ARM', 'WATCHDOG:KEEPALIVE', 'STOPALL'])
    contains('DetFirmware/src/protocol_packets.h', ['SPECTRO_STATUS_TEST', '0x10'])
    contains('src/usv_ros/scripts/usv_mavlink_router_bridge.py', ['USV_FAIL', '_measurement_timeout'])
    contains('ardupilot-usv/Rover/mode_auto.cpp', ['USV_FAIL', 'link_lost', 'ModeReason::FAILSAFE'])
    contains('src/usv_ros/scripts/pump_control_node.py', ['transaction_only', "action == 'automation_start'"])
    return errors


def compare_snapshot(current, expected, require_release=False):
    errors = []
    if not isinstance(expected, dict):
        return ['manifest must be a JSON object']
    if (expected.get('schema_version') != SCHEMA_VERSION or expected.get('contract') != current['contract']
            or expected.get('source_hash_format') != SOURCE_HASH_FORMAT):
        errors.append('unsupported manifest schema/contract')
    repositories = expected.get('repositories')
    if not isinstance(repositories, dict):
        errors.append('manifest repositories must be an object')
        repositories = {}
    for name, actual in current['repositories'].items():
        if actual != repositories.get(name):
            errors.append('%s differs from the recorded candidate (commit/files/dirty state)' % name)
    if require_release:
        if set(repositories) != set(REPOS):
            errors.append('release requires all five repositories')
        if expected.get('field_verified') is not True:
            errors.append('field acceptance has not been recorded')
        if any(repo['dirty'] for repo in current['repositories'].values()):
            errors.append('release requires clean, committed child repositories')
        if not expected.get('evidence_ref') or not expected.get('artifacts'):
            errors.append('release requires acceptance evidence and firmware/application artifact hashes')
        artifacts = expected.get('artifacts', {})
        for name in RELEASE_ARTIFACTS:
            digest = artifacts.get(name) if isinstance(artifacts, dict) else None
            if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
                errors.append('release artifact hash missing/invalid: ' + name)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', action='store_true', help='print a candidate manifest; never writes files')
    parser.add_argument('--manifest', type=Path, help='compare against a recorded candidate')
    parser.add_argument('--require-release', action='store_true', help='also require clean commits and field evidence')
    args = parser.parse_args()
    if args.require_release and not args.manifest:
        parser.error('--require-release requires --manifest')
    errors = check_contract()
    current = snapshot()
    if args.manifest:
        errors.extend(compare_snapshot(current, json.loads(args.manifest.read_text(encoding='utf-8')), args.require_release))
    if args.snapshot:
        print(json.dumps(current, ensure_ascii=False, indent=2))
    elif not errors:
        print('Source contracts match. This is NOT SITL/bench/field acceptance.')
    for error in errors:
        print('ERROR: ' + error)
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
