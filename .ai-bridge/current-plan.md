# 航点/GPS 分光切片与人工浓度记录开发方案

Updated: 2026-06-29T09:17:25.001Z
Workspace: D:\usv_ws
Target agent: Codex (codex)

## Plan

# 航点/GPS 分光切片与人工浓度记录开发方案

## 0. 任务背景

用户目标：在完成一轮航点采样后，Web 页面可以便捷查看“按航点划分的、不同航点的采样信号”。由于液滴微流控的污染物浓度计算算法尚未接入整套系统，本阶段先实现：

1. 按采样生命周期切分真实分光原始信号。
2. 将切片关联到 mission、航点序号、GPS、采样来源。
3. 在 Web 数据中心按航点/采样窗口查看信号。
4. 支持人工录入某航点污染物浓度、单位、备注。
5. 为后续自动液滴处理算法预留处理结果字段。

本计划只做 ROS/Web 端开发。不要修改 `ardupilot-usv/`、`DetFirmware/`、`WQ-USV-QGroundControl/` 的协议或命令号，除非实施中发现必须同步文档说明。

## 0.1 2026-06-30 复核修订

本计划原本把 P0 实现路线描述为“待实现”。当前工作区已经出现了一部分实现文件，但复核后应按以下状态继续：

- `scripts/lib/sample_recording/` 已存在，可作为 SampleWindow 模型、summary、raw JSONL 存储和人工结果记录的基础库。
- `frontend/src/pages/Data.tsx` 已改为 mission -> sample window -> detail/raw signal/manual result 页面结构。
- `tests/test_sample_recording_storage.py` 和 `tests/test_sample_recording_web_api.py` 已存在，但 Web API 测试通过手动注入 `server.sample_storage`，不能证明生产 WebConfigServer 已完成集成。
- `pump_control_node.py` 已确认发布 `/usv/spectrometer_raw`、`/usv/spectrometer_voltage`、`/usv/spectrometer_absorbance`。
- `web_config_server.py` 约 247 KB，超过 CodexPro `read` 单文件上限；同时目标搜索未找到 `SampleRecordingStorage`、`sample_storage`、`/samples`、`manual-result`、`spectrometer_raw` 等生产集成标记。因此当前 P0-blocker 是：**核实并补齐 WebConfigServer 的生产路由、ROS raw subscriber 和 `sampling_started/stopped` 生命周期接入**。

后续执行时，不要直接声明“已完整实现按航点/GPS 切片”。更准确的表述是：**底层库和前端已具备雏形；生产闭环需要先确认/补齐 WebConfigServer 集成。**

## 0.2 2026-06-30 Codex 后续执行结果

Codex 已用 Git Bash 读取完整 `web_config_server.py`，确认 0.1 中的 P0-blocker 是工具读取限制导致的误判。生产 WebConfigServer 中已存在：

- `SampleRecordingStorage` 初始化与 `current_sample_window` 状态。
- `/usv/spectrometer_raw` 订阅。
- `sampling_started` 打开 SampleWindow。
- `sampling_stopped` / `survey_stopped` 关闭 SampleWindow 并保存 mission。
- samples/detail/raw/manual-result API 路由。

本轮补齐了 P0.5 测试盲区：

- GPS normalization 同时兼容 `{wgs84:{lat,lng,alt}, received_at}` 和 `{lat,lng,alt,received_at}`。
- Storage 测试显式断言 `gps_start`、`gps_end`、`gps_latest`。
- Web API 测试改为验证生产初始化，并走 `sampling_started -> raw frame x3 -> sampling_stopped` 回调链。

当前采样窗口 P0/P0.5 可作为已覆盖状态继续推进。下一步应进入 P1：航点/GPS 强关联、走航窗口策略、Web 层重启恢复。

## 0.3 2026-07-05 Codex 后续执行结果

