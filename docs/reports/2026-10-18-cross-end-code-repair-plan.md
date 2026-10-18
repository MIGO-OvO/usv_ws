# 无人船跨端代码修复方案

日期：2026-10-18；实施更新：2026-10-19。状态：代码与离线验证完成，分仓发布中；设备验收待用户执行。范围：ROS、ESP32、ArduRover、QGC，以及受协议变更影响的 Web 和 Windows 上位机。地图功能不改、地图测试跳过。

## 一 总体决策

先修复停止与恢复安全，再修复真实采样准入、ADS 事务、通信传输和状态展示。不能用延长超时、取消有效帧检查、自动重放启动命令或频繁重启来替代根因修复。保留现有 owner、watchdog、采样结果和人工接管保护。

本方案依据 [GPT-6-PRO 审计报告](D:/usv_ws/USV_Cross_End_Audit_2026-10-18/01_AUDIT_REPORT.zh-CN.txt)、[现场取证说明](D:/usv_ws/USV_Cross_End_Audit_2026-10-18/02_FIELD_EVIDENCE.zh-CN.txt)及当前工作树制定。审计的 A 级现场证据、B 级源码复现、C 级条件机制必须分别验收：

- 现场指定 attempt 的直接终止原因是 `spectrometer_stale`。修复必须保留这项保护，同时查明有效帧中断原因。
- 旧泵命令跨重连、STOP 被阻塞、真实 lab 无测量仍完成、ADS 事务缺锁等，可以立即进入修复。
- 整组载荷失联仍缺同窗口收发证据。TCP 写缺陷可以修，但不能据此宣布已唯一定位现场失联。
- 不重新设计驾驶舱布局，不做全仓重构，不修改 GPS 可选采样政策，不改变飞控人工接管策略。

本文件保留原计划的任务与验收要求，并追加实际证据；“现场验收”是后续操作者步骤，不代表已经执行。实施采用 Karpathy 的目标与验收先行原则，以及 Ponytail full 的复用现有机制、最小完整补丁原则。没有连接真实设备或烧录。

## 二 2026-10-18 实施前基线与审计差异（历史）

### 2.1 仓库基线

| 仓库 | 当前 HEAD | 本地状态与处理 |
|---|---|---|
| 根文档 | `3f350fba06a402a294907d7762f50321c3d0b01b` | 与报告一致；审计目录未跟踪，不能整体加入提交 |
| ROS | `8ce106da84be32d417eec60e6420618ffc378690` | 干净，与报告一致 |
| QGC operations | `5cb464046a26a3ee0aecd0b2e5d3adb4d07a7973` | 71 条 porcelain 状态记录，含目录记录；不能等同于 71 个文件，必须保留全部原有改动 |
| ArduRover | `2ff2a2bc922088667d4421d4d7a7a9f6767356b5` | 与报告一致；另有未跟踪 WSL 构建入口，不纳入本次修复 |
| DetFirmware | `7275ecd178ae12045e9d4885b9208146e2bbe838` | 干净，与报告一致 |
| Windows 上位机 | `c4ea4f1b6ef85238cc94f691b43f359045f7bea7` | 干净；不在原报告主控制链核验范围，仅安排串口协议兼容修改 |

对审计 `SOURCE_FILES.json` 的 Git blob 指纹做了当前文件核对，ROS 132 项、ArduRover 17 项、DetFirmware 7 项均一致。此结论是源码一致，不是报告中所有测试已在本机重跑。

当前运行的 QGC 是 `D:/usv_ws/WQ-USV-QGroundControl/build/Desktop_Qt_6_10_1_MSVC2022_64bit-Debug-usv_ws/Debug/QGroundControl.exe`，SHA-256 为 `9919679B4295367BBBCC4D14B21448D076B11698DDA1CE54FA611549D89126DD`。仅凭该指纹不能证明它包含当前所有未提交代码；正式验证必须重新构建并记录源码和产物对应关系。

### 2.2 QGC 必须按当前工作树修复

| 审计发现 | 当前本地实现 | 实施结论 |
|---|---|---|
| 任一字段续期整组 VLD/BSET | FactGroup 已有 `freshFields`、单调时钟；OperationsState 已检查 VLD、电压、基线各自年龄 | 保留，补真实 Qt 定时器测试和上游缓存过期，不能重建一套 freshness |
| 31010、31013 匹配过宽 | 已收紧为准备、采样、检测等明确状态 | 保留并补异常与迟到状态用例 |
| 31019 用无效信号认定停止 | 已要求新鲜 `VLD=0` | 仍不足：采集中产生的新鲜无效帧也可为 0，需要独立采集状态 |
| ACK 前遥测丢失 | `observeTelemetry()` 仍只处理 `awaitedCommand` | 缺陷仍存在，必须修复 |
| 自定义命令不自动重试 | 本地 Vehicle 已对 31011、31016、31019 启用重试；启动不重试 | 验证停止幂等、迟到停止对新任务的影响、总 deadline；不可沿用报告旧结论 |
| 无本地驾驶舱代码 | 已有 CockpitController、独立急停面板和安全锁等未提交文件 | 在这些实现上接入结果，保留人工核验解锁机制 |

本轮对报告的控制器测试做了仅在内存中的当前路径/属性替身适配，执行当前 QML 的实际 JS 函数：5 项中 3 项通过、2 项失败。失败项为“丢 ACK 后基线继续锁住”和“ACK 前准备到结束的状态被丢弃”。现有 `custom/tests/test_usv_qgc_contract.py` 34 项通过。两者不矛盾：旧回归没有覆盖完整命令生命周期；这些也不等于 Qt/硬件验收。

## 三 跨端不变量与接口决策

### 3.1 必须保持的链路

命令：QGC `COMMAND_LONG(target=1/191)` → 飞控路由 → router → bridge TCP 5760 → trigger → pump → ESP32。ACK 反向返回。

遥测：ESP32 → ROS → bridge `source=1/191` → 飞控缓存 → 飞控以 `source=1/1` 向 QGC 重新发送。原始 `NAMED_VALUE_FLOAT` 不靠通用路由直通。MAVROS 的 1/240 和 UDP 在线不代表这条独立 TCP 路径健康。

