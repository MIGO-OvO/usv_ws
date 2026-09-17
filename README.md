# usv_ws 总管理仓库

Updated: 2026-05-20

本仓库是水质监测无人船工作区的总入口，只管理根文档、bootstrap 脚本和跨仓库索引；业务源码由各子仓库独立管理。

## 当前文档入口

- 总索引：`docs/current/00_index.md`
- Agent 入口：`AGENTS.md`
- 完整 Agent 规范：`docs/current/10_agent.md`
- 系统概览：`docs/current/20_system_overview.md`
- 接口速查：`docs/current/40_interfaces.md`
- 构建运行：`docs/current/50_build_update_runbook.md`

## 外部源码目录

| 目录 | 说明 |
|---|---|
| `ardupilot-usv/` | 定制 ArduRover 固件 |
| `WQ-USV-QGroundControl/` | 定制 QGroundControl |
| `src/usv_ros/` | Jetson Nano ROS 载荷系统 |
| `DetFirmware/` | ESP32 检测装置固件，独立私有仓库 [MIGO-OvO/DetFirmware](https://github.com/MIGO-OvO/DetFirmware)，默认分支 `main` |
| `MotorControlApp_Pyside6/` | Windows 检测装置上位机 |

## Bootstrap

Windows 根入口：

```bat
bootstrap_workspace.bat
```

脚本负责拉取/更新外部源码仓库。不要把外部源码目录提交到根仓库。

`DetFirmware` 需要已获授权的 GitHub 账号。脚本不会覆盖现有目录：旧工作区中若
`DetFirmware/` 没有独立 `.git`，须先备份本地改动，再迁移或另行克隆；不要直接清空目录。
新克隆通过 bootstrap 获取固件，开发与台架验证说明见 `DetFirmware/README.md`。

## 根仓库保留内容

- `README.md`
- `AGENTS.md`
- `bootstrap_workspace.bat`
- `.gitignore`
- `docs/current/`
- `docs/archive/`

## 最小构建入口

### ROS

```bash
cd ~/usv_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

### QGroundControl

```bash
cd ~/usv_ws/WQ-USV-QGroundControl
make submodules
make configure
make build
```

### ArduPilot

```bash
wsl
cd /mnt/d/usv_ws/ardupilot-usv
git submodule update --init --recursive
./waf configure --board Pixhawk6C
./waf rover
cp build/Pixhawk6C/bin/ardurover.apj /mnt/d/usv_ws/ardurover.apj
```

## Git 约束

- 根仓库只提交文档和根入口。
- `src/usv_ros/`、`ardupilot-usv/`、`WQ-USV-QGroundControl/`、`DetFirmware/`、`MotorControlApp_Pyside6/` 的改动必须进入对应子仓库单独 commit。
- 不在根目录执行跨仓库全量提交。
- 不记录带凭证的 remote URL。
- `DetFirmware/` 已从根仓库当前版本停止跟踪；历史未改写，旧提交仍保留当时源码及其原有访问权限。切换仍跟踪该目录的旧分支前，先备份独立仓库。
