# usv_ws Agent Knowledge Base

Generated: 2026-06-15
Root commit: ed52153
Root branch: codex/detector-stress-closure

## OVERVIEW

`usv_ws` 是水质监测无人船总管理仓库，只管理根文档、bootstrap 和跨仓库入口；业务源码在各子仓库内维护。所有任务先读 `docs/current/00_index.md`，完整协同规则在 `docs/current/10_agent.md`。

## STRUCTURE

```text
usv_ws/
├── README.md                         # 总入口
├── bootstrap_workspace.bat           # Windows 外部源码拉取/更新入口
├── docs/current/                     # 当前事实源
├── ardupilot-usv/                    # Pixhawk 6C 定制 ArduRover
├── WQ-USV-QGroundControl/            # 定制 QGC
├── src/usv_ros/                      # Jetson ROS/Web/MAVLink bridge
├── DetFirmware/                      # ESP32 检测装置固件
└── MotorControlApp_Pyside6/          # Windows 检测装置上位机
```

## WHERE TO LOOK

| 任务 | 位置 | 注意 |
|---|---|---|
| 新 Agent 接手 | `docs/current/00_index.md` -> `docs/current/10_agent.md` | 中文、简明、源码优先 |
| 系统链路理解 | `docs/current/20_system_overview.md` | 五端结构和主数据链路 |
| MAVLink 命令/遥测 | `docs/current/40_interfaces.md` + `ardupilot-usv/Rover/` | 先查固件源码 |
| ROS 现场启动 | `docs/current/50_build_update_runbook.md` + `src/usv_ros/README.md` | Jetson/Ubuntu 为准 |
| 源码边界 | `docs/current/60_source_map.md` | 避免把逻辑写错端 |
| 验证矩阵 | `docs/current/70_verification.md` | 当前环境多为静态验证 |

## CODE MAP

| 端 | 核心入口 | 角色 |
|---|---|---|
| QGC | `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`、`custom/res/USVPayloadPanel.qml` | 载荷 Fact 与面板 |
| ROS | `src/usv_ros/launch/usv_bringup.launch`、`scripts/usv_mavlink_router_bridge.py`、`scripts/mavlink_trigger_node.py` | 主启动、MAVLink bridge、采样状态机 |
| 固件 | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`Rover/sensors.cpp`、`Rover/mode_auto.cpp` | 载荷缓存、2 Hz 转发、mission script |
| 检测装置 | `DetFirmware/src/main.cpp`、`DetFirmware/src/protocol_packets.h` | 串口命令和二进制帧 |
| 上位机 | `MotorControlApp_Pyside6/main.py`、`MotorControlApp_Pyside6/src/` | Windows 本地调试 |

## CONVENTIONS

- 回复中文、简明；涉及协议时给出源码路径和验证方式。
- 文档冲突时以源码为准；MAVLink 事实以 `ardupilot-usv/` 为准。
- 根仓库只提交 `README.md`、`AGENTS.md`、`docs/`、bootstrap 入口和根配置。
- `src/usv_ros/`、`ardupilot-usv/`、`WQ-USV-QGroundControl/`、`DetFirmware/`、`MotorControlApp_Pyside6/` 有独立 Git，业务改动在子仓库内就地提交。
- `DetFirmware` 为 `MIGO-OvO/DetFirmware` 私有仓库，默认分支 `main`，开发入口为其 `README.md`；根仓库忽略该目录，不使用 submodule。
- 不在根目录执行跨仓库全量 `git add .`。
- 不在文档中记录带凭证的 remote URL。

## ANTI-PATTERNS

- MAVLink 相关变更只按通用 MAVLink 文档或经验修改 ROS/QGC。
- 在 ArduPilot/DetFirmware 中加入污染物浓度、历史记录、热力图逻辑；这些归 `src/usv_ros`。
- 把 QGC 第一阶段改成污染物热力图载体；QGC 当前只管任务、命令、遥测展示。
- 提交 `build/`、`devel/`、`.pio/`、`.venv/`、`node_modules/`、地图瓦片缓存和现场日志。

## COMMANDS

```bash
# 根文档/路径静态检查优先
rg -n "USV_SMPL|USV_DONE|31010|31019|NAMED_VALUE_FLOAT" docs/current src/usv_ros ardupilot-usv/Rover WQ-USV-QGroundControl/custom DetFirmware/src

# ROS 常用离线验证（在有 Python/ROS 环境时）
python3 -m py_compile src/usv_ros/scripts/*.py
python3 -m unittest discover -s src/usv_ros/tests -p 'test_*.py'

# 前端改动后
cd src/usv_ros/frontend && npm run build
```

## NOTES

- 航线定点采样使用 `MAV_CMD_NAV_SCRIPT_TIME(param1=1)`；手动载荷控制使用 `COMMAND_LONG 31010..31019`。
- ROS 通过 `USV_DONE` 通知固件继续 mission script；固件发 `USV_SMPL` 触发 ROS 定点采样。
- 检测装置串口协议变更必须同时核对 `DetFirmware/src/main.cpp` 与 `src/usv_ros/scripts/pump_control_node.py`。
