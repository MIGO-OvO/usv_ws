# 验证矩阵

Updated: 2026-10-20

## 停止恢复闭环验证边界（2026-10-20）

本轮（命令受理去持久化门槛 + 阶段化测量门禁 + 停止范围 + QGC 等待与恢复 + 旧任务收敛与测量证据绑定）的自动化验证入口（离线、使用生产函数与受控时钟）：

| 范围 | 入口 | 覆盖 |
|---|---|---|
| ROS 就绪快照与准备门禁 | `tests/test_stop_recovery_contract.py` | 并发帧不被误判、真 stale 仍拒绝、旧会话帧不能支撑新 START、机械准备不等待测量、交接仍拒绝、后台 freshness 不取消慢准备 |
| ROS 陈旧测量证据绑定 | 同上 `PreflightStaleMeasurementTests` | 观察后收到有效新帧不再被判 stale、旧任务停止且新 attempt 启动后旧检查不停止/不失效新任务、归属重验与停止认领在同一临界区 |
| ROS 停止结果与锁存 | 同上 `ConfirmedStopTests` | 旧 `cleanup_failed`/分光故障不否决本次成功 STOP、未确认仍失败、只写失败不算停止、不可恢复故障保留、ADS/全输出范围分开、手动进样仍运行时只停分光不虚报全停 |
| ROS 请求受理与回执 | `tests/test_payload_disk_stop.py` | 日志目录不可写/写入阻塞时普通命令与 STOP 仍有正确 ACK 且不触发维护锁；busy 拒绝立即产生关联 rejected + ACK；同身份重放原结果不重复执行；已拒绝身份在通道空闲后仍重放拒绝；31016 紧接 31019 两个 STOP 串行完成且各自结果保留 |
| ROS 请求关联结构 | `tests/test_payload_protocol.py` | 内存去重、处理中返回、参数冲突拒绝、新任务不被淘汰、旧身份退休、终态保留、走航多 attempt 继续、日志故障不影响受理、重启不承诺精确一次 |
| ROS 接收分帧 | `tests/test_mavlink_framing_contract.py` | 半帧/粘包、坏 CRC、未知消息 ID、合法外层帧 payload 内嵌命令不执行、BAD_DATA 不重连 |
| QGC 任务收敛依据 | `custom/tests/tst_USVPayloadCommandController.qml` | 同值周期性 Idle 不提前退休新 START（正常失败与 `cleanup_failed` 两种后续结果都保留）、走航 accepted 后同值 Idle 不放行新物理任务、真实终态/STOP accepted 后的新 Idle 正常收敛、accepted 立即结束接单等待 |
| QGC 控制器（其余） | 同上 | accepted 结束接单等待、4.9s accepted/5.4s 状态不锁船、回执超时只结束等待且不伪造空闲、普通失败不锁船、31016→31019 两个命令各自结束、无身份兼容 STOP 用标准 ACK 结束等待、退休请求迟到终态只进历史、Fault/Aborted 仍可恢复 |
| QGC 契约 | `custom/tests/test_usv_qgc_contract.py` | 期限常量、`allowed` 门禁、`expire` 的已接受/未收到回执分支（不再整船锁） |

未执行：QGC 完整 C++ 构建、Qt on-device 运行、Jetson ROS 运行、ESP32/飞控刷写、实船/台架、抓包重放。本轮未修改 `Vehicle.cc`/`Vehicle.h` 与固件，`Vehicle` 的 ACK/期限行为按源码核对与既有契约测试确认。

### 台架最小清单

| 端 | 必须核验的现象 |
|---|---|
| QGC | 连续“准备→采样→停止→再次采样”无需重启进程；点采样刚发出时收到周期性 Idle 不会让界面提前“空闲”，随后 accepted、运行状态与失败结果都归到本次请求；普通失败后停止确认即恢复准备，无需先急停或勾选现场核验；回执超时显示“未收到回执”但停止按钮仍可用；31016 后紧接 31019 两次都出现各自结果；真急停仍要求核验后才解除锁定 |
| Jetson/ROS | 停止后 `USV_STAT` 回到 0 且 `terminal_reason` 仍可查；`~/.ros/usv_payload_requests.jsonl` 删除或不可写后命令照常执行；准备阶段无测量也能完成归零/360°/油相分割，交接前仍拒绝无有效测量；交接瞬间恢复的分光帧不会被后台检查改写为 stale |
| 检测板 | `ADS_OK:START` 后先出现 `starting`（`USV_VLD=0`），首帧到达才 `acquiring`；只按“停止信号”时泵仍在转是预期，`outputs_stop` 不得显示为真 |
| 飞控 | 采样失败后 `USV_STAT` 不长期停留 3；`USV_SMPL/USV_DONE` 配对不因本次修复改变 |

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
| QGC 冷启动 | ROS 启动后立即点击启动信号 | bridge 不等待飞控心跳才开始接收；采样 owner 在 MAVROS 初始化等待期间仍每秒续约；配置回显和有效首帧后才成功 |
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
