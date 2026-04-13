# ArduRover 固件说明
Updated: 2026-04-08T00:00:00Z

## 1. 范围
- 固件源码目录：`ardupilot-usv/`
- 车辆类型：`Rover`
- 目标控制器：Pixhawk 6C
- 构建环境：WSL Ubuntu

## 2. 当前固件实现
### 2.1 接收
文件：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`
- 在 `handle_message()` 中新增 `case MAVLINK_MSG_ID_NAMED_VALUE_FLOAT`。
- 解析字段：`USV_VOLT` `USV_ABS` `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` `USV_STAT` `USV_PKT`。
- 缓存位置：`rover.usv_payload.*`
- 首帧诊断：`GCS_SEND_TEXT(MAV_SEVERITY_INFO, "USV: first payload ...")`

### 2.2 调度
文件：`ardupilot-usv/Rover/Rover.cpp`
- 调度项：`SCHED_TASK(usv_telemetry_send, 2, 200, 132)`
- 当前调度频率：`2Hz`

### 2.3 转发
文件：`ardupilot-usv/Rover/sensors.cpp`
- 函数：`Rover::usv_telemetry_send()`
- 超时：`last_update_ms` 超过 `3000ms` 不发送
- 发送方式：`gcs().send_named_float()`
- 转发字段：`USV_VOLT` `USV_ABS` `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` `USV_STAT` `USV_PKT`

### 2.4 路由
文件：`ardupilot-usv/libraries/GCS_MAVLink/MAVLink_routing.cpp`
- 当前代码保留默认 `forward(in_link, msg)` 路径。
- 历史屏蔽 `NAMED_VALUE_FLOAT` 的分支已注释移除。

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
复制文件
```bash
cp build/Pixhawk6C/bin/ardurover.apj /mnt/d/usv_ws/
```

## 5. 刷写
- 复制文件
```bash
cp build/Pixhawk6C/bin/ardurover.apj /mnt/d/usv_ws/
```
- 使用 QGroundControl 的自定义固件刷写入口。
- 文档未包含自动刷写脚本。

## 6. 验证
### 6.1 SITL
文件：`ardupilot-usv/Tools/scripts/test_sitl_usv.py`
- 持续发送 8 个 `NAMED_VALUE_FLOAT` 字段。
- 用于验证飞控缓存与 QGC 面板显示。

### 6.2 真机
- `src/usv_ros/scripts/test_real_usv_serial.py` 已验证直接串口发送可在 QGC 面板显示数据。
- 当前主链路已切换到 `mavlink-routerd + usv_mavlink_router_bridge.py`。

## 7. 未包含
- 未包含参数导出文件。
- 未包含固件二进制版本管理流程。
- 未包含自动刷写或 CI 构建配置。