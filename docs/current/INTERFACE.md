# 接口速查
Updated: 2026-04-26T19:40:51+08:00

## 0. 总管理仓库入口
- 根文档：`README.md`
- 根脚本（Windows）：`bootstrap_workspace.bat`
- 内置仓库地址：`https://github.com/MIGO-OvO/ardupilot-usv.git` `https://github.com/MIGO-OvO/WQ-USV-QGroundControl.git` `https://github.com/MIGO-OvO/usv_ros.git`
- 克隆目标：`ardupilot-usv/` `WQ-USV-QGroundControl/` `src/usv_ros/`
- 同步动作：`git clone --recursive` + `git submodule update --init --recursive`
- 根忽略文件：`.gitignore`
- 忽略目录：`/ardupilot-usv/` `/WQ-USV-QGroundControl/` `/src/usv_ros/` `/src/CMakeLists.txt` `/build/` `/devel/` `/log/` `/.usv_run/`

## 1. 启停脚本
目录：`src/usv_ros/scripts/`
- `common_env.sh`：加载 ROS 环境，管理 `RUN_DIR`、`LOG_DIR`、`mavlink-routerd` 启停。
- `start_usv_all.sh`：后台启动 `roscore`、`mavlink-routerd`、`roslaunch usv_ros usv_bringup.launch`。
- `start_usv_system.sh`：前台启动 `roslaunch`，启动前确保 `roscore` 与 `mavlink-routerd` 已就绪。
- `stop_usv_all.sh`：停止 `usv_system`、`mavlink-routerd`、`roscore`。
- `status_usv_all.sh`：输出 `roscore`、`mavlink_router`、`usv_system` 状态与日志路径。
- `restart_usv_all.sh`：未包含单独逻辑说明；功能为 stop -> start。
- `usvctl.sh`：统一 CLI 分发入口，支持 `start`、`stop`、`restart`、`status`、`update`、`build`、`deploy`。
- `install_usv_commands.sh`：向 `~/.local/bin` 安装/卸载 `usvctl`、`usvon`、`usvoff`、`usvrestart`、`usvstatus`、`usvupdate`、`usvbuild`、`usvdeploy` symlink。

### 1.1 全局命令
- `usvon`：后台启动完整 ROS 系统；等价 `usvctl start`，参数透传给 `roslaunch usv_ros usv_bringup.launch`。
- `usvoff`：停止完整 ROS 系统；等价 `usvctl stop`。
- `usvstatus`：输出进程、热点、外网、ROS 节点、MAVROS、bridge 状态；等价 `usvctl status`。
- `usvrestart`：stop -> start；等价 `usvctl restart`，参数透传给 `roslaunch`。
- `usvupdate`：仅在 `src/usv_ros/` 执行 `git pull --ff-only`；系统运行时拒绝执行。
- `usvbuild`：在工作区根目录执行 `catkin_make`；系统运行时拒绝执行。
- `usvdeploy`：stop -> update -> build -> start；用于 Nano 现场更新部署。

## 2. Launch 入口
文件：`src/usv_ros/launch/usv_bringup.launch`

### 2.1 启动节点
- `pump_control_node`
- `web_config_server`
- `usv_mavlink_bridge`（实际脚本：`usv_mavlink_router_bridge.py`）
- `mavlink_trigger_node`
- 顺序：`usv_mavlink_bridge` 在 `mavlink_trigger_node` 前声明；核心依赖仍以 topic 重连与 bridge `autoreconnect=True` 兜底。

### 2.2 Launch 参数
- 泵控：`pump_port` `pump_baudrate` `pump_timeout` `pid_mode` `pid_precision` `spectro_sample_wait_timeout`
- Web：`web_host` `web_port` `web_ui`
- MAVROS：`mavros_timeout` `enable_mavros` `mavros_fcu_url` `mavros_gcs_url` `mavros_tgt_system` `mavros_tgt_component` `mavros_fcu_protocol` `mavros_respawn`
- MAVLink：`auto_trigger_on_waypoint` `trigger_waypoints` `hold_settle_time` `stable_check_timeout` `stable_speed_threshold` `stable_yaw_rate_threshold` `sampling_retry_count` `sampling_on_fail` `mavlink_source_system` `mavlink_source_component` `mavlink_router_url`
- 开关：`enable_pump` `enable_web` `enable_mavlink_trigger` `enable_mavlink_bridge`

