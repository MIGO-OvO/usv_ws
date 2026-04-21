# 无人船自动采样任务开发方案
Updated: 2026-04-13T13:34:06Z

## 1. 目标

### 1.1 当前优先目标
实现以下自动任务流程：
1. 无人船下水并完成基础连接。
2. 在 QGC 上点击开始任务。
3. 飞控进入 AUTO，自动航行至第一个航点。
4. 到达采样航点后，ROS 协调节点切换飞控到 HOLD。
5. 船体稳定后，自动执行一轮采样流程。
6. 采样完成后自动切回 AUTO，继续前往下一航点。
7. 在每个采样点重复上述流程，直至任务结束。

### 1.2 最终目标
1. 支持在 QGC 或 Web 端为每个采样点单独配置采样循环次数。
2. 支持 QGC 航点配置与 Web/ROS 采样配置双向同步。
3. 将“导航任务 + 采样任务”从当前松耦合实现，升级为统一任务模型。

## 2. 当前实现评估

### 2.1 已完成能力
#### A. 航点到达触发采样
`src/usv_ros/scripts/mavlink_trigger_node.py:124-135`
- 订阅 `/mavros/mission/reached`。
- 在 `_waypoint_cb()` 中根据 `auto_trigger_on_waypoint` 自动触发采样。
- 支持 `trigger_waypoints` 白名单方式限制触发航点。

#### B. 到点切 HOLD 并启动采样序列
`src/usv_ros/scripts/mavlink_trigger_node.py:330-365`
- `_start_sampling_sequence()` 已实现：
  - `set_mode("HOLD")`
  - 加载 `sampling_config.json`
  - 发布 `/usv/automation_steps`
  - 调用 `/usv/automation_start`

#### C. 采样自动化执行引擎
`src/usv_ros/scripts/pump_control_node.py:1227-1245`
`src/usv_ros/scripts/lib/automation_engine.py:115-123,261-307`
- 支持自动化步骤列表 `steps`。
- 支持 `loop_count` 循环次数。
- 支持 pause/resume/stop。
- 支持 PID 完成等待和步骤完成后 interval 计时。

#### D. 采样完成后恢复 AUTO
`src/usv_ros/scripts/mavlink_trigger_node.py:137-143,390-405`
- 采样完成后调用 `_resume_auto_if_mission_exists()`。
- 若飞控中存在 mission，则切回 `AUTO`；否则维持 `HOLD`。

#### E. 飞控支持标准 Mission Start 与 HOLD/AUTO 模式
`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp:494-500`
`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp:1013-1020`
- 飞控支持 `MAV_CMD_MISSION_START`。
- Rover 模式集中存在 `mode_hold` 与 `mode_auto`。

#### F. QGC 已具备采样控制与采样数据展示能力
`WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml:87-90,316-320`
`docs/current/overview.md:47-49`
- QGC 可发送 `31010~31014` 采样控制命令。
- QGC 已有独立采样数据页面 `USVSamplingDataView.qml`。
- QGC 已能显示 `USV_STEP/USV_STOT/USV_SCNT/USV_PERR/USV_PMOD` 等遥测字段。

### 2.2 未完成能力
#### A. 船体稳定判定
`src/usv_ros/scripts/mavlink_trigger_node.py:339-341`
- 当前仅在切换 HOLD 后固定 `sleep(1.0)`。
- 尚未根据速度、航向变化率、位置漂移等状态判断“稳定”。

#### B. 航点级采样次数配置
- 当前 `loop_count` 为整套 `sampling_sequence` 的全局循环次数。
- 尚未实现“每个 waypoint 单独配置 loop_count”。

#### C. QGC Mission 与采样任务未统一
- 当前 QGC 航点任务属于飞控标准 Mission。
- 当前采样任务属于 ROS 自动化流程。
- 两者通过 `mission/reached` 事件临时耦合，未形成统一任务模型。

