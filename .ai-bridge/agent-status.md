# Agent Status

Updated: 2026-07-05T21:15:00+08:00

## Current status

QGC P0 optimization from `.ai-bridge/qgc-optimization-plan.md` is implemented in `WQ-USV-QGroundControl/`.

Completed:

- Unified `USV_STAT=3` wording as task/sample failure, not hardware fault, including the main panel, top banner, summary strip, Fact metadata, and sampling data tokens.
- Removed manual payload commands `31010..31019` from Rover Plan mission metadata; `42702 MAV_CMD_NAV_SCRIPT_TIME` remains the only USV Plan command.
- Kept manual commands in `custom/res/actions/usv_actions.json`.
- Aligned `USVActionBar.qml` start and stop-action gates with `USVPayloadPanel.qml` for link, valid spectrometer signal, baseline, and status.
- Updated `custom/tests/test_usv_qgc_contract.py` to cover status wording in summary/data surfaces, Plan/Action boundary, and action-bar gates.
- Promoted `USVFlyViewLayout.js` to the single QGC status-code text source; payload panel, summary strip, and sampling data view now consume `USVLayout.statusText()`.
- Added a static cross-end named-value contract test covering the 22 payload fields across ROS bridge, ArduRover cache/forwarding, and QGC FactGroup metadata.
- Scoped PX4 documentation to UI/basic Rover compatibility; complete USV sampling mission closure remains ArduRover-custom-firmware based.
- Added a compact task-prep block to the payload panel using existing vehicle/link/signal/baseline/status gates only.
- Fixed the task-prep headline readiness so "可执行" now requires vehicle, payload link, valid spectrometer signal, baseline, and point-sample status gate.

Verification:

- `python custom/tests/test_usv_qgc_contract.py`: passed, 16 tests.
- Readiness regression test covers `_readyForPointSample` and rejects `_canStartPointSample ? qsTr("可执行")`.
- `python -m json.tool src/MissionManager/MavCmdInfoRover.json`, `custom/res/USVPayloadFactGroup.json`, `custom/res/actions/usv_actions.json`: passed.
- `rg -n "载荷故障，请检查采样模块" custom src/MissionManager`: no matches.
- `rg -n "StatusFault.*故障|case StatusFault: return \"故障\"" custom src/MissionManager`: no matches.
- `rg -n "function statusText\(|SDTokens\.Status|SDTokens\.statusText|载荷故障，请检查采样模块|StatusFault.*故障|case StatusFault: return \"故障\"" custom/res src/MissionManager`: only `custom/res/USVFlyViewLayout.js` defines `statusText()`.
- Runtime visual QA was not run because no local QGC Qt runtime/render surface is available in this session.

Skipped:

- P1 separate status-code JS file. Existing `USVFlyViewLayout.js` now covers the single-source need with less code.
- P2 task-upload readiness. No existing QGC Fact or reliable local source exists for uploaded mission state, so the prep block does not invent one.

The previous CodexPro review was limited by a 180 KB read cap on `src/usv_ros/scripts/web_config_server.py` and incorrectly treated production WebConfigServer integration as unconfirmed. This follow-up used Git Bash to inspect the full file and verified the production markers are present.

Confirmed in `src/usv_ros/scripts/web_config_server.py`:

- `SampleRecordingStorage` is imported and initialized as `self.sample_storage`.
- `self.current_sample_window` is initialized.
- `/usv/spectrometer_raw` is subscribed in ROS mode.
- `sampling_started` starts data recording and opens a sample window.
- `sampling_stopped` / `survey_stopped` close the active sample window and save the mission.
- Sample APIs are registered:
  - `GET /api/data/mission/<mission_id>/samples`
  - `GET /api/data/mission/<mission_id>/sample/<sample_id>`
  - `GET /api/data/mission/<mission_id>/sample/<sample_id>/raw`
  - `POST /api/data/mission/<mission_id>/sample/<sample_id>/manual-result`

## Follow-up changes completed

- `normalize_gps_payload()` now accepts both Web position shape `{wgs84:{lat,lng,alt}, received_at}` and flat `{lat,lng,alt,received_at}`.
- Storage tests now assert `gps_start`, `gps_end`, and `gps_latest` for both shapes.
- Web API test now proves the production server initializes `sample_storage` and drives the real callback chain:
  `sampling_started -> raw frame x3 -> sampling_stopped`.
- The lifecycle test verifies mission JSON contains one closed sample window, raw JSONL has three lines, sample APIs read it back, and manual concentration persists.
- Added a missing-sample route error-path assertion.
- `SampleRecordingStorage.close_window()` now rebuilds spectrometer summary from raw JSONL when the in-memory builder is missing; this is storage-level recovery, not full Web process restart recovery.
- Added a restart-regression test for closing an existing window with a fresh storage instance.

## Verification

- `python -m py_compile scripts/web_config_server.py scripts/lib/sample_recording/*.py`: passed.
- `python -m unittest tests.test_sample_recording_storage tests.test_sample_recording_web_api`: passed, 6 tests.
- `python -m unittest discover -s tests -p 'test_*.py'`: failed only on existing map tests:
  - `test_web_map_config_serves_offline_tile_proxy_without_amap_key`: provider is `leaflet-google-raster`, expected `leaflet-amap-raster`.
  - `test_frontend_declares_runnable_map_smoke_script`: `smoke-map.mjs` missing `MAP_TILE_NATIVE_MAX_ZOOM = 18`.

## Next priority

P0/P0.5 for sample-window production integration is now covered. Remaining sample-window work is P1:

1. Strengthen waypoint/GPS association with waypoint cache, distance-to-waypoint, and quality flags.
2. Recover the latest open sample window in `WebConfigServer` after process restart or on `sampling_stopped`.
3. Define survey/走航 window slicing policy.
Protocol boundary remains unchanged: no ArduPilot, DetFirmware, QGroundControl, MAVLink command id, or ESP32 serial packet changes are needed.
