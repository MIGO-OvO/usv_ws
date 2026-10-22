# 验证矩阵

Updated: 2026-10-23

## 采样请求 TCP 与结果恢复

| 验收场景 | 离线入口与断言 |
|---|---|
| 健康连接发送前延迟超过 30 ms | ROS `test_mavlink_tcp_transport.py`、`test_payload_transport_recovery.py`：连接保留、generation 不变、任务不停止；ACK/USV_DONE/文本/事件稍后完整发出 |
| 部分写入与背压 | 相同测试：offset=0 预算/背压延期；offset>0 截止或 EPIPE 退役、停止；记录真实写入偏移，不把未完成帧计入成功 |
| USVE1 续发 | `test_bridge_qml_event_chain.py` 单独运行于真实 pymavlink：短写、EAGAIN、首帧前及分片中途预算耗尽，所有片段最终解析完整；超过 1 秒组包期从新 id 的 chunk 0 重播 |
| 同身份恢复 | `test_payload_transport_recovery.py`：原终态、清理中重连、连续连接失败后恢复、同身份重试；seq/attempt/原因保持，START 一次；未知/冲突身份与旧执行实例不执行 |
| 泵节点完整调用链 | `test_qgc_payload_startup.py::test_tcp_loss_stops_real_preflight_and_recovery_never_restarts_pumps`：生产 trigger/pump/准备状态机，替换串口与 ROS 边界；准备中 TCP 退役发送 STOPALL，停止后查询/重试不再发泵命令，原因为 transport_session_lost |
| 旧结果与新任务 | ROS 新回归连续 8 轮开始/停止后再启动，重复、迟到、旧 TCP 事件不改新请求；QGC `test_transportCancellationRecoveryKeepsReasonAndNewTaskIsolated` 验证中文取消反馈、迟到结果隔离与停止未确认时保留锁 |

真实 socket、pymavlink、Qt 控制器与模拟串口调用链均为主机离线验证，不代表 Jetson、飞控、串口设备或实船通过。

### 执行记录

| 类型 | 结果与入口 |
|---|---|
| ROS 非地图回归 | `python -B tests/run_non_map_tests.py`：746 项，730 通过、16 跳过；排除地图相关 130 项。真实 pymavlink/TCP 独立运行；Linux/Bash 等环境跳过不计通过 |
| Linux/WSL 定向回归 | 独立 Python 进程运行 transport 7、真实 TCP 2、bridge 字节流 1、恢复 8，共 18 通过，0 跳过 |
| QGC Qt 控制器/布局 | Qt 6.10.1 `qmltestrunner -input custom/tests`，offscreen/software：88 通过、0 失败/跳过；Vehicle 为测试夹具 |
| QGC 契约 | `python -B -m unittest discover -s custom/tests -p test_usv_qgc_contract.py`：37 通过 |
| 根文档/源码契约 | `python docs/tools/check_workspace_compatibility.py`：Source contracts match；`python -B -m unittest discover -s docs/tools`：11 通过 |
| Windows 本地 | Qt 6.10.1/MSVC 14.44，以并行度 2 编译修改的 `Vehicle.cc`、`StatusTextHandler.cc` 对象及依赖通过（exit 0）。完整增量构建首次遇 C1060 编译器内存不足；本轮完整 Windows 应用尚未链接，未运行新二进制原生集成测试 |
| Windows/Android CI | QGC `2d3e0bf7657e13a9eea841c8675a2c32e4b1ce10` 的 [Windows](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850321936)、[Android](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850322366) 发布时运行中；未额外重跑同一 head，未完成不计通过 |

### 最小实机检查

1. 停止当前任务后一起更新 ROS bridge/trigger，重启载荷节点；运行包含新反馈与诊断的 QGC。飞控、检测板本轮不需刷写。
2. 保留同一时间窗 QGC `.tlog`/调试日志、Jetson `usv_system.log`/`mavlink_router.log`、`/usv/payload_event`、`/usv/sampling_result` 和 `/usv/bridge_diagnostics`。QGC 开启 `Vehicle.Vehicle` 与 `MAVLink.StatusTextHandler` 调试分类，记录 request/session/command、MAVLink seq、chunk id/seq。
3. Jetson 用 `sudo tcpdump -i lo -s 0 -U -w /tmp/usv-sampling-check.pcap 'tcp port 5760 or udp port 14550 or udp port 14551'` 抓取 router/bridge 链路；用新的输出路径保留每次现场证据。在停止状态导出飞控串口/路由参数和实际 router 命令行、版本，不修改 NO_FORWARD 等选项。
4. 正常链路连续开始/停止 10 轮，核对每个请求的受理/终态、每个 attempt 的实际动作次数和 STOPALL_OK。准备中断开 router TCP 后恢复，确认原请求取消并返回 `transport_session_lost`，同身份重试不能重新驱动泵。受控延迟/背压试验与真实断线分开执行。
5. 命令在 TCP 抓包中有合法完整帧而无 `Payload command rx` 时，对照 BAD_DATA 前缀、CRC/未知消息、解析器版本和原始字节；TCP 抓包中缺失时，继续取得飞控输入/输出或 router 串口入口镜像以区分上游路由。USVE1 对照 bridge 每片完整写入、TCP 出站片段、QGC tlog 和组包日志，确定尾片在哪一段消失。

