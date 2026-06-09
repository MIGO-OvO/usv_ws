# 源码地图

Updated: 2026-06-03

## 根仓库

| 路径 | 职责 |
|---|---|
| `README.md` | 总入口，指向 `docs/current/00_index.md` |
| `AGENTS.md` | Agent 自动发现短入口 |
| `bootstrap_workspace.bat` | Windows 外部源码拉取入口 |
| `docs/current/` | 当前真源文档 |
| `docs/archive/2026-05-20-current-pre-restructure/` | 重构前 current 归档 |

## ROS / usv_ros

| 路径 | 职责 |
|---|---|
| `src/usv_ros/README.md` | ROS 仓库局部真源 |
| `src/usv_ros/launch/usv_bringup.launch` | 默认启动入口、参数定义、节点拓扑 |
| `src/usv_ros/config/usv_params.yaml` | 运行参数基线 |
| `src/usv_ros/scripts/common_env.sh` | ROS 环境、run/log 目录、router 启停公共逻辑 |
| `src/usv_ros/scripts/start_usv_all.sh` | 后台启动 roscore/router/主 launch |
| `src/usv_ros/scripts/stop_usv_all.sh` | 停止主系统/router/roscore |
| `src/usv_ros/scripts/status_usv_all.sh` | 进程、热点、MAVROS、bridge 诊断 |
| `src/usv_ros/scripts/usvctl.sh` | `usvctl/usvon/usvoff/usvdeploy` 分发入口 |
| `src/usv_ros/scripts/usv_mavlink_router_bridge.py` | router TCP、22 字段遥测、命令接收、ACK、`USV_DONE` |
| `src/usv_ros/scripts/mavlink_trigger_node.py` | `31010..31019` 命令解释、采样状态机、航点采样 |
| `src/usv_ros/scripts/pump_control_node.py` | 检测装置串口、自动化、分光、泵控 |
| `src/usv_ros/scripts/system_health_node.py` | Jetson CPU/内存/温度、ROS 节点、ESP32 健康聚合 |
| `src/usv_ros/scripts/web_config_server.py` | Flask API、Socket.IO、配置、日志、诊断 |
| `src/usv_ros/frontend/` | React/Vite Web 前端 |
| `src/usv_ros/static/dist/` | Web 前端构建产物 |
| `src/usv_ros/tests/` | Python 单元/脚本测试 |

## ArduPilot / ardupilot-usv

| 路径 | 职责 |
|---|---|
| `ardupilot-usv/AGENTS.md` | 固件仓库 AI 贡献规则 |
| `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp` | `NAMED_VALUE_FLOAT` 缓存、`USV_DONE` 处理、MAVLink 消息入口 |
| `ardupilot-usv/Rover/sensors.cpp` | `usv_telemetry_send()`，2 Hz 转发 22 字段 |
| `ardupilot-usv/Rover/Rover.h` | `usv_payload` 结构体字段 |
| `ardupilot-usv/Rover/mode_auto.cpp` | mission script/NAV_SCRIPT_TIME 相关逻辑 |
| `ardupilot-usv/libraries/GCS_MAVLink/` | MAVLink 路由、流控、消息基础实现 |
| `ardupilot-usv/wscript`、`./waf` | 固件构建入口 |

## QGroundControl

| 路径 | 职责 |
|---|---|
| `WQ-USV-QGroundControl/custom/src/USVFirmwarePlugin.cc` | USV 固件插件、命令/UI 集成点 |
| `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc` | 载荷 Fact 数据更新 |
| `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.h` | 载荷 Fact 声明 |
| `WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml` | 载荷数据显示面板 |
| `WQ-USV-QGroundControl/custom/res/USVFlyViewCustomLayer.qml` | FlyView 自定义层 |
| `WQ-USV-QGroundControl/Makefile`、`justfile` | QGC 构建辅助入口 |

## 检测装置与上位机

| 路径 | 职责 |
|---|---|
| `DetFirmware/src/main.cpp` | ESP32 主控固件、串口命令、角度/分光/健康二进制帧 |
| `DetFirmware/src/protocol_packets.h` | ESP32 二进制帧格式定义 |
| `DetFirmware/platformio.ini` | ESP32 构建配置，如存在则优先使用 |
| `MotorControlApp_Pyside6/` | Windows 上位机源码与调试入口 |

## 常查映射

| 问题 | 查哪里 |
|---|---|
| QGC 发命令 ROS 不响应 | `USVFirmwarePlugin.cc` -> `usv_mavlink_router_bridge.py` -> `mavlink_trigger_node.py` |
| QGC 不显示载荷 | `usv_mavlink_router_bridge.py` -> `GCS_MAVLink_Rover.cpp` -> `sensors.cpp` -> `USVPayloadFactGroup.cc` |
| Web 不显示系统健康 | `system_health_node.py` -> `/usv/system_health` -> `web_config_server.py` -> `frontend/src/components/system-health-card.tsx` |
| 航点采样不继续 | `mode_auto.cpp` -> `USV_SMPL/USV_DONE` -> `mavlink_trigger_node.py` |
| router/MAVROS 冲突 | `common_env.sh`、`usv_bringup.launch` |
| 分光或健康数据无效 | `pump_control_node.py`、`DetFirmware/src/main.cpp`、Web Socket.IO payload |
| 污染物浓度或热力图异常 | `web_config_server.py` -> `frontend/src/pages/Map.tsx` -> `tests/test_hardware_runtime_sync.py` |

## 污染物地图边界

- 污染物线性模型、校准元数据、点质量、GeoJSON/CSV 导出和 IDW 热力图 surface 的源码归属 `src/usv_ros`。
- 不在 `ardupilot-usv/` 增加污染物浓度计算、历史记录或热力图逻辑；固件只处理 `USV_SMPL/USV_DONE` 和载荷遥测转发。
- 不在 `DetFirmware/` 增加污染物浓度输出；检测装置固件保持分光原始量、电压、valid、基线和健康帧职责。
- 第一阶段不在 `WQ-USV-QGroundControl/` 实现污染物热力图；QGC 只保留任务、命令和遥测展示边界。
