import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_workspace_compatibility import (
    compare_snapshot, snapshot, REPOS, RELEASE_ARTIFACTS, SCHEMA_VERSION, SOURCE_HASH_FORMAT,
)


class ManifestTests(unittest.TestCase):
    def test_contract_hashes_are_independent_of_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            roots = [Path(temporary) / name for name in ('windows', 'linux')]
            for root, data in zip(roots, (b'line1\r\nline2\r\n', b'line1\nline2\n')):
                for relative, files in REPOS.values():
                    for name in files:
                        path = root / relative / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
            with patch('check_workspace_compatibility.git', side_effect=lambda directory, *args: 'a' * 40 if args[0] == 'rev-parse' else ''), \
                    patch('check_workspace_compatibility.subprocess.check_output', return_value=b''):
                self.assertEqual(snapshot(roots[0]), snapshot(roots[1]))

    def test_candidate_is_not_a_release(self):
        snapshot = {'schema_version': SCHEMA_VERSION, 'source_hash_format': SOURCE_HASH_FORMAT,
                    'contract': 'usv-safety1', 'field_verified': False,
                    'repositories': {'ros': {'commit': 'abc', 'dirty': True, 'contract_files': {'a': 'hash'}}}}
        self.assertEqual(compare_snapshot(snapshot, snapshot), [])
        self.assertTrue(compare_snapshot(snapshot, snapshot, require_release=True))

    def test_mixed_commit_and_modified_sources_are_rejected(self):
        snapshot = {'schema_version': SCHEMA_VERSION, 'source_hash_format': SOURCE_HASH_FORMAT,
                    'contract': 'usv-safety1', 'repositories': {
            'ros': {'commit': 'abc', 'dirty': False, 'contract_files': {'a': 'hash'}}}}
        for field, value in [('commit', 'def'), ('contract_files', {'a': 'changed'})]:
            other = copy.deepcopy(snapshot)
            other['repositories']['ros'][field] = value
            self.assertTrue(compare_snapshot(snapshot, other))

    def test_sitl_binary_is_not_a_hardware_release_artifact(self):
        snapshot = {'schema_version': SCHEMA_VERSION, 'source_hash_format': SOURCE_HASH_FORMAT,
                    'contract': 'usv-safety1', 'field_verified': True,
                    'evidence_ref': 'bench-evidence',
                    'repositories': {name: {'dirty': False} for name in REPOS},
                    'artifacts': {'fcu_sitl': 'a' * 64}}
        self.assertTrue(compare_snapshot(snapshot, snapshot, require_release=True))
        snapshot['artifacts'] = {name: 'a' * 64 for name in RELEASE_ARTIFACTS}
        self.assertEqual(compare_snapshot(snapshot, snapshot, require_release=True), [])

    def test_malformed_manifest_fails_closed(self):
        current = {'contract': 'usv-safety1', 'repositories': {}}
        for expected in (None, [], {'repositories': []}, {'schema_version': 1}):
            self.assertTrue(compare_snapshot(current, expected, require_release=True))


if __name__ == '__main__':
    unittest.main()
