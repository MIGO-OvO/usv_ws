# 接口速查
Updated: 2026-04-13T13:34:06Z

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

## 2. Launch 入口
文件：`src/usv_ros/launch/usv_bringup.launch`

### 2.1 启动节点
- `pump_control_node`
- `web_config_server`
- `mavlink_trigger_node`
- `usv_mavlink_bridge`（实际脚本：`usv_mavlink_router_bridge.py`）

### 2.2 Launch 参数
- 泵控：`pump_port` `pump_baudrate` `pump_timeout` `pid_mode` `pid_precision`
- Web：`web_host` `web_port` `web_ui`
- MAVROS：`mavros_timeout` `enable_mavros` `mavros_fcu_url` `mavros_gcs_url` `mavros_tgt_system` `mavros_tgt_component` `mavros_fcu_protocol` `mavros_respawn`
- MAVLink：`auto_trigger_on_waypoint` `trigger_waypoints` `mavlink_source_system` `mavlink_source_component` `mavlink_router_url`
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
- `/usv/mavlink_cmd_rx` `std_msgs/Float32MultiArray`
- `/usv/mavlink_cmd_ack` `std_msgs/Float32MultiArray`
- `/mavros/state` `mavros_msgs/State`
- `/mavros/mission/reached` `mavros_msgs/WaypointReached`

## 4. ROS Services
- `/usv/pump_stop`
- `/usv/automation_start`
- `/usv/automation_stop`
- `/usv/automation_pause`
- `/usv/automation_resume`
- `/usv/injection_pump_on`
- `/usv/injection_pump_off`
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
- `POST /api/injection-pump/status`
- `POST /api/injection-pump/on`
- `POST /api/injection-pump/off`
- `POST /api/injection-pump/set`
- `GET /api/hardware/config`
- `POST /api/hardware/config`
- `GET /api/hardware/serial-ports`
- `POST /api/hardware/test-pump-port`
- `POST /api/hardware/apply`
- `GET /api/diagnostics/link`
- `GET /api/diagnostics/history`
- `GET /api/diagnostics/events`
- `GET /api/diagnostics/export`

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
- 指令：`31010` `31011` `31012` `31013` `31014`
- 应答：触发节点执行后发布状态到 `/usv/mavlink_cmd_ack`，网桥封装为 `COMMAND_ACK` (`msgid=77`) 并通过 `router_url` 发送。
- `31014`：发布 `CALXYZA\r\n`

### 7.2 上行遥测
文件：`src/usv_ros/scripts/usv_mavlink_router_bridge.py`
- 连接：`router_url`，默认 `tcp:127.0.0.1:5760`
- 消息：`HEARTBEAT`、`NAMED_VALUE_FLOAT`
- 频率：`HEARTBEAT 1Hz`，载荷遥测 `2Hz`
- 字段：`USV_VOLT` `USV_ABS` `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` `USV_STAT` `USV_PKT`

### 7.3 飞控转发
文件：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`ardupilot-usv/Rover/sensors.cpp`
- 接收缓存：`MAVLINK_MSG_ID_NAMED_VALUE_FLOAT`
- 转发函数：`Rover::usv_telemetry_send()`
- 调度：`SCHED_TASK(usv_telemetry_send, 2, 200, 132)`

### 7.4 QGC 显示
文件：`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`
- `voltage` <- `USV_VOLT`
- `absorbance` <- `USV_ABS`
- `pumpX/pumpY/pumpZ/pumpA` <- `PUMP_X/Y/Z/A`
- `status` <- `USV_STAT`
- `packetCount` <- `USV_PKT`
- `linkActive`：5 秒超时后置 0

## 8. 运行目录
- 运行目录：`~/usv_ws/.usv_run/`
- PID：`roscore.pid` `mavlink_router.pid` `usv_system.pid`
- 日志：`logs/roscore.log` `logs/mavlink_router.log` `logs/usv_system.log`

## 9. 未包含
- 未包含 ROS2 运行链路。
- 未包含 `mission_coordinator_node.py` 在默认启动链中的调度说明。
- 未包含 `README.en.md` 的接口镜像文档。