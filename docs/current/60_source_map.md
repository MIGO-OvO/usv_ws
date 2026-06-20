# 源码地图

Updated: 2026-06-19

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
| `src/usv_ros/scripts/mavlink_trigger_node.py` | `31010..31019` 命令解释、采样状态机、航点采样、实验液滴事件发布 |
| `src/usv_ros/scripts/pump_control_node.py` | 检测装置串口、自动化、分光、泵控 |
| `src/usv_ros/scripts/lab_sim_node.py` | 实验虚拟船位仿真节点，`/usv/lab_sim/*` 话题 |
| `src/usv_ros/scripts/system_health_node.py` | Jetson CPU/内存/温度、ROS 节点、ESP32 健康聚合 |
| `src/usv_ros/scripts/web_config_server.py` | Flask API、Socket.IO、配置、日志、诊断、Lab/坐标/surface |
| `src/usv_ros/frontend/` | React/Vite Web 前端 |
| `src/usv_ros/static/dist/` | Web 前端构建产物 |
| `src/usv_ros/tests/` | Python 单元/脚本测试 |

## 实验仿真库 lab_sim

源码目录：`src/usv_ros/scripts/lib/lab_sim/`。纯计算模块，单一职责，按概念命名。

| 路径 | 职责 |
|---|---|
| `coordinates.py` | CRS 转换（WGS-84 / GCJ-02 迭代反算）、ENU 投影、haversine 距离、坐标解析与边界 |
| `models.py` | schema v2 数据类聚合入口，重导出 config/events/primitives/parsing |
| `model_primitives.py` | `CoordinatePairRef`、`GeoPoint` 等坐标原语 |
| `model_config.py` | `LabConfigV2`、`WaterSnapshot`、`RouteSnapshot` 等配置数据类 |
| `model_events.py` | `SamplingEvent`、`DropletResult` 事件数据类 |
| `model_parsing.py` | schema v2 解析、校验与 typed error |
| `calibration.py` | Beer-Lambert 与线性工作曲线互逆校准（`A=k*C+b`） |
| `droplet_signal.py` | 有界合成液滴信号生成（`generate_droplets`，截断 `3..64`） |
| `aggregation.py` | 液滴聚合为单条事件均值（`aggregate_droplets`） |
| `pollution_field.py` | 确定性 seeded 局部 ENU 污染浓度场（`PollutionField`） |
| `route_geometry.py` | 覆盖航线几何基元（条带、连接节点、路段拼接） |
| `route_planner.py` | 弓字形覆盖航线规划（`plan_coverage_route`） |
| `sampling_service.py` | 组装一次 `SamplingEvent`（坐标、校准、液滴、污染场、上下文） |
| `vessel_model.py` | WGS-84 虚拟船运动模型（`VesselSimulator`） |
| `survey_window.py` | 走航采样距离/时间触发窗口判定 |
| `surface.py` | 版本化水域快照 ENU 网格科研 surface，polygon 外严格 mask |
| `figure_export.py` | 无头 matplotlib 导出 300 DPI PNG/TIFF、SVG/PDF 与 metadata（`export_surface_figure`） |

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
| 实验坐标 WGS/GCJ 不一致 | `lib/lab_sim/coordinates.py` -> `web_config_server.py` -> `frontend/src/lib/lab-coordinate-adapter.ts`、`frontend/src/pages/Map.tsx` |
| 实验液滴事件/采样计数 | `mavlink_trigger_node.py` -> `lib/lab_sim/sampling_service.py` -> `tests/test_lab_sampling_event_storage.py` |
| auto-scan 航线 | `web_config_server.py:build_auto_scan_route_response` -> `lib/lab_sim/route_planner.py` -> `tests/test_lab_auto_scan_api.py` |
| 科研 surface/图件 | `lib/lab_sim/surface.py`、`lib/lab_sim/figure_export.py` -> `tests/test_lab_surface_export.py` |

## 前端实验与地图

| 路径 | 职责 |
|---|---|
| `frontend/src/pages/Lab.tsx` | 实验模式页面：waypoint/survey、droplet count、seed、污染源、auto-scan 参数 |
| `frontend/src/pages/Map.tsx` | 地图与污染物 surface；消费后端返回的 GCJ-02 坐标并标记 GCJ-02 图面输入 |
| `frontend/src/lib/lab-coordinate-adapter.ts` | schema v2 双坐标读写适配：`gcj02Input`、`gcj02ForDrawing` |
| `frontend/src/lib/lab-types.ts`、`frontend/src/lib/lab-map.ts`、`frontend/src/hooks/use-lab-map.ts` | 实验类型、地图与 hook |

## 污染物地图边界

- 污染物线性模型、校准元数据、点质量、GeoJSON/CSV 导出和 IDW 热力图 surface 的源码归属 `src/usv_ros`。
- 不在 `ardupilot-usv/` 增加污染物浓度计算、历史记录或热力图逻辑；固件只处理 `USV_SMPL/USV_DONE` 和载荷遥测转发。
- 不在 `DetFirmware/` 增加污染物浓度输出；检测装置固件保持分光原始量、电压、valid、基线和健康帧职责。
- 第一阶段不在 `WQ-USV-QGroundControl/` 实现污染物热力图；QGC 只保留任务、命令和遥测展示边界。
- 实验仿真液滴生成、科研 surface 与 300 DPI/SVG/PDF 图件导出的源码归属 `src/usv_ros/scripts/lib/lab_sim/`；坐标 schema v2 反算和持久化由 `web_config_server.py` 承载。ArduPilot/DetFirmware/QGC 不参与。