已完成一个可独立验收的 P1 韧性项：`SampleRecordingStorage.close_window()` 在内存 builder 缺失时会从 raw JSONL 重建分光摘要，不再把已有帧统计重置为 0。

新增回归测试覆盖：旧 storage 写入 raw frame，新 storage 关闭同一 window，仍保留 `frame_count`、`valid_count`、`voltage_mean`、`raw_code_min/max`。

边界：这不等价于完整 Web 进程重启恢复。真实 Web 重启后 `WebConfigServer.current_sample_window` 会重新初始化为 `None`；后续 P1 应在启动或收到 `sampling_stopped` 时从当前 mission 的 `sample_windows[]` 恢复最后一个 `state=="open"` 的窗口并关闭。

当前采样窗口下一步仍是：

1. Web 层 open window 恢复：启动或 `sampling_stopped` 时恢复并关闭最后一个 open SampleWindow。
2. 航点/GPS 强关联：waypoint cache、distance-to-waypoint、position quality。
3. 走航窗口策略：按时间、距离、有效帧数或混合门控生成 survey windows。

## 1. 已确认的现状依据

### 1.1 系统职责边界

- 根文档明确：污染物浓度、采样点质量、GeoJSON/CSV、IDW surface 均归 `src/usv_ros`，不放在 ArduPilot/DetFirmware/QGC 中。
- 当前系统链路：QGC / Pixhawk / mavlink-router / ROS / ESP32 detector 已打通。
- Web 数据中心已跟随 `sampling_started` / `sampling_stopped` / `survey_stopped` 生命周期建档和停止。

重点依据：

- `AGENTS.md`
- `docs/current/20_system_overview.md`
- `docs/current/40_interfaces.md`
- `src/usv_ros/README.md`

### 1.2 真实分光数据已经存在，但没有按航点原始切片展示

真实检测装置数据流：

- `pump_control_node.py` 解析 `[0x55][0xDD]` 分光包。
- 原始字段包括：`timestamp_ms`、`tca_channel`、`status`、`raw_code`、`voltage`、`valid`、`i2c_error`、`not_configured`、`saturated`。
- 发布话题：
  - `/usv/spectrometer_raw`
  - `/usv/spectrometer_voltage`
  - `/usv/spectrometer_absorbance`

关键代码：

- `src/usv_ros/scripts/pump_control_node.py`：`_parse_spectro_packet()`
- `src/usv_ros/scripts/pump_control_node.py`：`_on_spectro_received()`

当前 Data 页面：

- `src/usv_ros/frontend/src/pages/Data.tsx` 只按 mission 展示 `data_points` 的电压/吸光度曲线。
- 没有航点/采样窗口列表。
- 没有 raw frame 文件查看。
- 没有人工浓度录入表单。

### 1.3 航点采样和走航采样是两套触发逻辑

定点采样：

- `NAV_SCRIPT_TIME(param1=1)` 触发 `USV_SMPL`。
- ROS 执行采样，完成后 bridge 发送 `USV_DONE`。
- `mavlink_trigger_node.py` 中 `_do_fcu_sample()` 设置 `current_sampling_context`，包含 `waypoint_seq`、`source: fcu`、`sample_id`。

走航采样：

- `COMMAND_LONG 31015` 开始，`31016` 停止。
- `mavlink_trigger_node.py` 通过 `_start_survey()`、`_survey_loop()`、`_start_survey_sample_once()` 按间隔/门控触发采样。
- 门控条件包括 GPS、新鲜度、速度、距离、分光有效性。

因此数据模型不能只叫 waypoint record，应抽象为 `SampleWindow`：

- waypoint / fcu：按航点事件切片。
- survey：按走航采样窗口切片。
- manual：按手动采样窗口切片。
- lab：兼容实验仿真。

## 2. 本阶段开发目标

### 2.1 P0 必须交付