## 3. ROS Topics
### 3.1 发布
- `/usv/pump_angles` `std_msgs/String`
- `/usv/pump_status` `std_msgs/String`
- `/usv/pump_pid_complete` `std_msgs/String`
- `/usv/pump_pid_error` `std_msgs/String`
- `/usv/injection_pump_status` `std_msgs/String`
- `/usv/spectrometer_voltage` `std_msgs/String`
- `/usv/spectrometer_status` `std_msgs/String`
- `/usv/spectrometer_raw` `std_msgs/String`
- `/usv/spectrometer_absorbance` `std_msgs/String`
- `/usv/spectrometer_command` `std_msgs/String`
- `/usv/mission_status` `std_msgs/String`
- `/usv/detection_result` `std_msgs/String`
- `/usv/trigger_status` `std_msgs/String`
- `/usv/automation_steps` `std_msgs/String`
- `/usv/bridge_diagnostics` `std_msgs/String`
- `/usv/mavlink_cmd_rx` `std_msgs/Float32MultiArray`
- `/usv/mavlink_cmd_ack` `std_msgs/Float32MultiArray`

### 3.2 订阅
- `/usv/pump_command` `std_msgs/String`
- `/usv/pump_step` `std_msgs/String`
- `/usv/spectrometer_command` `std_msgs/String`
- `/usv/mavlink_cmd_rx` `std_msgs/Float32MultiArray`
- `/usv/mavlink_cmd_ack` `std_msgs/Float32MultiArray`
- `/mavros/state` `mavros_msgs/State`
- `/mavros/mission/reached` `mavros_msgs/WaypointReached`
- `/mavros/local_position/velocity_local` `geometry_msgs/TwistStamped`
- `/mavros/imu/data` `sensor_msgs/Imu`

### 3.3 `/usv/mission_status` 语义
- 发布源：`src/usv_ros/scripts/mavlink_trigger_node.py`
- 当前阶段值：
  - `IDLE`
  - `NAVIGATING:<wp_seq>`
  - `WAYPOINT_REACHED:<wp_seq>`
  - `HOLDING:<wp_seq>`
  - `WAITING_STABLE:<wp_seq>`
  - `SAMPLING:<wp_seq>`
  - `SAMPLING_DONE:<wp_seq>`
  - `RESUMING_AUTO:<wp_seq>`
  - `SURVEYING:<interval_s>`
  - `HOLD_NO_MISSION:<wp_seq>`
  - `FAILED:<wp_seq>:<reason>`
  - `PAUSED:<wp_seq>`
  - `ABORTED:<wp_seq>`
- 用途：供 Web/QGC 判断自动采样任务当前所处阶段，而不再仅依赖 `pump_status`

## 4. ROS Services
- `/usv/pump_stop`
- `/usv/automation_start`
- `/usv/automation_stop`
- `/usv/automation_pause`
- `/usv/automation_resume`
- `/usv/injection_pump_on`
- `/usv/injection_pump_off`
- `/usv/spectrometer_start`
- `/usv/spectrometer_stop`
- `/usv/i2c_map_apply`
- `/usv/injection_pump_get_status`
- `/usv/pump_reconnect`
- `/usv/trigger_sampling`
- `/mavros/set_mode`

## 5. Web API
文件：`src/usv_ros/scripts/web_config_server.py`
- `GET /api/config`
- `POST /api/config`
- `POST /api/config/reset`
- `POST /api/mission/start`
- `POST /api/mission/stop`
- `POST /api/mission/pause`
- `POST /api/mission/resume`
- `GET /api/ui/debug`
- `GET /api/calibration/offsets`
- `POST /api/calibration/zero`
- `POST /api/calibration/reset`
- `POST /api/calibration/start`
- `GET /api/waypoint-sampling`
- `POST /api/waypoint-sampling`
- `GET /api/waypoint-sampling/<seq>`
- `POST /api/waypoint-sampling/<seq>`
- `DELETE /api/waypoint-sampling/<seq>`
- `GET /api/mission-config/export`
- `POST /api/mission-config/import`
- `POST /api/injection-pump/status`
- `POST /api/injection-pump/on`
- `POST /api/injection-pump/off`
- `POST /api/injection-pump/set`
- `POST /api/spectrometer/start`
- `POST /api/spectrometer/stop`
- `POST /api/spectrometer/baseline`: baseline must have a valid spectrometer sample; the current valid voltage becomes `reference_voltage`. `reference_voltage=0.0` means baseline is not set.
- `GET /api/hardware/config`
- `POST /api/hardware/config`
- `GET /api/hardware/serial-ports`
- `POST /api/hardware/test-pump-port`：请求字段 `serial_port` `baudrate` `timeout`；成功条件为串口打开且收到 `DET_ID:USV_DETECTOR*`。
- `POST /api/hardware/apply`
- `GET /api/diagnostics/link`
- `GET /api/diagnostics/history`
- `GET /api/diagnostics/events`
- `GET /api/diagnostics/export`


