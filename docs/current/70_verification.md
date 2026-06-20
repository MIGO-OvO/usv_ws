# 验证矩阵

Updated: 2026-06-19

## 静态验证

| 项 | 命令/方法 | 通过标准 |
|---|---|---|
| current 文件集 | `Get-ChildItem docs/current` | 仅编号当前文档 |
| 归档存在 | `Test-Path docs/archive/2026-05-20-current-pre-restructure` | 返回 true |
| 本地路径引用 | 手动/脚本检查反引号路径 | 根仓库内路径存在；外部子仓库路径明确 |
| 旧入口污染 | 搜索旧入口名、旧字段数、旧频率说法 | current 不出现过时说法 |
| MAVLink 字段 | 对照 `GCS_MAVLink_Rover.cpp`、`sensors.cpp`、`Rover.h`、QGC FactGroup | 22 字段名称一致 |
| Mission 采样指令 | 对照 `mode_auto.cpp`、QGC `MavCmdInfoRover.json` | 航线定点采样为 `MAV_CMD_NAV_SCRIPT_TIME`，不使用 mission `31010` |
| COMMAND_LONG | 对照 `mavlink_trigger_node.py`、`usv_mavlink_router_bridge.py` | 手动 `31010..31019` 一致 |
| 串口握手 | 对照 `pump_control_node.py`、`DetFirmware/src/main.cpp` | `HELLO?` / `DET_ID` 一致 |

## ROS 离线验证

| 项 | 命令 | 通过标准 |
|---|---|---|
| Python 语法 | `python3 -m py_compile src/usv_ros/scripts/*.py` | 无语法错误 |
| Launch 参数 | `roslaunch usv_ros usv_bringup.launch --dump-params` | 参数可展开 |
| 单元测试 | `python3 -m unittest discover -s src/usv_ros/tests -p 'test_*.py'` | 全部通过 |
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
| 校准命令 | QGC 发送 `31014` | `/usv/pump_command` 出现 `CALXYZA` |
| 遥测字段 | 运行 bridge | QGC 显示 22 字段；固件 2 Hz 转发 |
| 健康遥测 | 运行 system health + bridge | QGC 显示 `USV_JTMP/ETMP/JCPU/JMEM/EHEAP` 对应 Fact |
| 电台链路 | RADIO_STATUS 输入 | `/usv/radio_status` 有 rssi/remrssi/noise 等字段 |

## 采样闭环验证

| 步骤 | 观测点 | 通过标准 |
|---|---|---|
| 固件触发 | `NAV_SCRIPT_TIME(param1=1)` | ROS bridge 收到 `USV_SMPL` |
| ROS 采样 | `/usv/trigger_status`、`/usv/pump_status` | 出现 `sampling_started`，状态进入采样并执行序列 |
| QGC/Web 记录 | QGC 采样数据页、Web 数据中心 | `USV_SCNT` 递增，Web 新任务记录数据点增长 |
| 完成通知 | bridge 日志、固件行为 | ROS 发 `USV_DONE`，固件继续 mission script |
| 失败策略 | 配置 `HOLD/SKIP/ABORT` | 行为与配置一致 |

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
