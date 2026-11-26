# 系统概览

Updated: 2026-11-23

## 五端结构

| 端 | 路径 | 运行平台 | 职责 |
|---|---|---|---|
| 地面站 | `WQ-USV-QGroundControl/` | Windows / Android（交付验收） | 定制 QGC、发送 USV 命令、显示载荷遥测 |
| 船载 ROS | `src/usv_ros/` | Jetson Nano / Ubuntu 20.04 / ROS Noetic | 泵控、Web、MAVROS、MAVLink bridge、任务编排 |
| 飞控固件 | `ardupilot-usv/` | Pixhawk 6C | ArduRover、任务执行、载荷字段缓存与转发 |
| 检测装置固件 | `DetFirmware/` | ESP32 | X/Y/Z/A 步进泵、PWM 进样泵、角度、ADS 分光采集 |
| Windows 上位机 | `MotorControlApp_Pyside6/` | Windows / PySide6 | 检测装置手动调试、PID 调参、数据导出 |

## 主数据链路

```text
QGroundControl custom UI
  | Plan: MAV_CMD_NAV_SCRIPT_TIME(param1=1)
  | Manual: COMMAND_LONG 31010..31019
  | NAMED_VALUE_FLOAT payload display
  v
Pixhawk 6C / ardupilot-usv
  | TELEM2 MAVLink2
  v
mavlink-routerd on Jetson
  |-- UDP 127.0.0.1:14550 -> MAVROS
  |-- TCP 127.0.0.1:5760 -> usv_mavlink_router_bridge.py
  v
ROS Noetic / usv_ros
  |-- mavlink_trigger_node.py
  |-- web_config_server.py
  |-- system_health_node.py
  |-- pump_control_node.py
  v
ESP32 detector firmware
```

## 采样任务闭环

```text
采样航点 -> NAV_SCRIPT_TIME(param1=1) -> AUTO 内驻留
  -> 31021 OFFER / READY / START
  -> bridge -> /usv/fcu_sampling -> trigger -> pump
  -> /usv/sampling_result -> bridge -> 31021 终态
  -> 飞控按结果继续航线、LOITER 或 HOLD
```

## 当前能力

飞控负责到点、稳船和任务推进。ROS 负责载荷准入、清理和记录。飞控收到同一采样身份的 DONE 或 SKIP 后继续航线，Web 依据同一 attempt 的最终结果结束记录。ESP32 `WATCHDOG1` 在主机失联时停止设备输出。

- 航线定点采样使用 `MAV_CMD_NAV_SCRIPT_TIME(param1=1)`。飞控在驻留期间等待本次采样终态，旧航线的时限字段供旧固件使用。
- `COMMAND_LONG 31010..31019`：手动采样、停止、暂停、恢复、校准、走航、基线、分光启停。
- 26 个 `NAMED_VALUE_FLOAT` 载荷字段：原 22 项加 `USV_LOOP/LTOT`、`USV_ADS/PROTO`，字段清单以 `Rover/USVPayload.h` 为准。
- 固件缓存载荷字段并以 2 Hz 转发到 GCS。
- `system_health_node.py` 聚合 Jetson CPU/内存/温度、ROS 节点和 ESP32 主控健康状态，Web 监控页可查看。
- Web 数据中心跟随 `sampling_started` 建档；trigger 所有任务按匹配 attempt 的最终 `/usv/sampling_result` 关窗，泵步骤结束不代表清理成功。
- `mavlink-routerd` 独占飞控串口，MAVROS 与自定义 bridge 分离。
- `usvctl`、`usvon`、`usvoff`、`usvstatus`、`usvdeploy` 管理现场启动更新。
- `web_config_server.py` 提供 Web API、Socket.IO 实时数据、日志与链路诊断。
- 检测装置串口握手使用 `HELLO?` / `DET?`，期望 `DET_ID:USV_DETECTOR*`。

## 运行约束

- Jetson 现场主链路必须先启动 `mavlink-routerd`，再启动 MAVROS 与 bridge。
- `src/usv_ros/launch/usv_bringup.launch` 是默认 ROS 启动入口。
- ArduPilot 固件构建必须在 WSL Ubuntu 或 Linux 环境执行。
- QGC 构建见[构建与运行](50_build_update_runbook.md#qgroundcontrol)，目标产物见[验证矩阵](70_verification.md#qgc-构建与-ci-验收)。

## 常用源码入口

| 问题 | 源码 |
|---|---|
| 航点到达、驻留与任务推进 | `ardupilot-usv/Rover/mode_auto.cpp`、`ardupilot-usv/Rover/usv_sampling.cpp` |
| MAVLink 接收、缓存、转发 | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`ardupilot-usv/Rover/USVPayload.h`、`ardupilot-usv/Rover/sensors.cpp` |
| ROS 启动、router 与参数 | `src/usv_ros/launch/usv_bringup.launch`、`src/usv_ros/config/usv_params.yaml`、`src/usv_ros/scripts/common_env.sh` |
| 采样或停止未收尾 | `src/usv_ros/scripts/usv_mavlink_router_bridge.py`、`src/usv_ros/scripts/mavlink_trigger_node.py`、`src/usv_ros/scripts/pump_control_node.py`。关联请求和采样握手定义在 `src/usv_ros/scripts/lib/payload_protocol.py` 与 `src/usv_ros/scripts/lib/fcu_sampling.py` |
| QGC 命令、载荷 Fact 或面板 | `WQ-USV-QGroundControl/custom/src/FirmwarePlugin/USVFirmwarePlugin.cc`、`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`、`WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml` |
| Web 接口、数据记录与健康状态 | `src/usv_ros/scripts/web_config_server.py`、`src/usv_ros/scripts/lib/sample_recording/`、`src/usv_ros/scripts/system_health_node.py` |
| 地图、实验航线、液滴和科研图件 | `src/usv_ros/scripts/lib/lab_sim/`、`src/usv_ros/frontend/src/pages/Map.tsx`、`src/usv_ros/frontend/src/pages/Lab.tsx` |
| 检测装置串口、看门狗和分光帧 | `DetFirmware/src/main.cpp`、`DetFirmware/src/control_watchdog.h`、`DetFirmware/src/protocol_packets.h`。Windows 对端在 `MotorControlApp_Pyside6/src/core/serial_manager.py` 和 `MotorControlApp_Pyside6/src/hardware/serial_reader.py` |

污染物浓度、原始分光采样窗口、人工浓度录入、GeoJSON/CSV 和 IDW 热力图由 ROS/Web 维护。原始分光采样窗口由 `sample_recording` 管理。各端的测试入口见[验证矩阵](70_verification.md)。
