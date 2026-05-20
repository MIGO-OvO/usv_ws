# docs/current 当前真源索引

Updated: 2026-05-20

`docs/current/` 只保存当前有效事实、接口、运行步骤和验证矩阵。历史计划、流水账、旧索引已归档到 `docs/archive/2026-05-20-current-pre-restructure/`。

## 阅读顺序

1. `10_agent.md`：Agent 协同规则、MAVLink 源码优先、提交边界。
2. `20_system_overview.md`：五端结构、链路、当前能力。
3. `30_development_requirements.md`：已完成、进行中、待办。
4. `40_interfaces.md`：ROS、Web、Socket.IO、MAVLink、串口协议速查。
5. `50_build_update_runbook.md`：更新、构建、运行、部署。
6. `60_source_map.md`：关键源码位置和职责边界。
7. `70_verification.md`：静态、联调、现场验证矩阵。

## 按任务查文档

| 任务 | 首读 | 交叉核对 |
|---|---|---|
| 新 Agent 接手 | `10_agent.md` | `60_source_map.md` |
| MAVLink 命令/遥测变更 | `40_interfaces.md` | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`ardupilot-usv/Rover/sensors.cpp` |
| ROS 现场启动/更新 | `50_build_update_runbook.md` | `src/usv_ros/README.md` |
| QGC 载荷面板变更 | `40_interfaces.md` | `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc` |
| 检测装置串口联调 | `40_interfaces.md` | `DetFirmware/src/main.cpp`、`src/usv_ros/scripts/pump_control_node.py` |
| 规划下一阶段 | `30_development_requirements.md` | `70_verification.md` |

## 当前事实源规则

- 源码优先级高于文档；文档冲突时先查源码，再更新本目录。
- MAVLink 事实以 `ardupilot-usv/` 固件实现为准。
- ROS 运行事实以 `src/usv_ros/README.md`、`launch/usv_bringup.launch`、`scripts/*.py|*.sh` 为准。
- QGC UI 事实以 `WQ-USV-QGroundControl/custom/` 为准。
- 检测装置协议以 `DetFirmware/src/main.cpp` 与 `pump_control_node.py` 双向核对。
- `docs/CGEDC/` 为比赛材料区，不属于本次 current 文档真源。

## 目录约束

- `docs/current/` 禁止存放历史流水账、一次性计划、旧索引。
- `docs/archive/` 可保存历史版本；归档内容不代表当前有效状态。
- 根 `AGENTS.md` 只作为自动发现短入口；完整规则在 `docs/current/10_agent.md`。
- 不在文档中记录带凭证的 remote URL。
