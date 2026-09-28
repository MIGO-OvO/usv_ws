# 采样记录与开始位置绑定

Updated: 2026-09-28

## 范围与调用链

现场入口：QGC 手动 31010、FCU `USV_SMPL`、可选 waypoint 自动触发、走航调度、lab_real、Web `/api/mission/start`。
trigger 的现场入口在首次进样/自动化调用前验证 GPS 并建立 acquisition context；Web 直接启动使用同一个共享校验器。
一轮自动化事务（包含其配置的步骤/loop）为一次采样；原始分光帧和模拟液滴是该记录的子数据，不分别创建 SampleRecord。

现有闭环保持：QGC → 飞控命令/mission script → bridge → trigger → pump；
trigger 的 `sampling_context` → `sampling_started` 在同一状态发布流上传给 Web；
Web 建立 `sample_windows[]`，原始帧仍写 `raw/<mission_id>/<sample_id>.jsonl`。
`sample_windows[]` 是兼容旧 API 的持久化 SampleRecord 容器，不额外维护一份独立的记录表。

trigger 终态新增 `/usv/sample_record` (`String(JSON)`)；FCU `/usv/sampling_result` 增加嵌套 `sample_record`，顶层旧整数 `sample_id` 不变。
模拟事件与聚合电压也携带同一 `sample_record`；模拟测量通过同一状态流的 `sampling_measurement:<JSON>` 写入窗口，避免依赖跨话题先后顺序。
Web 直接启动的记录通过现有 samples API 读取；它不经过 trigger 的终态话题。

## 数据约定

| 字段 | 约定 |
|---|---|
| `record_schema_version` | 1；旧窗口 `schema_version`/`sample_windows_schema_version` 保持 1 |
| `sample_id` | UUID4 hex，全局唯一；context 中称 `record_id`，不覆盖旧 FCU ID |
| `timestamp_start` / `timestamp_end` | Unix 秒；开始为主机提交采样的时刻，结束前为 null |
| `latitude` / `longitude` | 开始位置，WGS84 度；绝不从结束位置补写 |
| `altitude` | NavSatFix 高度（米，通常 WGS84 椭球高）；缺失为 null，不假称海拔 |
| `gps_timestamp` | NavSatFix `header.stamp` 的 ROS 秒值，不假称原始 GNSS UTC；仿真无实测 GPS 时间时为 null |
| `position_age_s` | 开始时 GPS 源时间年龄，冻结后不继续增长 |
| `position_source` / `simulated` | `gps`/false 或 `lab_sim`/true；历史无上下文数据标 `legacy_unknown` |
| `waypoint_id` | 已知关联航点；未知为 null。旧 `waypoint_seq` 的兼容语义保留 |
| `mission_id` | Web 持久化时绑定归档任务 ID；trigger 没有获知任务 ID 时为 null，不用 FCU script ID 冒充 |
| `mavlink_sample_id` | 可选的 1..65535 FCU 握手编号，不具有跨任务唯一性 |
| `spectrometer` | trigger：本次窗口内最新测量；归档：原有 raw_file/计数/统计 + 可选 measurement，不删除旧统计字段 |
| `water_quality` | concentration/unit；有标定时 Web 使用现有工作曲线并保存标定信息，无测量/无标定不伪造浓度 |

保留 `start_time/end_time` ISO 字符串、`gps_start/gps_end/gps_latest`、manual_result、processing、raw 文件与旧 samples API。
`gps_end` 仍可用于诊断漂移，但不作为采样点位置；地图摘要点通过冻结 GPS 重建 WGS84/GCJ02 对，轨迹本身仍实时更新。
历史记录不迁移、不臆测开始 GPS；新旧数据可以并存。

## GPS 准入与边界

- `survey_require_gps` 默认 true；`survey_max_position_age_s` 默认 2；新增 `sampling_max_position_age_s` 默认 2（所有现场入口硬门槛）。
- `survey_require_gps=false` 仅保留旧配置兼容性，不能绕过现场采样硬门槛；采样年龄设 0、负数、NaN 时回退 2 秒，不代表无限期有效。
- 纬经度必须有限且在合法范围，NavSatFix status >= 0，源 stamp > 0。
- 接收时用 ROS 时钟计算源年龄，之后用 monotonic 计算缓存驻留时间，两者之和 <= 门槛；旧源数据即便刚收到也拒绝。缺时间戳、未来时间戳、无 fix、非法坐标均拒绝。
- 无效定位消息替换旧缓存，防止失锁后沿用旧有效点。GPS 正好 2 秒有效，超过 2 秒拒绝。
- waypoint 在 HOLD/稳定等待之后冻结；manual/FCU 在进样前冻结；每轮 survey 单独冻结/生成 UUID；lab_real 永远使用硬件 GPS，不使用虚拟航点位置。
- lab_sim 使用显式模拟坐标，不要求硬件 GPS；模拟走航优先使用 lab status 船位，兼容原有可用位置输入。仿真记录明确标 simulated，不能冒充现场点。
- 采样期间船位移动或 GPS 失锁，不改已冻结的位置；下一次采样重新检验。无 GPS 的 FCU 启动直接失败/HOLD，即使 on_fail=SKIP 也不发成功放行。
- bench 调试的低层电机、进样、分光连续流及直接 ROS pump 控制服务不是地理采样 API，本次不禁止这些调试接口；正式现场采样须走上述入口。ROS 控制网仍需访问隔离。