源码依据：[飞控载荷接收](D:/usv_ws/ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp:597)、[NVF 路由限制](D:/usv_ws/ardupilot-usv/libraries/GCS_MAVLink/MAVLink_routing.cpp:143)、[缓存发送](D:/usv_ws/ardupilot-usv/Rover/sensors.cpp:100)、[bridge 收命令](D:/usv_ws/src/usv_ros/scripts/usv_mavlink_router_bridge.py:471)。验证须同时检查 source、target、字段名和当前会话，不以截图中缺少 191 NVF 直接判故障。

### 3.2 八项强制不变量

1. STOP、超时、owner 失效或连接换代后，旧 ON、非零 SET、start、resume 及其回调不得产生新动作。
2. STOP 不等待分光 ACK、首帧、重试退避或普通服务完成；串口字节写入仍有序。
3. 无 GPS 可以真实采样；没有真实有效测量、有效基线和设备准备结果，不得执行采样运动或产生成功结果。
4. 明确仿真、机械调试、真实采样三种语义分离。机械调试可运动，但不能生成真实采样成功、浓度记录或 `USV_DONE`。
5. 链路在线、采集中、测量有效、基线有效、任务成功分别表示；相互不能替代。
6. 只有本次任务的明确成功或既有显式 SKIP 策略可以放行 mission script；取消/失败/清理结束不能伪装成成功。
7. 重连只恢复身份、配置和遥测。新动作必须来自新的明确请求；失败的清理记录不能被连接成功抹掉。
8. 软件 ACK、固件停止状态和物理停机是三层证据；任何软件测试均不能替代台架物理停机测量。

### 3.3 兼容优先的接口路线

第一批安全补丁保持现有 MAVLink 命令号、参数 1/2 和二进制串口帧长度不变。复用 `ControlCommand.command_id`、`sampling_context.attempt_id`、owner 及 `/usv/control_events`，不新建通用任务平台。

完整闭环已实现以下配套信息，必须成套升级：

- 已增加 `USV_ADS`：0 未知、1 停止已确认、2 启动中、3 采集中、4 错误、5 停止未确认。`VLD=0` 不再承载“停止已确认”。接口表与三端契约测试同步。
- 已增加 `USV_PROTO`，识别关联事件/明确采集状态支持。字段名不超过 NVF 的 10 字节；常规遥测由 24 项增为 26 项，根契约检查器覆盖完整清单。
- 自定义 31010..31019 的参数 3/4 传递请求序号/客户端会话号，限制为可精确表示的 24 位正整数；参数 1/2 与 FCU sample_id 不变。QGC 持久化身份并加文件锁，损坏/不可写/耗尽均拒绝新动作；ROS SQLite 账本持久化防重。旧 7 元消息继续显式按旧协议解析。
- 通过现有 `STATUSTEXT` 通道新增版本化事件，内容包含完整 `attempt_id`、请求/会话号、命令、阶段、结果、原因、取消前准备阶段和事件序号。完整 UUID 保留为字符串，禁止塞进 float 或截短后当唯一标识。长事件采用 MAVLink 2 `id/chunk_seq`，设最大长度、分片数、重组超时和去重边界；缺片只产生“结果未知”。
- QGC 已有 [StatusTextHandler 分片入口](D:/usv_ws/WQ-USV-QGroundControl/src/MAVLink/StatusTextHandler.cc:263)，优先复用并为机器事件提供完整性/来源标记。现有展示会把缺片替换为省略号，不能将这种展示文本当可靠终态；补重复、乱序、缺片、不同组件交错测试，不再无条件复制一个重组器。
- 版本化 `USVE1` 事件包含会话/请求、完整 attempt UUID、命令、序号、阶段、结果、原因及 preflight 阶段；实际编码见 ROS `scripts/lib/payload_protocol.py` 与 QGC FactGroup。发送/重组有长度、容量、超时和去重限制，不保证无线链路 exactly-once。
- 标准 ACK 保持命令接收/执行请求的语义；完整任务终态使用关联事件。若使用 `IN_PROGRESS`，必须一并接通 QGC C++ 到 QML 的进度信号及总 deadline。

隔离 SITL 两 UDP 链路已验证 STATUSTEXT 原样转发，QGC 真实 C++/QML 测试验证重组、命令参数与关联生命周期；无线实链路仍待现场验证。旧设备/旧地面站组合只允许基础遥测和尝试停止，不声称强事务关联，新增动作门禁保守关闭。端到端关闭仍需要成套版本与台架证据。

## 四 修复任务与验收

### R0 固化版本与失败用例

优先级 P0，先于业务修改。

1. 保存各仓库 HEAD、tracked diff、未跟踪文件清单及相关文件哈希；QGC 同时记录运行产物。保存到独立证据目录，不覆盖用户文件，不使用 reset/clean。
2. 将审计失败用例迁入对应仓库现有测试目录，按当前方法适配，不依赖报告缺失的 `audit-src`，不把“抽取器找不到函数”计为通过。
3. 测试应先证明修复前失败，再与生产补丁成对变绿。原报告的路由 17 场景是行为刻画，不能把“复现了丢包”当修复成功。
4. 为 QGC 当前工作树建立差异基线，先保留已实现保护，再针对剩余问题补测试。

验收：每个 R 项有失败断言、准确仓库、可运行测试命令和预期；没有硬件动作、没有生产配置写入。

### R1 阻止旧进样与运动动作跨会话执行

优先级 P0。文件：[injection_pump_worker.py](D:/usv_ws/src/usv_ros/scripts/lib/injection_pump_worker.py:13)、[pump_control_node.py](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:683)。

改动方案：

