# 接口速查

Updated: 2026-10-23

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
| `/usv/payload_command` | `String(JSON)` | bridge -> trigger | `{executor, values:[cmd,param1,param2,target_sys,target_comp,src_sys,src_comp,request,session,tcp_session]}`，固定首次转发的执行实例；`recover_only:true` 只查询已知结果 |
| `/usv/payload_protocol` | `String(JSON)` | trigger -> bridge | `{version,executor,tcp_session,source_monotonic}`；回显已处理的 TCP 会话，供 bridge 安排结果恢复 |
| `/usv/mavlink_cmd_rx` | `Float32MultiArray` | bridge -> trigger | 旧 7 元飞控内部事件、无关联兼容 STOP；关联请求须经执行实例封装 |
| `/usv/mavlink_cmd_ack` | `Float32MultiArray` | trigger -> bridge | `[cmd,result,target_sys,target_comp,tcp_session]`，过滤旧 TCP 会话；兼容旧 4 元 ACK |
| `/usv/trigger_status` | `String` | trigger -> bridge/Web | 采样状态事件 |
| `/usv/sampling_result` | `String(JSON)` | trigger -> bridge/Web | 各 trigger 来源的 `attempt_id/source/outcome/reason` 最终结果；FCU 另带整数 1..65535 的 `sample_id`；非 latched |
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

### 命令完成条件（31010–31019）

“接单结果”与“动作完成”“输出停止确认”是三件事，不能互相冒充。标准 `COMMAND_ACK` 不带请求身份，只能作证据；关联判定只用 `USVE1` 事件的 session/request/command/sender。

| 命令 | 关联接单结果 | 动作完成条件 | 状态变化 | QGC 接单等待期限 | 后端重试 | 失败后恢复 |
|---:|---|---|---|---|---|---|
| 31010 | `request/accepted`＝启动准入通过 | 对应 `terminal`；进入采样仅证明执行 | `USV_STAT` 8→1/2 | 5s | 不自动 | 停止确认后按当前状态恢复；缺什么补什么 |
| 31011 | `request/accepted`＝本次 `STOPALL_OK` | accepted 即本次停止结果；当前新状态是恢复的补充证据 | `USV_STAT`→0/12 | 15s | 可重发，同身份只重放结果 | 通信锁可由本次结果及同步状态解除 |
| 31012 | `request/accepted` | 状态进入 11 是异步证据，不是接单条件 | `USV_STAT`=11 | 5s | 不自动 | 用 31013 或 31011 |
| 31013 | `request/accepted` | 状态回到 1/2 是异步证据 | `USV_STAT`=1/2 | 5s | 不自动 | 失败用 31011 |
| 31014 | `request/accepted` | 对应 `terminal` | `USV_STAT`=4 | 5s | 不自动 | 31011 → 重新校准 |
| 31015 | `request/accepted` | 每个 attempt 一个 `terminal`；成功样本不结束调度 | `USV_STAT`=14 | 5s | 不自动 | 31016 或 31011 |
| 31016 | `request/accepted`＝走航停止结果 | 关闭走航调度并清理其采样；无走航时幂等成功 | `USV_STAT`→0/9/12/13（活动走航） | 15s | 可重发 | 不证明无关泵输出已停止，不能解除通信锁 |
| 31017 | `request/accepted`＝基线命令成功 | `USV_BSET` 新序号（异步证据） | `USV_BSET`=1 | 5s | 不自动 | 等待有效帧后重设 |
| 31018 | `request/accepted`＝启动命令成功（配置回显 + `ADS_OK:START`） | 首帧、基线另按真实测量判断 | `USV_ADS` 2→3 | 40s | 不自动 | 无帧时按测量状态处理，不锁船 |
| 31019 | `request/accepted`＝本次 `ADS_OK:STOP` | accepted 即分光停止结果 | `USV_ADS`=1 | 15s | 可重发 | ADS-only 不证明泵已停止 |

关联 `accepted` 就是该命令的接单答案：QGC 收到后结束发送等待，`pendingCommand` 清零，之后只按 ROS 当前状态与任务结果更新界面。`31010/31014/31015` 的 accepted 只表示任务已受理，不表示任务完成；`31011/31016/31019` 的 accepted 就是本次停止结果；`31018` 的 accepted 只表示启动命令成功，首帧与基线仍由 `USV_VLD`/`USV_BSET` 异步决定。