### 5.1 任务配置结构
- `GET /api/config` / `POST /api/config` 的任务配置包含：
  - `sampling_sequence.loop_count`
  - `sampling_sequence.steps[]`
  - `waypoint_sampling.<seq>.enabled`
  - `waypoint_sampling.<seq>.loop_count`
  - `waypoint_sampling.<seq>.retry_count`
  - `waypoint_sampling.<seq>.hold_before_sampling_s`
  - `waypoint_sampling.<seq>.on_fail`
- `POST /api/mission/start` 支持额外携带：
  - `sampling_sequence`
  - `waypoint_sampling`
- 语义：启动任务时，Web 可用请求体覆盖当前保存配置，然后下发至 `mavlink_trigger_node.py` / `pump_control_node.py`

### 5.2 自动化步骤等待语义
- 文件：`src/usv_ros/scripts/lib/automation_engine.py`、`src/usv_ros/scripts/pump_control_node.py`
- 顺序：`_send_step_command()` -> `_wait_for_step_execution()` -> `on_step_complete` -> `interval`
- `pump_control_node.py::_wait_for_automation_step()`：非 PID 电机估算等待；进样泵 `pump.duration_ms` 定时关闭；ADS `spectro_state=acquiring` 时等待 1 条新的 `valid=true` 分光包。
- 超时参数：`~spectro_sample_wait_timeout`，默认 `2.0s`。

## 6. Socket.IO 事件
### 6.1 后端发出
- `status`
- `angles`
- `pump_angles`
- `raw_angles`
- `voltage`
- `pid_error`
- `injection_pump_status`
- `log`
- `mavros_state`
- `bridge_diagnostics`

### 6.2 前端监听
文件：`src/usv_ros/frontend/src/store.ts`
- `status`
- `angles`
- `pump_angles`
- `raw_angles`
- `voltage`
- `injection_pump_status`
- `log`
- `mavros_state`
- `bridge_diagnostics`

## 7. MAVLink 指令与遥测
### 7.1 下行指令
文件：`src/usv_ros/scripts/usv_mavlink_router_bridge.py` 与 `mavlink_trigger_node.py`
- 接收：`usv_mavlink_router_bridge.py` 通过 TCP `router_url` (默认 `127.0.0.1:5760`) 直接监听 `COMMAND_LONG` (`msgid=76`)，绕过 MAVROS。
- 内部流转：网桥解析后通过 `/usv/mavlink_cmd_rx` (Float32MultiArray) 发给 `mavlink_trigger_node.py`。
- 指令范围：`31010..31019`
- 指令：`31010` `31011` `31012` `31013` `31014` `31015` `31016` `31017` `31018` `31019`
- 应答：触发节点执行后发布状态到 `/usv/mavlink_cmd_ack`，网桥封装为 `COMMAND_ACK` (`msgid=77`) 并通过 `router_url` 发送。
- `31014`：发布 `CALXYZA\r\n`
- `31015 MAV_CMD_USV_START_SURVEY`：`param1` 为走航采样间隔秒数，QGC 默认 `5`。
- `31016 MAV_CMD_USV_STOP_SURVEY`：停止走航采样。
- `31017 MAV_CMD_USV_SET_BASELINE`：`param1=0` 使用最新有效分光电压设 baseline；`param1>0` 使用显式参考电压；`param2..7=0`。
- `31018 MAV_CMD_USV_SPECTRO_START`：启动分光检测器信号采集；`param1..7=0`。
- `31019 MAV_CMD_USV_SPECTRO_STOP`：停止分光检测器信号采集；`param1..7=0`。

