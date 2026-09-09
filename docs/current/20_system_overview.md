# 系统概览

Updated: 2026-06-03

## 五端结构

| 端 | 路径 | 运行平台 | 职责 |
|---|---|---|---|
| 地面站 | `WQ-USV-QGroundControl/` | Windows/Linux/macOS | 定制 QGC、发送 USV 命令、显示载荷遥测 |
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
NAV_SCRIPT_TIME(param1=1)
  -> ardupilot-usv sends NAMED_VALUE_FLOAT USV_SMPL
  -> usv_mavlink_router_bridge.py publishes /usv/mavlink_cmd_rx
  -> mavlink_trigger_node.py starts ROS sampling
  -> trigger_status sampling_started
  -> pump_control_node.py executes detector sequence
  -> sampling_result {source:fcu, sample_id, outcome:succeeded}
  -> usv_mavlink_router_bridge.py sends NAMED_VALUE_FLOAT USV_DONE
  -> ardupilot-usv mode_auto resumes script
```

## 当前能力

`sampling_stopped` 仍用于关闭 Web 记录窗口，但不触发飞控完成通知。失败/取消不发送 `USV_DONE`；明确配置的 SKIP 以 `skipped` 结果放行，不标记为成功。HOLD 请求及飞控自身脚本超时行为须分别验证。

- 航线定点采样只使用 `MAV_CMD_NAV_SCRIPT_TIME`，`param1=1` 表示 USV 定点采样，`param2` 为 1..255 秒超时。
- `COMMAND_LONG 31010..31019`：手动采样、停止、暂停、恢复、校准、走航、基线、分光启停。
- 22 个 `NAMED_VALUE_FLOAT` 载荷字段：17 个采样/分光/泵控字段，加 `USV_JTMP`、`USV_ETMP`、`USV_JCPU`、`USV_JMEM`、`USV_EHEAP` 系统健康字段。
- 固件缓存载荷字段并以 2 Hz 转发到 GCS。
- `system_health_node.py` 聚合 Jetson CPU/内存/温度、ROS 节点和 ESP32 主控健康状态，Web 监控页可查看。
- Web 数据中心跟随 `sampling_started` / `sampling_stopped` 采样生命周期自动建档和停止，不只依赖 Web 端启动任务。
- `mavlink-routerd` 独占飞控串口，MAVROS 与自定义 bridge 分离。
- `usvctl`、`usvon`、`usvoff`、`usvstatus`、`usvdeploy` 管理现场启动更新。
- `web_config_server.py` 提供 Web API、Socket.IO 实时数据、日志与链路诊断。
- 检测装置串口握手使用 `HELLO?` / `DET?`，期望 `DET_ID:USV_DETECTOR*`。

## 运行约束

- Jetson 现场主链路必须先启动 `mavlink-routerd`，再启动 MAVROS 与 bridge。
- `src/usv_ros/launch/usv_bringup.launch` 是默认 ROS 启动入口。
- ArduPilot 固件构建必须在 WSL Ubuntu 或 Linux 环境执行。
- QGC 构建由用户本地 Qt/QGC 环境验证。
- 根仓库不纳入三大外部源码仓库版本历史。