关联 USVE1 同时结束原生队列和 QML 收执等待；按钮直接绑定原生 `pendingMavCommands` 通知。标准 ACK 不释放或续期关联请求，迟到旧 ACK 无法清除后续同 command 的新请求。接单超时显示“响应超时”，保留停止入口、任务身份与后续状态，不设置整船锁，也不创建新 START 请求。

Web `/api/calibration/start` 与 QGC 31014 统一调用泵节点 `calibration_start`，从 Web 保存的 `calibration.json` 读取所选轴零点，使用新鲜原始角度计算最短相对 R/PID，逐轴真实 PID_DONE 后完成。缺失标定或过期角度拒绝运动，失败/取消沿用 STOPALL_OK 核验。独立回零只做 PIDQUERY 屏障与回零；自动化仍保留回零、正转360°补偿、油相分隔。Web 修改零点后立即更新快照，bridge 每次发送显示帧重读同一文件，内部原始角度不扣偏移。

`status` 的接收序号是客户端计数，`USV_STAT` 数值不变也会递增，因此“收到一帧 Idle”本身不能证明某个任务已经结束。旧任务自动进入历史必须有自己的结束依据，且该依据必须早于用来判定的那帧 Idle：

| 结束依据 | 收敛条件 |
|---|---|
| 本请求的 `terminal` | 其后的新 Idle 使任务进入历史（原因保留）；`31015` 单次 attempt 的 `succeeded` 不算整体结束 |
| 实际观察到运行（如 `USV_STAT` 进入采样/走航） | 其后的新 Idle 表示这次运行已经停下 |
| 发送时针对该任务的 STOP 真实 accepted 结果 | `31011` 可收敛输出任务；`31016` 仅收敛走航；需在该停止结果之后收到新 Idle |
| 完全没有回执的请求 | 超时与同值 Idle 均不能单独证明结束；仍需运行后回空闲、终态或对应停止结果 |

尚未被受理、没有终态、也没有停止结果的新 START：同值 Idle 不得结束接单等待、不得标记 `retired`、不得清空当前任务，也不得放行另一项互斥物理任务。只有确实结束或已确认停止的旧请求，其迟到事件才只进入历史。

31016 后紧接 31019（前者尚无 ACK/accepted）是受支持的重叠操作。STOP 发送时保存原物理任务的请求引用，以既有 `sameRequest()` 比较 Vehicle、session、request、command 和发送方身份；走航调度身份不等于其中一次采样的 `attempt_id`。

STOP 无论仍为当前请求还是已进入 history，合法 accepted 都先写回自己的记录，再按命令范围给发送时目标任务建立停止依据。使用结果到达时的 `evidenceStatus`，之后收到符合规则的新静止状态才退休该任务；结果以前收到的 Idle 不作证明。历史 STOP 不改写当前请求的提示、pending 或结果；目标已结束、后来启动了新任务时，旧 STOP 不能作用于新任务。`31019` 单独成功只证明分光停止，不能结束走航占用、证明全泵停止或解除输出未知锁。

已退休且 `cleanup_failed=false` 的普通失败继续保留终态、原因、阶段和请求身份，但不再由 `activeFailure()` 占据新任务的 `feedback/warning/taskFailed`；新任务按自己的发送、accepted、progress 和终态显示。尚未解除的 `cleanup_failed`、输出停止未知与主动急停保留原限制，不清空 history、不伪造 `physicalStopVerified`，也不在新 START 时清除 Vehicle 锁。

无关联身份的历史 STOP 只能按“兼容停止”降级处理：只用匹配 Vehicle/组件/命令的唯一在途标准 ACK 判定。`ACCEPTED` 保存到该请求并结束等待，`IN_PROGRESS` 继续等待，明确失败保留失败；后续遥测不得重新要求不会出现的 USVE1，也不得抹掉失败。`31019` 只表示分光范围。已退休（`retired`）请求的迟到 accepted/progress/terminal 只更新历史，不得重开等待、覆盖已核验标志、覆盖已有终态或影响新任务。

## MAVLink Named Values