### 7.2 上行遥测
文件：`src/usv_ros/scripts/usv_mavlink_router_bridge.py`
- 连接：`router_url`，默认 `tcp:127.0.0.1:5760`
- 消息：`HEARTBEAT`、`NAMED_VALUE_FLOAT`
- 频率：`HEARTBEAT 1Hz`，载荷遥测 `2Hz`
- 字段：`USV_VOLT` `USV_ABS` `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` `USV_STAT` `USV_PKT` `USV_STEP` `USV_STOT` `USV_SCNT` `USV_PERR` `USV_PMOD` `USV_BSET` `USV_REF` `USV_BASE` `USV_VLD`
  - `USV_STEP`：当前自动化步骤号（float，整数编码）
  - `USV_STOT`：总步骤数（float，整数编码）
  - `USV_SCNT`：已采集样本计数（float，整数编码）
  - `USV_PERR`：PID 误差值（float）
  - `USV_PMOD`：PID 模式（float，0=空闲, 1=运行中, 2=已完成, 3=错误）
  - `USV_BSET`：baseline 是否已设置，`0/1`
  - `USV_REF`：reference voltage，单位 V
  - `USV_BASE`：baseline voltage，单位 V
  - `USV_VLD`：分光检测器当前采样是否有效，`0/1`
  - `USV_STAT=14`：`SURVEYING`，QGC 用于区分走航检测和普通采样

### 7.3 飞控转发
文件：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`ardupilot-usv/Rover/sensors.cpp`
- 接收缓存：`MAVLINK_MSG_ID_NAMED_VALUE_FLOAT`，缓存上述 17 个字段到 `rover.usv_payload`
- 转发函数：`Rover::usv_telemetry_send()`
- 调度：`SCHED_TASK(usv_telemetry_send, 2, 200, 132)`

### 7.4 QGC 显示
文件：`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`
- `voltage` <- `USV_VOLT`
- `absorbance` <- `USV_ABS`
- `pumpX/pumpY/pumpZ/pumpA` <- `PUMP_X/Y/Z/A`
- `status` <- `USV_STAT`
- `packetCount` <- `USV_PKT`
- `stepCurrent` <- `USV_STEP`
- `stepTotal` <- `USV_STOT`
- `sampleCount` <- `USV_SCNT`
- `pidError` <- `USV_PERR`
- `pidMode` <- `USV_PMOD`
- `baselineSet` <- `USV_BSET`
- `referenceVoltage` <- `USV_REF`
- `baselineVoltage` <- `USV_BASE`
- `spectrometerValid` <- `USV_VLD`
- `linkActive`：5 秒超时后置 0


## 8. 检测装置主控串口协议
文件：`DetFirmware/src/main.cpp`、`src/usv_ros/scripts/pump_control_node.py`、`src/usv_ros/scripts/web_config_server.py`、`MotorControlApp_Pyside6/src/ui/mixins/serial_mixin.py`、`MotorControlApp_Pyside6/src/core/serial_manager.py`
- 串口参数：`115200 8N1`，文本命令终止符 `\r\n`。
- 身份握手：`HELLO?\r\n` 或 `DET?\r\n` -> `DET_ID:USV_DETECTOR,FW=<version>,BAUD=115200`；上位机/ROS 端打开串口时预置并释放 `DTR=False/RTS=False`，握手阶段不主动复位下位机。
- ROS 连接：`pump_control_node.connect()` 打开串口后先执行 `perform_detector_handshake()`，失败则关闭串口并发布错误。
- Web 测试：`POST /api/hardware/test-pump-port` 执行同一握手，返回 `identity`。
- 命令确认：普通 `J/R` 电机命令解析后返回 `CMD_OK`；无法识别返回 `CMD_ERR:UNKNOWN`。
- Windows 上位机：`serial_mixin.open_serial()` 和 `serial_manager.connect_port()` 打开串口后执行 `_perform_handshake()`，失败则关闭串口并弹出错误。

- 通信任务：`TaskComms()` 空闲延迟 `COMMS_TASK_DELAY_MS=1ms`，PID/校准周期 `20ms`。
- 二进制上行：`0x55 0xAA` PID、`0x55 0xBB` 测试结果、`0x55 0xCC` 角度、`0x55 0xDD` 分光。


## 9. 运行目录
- 运行目录：`~/usv_ws/.usv_run/`
- PID：`roscore.pid` `mavlink_router.pid` `usv_system.pid`
- 日志：`logs/roscore.log` `logs/mavlink_router.log` `logs/usv_system.log`

## 10. 未包含
- 未包含 ROS2 运行链路。
- 未包含 `mission_coordinator_node.py` 在默认启动链中的调度说明。
- 未包含 `README.en.md` 的接口镜像文档。
