# 2026-10-19 跨端审计续修闭环

本轮边界：分仓提交、推送和 PR；不合并、不部署、不刷写、不启动真实泵。地图测试排除。离线/原生 Qt/SITL 结果均不等于 Jetson、台架或实船验收。

## 实际起点

2026-10-19 修复前重新读取本地 Git 与 GitHub PR，未把审计时 SHA 当作当前源码，也未把源码当作运行程序版本。

| 仓库 | 本地 HEAD | 分支 | 修复前工作树 | 上轮 PR 最新状态 |
|---|---|---|---|---|
| usv_ws | `0d912eee7c270b941c82d01c33b52728260ef4c9` | `codex/cross-end-safety-docs-20261019` | 仅旧审计目录未跟踪 | #24 OPEN，head 同本地 |
| usv_ros | `778d055c9df80d2b9f29872fc54eeb8a2c34df93` | `main` | 干净 | #87 MERGED，PR head `a2d0364adfe561825f44291a2bc43df355c61c59` |
| QGC | `15e924c5d9c2090b5e20dbdfb19a7d7bafcf38fb` | `codex/usv-operations-ui` | 仅 `.workbuddy/` 未跟踪 | #17 OPEN / UNSTABLE，head 同本地 |
| ArduRover | `925ee45f568521efdbb0b39b69b94ab81e11625d` | `master` | 两个用户构建脚本未跟踪 | #10 MERGED，PR head `d5cc7a07d181b94181e5a04ea2b3a8fc3af65642` |
| DetFirmware | `186427df75047c0212d74969df2c18a3df01fd40` | `main` | 干净 | #3 MERGED，PR head `49c6fa17967b6e567fc3a8845b13de4446826d1f` |
| Windows | `241ee6230576289b78448075525b57ffd611535a` | `master` | 干净 | #8 MERGED，PR head `a8dfdf64905d9cc8c753b32b7ce1459464af2f37` |

所有仓库修复前 tracked/staged diff 均为空。新续修分支为 ROS `codex/audit-measurement-events-20261019`、Rover `codex/audit-link-policy-20261019`、Windows `codex/audit-stop-session-20261019`；QGC/根继续更新开放 PR。

未跟踪内容已审查用途，全部保留且不暂存：

- 根 `USV_Cross_End_Audit_2026-10-18/` 为原始报告、源码清单、失败输出和审计测试，不是本轮实现。未发现新版 `USV_PR_Audit_2026-10-19.zip`，因此按用户复现补生产路径回归。
- QGC `.workbuddy/memory/` 三个既有上下文文件，不属于业务源码。
- Rover `build_ardurover_wsl.cmd` / `.ps1` 是用户 WSL 构建和刷写交接工具，不执行、不修改。原始 SHA256 分别为 `6fa8a456c4b3cf7e0c80122d501c58cdf65fcacd1c3b346494c04f174000ff10`、`6e0f8b1975d335f3785a7739d5e66f28b092ba21a895284b879b73cbebc874d3`。

## 写入责任及闭环标准

ROS 测量门禁/引擎由 `ros_measurement` 负责；QGC 控制器/任务显示由 `qgc_lifecycle` 负责；Windows 回复范围/reader 会话由 `windows_scope` 负责。主代理负责 ROS bridge、Rover 链路策略、根快照工具、集成与发布。每个文件只有一个写入负责人。