QGC 只保留接单等待（`31018` 40 秒、停止类 `31011/31016/31019` 15 秒、其余 5 秒），不存在执行静默窗或 progress 续期。accepted 或合法关联 progress 结束接单等待，后续按设备状态及任务事件更新。超时只提示“未收到回执”，迟到合法结果仍按身份归属。

启动与停止的成功含义不同：`31018` 的关联 `request/accepted` 只表示启动命令成功（配置回显 + `ADS_OK:START`），有效帧与基线异步决定“采样就绪”；没有首帧不得把已成功的启动命令改判为未响应或锁定整船。`31011` 需本次 `STOPALL_OK`；`31016` 仅在走航拥有采样时要求该 attempt 的停止清理，无走航或尚未拥有采样时可本地幂等成功；`31019` 需本次 `ADS_OK:STOP`。不能把 `31016` 的无操作成功写成全输出物理确认。

`31016` 仅在存在活动走航或普通通道已受理 `31015` 时推进现有 cancellation generation；通道记录涵盖已入队尚未执行的命令。走航正式激活、发布 `survey_started` 和启动 scheduler 与 STOP 准入共用 `_command_dispatch_lock`：STOP 先取消则旧 START 不激活；START 先激活则 STOP 能观察并关闭。无走航的 `31016` 不取消独立 `31018`。满队列拒绝及同身份重放不推进 generation。

ROS bridge 启动后立即发送 component 191 心跳，trigger 的 MAVROS 服务初始化不阻塞采样 owner 续约。自动化准备期间使用现有 `USV_STAT=8`（准备/稳定等待），QGC 主动作提供停止准备，准备结束后进入采样状态才可暂停。QGC 手动点采样采用 Web 自动进样泵策略的速度，进样泵在准备完成后开启。