本地 `2026-10-23 03-31-19.tlog` 包含 request 3/5/7、session 9 的三份 START（confirmation 0/1/2，目标 1/191）；71 组可识别 USVE1 中 10 组未见尾片，没有匹配 START 的完整结果。该 tlog 只证明 QGC 侧发送与接收事实，缺少同期上游入口和 Jetson 原始抓包，无法判定命令或尾片丢失在哪一跳。无线质量、NO_FORWARD 和 QGC 组包窗口均未作为已确认根因。

## 重叠停止与历史反馈（2026-10-21）

本轮只改 QGC 请求归属和反馈筛选，以及相关测试、文档；不修改 ROS、Vehicle C++、飞控或固件。下方 2026-10-20 数量属于此前记录，不代表本轮 head 的验证。

| 场景 | 行为入口与断言 |
|---|---|
| R1-A/B 真正重叠 STOP | Qt `test_overlappingSurveyAndDetectorStops` 两个数据行：走航一次 succeeded 后仍在轮次间隔，先连续发送 31016/31019，再按两种顺序交付各自 ACK/accepted；各存结果、清传输 pending、建立原走航停止依据；结果前 Idle 不退休，结果后新 Idle 才退休，无需第二次 STOP 即可新采样 |
| R1-C 旧 STOP 迟到 | `test_lateSurveyStopCannotStopANewerSample`：旧走航结束、旧 STOP 结束等待、新采样发出并运行后，旧结果只更新自身历史，不改新任务身份、停止依据、反馈、warning 或 pending |
| R1-D 分光范围 | `test_detectorStopAloneCannotCloseSurvey`：31016 尚无结果或明确拒绝时，仅 31019 accepted/ADS=1 及重复 Idle 均不能结束走航或确认泵停止；兼容 31016 路径也经过原信号与遥测 |
| R2-E 完整重新采样 | `test_retiredFailureDoesNotOverrideACompleteNewSamplingCycle`：普通失败→Idle 退休→31011 确认及新 Idle→31018 与有效帧→31017 基线→新 31010 accepted/运行/progress；读取真实 QML 绑定的 feedback/warning/taskFailed；旧终态、原因和阶段仍在 history，不伪造核验；旧迟到终态不覆盖当前请求 |
| R2-F 当前失败与实际限制 | 同一用例确认新任务自身失败仍显示；`test_retiredCleanupFailureStillRequiresVerifiedStop` 确认退休的 cleanup_failed 仍保持 outputs 锁及提示；复用现有主动急停与通信恢复行为检查 |

### 本轮验证分类

| 类型 | 实际入口 | 本轮结果/边界 |
|---|---|---|
| 真实 Qt 定向红绿 | `qmltestrunner -input custom/tests/tst_USVPayloadCommandController.qml` | 修复前 44 通过、3 失败：两种重叠顺序均缺 stoppedByRequest，重新采样仍显示旧失败；修复后 48 通过、0 失败/跳过（含补齐的兼容走航停止） |
| 真实 Qt 最终回归 | Qt 6.10.1 `qmltestrunner -input custom/tests`，offscreen/software | 72 通过、0 失败、0 跳过；PayloadController 48 项；本轮源码批次对应 QGC `716df904c8e856029ab4f9a9aad5d6af7b118437` |
| Python/Node 契约 | `python -B -m unittest discover -s custom/tests -p test_usv_qgc_contract.py` | 35 通过、0 失败/跳过；不等同 Qt 信号、绑定或 C++ 集成 |
| PySide6 行为 | 复用 `CockpitFixture.qml::verifyBehavior()`，仅运行行为入口 | Qt 6.10.1，60 项既有行为检查通过、无 QML 运行错误；未运行全视口截图，Vehicle 为 mock |
| Windows | `VsDevCmd.bat -arch=x64 -host_arch=x64 -vcvars_ver=14.44` 后 `cmake --build build/audit-debug-20261018-v2 --parallel 6` | 本轮 QGC head 的 Qt 6.10.1/MSVC 14.44 Debug 增量编译/链接成功（exit 0），含修改后的 QML 资源；无 C++ 改动，未扩大原生测试；发布时[当前 head CI](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39542755570) 运行中 |
| Android | 现有 Android 工作流的本轮 head | 发布时 [PR run](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39542755710) 与 [push run](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39542751177) 运行中，均由现有触发规则自动产生；未手动重复触发，未完成不能写通过 |
| 文档与源码契约 | `python docs/tools/check_workspace_compatibility.py`；`python -B -m unittest discover -s docs/tools` | Source contracts match；11 通过、0 失败/跳过；各仓 diff --check 通过 |
| 串口、台架、实机、抓包重放 | 本轮未执行 | 自动化与构建不替代现场验收；未部署、未刷写 |

### 构建与 CI 范围

长期规则见 `10_agent.md` 的“QGC 构建与 CI 验收”。构建验收只看 **Windows/Android 目标产物**；Ubuntu/macOS runner 或 Docker 构建 Android 仍计入。其他平台产物不排查详细失败、不修依赖、不重跑、不轮询等待，不作为本轮交付阻塞。保留改动相关的 QML/Python/ROS 逻辑验证，本轮不跑无关 ROS 全量回归。

复用现有工具链、目录和矩阵，定向验证后对最终修改批次构建；同 head 不重复触发，代码或明确环境修正后才重跑相关失败，不用空提交或连续重跑刷绿。旧全仓 lint 只记录，本轮引入问题就地修正。推送后与交付前必要时查看相关状态，长时间排队/运行则如实交付链接；旧 head 的绿色结果不能代替当前 head。非目标平台若被要求为合并必需项，只报告配置与验收范围不一致，保留分支保护。