1. 在现有 work item 上增加连接代次、动作取消代次、owner/attempt 标识、单调 deadline 和取消状态。手动动作使用独立的显式控制会话，不借用旧采样 owner。
2. 入队、出队后、最终串口写入前分别校验；最后一次检查与串口切换共用 `serial_lock` 临界区。仅清空队列或在出队前检查不够。
3. 等待超时使未写出的任务失效；已写出的动作只能标为执行未知并走停止/确认，不能宣称已撤销。deadline 覆盖排队和执行总时长。
4. STOP/断连/重连/owner 终止递增取消代次。成功、失败回调也携带代次，旧回调不得更新新会话的泵状态或故障。
5. 队列满时明确拒绝，不静默挤掉可能承载 OFF 的任务。停止走 R2 的优先入口；不受满队列或旧任务限制。
6. 同步检查所有进入 Worker 的 ON、SET、调速和原始文本入口，以及 preflight、AutomationEngine 的延迟动作。复用已有会话检查，不新建第二套 engine。

回归：旧 ON 已出队但未写时重连；同会话 STOP 后释放旧任务；submit 超时后释放；满队列 OFF；旧成功/失败回调迟到；新 owner 不能被旧 owner 续租。每个用例断言新连接和新任务都没有旧非零输出，不只断言最终 OFF。

完成门槛：报告旧命令用例由失败变通过，既有 9 项安全保护仍通过。重连返回要区分 transport_connected、configuration_ready、stop_confirmed 和 prior_cleanup_failed。

### R2 让停止贯通 trigger 和串口事务

优先级 P0，依赖 R1 的取消边界。文件：[trigger 分发](D:/usv_ws/src/usv_ros/scripts/mavlink_trigger_node.py:1135)、[分光启动事务](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:1341)、[文本 ACK 等待](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:1123)、[统一控制入口](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:2585)。

上游：订阅回调仅做校验和有界入队，普通长命令由一个受控执行入口处理；STOP 不排在普通任务后面。保留同设备普通动作互斥，拒绝忙时冲突启动，不采用每条消息任意新建线程。ServiceProxy 外层超时不等于服务已取消；取消必须传到 pump 的动作代次，迟到服务返回不得复活旧请求。

下游：缩短 `_control_lock` 到状态检查/更新；将文本事务独占与控制状态保护分开。所有 ACK 等待、首帧等待、settling、重试退避和步骤等待检查取消事件。STOP 先取消旧事务及其后续动作，再优先完成有序 STOPALL 写入，最后做确认与清理；不得先等待 engine join 或分光 barrier 才发停止。

ACK 匹配仍为单活跃文本事务；保留既有 `ADSSTATUS?` / `PIDQUERY` 回包屏障思想。被取消事务的迟到 ACK 不能匹配新的启动或 STOP 确认。首个安全 STOP 写出不等待屏障，后续确认可用屏障排除旧回包。明确锁顺序，禁止持状态锁等待串口 Worker、ACK 或线程退出。

串口已有 `write_timeout`，必须继续检查完整写入和 `flush` 的可中断性/平台行为。若驱动写阻塞或 STOP 未确认，锁存故障并禁止新动作；不能无限续租让已知危险输出维持。watchdog 停机策略沿用现有会话规则并补故障测试，不以任意关闭心跳代替正常 STOP。

回归：I2CMAP、ADSCFG、ADSSTART、首帧、重试退避各阶段阻塞时，后到 31011/Web STOP 都可先送出；31018 ServiceProxy 不返回时 STOP 仍能进入 pump；STOP 后没有新 start/ON；串口写阻塞、断开和旧 ACK 不制造成功。

软件验收建议目标：可写假串口条件下，停止请求被 trigger/pump 接收至首个 STOPALL 写出不超过 250 ms，并且不依赖原 2 秒 ACK timeout 到期。该数值是开发回归预算，不是硬实时或实船停机保证；真实线路、MCU 和物理停止门槛另行测量。停止重复请求幂等，并阻止旧停止重试误伤已开始的新任务。

### R3 恢复真实采样的测量门禁

优先级 P0，依赖 R1/R2。文件：[采样准入](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:2991)、[样本等待](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:1782)、[freshness 保护](D:/usv_ws/src/usv_ros/scripts/pump_control_node.py:2279)，以及现有 preflight、AutomationEngine、trigger 和采样记录模块。

默认决策：不新增隐式自动启动分光行为。`auto_start=false` 且检测未准备时，在第一条采样运动前明确拒绝 `spectrometer_not_ready`；一键入口如需准备，显式复用现有分光启动事务，成功取得有效首帧和基线后再申请真实采样。

1. 复用现有 lab_sim/lab_real 来源及模式配置，真实 manual、FCU、survey、lab_real 共用后端门禁。`lab_mode=True` 或 `spectrometer.enabled=false` 都不能绕过真实采样测量要求。
2. 准入检查当前串口会话、owner、配置、采集状态、真实有效帧年龄、测试帧标志及基线来源。基线与配置/采集会话绑定，重连、配置改变、重新启动后的失效规则明确化。
3. Preflight 运动前及每个真实采样步骤维持同一不变量；步骤要求新的有效样本，不能复用启动前旧帧。已合入用户要求的超时热修复：PID 默认 120 秒、新帧等待 10 秒、首帧至少 4 秒、油相无进展 5 秒、总预算乘 2 加 10 秒；设备返回 PID_TIMEOUT/PID_FAIL 仍失败，检测板自身 30 秒 PID 保护未取消。
4. 信号超过 2 秒即失效；本会话曾收到真帧且配置/基线仍有效时，允许默认至 10 秒的有界恢复等待，恢复前不发新运动、旧帧不能完成任务。已有输出在此窗口可能继续，不等于即时停机。明确 I2C/disabled/fault、ADSSTOP、owner 丢失和 STOP 不豁免；从未有真帧的任务不能借此启动。空闲 ADSSTOP 不导致整组载荷离线。
5. `test_automation_cold_start.py` 中“lab 无分光仍真实完成”的旧断言需明确迁到机械调试语义，同时增加真实采样拒绝断言；这是需求纠正，不能简单删测试换全绿。
6. Web、QGC 手动、FCU、survey、lab_real 全入口一致；GPS 缺失仍记录 null 坐标，保留开始位置快照及不回填约束。失败记录可以存在，成功记录和 `USV_DONE` 不得误发。

验收：无 GPS + 真实有效信号 + 基线可正常采样；从无有效帧、仅 START ACK、测试帧、旧基线、采集中 ADSSTOP 均不得完成真实采样。机械调试有明确标签且不污染真实数据。记录终止前 phase，不能只剩 cancelled。

