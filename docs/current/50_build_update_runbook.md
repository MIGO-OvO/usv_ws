# 构建、更新、运行 Runbook

Updated: 2026-05-20

## 根仓库

```bat
bootstrap_workspace.bat
```

作用：拉取/更新外部源码目录 `ardupilot-usv/`、`WQ-USV-QGroundControl/`、`src/usv_ros/`。根仓库只管理文档、入口和总配置。

## ROS / Jetson Nano

首次依赖：

```bash
cd ~/usv_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
sudo apt install ros-noetic-mavros ros-noetic-mavros-extras mavlink-router python3-pip
python3 -m pip install pyserial flask flask-cors flask-socketio eventlet pymavlink
```

启动：

```bash
cd ~/usv_ws
chmod +x src/usv_ros/scripts/*.sh
src/usv_ros/scripts/start_usv_all.sh
src/usv_ros/scripts/status_usv_all.sh
```

全局命令安装后：

```bash
usvon
usvstatus
usvoff
usvdeploy
```

`usvdeploy` 语义：stop -> `git pull --ff-only` -> `catkin_make` -> start。系统运行时 `usvupdate/usvbuild` 应拒绝执行。

## MAVLink router

`src/usv_ros/scripts/common_env.sh` 当前默认：

| 变量 | 默认 |
|---|---|
| `FCU_UART_DEVICE` | `/dev/ttyTHS1` |
| `FCU_UART_BAUD` | `921600` |
| `ROUTER_MAVROS_UDP` | `127.0.0.1:14550` |
| `ROUTER_BRIDGE_UDP` | `127.0.0.1:14551` |
| `ROUTER_TCP_PORT` | `5760` |

启动脚本执行：`mavlink-routerd -e 127.0.0.1:14550 -e 127.0.0.1:14551 /dev/ttyTHS1:921600`，并维护 `.usv_run/mavlink_router.pid` 与 `.usv_run/logs/mavlink_router.log`。

## QGroundControl

```bash
cd ~/usv_ws/WQ-USV-QGroundControl
make submodules
make configure
make build
```

如本机 Qt/QGC 环境不同，以 `WQ-USV-QGroundControl/README.md`、`Makefile`、`justfile` 为准。最终构建由用户本地验证。

## ArduPilot / Pixhawk 6C

必须在 WSL Ubuntu 或 Linux 下：

```bash
cd /mnt/d/usv_ws/ardupilot-usv
git submodule update --init --recursive
./waf configure --board Pixhawk6C
./waf rover
cp build/Pixhawk6C/bin/ardurover.apj /mnt/d/usv_ws/ardurover.apj
```

生成固件后按现场刷写流程导入 Pixhawk 6C。禁止在 Windows PowerShell 中直接假定 waf 构建可用。

## DetFirmware / ESP32

当前事实源：`DetFirmware/`。构建方式以该仓库内 PlatformIO/Arduino 配置为准。验证重点：

- 串口握手返回 `DET_ID:USV_DETECTOR*`。
- X/Y/Z/A 角度帧稳定输出。
- 分光帧 `0xDD` 有效位和电压字段与 ROS 解析一致。

## Windows 上位机

路径：`MotorControlApp_Pyside6/`。用于检测装置本地调试，不替代 ROS 现场主链路。协议变更需与 `pump_control_node.py`、`DetFirmware/src/main.cpp` 对齐。

## 日志

| 位置 | 内容 |
|---|---|
| `.usv_run/logs/mavlink_router.log` | router 输出 |
| `.usv_run/logs/` | ROS 启停脚本后台日志 |
| Web 日志 API | 日志列表、读取、下载 |
| ROS console | 节点实时输出 |

## 最小现场启动检查

```bash
usvstatus
rostopic list | grep usv
rostopic echo -n 1 /usv/bridge_diagnostics
rostopic echo -n 1 /usv/radio_status
```

通过标准：router 运行、MAVROS 连接、bridge 发送计数递增、QGC 可见载荷字段。
