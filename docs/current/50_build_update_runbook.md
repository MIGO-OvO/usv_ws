# 构建、更新、运行 Runbook

Updated: 2026-10-19

## 根仓库

### safety1 成套发布要求

本版本不得只更新 ROS：DetFirmware/ROS/Windows 要匹配 `WATCHDOG1`；飞控/QGC 要匹配超时 HOLD 和 `USV_FAIL` 语义。更新前停任务和执行器，保留上一整套产物与参数；不要在运行中混用进程版本。

在总仓库运行 `python docs/tools/check_workspace_compatibility.py` 做源码检查；`--snapshot` 将候选五端提交号、工作树状态及关键文件哈希打印为 JSON。保存候选后用 `--manifest <候选文件>` 检查匹配。`--require-release` 额外拒绝脏子仓库、未记录现场验收、缺少证据引用/产物哈希的清单。脚本不部署、不修改仓库，不是自动认证器。

当前清单 schema v2 的文本源码哈希先将 CRLF 规范化为 LF，避免相同提交在 Windows/Linux 检出时误报。归档的 v1 工作树快照保留历史意义，不作为当前版本匹配清单；提交后重新生成 v2 候选，仍须独立记录现场验收。

船载热点/LAN 的 Web 控制默认无需登录，前端可直接执行分光、泵控、自动采样；同源/跨站防护保留。需要认证时，在服务进程环境设置 `USV_WEB_REQUIRE_AUTH=1` 和 `USV_WEB_CONTROL_TOKEN`（至少 16 字符，随机生成并安全分发，不提交 Git），然后重启 Web 服务；启用认证但令牌缺失或过短会拒绝启动，仅配置 token 不启用认证。认证模式下浏览器先打开 `http://船载地址:5000/api/control/auth`，用户名 `operator`，密码为该令牌，再使用控制台。默认模式允许任何可达客户端控制，非可信网络应启用认证、网络访问隔离及 HTTPS/VPN；令牌不加密 HTTP。

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

实验仿真科研 surface 和图件导出额外依赖（仅 `lab_sim` surface/figure_export 与其测试需要，Web 端 IDW 热力图为纯 Python，不需要）：

```bash
python3 -m pip install numpy matplotlib
```

`numpy` 用于 `scripts/lib/lab_sim/surface.py` 的 ENU 网格 surface；`matplotlib` 用于 `figure_export.py` 导出 300 DPI PNG/TIFF、SVG/PDF，缺失时导出抛 `FigureExportError`。

启动：

```bash
cd ~/usv_ws
chmod +x src/usv_ros/scripts/*.sh
src/usv_ros/scripts/start_usv_all.sh
src/usv_ros/scripts/status_usv_all.sh
```

任务数据默认写入 `~/usv_ws/data/missions`。如数据盘挂载到其他位置，使用显式绝对路径启动：

```bash
src/usv_ros/scripts/start_usv_all.sh data_dir:=/mnt/usv-data/missions
```

热点连接后可下载完整历史任务包：

```bash
curl http://10.42.0.1:5000/api/data/missions
curl http://10.42.0.1:5000/api/data/mission/<mission_id>/archive > mission.zip
```

全局命令安装后：

```bash
usvon
usvstatus
usvoff
usvdeploy
```

`usvdeploy` 语义：stop -> 自动 stash 本地改动 -> `git pull --ff-only` -> 脚本赋权 -> `catkin_make` -> start。
`usvupdate` 共用更新逻辑：工作区不干净时，先用 `git stash push --include-untracked` 备份
已跟踪文件的工作区/暂存区改动及未跟踪文件；Git 忽略的数据、日志、缓存不纳入 stash。
备份带时间标记并保留，更新后不自动恢复，命令会打印固定备份提交号和 `stash apply --index` 恢复命令。
已有 stash 不删除，干净工作区不创建新备份；备份/拉取失败则停止后续部署。
同步目标为当前分支配置的远端上游，本地已提交的分叉仍由 `--ff-only` 拒绝，不自动丢弃提交。
系统运行时 `usvupdate/usvbuild` 应拒绝执行。详细备份查看与恢复步骤见 `src/usv_ros/README.md`。

离线逻辑验证（无需硬件，在 `src/usv_ros` 目录）：