### 本轮最小实机验收（未执行）

1. 走航完成一次采样后，在轮次间隔快速连续点击停止走航、停止信号；确认两条结果各自到达，旧任务退出，直接重新准备和采样，无需再次停止走航。
2. 制造普通采样失败，完成停止、分光启动、有效帧及基线准备，再启动新采样；当前提示属于新任务，旧失败原因仍保存在历史记录。
3. 单独停止分光不显示全泵停止；未确认输出停止和主动急停仍保留原限制与核验条件。

### 相对零点与传输回归

- ROS `test_calibration_lifecycle.py`、`test_preflight_web_contract.py`：不同轴非零偏移、跨0°、未校准、保存/重启显示一致、真实 PID_DONE、STOP/超时/断线、清理失败不能先发成功终态，以及同身份重传仅下发一次相对运动。
- ROS `test_payload_event_bridge.py`：请求/回执丢失、RequestLedger 重放、trigger 单独重启、capability 到达顺序与旧实例拒绝。
- QGC `SendMavCommandWithSignallingTest::_payloadReceiptOrderingAndButtons`：真实 Vehicle + FactGroup 分帧 + Button.enabled，覆盖 ACK/USVE1 两种顺序、旧 ACK/旧事件、同 command 连续请求、STOP、有限重传和原生超时释放。QML mock 测试只作控制器回归。
- 构建以 Windows/Android 为限。USV 默认 `DISABLE_SPEECH=ON`；同时核对 OFF 语音路径、ON 无 TextToSpeech 导入及 Windows 部署依赖，其他 Multimedia 功能保留。`AudioOutputTest::_speechConfiguration` 验证禁用接口、隐藏设置与声音起航检查。
- 台架仍须验证两端回到同一保存零点、R0/跨0°的真实完成、回零中 STOP 与断线看门狗、丢包重传物理动作一次，以及校准单独回零/自动化补偿分隔各自范围。离线通过不替代 Jetson、Android 或设备验收。

## PID 油相分隔与日志管理验证

- ROS `test_automation_preflight.py`、`test_preflight_review_regressions.py`、`test_preflight_stop_races.py`、`test_sampling_timeout_budget.py`：多圈 PID 分段、最低速度与 30 秒限时、每段真实 PID_DONE、角度不足/跳变/断流/停滞、STOP 抢占、任务归属及失败锁存。分隔不发送 J；回零、360° 补偿、进样与正式序列沿用原流程。
- ROS `test_usv_cli_scripts.py`、`test_usv_logs.py`：旧命令文件与符号链接备份迁移、重复安装及卸载、预览不删除、最近数量优先于容量、活动/一小时保护、预算告警和自动清理显式启用。Linux `/proc`、Bash 与临时目录用于执行日志回归。
- Jetson/ESP32 台架：验证实际 PID 参数下油相泵带负载起转、跨零点十圈与分段衔接；逐段确认 PID_DONE 与角度行程。分隔中 STOP、断开角度反馈及串口，核对真实输出停止、故障锁存与新任务归属。核验现有命令备份后再清理预览，重要现场日志先打包下载。离线回归不代替设备验收。

## 停止恢复闭环验证边界（2026-10-20）

本轮保留既有内存关联、去重、尽力 JSONL 与 STOP 通道，围绕 F1–F6 补齐行为回归。测试使用生产控制器/模块，替换 ROS、串口或 RPC 边界；并发交错使用 Event/barrier。它们不代表设备已经完成现场验收。

| 范围 | 入口 | 覆盖 |
|---|---|---|
| F1：新 START 与同值 Idle | `custom/tests/tst_USVPayloadCommandController.qml` | START→同值 Idle→accepted→真实运行→正常失败/cleanup_failed；超时后同值 Idle 仍不退休；走航单次成功不结束调度；各自 STOP 结果加新 Idle 能收敛 |
| F2：旧测量观察 | ROS `tests/test_stop_recovery_contract.py` 的 `FreshnessInterleavingTests` | 原 reader 新帧→原 PRE verifying/交接→真实 AutomationEngine；旧 runtime 本次 STOPALL_OK 后被新 attempt 替换；同 runtime 新帧；均比较数据、聚合、原因、清理与 STOP 副作用；真实持续超时停止，拒绝 STOP 不报成功 |
| F3：通信恢复 | QGC `custom/tests/CockpitFixture.qml`、`test/Vehicle/SendMavCommandWithSignallingTest.cc::_payloadCommunicationRecovery` | Payload/Cockpit 信号绑定与 Vehicle 锁共同验证；整链断开→重连→本次 31011 ACK/accepted→新 Idle，仍 armed 可恢复；仅重连/Idle、旧 STOP、ADS-only、明确失败不能解锁；主动急停来源保留，仅载荷离线不锁船 |
| F4：阶段重放 ACK | ROS `tests/test_payload_disk_stop.py` 的 `JournalFaultTests` | 真实接收、handler/RPC 与内存 ledger；accepted、progress、成功/失败/取消 terminal、拒绝、尚无事件在途请求；ACK 按 phase/outcome，原事件 seq/attempt 不变、动作一次、generation 不变 |
| F5：兼容 STOP | QGC `custom/tests/tst_USVPayloadCommandController.qml` | 无身份 31011/31019→ACCEPTED→对应新状态→多帧；不再等 USVE1，ADS-only 不确认泵停止；IN_PROGRESS 不提前成功，FAILED/DENIED、错误目标与迟到 ACK 不覆盖结果 |
| F6：走航取消范围 | ROS `tests/test_payload_disk_stop.py` 的 `SurveyCancellationTests` | 独立 31018 的真实服务边界阻塞时无走航 31016 不取消；已受理未执行/未激活 31015 被取消，不创建 scheduler/采样/迟到 started；真实 scheduler 启动采样后清理同一 attempt；满队列、重放、异常退出不遗留标记或错误推进 generation |
| 保留路径 | ROS `test_payload_protocol.py`、`test_sampling_timeout_budget.py`、`test_mavlink_framing_contract.py`、`test_stop_recovery_contract.py` | 内存去重、可选日志、超时预算、CRC/分帧、机械 PRE 不等测量、正式交接仍需测量、真实停止确认及旧锁存释放 |
| 日志阻塞 | ROS `test_payload_disk_stop.py::JournalFaultTests` | 在日志写入 barrier 解除之前，STOP 已执行、ACK 已发且通道已释放；不可写日志不阻塞受理 |