| 项目 | 起点核验 / 最小复现 | 修复与回归证据 | 剩余限制 |
|---|---|---|---|
| P1-1 停止受测量门禁阻塞 | 成立；帧龄 1.9 秒，经 PIDQUERY ACK 0.4 秒后 OFF 原实现多等 1.7 秒 | `_send_preflight_command` 对可信当前任务 OFF/轴 DFV0J0 不等测量；回归含旧 owner 不得停新任务 | 只证明软件发送时序；不据有限 J 行程的 disable 延迟推断额外运动 |
| P1-2 lead 后新动作未复查 | 成立；真实引擎暂停且 OFF 后恢复，3 秒 lead 后 stale 仍写 AEFR180.0P0.1 | `_send_automation_step` 最终 serial_lock 内重验测量/取消/连接/owner；短静默锁外等帧，STOP/故障可打断 | 假串口，不等于实物进样与停机验收 |
| P1-3 明确分光错误未终止 | 成立；生产解析器正确 checksum 的 0x09 VALID/SATURATED 帧后，PID/长 interval 继续且被改成 stale | reader 保留 `spectrometer_not_ready` 首因及明确状态；`notify_failure` 唤醒引擎线程收尾，定时等待分段不超过 50 ms；不在 reader 等 ACK/join | 普通静默仍保留原 2 秒失效/10 秒恢复窗口；新帧不清故障、不续泵 |
| P1-4 progress 丢失 accepted | 成立；accepted seq=1 后合法 progress seq=2，旧 bridge 只留最新，QGC 5 秒后 unknown/锁定 | bridge 保留每请求首个未发转换与最新 progress，终态覆盖；QGC 对身份/attempt/序号合法且 `outcome==""` 的 progress 直接证明 executing，不要求更早 accepted；最终成功仍须 terminal。`test_event_delivery_priority` 7 项、`test_bridge_qml_event_chain` 真实 pymavlink、QML 46 项、原生 10 项通过 | 32 请求/30 秒缓存不变；全 STOP 超载仍可能淘汰证据，客户端必须 fail closed；不把 progress 当成功 |
| P1-5 短命令覆盖物理任务 | 成立；暂停后原采样 failed/cleanup_failed 只进 history 不报警；断线不锁原任务；校准 31014 未纳入 reset | `request` 与 `activeTask` 分离；失败/cleanup_failed 按 Vehicle 留在 history，直到 `confirmPhysicalStop`；`reset` 覆盖 31014，切船按 Vehicle 隔离。定向 QML 7 项、46 项全量、原生生命周期通过。修复中发现并修正“断线时 failed+cleanup_failed 被直接丢弃”的回归 | 保留正常暂停/恢复和 STOP；锁定的是未核验物理停止，不是禁止操作 |
| QGC 阶段残留 | 成立；固定“保持稳定”，仅按 hasMission 区分航线/手动 | `USVCurrentTaskPanel` 由 activeTask、attempt、preflight_phase 和任务来源显示准备/执行/结果；航线阶段只在真实走航状态出现。原生测试校验标题、homing/complete/injection、暂停和走航 attempt | 不重做驾驶舱；不把已加载航线当手动采样来源 |
| bridge 事件优先级 | 成立；12 个已发历史阻塞新请求首发，普通 LRU 压力淘汰未发 STOP | `_payload_event_cb/_send_payload_event` 新转换/终态优先历史、STOP 优先；容量压力保护重要未发证据；7 项先红后绿 | 32 请求/30 秒不变，一周期一条完整事件；全 STOP 超载仍有限，客户端 fail closed；回执丢失不等于物理 STOP 未执行 |
| 飞控链路过滤 | 成立；宿主编译执行原生产函数，两种宏下均误发 private 链路 | `Rover/sensors.cpp` 恢复 null/private/inactive/high-latency 过滤，独立游标不变；双宏原函数回归通过 | 特殊链路策略缺陷，不是普通 TELEM2 离线根因证据 |
| 候选 untracked 身份 | 成立；真实 Git 临时仓库中两次 dirty=true，未跟踪内容变化未被比较识别 | schema 3 加规范路径、file/symlink 类型及原始字节摘要；内容/改名/Unicode 空格/ignored/symlink 回归；根 11 项通过 | require-release 拒 dirty 从未绕过；旧 schema 2 须重新取证，不包含 ignored 缓存/产物 |
| Windows STOP 回复范围 | 成立；旧 START/配置 ADS_ERR 清 STOP pending，随后真实 STOP OK 无效 | `_spectro_handle_ads_reply` 仅消费 STOP 的三种固件专属回复；真实 Qt/生产混合解析器定向回归 | 假串口，不声称 Windows 现场复现或物理停止已验收 |
| Windows 旧 reader queued 回调 | 条件风险成立；真实 Qt 事件循环、生产 SerialReader 排队六类回调，实际 close/open 后旧回调进入新会话 | `serial_mixin.py` 所有交付入口捕获不可变 reader 身份并核验当前对象；关闭/重连定向 7 项从 5 失败变全通过，连续 5 轮通过 | 证实可达软件缺口，不把人为旧 ACK 当作现场日志；无需改固件 |

