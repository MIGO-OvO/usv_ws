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
| `/usv/sampling_result` | `String(JSON)` | trigger -> bridge | FCU 结果：`source=fcu`、`sample_id`（整数 1..65535）、`outcome`、`reason`；非 latched |
| `/usv/sample_record` | `String(JSON)` | trigger -> 记录消费者 | 采样终态 SampleRecord：UUID sample_id、开始 GPS 快照、起止时间、光谱/水质；非 latched，详见 `80_sample_gps_binding.md` |
| `/usv/mission_status` | `String` | trigger -> bridge | 状态码来源 |
| `/usv/automation_status` | `String(JSON)` | pump -> bridge/Web | 自动化运行、暂停、步骤和 PID 状态 |
| `/usv/pump_command` | `String` | trigger/Web -> pump | 下发检测装置文本命令 |
| `/usv/pump_status` | `String` | pump -> Web/trigger | 泵控和自动化状态 |
| `/usv/pump_angles` | `String` | pump -> bridge/Web | X/Y/Z/A 角度 |
| `/usv/spectrometer_voltage` | `String` | pump/trigger -> bridge/Web | 电压、吸光度、基线、有效位；实验模拟下由 trigger 发布液滴事件聚合值 |
| `/usv/spectrometer_raw` | `String(JSON)` | pump -> Web | 原始分光帧；Web 在采样窗口打开期间写入 `data/missions/raw/<mission_id>/<sample_id>.jsonl` |
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
| USV_LOOP | 当前自动化循环（从 1 起） |
| USV_LTOT | 总循环数（无限循环为 0，QGC 显示 x/∞） |
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
| `USV_DONE` | 仅在匹配 ID 的 `succeeded` 或明确 `skipped` 结果后，ROS 通知固件结束采样等待 |

### FCU 采样结果约束

- 采样结果可附加 `sample_record`；其 UUID 与顶层 FCU 握手 `sample_id` 不同。真实采样默认要求有效 GPS 且源时间年龄 <=2 秒；开始冻结位置，结束不回填。Web sample_windows 保留旧字段并增加统一记录字段，详见 [采样 GPS 绑定](80_sample_gps_binding.md)。当前 MAVLink/QGC 不原子传输样本点，WQ_SAMPLE_POINT 仅为待三端实现的设计草案。

- `sampling_stopped` 只关闭 Web 记录生命周期，不再触发 `USV_DONE`。
- `outcome` 仅接受 `succeeded/failed/cancelled/skipped`。失败、取消、非 FCU 来源、ID 不匹配或非法结果均不放行。
- FCU 启动失败、执行失败按 `sampling_on_fail` 处理：HOLD/ABORT 请求 HOLD 且不放行；明确 SKIP 才发布 `skipped` 允许放行。主动取消不受 SKIP 策略影响。忙碌拒绝不会中断已有采样。
- 自动化正常结束为 `finished`，直接停止为 `stopped`，异常为 `failed`；不得把后两者解释成成功。
- bridge 先登记 ID 再发布触发；最近同 ID 重复触发不重启采样，终态结果只接受一次，新 ID 清除尚未发送的旧完成通知。
- safety1 固件对 `param1=1` 的采样脚本：超时或伴随遥测超过 3 秒未更新时停止当前导航输出并进入 HOLD，不自动放行；其他脚本保留原有超时语义。`param2=0` 对 USV 采样按 255 秒上限处理。
- ROS `set_mode` 在请求发送后最多等待 3 秒观测实际模式；`mode_sent` 不再等同于模式已生效。HOLD 不是原地定位保持，实际船态仍需实测。
- 人工 MANUAL/RTL 接管优先于迟到的旧采样失败；ROS 取消旧采样而不回切模式，飞控 `USV_FAIL` 只作用于当前 AUTO 中匹配的采样。非 USV 脚本进入失败不继承上一 USV 的超时状态。
- 新增控制事件 `USV_FAIL(sample_id)`：ROS 失败/取消通知飞控 HOLD；飞控超时也用同名事件通知 bridge 取消匹配采样。它不是第 23 个显示遥测字段。飞控只接受本 sysid、component 191 的载荷消息；bridge 只接受本 sysid、component 1 的飞控事件。
- `USV_DONE/USV_FAIL` 仍为有限传输重试，不具备端到端 ACK 或持久化交付；未引入飞控跨重启会话 ID。丢包时安全兜底是 HOLD，而不是宣称任务必定完成。FCU 仍不走旧 waypoint 自动重试路径。
- 更新必须停机并成套重启 trigger/bridge/pump；不得混用新旧版本进程。QGC 和飞控的命令号、22 个遥测字段保持不变。

### safety1 本地采样事务

