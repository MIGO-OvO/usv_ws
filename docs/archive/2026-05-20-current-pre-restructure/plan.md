# 技术计划
Updated: 2026-04-25T15:46:29+08:00

## 1. 当前目标
- 纳入 `DetFirmware/` 检测装置主控固件架构说明。
- 修复固件串口命令响应慢：降低 `TaskComms()` 空闲延迟并增加命令确认。
- 增加检测装置串口身份握手：固件响应 `HELLO?`/`DET?`，ROS/Web 连接前校验 `DET_ID:USV_DETECTOR`。
- 同步 `docs/current/`。

## 2. 影响文件
- `DetFirmware/src/main.cpp`
- `src/usv_ros/scripts/pump_control_node.py`
- `src/usv_ros/scripts/web_config_server.py`
- `docs/current/overview.md`
- `docs/current/INTERFACE.md`
- `docs/current/plan.md`
- `docs/current/task.md`
- `docs/current/TREE.md`
- `docs/current/det_firmware_guide.md`

## 3. 受影响符号与范围
- `DetFirmware/src/main.cpp:DET_FIRMWARE_ID/COMMS_TASK_DELAY_MS/sendIdentity/TaskComms/parseCommand ~+24`
- `src/usv_ros/scripts/pump_control_node.py:perform_detector_handshake/connect ~+28`
- `src/usv_ros/scripts/web_config_server.py:test_pump_port ~+23/-4`
- `docs/current/*.md ~+120/-60`

## 4. 执行步骤
1. 审阅 `DetFirmware/src/main.cpp`、`i2c_mux.h`、`ads122c04.h`、`protocol_packets.h`。
2. 固件新增 `DET_ID` 握手响应与启动身份输出。
3. 固件 `TaskComms()` 空闲延迟改为 `1ms`，普通命令后返回 `CMD_OK`/`CMD_ERR:UNKNOWN`。
4. ROS 连接串口时执行 `HELLO?` 握手，失败即关闭串口。
5. Web 串口测试 API 执行同一握手。
6. 更新 docs/current 架构、接口、TREE、任务记录与新增固件说明。

## 5. 验收条件
- `python -m py_compile src/usv_ros/scripts/pump_control_node.py src/usv_ros/scripts/web_config_server.py -> rc=0`
- `diagnostics(DetFirmware/src/main.cpp, pump_control_node.py, web_config_server.py, docs/current/*.md)=0`
- `pio run`：当前 Windows 环境未安装 PlatformIO，记录为环境阻塞，不声明固件编译通过。
- Web 串口测试成功响应必须包含 `identity=DET_ID:USV_DETECTOR*`。

## 6. 回滚
```bash
git restore DetFirmware/src/main.cpp docs/current/overview.md docs/current/INTERFACE.md docs/current/plan.md docs/current/task.md docs/current/TREE.md docs/current/det_firmware_guide.md
cd src/usv_ros && git restore scripts/pump_control_node.py scripts/web_config_server.py
```

## remeber.plan.1
label=scope|fact=本轮新增 DetFirmware 为检测装置主控固件上下文|impact=docs/current 需从三端扩展为三端+检测装置主控|next=同步 overview/interface/tree

## remeber.plan.2
label=latency|fact=固件原 TaskComms 空闲延迟为 10ms 且普通电机命令无接收确认|impact=上位机无法区分串口排队/未识别/已执行|next=改为 1ms 并返回 CMD_OK

## remeber.plan.3
label=handshake|fact=现有 Web 测试只验证串口可打开|impact=用户无法确认 ttyUSB 是否为检测装置|next=固件+ROS+Web 使用 HELLO 握手闭环