#### D. QGC 缺少任务过程视图
- 当前 QGC 能显示采样遥测，但不能直接表达：
  - 当前航点是否配置采样
  - 当前航点要求采样几次
  - 已完成几次
  - 当前任务阶段（航行 / HOLD / 稳定等待 / 采样 / 恢复 AUTO）

#### E. QGC 与 Web 配置未同步
`src/usv_ros/scripts/web_config_server.py:802-831,1397-1440`
- Web 已能保存采样配置和触发 mission start/stop。
- 但未建立 QGC Mission 与 Web 任务配置之间的统一数据结构和同步机制。

## 3. 当前完成度判断

### 3.1 第一项目标完成度
目标：“QGC 开始任务 -> 航点自动采样 -> 继续下一个点”。

完成情况：
- 已完成：航点到达触发、HOLD、采样执行、AUTO 恢复。
- 未完成：稳定判定、航点级循环配置、统一任务可视化。

结论：
- 当前完成度约 `65%`。
- 现有实现可视为“ROS 协调层闭环原型”，不是“任务系统级闭环”。

### 3.2 最终目标完成度
目标：“每个采样点可配置采样次数 + QGC/Web 双向同步”。

完成情况：
- Web 侧已有配置存储、任务 API、预设机制。
- QGC 侧已有采样遥测显示。
- 缺少统一任务模型、航点级采样配置、双向同步协议、QGC Mission 编辑扩展。

结论：
- 当前完成度约 `20%~30%`。

## 4. 问题根因

### 4.1 当前架构的本质
当前实现并非“飞控任务内建采样”，而是：
- 飞控执行标准导航 mission。
- ROS 监听航点到达后插入 HOLD 和采样动作。
- 采样结束后 ROS 再恢复 AUTO。

即：
`航点导航任务` 与 `采样任务` 目前是两套系统，通过事件触发拼接。

### 4.2 导致的问题
1. 任务语义分裂：QGC Mission 中看不到航点采样配置。
2. 状态语义分裂：QGC 只能分别显示导航状态和采样状态。
3. 配置真源分裂：航点在 QGC，采样步骤在 Web/ROS。
4. 联调复杂：任务修改需同时操作 QGC 与 Web。

## 5. 目标架构

### 5.1 阶段目标架构
短期内不直接改飞控 Mission 内核，采用以下结构：
- 飞控：继续负责标准航点导航与模式切换。
- ROS：负责采样协调、稳定判定、航点级采样策略。
- QGC/Web：逐步共享同一份任务元数据。

### 5.2 最终任务模型
建议引入统一任务结构：

```json
{
  "mission_meta": {
    "name": "river-demo"
  },
  "waypoints": [
    {
      "seq": 0,
      "lat": 30.0,
      "lon": 114.0,
      "hold_before_sampling_s": 5,
      "sampling": {
        "enabled": true,
        "loop_count": 2,
        "preset": "default",
        "retry_count": 1,
        "on_fail": "HOLD"
      }
    }
  ]
}
```

该结构用于描述：
- 哪些航点需要采样。
- 每个航点采样几轮。
- 稳定等待时间。
- 失败策略。
- 采样预设名称。

## 6. 分阶段开发路径

## 6.1 阶段一：补全现有 ROS 自动闭环（优先级最高）
目标：让当前自动任务流程达到现场可用状态。

### 阶段一改动点
#### A. 增加稳定判定
改动位置：`src/usv_ros/scripts/mavlink_trigger_node.py`

新增能力：
- 在 HOLD 后不立即采样。
- 通过 MAVROS 订阅以下信息进行稳定判断：
  - 地速
  - 航向变化率
  - 到航点距离
  - 持续稳定时间

建议接口：
- `wait_until_stable(timeout_s, speed_thresh, yaw_rate_thresh, dist_thresh)`

验收标准：
- 到达航点后进入 HOLD。
- 满足稳定条件后才开始采样。
- 超时进入失败策略。