- Web/trigger 经 `/usv/control_command` 的 `automation_start` 同步提交步骤、来源、`attempt_id`，FCU 来源另带 `sample_id`。泵控在同一控制锁内验证、装载、启动；失败不启动旧配置。
- 内部收尾使用 `automation_cleanup`，payload 带 `attempt_id`（可附 reason），在同一控制锁内校验归属并停止全部输出。结果回显 ID 和 `cleanup=stopped/failed/superseded`，仅无会话故障的 stopped 为成功；superseded 不触碰新 owner，失败锁存并停止 MCU 心跳续约。人工 31011/STOPALL 保持全局停止语义。
- `/usv/automation_steps` 的 `transaction_only=true` 消息仅供观察，不装载；普通步骤消息在自动化运行/暂停期间被拒绝。
- 启动必须消费一次新装载且未过期的 `attempt_id` 配置；旧 `/usv/automation_start` 不能直接重放无 owner 或已用过的配置。自定义 ROS 调试客户端也需提供 ID 并续约 owner。
- trigger 在同一 `/usv/trigger_status` 发布流中先发 `sampling_context:<JSON>`，再发 `sampling_started`；Web 以该上下文归档，不再从航点存在与否猜来源。
- 终态以 `/usv/automation_status.sampling_context` 的 attempt_id/source/FCU sample_id 关联；旧或无 ID 终态不能结束新 owned 采样。启动 ACK 前的匹配终态先缓存，启动获准后按 started→terminal 顺序处理；启动拒绝优先。
- Web 的记录窗口准备和终态清理使用同一生命周期锁；网络启动 RPC 不持此锁。拒绝/取消启动只回滚本次窗口和本次新建文件，不关闭既有 survey/lab 文件；全局停止先发硬件 RPC，再处理记录 I/O。
- 走航停止取消整个调度（含两次采样间隔），不会自动启动下一轮。明确恢复需要重新开始走航。
- `/usv/sampling_owner` 每秒续约本地 `attempt_id`；有 ID 的自动化超过 5 秒无匹配 owner 心跳则取消并锁存 `owner_lost`。旧 ID 心跳不续约新采样。Web 端以 2 Hz 续约自身启动的任务。
- 预启动进样绑定同一 attempt；走航采样间隔仍续约进样 owner，泵端在进样开启而引擎空闲时也检查 owner，避免孤儿进样。attempt ID 是关联标识，不是权限凭证。
- `STOP`、`STOPALL`、四轴旧停止文本、`manual_stop_all`、Web `/api/motor/stop` 均取消自动化并停止全部输出。重连先取消旧事务，禁止跨设备连接延续采样。
- 分光无效帧立即清除旧有效平均值；泵控和 bridge 默认 2 秒超时置无效，bridge 健康值超过 5 秒恢复未知。有效性与链路在线分别判定。

### safety1 Web 访问

- HTTP API 写操作默认允许船载热点/LAN 客户端无需登录直接调用。仅在进程环境 `USV_WEB_REQUIRE_AUTH=1` 时启用认证，所有 API 写操作（含本机）需要 `USV_WEB_CONTROL_TOKEN`（至少 16 字符）；缺失或过短时拒绝启动。仅设置 token 不启用认证，环境变更需重启 Web 服务；普通只读 API 仍无需认证。
- 支持 `Authorization: Bearer ...` 或 HTTP Basic（用户名 `operator`、密码为令牌）；浏览器可先访问 `/api/control/auth` 完成认证。令牌不写配置文件、不回传、不记录日志。
- 两种模式均拒绝跨源/跨站写请求；Socket.IO 使用同源默认值。默认模式允许任何可达客户端控制，同源检查不是身份认证；非可信网络或对外代理部署应显式启用认证并限制网络访问。
- HTTP Basic/Bearer 不提供传输加密。仅在受控网络使用，远程链路需 TLS/VPN；只读数据同样需要部署层访问隔离。

## Web API / Socket.IO

入口：`src/usv_ros/scripts/web_config_server.py`。当前页面由 Flask 提供，实时数据由 Flask-SocketIO 推送。

关键能力：

- 硬件配置读写、串口测试、泵重连。
- 采样序列配置、任务配置导入导出。
- 自动化启动/暂停/恢复/停止。
- 分光基线设置与电压/吸光度实时推送。
- 数据中心跟随 `sampling_started` 自动建档，跟随 `sampling_stopped` / `survey_stopped` 停止记录。
- 数据中心按 `sampling_started` -> `sampling_stopped` 生成 `sample_windows[]`；raw frame 不写入 mission JSON，只保存相对路径与摘要。
- 任务元数据采用同目录临时文件 + `fsync` + 原子替换；raw JSONL 周期同步并在窗口关闭时强制同步。正常结束状态为 `completed`，服务重启后未结束任务标记为 `interrupted`。
- 航点采样配置 CRUD。
- 采样窗口 API：`GET /api/data/mission/<id>/samples`、`GET /api/data/mission/<id>/sample/<sample_id>`、`GET /api/data/mission/<id>/sample/<sample_id>/raw?limit=2000&offset=0`、`POST /api/data/mission/<id>/sample/<sample_id>/manual-result`。
- 整任务归档：`GET /api/data/mission/<id>/archive` 下载 ZIP，包含任务 JSON、摘要 CSV、各采样窗口 JSONL 与原始帧 CSV。
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

safety1 成套更新要求：身份响应须包含 `CAP=WATCHDOG1`。上电禁止控制命令，先 `WATCHDOG:ARM`（先停止全部输出）再开始会话；ROS/Windows 每 500 ms 发 `WATCHDOG:KEEPALIVE`。超过 3000 ms 无心跳时停止 PID、校准、PID 测试、开环电机及进样泵，保持故障锁存。迟到心跳不解锁；重新连接/显式 ARM 后需重新发起任务。`STOPALL` 无条件停全部输出。诊断查询和停止命令不依赖 ARM。

分光状态 bit4 (`0x10`) 表示压力测试合成帧，bit0 清零；接收端同时检查 bit4，不能仅按 bit0 判有效。帧长度不变。ROS 不把测试帧写入真实采样窗口；Windows 标记为无效。该标记不同于 ROS Lab 的显式模拟数据源。

ROS/Windows 混合串口解析器均保留读取块末尾单独的 `0x55`，避免帧头跨读取边界时丢帧；联合黄金帧回归覆盖分片、坏校验与测试位。

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