### 执行记录与验证类型

以下命令在对应仓库运行；构建与测试日志留在被忽略的 `build/` 下，不随源码提交。

| 类型 | 实际入口 | 结果/边界 |
|---|---|---|
| Python 语法 | ROS `python -m py_compile scripts/mavlink_trigger_node.py scripts/pump_control_node.py tests/test_payload_disk_stop.py tests/test_stop_recovery_contract.py` | 通过；不是 ROS on-device 运行 |
| ROS 直接行为 | `python -B -m unittest discover -s tests -p <文件名>` | `test_payload_disk_stop.py` 12、`test_stop_recovery_contract.py` 22、`test_payload_protocol.py` 11、`test_sampling_timeout_budget.py` 8、`test_mavlink_framing_contract.py` 5；均通过 |
| ROS 非地图回归 | `python -B tests/run_non_map_tests.py` | 712 项，699 通过、13 跳过，地图相关 130 项排除；跳过为真实 pymavlink/TCP 独立运行 1、Linux logrotate 1、Linux/WSL Bash/Git CLI 11 |
| 真实 Qt Quick Test | Qt 6.10.1 `qmltestrunner -input custom/tests -o build/tests/all-qml-final-20261020.txt,txt`，offscreen/software | 65 通过、0 失败、0 跳过；其中 PayloadController 41 项 |
| Node 原函数/源码契约 | `python -B -m unittest discover -s custom/tests -p test_usv_qgc_contract.py` | 35 通过；此层不能证明 Qt Timer、信号或 C++ 集成 |
| PySide6 真实 QML 夹具 | `python -B custom/tests/verify_workflow_ui.py --output build/stop-recovery-workflow-final`；`verify_cockpit_ui.py --output build/stop-recovery-cockpit-final` | Workflow 37 行为检查、13 视口/状态；Cockpit 60 行为检查、23 视口/状态、28 键盘目标；无 QML runtime error；Vehicle 为 mock |
| C++ 编译/链接 | VS 2022 `VsDevCmd.bat -arch=x64 -host_arch=x64 -vcvars_ver=14.44` 后 `cmake --build build/audit-debug-20261018-v2 --parallel 6` | 包含本轮 `Vehicle.cc/h` 与原生集成测试；Qt 6.10.1 Debug；完整编译和链接已通过 |
| 原生 Vehicle/QML 集成 | `QGroundControl.exe --allow-multiple --no-windows-assert-ui --unittest:SendMavCommandWithSignallingTest` | 11 通过、0 失败、0 跳过；使用真实 Vehicle、FactGroup、MAVLink 分帧/标准 ACK、Payload/Cockpit，含 armed 通信恢复 |
| CI | 最终远端 head 的 checks | 按发布后实际状态报告；不借用旧 head 的成功 |
| 根文档/跨仓源码契约 | `python docs/tools/check_workspace_compatibility.py`；`python -B -m unittest discover -s docs/tools` | 源码契约匹配；11 通过、0 失败；不是 SITL/台架/现场验收 |
| 台架、实机、抓包重放 | 本轮未执行 | 无 Jetson/串口/检测板/飞控现场接入；未部署或刷写 |

初次构建混用了 14.44 编译器与 14.51 STL，报 `STL1001`；按缓存固定 `vcvars_ver=14.44` 后解决。初次原生测试未配置 offscreen plugin 路径，启动失败；设置 `QT_QPA_PLATFORM_PLUGIN_PATH=C:\Qt\6.10.1\msvc2022_64\plugins\platforms` 后可运行。其遗留测试进程导致一次 `LNK1168`，仅终止该测试进程后重新链接成功。新集成测试帧缺少必填 reason/preflight_phase 的夹具错误已补齐，不把该次失败计为通过。

夹具已移除失效的 `expireTelemetry()`/`clearEmergencyRequest()` 调用；同值状态也增加接收 sequence，mock 维护 pending 命令并由匹配 ACK 清除；关联 START 不由普通 ACK 完成，时间测试推进模拟时钟。

### 台架最小清单

先停机更新 ROS 的 trigger/pump 文件并成套重启 trigger、pump、bridge，使用本轮重新构建的 QGC；不改固件/参数。保留独立断电手段，涉及 armed 的通信测试先隔离推进硬件。