## MAVLink / QGC 审查与最小扩展方案（未启用）

源码依据：

- `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp` 的 NAMED_VALUE_FLOAT 分支只缓存既有载荷字段，并处理 `USV_DONE/USV_FAIL`。
- `ardupilot-usv/Rover/sensors.cpp::usv_telemetry_send` 按 2 Hz 重发缓存，不携带某个采样点的原子 ID/坐标。
- `ardupilot-usv/libraries/GCS_MAVLink/MAVLink_routing.cpp::check_and_forward` 阻止 NAMED_VALUE_FLOAT 直接转发；未知消息的 CRC/路由也不能视为天然可透传。
- `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc::handleMessage` 处理旧遥测，无 WQ_SAMPLE_POINT 解码。
- `src/usv_ros/scripts/usv_mavlink_router_bridge.py::_sampling_result_cb` 按顶层整数 ID/终态完成握手；新增嵌套记录不改变判定。

不能把 UUID 或高精度经纬度拆成几个 NAMED_VALUE_FLOAT：会丢精度、丢原子性，且飞控不会自动缓存新字段。
最小提案：MAVLink 2 `WQ_SAMPLE_POINT`，候选 message ID 42010（仅草案；三端 dialect 合并前核查所有实际依赖并登记 ID/CRC，不直接投产）。

| MAVLink 字段 | 类型 / 单位 |
|---|---|
| time_start_usec, time_end_usec, gps_time_usec | 各 uint64_t；Unix/源时钟微秒；未知 GPS 时间为 0，GPS 时间语义随 flags 明确 |
| latitude, longitude | 各 int32_t，度 × 1e7 |
| altitude_mm | int32_t，毫米；未知 INT32_MAX |
| position_age_ms | uint32_t，毫秒 |
| waypoint_id, fcu_sample_id | 各 uint16_t；未知航点 UINT16_MAX，无 FCU 关联为 0 |
| sample_uuid | uint8_t[16]，UUID 原始 16 字节，不用浮点表示 |
| voltage, absorbance | 各 float；无有效数据用 NaN |
| flags | uint8_t：bit0 GPS有效，bit1 分光有效，bit2 simulated，bit3 采样成功，bit4 GPS时间为ROS源时间（不保证UTC）；其余保留 |

固定 payload 69 字节。最小消息只传点、关联 ID、质量位和基础测量；完整 mission_id、污染物种类/单位、浓度/原始数据继续由 ROS API 按 UUID 查询，避免飞控承载业务数据库。

后续投产要求：同一 XML 生成 pymavlink、ArduPilot、QGC 三份定义；bridge 单 socket writer 发送，飞控显式白名单转发；QGC 以 sysid+UUID 去重并关联点位。端到端 CRC、MAVLink2 链路、低带宽、丢包/乱序/重启必须联调。
本次不修改既有 22 个遥测字段，不启用此消息，不声称 QGC 已能展示样本点；USV_DONE/USV_FAIL 不依赖扩展消息的送达。后续要可靠交付需另设计 ACK/补传，不能用固定重发次数假称 exactly-once。

## 涉及文件与原因