### R4 修复 ESP32 ADS 原子事务与真实停止结果

优先级 P0/P1，独立于 R1 可开发，台架需与 R2/R3 一起验收。文件：[ADS 命令分支](D:/usv_ws/DetFirmware/src/main.cpp:768)、[adsInitAndStart 与 adsStop](D:/usv_ws/DetFirmware/src/ads122c04.h:166)。

1. 使用既有 `i2cMutex` 包住通道选择、RESET、配置和 START 的完整事务；STOP 的通道选择与 POWERDOWN 同样互斥。核查调用层级，避免非递归 mutex 重入。
2. mutex 获取、Wire 操作都有有界超时；失败走统一出口释放锁。不要在步进控制循环增加延迟；度量 TaskComms 被阻塞的上限，保证 STOPALL/watchdog 可运行。
3. `adsStop` 检查 POWERDOWN 返回值；只有实际事务成功才回 `ADS_OK:STOP`。选择通道、总线或锁失败回明确错误，软件停轮询可立即执行，但不能因此声明硬件停机已确认。
4. 明确 `ADSSTATUS` 中软件轮询与硬件停止确认的区别。新增兼容字段时保留旧前缀与二进制帧布局；ROS 和 Windows 的解析器同步处理错误/未知，不吞掉新错误。
5. 首帧必须晚于本次 START；失败启动清除旧有效性。角度/健康流不因正常 ADSSTOP 中断。

回归：原报告无竞争对照、RESET delay 期间角度任务交错、mux 失败、POWERDOWN 失败；再补 mutex 超时、释放后恢复、重复 STOP、看门狗和两种上位机解析。宿主测试之外必须完成 PlatformIO 编译和真实 I²C/执行器台架。

### R5 修复 bridge 完整帧传输与分层恢复

优先级 P1；涉及自动恢复的启用依赖 R1/R2。文件：[usv_mavlink_router_bridge.py](D:/usv_ws/src/usv_ros/scripts/usv_mavlink_router_bridge.py:132)，优先在现有发送封装处修复，仅在需要单独测试时抽取一个小型 transport 辅助模块。

1. 先核验 Jetson 正在运行的解释器、pymavlink 实际加载文件/版本/哈希。报告三版本均存在问题，不能把“升级到新版”直接当解法。
2. 保留 pymavlink 编解码，替换吞 EAGAIN/短写的写入边界，使 bridge 获得真实完整写结果。非阻塞写保留未写尾部、偏移和会话号；EAGAIN 等待可写，零字节、永久错误或总截止时间到期进入明确故障。
3. 一个串口/TCP 会话只有一个实际 writer；TCP 同一连接上未写完一帧前不能插入另一帧，也不能从帧头重复发送已接受的前缀。半帧无法在截止前完成时关闭该会话，不把尾部送往新 socket。
4. 背压缓存有界。普通遥测保留最新快照，未开始写出的过时快照可合并；已开始的帧不能被随意丢尾。ACK、失败结果、心跳优先于批量遥测，但仍受总循环预算约束，避免 24 项分别等待导致秒级阻塞。
5. 去掉“send_fn 未抛异常即整批成功”的统计方式，区分 generated_frames、fully_written_frames/bytes、short_writes、would_block、dropped/coalesced、send_errors、receive_errors。完整写入仅表示本机 socket 接受，不是飞控/QGC 已收到。
6. 接收按消息数和单调时间双预算退出，BAD_DATA 也消耗预算；持续接收不能饿死心跳、停止 ACK、失败通知和诊断。预算作为少量内部常量，先用压力测试定值，不新增大批配置。
7. 由 bridge 单点管理连接 generation、连接中/待入站心跳/可用/退避等状态；统一 EOF、EBADF、写异常的恢复，避免 pymavlink 隐式重连与外层重复重连竞争。保留报告已验证的 EOF 可恢复对照，不把它误写成原有死路。
8. 收发年龄、heartbeat 调度、退避使用 monotonic；UTC 仅用于日志。复用同 TCP 的 `gps_diagnostics.HEARTBEAT.received_monotonic`，不另开竞争 MAVLink 客户端。
9. TCP 恢复不重放 QGC 启动/resume；旧 ACK、旧终态发送队列按会话及 attempt 失效或重新验证。`USV_DONE/USV_FAIL` 保持既有 sample_id/终态约束，不引入跨重启无条件重试。

回归：实际 transport + 可控 socket 的 EAGAIN、短写、零写、写至半帧断开、EOF、持续 EBADF；真实 loopback 限速/停止读造成的背压；接收洪泛；墙钟前后跳；反复重连。要求接收端可解析帧、无字节拼接污染、计数真实、队列有界、停止优先且没有旧动作。

现场验收：同窗口 pcap 显示 bridge 双向数据；新会话看到真实入站 FCU 心跳；QGC 重新收到新鲜载荷。仅连接成功或 MAVROS CONNECTED 不算端到端恢复。

### R6 修复源数据年龄和飞控固定尾部饥饿

优先级 P1。文件：bridge、[Rover.h](D:/usv_ws/ardupilot-usv/Rover/Rover.h:449)、[GCS_MAVLink_Rover.cpp](D:/usv_ws/ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp:597)、[sensors.cpp](D:/usv_ws/ardupilot-usv/Rover/sensors.cpp:100)，按需要在 `Rover/GCS_MAVLink_Rover.h` 放置每链路发送游标，不扩展通用路由为可靠传输系统。

分三层处理：

1. ROS 源数据层：每类回调保存真实接收年龄；未更新的角度/测量不得因为 bridge 周期运行而伪装成新测量。VLD、明确采集状态、故障状态继续发送真实当前状态；过期值停止按实时字段发布，或使用双方已定义的显式未知值，不能随意发 NaN 后又被接收端丢弃。
2. 飞控缓存层：为每字段记录接收时间和 seen 标记，收到哪个字段只刷新哪个字段；过期字段不重发，PUMP_X 不能续期 VLD/BSET/STAT。保留全组链路判定，但它不授予任一字段新鲜性。时间回绕使用 HAL 的无符号差值规则。
3. 飞控调度层：用小型固定字段表和每 MAVLink 输出链路独立游标轮转。检查 txspace 后发送，成功才推进相应游标；重要状态可优先但不能耗尽普通字段预算。复用现有每链路发送能力，局部封装返回发送结果，避免只改全局起点却无法观察各链路实际发送。

