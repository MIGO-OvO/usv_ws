# 接口速查

Updated: 2026-06-19

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
| `enable_system_health` | `true` | 启动 Jetson/ROS/ESP32 健康聚合节点 |

## ROS Topics / Services

| 名称 | 类型 | 方向 | 说明 |
|---|---|---|---|
| `/usv/mavlink_cmd_rx` | `Float32MultiArray` | bridge -> trigger | `[cmd,param1,param2,target_sys,target_comp,src_sys,src_comp]` |
| `/usv/mavlink_cmd_ack` | `Float32MultiArray` | trigger -> bridge | COMMAND_ACK 队列 |
| `/usv/trigger_status` | `String` | trigger -> bridge/Web | 采样状态事件 |
| `/usv/mission_status` | `String` | trigger -> bridge | 状态码来源 |
| `/usv/automation_status` | `String(JSON)` | pump -> bridge/Web | 自动化运行、暂停、步骤和 PID 状态 |
| `/usv/pump_command` | `String` | trigger/Web -> pump | 下发检测装置文本命令 |
| `/usv/pump_status` | `String` | pump -> Web/trigger | 泵控和自动化状态 |
| `/usv/pump_angles` | `String` | pump -> bridge/Web | X/Y/Z/A 角度 |
| `/usv/spectrometer_voltage` | `String` | pump/trigger -> bridge/Web | 电压、吸光度、基线、有效位；实验模拟下由 trigger 发布液滴事件聚合值 |
| `/usv/lab_sim/sample_event` | `String(JSON)` | trigger -> Web | 实验定点采样液滴事件明细：`event_id`、`mode`、`droplets[]`、`mean`、`valid_count`、`quality_flags` |
| `/usv/lab_sim/command` | `String(JSON)` | Web -> lab_sim | 实验仿真控制：`config`、`start`、`stop`、`waypoints` |
| `/usv/lab_sim/status` | `String(JSON)` | lab_sim -> Web | 虚拟船位、航向、运行状态（latched） |
| `/usv/lab_sim/waypoint_reached` | `String(JSON)` | lab_sim -> trigger | 虚拟航点到达事件，不污染 `/mavros/mission/reached` |
| `/usv/detector_health` | `String(JSON)` | pump -> system/Web | ESP32 温度、heap、任务栈水位等 |
| `/usv/system_health` | `String(JSON)` | system -> Web/bridge | Jetson、ESP32、ROS 节点聚合健康状态 |
| `/usv/bridge_diagnostics` | `String` | bridge -> Web | router bridge 诊断 |
| `/usv/radio_status` | `String` | bridge -> Web | RADIO_STATUS 电台链路 |
| `/usv/pump_reconnect` | `Trigger` | Web -> pump | 保存硬件配置后重连 |

## MAVLink Mission Command

航线定点采样只使用 ArduPilot 原生 mission command：

| Command | 参数 | 语义 | 主要处理 |
|---:|---|---|---|
| 42702 `MAV_CMD_NAV_SCRIPT_TIME` | `param1=1`，`param2=1..255` 秒，`param3..6=0` | USV 定点采样，飞控发送 `USV_SMPL`，ROS 完成后回 `USV_DONE` | `ardupilot-usv/Rover/mode_auto.cpp`、`usv_mavlink_router_bridge.py` |

## MAVLink Manual Commands

| Command | 语义 | 主要处理 |
|---:|---|---|
| 31010 | 手动开始采样，不作为 mission item | `mavlink_trigger_node.py` |
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
| `USV_JTMP` | Jetson CPU/SoC 温度，单位 °C；未知为 `-1` |
| `USV_ETMP` | ESP32 内部温度，单位 °C；未知为 `-1` |
| `USV_JCPU` | Jetson CPU 使用率，单位 `%`；未知为 `-1` |
| `USV_JMEM` | Jetson 内存使用率，单位 `%`；未知为 `-1` |
| `USV_EHEAP` | ESP32 可用 heap 百分比，单位 `%`；未知为 `-1` |
| `USV_SMPL` | 固件在 `NAV_SCRIPT_TIME(param1=1)` 触发 ROS 定点采样 |
| `USV_SURV` | 固件触发走航采样开关 |
| `USV_DONE` | ROS 通知固件采样完成 |

## Web API / Socket.IO

入口：`src/usv_ros/scripts/web_config_server.py`。当前页面由 Flask 提供，实时数据由 Flask-SocketIO 推送。

关键能力：