| 场景 | 最小步骤与必须观测 |
|---|---|
| F1 正常与失败 | 准备分光/基线→31010→在 accepted 前观察周期 Idle→运行→成功或普通失败；Idle 不放行第二个物理任务，真正失败有原因；再 31011 确认→重新准备/采样，无需重启 |
| F2 测量交接 | 机械 PRE 保留归零/360°/油相 X 圈/进样预启动；短暂断帧后在 verifying 前恢复真帧，确认正式交接及聚合不被旧检查清空；持续缺帧则真实 STOPALL_OK，故意拒绝 STOP 不能显示成功 |
| F3 普通恢复 | 任务运行→切断整条 QGC MAVLink→重连→仅 Idle 保持通信锁→新 31011 的标准 ACK/关联 accepted→其后新 Idle；保持逻辑 armed 可重新准备，不触发 disarm/模式改变、不声称推进已停；另测主动急停仍需原核验，仅 ROS 离线不新增锁 |
| F4 重传 | 在已受理/进度/成功终态后分别重传同身份帧，保存 ACK 与 USVE1；ACK 为 ACCEPTED/IN_PROGRESS/ACCEPTED，原 seq/attempt 不变、设备动作一次；拒绝/失败保留原语义 |
| F5 兼容停止 | 用无身份旧客户端发 31019→本次 ADS_OK:STOP/ACCEPTED→多帧 ADS=1，不再等 USVE1；手动进样泵不据此显示已停；另测无身份 31011→STOPALL_OK/ACCEPTED→Idle |
| F6 走航范围 | 无走航时独立 31018 启动过程中发 31016，分光仍成功；受理 31015 后立刻 31016，STOP 后无新的 survey_started/采样动作；活动走航停止清理对应 attempt；31016→31019 各自得到结果 |
| 抓包与现场闭环 | 同一窗口保存 QGC `.tlog`、Jetson `.pcap` 及 ROS/串口日志，分别核对命令到达、ACK 返回、关联结果与设备执行；本轮未执行抓包重放或实船验收 |

## 跨端修复验证边界

2026-10-19 本轮按用户要求跳过地图测试，不修改地图功能。可重复入口：ROS `python -B tests/run_non_map_tests.py`，QGC 控制器 Qt Quick Test、真实 Vehicle/StatusText 单测，DetFirmware native/PIO，Rover SITL/Pixhawk6C。结果及版本清单见 `docs/reports/2026-10-18-cross-end-code-repair-plan.md`。

续修实际基线、逐项红绿、最终 PR/CI 分类与候选指纹见 [2026-10-19 续修闭环](../reports/2026-10-19-audit-followup.md)。不以旧审计 SHA、旧构建或正在运行的旧 QGC 窗口代表本轮产物。

重点覆盖：旧动作取消与重连、STOP 不等长事务/磁盘、当前会话真帧与基线、2 秒失效/10 秒有界恢复、ADS I²C 互斥与真实 POWERDOWN、TCP 背压/部分帧/会话换代、26 字段独立年龄/公平转发、请求持久化与分片重组、校准完成与失败首因、Web 最终结果导出。

所有设备更新、烧录、台架、低剂量及实船测试由操作者执行。需保留独立断电手段并测量真实停机时间；不能把 ACK、离线测试或编译通过当现场验收。地图相关章节保留为后续参考，本轮未执行。

## 静态验证

| 项 | 命令/方法 | 通过标准 |
|---|---|---|
| current 文件集 | `Get-ChildItem docs/current` | 仅编号当前文档 |
| 归档存在 | `Test-Path docs/archive/2026-05-20-current-pre-restructure` | 返回 true |
| 本地路径引用 | 手动/脚本检查反引号路径 | 根仓库内路径存在；外部子仓库路径明确 |
| 旧入口污染 | 搜索旧入口名、旧字段数、旧频率说法 | current 不出现过时说法 |
| MAVLink 字段 | 对照 `Rover/USVPayload.h`、bridge、QGC FactGroup | 26 字段名称一致 |
| Mission 采样指令 | 对照 `mode_auto.cpp`、QGC `MavCmdInfoRover.json` | 航线定点采样为 `MAV_CMD_NAV_SCRIPT_TIME`，不使用 mission `31010` |
| COMMAND_LONG | 对照 `mavlink_trigger_node.py`、`usv_mavlink_router_bridge.py` | 手动 `31010..31019` 一致 |
| 串口握手 | 对照 `pump_control_node.py`、`DetFirmware/src/main.cpp` | `HELLO?` / `DET_ID` 一致 |

## ROS 离线验证