- `src/usv_ros/scripts/lib/sample_recording/record.py`：共享 GPS 准入、不可回填快照和 SampleRecord 构造。
- `scripts/mavlink_trigger_node.py`：所有现场/实验入口绑定、模拟船位订阅、每轮 survey 唯一记录、关联结果发布。
- `scripts/lib/sample_recording/models.py`、`storage.py`：窗口复用标准字段、UUID、防重复建档、原始统计与测量保留。
- `scripts/web_config_server.py`：直接启动 GPS 门槛、窗口/地图冻结位置、模拟事件记录、真实工作曲线结果。
- `launch/usv_bringup.launch`：安全默认值与可配置现场 freshness。
- `tests/test_sample_gps_binding.py`、`gps_fixtures.py`：GPS/时间/移动/一致性/去重验证。
- `tests/test_sampling_context_contract.py`：Web 准入、真实归档和同流模拟测量落盘验证。
- `tests/test_mavlink_command_compat.py`、`test_fcu_sampling_result.py`、`test_sampling_cleanup_ownership.py`、`test_hardware_runtime_sync.py`：旧安全/兼容测试补入有效 GPS 与 ROS 时钟夹具，不移除原有断言。
- 根 `docs/current/00_index.md`、`40_interfaces.md` 与本文：接口约定和验证步骤。

未修改用户已有的 pump_control_node.py / test_system_safety_contract.py 改动；未修改 ArduPilot、QGC、DetFirmware、Windows 上位机的业务代码或串口协议。

## 现场验收（先系泊/断开推进输出，再低速受控水域）

1. 成套停止旧 ROS 进程，备份现场配置/数据，同步 usv_ros；Jetson 执行 `python3 -m unittest discover -s tests -p 'test_sample_gps_binding.py'` 和相关采样回归。检查配置/launch 的两个年龄门槛均为 2 秒，真实模式关闭模拟数据源。
2. 检查 `/mavros/global_position/global`：status >= 0，header.stamp 正常，定位持续更新。确认 ROS/MAVROS 时间同步；不要用反复发布旧 stamp 的定位充当新数据。
3. 分别用 QGC 手动、NAV_SCRIPT_TIME、Web start、survey 发起采样。对照 `/usv/trigger_status` 中 sampling_context、`/usv/sample_record`（trigger 来源）和 `GET /api/data/mission/<id>/samples`：每轮一个 UUID，起止时间、坐标、age、关联航点、光谱/水质字段齐全，raw 文件可读取。
4. 在系泊台架停发 GPS 超过 2 秒后重试。确认不启动采样自动化；FCU 返回失败且保持 HOLD、不收到 USV_DONE。恢复 GPS 后可再次启动。另测试 status=-1、旧源 stamp、NaN 和未来 stamp；不要在真实航行中注入假定位。
5. 在 A 点启动一次采样，采样过程中缓慢移动到 B 点；记录 latitude/longitude 与 gps_start 必须为 A，gps_end/实时轨迹允许为 B。下一轮 UUID 不同且绑定新的开始位置。
6. survey 连续执行至少 3 轮，核对 3 个不同 UUID/原始文件，停止/取消后无额外记录或下一轮启动。GPS 丢失期间不允许开启新轮次。
7. lab_sim 离线运行，与现场 samples API 比较字段集合；检查 simulated=true、position_source=lab_sim、无假 GPS 时间。lab_real 无硬件 GPS 必须拒绝，有硬件 GPS 时不能绑定虚拟船位。
8. 测试重复 started/终态、失败、停止、进程重启及网络短断；不能由重复终态放行新 FCU 任务。重启未完成记录按现有 interrupted 语义处理，不伪造成功或结束坐标。
9. QGC 确认旧电压/吸光度/状态等 22 字段和命令照常工作。样本点尚经 ROS/API 查看，不以 QGC 未实现的扩展消息作为验收项。

## 已知边界

本地验证：Windows/Python 3.14 分文件扫描 473 个用例，471 通过，2 个既有地图断言失败（后端 Google provider 与测试高德预期不一致；原生缩放 22 与 smoke 的 18 预期不一致，已核对 HEAD）。新增 14 个 GPS 专项测试及 3 个 Web 绑定场景通过；相关采样/握手/清理回归通过。两个 Bash/WSL 脚本测试文件未完成验证，首个调用超时后已停止测试子进程。Python 语法、launch XML、本次改动范围的 diff whitespace 检查通过。没有执行 Qt/飞控/ESP32 编译或真实无人船测试。

- Python 离线测试不能替代 ROS 多进程、硬件动作、GNSS 精度、Qt 和飞控编译/无线链路验收。
- 本次沿用 Web 持久化架构：现场必须运行 Web 记录服务；`/usv/sample_record` 是非 latched ROS 事件，无独立持久化重放队列。Web 掉线/进程崩溃仍可能漏档；UUID 去重不等于跨进程崩溃 exactly-once。
- 冻结的是主机下发采样开始前的最新有效位置，不是检测装置硬件曝光/取水的 PPS 触发时刻；需要亚秒硬件同步时须另行设计时间同步和取水延迟标定。
- 水质无配置标定或没有有效数据时保留 null；不从上一次采样拷贝浓度。