#### B. 增加航点触发去重机制
改动位置：`src/usv_ros/scripts/mavlink_trigger_node.py`

新增能力：
- 为 waypoint seq 建立状态机，避免重复采样。
- 状态建议：
  - `ARRIVED`
  - `HOLDING`
  - `SAMPLING`
  - `DONE`
  - `FAILED`

验收标准：
- 同一航点 `mission/reached` 重复上报时，不重复启动采样。

#### C. 增加失败处理策略
改动位置：`src/usv_ros/scripts/mavlink_trigger_node.py`

新增能力：
- 每个采样点支持：
  - `retry_count`
  - `on_fail = HOLD | SKIP | ABORT`

验收标准：
- 稳定等待超时或采样失败时，能按策略自动处理。

#### D. 支持航点级 loop_count（先放 ROS/Web）
改动位置：
- `src/usv_ros/scripts/web_config_server.py`
- `src/usv_ros/scripts/mavlink_trigger_node.py`
- `src/usv_ros/config/*.json|yaml`

新增能力：
- 在 ROS 配置中为 waypoint seq 单独定义采样配置。
- 到达不同航点时，按 seq 覆盖默认 `loop_count`。

验收标准：
- 不同航点可执行不同次数的采样循环。

#### E. 增加任务阶段状态发布
改动位置：
- `src/usv_ros/scripts/mavlink_trigger_node.py`
- `src/usv_ros/scripts/usv_mavlink_router_bridge.py`
- `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.*`

新增状态建议：
- `NAVIGATING`
- `WAYPOINT_REACHED`
- `HOLDING`
- `WAITING_STABLE`
- `SAMPLING`
- `SAMPLING_DONE`
- `RESUMING_AUTO`
- `FAILED`

验收标准：
- QGC 和 Web 可观察完整任务阶段，而不仅是“采样中/空闲”。

### 阶段一交付结论
完成后可实现：
- QGC 开始导航任务。
- 到采样点自动 HOLD。
- 稳定后采样。
- 采样完成后继续 AUTO。
- 不同采样点执行不同采样轮次。

## 6.2 阶段二：建立统一任务数据模型
目标：让 QGC 与 Web 使用同一套任务语义。

### 阶段二改动点
#### A. 在 Web/ROS 侧定义任务模型
改动位置：
- `src/usv_ros/scripts/web_config_server.py`
- `src/usv_ros/frontend/src/`
- `~/usv_ws/config/*.json`

新增能力：
- 统一存储 `waypoints + sampling` 组合任务数据。
- 支持导入/导出任务文件。
- 支持按航点编辑采样参数。

#### B. 建立 Mission ID / 版本号机制
建议字段：
- `mission_id`
- `updated_at`
- `source = qgc | web`
- `version`

用途：
- 用于处理同步冲突。
- 用于标记当前 QGC 与 Web 是否一致。

#### C. Web 页面升级为任务编辑器
改动位置：`src/usv_ros/frontend/src/pages/`

新增能力：
- 基于 waypoint seq 显示采样配置表。
- 支持修改：
  - sampling enabled
  - loop_count
  - hold_before_sampling_s
  - retry_count
  - on_fail
  - preset

阶段二验收标准：
- Web 可独立编辑完整采样任务配置。
- 配置不再只是全局 `sampling_sequence`。

## 6.3 阶段三：实现 QGC/Web 同步
目标：任务配置在两端可互通。

### 方案选择
#### 方案 A：轻量同步（建议先做）
- QGC 管理标准航点。
- ROS/Web 管理扩展采样 metadata。
- 两者通过文件/API 进行同步。

优点：
- 对现有 QGC 内核侵入小。
- 适合快速交付。

缺点：
- QGC 中航点的采样字段不是原生 Mission 字段。

#### 方案 B：深度集成（长期方案）
- 在 QGC Plan/MissionItem 层引入 USV 自定义采样字段。
- 航点编辑器中可直接配置采样次数与采样策略。

