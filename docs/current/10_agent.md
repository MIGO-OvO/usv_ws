# Agent 协同规范

Updated: 2026-10-21

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

- QGC Plan 航线定点采样使用 `MAV_CMD_NAV_SCRIPT_TIME(param1=1)`；手动载荷控制发送 `COMMAND_LONG 31010..31019`。
- ROS `usv_mavlink_router_bridge.py` 从 router TCP 收命令；关联载荷请求发布带执行实例的 `/usv/payload_command`，飞控内部事件和无关联兼容 STOP 走 `/usv/mavlink_cmd_rx`。
- ROS `mavlink_trigger_node.py` 解释命令，控制采样/校准/走航/分光。
- ROS `usv_mavlink_router_bridge.py` 以 `NAMED_VALUE_FLOAT` 发送 26 个载荷字段，其中 5 个为系统健康字段；新增能力与采集状态为 `USV_PROTO/USV_ADS`。
- ArduRover `GCS_MAVLink_Rover.cpp` 缓存字段，`sensors.cpp` 以 2 Hz 转发到 GCS。
- `NAV_SCRIPT_TIME(param1=1)` 触发时，固件发 `USV_SMPL`；ROS 完成采样后回 `USV_DONE`。

## 多仓库提交边界

- 根仓库：只提交 `README.md`、`AGENTS.md`、`docs/`、bootstrap 入口和根配置。
- `src/usv_ros/`：ROS/Web/前端/脚本改动必须在该仓库内单独 commit。
- `ardupilot-usv/`：固件改动必须在该仓库内单独 commit；构建在 WSL Ubuntu。
- `WQ-USV-QGroundControl/`：QGC 改动必须在该仓库内单独 commit。
- `DetFirmware/`：独立私有仓库 `MIGO-OvO/DetFirmware`，默认分支 `main`；固件、协议及测试在该仓库内单独 commit，先读 `DetFirmware/README.md`。根仓库不再跟踪该目录，不使用 submodule。
- 不在根目录执行跨仓库全量 `git add .`。

## 输出要求

涉及 MAVLink 交互的回复必须包含：

- 源码依据：文件路径和行号。
- 逻辑映射：QGC/ROS/固件如何对应。
- 验证方式：至少说明静态核对命令或需用户实测的步骤。

## 运行验证边界

- QGC：复用现有 Qt、本地构建目录或 CI，区分逻辑测试、平台产物与现场验收。
- ROS：用户同步到 Jetson/Ubuntu 后运行验证。
- ArduPilot：在 WSL Ubuntu 按固件构建流程验证。
- Agent 按实际可用环境运行相关验证，如实记录未执行部分。

## QGC 构建与 CI 验收（长期）

- 构建验收目标只有 **Windows、Android**，按产物目标平台判断。Ubuntu/macOS runner 或 Docker 上构建 Android 仍属范围，保留其共享前置步骤。
- Linux 桌面、AppImage、macOS 等非目标产物不进入排查、依赖修复、重跑或等待范围，不阻塞本轮代码交付。混合工作流只查看 Windows/Android 对应 job，无需为此重构工作流。
- 先跑改动直接相关的 QML/Python/ROS 逻辑测试，再对最终修改批次做必要平台验证。复用工具链、构建目录和矩阵；QML 小修不搭建其他桌面平台环境，无 ROS 改动不跑无关全量回归。
- 同一有效 head 不重复触发相同构建、不做空提交刷 CI。失败先判断与改动的关系，仅在代码或明确环境修正后重跑相关项；偶发超时不触发全局放宽或连续重跑。旧全仓 lint 问题只记录，本轮引入的格式问题就地修正。
- 推送后查看相关状态，交付前必要时再看一次。排队或长时间运行时交付实际状态与链接，不无限轮询；旧 head 通过不能替代当前 head 验证。
- 若分支保护要求非目标平台，报告“仓库合并配置与当前验收范围不一致”；保留保护规则，不绕过检查或代为合并。验证分类与现场步骤见 `70_verification.md`。
