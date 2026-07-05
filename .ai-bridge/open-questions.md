# Open Questions

Updated: 2026-06-30T11:37:00+08:00

## Q1. Does `web_config_server.py` already contain hidden/unindexed sample API routes?

Status: resolved.

Git Bash inspection confirmed the expected production markers exist in `src/usv_ros/scripts/web_config_server.py`.

Answer:

- `SampleRecordingStorage` is imported and initialized in production.
- `/usv/spectrometer_raw` is subscribed by WebConfigServer in ROS mode.
- `/api/data/mission/<id>/samples`, `/sample/<sample_id>`, `/raw`, and `/manual-result` routes are registered.
- `sampling_started/stopped` opens/closes `SampleWindow`; this is now covered by `test_sample_recording_web_api.py`.

## Q2. What is the actual GPS object shape inside WebConfigServer?

Status: resolved.

WebConfigServer uses `{wgs84:{lat,lng,alt}, received_at}`. `normalize_gps_payload()` now also accepts the flat `{lat,lng,alt,received_at}` test/backfill shape, with explicit tests for both.

## Q3. How does `mavlink_trigger_node.py` expose sampling context to WebConfigServer?

Status: partially resolved.

WebConfigServer currently derives `waypoint_seq` from `current_waypoint_seq` and `mavlink_sample_id` from `latest_automation_status.sample_id`. The real end-to-end FCU context path still needs a field test or replay fixture.

## Q4. Should existing mission JSON files be migrated?

Status: later.

Older mission files may lack `sample_windows`. Data page already has an empty-state path. Migration is optional for P0; P1 may add a lazy migration that initializes `sample_windows_schema_version: 1` without modifying data points.

## Q5. What is the expected sampling-window frequency/size for survey mode?

Status: later.

Need domain decision for 走航: fixed time interval, fixed distance interval, valid-frame count, or hybrid gate. This affects raw file size, map density, and manual/automatic concentration semantics.