保持默认 2 Hz 基线，不通过全局提高波特率或扩大所有 buffer 掩盖问题。新增协议字段后按最终字段数重算预算。`time_boot_ms` 的发送时间与原始测量时间含义明确，不直接比较 Jetson、飞控和 QGC 的不同 monotonic 时钟。

回归：先发 VLD/BSET 再只发 PUMP_X；bridge 活着但源回调停止；一条 GCS 链路拥塞另一条正常；每轮只容纳约 8 帧时最终所有 26 项均可得到发送机会；缓存过期不继续刷新 QGC。持续零带宽时应明确降级，不承诺不存在的送达保证。

源码级验收：固定每周期 8 帧预算下，26 项需 `ceil(26/8)=4` 个 2 Hz 周期轮完；飞控字段 TTL 为 3 秒。关键字段最大年龄与 QGC/ROS 门禁协调，不以全组在线续期陈旧测量。

### R7 修复 QGC 命令证据与事务生命周期

优先级 P1；安全入口必须与 R2 一起验证，强关联依赖第三节协议闭环。文件：[命令控制器](D:/usv_ws/WQ-USV-QGroundControl/custom/res/USVPayloadCommandController.qml:89)、[OperationsState](D:/usv_ws/WQ-USV-QGroundControl/custom/res/USVOperationsState.qml:14)、[FactGroup](D:/usv_ws/WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc:85)、[Vehicle ACK 处理](D:/usv_ws/WQ-USV-QGroundControl/src/Vehicle/Vehicle.cc:2924)，以及现有 CockpitController、PayloadPanel、SamplingWorkflow。

1. `send()` 时建立请求记录并订阅证据，不等 ACCEPTED 才开始观察。分开保留 ACK、发出后新鲜遥测、关联准备/开始事件、终态及超时，而不是在一个 pending/awaited 变量间丢失历史。
2. 记录相关字段的接收序号/单调时间基线；相同 bool 再次到达也应可观察，不能只监听值变化。绝不能用发出前已为真的 VLD/BSET 作为本次命令已执行的证据。
3. 丢 ACK 但观察到新鲜有效测量时可显示“信号已观察到，命令回执未确认”；符合设备安全条件的基线操作可开放，不必为丢 ACK 锁满 40 秒。此时不是宣告该命令或采样任务成功。
4. 晚 ACK 到达时保留先前准备到终止的记录；有关联失败事件就显示失败原因，不能被后到 ACCEPTED 覆盖。冲突证据显示冲突/未知并保留诊断。
5. 31019 只由新鲜明确采集状态及停止结果确认；31013 只允许恢复到本次有效活动状态；31017 需本次基线操作事件/更新序号；31010 的开始和最终成功分别展示。
6. 旧 ACK 只有 command 编号，不能仅凭本地 generation 彻底判定来源。升级协议用请求关联事件证明本次动作；旧协议模式限制同命令重入，过期 ACK 不单独解锁危险操作或宣布成功。重连、切船时清理请求并保留“执行未知”和安全锁，不自动续跑。
7. 如果发 IN_PROGRESS，使用现有 `progressHandler` 接入或增加限定 USV 的进度信号，避免影响所有 QGC 命令；同时有阶段超时和绝对总 deadline。不能由重复 progress 无限续命，也不能只改 ROS 回 5。
8. 保留本地停止命令重试，但验证服务幂等、总重试时长和旧事务清退。新采样必须等停止事务结束及必要核验后才允许，避免旧 STOP 重试打断新任务。绝不把 start/calibrate/resume 加入无条件自动重试。
9. 驾驶舱急停与普通停止共用后端安全路径，但展示和操作锁继续独立。即使状态字段未知，只要通信入口仍可用就允许尝试停止；不可因载荷离线禁用所有安全动作。

回归：丢 ACK、晚 ACK、拒绝 ACK、IN_PROGRESS、重复 ACK、同命令旧 ACK、切船、TCP/Vehicle 重建、相同值新遥测、过期值、仅角度更新、停止重试完成前尝试新任务。QML 测试与真实 Vehicle ACK 注入测试都必须覆盖。

### R8 保留真实阶段和失败原因

优先级 P1，依赖 R3/R7 及协议事件。文件：pump、trigger、bridge 的现有状态发布，以及 QGC/前端现有状态展示；不新造另一份采样真源。

- 终止记录保留完整 attempt_id、source、首个 terminal_reason、取消前 preflight_phase、步骤/轮次、测量/owner 年龄及 cleanup 结果。清理失败作为附加原因，不覆盖最初 spectrometer_stale；旧线程不能覆盖新 attempt。
- 设备 preflight 显示“设备准备”，子阶段对应归零、补偿、分离/进样等。导航稳定与设备准备分别表述；兼容阶段不直接重定义旧 `USV_STAT=8`，通过上下文/新增事件区分。
- 保留 `USV_SCNT` 现有“启动次数”语义并更正标签，不直接改成成功数造成历史解释变化。成功次数必须从去重后的终态计算并说明统计会话；无终态来源时显示未知，不估算。
- ACK accepted、开始采样、完成采样、清理结束四者分别展示。latencyMs 改为其实际含义“心跳到达间隔”，payload freshness、命令 RTT 另按真实时间测量。
- Web 记录、导出及 QGC 展示同一个终态；前端需要改动时重建并提交 `static/dist`，避免部署仍用旧页面。

验收：同一 attempt 的 GUI、ROS 终态、记录文件可对账；多个 attempt 的取消不串台；latched 状态显示源时间，不把订阅时刻当故障发生时刻。

### R9 修复诊断解析和受控日志维护

优先级 P1/P2，可提前完成只读诊断部分。文件：[status_usv_all.sh](D:/usv_ws/src/usv_ros/scripts/status_usv_all.sh:435)、现有启动/日志脚本、bridge diagnostics、相关文档。

