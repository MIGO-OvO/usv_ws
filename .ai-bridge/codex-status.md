# Codex Status

Updated: 2026-07-05T21:15:00+08:00
Workspace: `D:\usv_ws`
Scope: sample-window recording, WebConfigServer integration, manual concentration entry, and follow-up handoff state.

## Current Conclusion

The earlier "WebConfigServer production integration unconfirmed/suspect" conclusion was a tool-read limitation, not the actual source state. Treat it as superseded.

Confirmed in `src/usv_ros/scripts/web_config_server.py`:

- `SampleRecordingStorage` is imported and initialized as `self.sample_storage`.
- `self.current_sample_window` is initialized.
- ROS mode subscribes `/usv/spectrometer_raw`.
- `sampling_started` opens a sample window.
- `sampling_stopped` / `survey_stopped` close the active sample window and save mission data.
- APIs exist for sample list, sample detail, raw frames, and manual-result update.

Confirmed in `src/usv_ros/scripts/lib/sample_recording/`:

- SampleWindow model, raw-frame normalization, GPS normalization, manual-result normalization.
- Raw JSONL storage under `missions_dir/raw/<mission_id>/<sample_id>.jsonl`.
- Summary statistics for frame counts, valid counts, voltage, absorbance, raw_code, and quality flags.
- Path traversal protection on raw reads.

Confirmed in frontend/docs/tests:

- `frontend/src/pages/Data.tsx` uses mission -> sample window -> detail/raw chart/manual result.
- README/API docs mention sample-window APIs.
- Storage tests cover lifecycle, path traversal, GPS payload shapes, empty windows, and builder-missing summary rebuild.
- Web API tests cover production server initialization and `sampling_started -> raw frame x3 -> sampling_stopped`.

## Completed Follow-Ups

### 2026-06-30 P0/P0.5

- Verified production WebConfigServer integration with full-file inspection.
- Fixed GPS normalization to accept both `{wgs84:{lat,lng,alt}, received_at}` and flat `{lat,lng,alt,received_at}`.
- Added explicit GPS assertions for both payload shapes.
- Reworked Web API test so it does not rely only on manual storage injection.
- Added missing-sample API error-path assertion.

### 2026-07-05 P1 Storage Resilience

- Fixed `SampleRecordingStorage.close_window()` so, when the in-memory builder is absent, it rebuilds spectrometer summary from the window raw JSONL file.
- Added a regression test for the storage-level restart shape: old storage writes frames, fresh storage closes the same window object.

Important boundary: this is not full Web process restart recovery. After a real Web process restart, `WebConfigServer.current_sample_window` starts as `None`; a later P1 should recover the latest open window from mission JSON on startup or when `sampling_stopped` arrives.

## Current Module Status

| Module | Status | Notes |
|---|---|---|
| Spectrometer raw source | Present | `pump_control_node.py` publishes raw/voltage/absorbance topics. |
| SampleWindow model/storage | Present | Schema, raw JSONL, summary, manual result, path safety. |
| WebConfigServer production routes | Verified present | Earlier "unconfirmed" result is superseded. |
| ROS sample lifecycle windowing | Verified present | Covered by Web API lifecycle test. |
| Data page sample UI | Present | Mission/sample/detail/raw/manual-result flow. |
| GPS payload compatibility | Fixed | Nested and flat shapes covered. |
| Storage builder-missing summary rebuild | Fixed | Raw JSONL replay covered by storage test. |
| Full Web process restart recovery | Not done | Needs open-window recovery at WebConfigServer layer. |
| Waypoint/GPS strong association | Not done | Needs waypoint cache, distance, quality flags. |
| Survey window policy | Not done | Needs time/distance/valid-frame gate decision. |
| Droplet microfluidic processing | Not done | `processing` field reserved; algorithm not connected. |

## Verification

- `python -m py_compile scripts/web_config_server.py scripts/lib/sample_recording/*.py`: passed on 2026-06-30.
- `python -m unittest tests.test_sample_recording_storage tests.test_sample_recording_web_api`: passed, 6 tests on 2026-06-30.
- `python -m py_compile scripts/lib/sample_recording/__init__.py scripts/lib/sample_recording/models.py scripts/lib/sample_recording/summary.py scripts/lib/sample_recording/storage.py`: passed on 2026-07-05.
- `python -m unittest tests.test_sample_recording_storage tests.test_sample_recording_web_api`: passed, 7 tests on 2026-07-05.
- `npm run build`: reported passed by review on 2026-07-05; generated `index-C23bzq72.js` and `index-Cutzexsa.css`, with only normal Browserslist/chunk warnings.

Full ROS unittest still has 2 unrelated map failures:

- `test_web_map_config_serves_offline_tile_proxy_without_amap_key`: provider is `leaflet-google-raster`, expected `leaflet-amap-raster`.
- `test_frontend_declares_runnable_map_smoke_script`: `smoke-map.mjs` missing `MAP_TILE_NATIVE_MAX_ZOOM = 18`.

## Next Work

1. Web-level open-window recovery after process restart.
2. Waypoint/GPS strong association: waypoint cache, distance-to-waypoint, position quality.
3. Survey/走航 window slicing policy.
4. Later: droplet processing endpoint and algorithm integration.

Protocol boundary remains unchanged: no ArduPilot, DetFirmware, QGroundControl, MAVLink command id, or ESP32 serial packet changes are required for these ROS/Web sample-window items.