1. 每次 `sampling_started -> sampling_stopped` 自动生成一个采样窗口 `SampleWindow`。
2. 窗口期间将 `/usv/spectrometer_raw` 原始分光帧写入该窗口专属 JSONL 文件。
3. 窗口关闭时生成摘要：帧数、有效帧数、电压均值/最小/最大、吸光度均值/最小/最大、raw_code 范围、质量标记。
4. 采样窗口关联：
   - mission_id
   - sample_id
   - mode/source
   - waypoint_seq，如可得
   - mavlink_sample_id，如可得
   - GPS start/end/latest，如可得
   - start_time/end_time
5. Web API 支持查询 mission 下采样窗口列表、查询某窗口 raw frames、写入人工浓度结果。
6. 前端数据中心改为 mission -> sample window -> raw signal/detail 的浏览结构。
7. 人工浓度录入后持久化，并在任务列表/窗口详情中显示。

### 2.2 P0 非目标

本阶段不要做：

- 自动污染物浓度算法。
- 液滴峰识别、峰面积积分、标曲计算。
- 修改 MAVLink 命令号或串口包格式。
- 在 QGC 展示污染物热力图。
- 在 ArduPilot/DetFirmware 写入浓度、历史记录或热力图逻辑。
- 大规模重构 `web_config_server.py`。

### 2.3 P1/P2 预留

P1：增强航点/GPS 关联准确性，包括 mission waypoint cache、距离航点误差、离线回放。

P2：接入液滴微流控自动处理算法：raw frames -> droplet detection -> features -> calibration -> concentration。

## 3. 推荐总体架构

### 3.1 第一阶段不要做独立 recorder node，优先集成 WebConfigServer

原因：当前 `MissionDataManager` 在 `web_config_server.py` 内部管理任务 JSON。若新建独立节点，它很难稳定知道 Web 当前 mission_id，容易出现两个进程各自建档、mission 对不齐的问题。

本阶段推荐：

1. 把核心逻辑封装到独立库：`scripts/lib/sample_recording/`。
2. 在 `web_config_server.py` 中最小集成这个库：
   - 复用现有 `sampling_started` / `sampling_stopped` / `survey_stopped` 回调。
   - 复用现有 `MissionDataManager.current_mission_data` / 当前任务文件。
   - 新增订阅 `/usv/spectrometer_raw`。
   - 由 Web 进程直接写 raw JSONL 和 mission sample metadata。

这样风险最低，第一版能最快闭环。

后续如需拆成独立 `spectral_recorder_node.py`，必须先设计跨进程 mission session 广播机制，例如 `/usv/data_recording/session`，否则不建议拆。

### 3.2 新增目录结构

建议新增：

```text
src/usv_ros/scripts/lib/sample_recording/
├── __init__.py
├── models.py
├── storage.py
└── summary.py
```

可选后续新增：

```text
src/usv_ros/scripts/lib/sample_recording/export.py
src/usv_ros/scripts/lib/sample_recording/processing.py
```

### 3.3 存储位置

已有 mission 文件位置：

```text
~/usv_ws/data/missions/mission_*.json
```

新增 raw frame 文件建议放在：

```text
~/usv_ws/data/missions/raw/<mission_id>/<sample_id>.jsonl
```

说明：

- `raw/` 是子目录，不影响现有 `mission_*.json` 列表。
- mission JSON 只保存 raw 文件相对路径和摘要，不保存全部 raw frames，避免任务文件膨胀。
- raw frame 使用 JSONL，一行一帧，便于边采边写、异常恢复和后续离线处理。

## 4. 数据模型设计

### 4.1 mission JSON 增量字段

在现有 mission JSON 顶层增加：

```json
{
  "sample_windows_schema_version": 1,
  "sample_windows": []
}
```

不要破坏现有 `data_points`、`track_points`、surface/geojson 相关逻辑。

### 4.2 SampleWindow schema v1