固件缓存字段：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`；固件转发：`ardupilot-usv/Rover/sensors.cpp`。

| 字段 | 含义 |
|---|---|
| `USV_VOLT` | 分光电压 |
| `USV_ABS` | 吸光度 |
| `PUMP_X` `PUMP_Y` `PUMP_Z` `PUMP_A` | 保存零点下的相对角度 `[0,360)`；未校准为 -1，QGC 显示“未校准”（Web 使用 null） |
| `USV_STAT` | 任务状态码 |
| `USV_PKT` | bridge 发送包计数 |
| `USV_STEP` | 当前自动化步骤 |
| `USV_STOT` | 自动化总步骤 |
| USV_LOOP | 当前自动化循环（从 1 起） |
| USV_LTOT | 总循环数（无限循环为 0，QGC 显示 x/∞） |
| `USV_SCNT` | 采样启动次数，不是成功次数 |
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
| `USV_ADS` | 0 未知、1 停止确认、2 启动中、3 采集中、4 错误、5 停止未确认 |
| `USV_PROTO` | 当前关联请求协议版本 1；过期/未知不得开放新动作 |
| `USV_SMPL` | 固件在 `NAV_SCRIPT_TIME(param1=1)` 触发 ROS 定点采样 |
| `USV_SURV` | 固件触发走航采样开关 |
| `USV_DONE` | 仅在匹配 ID 的 `succeeded` 或明确 `skipped` 结果后，ROS 通知固件结束采样等待 |

### 停止结果、恢复与准备门禁

准备流程的测量门禁按阶段划分，避免把“测量暂不可用”当成“泵控制失效”：

| 阶段 | 必需条件 |
|---|---|
| 启动准入（31010/31015 接单） | 当前会话真实有效帧 + 基线 + 串口会话 |
| 归零 → 360° 补偿 → 油相 X 圈 → 进样预启动 | 串口会话、取消请求、真实泵角度反馈、PID 完成、owner 心跳；**不要求**测量新鲜 |
| 交接给正式采样（preflight `verifying`） | 再次确认当前会话真实帧 + 基线；stale 但不能证明有效的数据不足以进入正式采集 |

`ADS_OK:START` 只确认启动命令，不写入最后有效测量时间；首帧前 `spectro_state=starting` 且 `USV_VLD=0`。首帧宽限为 `max(measurement_timeout, 4s)`，超时按 `spectrometer_frame_timeout` 处理。

分光测量错误（如帧中的 I2C 错误、未配置或测试数据）先使测量失效；只有当前阶段需要测量时，才锁存分光故障并通知原 worker 终止及停止清理。机械 PRE 不因分光测量不可用而取消，正式交接仍重验真实帧和基线。控制串口读写故障则取消当前动作、锁存断线并进入重连与停止清理；串口不可用时不能声称输出已取得物理停止确认。二者不是同一个故障范围。

停止结果只依据**本次**停止动作与本次确认，历史 `terminal_reason`、历史 `cleanup_failed`、已处理的分光故障不再否决本次成功停止。本次 `STOPALL_OK`（来自本次有效串口会话且经 `PIDQUERY` 排空旧回复）确认后清除可恢复锁存并发布当前静止状态，同时保留历史失败原因：

| 可恢复（确认停止后清除） | 需各自恢复条件（停止不清除） |
|---|---|
| `cleanup_failed`、`spectrometer_*`（分光会话类） | `disconnected`、`reconnecting`、`owner_lost`、`watchdog_tripped`、校准失败 |

分光停止与全输出停止是两个范围，分别报告：`spectrometer_stop` 返回 `ads_stop` 与 `outputs_stop`，只有本次确实停止并确认了对应范围才为真。只发送 `ADSSTOP` 时 `outputs_stop` 为假（即使当时没有自动化任务，手动进样泵仍可能在运行），`ads_stop` 由 `ADS_OK:STOP` 单独证明，仅停分光成功仍让该命令自身成功。`USV_STAT` 在明确 `stopped` 且无进行中任务时回到 `0`（空闲），历史失败仅通过 `terminal_reason`/请求日志查看。

各 STOP 的范围（不要互相代替）：

| 命令 | 停止范围 |
|---:|---|
| 31011 | 按现有契约停止采样及相关输出（本次 `STOPALL_OK` 确认） |
| 31016 | 停止走航调度及其对应采样 |
| 31019 | 仅停止分光；若触发采样清理，清理结果单独按真实结果表达 |

`owner_lost`、`watchdog_tripped`、串口断开等实际故障不被“清除状态”伪装成健康：本次 STOP 是否成功与该故障分别表达，恢复条件各自保留。

后台分光新鲜度检查与前台准备共用同一“当前阶段是否依赖测量”的判断：机械准备（归零、360°、油相 X 圈、进样预启动）期间分光短暂无帧只更新分光状态，不会升级为 `_controller_fault`，也不会取消准备；只有正式采集阶段才按既有业务规则结束或暂停本次采样。

测量快照在读取测量值时一并捕获取消 token、`attempt_id` 和当时需要测量的 owner（机械 PRE 为 None），之后才取比较时钟。产生 stale、数据失效或停止副作用之前，重验串口对象、`start_ack_at`、`last_valid_at`、分光状态、显式故障、任务 token/attempt 与阶段归属；任何变化均放弃旧结论。这样既保护替换任务，也保护同一 runtime 的新帧与聚合状态。重验、状态提交与停止认领使用 `_control_lock → serial_lock`；阻塞 ACK 确认及 join 前释放 `serial_lock`，并以 finally 完成 STOP 收尾。快照函数本身不获取 `_control_lock`。

QGC 侧的三类信息严格分开：

| 信息 | 内容 | 作用 |
|---|---|---|
| 本次命令 | 发送中、已接受、被拒绝、未收到回执 | 只控制本次发送等待 |
| 当前设备状态 | 空闲、准备、运行、暂停、当前故障、分光就绪 | 决定当前可用的操作入口 |
| 历史任务结果 | 上次成功、失败、取消及原因 | 展示历史，不再锁住当前操作 |

回执超时、状态稍晚、分光暂无数据、基线失败、命令被拒绝、失败但已确认停止只影响本请求或历史。任务可能仍在运行且整条 MAVLink 连接断开时，Vehicle 原锁记录来源 `communication`；`cleanup_failed` 为 `outputs`，主动急停为 `emergency`。来源与原 Vehicle 锁共享生命周期，通信丢失不能覆盖已有急停/输出停止未知来源。

通信恢复后，新发出的有关联身份 `31011` 取得本次 accepted（真实 `STOPALL_OK`）、其传输 pending 已结束，且随后收到新的当前空闲状态时，自动解除通信锁并退休旧任务/请求。保持 armed 也可恢复分光准备；不自动 arm/disarm，不改模式，不宣称推进停止。仅重连、Idle、断连前 STOP 的迟到结果、`31019` 或无走航 `31016` 均不足以解锁；仅 ROS 载荷离线而飞控连接仍在线不新增整船锁。主动急停与未确认输出停止保留原飞控 disarm 和现场勾选核验流程。

bridge 诊断 JSON 增加只读字段 `bad_data`（按 `bad_crc`/`unknown_message_id`/`bad_length`/`bad_signature`/`other` 分类的计数）与 `bad_data_last_reason`。已拒绝的入站帧只计数，不重连、不清账本、不执行其 payload 内部字节。

### 关联请求与逐字段新鲜度

常规显示遥测共 26 项；`USV_SMPL/SURV/DONE/FAIL` 是控制事件，不计入显示字段数。ROS 按源回调与字段年龄发送，失效 VLD/BSET/ADS 发 0；飞控每字段 3 秒 TTL、各链路独立游标、txspace 不足时不推进待发字段。QGC 同值重发也增加字段接收序号，5 秒本地 TTL 不是原测量时间。

`COMMAND_LONG 31010..31019` 的 param3=request、param4=session，均为 1..16777215 的精确整数，param1/2 不变。QGC 用文件计数器分配身份，ROS 只在内存里做会话内去重与结果重放。同身份同参数重传保留原事件、原 seq/attempt_id/结果，不执行 handler、不重新入队、不推进 generation；ACK 根据缓存事件的阶段返回：

| 缓存事实 | 重放标准 ACK |
|---|---|
| 在途，尚无事件；或 `phase=progress` | `IN_PROGRESS`（5） |
| `request/accepted` | `ACCEPTED`（0） |
| `request/rejected` | `TEMPORARILY_REJECTED`（1） |
| `terminal/succeeded` | `ACCEPTED`（0） |
| 实际 failed/cancelled | 原失败语义 `FAILED`（4） |

同身份不同参数明确拒绝且不破坏原记录；已拒绝身份即使通道空闲也继续重放拒绝。JSONL 仅为尽力写入的诊断日志，不参与准入、STOP 或通道释放。trigger capability 含本次进程的 executor（32 位 hex）；bridge 用 RequestLedger 固定请求归属并通过内部封装携带。trigger 重启但 bridge/TCP 未重连时，旧请求返回 `executor_restarted`；即使新 capability 尚未到 bridge，trigger 也拒绝旧实例封装。不能跨执行实例续跑；恢复须同步设备状态。旧协议仅允许尝试停止。

ROS 以 source=本 sysid/191 发送 MAVLink2 STATUSTEXT `USVE1:` + ASCII JSON（最多 750 字节），携带 v、session、request、seq、command、sender_system/component、tcp_session、phase、outcome、reason、完整 attempt_id 和 preflight_phase，可附 cleanup_failed。飞控原样转发 id/chunk_seq/source；QGC 仅使用完整重组消息，1 秒绝对组包期限，缺片/冲突不产生机器事件。标准 ACK 不携带 request 身份；任务成功必须是关联终态。comp191 关联请求以 1 秒间隔最多发送三份原身份/参数帧；普通总预算 5 秒、STOP 15 秒、31018 40 秒，末次发送保留剩余等待预算。仅载荷链路使用此策略；受理结束重传，物理任务继续由进度和终态更新。

普通 progress 的 `outcome` 为 `""`，`state` 可为 `running`。身份、attempt 和序号均合法的执行进度可证明已进入执行，不要求更早 accepted 必须送达；不能据此声称任务成功。bridge 保留每请求一个重要未发送转换及最新 progress，终态覆盖旧证据；缓存最多 32 请求，已发历史保留 30 秒，未发送转换保留至发送或容量淘汰。发送优先级为 STOP、新终态、其他新转换、历史重播；容量压力优先淘汰已发历史/普通待发，不能用历史重播拖延新请求首发。全安全回执超载仍受容量限制，请求端须保守处理未知状态。

TCP 每轮发送共用 30 ms 预算，从接收处理结束后开始。当前帧尚无字节写入时，预算耗尽或暂时背压只延期，ACK/结果/分片在完整写入后出队。部分帧无法完成、零写入、EOF 或实际 socket 错误仍退役会话并触发停止。USVE1 跨轮续发保留 chunk id 和偏移；完整 MAVLink 帧之间若有更高优先级事件，或已超过 QGC 既有 1 秒组包期限，则重新调度。STOP 可先于旧普通长事件发送；被中断事件保留原请求身份、seq 和内容，下次从 chunk 0 用新 id 重播。已部分写入的帧必须先完成，否则退役会话，不能插入其他帧。续发期间普通文本日志等待。

会话退役的取消首因是 `transport_session_lost`，贯通关联终态与采样结果。手动与 FCU 启动在创建采样上下文时就绑定关联请求，并在同一状态锁内发布上下文与采样状态；位置绑定期间发生断线也能归结到原请求，清理完成后启动线程不会恢复采样标志。bridge 在新会话得到 trigger capability 回显后，只对原先保存的请求发送 `recover_only` 查询；执行器、sender/session/request、command 与参数全部匹配后，RequestLedger 才绑定新回执会话。缓存终态立即重放；尚在清理的请求随后在已验证的新会话发布终态。同身份网络重试使用相同校验。查询未知身份或参数冲突不执行动作，旧执行器身份仍拒绝；旧会话事件继续过滤，恢复不推进执行 generation，不重做 START。

定位入口：bridge `Payload command rx/route` 记录请求身份、目标、MAVLink seq、confirmation、TCP 会话和执行实例；`USVE1 tx` 记录事件序号、chunk id/seq 和发送偏移。`/usv/bridge_diagnostics` 含 received_bytes、deferred_frames、短写/背压、最近写入偏移、待发数量、命令分支计数和 BAD_DATA 的分类/有限原始字节前缀。BAD_DATA 头部提示未经校验，只用于诊断。QGC `Vehicle.Vehicle` 记录命令发送，`MAVLink.StatusTextHandler` 记录每片与组包结算，不调整路由策略或组包期限。

trigger 的每个已识别请求都必须有明确结果：通道繁忙时除 `TEMPORARILY_REJECTED` 标准 ACK 外，还会立刻产生与请求身份关联的 `phase=request, outcome=rejected, reason=command_lane_busy`，直接走已有发布路径，不再需要单独的持久化拒绝线程，因此不会出现“无人负责、无结果、重试又被静默吞掉”的 reservation。STOP 不被普通通道占用阻挡，在有界安全通道中串行执行；安全队列满时明确拒绝，且不推进 cancellation generation。同身份重传重放既有结果，各个已受理请求保留自己的结果；STOP 的执行、回执与通道释放都不等待日志落盘。后端拒绝时 `request/failed` 的 `reason` 保留控制服务的具体消息（例如 `spectrometer_not_ready: ...`），不再统一压成 `command_rejected_or_cancelled`。

请求日志（`~command_ledger`，默认 `~/.ros/usv_payload_requests.jsonl`）只是诊断轨迹：目录不可写、文件被关闭或写入抛 `OSError` 时仅记录一次告警并继续运行，不影响命令受理、STOP 或通道释放，也不会触发任何控制维护锁。日志只记录已产生的请求与结果，不生成身份、seq 或唯一回执。

飞控逐链路独立游标继续适用，同时跳过 private、不活动及启用宏下的 high-latency 链路；这是既有链路策略，不代表普通 TELEM2 离线原因。

### FCU 采样结果约束

- 采样结果可附加 `sample_record`；其 UUID 与顶层 FCU 握手 `sample_id` 不同。GPS 可选；存在新鲜有效定位时冻结起点，缺失时记录空坐标且结束不回填。真实测量/基线门禁仍强制。Web sample_windows 保留旧字段并增加统一记录字段，详见 [采样 GPS 绑定](80_sample_gps_binding.md)。WQ_SAMPLE_POINT 仍未实现。

- `sampling_stopped` 不触发 `USV_DONE`；Web 关窗还需匹配 attempt 的最终结果，避免 pump finished 早于 trigger 清理失败。
- `outcome` 仅接受 `succeeded/failed/cancelled/skipped`。失败、取消、非 FCU 来源、ID 不匹配或非法结果均不放行。
- FCU 启动失败、执行失败按 `sampling_on_fail` 处理：HOLD/ABORT 请求 HOLD 且不放行；明确 SKIP 才发布 `skipped` 允许放行。主动取消不受 SKIP 策略影响。忙碌拒绝不会中断已有采样。
- 自动化正常结束为 `finished`，直接停止为 `stopped`，异常为 `failed`；不得把后两者解释成成功。
- bridge 先登记 ID 再发布触发；最近同 ID 重复触发不重启采样，终态结果只接受一次，新 ID 清除尚未发送的旧完成通知。
- safety1 固件对 `param1=1` 的采样脚本：超时或伴随遥测超过 3 秒未更新时停止当前导航输出并进入 HOLD，不自动放行；其他脚本保留原有超时语义。`param2=0` 对 USV 采样按 255 秒上限处理。
- ROS `set_mode` 在请求发送后最多等待 3 秒观测实际模式；`mode_sent` 不再等同于模式已生效。HOLD 不是原地定位保持，实际船态仍需实测。
- 人工 MANUAL/RTL 接管优先于迟到的旧采样失败；ROS 取消旧采样而不回切模式，飞控 `USV_FAIL` 只作用于当前 AUTO 中匹配的采样。非 USV 脚本进入失败不继承上一 USV 的超时状态。
- 控制事件 `USV_FAIL(sample_id)`：ROS 失败/取消通知飞控 HOLD；飞控超时也用同名事件通知 bridge 取消匹配采样。它不计入 26 个显示遥测字段。飞控只接受本 sysid、component 191 的载荷消息；bridge 只接受本 sysid、component 1 的飞控事件。
- `USV_DONE/USV_FAIL` 仍为有限传输重试，不具备端到端 ACK 或持久化交付；未引入飞控跨重启会话 ID。丢包时安全兜底是 HOLD，而不是宣称任务必定完成。FCU 仍不走旧 waypoint 自动重试路径。
- 更新必须停机并成套重启 trigger/bridge/pump；不得混用新旧进程。命令号不变，当前显示字段为 26 项；必须配套更新飞控和 QGC。

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
- 当前 owner/attempt 的可信 preflight 停止（`PUMP:OFF`、轴 `DFV0J0`）不等待测量；旧 owner 仍不得停止新任务。恢复进样 lead 后，在最终新运动串口写入边界重验当前测量、取消、连接会话与 owner。
- 普通短静默保留既有有界恢复窗口；明确 I²C/饱和等错误立即失效并记录首因、通知任务线程安全收尾，不能被 freshness 检查覆盖成普通 stale。reader 不同步等 ACK；新帧不能自动清故障或续泵。

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
- 数据中心跟随 `sampling_started` 自动建档；trigger 来源的真实窗口需匹配 `/usv/sampling_result` 后关窗，`sampling_stopped` / `survey_stopped` 不替代最终结果。Web 直接启动仍使用匹配自身 attempt 的自动化终态。
- 数据中心按开始上下文与关联终态生成 `sample_windows[]`；raw frame 不写入 mission JSON，只保存相对路径与摘要。
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

DetFirmware `2026.10.25-pid-phases1` 的单次 PID 总上限为 600 秒；首次进入剩余解环误差 10° 后，独立计时 180 秒收敛，两项期限先到者生效。每轴只进入收敛一次，往返纠偏和其他轴完成不重置期限。`PID_SETTLE:<轴>,err=...,elapsed_ms=...` 仅报告阶段变化，不能代替 `PID_DONE`。超时文本保留 `PID_TIMEOUT:<轴>,abs=...,err=...`，追加 `phase=total|settling,elapsed_ms=...,settle_ms=...`；ROS/Windows 仍按原轴字段识别失败，二进制帧布局不变。ROS 默认等待 610 秒。

Windows 的 ADS STOP 事务只消费当前固件专属回复 `ADS_OK:STOP`、`ADS_ERR:STOP_I2C`、`ADS_ERR:STOP_MUTEX_TIMEOUT`；迟到 START/配置错误不得推进 STOP。Qt 已排队 reader 回调在交付时按不可变 reader 身份过滤；关闭等待或清 buffer 不替代会话隔离。

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