### 已证伪或不重复修改

| 旧结论 | 当前源码/行为证据 | 处理 |
|---|---|---|
| “无 GPS 时禁止手动点采样” | 当前策略允许真实设备手动采样，记录空坐标且结束不回填；`test_manual_sampling_gps_policy.py`、`test_sampling_without_gps.py` 通过；文档 `80_sample_gps_binding.md` 已按源码修正 | 不重新加 GPS 门槛 |
| “所有自定义命令只发一次” | QGC 启动/校准等非停止命令为单次；停止类保留有界重试与总期限，`_payloadRetryPolicy`/`_payloadStopRetirementAndTotalDeadline` 原生测试通过 | 不把停止重试误删 |
| “发送计数增长或飞控姿态在线即可证明载荷在线” | 字段独立 freshness、来源/会话与关联终态已分开；计数/姿态不能替代端到端证据 | 不作为离线事件已解决的证据 |

### 仍受阻/未闭环

- QGC 新 CI 构建仍在运行；pre-commit 仍为既有基线失败（本轮文件已单独通过格式/lint 核验），需独立修复基线后才能全绿。
- 原始“待机后整组载荷离线”缺少匹配部署版本与同一运行窗口的 ROS→飞控→QGC 证据，保持未关闭。
- 未执行 Jetson 实进程、ESP32/飞控刷写、台架或实船验收；本轮只提交/推送开放 PR。

## 已执行验证

所有新增确认项先在未修复生产路径看到契约正确的失败，随后修改源码；未用只查源码字符串代替行为回归。

| 端 | 本轮执行结果 | 入口及边界 |
|---|---|---|
| ROS | 测量路径最终 14 项通过；事件优先级 7 项通过；非地图全量 669 项、0 失败、13 环境跳过、排除 130 地图项；Python 3.8 顶层 scripts/lib 25 文件语法通过 | `tests/run_non_map_tests.py`、`test_remaining_measurement_paths.py`、`test_event_delivery_priority.py`；无 GPS 真帧/基线/会话、STOP/owner/迟到结果、正常 ADS STOP 状态在线均在离线回归中 |
| ROS 真实传输 | WSL 真实 pymavlink bridge/TCP 短写、EAGAIN、丢 accepted 合法 progress fixture 通过；真实 TCP EOF/重连 2 项通过 | `test_bridge_qml_event_chain.py`、`test_mavlink_tcp_real.py` 独立进程；不能把装有 fake pymavlink 的 AST 单测当真实协议测试 |
| Windows | 全仓 103 通过、1 跳过（缺 pyqtgraph）；11 个既有 return-not-none 警告；定向与既有停止/会话共 17 通过；语法/diff 通过 | `test_windows_ads_reply_scope.py`、`test_serial_queued_session.py` 使用真实 Qt/线程/解析器，假串口 |
| QGC | 契约 34 通过；Qt Quick Test 46 通过；原生 `SendMavCommandWithSignallingTest` 10 通过；bridge 生成的 MAVLink2 分片交给原生解析器/QML 的 10 项通过；Debug/Release 全量构建通过 | `custom/tests`、`test/Vehicle/SendMavCommandWithSignallingTest.cc`、`USVPayloadLifecycleFixture.qml`；原生测试使用 MockLink/真实 Qt 事件循环，不是 AST 字符串检查 |
| ArduRover | 链路策略 1 项通过；Pixhawk6C `waf rover` 构建完成，APJ `git_identity=8379c475`；SITL 二进制已生成 | 宿主编译执行生产过滤函数；未刷写、未做实船链路测试 |
| DetFirmware | Windows pytest 18 通过、10 平台跳过；WSL native 2 项、ADS I²C interleaving 8 项通过 | 固件未修改，不冒称本轮重新 PIO 构建；WSL 无 pytest，采用现有 unittest 入口完成 native 验证 |
| 根 | 11 项通过、diff 检查通过 | `python -B -m unittest discover -s docs/tools -p 'test_*.py'`，快照行为用真实临时 Git 仓库 |