```json
{
  "sample_id": "mission_20260629_171432_wp003_001",
  "mission_id": "mission_20260629_171432",
  "schema_version": 1,
  "mode": "waypoint",
  "source": "fcu",
  "state": "closed",
  "waypoint_seq": 3,
  "mavlink_sample_id": 18,
  "survey_index": null,
  "route_ref": null,
  "start_time": "2026-06-29T17:14:32.123Z",
  "end_time": "2026-06-29T17:14:48.456Z",
  "duration_s": 16.333,
  "gps_start": {
    "lat": 30.0,
    "lng": 120.0,
    "alt": null,
    "received_at": 1782743672.123
  },
  "gps_end": {
    "lat": 30.00001,
    "lng": 120.00002,
    "alt": null,
    "received_at": 1782743688.456
  },
  "gps_latest": {
    "lat": 30.00001,
    "lng": 120.00002,
    "alt": null,
    "received_at": 1782743688.456
  },
  "spectrometer": {
    "raw_file": "raw/mission_20260629_171432/mission_20260629_171432_wp003_001.jsonl",
    "frame_count": 240,
    "valid_count": 232,
    "invalid_count": 8,
    "voltage_mean": 1.234,
    "voltage_min": 1.12,
    "voltage_max": 1.39,
    "absorbance_mean": 0.321,
    "absorbance_min": 0.28,
    "absorbance_max": 0.37,
    "raw_code_min": 12340,
    "raw_code_max": 12480,
    "first_timestamp_ms": 123456,
    "last_timestamp_ms": 139789,
    "quality_flags": []
  },
  "manual_result": {
    "status": "pending",
    "analyte": null,
    "concentration": null,
    "unit": null,
    "method": null,
    "operator": null,
    "recorded_at": null,
    "note": null
  },
  "processing": {
    "status": "not_run",
    "algorithm": null,
    "version": null,
    "result": null,
    "error": null,
    "processed_at": null
  }
}
```

### 4.3 Raw frame JSONL schema

每行一个 JSON 对象：

```json
{"received_at":1782743672.234,"timestamp_ms":123456,"tca_channel":2,"status":1,"raw_code":12345,"voltage":1.234,"valid":true,"i2c_error":false,"not_configured":false,"saturated":false,"absorbance":0.321,"baseline_set":true,"reference_voltage":2.8,"baseline_voltage":0.02}
```

字段来源：

- `/usv/spectrometer_raw`：`timestamp_ms`、`tca_channel`、`status`、`raw_code`、`voltage`、`valid`、错误标记。
- `/usv/spectrometer_voltage`：可补充 `absorbance`、`baseline_set`、`reference_voltage`、`baseline_voltage`。

P0 简化策略：

- raw JSONL 以 `/usv/spectrometer_raw` 为主。
- 如果 Web 已有 latest voltage payload，可在写 raw frame 时附加最近一次 absorbance/baseline 信息。
- 不要求逐帧严格同步 raw 与 voltage 两个 topic；后续自动算法可只依赖 raw voltage/raw_code。

## 5. 后端实现方案

### 5.1 `models.py`

职责：定义最小数据构造与校验函数。Python 3.8 兼容，不使用 `dict | None` 语法。

建议函数：

```python
def utc_now_iso(): ...
def make_sample_id(mission_id, mode, waypoint_seq=None, survey_index=None): ...
def default_manual_result(): ...
def default_processing(): ...
def make_window(...): ...
def normalize_manual_result(payload): ...
def normalize_raw_frame(payload, received_at=None, latest_voltage=None): ...
```

校验规则：

- `concentration`：允许空；非空必须是有限数字。
- `unit`：默认 `mg/L`，允许用户填写其他单位。
- `analyte`：默认空或 `unknown`，前端可显示“未指定”。
- `note`：最大长度建议 1000 字符。
- `operator`：最大长度建议 100 字符。

### 5.2 `summary.py`

职责：对 raw frame 流做增量统计。

建议类：

```python
class SpectrometerSummaryBuilder(object):
    def __init__(self): ...
    def add_frame(self, frame): ...
    def to_dict(self, raw_file): ...
```

