# 关键目录树
Generated: 2026-04-25T15:46:29+08:00

```text
.
├─ .gitignore
├─ README.md
├─ bootstrap_workspace.bat
├─ WQ-USV-QGroundControl/
│  ├─ README.md
│  ├─ src/
│  └─ custom/
│     ├─ src/
│     │  ├─ USVPlugin.h/cc
│     │  ├─ USVOptions.h/cc
│     │  ├─ USVPayloadFactGroup.h/cc
│     │  ├─ FirmwarePlugin/
│     │  └─ AutoPilotPlugin/
│     └─ res/
│        ├─ USVSamplingDataView.qml        # 采样数据独立页面
│        ├─ USVSamplingDataTokens.js        # 采样数据页面布局常量
│        ├─ USVSelectViewDropdown.qml       # 视图选择菜单（含采样数据入口）
│        ├─ USVPayloadPanel.qml
│        ├─ USVPayloadDetailPanel.qml
│        ├─ USVPayloadSummaryStrip.qml
│        ├─ USVFlyViewCustomLayer.qml
│        ├─ USVInstrumentPanel.qml
│        ├─ USVActionBar.qml
│        ├─ USVChecklist.qml
│        ├─ USVToolBarButton.qml
│        └─ USVPayloadFactGroup.json
├─ ardupilot-usv/
│  ├─ Rover/
│  ├─ Tools/
│  └─ libraries/
├─ DetFirmware/
│  ├─ platformio.ini
│  ├─ include/
│  ├─ lib/
│  ├─ test/
│  └─ src/
│     ├─ main.cpp
│     ├─ i2c_mux.h
│     ├─ ads122c04.h
│     └─ protocol_packets.h
├─ src/
│  └─ usv_ros/
│     ├─ README.md
│     ├─ README.en.md
│     ├─ TESTING.md
│     ├─ config/
│     ├─ launch/
│     │  └─ usv_bringup.launch
│     ├─ scripts/
│     │  ├─ common_env.sh
│     │  ├─ start_ros_master.sh
│     │  ├─ start_usv_system.sh
│     │  ├─ start_usv_minimal.sh
│     │  ├─ start_usv_all.sh
│     │  ├─ stop_usv_all.sh
│     │  ├─ status_usv_all.sh
│     │  ├─ restart_usv_all.sh
│     │  ├─ setup_hotspot.sh
│     │  ├─ stop_hotspot.sh
│     │  ├─ test_web_server.sh
│     │  ├─ pump_control_node.py
│     │  ├─ web_config_server.py
│     │  ├─ mavlink_trigger_node.py
│     │  ├─ mission_coordinator_node.py
│     │  ├─ usv_mavlink_bridge.py
│     │  ├─ usv_mavlink_router_bridge.py
│     │  ├─ named_value_float_probe.py
│     │  ├─ mavlink_topic_tap.py
│     │  ├─ preset_manager.py
│     │  ├─ test_real_usv_serial.py
│     │  └─ lib/
│     ├─ frontend/
│     └─ static/
├─ docs/
│  └─ current/
│     ├─ overview.md
│     ├─ INTERFACE.md
│     ├─ ardupilot_firmware_guide.md
│     ├─ det_firmware_guide.md
│     ├─ injection_pump_reference.md
│     ├─ plan.md
│     ├─ task.md
│     ├─ ppt_progress_report_20260331_20260413.md
│     └─ TREE.md
├─ build/
├─ devel/
└─ .usv_run/
   └─ logs/
```