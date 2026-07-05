# Decisions

Updated: 2026-06-30T11:37:00+08:00

## D1. Keep sample recording in ROS/Web, not firmware/QGC

Decision: Continue keeping pollutant concentration records, raw spectral sample windows, GeoJSON/CSV/IDW export, and manual concentration entry in `src/usv_ros`.

Reason: Existing project boundary says ArduPilot/DetFirmware/QGC should not own concentration/history/heatmap logic. The next step does not require MAVLink command id or detector serial protocol changes.

## D2. Treat current sample_recording library as usable foundation, not complete feature

Decision: Reuse `scripts/lib/sample_recording/` as the core storage/model/summary layer.

Reason: `models.py`, `summary.py`, and `storage.py` already provide SampleWindow schema, raw JSONL persistence, summary statistics, manual result normalization, and path traversal protection.

Consequence: The next implementation should not rewrite these from scratch. It should integrate them into `web_config_server.py` and add missing tests.

## D3. Production WebConfigServer integration is verified

Decision: Treat the WebConfigServer sample-window P0 integration as present and covered by focused tests.

Reason: Full-file Git Bash inspection found `SampleRecordingStorage`, `sample_storage`, `/samples`, `manual-result`, `/usv/spectrometer_raw`, and lifecycle callback integration in production `web_config_server.py`. `test_sample_recording_web_api.py` now verifies default production initialization and drives `sampling_started -> raw frame x3 -> sampling_stopped`.

## D4. Normalize GPS payload contract before relying on GPS association

Decision: GPS normalization accepts the actual Web server payload shape and the flat legacy/test shape.

Reason: WebConfigServer uses `{wgs84:{lat,lng,alt}, received_at}`, while tests/backfill data may use `{lat,lng,alt,received_at}`. Both are now explicitly asserted.

## D5. Survey/走航 should stay under SampleWindow, not waypoint-only records

Decision: Represent route sampling, waypoint sampling, manual sampling, lab sampling, and survey/走航 as `SampleWindow` variants.

Reason: The same raw spectral slicing and manual/automatic processing pipeline is needed across all acquisition modes; survey windows should add `survey_index`, distance/time interval, and GPS track metadata rather than pretending to be waypoints.