统计内容：

- frame_count
- valid_count
- invalid_count
- voltage_mean/min/max
- absorbance_mean/min/max，如果有
- raw_code_min/max
- first_timestamp_ms/last_timestamp_ms
- quality_flags

质量标记建议：

- `no_frames`
- `no_valid_frames`
- `low_valid_ratio`
- `i2c_error_seen`
- `saturated_seen`
- `not_configured_seen`
- `short_duration`

### 5.3 `storage.py`

职责：文件路径、JSONL 追加、mission JSON 原子更新。

建议类：

```python
class SampleRecordingStorage(object):
    def __init__(self, missions_dir): ...
    def start_window(self, mission_data, context, gps_latest): ...
    def append_raw_frame(self, window, frame): ...
    def close_window(self, mission_data, window, gps_latest): ...
    def list_windows(self, mission_data): ...
    def read_raw_frames(self, mission_id, sample_id, limit=None, offset=0): ...
    def update_manual_result(self, mission_data, sample_id, payload): ...
```

注意：

- mission JSON 更新必须尽量复用现有 `MissionDataManager` 保存方法。如果没有公开保存方法，再添加一个小方法，不要在多个地方复制写文件逻辑。
- raw JSONL 追加时使用 UTF-8，一行一个 JSON。
- raw 文件路径必须限制在 `missions_dir/raw/` 下，API 读取时防止 path traversal。
- 写 mission JSON 时尽量使用临时文件 + `os.replace()`，如果现有 manager 已经有原子保存则复用。

### 5.4 集成 `web_config_server.py`

最小侵入集成点：

1. 初始化：
   - 创建 `self.sample_storage = SampleRecordingStorage(self.data_manager.missions_dir or 等价路径)`。
   - 创建 `self.current_sample_window = None`。
   - 创建 `self.latest_spectrometer_voltage_payload = {}`。
   - 创建 `self.latest_gps_position = None`，如已有同名字段则复用。

2. 新增订阅：

```python
rospy.Subscriber('/usv/spectrometer_raw', String, self._spectrometer_raw_cb)
```

3. 扩展 `_voltage_cb`：
   - 保留原有 Socket.IO、MissionDataManager.add_data_point 逻辑。
   - 额外缓存 latest voltage payload，供 raw frame 补充 absorbance/baseline。

4. 扩展 `_gps_cb` 或已有 GPS 回调：
   - 缓存 latest GPS：`lat/lng/alt/received_at`。
   - 注意 ROS NavSatFix 使用 longitude；对 Web 统一字段用 `lng`。

5. 扩展 `_trigger_status_cb`：
   - 收到 `sampling_started`：
     - 先让现有数据记录逻辑确保 mission 已启动。
     - 如果当前没有窗口，则根据当前 mission_id、mission_status、trigger context 开启 SampleWindow。
   - 收到 `sampling_stopped`：
     - 如果当前窗口存在，则关闭窗口并写入 mission JSON。
   - 收到 `survey_started`：
     - 不一定开窗口，真正窗口仍以每次 `sampling_started` 开。
   - 收到 `survey_sample_done`：
     - 不重复关闭；走航单次窗口通常仍由 `sampling_stopped` 关闭。
   - 收到 `survey_stopped`：
     - 如果还有未关闭窗口，兜底关闭。

6. 新增 `_spectrometer_raw_cb`：
   - 如果 `current_sample_window is None`，丢弃或只缓存最近帧，不持久化。
   - 如果窗口打开，解析 JSON，normalize 后 append JSONL，并更新增量 summary。
   - 解析失败不要 crash，记录 log。

7. 采样 context 推断：
   - 优先从 mission status 文本中解析：`SAMPLING:<seq>`、`SURVEYING:<interval>`。
   - 优先使用现有 server 内部状态：如果已有 `last_mission_status` / `survey_status` / `lab_status`，复用。
   - P0 可接受 `waypoint_seq` 为空，但不能影响 raw 切片。
   - 后续 P1 再从 MAVROS mission cache 精准补航点。

