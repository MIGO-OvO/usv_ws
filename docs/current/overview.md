# 项目概览
Updated: 2026-04-26T19:40:51+08:00

## 1. 范围
- 地面端：`WQ-USV-QGroundControl/`
- 船载端：`src/usv_ros/`
- 飞控端：`ardupilot-usv/`
- 检测装置主控固件：`DetFirmware/`
- Windows 上位机：`MotorControlApp_Pyside6/`
- 当前文档目录：`docs/current/`

## 2. 当前系统结构
- QGC 自定义层发送 `COMMAND_LONG` 指令并显示载荷遥测。
- ROS Noetic 运行泵控、分光采集、Web 服务、MAVLink 指令接收与载荷遥测发送。
- `DetFirmware/` 为检测装置 ESP32 主控固件，负责四路步进泵、进样泵 PWM、MT6701 角度、ADS122C04 分光采集与串口协议。
- `MotorControlApp_Pyside6/` 为 Windows 端 PySide6 上位机，提供电机手动/自动控制、PID 调参、分光采集、数据导出等 GUI 功能。
- ArduRover 固件接收来自伴随计算机的 `NAMED_VALUE_FLOAT`，缓存后以 2Hz 周期性转发到 GCS（直转发已被 MAVLink_routing 阻断）。
- `mavlink-routerd` 独占 `/dev/ttyTHS1`，为 MAVROS（UDP:14550）与载荷遥测桥（TCP:5760）提供物理隔离的 MAVLink 路由。

## 3. 当前数据链路
### 3.1 QGC -> ROS（下行指令）
`QGC -> 数传电台 -> 飞控 -> mavlink-routerd -> usv_mavlink_router_bridge.py -> /usv/mavlink_cmd_rx -> mavlink_trigger_node.py`

### 3.2 ROS -> QGC（上行遥测 — 飞控中继模式）
```
bridge(sysid=1/compid=191) -[2Hz×13字段]-> mavlink-routerd -[UART]-> 飞控
  飞控: handle_message 缓存到 usv_payload（MAVLink_routing 阻断直转发）
  飞控: usv_telemetry_send() 以 2Hz 重发 gcs().send_named_float()
  飞控 -[TELEM1]-> 数传电台 -> QGC USVPayloadFactGroup
```

### 3.3 端点隔离
| 端点 | 协议 | 用途 |
|---|---|---|
| MAVROS | UDP 127.0.0.1:14550 | 参数下载、状态监控、set_mode、COMMAND_ACK |
| bridge | TCP 127.0.0.1:5760 | NAMED_VALUE_FLOAT 遥测、COMMAND_LONG 接收 |
| UART | /dev/ttyTHS1:921600 | 飞控物理链路 |

## 4. 当前已实现能力
- `mavlink_trigger_node.py` 处理 `31010~31014`，并回传 `COMMAND_ACK`。
- `mavlink_trigger_node.py` 将 `31014` 转换为 `CALXYZA\r\n` 并发布到 `/usv/pump_command`。
- `usv_mavlink_router_bridge.py` 通过 `pymavlink` 向 `mavlink-routerd` 发送 13 个 `NAMED_VALUE_FLOAT` 字段：`USV_VOLT`、`USV_ABS`、`PUMP_X/Y/Z/A`、`USV_STAT`、`USV_PKT`、`USV_STEP`、`USV_STOT`、`USV_SCNT`、`USV_PERR`、`USV_PMOD`（线程安全队列模式）。
- `start_usv_all.sh`、`stop_usv_all.sh`、`status_usv_all.sh`（含 ROS 节点级检查 + MAVROS 连通检查 + bridge 诊断摘要）。
- `bootstrap_workspace.bat` 为 Windows 提供唯一的外部仓库拉取入口，固定拉取 `ardupilot-usv`、`WQ-USV-QGroundControl`、`src/usv_ros`。
- 根 `.gitignore` 忽略三方源码目录与本地构建产物，保证总管理仓库只提交文档与入口文件。
- 根 `README.md` 汇总 clone、bootstrap、三端构建入口与 Git 管理策略。
- `USVPayloadFactGroup` 解析 `NAMED_VALUE_FLOAT`、`DEBUG_VECT`、`DEBUG`，维护 `linkActive`（5s 超时）、`packetCount`、诊断计数。
- ArduRover 固件 `GCS_MAVLink_Rover.cpp` 缓存 `NAMED_VALUE_FLOAT`；`sensors.cpp` 以 2Hz 受控重发；`MAVLink_routing.cpp` 阻断直转发。
- `web_config_server.py` 提供硬件配置 API、任务控制 API、进样泵 API、Socket.IO 状态推送。
- `pump_control_node.py` 提供四路步进泵、进样泵、自动化步骤执行、分光采集。
- `DetFirmware/src/main.cpp` 支持 `HELLO?`/`DET?` 身份握手，返回 `DET_ID:USV_DETECTOR,...`；普通命令处理后返回 `CMD_OK`/`CMD_ERR:UNKNOWN`。
- Web `/api/hardware/test-pump-port` 已从“串口可打开”升级为“串口打开 + 检测装置握手识别”。
- `MotorControlApp_Pyside6` 串口连接（`serial_mixin.py` 和 `serial_manager.py`）已统一执行 `HELLO?` 握手，非检测装置不启动读取线程。