1. 优先直接订阅并读取 `std_msgs/String.data`；保留命令输出路径时先用现有 PyYAML 完整还原外层再解析 JSON，删除正则/ast 猜测式提取。区分无发布者、等待超时、外层解析失败和 payload schema 错误。
2. 输出 TCP 会话号、最后入站 FCU heartbeat 年龄、最后完整写帧时间、收发错误类别和重连原因；MAVROS connected 仅作旁证。协议能力、固件版本和产物身份各自记录。
3. 被动取证复用报告 `capture_ros_window.py` 和现有话题，不启动额外 191 客户端，不用 source 240 的主动 NVF probe 证明主链路。旧 probe 保留时显著标注过滤边界，不扩大本次工具重写。
4. 先核对日志实际写入者和平台服务；优先标准日志轮转/现有 logging handler。运行中必须验证重新打开日志或轮转行为，不能只把打开的文件改名就声称限制生效。
5. 限额按现场速率和保留窗口确定，优先在下次维护窗口启用；不自动删除本次故障证据。日志体积仅作为维护问题，不能写成已经证明的故障根因。

验收：多行转义 String、中文、空消息、合法非对象 JSON、坏 YAML/JSON 均有明确输出；诊断失败不影响控制；轮转后仍有新日志且总量受限、已归档故障证据保留。

### R10 协议兼容与文档收口

优先级 P1，随对应代码批次完成。

- ROS/Windows 均验证 ADS 新错误/状态响应。Windows 修改限于 `src/ui/mixins/spectro_mixin.py`、`src/ui/main_window_complete.py` 和相关解析/测试；仅在实际调用需要时涉及串口核心，不开展整个 PySide6 软件审计。
- 验证 ROS 导入的 Windows `data/settings.json` 不会把机械调试/关闭分光配置解释成真实采样豁免；不擅自改用户现场配置文件。
- 新字段同步 bridge、Rover 缓存/调度、QGC `.cc/.h/.json`、使用者和测试。新增事件同步 sender、router/FC pass-through 测试、QGC parser，限制长度/类型/来源并处理未知版本。
- 实施完成后更新 `docs/current/40_interfaces.md`、`60_source_map.md`、`70_verification.md`，以及各子仓库公开 README；更新 22/24/26 字段口径与状态语义。一次性计划仍留在 `docs/reports/`，不把未完成项写成 current 的已实现事实。

## 五 实施批次和提交边界

| 批次 | 任务 | 依赖与交付门槛 |
|---|---|---|
| 0 基线 | R0；R9 的只读取证 | 确认当前 QGC 差异，迁移失败测试，冻结版本 |
| 1 停止恢复安全 | R1、R2 | 旧动作不能重放；长服务/ACK 等待不挡 STOP；9 项既有安全保护不退化 |
| 2 真实测量 | R3、R4；R10 的串口兼容 | 无测量不运动/不成功；ADS 完整互斥和真实结果；台架前置条件成立 |
| 3 传输与新鲜度 | R5、R6；R7 中现有协议可做的部分 | 背压/断连可识别；字段不过期续命；公平发送；保留用户本地 freshness |
| 4 事务闭环 | 第三节新增协议、R7 完整生命周期、R8 | 明确 ADS 状态；请求/attempt 关联；进度/终态/原因一致，旧协议保守降级 |
| 5 发布验收 | R9 日志、R10 文档、下节全部验证 | 版本成套、台架证据齐全后才评估实船 |

同一批次是集成顺序，不授权立即部署。R4 与诊断代码可独立推进；pump 内 R1/R2/R3 共用锁和状态，必须按顺序集成，不同时改动相同代码段。

建议按独立仓库、单一行为拆提交：ROS 队列隔离、ROS 停止通道、ROS 测量门禁、ESP32 ADS 事务、ROS transport、ArduRover 缓存/公平性、QGC 生命周期、跨端新协议配套、Windows 兼容、根文档。跨端协议提交相互标注依赖，避免半套发布。

用户已授权实施、推送、PR 与合并。新分支使用 `codex/` 前缀。QGC 原有改动已先提交并同步远端 `3f9056730086d8a6d21e5751623d35e0ddc1e701`；本轮在其上增量修复并复用 PR #17，不覆盖现有驾驶舱。禁止根仓库 `git add .`、force-push 和覆盖本地工作。

## 六 验证矩阵

### 6.1 迁入仓库的必测场景

| 场景 | 故障注入 | 必须断言 |
|---|---|---|
| T01 旧动作跨重连 | 已出队 ON 暂停，重连后释放 | 新会话无旧 ON/非零 SET，旧回调不改新状态 |
| T02 同会话取消 | 超时/STOP 后释放旧任务 | 无后续运动；已发送动作标未知并停止，不伪称撤销 |
| T03 停止优先 | ADS 各等待点、trigger 服务阻塞、队列满 | 可写条件下 STOP 先于长事务结束到设备边界 |
| T04 真实采样 | 无 GPS、无首帧、仅 ACK、无基线、测试帧 | GPS 可选；其余不合格真实采样在运动前拒绝 |
| T05 运行期测量 | ADSSTOP、stale、owner 超时 | 安全终止、保留首因、无 succeeded/错误 USV_DONE |
| T06 ADS 互斥 | RESET 间角度切通道、mutex/mux/POWERDOWN 失败 | 不错通道；锁释放；失败不能 ADS_OK:STOP |
| T07 TCP 写 | EAGAIN、短写、零写、半帧断开 | 帧完整/明确失败，统计不虚增，缓存有界 |
| T08 TCP 恢复 | EOF、EBADF、router 重建、时钟跳变 | 会话换代、退避正确、有真实新入站证据、无旧动作 |
| T09 公平调度 | RX 洪泛、单链路 txspace 缩小 | 心跳/ACK/失败通知不饿死，字段轮转且各链路独立 |
| T10 源头过期 | 停源回调、只发 PUMP_X、FC 旧 VLD | 旧测量不被持续转发伪装新鲜，局部降级不误判整组 |
| T11 命令生命周期 | ACK 丢/晚/重复/拒绝，遥测先到 | 不假成功、不丢历史、不无期限锁按钮 |
| T12 事务隔离 | 同命令重发、旧会话事件、切船、缺片 | 旧 ACK/事件不完成新请求，无法关联则未知 |
| T13 正常停止对照 | idle ADSSTOP | 角度/健康/载荷链路继续在线 |
| T14 诊断 | 多行 String、坏 JSON、latched 旧消息 | 区分解析/时间/通信状态，不触发控制动作 |
| T15 mission 回归 | 成功/取消/超时/失联/MANUAL/RTL/SKIP | 仅同 ID 成功或显式 skipped 放行；人工模式不被覆盖 |
| T16 原有保护 | 既有 owner/watchdog/会话/测试帧 9 项 | 全部继续通过，不放宽断言 |