## 6. Web API 设计

在 `web_config_server.py` 增加 API。

### 6.1 List sample windows

```text
GET /api/data/mission/<mission_id>/samples
```

返回：

```json
{
  "success": true,
  "data": {
    "mission_id": "mission_x",
    "samples": [ ...SampleWindow摘要... ]
  }
}
```

列表中不要返回 raw frames，只返回窗口 metadata 和 summary。

### 6.2 Get sample detail

```text
GET /api/data/mission/<mission_id>/sample/<sample_id>
```

返回单个 SampleWindow 完整 metadata，不返回 raw frames。

### 6.3 Get raw frames

```text
GET /api/data/mission/<mission_id>/sample/<sample_id>/raw?limit=2000&offset=0
```

返回：

```json
{
  "success": true,
  "data": {
    "mission_id": "mission_x",
    "sample_id": "sample_y",
    "count": 240,
    "frames": []
  }
}
```

限制：

- `limit` 默认 2000，最大 20000。
- `offset` 默认 0。
- 后续如果 raw 很大，再做分页/抽稀。

### 6.4 Manual result update

```text
POST /api/data/mission/<mission_id>/sample/<sample_id>/manual-result
```

请求：

```json
{
  "analyte": "COD",
  "concentration": 0.84,
  "unit": "mg/L",
  "method": "manual_microfluidic_calc",
  "operator": "user",
  "note": "第3航点人工根据液滴峰面积计算"
}
```

返回更新后的 SampleWindow。

校验：

- mission_id/sample_id 必须存在。
- concentration 可为空；非空必须 finite。
- 字符串字段裁剪前后空白。
- 失败返回 `{success:false, error:"..."}`，HTTP 400/404。

## 7. 前端实现方案

### 7.1 文件建议

新增：

```text
src/usv_ros/frontend/src/lib/sample-types.ts
src/usv_ros/frontend/src/components/sample-window-list.tsx
src/usv_ros/frontend/src/components/sample-window-detail.tsx
src/usv_ros/frontend/src/components/manual-result-form.tsx
```

修改：

```text
src/usv_ros/frontend/src/pages/Data.tsx
```

### 7.2 Data 页面结构

将当前两栏改为三段式：

```text
左侧：Mission 列表
中间：采样窗口列表
右侧：采样窗口详情
```

右侧详情包含：

1. 基本信息：
   - sample_id
   - mode/source
   - waypoint_seq
   - start/end/duration
   - GPS start/end
2. 分光摘要卡片：
   - frame_count
   - valid_count
   - valid ratio
   - voltage mean/min/max
   - absorbance mean/min/max
   - quality_flags
3. raw signal 图表：
   - X 轴：frame index 或 timestamp_ms。
   - Y 轴：voltage。
   - 可选第二轴：absorbance。
   - Tooltip 显示 raw_code、valid、status。
4. 人工浓度记录表单：
   - analyte
   - concentration
   - unit
   - method
   - operator
   - note
   - 保存按钮
5. 导出按钮：
   - 导出该窗口 raw JSONL 或 CSV。
   - P0 可先只用 raw API 前端生成 CSV。

### 7.3 前端兼容要求

- 如果 mission 没有 `sample_windows`，显示“该任务暂无航点级分光切片”，不要报错。
- 老任务仍能查看原有 mission 曲线。
- 如果 raw frames 数量很大，前端先只请求默认 limit；显示“已加载前 N 帧”。
- 移动端不强求完美，但不能完全不可用。

## 8. 测试计划

### 8.1 后端单元测试

新增测试文件建议：

```text
src/usv_ros/tests/test_sample_recording_storage.py
```

覆盖：

