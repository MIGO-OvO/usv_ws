# 采样记录与开始位置绑定

Updated: 2026-10-13

## 范围与调用链

现场入口：QGC 手动 31010、FCU `USV_SMPL`、可选 waypoint 自动触发、走航调度、lab_real、Web `/api/mission/start`。
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
| `latitude` / `longitude` | 可选开始位置，WGS84 度；无有效定位为 null，绝不从结束位置补写 |
| `altitude` | NavSatFix 高度（米，通常 WGS84 椭球高）；缺失为 null，不假称海拔 |
| `gps_timestamp` | NavSatFix `header.stamp` 的 ROS 秒值，不假称原始 GNSS UTC；仿真无实测 GPS 时间时为 null |
| `position_age_s` | 开始时 GPS 本地接收年龄，冻结后不继续增长 |
| `position_source` / `simulated` | `gps`/false、`<source>_no_gps`/false 或 `lab_sim`/true；历史无上下文数据标 `legacy_unknown` |
| `waypoint_id` | 已知关联航点；未知为 null。旧 `waypoint_seq` 的兼容语义保留 |
| `mission_id` | Web 持久化时绑定归档任务 ID；trigger 没有获知任务 ID 时为 null，不用 FCU script ID 冒充 |
| `mavlink_sample_id` | 可选的 1..65535 FCU 握手编号，不具有跨任务唯一性 |
| `spectrometer` | trigger：本次窗口内最新测量；归档：原有 raw_file/计数/统计 + 可选 measurement，不删除旧统计字段 |
| `water_quality` | concentration/unit；有标定时 Web 使用现有工作曲线并保存标定信息，无测量/无标定不伪造浓度 |

保留 `start_time/end_time` ISO 字符串、`gps_start/gps_end/gps_latest`、manual_result、processing、raw 文件与旧 samples API。
`gps_end` 仍可用于诊断漂移，但不作为采样点位置；地图摘要点通过冻结 GPS 重建 WGS84/GCJ02 对，轨迹本身仍实时更新。
历史记录不迁移、不臆测开始 GPS；新旧数据可以并存。

## 可选 GPS 位置与边界

所有真实采样入口在首次进样/自动化调用前建立 acquisition context，GPS 仅作为可选位置元数据，缺失、失锁或过期均不阻止启动。旧配置 `automation_policy.require_gps`、`survey_require_gps`、实验 `allow_no_gps` 和 Web 请求 `require_gps` 均被忽略；对应界面开关已移除。launch 保留默认 false 的 `survey_require_gps` 参数兼容旧启动命令，但不再传给节点。

有效硬件定位仍优先冻结；其他情况记录空坐标，`position_source=<source>_no_gps`（例如 `web_no_gps`、`manual_no_gps`、`fcu_no_gps`），均为 `simulated=false`。不绑定模拟船位、不事后回填采样起点、不作为地图定位点。`GET /api/gps` 继续提供硬件定位有效性、原因、WGS84 经纬度、海拔和数据年龄，用于诊断。

- `sampling_max_position_age_s` 默认 2，决定开始位置是否可记入元数据；`survey_max_position_age_s` 默认 2，进一步约束距离计算可用的位置年龄。这些参数不限制采样启动。采样年龄设 0、负数、NaN 时回退 2 秒，过期定位记为空坐标。
- 记录有效坐标时要求经纬度有限且在合法范围、NavSatFix status >= 0、本地 monotonic 接收时间存在且不在未来、接收年龄未过期；无效时采样继续。FCU/MAVROS header.stamp 保留作诊断，不因墙钟偏差丢弃本地刚收到的有效定位。
- 无效定位消息替换旧缓存，防止失锁后沿用旧有效点。默认正好 2 秒可记为有效位置，超过 2 秒记为空坐标。
- waypoint 在 HOLD/稳定等待之后绑定位置；manual/FCU 在进样前绑定；每轮 survey 单独生成 UUID；lab_real 只使用可选硬件 GPS，不使用虚拟航点位置。
- 走航无可用定位时按时间间隔采样，并清除旧距离锚点；有有效定位时执行最小距离筛选。速度、分光有效性、泵预检、故障、owner 和停止确认条件继续执行。
- lab_sim 使用显式模拟坐标，不要求硬件 GPS；模拟走航优先使用 lab status 船位。生成模拟液滴需要有效模拟坐标，仿真记录标记 simulated，不能冒充现场点。
- 采样期间船位移动或 GPS 失锁，不改已冻结的位置；无坐标记录即使随后恢复 GPS 也不回填起点。无 GPS 的 FCU 采样按真实执行结果回报，同 ID 正常完成后才发 USV_DONE。
- 飞控导航自身的定位条件独立于载荷采样；本次移除的是 ROS/Web 载荷采样的 GPS 条件。

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

