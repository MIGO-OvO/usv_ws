# docs/current Agent Rules

## OVERVIEW

`docs/current/` 只保存当前有效事实、接口、运行步骤和验证矩阵；历史计划、流水账和旧索引放 `docs/archive/`。

## STRUCTURE

| 文件 | 用途 |
|---|---|
| `00_index.md` | 阅读顺序和任务入口 |
| `10_agent.md` | Agent 协同、MAVLink 强制流程、提交边界 |
| `20_system_overview.md` | 五端结构、链路、当前能力 |
| `30_development_requirements.md` | 当前需求状态 |
| `40_interfaces.md` | ROS/Web/Socket.IO/MAVLink/串口速查 |
| `50_build_update_runbook.md` | 更新、构建、运行、部署 |
| `60_source_map.md` | 关键源码位置和职责边界 |
| `70_verification.md` | 静态、联调、现场验证矩阵 |

## CONVENTIONS

- 文档冲突时先查源码，再更新本目录。
- MAVLink 事实以 `ardupilot-usv/` 固件实现为准。
- ROS 运行事实以 `src/usv_ros/README.md`、`launch/usv_bringup.launch`、`scripts/*.py|*.sh` 为准。
- QGC UI 事实以 `WQ-USV-QGroundControl/custom/` 为准。
- 检测装置协议以 `DetFirmware/src/main.cpp` 与 `src/usv_ros/scripts/pump_control_node.py` 双向核对。

## ANTI-PATTERNS

- 在本目录记录历史流水账、一次性计划、旧状态。
- 只改文档不核对源代码，尤其是 MAVLink 字段、命令、ACK、路由。
- 记录带凭证的 remote URL。
- 把 `docs/CGEDC/` 比赛材料当作 current 真源。

## VERIFY

```bash
find docs/current -maxdepth 1 -type f -name '*.md' | sort
rg -n "USV_SMPL|USV_DONE|31010|31019|NAMED_VALUE_FLOAT|DET_ID" docs/current
```