1. `start_window()` 能生成合法 SampleWindow。
2. `append_raw_frame()` 写入 JSONL。
3. `close_window()` 生成 summary 并写入 mission data。
4. 无 raw frames 时标记 `no_frames`。
5. 有 invalid frames 时 valid_count/invalid_count 正确。
6. `update_manual_result()` 持久化人工浓度。
7. 防 path traversal：伪造 `../` sample_id 不允许读取任意文件。

### 8.2 Web API 测试

在现有 `src/usv_ros/tests/test_hardware_runtime_sync.py` 或新文件中添加：

1. `sampling_started` 后 raw frames 被写入当前窗口。
2. `sampling_stopped` 后 mission JSON 包含 `sample_windows`。
3. 连续两次采样形成两个窗口，raw_file 不相同。
4. `GET /api/data/mission/<id>/samples` 返回窗口列表。
5. `GET /api/data/mission/<id>/sample/<sample_id>/raw` 返回 raw frames。
6. `POST /manual-result` 更新浓度，重新 GET 仍存在。
7. survey 模式下窗口 `mode/source` 合理，不误覆盖 waypoint 窗口。

### 8.3 前端验证

至少执行：

```bash
cd src/usv_ros/frontend
npm run build
```

如现有 smoke 脚本可用，追加简单静态检查：

- Data 页面引用 `/api/data/mission/` 新 samples API。
- 没有 TypeScript 编译错误。

### 8.4 推荐验证命令

在 `src/usv_ros` 执行：

```bash
python3 -m py_compile scripts/*.py scripts/lib/lab_sim/*.py scripts/lib/sample_recording/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
cd frontend && npm run build
```

如果环境缺 ROS 依赖，至少运行已有测试使用的 mock loader 测试；不要因为本地缺真实硬件而跳过纯逻辑测试。

## 9. 实施步骤

### Step 1：定位现有 MissionDataManager 保存点

先在 `web_config_server.py` 中找到：

- `MissionDataManager` 定义。
- `start_mission()`。
- `stop_mission()`。
- `add_data_point()`。
- mission JSON 保存函数。
- `_trigger_status_cb()`。
- `_voltage_cb()`。
- `_gps_cb()` 或 GPS 相关回调。

目标：明确最小集成点，不重写现有数据中心。

### Step 2：先写 sample_recording 单元测试

用临时目录构造 mission data，不依赖 ROS。

测试先失败，锁定 schema 和存储行为。

### Step 3：实现 `scripts/lib/sample_recording/`

按第 5 节实现 models/storage/summary。

要求：

- Python 3.8 兼容。
- 不引入新第三方依赖。
- 不使用全局可变状态。
- 文件写入异常要返回可控错误或记录 log，不能导致 Web 主线程崩溃。

### Step 4：集成 WebConfigServer 生命周期

在 `web_config_server.py` 中最小改动：

- 初始化 storage。
- 新增 raw subscriber。
- trigger status 开关 window。
- raw callback 写 JSONL。
- voltage/gps callback 缓存 latest。
- mission stop 时兜底关闭窗口。

关键要求：

- 若没有 active mission，`sampling_started` 先调用现有 start recording 逻辑，再 start window。
- 若收到重复 `sampling_started`，不要重复开窗口。
- 若收到 `sampling_stopped` 但没有窗口，忽略并 log debug。
- 任何 raw frame 解析失败不影响 Web 服务。

### Step 5：增加 API

实现第 6 节 API。

注意：

- API 返回结构与现有风格一致：`success/data/error`。
- 404/400 明确。
- raw frames API 不返回任意路径文件。

### Step 6：改 Data 页面

从当前 mission-only 曲线升级到 mission/sample/window 结构。

保留老任务兼容：

- 没有 sample_windows 时仍显示原 data_points 曲线。
- 有 sample_windows 时优先显示采样窗口列表。

### Step 7：文档更新

更新：

