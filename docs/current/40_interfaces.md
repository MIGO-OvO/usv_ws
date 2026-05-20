# 接口速查

Updated: 2026-05-20

## ROS Launch

文件：`src/usv_ros/launch/usv_bringup.launch`

| 参数 | 默认 | 用途 |
|---|---|---|
| `pump_port` | `/dev/ttyUSB0` | 检测装置串口 |
| `pump_baudrate` | `115200` | 串口波特率 |
| `web_host` | `0.0.0.0` | Web 监听地址 |
| `web_port` | `5000` | Web 监听端口 |
| `mavros_fcu_url` | `udp://127.0.0.1:14550@` | MAVROS 连接 router UDP |
| `mavlink_router_url` | `tcp:127.0.0.1:5760` | 自定义 bridge 连接 router TCP |
| `mavlink_source_component` | `191` | companion component id |

## ROS Topics / Services

| 名称 | 类型 | 方向 | 说明 |
|---|---|---|---|
| `/usv/mavlink_cmd_rx` | `Float32MultiArray` | bridge -> trigger | `[cmd,param1,param2,target_sys,target_comp,src_sys,src_comp]` |
| `/usv/mavlink_cmd_ack` | `Float32MultiArray` | trigger -> bridge | COMMAND_ACK 队列 |
| `/usv/trigger_status` | `String` | trigger -> bridge/Web | 采样状态事件 |
| `/usv/mission_status` | `String` | trigger -> bridge | 状态码来源 |
| `/usv/pump_command` | `String` | trigger/Web -> pump | 下发检测装置文本命令 |
| `/usv/pump_status` | `String` | pump -> Web/trigger | 泵控和自动化状态 |
| `/usv/pump_angles` | `String` | pump -> bridge/Web | X/Y/Z/A 角度 |
| `/usv/spectrometer_voltage` | `String` | pump -> bridge/Web | 电压、吸光度、基线、有效位 |
| `/usv/bridge_diagnostics` | `String` | bridge -> Web | router bridge 诊断 |
| `/usv/radio_status` | `String` | bridge -> Web | RADIO_STATUS 电台链路 |
| `/usv/pump_reconnect` | `Trigger` | Web -> pump | 保存硬件配置后重连 |

## MAVLink Commands

| Command | 语义 | 主要处理 |
|---:|---|---|
| 31010 | 开始采样 | `mavlink_trigger_node.py` |
| 31011 | 停止采样 | `mavlink_trigger_node.py` |
| 31012 | 暂停采样 | `mavlink_trigger_node.py` |
| 31013 | 恢复采样 | `mavlink_trigger_node.py` |
| 31014 | 校准/`CALXYZA` | `mavlink_trigger_node.py` -> `/usv/pump_command` |
| 31015 | 开始走航采样 | `mavlink_trigger_node.py` |
| 31016 | 停止走航采样 | `mavlink_trigger_node.py` |
| 31017 | 设置分光基线 | `mavlink_trigger_node.py` |
| 31018 | 分光采集开始 | `mavlink_trigger_node.py` |
| 31019 | 分光采集停止 | `mavlink_trigger_node.py` |

## MAVLink Named Values

固件缓存字段：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`；固件转发：`ardupilot-usv/Rover/sensors.cpp`。

| 字段 | 含义 |
|---|---|
| `USV_VOLT` | 分光电压 |
| `USV_ABS` | 吸光度 |
| `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` | 四轴泵角度 |
| `USV_STAT` | 任务状态码 |
| `USV_PKT` | bridge 发送包计数 |
| `USV_STEP` | 当前自动化步骤 |
| `USV_STOT` | 自动化总步骤 |
| `USV_SCNT` | 采样计数 |
| `USV_PERR` | PID 误差 |
| `USV_PMOD` | PID 模式 |
| `USV_BSET` | 基线是否已设置 |
| `USV_REF` | 参考电压 |
| `USV_BASE` | 基线电压 |
| `USV_VLD` | 分光数据有效位 |
| `USV_SMPL` | 固件触发 ROS 定点采样 |
| `USV_SURV` | 固件触发走航采样开关 |
| `USV_DONE` | ROS 通知固件采样完成 |

## Web API / Socket.IO

入口：`src/usv_ros/scripts/web_config_server.py`。当前页面由 Flask 提供，实时数据由 Flask-SocketIO 推送。

关键能力：

- 硬件配置读写、串口测试、泵重连。
- 采样序列配置、任务配置导入导出。
- 自动化启动/暂停/恢复/停止。
- 分光基线设置与电压/吸光度实时推送。
- 航点采样配置 CRUD。
- 日志列表、日志读取、日志下载。
- 链路诊断、电台状态、bridge 诊断。

## 检测装置串口协议

| 项 | 当前值 |
|---|---|
| 默认串口 | `/dev/ttyUSB0` |
| 默认波特率 | `115200` |
| 握手命令 | `HELLO?\r\n`、`DET?\r\n` |
| 期望响应 | `DET_ID:USV_DETECTOR*` |
| 二进制帧 | 角度、PID、测试、分光数据 |
| 分光帧头 | `0xDD` |
| 文本命令示例 | `CALXYZA\r\n` |

串口协议变更必须同时核对 `DetFirmware/src/main.cpp` 与 `src/usv_ros/scripts/pump_control_node.py`。