- `src/usv_ros/scripts/lib/sample_recording/record.py`：共享可选位置绑定、不可回填快照和 SampleRecord 构造。
- `scripts/mavlink_trigger_node.py`：所有现场/实验入口绑定、模拟船位订阅、每轮 survey 唯一记录、关联结果发布。
- `scripts/lib/sample_recording/models.py`、`storage.py`：窗口复用标准字段、UUID、防重复建档、原始统计与测量保留。
- `scripts/web_config_server.py`：无定位直接启动、弃用 GPS 策略字段兼容、窗口/地图冻结位置、模拟事件记录、真实工作曲线结果。
- `launch/usv_bringup.launch`：旧启动参数兼容与位置元数据的年龄参数。
- `tests/test_sample_gps_binding.py`、`gps_fixtures.py`：GPS/时间/移动/一致性/去重验证。
- `tests/test_sampling_without_gps.py`：各真实入口无定位/失锁/过期启动、旧配置不生效、FCU 同 ID 成功完成与走航距离回退验证。
- `tests/test_manual_sampling_gps_policy.py`：旧 GPS 策略不限制 QGC 手动采样，空坐标归档和接受/失败/忙碌 ACK 验证。
- `tests/test_sampling_context_contract.py`：Web 无定位启动、真实归档和同流模拟测量落盘验证。
- `tests/test_mavlink_command_compat.py`、`test_fcu_sampling_result.py`、`test_sampling_cleanup_ownership.py`、`test_hardware_runtime_sync.py`：旧安全/兼容测试补入有效 GPS 与 ROS 时钟夹具，不移除原有断言。
- 根 `docs/current/00_index.md`、`40_interfaces.md` 与本文：接口约定和验证步骤。

`pump_control_node.py` 仅移除无作用的实验 GPS 选项；泵安全逻辑保持既有行为。ArduPilot、QGC、DetFirmware、Windows 上位机的业务代码与串口协议不涉及本次修改。

## 现场验收（先系泊/断开推进输出，再低速受控水域）

1. 成套停止旧 ROS 进程，备份现场配置/数据，同步 usv_ros（含 `static/dist`）；Jetson 执行 `python3 -B -m unittest discover -s tests -p 'test_sampling_without_gps.py'` 和相关采样回归。成套重启 pump、trigger、bridge、Web，真实模式关闭模拟数据源。
2. 检查 `/mavros/global_position/global` 和 `/api/gps`：有效且持续更新时可记录位置；无 fix 时仍应能启动载荷采样。定位诊断不能误报为采样启动失败。
3. 分别用 QGC 手动、NAV_SCRIPT_TIME、Web start、survey 发起采样。对照 `/usv/trigger_status` 中 sampling_context、`/usv/sample_record`（trigger 来源）和 `GET /api/data/mission/<id>/samples`：每轮一个 UUID，起止时间、坐标、age、关联航点、光谱/水质字段齐全，raw 文件可读取。
4. 在系泊台架停发 GPS 超过 2 秒，或输入 status=-1、NaN、缺失/未来的本地接收时间。各真实采样入口在硬件预检通过后仍应启动，记录空坐标且 `position_source=<source>_no_gps`。恢复 GPS 后已有记录的起点仍为空。旧配置即使保留 `require_gps=true` 或 `survey_require_gps=true` 也不恢复限制；QGC 手动启动回执为 `[31010,0,...]`。FCU 同 ID 采样正常完成后才返回 USV_DONE，失败/取消仍不放行。旧或未来 header.stamp 只作诊断。
5. 在 A 点启动一次采样，采样过程中缓慢移动到 B 点；记录 latitude/longitude 与 gps_start 必须为 A，gps_end/实时轨迹允许为 B。下一轮 UUID 不同且绑定新的开始位置。
6. survey 在无 GPS 时连续执行至少 3 轮，核对不同 UUID/原始文件和时间间隔，停止/取消后无额外记录或下一轮启动。恢复定位后检查有效坐标下的最小距离筛选。
7. lab_sim 离线运行，与现场 samples API 比较字段集合；检查 simulated=true、position_source=lab_sim、无假 GPS 时间。lab_real 无硬件 GPS 时正常启动并记录空坐标，有硬件 GPS 时绑定真实位置，不能绑定虚拟船位。
8. 测试重复 started/终态、失败、停止、进程重启及网络短断；不能由重复终态放行新 FCU 任务。重启未完成记录按现有 interrupted 语义处理，不伪造成功或结束坐标。
9. QGC 确认旧电压/吸光度/状态等 22 字段和命令照常工作。样本点尚经 ROS/API 查看，不以 QGC 未实现的扩展消息作为验收项。

## 已知边界

本地验证：Windows/Python 3.14 下，256 个相关 GPS、采样、握手、清理、预检与归档用例全部通过；9 个前端控制/GPS 位置用例通过，`npm run build` 成功并更新 `static/dist`。扩展检查仍有一个既有地图服务商断言失败（实际 Google provider、测试预期高德），已用修改前 HEAD 的服务端源码复现；它不属于 GPS 启动限制。修改脚本的 Python 3.8 语法兼容、launch XML、源码与文档空白检查通过。本次未跑全量 Bash/WSL 测试，未执行 Qt/飞控/ESP32 编译或 Jetson/真实硬件测试。

- Python 离线测试不能替代 ROS 多进程、硬件动作、GNSS 精度、Qt 和飞控编译/无线链路验收。
- 本次沿用 Web 持久化架构：现场必须运行 Web 记录服务；`/usv/sample_record` 是非 latched ROS 事件，无独立持久化重放队列。Web 掉线/进程崩溃仍可能漏档；UUID 去重不等于跨进程崩溃 exactly-once。
- 冻结的是主机下发采样开始前的最新有效位置，不是检测装置硬件曝光/取水的 PPS 触发时刻；需要亚秒硬件同步时须另行设计时间同步和取水延迟标定。
- 水质无配置标定或没有有效数据时保留 null；不从上一次采样拷贝浓度。
