# 开发需求与状态

Updated: 2026-05-20

本文件替代旧 `roadmap.md`，只记录当前有效需求和状态。

## 已完成

| 模块 | 状态 | 依据 |
|---|---|---|
| ROS 主启动链路 | 已完成 | `src/usv_ros/launch/usv_bringup.launch` |
| MAVLink router bridge | 已完成 | `src/usv_ros/scripts/usv_mavlink_router_bridge.py` |
| MAVLink 指令节点 | 已完成 | `src/usv_ros/scripts/mavlink_trigger_node.py` |
| 17 字段载荷遥测 | 已完成 | `usv_mavlink_router_bridge.py`、`ardupilot-usv/Rover/sensors.cpp` |
| 固件侧字段缓存与 2 Hz 转发 | 已完成 | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`Rover/sensors.cpp` |
| `NAV_SCRIPT_TIME -> USV_SMPL -> ROS采样 -> USV_DONE` | 已完成 | `usv_mavlink_router_bridge.py`、`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp` |
| Web 控制台与 API | 已完成 | `src/usv_ros/scripts/web_config_server.py`、`src/usv_ros/frontend/` |
| 检测装置串口握手 | 已完成 | `src/usv_ros/scripts/pump_control_node.py` |
| 系统启动脚本与 `usvctl` | 已完成 | `src/usv_ros/scripts/*.sh` |

## 进行中

| 方向 | 当前目标 | 验证入口 |
|---|---|---|
| 实船联调 | 验证电台、router、MAVROS、QGC 面板全链路 | `70_verification.md` |
| 采样可靠性 | 验证航点等待、稳定判定、失败策略 | `mavlink_trigger_node.py` |
| 检测装置长期运行 | 验证串口重连、分光数据有效位、泵控反馈 | `pump_control_node.py` |
| QGC 展示一致性 | 核对 17 字段名称、状态码、component id | `WQ-USV-QGroundControl/custom/` |

## 待办

| 优先级 | 项 | 说明 |
|---|---|---|
| P0 | 现场链路验证记录 | 形成一份真实设备验证表，覆盖 QGC 命令、ROS 响应、固件 ACK、遥测显示 |
| P0 | `USV_STAT` 状态码收口 | 固件、ROS、QGC 统一状态码表；禁止 UI 自行猜测 |
| P1 | Web API 自动化检查 | 对关键 GET/POST 做离线冒烟脚本，不依赖真实硬件时使用 mock |
| P1 | 检测装置固件构建记录 | 固化 PlatformIO/Arduino 构建与刷写命令 |
| P1 | Windows 上位机与 ROS 协议差异表 | 避免 DetFirmware 串口命令双入口语义漂移 |
| P2 | 日志保留策略 | 统一 `.usv_run/logs`、Web 日志 API、现场导出格式 |

## 不做范围

- 不在根仓库修改业务源码。
- 不整理 `docs/CGEDC/`。
- 不把历史计划继续放入 `docs/current/`。
- 不记录任何带凭证的 remote URL。

## 变更准入

MAVLink、串口协议、Web API 变更必须同步更新：

1. `40_interfaces.md`
2. `60_source_map.md` 对应源码位置
3. `70_verification.md` 对应验证项
4. 子仓库 README 或局部文档（若接口已公开）