### 6.2 可运行的验证入口

以下为复现入口；实际执行结果见 6.4。除列明项外，工作目录为对应仓库根目录。地图测试明确排除。

```text
# ROS
python3 -B tests/run_non_map_tests.py
# 先定向执行 test_system_safety_contract.py、test_field_transactions.py、
# test_preflight_stop_races.py、test_qgc_payload_startup.py、test_fcu_sampling_result.py，
# 再执行迁入的审计回归与全量测试；修改前后使用同一环境比较。

# ROS Web 前端有改动时，在 frontend 目录
npm run build

# QGC
python -B -m unittest discover -s custom/tests -p test_usv_qgc_contract.py
qmltestrunner.exe -input custom/tests
# 另运行 Vehicle 的 SendMavCommandWithHandler/Signalling 及新增真实 ACK/进度测试。

# DetFirmware
python -m pytest tests -q
python3 -B tests/test_control_watchdog_native.py
python3 -B tests/test_pid_test_scheduling_native.py
pio run -e nodemcu-32s

# Windows 上位机
python -m pytest tests -q

# ArduRover，Linux/WSL
python3 -B tests/test_usv_sampling_safety.py
./waf configure --board sitl
./waf rover
# 使用刚构建的绝对 binary 路径运行现有隔离 SITL 脚本
python3 -B tests/check_usv_sitl_sampling.py --binary <实际SITL产物> --scenario all
./waf configure --board Pixhawk6C
./waf rover

# 根仓库
python -B docs/tools/check_workspace_compatibility.py
python -B -m unittest discover -s docs/tools
# 每个修改仓库分别运行
git diff --check
```

QGC 已用 Qt 6.10.1 / MSVC 14.44 完整构建隔离 Debug `build/audit-debug-20261018-v2` 与既有 Release。没有关闭用户正在运行的旧 Debug 窗口或覆盖其产物；它仍是旧版本，需用户在维护窗口切换。实际应用测试加 `--allow-multiple`，并恢复了 UnitTestList 中被注释的 Vehicle 测试注册，避免“退出成功但零测试”。ROS 另做 Python 3.8 兼容语法和 launch XML 检查；native C++ 回归使用 Linux/WSL。

全量测试若存在预先失败项，先在基线复现并单独列出；不能把它算本次引入，也不能把未跑/不支持静默写成通过。原报告固定快照的结果与本机新回归结果分开保存。

### 6.3 Jetson 与真实台架

必须先停止任务、确认安全、准备独立硬件断电手段，再由用户执行。Agent 本轮不远程重连、不发控制指令、不烧录。

1. 记录 ROS、QGC、ESP32、飞控、Windows 版本及产物哈希、配置和 pymavlink/router 身份；启动新日志会话，计数归零与重启分开记录。
2. 无 GPS 冷启动：手动准备分光、首帧、基线、preflight、采样、正常停止。验证每种准备阶段取消及失败原因保留。
3. 采集启动/配置卡住时发普通 STOP；分别记录 QGC 点击、bridge 接收、trigger 受理、STOPALL 写出、固件确认和实际泵/轴停止时刻。给出最坏值和分布，不仅给平均值。
4. 在低负载受控条件下验证串口断开、进程退出、owner 失联、硬件 watchdog、重连；确认任何旧动作都不重放，恢复后必须显式新请求。
5. 只停 ADS 时持续观察角度/健康；对 I²C 间歇异常核对 success、mutex_timeout、i2c_error、crc_error、duplicate、transient_drop 的同会话增量。
6. TCP/router 场景先在隔离环境注入，再按现场维护流程测试真实路径。使用同 15 秒窗口的 bridge 双向 pcap、ROS 话题和 QGC tlog 缩小断点，不为了取证再启动真实采样。
7. 建议最低耐久项为 100 次启停及不少于 60 分钟运行，并覆盖至少历史故障时间的两倍；如果已知故障窗口更长则延长。该建议是回归下限，不代表可靠性认证。

物理停止可接受上限须依据泵路、机械惯性、压力和现场风险在台架前确定。不能把 UI 等待、约 3 秒硬件 watchdog 或软件 250 ms 预算直接当物理合格线。任一实际停止超限、旧动作重放、结果冒充成功均阻断实船使用。

### 6.4 2026-10-19 实际验证证据

| 端 | 已完成结果 | 边界 |
|---|---|---|
| ROS | 非地图 unittest 647 项，0 失败、13 环境跳过，排除 130 地图项；定向 102 项/44 subtests；最终记录关联 22 项/10 subtests；前端 build 成功；59 文件 Python 3.8 语法与 launch XML 通过 | 跳过项不算通过；WSL 真实 TCP 2、logrotate 与 event bridge 各 1 项另通过 |
| QGC | 完整 Debug/Release 构建；StatusText 7、Vehicle Signalling 9、Handler 5；QML 34；Python 契约 34；Cockpit 行为 49 检查通过 | 未执行地图或实机；保留旧运行窗口 |
| ArduRover | SITL、Pixhawk6C 完整构建；success/cancel/timeout/link_loss/manual_takeover/rtl_takeover 六场景；两 UDP 事件转发；native cache 1、sampling safety 4 通过 | 未烧录；Pixhawk6C Flash 1,455,780 B，余 510,292 B |
| DetFirmware | PlatformIO 成功；Windows pytest 18 通过/10 平台跳过；WSL native 10 通过（含 ADS 8） | RAM 24,684 B，Flash 331,729 B；未烧录 |
| Windows | pytest 96 通过、1 跳过；包含真实 Qt 定时器的断线/STOP 结果回归 | 11 项既有 return-not-none 警告；未接串口硬件 |
| 根契约 | 26 字段三端源码核对与 6 项检查器测试通过 | 快照不代表现场验收；检查器仍要求独立现场证据 |

