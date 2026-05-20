# 检测装置主控固件说明
Updated: 2026-04-26T19:55:14+08:00

## 1. 代码位置
- 固件目录：`DetFirmware/`
- 构建系统：PlatformIO
- 目标环境：`platform=espressif32`、`board=nodemcu-32s`、`framework=arduino`
- 入口文件：`DetFirmware/src/main.cpp`

## 2. 模块结构
- `main.cpp`：ESP32 初始化、串口命令解析、FreeRTOS 通信任务、步进电机控制、进样泵 PWM、PID 定位、校准、分光轮询。
- `i2c_mux.h`：TCA9548A 通道选择、MT6701 角度读取、`I2CMAP:*` 命令解析。
- `ads122c04.h`：ADS122C04 配置、启动/停止、原始码读取、电压换算、`ADSCFG:*` 命令解析。
- `protocol_packets.h`：二进制上行包定义：PID `0xAA`、测试结果 `0xBB`、角度 `0xCC`、分光 `0xDD`。

## 3. 串口协议
- 波特率：`115200`
- 文本命令终止符：`\r\n` 或 `\n`
- 身份握手：上位机发送 `HELLO?\r\n` 或 `DET?\r\n`，固件返回 `DET_ID:USV_DETECTOR,FW=<version>,BAUD=115200`
- 普通电机命令：`<Motor>E<Dir>V<rpm>J<angle>`，例：`XEFV5J90.000`
- PID 相对定位命令：`<Motor>E<Dir>R<delta>P<precision>`，例：`XEFR90.0P0.1`
- 校准命令：`CALX`、`CALY`、`CALZ`、`CALA`、`CALXYZA`、`CALSTOP`、`CALSTATUS`
- 进样泵命令：`PUMP:ON`、`PUMP:OFF`、`PUMP:SPD:<0-100>`、`PUMP:SET:<0-100>`、`PUMP:STATUS`
- 分光命令：`ADSCFG:*`、`ADSSTART`、`ADSSTOP`、`ADSSTATUS?`
- 角度流命令：`ANGLESTREAM_START`、`ANGLESTREAM_STOP`、`GETANGLE`

## 4. 运行任务
- Arduino `loop()`：Core 1，按 `MotorState` 输出步进脉冲。
- `TaskComms()`：Core 0，读取串口、解析命令、周期执行 PID/校准、发送角度/分光包。
- 通信任务空闲延迟：`COMMS_TASK_DELAY_MS=1`。
- PID/校准周期：`CAL_INTERVAL=20ms`。
- 任务看门狗：`TASK_WDT_TIMEOUT_SEC=5`；`loop()`、`TaskComms()`、`TaskSensors()` 已注册并周期喂狗。

## 5. 本轮修复
- 新增固件身份握手，解决“串口可打开但不能确认是否为检测装置”的问题。
- ROS `pump_control_node.py` 连接时必须通过 `HELLO?` 握手后才启动读取器和运行时配置。
- Web `/api/hardware/test-pump-port` 从“仅测试可打开”升级为“打开 + 握手识别”。
- Windows 上位机 `MotorControlApp_Pyside6` 串口连接时先握手，失败弹出错误并关闭串口。

- 固件普通命令解析后返回 `CMD_OK` / `CMD_ERR:UNKNOWN`，便于上位机判断命令已被固件接收。
- `TaskComms()` 空闲延迟由 `10ms` 改为 `1ms`，降低串口命令排队延迟。
- 串口输入长度限制：`MAX_COMMAND_LENGTH=160`，超长命令返回 `CMD_ERR:TOO_LONG` 并丢弃至换行。
- 电机开环速度/角度已钳位：`MAX_OPEN_LOOP_RPM=20.0`、`MAX_COMMAND_DEGREES=3600.0`。
- ESP32 任务看门狗已启用：`loop()`、`TaskComms()`、`TaskSensors()` 均注册。

## 6. 验证命令
```bash
python -m py_compile src/usv_ros/scripts/pump_control_node.py src/usv_ros/scripts/web_config_server.py
cd DetFirmware && pio run
```