| 项 | 命令 | 通过标准 |
|---|---|---|
| Python 语法 | `python3 -m py_compile src/usv_ros/scripts/*.py` | 无语法错误 |
| Launch 参数 | `roslaunch usv_ros usv_bringup.launch --dump-params` | 参数可展开 |
| 单元测试 | `python3 -m unittest discover -s src/usv_ros/tests -p 'test_*.py'` | 全部通过 |
| 本轮非地图回归 | ROS 内 `python -B tests/run_non_map_tests.py` | 明确排除项、环境跳过与失败数；不得宣称全地图验证 |
| 测量最终边界 | ROS 内 `python -B tests/test_remaining_measurement_paths.py` | scoped 停止不等帧、lead 后重验、生产错误帧及时终止；短静默仍可有界等待 |
| 事件首发与背压 | ROS 内 `python -B tests/test_event_delivery_priority.py` | 新转换/终态不被历史拖延、STOP 优先、容量有界、完整帧 |
| 真实协议联测 | 真实 pymavlink 环境运行 `tests/test_bridge_qml_event_chain.py`，将其完整 MAVLink2 帧交给原生 QGC 测试 | 丢 accepted 后合法空 outcome progress 仍进入执行；最终成功必须 terminal |
| lab_sim 库编译 | `python3 -m py_compile src/usv_ros/scripts/lib/lab_sim/*.py` | 无语法错误 |
| 前端构建 | `cd src/usv_ros/frontend && npm run build` | 构建成功；产物写入 `static/dist` |
| 系统健康节点 | `rostopic echo -n 1 /usv/system_health` | Jetson、detector、ROS 节点字段存在 |

## 实验仿真 Schema v2 验证

坐标真源、液滴事件粒度和科研导出的验收阈值与命令（在 `src/usv_ros` 目录执行）：

| 项 | 命令 | 通过标准 |
|---|---|---|
| 坐标 round-trip | `python3 -m unittest tests.test_lab_sim_coordinates` | WGS-84 -> GCJ-02 -> WGS-84 桂林/上海/北京点地面误差 `<=0.5 m`；非法/非有限坐标拒绝 |
| 图面对齐 | 浏览器 Lab/Map 页 | 点击点、保存后航点 marker、船位到点 marker 中心图面距离 `<=2 CSS px` |
| schema v2 数据类 | `python3 -m unittest tests.test_lab_sim_models` | 默认值、边界、非法 schema、JSON round-trip 通过 |
| 坐标迁移 | `python3 -m unittest tests.test_lab_coordinate_migration` | 裸 `{lat,lng}` 按 GCJ-02 迁移幂等，响应含 `wgs84`+`gcj02`，`missing_crs` 被拒 |
| auto-scan API | `python3 -m unittest tests.test_lab_auto_scan_api` | 返回双坐标航点与 64 位 `water_snapshot_hash`，`preview=true` 不保存 |
| 液滴事件粒度 | `python3 -m unittest tests.test_lab_sampling_event_storage` | 1 事件=1 写入=1 `data_point`（携带 `sample_event_id`/`droplet_count`）；100 事件 => 100 点 + 100 次写入 |
| 校准互逆 | `python3 -m unittest tests.test_lab_sim_calibration` | Beer-Lambert/工作曲线互逆误差达标；零斜率/无效电压返回 typed error |
| 科研 surface/图件 | `python3 -m unittest tests.test_lab_surface_export` | 六层 surface polygon 外严格 mask；导出 PNG/TIFF/SVG/PDF + metadata，DPI 与像素尺寸正确 |

## MAVLink 联调

| 场景 | 步骤 | 通过标准 |
|---|---|---|
| router 启动 | `usvon` 后 `usvstatus` | router pid 存在，TCP 5760 可用 |
| MAVROS 连接 | `rostopic echo -n 1 /mavros/state` | `connected: True` |
| QGC 手动命令 | QGC 发送 `COMMAND_LONG 31010` | `/usv/mavlink_cmd_rx` 收到，trigger 发布状态，ACK 返回 |
| QGC 冷启动 | ROS 启动后立即点击启动信号 | bridge 不等待飞控心跳才开始接收；采样 owner 在 MAVROS 初始化等待期间仍每秒续约；31018 的关联 accepted 确认启动命令成功（配置回显 + ADS_OK:START），首帧与基线由遥测另行决定采样就绪 |
| QGC 点采样进样 | Web 自动进样策略设不同于 `default_speed` 的速度，QGC 启动点采样 | 准备完成后按策略速度开启进样泵；准备时不提供暂停，主按钮可停止准备 |
| QGC 普通停止 | 准备、采样、暂停阶段分别点击 `31011` | 取消当前流程并请求全部输出停止；关联终态/清理结果与实物停止分别确认，标准 ACK 不代替它们；不依赖紧急停止；Web 记录窗口按匹配结果关闭 |
| 校准命令 | QGC 发送 `31014` | `/usv/pump_command` 出现 `CALXYZA` |
| 遥测字段 | 运行 bridge | QGC 显示 26 字段；固件 2 Hz 公平转发，停源后不续旧值 |
| 健康遥测 | 运行 system health + bridge | QGC 显示 `USV_JTMP/ETMP/JCPU/JMEM/EHEAP` 对应 Fact |
| 电台链路 | RADIO_STATUS 输入 | `/usv/radio_status` 有 rssi/remrssi/noise 等字段 |

## 采样闭环验证

QGC 启动/普通停止离线回归：ROS 下 `python -B -m unittest discover -s tests -p test_qgc_payload_startup.py`；QGC 下 `python -B -m unittest discover -s custom/tests -p test_usv_qgc_contract.py` 和 `python -B custom/tests/verify_workflow_ui.py`。真实停泵、冷启动延迟和无线 ACK 往返仍需上述台架步骤。