产物 SHA-256（修复工作树构建，嵌入的 Git 标签仍可能为提交前基线；不是硬件验收版本声明）：

| 产物 | SHA-256 |
|---|---|
| QGC Debug exe | `C68EF1C6D6CD1221597948FD43242C70C6808DD7DD38E87DF3599A681B6E4017` |
| QGC Release exe | `8C7D1E3D087C092E79BBA40ADDA9D8B12F0C28114B15DD8216EC5F047401D5FA` |
| Pixhawk6C ardurover.apj | `6A01DE660B7FE540405FBEEBF1F529EDF5094AD76FF8E73848DE70C9C4F107CF` |
| ESP32 firmware.bin | `DC16A1F5C97895C9EF1C36BE0066CAB3EEA23B964AF0787C8DE4424E0B1A21E5` |

QGC 日志在 `build/audit-*.log`，QML 报告在 `build/tests/reports/test-report-2026-10-19-014500.md`；ROS/Windows 最终日志在本机临时目录 `usv-cross-end-final-runner-20261019.log` / `usv-windows-final-tests.log`。构建目录与运行日志不提交。

## 七 部署与回滚

部署前提：对应批次离线、编译、隔离集成均通过；存在可恢复的原配置/产物和现场人工停止手段。先测试环境，再低负载台架，再讨论实船。不能混用未经兼容矩阵验证的新 QGC/旧 ROS 或新 ADS 语义/旧解析器。

推荐维护顺序：停任务并确认执行器安全 → 保存旧版本/配置/证据 → 安装匹配 ROS 和解析端 → 在授权下更新 ESP32/飞控 → 更新 QGC → 成套启动并只读核验 → 无负载到低负载操作。ROS 的 trigger/bridge/pump 一起更新重启；前端同时更新 `static/dist`。升级本身不得恢复旧 attempt。

回滚触发：旧动作出现、STOP 延迟超门槛、真测量门禁失效、串口/协议不兼容、持续丢帧或终态关联错误。先停机锁定，再回退整个兼容组合，不在任务运行中混搭回退。回退到已知含 P0 缺陷的版本只能作为停机诊断手段，不授权恢复自动采样。保留失败日志，不自动恢复旧任务、旧队列或旧 ARM 状态。

发布清单包括每仓库提交、构建产物 SHA-256、dirty 状态、协议能力、参数快照、测试输出、台架证据和剩余风险。QGC 原有未提交 UI 修改如纳入发布，须单独明确范围并验证，不能在安全修复提交中顺带打包。

## 八 完成判据与剩余风险

完整修复关闭需要同时满足：

- R1/R2/R3 的 P0 失败用例转绿，原有保护不退化；所有安全入口覆盖。
- ADS 原子事务、真实结果、bridge 完整写、恢复、字段年龄、公平调度和命令生命周期均通过真实代码回归。
- 协议、文档、QGC/Web/Windows 兼容一致；当前实际运行产物与验收源码对应。
- Jetson 和低负载台架证明真实停机、无旧动作、无假成功，正常 ADSSTOP 不造成整体离线。
- 整组失联有同窗口证据解释断点，或明确保留为未关闭事件；不能因修了多个 B 级缺陷就宣布该现场事件已根治。

本轮已完成 R0–R10 代码配套和 6.4 所列离线/构建/SITL 验证；PR 与远端版本记录在发布清单。未执行 Jetson 实进程、ESP32/飞控烧录、台架或实船验收，因此不将现场整组失联事件标为已根治。

仍需现场确认的风险包括：真实 router/UART/无线断点、pymavlink 实际加载版本、供电/EMI/器件间歇失效、物理停止时间、MAVLink 事件分片在实际链路上的行为，以及原有 FCU 跨重启 sample_id 复用边界。最后一项继续维持既有人工确认和不自动放行策略；若要改变该策略，应单列端到端持久化结果协议项目，不混入本轮局部修复。

## 九 发布清单（2026-10-19）

| 仓库 / 默认分支 | PR | 默认分支提交 / 状态 |
|---|---|---|
| ROS / main | [#87](https://github.com/MIGO-OvO/usv_ros/pull/87) | 已合并 `778d055c9df80d2b9f29872fc54eeb8a2c34df93`；含 #86 超时热修复 |
| ArduRover / master | [#10](https://github.com/MIGO-OvO/ardupilot-usv/pull/10) | 已 squash 合并 `925ee45f568521efdbb0b39b69b94ab81e11625d` |
| DetFirmware / main | [#3](https://github.com/MIGO-OvO/DetFirmware/pull/3) | 已合并 `186427df75047c0212d74969df2c18a3df01fd40` |
| Windows / master | [#8](https://github.com/MIGO-OvO/MotorControlApp_Pyside6/pull/8) | 已合并 `241ee6230576289b78448075525b57ffd611535a` |
| QGC / master | [#17](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/pull/17) | 修复分支已推送 `8923ce3c4`；CI 扫描器修正 `15e924c5d`；等待云端检查，不绕过失败合并 |

前四仓库本地默认分支已 fast-forward，并与 `git ls-remote` 核对 SHA；合并树与已验证候选树一致。它们未配置 PR 云端检查，不将空检查列表描述为 CI 通过。QGC 复用已有 PR #17，保留其原 UI 基线；仅复用 #16 已存在并核实的 Trivy action/tool 版本修正，不合并 #16 其他改动。其他开放 PR 不自动关闭或合并。

用户已有审计目录、QGC `.workbuddy/`、Rover WSL 构建入口及旧运行窗口均保留，未纳入提交。构建产物、日志不提交。仓库合并不是现场部署授权或验收结论；请按第七节成套升级，并先完成停止与低负载台架验证。