```bash
cd ~/usv_ws/src/usv_ros
python3 -m py_compile scripts/*.py scripts/lib/lab_sim/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

实验仿真验收细项见 `docs/current/70_verification.md` 的「实验仿真 Schema v2 验证」；现场前端验收前重建产物：

```bash
cd ~/usv_ws/src/usv_ros/frontend && npm run build
```

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

Jetson 更新 ROS 仓库后运行 `bash ~/usv_ws/src/usv_ros/scripts/install_usv_commands.sh install`，安装 `usvlogs` 快捷命令：

```bash
usvlogs pack field-1022       # 最近 3 个 ROS 会话与启动日志
usvlogs usage                # 启动日志、ROS 日志、日志包占用
usvlogs clean                # 预览
usvlogs clean --apply        # 轮转并删除过期会话/日志包，不可恢复
usvlogs auto on              # 每 10 分钟自动清理；auto off 关闭
usvlogs auto status
```

自动清理需要 `logrotate`、`cron`，以运行 USV 的普通用户启用，并确认 `systemctl is-active cron` 返回 active。默认保留 3 个会话/日志包，ROS 会话预算 512 MiB，日志包预算 256 MiB；保留活跃会话和最近一小时日志，超出预算时输出警告。启动日志和 ROS 文本日志按 10 MiB、5 份轮转。检查间隔与活动文件保护意味着预算不是硬磁盘上限。工具不清理采样数据、pcap 或系统 journal。

日志包输出到 `~/usv_ws/.usv_run/bundles/`，单文件末尾最多 2 MiB、总计最多 64 MiB，截取情况见包内 `manifest.json`。Windows 同步根仓库和 ROS 仓库后，双击根目录 `download_jetson_logs.bat`，输入 IP 与包名，下载到本机 `.usv_run/downloads/`；默认 SSH 用户为 jetson，认证由 OpenSSH 处理。完整参数与保留规则见 `src/usv_ros/README.md` 的“日志管理与下载”。

| 位置 | 内容 |
|---|---|
| `.usv_run/logs/mavlink_router.log` | router 输出 |
| `.usv_run/logs/` | ROS 启停脚本后台日志 |
| Web 日志 API | 日志列表、读取、下载 |
| ROS console | 节点实时输出 |

## 最小现场启动检查

2026-10 跨端版本需成套部署：先停任务并确认执行器安全，备份配置/旧产物/故障证据，再更新 ROS（含 static/dist）、DetFirmware、ArduRover 和 QGC，最后重启并只读核验。ROS 保留请求 SQLite 与 transport 会话文件，QGC 保留 `payload-request-identity.ini`；不要通过删除账本重置编号。旧 QGC 窗口必须退出后再启动新产物，本次 Agent 未替换运行中的窗口，也未烧录设备。

先验证 STOP 与确认状态，再低负载验证准备/采样/失败恢复；检测板仍有独立 30 秒 PID 限时。出现旧动作重放、假成功、停止未确认或持续失联，立即停机并保留日志，回退匹配组合；不能回退到含已知安全缺陷的版本后继续自动采样。`rotate_runtime_logs.py` 默认 dry-run，仅显式 `--rotate` 时采用 10 MiB × 5 的 copytruncate；有微小丢行窗口，不自动处理现场证据。

```bash
usvstatus
rostopic list | grep usv
rostopic echo -n 1 /usv/bridge_diagnostics
rostopic echo -n 1 /usv/radio_status
```

上述输出只证明部分链路和进程活动：飞控/MAVROS 在线、发送计数增长、QGC 可见旧字段，均不能单独证明 ROS 当前在线或原始“待机后载荷离线”已解决。

端到端验收须记录同一运行窗口的实际部署提交与产物摘要、sysid/component、request/session/tcp_session、attempt、字段独立 freshness 及关联终态。分光未启动/正常 STOP 后，其他载荷状态应长期继续更新，不能将分光无效等同整组离线。标准 ACK、进入准备、任务终态、软件清理和实物停止分别确认；通信恢复不得续泵或重放旧请求。

本轮 Agent 仅提交/推送 PR，不合并、部署、烧录或控制硬件。操作者成套更新前，应按 [续修闭环](../reports/2026-10-19-audit-followup.md) 的版本清单与最小台架步骤验收；保留配置、身份账本和原始故障证据。