| 步骤 | 观测点 | 通过标准 |
|---|---|---|
| 固件触发 | `NAV_SCRIPT_TIME(param1=1)` | ROS bridge 收到 `USV_SMPL` |
| ROS 采样 | `/usv/trigger_status`、`/usv/pump_status` | 出现 `sampling_started`，状态进入采样并执行序列 |
| QGC/Web 记录 | QGC 采样数据页、Web 数据中心 | `USV_SCNT` 为启动次数而非成功计数；Web 新任务记录有效数据点增长，成功另看匹配终态 |
| 完成通知 | bridge 日志、固件行为 | ROS 发 `USV_DONE`，固件继续 mission script |
| 失败策略 | 配置 `HOLD/SKIP/ABORT` | 行为与配置一致 |

## FCU 采样结果安全回归

离线：在 `src/usv_ros` 执行 `python3 -m unittest discover -s tests -p 'test_fcu_sampling_result.py'`。测试使用真实 trigger/bridge 方法和模拟传输，不连接设备。

现场需同步记录 `/usv/sampling_result`、`/usv/trigger_status`、`/mavros/state` 与 MAVLink 消息：

| 场景 | 通过标准 |
|---|---|
| 正常完成 | 同 ID `succeeded` 后才有 `USV_DONE`；重复结果不重复放行 |
| 进样启动失败、自动化启动失败、PID 超时 | HOLD/ABORT 下为 `failed`，无 `USV_DONE`，记录窗口结束；单独确认实际 HOLD |
| QGC 31011、Web 自动化停止 | `cancelled`，无 `USV_DONE`；停止服务期间到达的 finished 不可覆盖取消 |
| 明确 SKIP | 结果为 `skipped` 而非成功，允许同 ID `USV_DONE` |
| 重复触发、旧 ID/非法/非 FCU 结果 | 不重复采样，不释放当前新 ID；新 ID 清除未发送的旧完成通知 |
| 普通 sampling_stopped | 不生成完成通知；有 attempt 的真实窗口等待匹配最终结果后关窗 |

必须停机更新并成套重启 trigger/bridge/pump。离线测试不能证明实际船态、跨重启 ID 复用或无线端到端送达；safety1 的超时/失联 HOLD 必须补 SITL 和实船验收。

## safety1 安全回归与发布门槛

离线命令（在各仓库根目录）：

- ROS：`python -B -m unittest discover -s tests -p 'test_system_safety_contract.py'`、`test_sampling_context_contract.py`、`test_web_control_access.py`，再跑全量 `test_*.py`。
- 串口联合黄金帧：ROS 下 `python -B -m unittest discover -s tests -p test_detector_protocol_contract.py`；完整工作区及 PySide6 可用时，将同一有效/测试/坏校验帧分片送入 ROS 和 Windows 的真实解析器比较。
- ArduPilot（Linux/WSL）：`python3 -B tests/test_usv_sampling_safety.py`，执行真实 verifier 函数的宿主 C++ 回归；不是 SITL。另按 runbook 编译目标固件。
- 隔离 SITL：在 ArduPilot 仓库构建 Rover 后运行 `python3 -B tests/check_usv_sitl_sampling.py --binary build/usv-safety-sitl/sitl/bin/ardurover --scenario all`，按实际构建目录调整路径。脚本创建私有仿真进程和回环 UDP（默认实例178），不连接既有飞控，检查成功/取消/超时/伴随失联/MANUAL接管/RTL接管六场景，并断言同 ID 失败通知、时间窗与迟到 DONE 后不推进。
- DetFirmware：`python -m pytest tests -q`；Linux/WSL `python3 -B tests/test_control_watchdog_native.py`；`pio run -e nodemcu-32s`。源码测试不替代实际电机停机测试。
- Windows：`python -m pytest tests -q`；QGC：`python -m unittest discover -s custom/tests -p test_usv_qgc_contract.py`。
- 总仓库：`python docs/tools/check_workspace_compatibility.py`、`python -m unittest discover -s docs/tools`。

必须人工/台架验收：

| 场景 | 必须观测 |
|---|---|
| AUTO 内采样超时、bridge 断连、ROS 失败、取消 | 飞控实际 HOLD；不推进后续航点；检测输出停止；无成功采样结果（记录文件结束不等于采样成功） |
| 人工切 MANUAL/RTL 后迟到失败 | 取消旧采样，保留操作者选择的飞行模式 |
| 明确 SKIP | 只在同 ID `skipped` 后放行；超时/失联本身不算 SKIP |
| USB 拔除、控制进程终止、Windows UI 卡死 | ESP32 约 3 秒心跳期限后停止全部执行器；迟到心跳/旧运动命令不复位锁存 |
| trigger/Web owner 进程终止 | pump 约 5 秒后取消本次自动化；FCU owner 丢失触发 `USV_FAIL`；重启不续跑旧步骤 |
| 校准/PID 测试/开环运行中各停止入口 | STOPALL、Web 急停、QGC 停采样均不产生后续动作；暂停不能被错误转成完成 |
| 运行中重连 | 原采样取消；新连接 ARM 前停输出；不得返回旧任务 succeeded |
| ADS 停流/错误/FULL 压测 | 有效位及时清零；测试帧不进入真实记录；基线不得使用过期测量 |
| 两个来源同时启动/迟到步骤 | 恰好一个启动成功；执行其提交的配置和 attempt_id；另一个明确拒绝 |
| 整船重启/丢失 USV_DONE | 不自动将旧 ID 放行；人工确认当前船态与采样状态；本版本尚无跨重启交付保证 |

验收记录须含五端提交号、固件/应用产物 SHA-256、配置快照、事件日志和实际执行器证据。不得仅凭通过源码契约检查标记为可上船。

