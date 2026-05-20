# ArduRover 固件说明
Updated: 2026-05-20T00:00:00+08:00

## 1. 范围
- 固件源码目录：`ardupilot-usv/`
- 车辆类型：`Rover`
- 目标控制器：Pixhawk 6C
- 构建环境：WSL Ubuntu

## 2. 当前固件实现
### 2.1 接收
文件：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`
- 在 `handle_message()` 中处理 `MAVLINK_MSG_ID_NAMED_VALUE_FLOAT`。
- 缓存字段：`USV_VOLT` `USV_ABS` `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` `USV_STAT` `USV_PKT` `USV_STEP` `USV_STOT` `USV_SCNT` `USV_PERR` `USV_PMOD` `USV_BSET` `USV_REF` `USV_BASE` `USV_VLD`。
- `USV_DONE` 只用于通知 `mode_auto.nav_script_time_done()`，不作为普通遥测缓存。

### 2.2 调度
文件：`ardupilot-usv/Rover/Rover.cpp`
- 调度项：`SCHED_TASK(usv_telemetry_send, 2, 200, 132)`。
- 当前转发频率：`2Hz`。

### 2.3 转发
文件：`ardupilot-usv/Rover/sensors.cpp`
- 函数：`Rover::usv_telemetry_send()`。
- 超时：`last_update_ms` 超过 `3000ms` 不发送。
- 发送方式：`gcs().send_named_float()`。
- 转发字段为上述 17 个载荷遥测字段。

### 2.4 路由
文件：`ardupilot-usv/libraries/GCS_MAVLink/MAVLink_routing.cpp`
- 当前代码保留默认 `forward(in_link, msg)` 路径。
- 历史屏蔽 `NAMED_VALUE_FLOAT` 的分支已注释移除；载荷遥测通过飞控缓存后 2Hz 受控重发。

## 3. 当前链路
### 3.1 进入飞控
`usv_mavlink_router_bridge.py -> mavlink-routerd -> /dev/ttyTHS1 -> 飞控`

### 3.2 飞控发往 QGC
`handle_message() -> rover.usv_payload -> usv_telemetry_send() -> gcs().send_named_float() -> 数传电台 -> QGC`

## 4. 构建步骤
```bash
wsl
cd /mnt/d/usv_ws/ardupilot-usv
git submodule update --init --recursive
./waf configure --board Pixhawk6C
./waf rover
```

输出文件：`ardupilot-usv/build/Pixhawk6C/bin/ardurover.apj`