- `docs/current/40_interfaces.md`：增加 API 和 SampleWindow 说明。
- `src/usv_ros/README.md`：增加数据存储位置、Web API、人工浓度记录说明。
- 如改 launch 或新增参数，再同步 `docs/current/50_build_update_runbook.md`。

### Step 8：运行验证并记录结果

执行第 8.4 节命令。若某些命令因环境缺失失败，记录失败原因和已完成的静态验证。

## 10. 验收标准

P0 合格标准：

1. 在测试中模拟一次 mission：
   - 触发 `sampling_started`。
   - 注入 3 条 `/usv/spectrometer_raw`。
   - 触发 `sampling_stopped`。
   - mission JSON 出现 1 个 `sample_windows`。
   - raw JSONL 存在 3 行。
2. 模拟两次航点采样后，Web API 能列出 2 个 sample windows。
3. 每个 sample window 有独立 raw_file。
4. POST 人工浓度后，重新读取 mission 仍能看到 manual_result。
5. 前端 build 通过。
6. 老任务没有 sample_windows 时，Data 页面不崩溃。
7. 不修改 ArduPilot/DetFirmware/QGC 协议。

## 11. 风险与处理

### 风险 A：WebConfigServer 文件过大，改动容易引入回归

处理：核心逻辑放在 `scripts/lib/sample_recording/`，`web_config_server.py` 只做薄集成。

### 风险 B：当前 Web 进程和 MissionDataManager 保存逻辑不易复用

处理：先查现有保存方法；如果没有公开方法，给 `MissionDataManager` 添加小的 `_save_current_mission()` 或等价方法，并用测试覆盖。

### 风险 C：waypoint_seq 不一定总能准确获得

处理：P0 允许 `waypoint_seq=null`，但必须保存 GPS 和时间窗口。P1 再做 mission waypoint cache 和 nearest waypoint 匹配。

### 风险 D：raw frame 量过大

处理：P0 使用 JSONL 文件，不塞进 mission JSON。API 默认 limit，前端只加载部分或按需加载。

### 风险 E：真实硬件 topic 频率高，Web 回调阻塞

处理：JSONL 逐行追加尽量轻量；必要时在 storage 内使用简单队列/后台 flush，但 P0 先保持简单。如果现场频率很高，再做批量 flush。

## 12. 后续 P1/P2 设计预留

### P1：航点/GPS 强关联

新增 mission waypoint cache：

- 从 `/mavros/mission/waypoints` 或现有 QGC 导入缓存读取航点坐标。
- SampleWindow 增加：
  - `waypoint_wgs84`
  - `distance_to_waypoint_m`
  - `gps_nearest`
  - `position_quality`

### P2：自动液滴处理

新增处理接口：

```text
POST /api/data/mission/<mission_id>/sample/<sample_id>/process
```

处理器输入 raw JSONL，输出：

```json
{
  "status": "processed",
  "algorithm": "droplet_peak_v1",
  "version": "0.1.0",
  "result": {
    "concentration": 0.84,
    "unit": "mg/L",
    "features": {
      "droplet_count": 12,
      "peak_area": 123.4,
      "peak_height": 0.32
    }
  }
}
```

人工结果保留，后续用于校核或覆盖自动结果。

## 13. 开发边界提醒

- 不要在根仓库做跨仓库全量提交。
- 业务代码改动应在 `src/usv_ros/` 子仓库内提交。
- 回答或提交说明中要列出源码依据和验证命令。
- 若发现文档与源码冲突，以源码为准，并同步更新 `docs/current/`。

## Implementation contract

- Work from this plan in small, reviewable steps.
- Keep edits scoped to the requested task and existing project conventions.
- Run focused verification before handing work back.
- Update .ai-bridge/agent-status.md with files touched, checks run, results, blockers, and review notes.
- Save the final review diff to .ai-bridge/implementation-diff.patch when practical.
- Append notable execution events to .ai-bridge/execution-log.jsonl when the implementation agent supports logging.