- 硬件配置读写、串口测试、泵重连。
- 采样序列配置、任务配置导入导出。
- 自动化启动/暂停/恢复/停止。
- 分光基线设置与电压/吸光度实时推送。
- 数据中心跟随 `sampling_started` 自动建档，跟随 `sampling_stopped` / `survey_stopped` 停止记录。
- 航点采样配置 CRUD。
- 实验模式 Lab：`GET/POST /api/lab/config`、`POST /api/lab/start`、`POST /api/lab/stop`、`GET /api/lab/status`、`GET/POST /api/lab/water-area`、`POST /api/lab/mission`、`POST /api/lab/route/auto-scan`、`POST /api/lab/mission/import-qgc`。
- 污染物 surface：`GET /api/data/mission/<id>/surface`、`GET /api/map/live/surface`，支持 `metric`、`size`、`power`、`include_lab`、`download`。
- 日志列表、日志读取、日志下载。
- 链路诊断、电台状态、bridge 诊断。
- 系统健康：`GET /api/diagnostics/system`；Socket.IO 事件 `system_health`。

## 坐标 Schema v2

实验模式坐标统一使用 schema v2 双坐标对，源码：`src/usv_ros/scripts/lib/lab_sim/coordinates.py`、`src/usv_ros/scripts/web_config_server.py`。

- 实体结构：`{"coordinate_schema_version": 2, "wgs84": {lat,lng,alt?}, "gcj02": {lat,lng,alt?}}`。
- WGS-84 是计算、持久化、航行、距离、ENU、污染场和 surface 的唯一真源；GCJ-02 仅用于高德底图显示。
- Web 点击事件 `event.latlng` 标记 `input_crs=GCJ02` 提交；后端按迭代式 GCJ-02 -> WGS-84 反算得到真源，响应同时返回 `wgs84` 与 `gcj02`。
- QGC 导入读取航点的 `wgs84`；`POST /api/lab/route/auto-scan` 返回双坐标航点与 `water_snapshot_hash`，`preview=true` 只生成不保存。
- 旧版裸 `{lat,lng}` 配置按 GCJ-02 迁移到 schema v2，迁移幂等。
- 旧实验航线接口 `/api/lab/route` 已废弃，由上述 `/api/lab/*` 接口取代。

## 污染物地图职责边界

- 第一阶段污染物浓度计算、采样点质量标记、历史 GeoJSON、CSV 和 IDW 热力图 surface 均由 ROS/Web 承载：`src/usv_ros/scripts/web_config_server.py` 与 `src/usv_ros/frontend/`。
- QGC 第一阶段不显示污染物热力图；QGC 继续承担任务规划、手动/走航采样命令、载荷遥测和采样数据页入口。
- ArduPilot 只保留 mission script、`USV_SMPL/USV_DONE` 闭环和 `NAMED_VALUE_FLOAT` 载荷转发，不计算污染物浓度，不保存污染物历史数据，不生成热力图。
- DetFirmware 只输出 raw code、电压、吸光度、valid、基线和健康状态，不输出污染物浓度。

## 实验仿真液滴事件与科研导出

源码：`src/usv_ros/scripts/lib/lab_sim/`、`src/usv_ros/scripts/mavlink_trigger_node.py`、`src/usv_ros/scripts/web_config_server.py`。

- 模拟数据源下，每个定点采样生成一个有界液滴事件（`droplet_count` 截断到 `3..64`，默认 12）。事件聚合为一条记录：`/usv/lab_sim/sample_event` 发布 `droplets[]` 明细，`/usv/spectrometer_voltage` 发布聚合电压、吸光度、浓度。
- 持久化粒度：一个事件 = 一次写入 = 一个 `data_point`；`data_point` 携带 `sample_event_id` 与 `droplet_count`。`data_points` 数量等于事件数，不等于液滴数。
- 科研 surface 在版本化水域快照的 ENU 网格上生成 truth/reconstruction/error/voltage/absorbance/risk 六层，polygon 外严格 mask；`figure_export.export_surface_figure()` 导出 300 DPI PNG/TIFF、SVG/PDF 和 metadata（DPI 限 72..1200，尺寸 0.1..20 inch）。
- 这些计算只在 ROS/Web 承载；ArduPilot、DetFirmware、QGC 不参与液滴生成、surface 计算或科研绘图。

## 检测装置串口协议

| 项 | 当前值 |
|---|---|
| 默认串口 | `/dev/ttyUSB0` |
| 默认波特率 | `115200` |
| 握手命令 | `HELLO?\r\n`、`DET?\r\n` |
| 期望响应 | `DET_ID:USV_DETECTOR*` |
| 二进制帧 | 角度、PID、测试、分光数据、系统健康 |
| 分光帧头 | `0xDD` |
| 健康帧头 | `0x55 0xEE`，37 字节，1 Hz |
| 文本命令示例 | `CALXYZA\r\n` |

串口协议变更必须同时核对 `DetFirmware/src/main.cpp` 与 `src/usv_ros/scripts/pump_control_node.py`。

健康帧字段：`version`、`flags`、`timestamp_ms`、`uptime_s`、`temp_c_x10`、`cpu_freq_mhz`、
`heap_free`、`heap_min_free`、`heap_total`、`task_count`、`loop_stack_hwm`、`comms_stack_hwm`、
`sensors_stack_hwm`、`checksum`、`0x0A`。ROS 会换算为 `/usv/detector_health` JSON。