候选快照现为 schema 3：未跟踪且未忽略文件的规范路径、类型及原始内容/链接目标摘要纳入身份。旧 schema 2 清单须重新生成，不能直接比较。`--require-release` 仍拒绝 dirty 子仓库并要求验收与产物摘要；保留用户未跟踪文件的候选如实标 dirty，不等于发布门禁已通过。

## 检测装置验证

| 项 | 方法 | 通过标准 |
|---|---|---|
| 串口识别 | Web 测试端口或 ROS 启动 | 返回 `DET_ID:USV_DETECTOR*` |
| 角度帧 | 监听 `/usv/pump_angles` | X/Y/Z/A 持续更新 |
| 分光帧 | 监听 `/usv/spectrometer_voltage` | voltage/absorbance/valid 字段存在 |
| 健康帧 | 监听 `/usv/detector_health` | `temperature_c`、`heap_percent_free`、`task_stack_hwm` 字段存在 |
| 基线 | Web 或 MAVLink `31017` | `USV_BSET=1`，`USV_BASE` 更新 |
| 自动化 | 启动采样序列 | step/total/sample_count 递增 |

## Web 系统健康验证

| 项 | 方法 | 通过标准 |
|---|---|---|
| REST 快照 | `curl http://127.0.0.1:5000/api/diagnostics/system` | `success=true`，包含 `latest` 和 `history` |
| Socket.IO | 打开 Web 监控页 | 系统健康卡片随 `/usv/system_health` 更新 |
| Jetson 指标 | 查看 Web/ROS JSON | CPU、内存、温度、uptime 字段存在；无温度传感器时为 `null` |
| ESP32 指标 | 查看 Web/ROS JSON | 串口健康帧在线时显示温度、heap、任务栈水位 |

## 污染物地图离线验证

| 项 | 方法 | 通过标准 |
|---|---|---|
| Web 浓度模型 | `python -m unittest tests.test_hardware_runtime_sync.HardwareRuntimeSyncTests.test_web_records_geo_sample_with_concentration_when_work_curve_enabled` | 数据点含污染物名称、单位、校准 ID、浓度和质量快照 |
| Web 热力图 API | `python -m unittest tests.test_hardware_runtime_sync.HardwareRuntimeSyncTests.test_web_idw_surface_uses_valid_metric_points` | GeoJSON 与 surface 含 `meta`，IDW 只使用有效 GPS/分光/量程点 |
| 走航门控 | `python -m unittest tests.test_mavlink_command_compat.MavlinkCommandCompatibilityTests.test_survey_gate_uses_wgs84_distance_from_last_successful_start` | WGS-84 距离不足时只发布 `survey_gate_skipped:distance_too_short` |
| 职责边界 | `rg -n "污染物|热力图|浓度|QGC|ArduPilot|DetFirmware" docs/current src/usv_ros/README.md` | 文档明确：ROS/Web 负责污染物地图；QGC 第一阶段不做热力图；ArduPilot/DetFirmware 不计算浓度 |

## 污染物地图现场取证

第一阶段以 Web 为主，不在 QGC 绘制污染物热力图。现场验收必须把数据、截图和 MAVLink 闭环日志放到同一个 `mission_id` 证据目录。

| 证据 | 获取方式 | 通过标准 |
|---|---|---|
| 任务原始数据 | `GET /api/data/mission/<mission_id>` | 含采样点、GPS、分光质量、污染物浓度与校准元数据 |
| CSV | `GET /api/data/mission/<mission_id>/csv` | `csv_rows` 与任务有效记录数可对账 |
| GeoJSON | `GET /api/data/mission/<mission_id>/geojson?metric=concentration&download=true` | feature 数等于 `valid_gps_points`，剔除原因可追溯 |
| IDW surface | `GET /api/data/mission/<mission_id>/surface?metric=concentration&size=80&power=2&download=true` | `surface_grid`、`power`、有效点数和污染物单位写入 `meta` |
| 实时快照 | `GET /api/map/live` | 包含当前 surface、轨迹、`survey_status` 与 `mapping_profile` |
| 桌面截图 | Web 地图页 16:9 | 点位、热力图、图例、质量统计、走航门控状态均可见 |
| MAVLink 日志 | `grep -E "USV_SMPL|USV_DONE|USV_SURV|survey_gate_skipped" usv_system.log` | 定点采样存在 `USV_SMPL/USV_DONE` 闭环；走航跳过只记录门控原因 |

## 现场验证记录模板

| 时间 | 固件 commit | ROS commit | QGC commit | 场景 | 结果 | 备注 |
|---|---|---|---|---|---|---|
|  |  |  |  | QGC 31010 定点采样 |  |  |
|  |  |  |  | NAV_SCRIPT_TIME 闭环 |  |  |
|  |  |  |  | 走航采样 |  |  |
|  |  |  |  | 分光基线 |  |  |
|  |  |  |  | 电台链路 |  |  |

污染物地图证据模板：

| 字段 | 记录值 |
|---|---|
| `mission_id` |  |
| `pollutant_name` / `unit` |  |
| `calibration_id` / `work_curve_id` |  |
| `sample_total` / `csv_rows` |  |
| `valid_gps_points` / `excluded_points` |  |
| `excluded_reasons` |  |
| `surface_grid` / `idw_power` |  |
| `survey_min_distance_m` / `last_gate_reason` |  |
| `screenshot_path` |  |
| `USV_SMPL/USV_DONE` 日志 |  |
