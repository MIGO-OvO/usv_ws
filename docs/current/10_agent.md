# Agent 协同规范

Updated: 2026-05-20

## 角色

本项目是水质监测无人船多端协同系统。Agent 需要同时理解：

- `WQ-USV-QGroundControl/`：地面站定制 UI 与载荷遥测展示。
- `src/usv_ros/`：Jetson Nano 船载 ROS、Web、MAVLink bridge、检测装置控制。
- `ardupilot-usv/`：Pixhawk 6C 定制 ArduRover 固件。
- `DetFirmware/`：ESP32 检测装置主控固件。
- `MotorControlApp_Pyside6/`：Windows 检测装置上位机。

核心原则：协议一致性优先，固件源码为纲，中文简明回复。

## MAVLink 强制流程

任何 MAVLink 命令、遥测、路由、component id、ACK 行为变更前，必须先查 `ardupilot-usv/`：

| 场景 | 必查文件 | 目的 |
|---|---|---|
| `COMMAND_LONG 31010..31019` | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp` | 确认命令接收、参数、ACK 时机 |
| `NAMED_VALUE_FLOAT` 载荷字段 | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`Rover/sensors.cpp`、`Rover/Rover.h` | 确认字段名、缓存结构、2 Hz 转发 |
| MAVLink 路由/过滤 | `ardupilot-usv/libraries/GCS_MAVLink/` | 确认路由规则、payload 限制、转发策略 |
| NAV_SCRIPT_TIME 采样闭环 | `ardupilot-usv/Rover/mode_auto.cpp`、`src/usv_ros/scripts/usv_mavlink_router_bridge.py` | 确认 `USV_SMPL` 与 `USV_DONE` 闭环 |

禁止只按通用 MAVLink 文档或经验改 ROS/QGC 代码。

## 三端逻辑映射

- QGC 发送 `COMMAND_LONG 31010..31019`。
- ROS `usv_mavlink_router_bridge.py` 从 router TCP 收命令，发布 `/usv/mavlink_cmd_rx`。
- ROS `mavlink_trigger_node.py` 解释命令，控制采样/校准/走航/分光。
- ROS `usv_mavlink_router_bridge.py` 以 `NAMED_VALUE_FLOAT` 发送 17 个载荷字段。
- ArduRover `GCS_MAVLink_Rover.cpp` 缓存字段，`sensors.cpp` 以 2 Hz 转发到 GCS。
- `NAV_SCRIPT_TIME` 触发时，固件发 `USV_SMPL`；ROS 完成采样后回 `USV_DONE`。

## 多仓库提交边界

- 根仓库：只提交 `README.md`、`AGENTS.md`、`docs/`、bootstrap 入口和根配置。
- `src/usv_ros/`：ROS/Web/前端/脚本改动必须在该仓库内单独 commit。
- `ardupilot-usv/`：固件改动必须在该仓库内单独 commit；构建在 WSL Ubuntu。
- `WQ-USV-QGroundControl/`：QGC 改动必须在该仓库内单独 commit。
- 不在根目录执行跨仓库全量 `git add .`。

## 输出要求

涉及 MAVLink 交互的回复必须包含：

- 源码依据：文件路径和行号。
- 逻辑映射：QGC/ROS/固件如何对应。
- 验证方式：至少说明静态核对命令或需用户实测的步骤。

## 运行验证边界

- QGC：用户在 Qt Creator 或本地构建环境验证。
- ROS：用户同步到 Jetson/Ubuntu 后运行验证。
- ArduPilot：在 WSL Ubuntu 按固件构建流程验证。
- Agent 当前环境可做静态核对、文档链接检查、语法级检查。