优点：
- 用户体验最佳。
- Mission 与采样真正统一。

缺点：
- 改动大，涉及 QGC MissionManager 与编辑器链路。

### 推荐顺序
先做方案 A，再评估是否升级为方案 B。

## 6.4 阶段四：QGC Plan 原生扩展（长期）
目标：将采样配置真正收口到 QGC 航点编辑流程。

### 需要重点修改的模块
- `WQ-USV-QGroundControl/src/MissionManager/`
- `PlanMasterController`
- 航点编辑 QML
- 自定义 FirmwarePlugin / Mission command 扩展

### 目标能力
- 每个 waypoint 直接显示“是否采样 / 采样次数 / 保持时间 / 失败策略”。
- 上传 mission 时一并上传采样元数据。
- 下载 mission 时恢复采样配置。

## 7. 三端开发分工建议

### 7.1 ROS 端
重点文件：
- `src/usv_ros/scripts/mavlink_trigger_node.py`
- `src/usv_ros/scripts/web_config_server.py`
- `src/usv_ros/scripts/lib/automation_engine.py`
- `src/usv_ros/scripts/pump_control_node.py`

职责：
- 稳定判定
- 航点级采样策略
- 任务状态机
- Web API 和任务配置存储

### 7.2 QGC 端
重点文件：
- `WQ-USV-QGroundControl/custom/res/USVSamplingDataView.qml`
- `WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml`
- `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.*`
- 后续阶段再进入 `src/MissionManager/`

职责：
- 任务状态可视化
- 航点采样参数展示
- 中后期支持编辑与同步

### 7.3 飞控端
重点文件：
- `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`
- `ardupilot-usv/Rover/sensors.cpp`
- `ardupilot-usv/Rover/Rover.h`

职责：
- 保持标准 Mission 导航能力稳定
- 保持 `NAMED_VALUE_FLOAT` 遥测缓存和重发稳定
- 如后续需要，可增加与任务状态更贴合的遥测字段

## 8. 推荐实施顺序
1. 阶段一：补稳定判定、去重、失败策略、航点级 loop_count。
2. 阶段一补充：增强 QGC/Web 任务阶段显示。
3. 阶段二：定义统一任务 JSON 模型。
4. 阶段二补充：Web 侧形成任务编辑器。
5. 阶段三：实现 QGC 与 Web 的轻量同步。
6. 阶段四：视需要再做 QGC Plan 原生扩展。

## 9. 风险与注意事项

### 9.1 风险
1. `mission/reached` 的触发时机与现场漂移可能不一致，稳定判定必须独立实现。
2. 如果重复切 HOLD/AUTO，可能影响飞控任务推进，需要增加航点状态去重。
3. QGC/Web 同步若没有 mission_id/version，会出现覆盖冲突。
4. QGC 深度改 MissionManager 的成本高，应在数据模型稳定后再开展。

### 9.2 约束
1. MAVLink 相关实现必须以飞控源码为准，不可仅凭协议猜测。
2. 自定义上行遥测仍需遵循飞控当前 `NAMED_VALUE_FLOAT` 缓存与 2Hz 转发机制。
3. 现阶段验证以逻辑验证为主，实际现场联调由用户完成。

## 10. 建议近期里程碑

### 里程碑 M1
- 完成稳定判定
- 完成 waypoint seq 去重
- 完成采样失败策略
- 完成航点级 loop_count

交付结果：
- 第一项目标进入可现场测试状态。

### 里程碑 M2
- 完成统一任务 JSON 模型
- Web 支持按航点编辑采样配置

交付结果：
- Web 成为完整任务配置端。

### 里程碑 M3
- 完成 QGC 与 Web 轻量同步
- QGC 显示航点采样参数和任务阶段

交付结果：
- 用户在 QGC / Web 均能理解当前任务结构。

### 里程碑 M4
- 评估是否推进 QGC Plan 原生扩展

交付结果：
- 决定是否进入深度集成路线。