- `mavlink_trigger_node.py` 已完成阶段一第一轮闭环增强：
  - 支持 `hold_settle_time` / `stable_check_timeout` / `stable_speed_threshold` / `stable_yaw_rate_threshold`
  - 支持 waypoint 级 `loop_count` / `retry_count` / `hold_before_sampling_s` / `on_fail`
  - 支持航点去重状态机与 `/usv/mission_status` 任务阶段发布
- `web_config_server.py` 新增航点采样配置 CRUD API（`/api/waypoint-sampling`）和任务配置导入导出（`/api/mission-config/export|import`）。
- 前端新增 `WaypointSamplingCard` 航点采样编辑器和任务配置导入/导出入口。
- 前端启动任务时自动携带最新 `waypoint_sampling` 下发。
- QGC `USVPayloadPanel.qml` 命令发送 `showError=true`，命令超时/拒绝时弹出 toast。
- QGC `USVSamplingDataView.qml` 采样数据独立顶层页面（与航行/规划/配置同级），包含实时电压/吸光度曲线、采样任务概览、泵组状态与PID监控、统计分析。
- `usv_mavlink_router_bridge.py` 新增 `USV_STEP`/`USV_STOT`/`USV_SCNT`/`USV_PERR`/`USV_PMOD` 遥测字段，支持采样步骤进度、样本计数、PID状态上报。
- ArduRover `usv_payload` 已缓存并以 2Hz 中继上述 13 个载荷遥测字段。
- `pump_control_node.py` 自动化步骤等待顺序：电机/PID 完成 -> 进样泵 `duration_ms` -> ADS 采集中时等待 1 条新的 valid 分光样本。

## 5. 当前运行约束
- `mavlink-routerd` 为必需依赖；未包含自动安装逻辑。
- MAVROS 默认连接 `udp://127.0.0.1:14550@`；bridge 默认连接 `tcp:127.0.0.1:5760`。
- `mission_coordinator_node.py` 未包含在默认 launch 主链路。
- 阶段一稳定判定当前为 ROS 侧轻量实现，依赖 `/mavros/local_position/velocity_local` 与 `/mavros/imu/data`；未引入位置漂移闭环。
- 航点级采样配置当前由 `sampling_config.json` / Web `waypoint_sampling` 驱动，尚未进入 QGC Plan 原生任务模型。
- 根仓库只保留一个 Windows `.bat` 引导脚本；不再保留 `.sh`/`.ps1` bootstrap 入口。
- `.bat` 已写死 3 个外部源码仓库 URL；ROS/QGC/ArduPilot 仍按各自仓库原生构建入口执行。
- `DetFirmware` 构建依赖 PlatformIO；当前 Windows 环境未安装 `pio`，只能完成源码逻辑与 Python 语法验证，实机烧录需用户执行。

## 6. 稳定版本标签
| 仓库 | 标签 | commit | 说明 |
|---|---|---|---|
| `ardupilot-usv` | `v0.2.0-stable` | `56741bb0fa` | 含 NAMED_VALUE_FLOAT 路由阻断 + 2Hz 重发 |
| `src/usv_ros` | `v0.2.0-stable` | `63ae83ec` | 含线程安全队列 + MAVROS UDP 隔离 + 遥测解耦 |
| `WQ-USV-QGroundControl` | `v0.2.0-stable` | `af6c56478` | 含 showError=true + UI 优化 |

回滚命令：
```bash
cd ~/usv_ws/src/usv_ros && git checkout v0.2.0-stable
cd ~/usv_ws/ardupilot-usv && git checkout v0.2.0-stable
cd ~/usv_ws/WQ-USV-QGroundControl && git checkout v0.2.0-stable
```

## 7. 文档入口
- 根入口：`README.md`
- 运维入口：`src/usv_ros/README.md`
- 测试入口：`src/usv_ros/TESTING.md`
- 接口速查：`docs/current/INTERFACE.md`
- 固件说明：`docs/current/ardupilot_firmware_guide.md`
- 检测装置固件说明：`docs/current/det_firmware_guide.md`
- 技术计划：`docs/current/plan.md`
- 任务记录：`docs/current/task.md`
- 后续规划：`docs/current/roadmap.md`