本地红绿证据保留在 `.worktrees/audit-20261019/`（不提交构建和运行日志）；可发布的可重复回归在各端 PR，原始旧审计目录保持未跟踪。

## 发布与剩余门槛

| 仓库 | 本轮提交 | PR / 状态 |
|---|---|---|
| ROS | `6e94afa34eef6b98e75208ad0518155c8d7a6bab` | [#88](https://github.com/MIGO-OvO/usv_ros/pull/88)，OPEN；远端 SHA 已核对；仓库无检查，不称 CI 通过 |
| QGC | `abe2994b374731495358b8de5dd2fd50a02d4811` | [#17](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/pull/17)，OPEN；远端 SHA 已核对；新 CI 运行见下方归因 |
| ArduRover | `8379c475f9315a3a439c948d4e6cf6de832d305b` | [#11](https://github.com/MIGO-OvO/ardupilot-usv/pull/11)，OPEN；远端 SHA 已核对；无 CI workflows |
| Windows | `5301057a40793d218d852885f586d1cf41e23667` | [#9](https://github.com/MIGO-OvO/MotorControlApp_Pyside6/pull/9)，OPEN；远端 SHA 已核对；无 CI workflows |
| DetFirmware | `186427df75047c0212d74969df2c18a3df01fd40`（未改） | 旧 #3 已合并，无人为制造续修 PR |
| usv_ws | 本轮文档提交见 [#24](https://github.com/MIGO-OvO/usv_ws/pull/24) HEAD | OPEN；不在自身内容中伪造自引用 SHA |

本轮不改变 USVE1 线协议版本、命令号、字段数、watchdog 或板端 PID 限时。ROS 与 QGC 的事件/任务修复应作为匹配组合验收；Windows 关闭旧会话后启动新程序。DetFirmware 复用上述已核验版本，无新增固件补丁，不要求为本轮相同源码重复刷写。清单是源码候选，不是现场部署记录；根仓最终提交以 #24 HEAD 为准，避免在自身内容中伪造自引用 SHA。

### 候选产物摘要（工作树构建）

| 产物 | SHA-256 |
|---|---|
| QGC Debug `build/audit-debug-20261018-v2/Debug/QGroundControl.exe` | `1C7B63C507D4EEF0A91479A9FFD36BB0D018CDEE25ABF965759E817A9360F2E1` |
| QGC Release `build/Desktop_Qt_6_10_1_MSVC2022_64bit-Release/Release/QGroundControl.exe` | `F5CF7D6357429202EE8C9182263DEDBA967BF923E57FD7A783AA960BB640D64A` |
| Pixhawk6C `build/Pixhawk6C/bin/ardurover.apj`（`git_identity=8379c475`） | `1DAC197B852DB92692BB3B2B66657B00C74D02C724EE649017BDF4D920B39749` |
| ESP32 `.pio/build/nodemcu-32s/firmware.bin`（未改） | `DC16A1F5C97895C9EF1C36BE0066CAB3EEA23B964AF0787C8DE4424E0B1A21E5` |

QGC 构建配置生成于 `15e924c5` 时期，exe 内嵌版本字符串可能仍是该基线；摘要只标识本轮工作树产物，不替代重新打包的安装包身份。APJ 摘要包含本轮源码编译结果，但未刷写。

### QGC CI 基线归因

PR #17 起点 `15e924c5...` 的旧 CI 已失败，不是仍在运行：Windows run `39150655161`、Linux `39150655110`、Custom plugin `39150655188` 的代表 job 均在 libevents `receive.h:157/200` 缺 `mavlink_msg_target_field/mavlink_msg_get_target_system`。它们 checkout 的合并测试提交为 `f74baa1b8274de4186145cd17ee2a8556d5b56d3`，不能归因于随后才产生的本轮本地修改。

`src/MAVLink/LibEvents/CMakeLists.txt` 在 master/起点均跟随 `main`；libevents `0ef305faa4cffdb09f01ca862ebfc108b7ff0cd5` 增加新 helper 及双参数回调，而 QGC 仍是旧 MAVLink/单参数回调。已有本地成功缓存实际是 `840a88ea...`，缓存目录 hash 不是依赖版本，不能证明新 main 可构建。本轮最小兼容固定为其 breaking change 前版本 `077677a7d2f48f0af0eb8a4e4a7b6310956728bc`，保留后续 Android 链接与 dangling-pointer 修复，不升级全套 MAVLink。

旧 pre-commit run `39150655160` 是混合基线问题：`package.json`、`APMFlightModesComponent.h`、`tools/analyzers/README.md` 的代表失败与 master 相同；但 PR #17 自己改过的 `custom/res/actions/usv_actions.json` 也失败，不能统称无关历史。其他平台/其他 hook 未逐项归因，不宣称全部是环境问题；只修本轮/本 PR 已确认问题，不全仓格式化或降低门禁。

新提交 `abe2994b3` 的 pre-commit run `39193987095` 仍为 11 通过/48 失败，与旧基线同量级；hooks 自动修改的 7 个文件均不是本轮文件。本轮变更单独核验：C++ 测试用 CI 同版本 clang-format `21.1.7` 通过；两个 QML 文件 `qmllint` 无输出；Python 契约文件的 ruff 8 项错误与 HEAD 完全相同；`src/MAVLink/LibEvents/CMakeLists.txt` 的 cmake-format 在 HEAD 基线同样失败。因此不把全仓 48 项失败写成本轮通过，也不通过跳过检查或全仓格式化制造全绿。

### 最小台架验收（由操作者执行）

1. 记录实际运行五端提交、应用/固件产物 SHA-256、配置与身份文件；先确认独立断电和停止入口。不要将本地源码或当前云端 HEAD 当成已部署版本。
2. 无 GPS，以当前会话真实有效分光帧、合法配置与基线执行完整手动点采样；检查空坐标记录且结束不回填。
3. 分光未启动及正常 STOP 后长期观察其他载荷字段独立更新、来源/会话与年龄；保留同一窗口 ROS→飞控→QGC 日志。姿态在线或发送计数增长不足以验收。
4. 分别在 preflight 等 ADS、油相结束、进样 lead、正式 PID、定时等待、暂停、校准时 STOP；分别记录关联回执、软件清理和实物停止时间。旧 owner 清理不得停止新任务。
5. 短静默应等待有效帧再允许新动作；明确饱和/I²C 错误及时终止且首因保留。恢复通信/收到好帧不自动清故障或恢复泵动作。
6. 断线/重连/切船、旧 ON/STOP、过期请求、取消后迟到终态不得重放或影响新任务；暂停/恢复后原任务失败仍可见，未完成校准断线须锁定，STOP 始终可用。

未取得匹配部署版本和同一运行窗口的端到端证据前，不宣布原始“待机后载荷离线”已彻底解决。所有 PR 保持未合并；不在此任务中部署、刷写或启动硬件。
