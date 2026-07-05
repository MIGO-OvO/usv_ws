# QGC 地面站专项优化方案

Updated: 2026-07-03T17:34:28+08:00
Workspace: `D:\usv_ws`
Target agent: Codex / local implementation agent
Scope: `WQ-USV-QGroundControl/` 为主，必要时同步 `docs/current/`；不要修改 ROS/固件协议语义，除非发现 QGC 与现有协议事实不一致。

## 0. 背景与目标

本方案来自对当前项目中 QGC 地面站适配性的静态分析。当前系统中 QGC 的正确定位是：

- 任务规划：在 Plan 中添加 USV 采样任务项。
- 手动控制：发送 `COMMAND_LONG 31010..31019` 给 companion component `191`。
- 遥测展示：展示固件转发的 `NAMED_VALUE_FLOAT` 载荷遥测。
- 现场反馈：给操作员展示链路、状态、ACK、超时、健康和采样进度。

QGC 不应在第一阶段承担污染物浓度计算、历史数据、GeoJSON/CSV、IDW 热力图、科研 surface 或图件导出。这些职责属于 `src/usv_ros/` 的 Web/API/数据中心。

本次优化的目标不是大改架构，而是把 QGC 的任务流和工作流边界进一步收口，降低现场误操作和跨端语义漂移。

## 1. 当前已确认事实

### 1.1 系统链路

主链路如下：

```text
QGC custom UI
  | Plan: MAV_CMD_NAV_SCRIPT_TIME(param1=1)
  | Manual: COMMAND_LONG 31010..31019
  | Display: NAMED_VALUE_FLOAT facts
  v
Pixhawk 6C / ardupilot-usv
  | TELEM2 MAVLink2
  v
mavlink-routerd on Jetson
  |-- UDP 127.0.0.1:14550 -> MAVROS
  |-- TCP 127.0.0.1:5760 -> usv_mavlink_router_bridge.py
  v
ROS Noetic / usv_ros
  |-- mavlink_trigger_node.py
  |-- pump_control_node.py
  |-- web_config_server.py
  v
ESP32 detector firmware
```

依据文档：

- `docs/current/20_system_overview.md`
- `docs/current/40_interfaces.md`
- `docs/current/60_source_map.md`
- `docs/current/70_verification.md`

### 1.2 QGC 关键源码

重点文件：

| 文件 | 职责 |
|---|---|
| `WQ-USV-QGroundControl/custom/src/FirmwarePlugin/USVFirmwarePluginFactory.cc` | 限制 Rover/Boat，选择 ArduPilot/PX4 USV 插件 |
| `WQ-USV-QGroundControl/custom/src/FirmwarePlugin/USVFirmwarePlugin.cc` | 注册 `usvPayload` FactGroup |
| `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.h` | QGC 载荷 Facts 声明 |
| `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc` | 解析 `NAMED_VALUE_FLOAT` 到 Facts |
| `WQ-USV-QGroundControl/custom/res/USVPayloadFactGroup.json` | Fact 元数据与状态枚举 |
| `WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml` | 主载荷控制面板，手动命令、ACK、超时、门控 |
| `WQ-USV-QGroundControl/custom/res/USVActionBar.qml` | FlyView 底部快捷操作栏 |
| `WQ-USV-QGroundControl/custom/res/USVFlyViewCustomLayer.qml` | FlyView 自定义层、警告横幅、载荷入口 |
| `WQ-USV-QGroundControl/custom/res/USVFlyViewLayout.js` | 状态码常量与面板显示逻辑 |
| `WQ-USV-QGroundControl/src/MissionManager/MavCmdInfoRover.json` | Rover Plan 任务命令元数据 |
| `WQ-USV-QGroundControl/custom/res/actions/usv_actions.json` | MAVLink Actions 手动命令定义 |
| `WQ-USV-QGroundControl/custom/tests/test_usv_qgc_contract.py` | QGC 合约测试 |
| `WQ-USV-QGroundControl/custom/tests/tst_USVFlyViewLayoutLogic.qml` | QML 状态逻辑测试 |

### 1.3 航线定点采样闭环

正确闭环：

```text
QGC Plan 添加 MAV_CMD_NAV_SCRIPT_TIME(param1=1, param2=timeout)
  -> ArduRover mode_auto.cpp 执行 NAV_SCRIPT_TIME
  -> 固件发送 NAMED_VALUE_FLOAT USV_SMPL(sample_id)
  -> usv_mavlink_router_bridge.py 转发为 /usv/mavlink_cmd_rx: 31010,param2=sample_id
  -> mavlink_trigger_node.py 识别 param2>0 为 FCU 触发采样
  -> ROS/泵控执行采样
  -> sampling_stopped
  -> bridge 发送 NAMED_VALUE_FLOAT USV_DONE(sample_id)
  -> ArduRover nav_script_time_done(sample_id)，mission 继续
```

关键事实：

- 航线定点采样使用 `MAV_CMD_NAV_SCRIPT_TIME`，不是 mission item `31010`。
- `31010` 只用于手动点采样；若 `param2>0`，ROS 侧将其视为 FCU `USV_SMPL` 转换后的内部触发。
- QGC 载荷面板不应发送 `42702`，Plan 任务才使用 `42702`。

## 2. 总体执行原则

1. 以源码为准，文档只作为辅助。若文档和源码冲突，先按源码判断，再同步文档。
2. 不改 MAVLink 命令号，不改 component id，不改串口协议。
3. QGC 只做任务、命令和遥测展示；不要把污染物地图、浓度计算、历史导出搬进 QGC。
4. 所有 UI 命令入口必须共享相同语义：同一命令在不同按钮上不能有不同前置条件。
5. 涉及状态码、字段名、命令边界时必须同步测试。
6. 不要做大规模重构 QGC 原工程，只改 `custom/` 和必要的 mission metadata。

## 3. P0：必须优先完成

### P0.1 统一 `USV_STAT` 状态码语义

#### 问题

当前主载荷面板已经把 `USV_STAT=3` 显示为“任务失败”，但 FlyView 顶部警告横幅仍显示“载荷故障，请检查采样模块”。这会把流程失败误导成硬件故障。

相关文件：

- `WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml`
- `WQ-USV-QGroundControl/custom/res/USVFlyViewCustomLayer.qml`
- `WQ-USV-QGroundControl/custom/res/USVPayloadFactGroup.json`
- `WQ-USV-QGroundControl/custom/res/USVFlyViewLayout.js`
- `WQ-USV-QGroundControl/custom/tests/test_usv_qgc_contract.py`

#### 要求

1. 将所有 QGC UI 中 `USV_STAT=3` 的文案统一为“任务失败”或“采样任务失败”。
2. 不要再显示“载荷故障，请检查采样模块”这种硬件归因文案，除非未来有独立硬件故障状态码。
3. 补充或更新测试，禁止该旧文案再次出现。
4. 检查 `USVPayloadFactGroup.json` 的枚举文案与 QML 文案一致。

#### 验收

- 搜索 `载荷故障，请检查采样模块`，QGC custom 中不应再出现。
- `USV_STAT=3` 在主面板、顶部横幅、数据页或摘要条中含义一致。
- `python custom/tests/test_usv_qgc_contract.py` 能通过，或至少静态断言覆盖该文案变化。

### P0.2 收口 Plan mission command 与 manual action command 的边界

#### 问题

当前约定是：

- 航线定点采样：`MAV_CMD_NAV_SCRIPT_TIME(param1=1)`。
- 手动控制：`COMMAND_LONG 31010..31019`。

但 `WQ-USV-QGroundControl/src/MissionManager/MavCmdInfoRover.json` 中除了 `42702`，还注册了 `31015/31016/31017/31018/31019` 为 Plan 可编辑命令。这会让操作员误以为这些手动动作可以直接作为航线任务项使用。

#### 推荐决策

第一阶段采用保守边界：

- Plan mission 中只保留 `42702 MAV_CMD_NAV_SCRIPT_TIME` 作为“定点采样任务项”。
- `31010..31019` 全部保留为手动命令或 Actions，不作为航线 mission item。
- 如果确实需要航线中控制走航/基线/信号采集，另起方案设计阻塞/非阻塞语义、失败策略、ACK 处理和固件支持；不要在本轮顺手开放。

#### 要求

1. 检查 `MavCmdInfoRover.json` 是否应该移除 `31015/31016/31017/31018/31019`。
2. 保留 `custom/res/actions/usv_actions.json` 中的手动动作定义。
3. 保持 `31010` 不出现在 Plan mission metadata。
4. 更新测试：
   - Plan metadata 应包含 `42702`。
   - Plan metadata 不应包含 `31010..31019`，除非项目决策明确改变。
   - Actions JSON 应包含必要手动命令。
   - Payload panel 不应发送 `42702`。

#### 验收

- `MavCmdInfoRover.json` 的 USV category 不误导用户把手动命令当 mission item。
- `custom/tests/test_usv_qgc_contract.py` 明确覆盖 Plan/Action 分界。
- `docs/current/40_interfaces.md` 如有描述变更，需要同步。

### P0.3 让 `USVActionBar.qml` 与主载荷面板共享门控语义

#### 问题

`USVPayloadPanel.qml` 的门控较完整：

- 点采样要求 `vehicle && _linkOk && spectrometerValid && baselineSet && _canStartPointSample`。
- 设基线要求 `vehicle && _linkOk && spectrometerValid && payloadStatus !== _stFault`。
- 走航要求 `vehicle && _linkOk && spectrometerValid && baselineSet && payloadStatus !== _stFault && payloadStatus !== _stSurveying`。

但 `USVActionBar.qml` 的快捷按钮较宽松：

- “设基线”未检查 `spectrometerValid`。
- “走航”未检查 `baselineSet` 和 `spectrometerValid`。
- 快捷栏无 pending/ACK/timeout 反馈。

#### 要求

1. 给 `USVActionBar.qml` 增加必要 Fact 读取：`linkActive`、`baselineSet`、`spectrometerValid`。
2. 快捷栏按钮门控与 `USVPayloadPanel.qml` 对齐，至少：
   - 设基线：链路正常 + 有有效信号 + 非故障。
   - 点采样：链路正常 + 有效信号 + baseline 已设置 + 状态允许。
   - 走航：链路正常 + 有效信号 + baseline 已设置 + 非故障 + 非走航。
3. 低风险替代方案：如果快捷栏复杂度过高，可只保留“停止检测/停止走航/暂停/恢复”等应急类按钮，把启动类动作放回主面板。
4. 需要测试覆盖快捷栏不再绕过前置条件。

#### 验收

- 同一动作在主面板与快捷栏不会出现“一个可点、一个不可点”的明显矛盾。
- 搜索 `USVActionBar.qml`，可见 `baselineSet`、`spectrometerValid` 或等价门控。
- 测试中断言快捷栏门控不弱于主面板。

## 4. P1：增强可靠性与一致性

### P1.1 建立 QGC 状态码单一真源

建议新增轻量状态码定义，例如：

```text
WQ-USV-QGroundControl/custom/res/USVStatusCodes.js
```

或继续使用 `USVFlyViewLayout.js` 作为单一真源，但要确保所有 QML 都从同一处读取状态常量和文案。

目标：

- 状态码常量不要在多个 QML/JSON 中手写漂移。
- `USVPayloadFactGroup.json` 的枚举、QML 的 `statusText()`、摘要条/详情页/数据页的文案一致。

验收：

- 搜索状态码文案，重复定义显著减少。
- 测试覆盖 `0..14` 主要状态文案。

### P1.2 做跨端字段一致性测试

字段链路跨越 ROS bridge、ArduRover、QGC，很容易漂移。建议添加一个静态测试脚本或扩展现有 `test_usv_qgc_contract.py`，对比这些文件中的字段：

- `src/usv_ros/scripts/usv_mavlink_router_bridge.py`
- `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`
- `ardupilot-usv/Rover/sensors.cpp`
- `ardupilot-usv/Rover/Rover.h`
- `WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`
- `WQ-USV-QGroundControl/custom/res/USVPayloadFactGroup.json`

当前字段基线：

```text
USV_VOLT
USV_ABS
PUMP_X
PUMP_Y
PUMP_Z
PUMP_A
USV_STAT
USV_PKT
USV_STEP
USV_STOT
USV_SCNT
USV_PERR
USV_PMOD
USV_BSET
USV_REF
USV_BASE
USV_VLD
USV_JTMP
USV_ETMP
USV_JCPU
USV_JMEM
USV_EHEAP
```

注意：QGC 的 `linkActive` 是本地派生 Fact，不是 MAVLink 原始字段。

### P1.3 明确 PX4 支持等级

当前 QGC custom 插件代码支持 PX4 Rover 入口，但完整采样闭环依赖 ArduRover 定制固件中的：

- `USV_SMPL`
- `USV_DONE`
- `NAMED_VALUE_FLOAT` 缓存与 2 Hz 转发

因此文档和 UI 中不要写“PX4 完全支持完整采样闭环”。更准确表述：

> QGC UI 层兼容 PX4 Rover，但完整 USV 采样 mission 闭环当前以 ArduRover 定制固件为准。PX4 仅支持基础 Rover/Boat UI 和部分手动/遥测能力，除非实现等价的 mission trigger / done / payload forwarding 机制。

需要检查：

- `WQ-USV-QGroundControl/custom/README.md`
- QGC 设置/固件选择相关文案，如存在。
- `docs/current/20_system_overview.md` 或 `40_interfaces.md` 是否需要补一句边界说明。

## 5. P2：操作体验优化

### P2.1 任务前准备状态卡

可以在主载荷面板或 FlyView 详情里增加“任务前准备”区域，显示：

- 飞控已连接。
- 载荷链路在线。
- 分光信号采集中。
- 当前分光数据有效。
- baseline 已设置。
- 任务已上传。
- 当前模式/任务状态适合执行。

注意：只做展示和门控提示，不要把 Web 数据中心逻辑搬进 QGC。

### P2.2 Plan 中 `MAV_CMD_NAV_SCRIPT_TIME` 的中文提示优化

优化 `MavCmdInfoRover.json` 中 `42702` 的说明，让操作员明白：

- 这个任务项应放在需要采样的航点之后。
- `param1` 固定为 1，表示 USV 定点采样。
- `param2` 是最大等待秒数，飞控会等待 `USV_DONE` 或超时。
- 这不是手动按钮命令。

## 6. 明确禁止事项

实施 agent 不要做以下事情：

1. 不要把 `31010` 加回 Plan mission metadata。
2. 不要让 `USVPayloadPanel.qml` 发送 `42702`。
3. 不要修改 MAVLink 命令号 `31010..31019` 或 component id `191`。
4. 不要在 QGC 实现污染物热力图、浓度算法、GeoJSON/CSV 导出或科研 surface。
5. 不要在 `ardupilot-usv/`、`DetFirmware/` 中加入污染物历史/浓度/热力图逻辑。
6. 不要大规模重构 QGC 原工程；优先在 `custom/` 和必要 metadata 中小步改动。
7. 不要只改 UI 文案不改测试。
8. 不要把状态码 `3` 继续解释为硬件故障。

## 7. 推荐执行顺序

1. 阅读本方案。
2. 阅读：
   - `AGENTS.md`
   - `docs/current/00_index.md`
   - `docs/current/40_interfaces.md`
   - `docs/current/60_source_map.md`
   - `WQ-USV-QGroundControl/custom/AGENTS.md`
3. 处理 P0.1：状态码文案统一。
4. 处理 P0.2：Plan / Action 命令边界收口。
5. 处理 P0.3：快捷栏门控对齐。
6. 更新或新增测试。
7. 如改了接口文档，同步 `docs/current/40_interfaces.md`、`60_source_map.md`、`70_verification.md`。
8. 运行静态验证。
9. 在 `.ai-bridge/agent-status.md` 记录执行结果、触达文件、测试结果和遗留问题。

## 8. 建议验证命令

在 `WQ-USV-QGroundControl/` 下执行：

```bash
python custom/tests/test_usv_qgc_contract.py
```

搜索检查：

```bash
rg -n "载荷故障，请检查采样模块|USV_STAT|31010|31019|42702|MAV_CMD_NAV_SCRIPT_TIME|baselineSet|spectrometerValid" custom src/MissionManager
```

在根仓库或对应目录静态核对：

```bash
rg -n "USV_VOLT|USV_ABS|PUMP_X|PUMP_Y|PUMP_Z|PUMP_A|USV_STAT|USV_PKT|USV_STEP|USV_STOT|USV_SCNT|USV_PERR|USV_PMOD|USV_BSET|USV_REF|USV_BASE|USV_VLD|USV_JTMP|USV_ETMP|USV_JCPU|USV_JMEM|USV_EHEAP" docs/current src/usv_ros/scripts/usv_mavlink_router_bridge.py ardupilot-usv/Rover WQ-USV-QGroundControl/custom
```

若本地 QGC 构建环境可用，再执行项目现有构建/测试流程；否则至少完成上述静态验证并记录限制。

## 9. 完成标准

本方案完成时应满足：

- QGC UI 对 `USV_STAT=3` 的语义统一为任务/采样失败。
- Plan 中 `MAV_CMD_NAV_SCRIPT_TIME` 与手动 `31010..31019` 的边界明确，没有误导性 mission command。
- 快捷栏不会绕过主面板的 baseline / valid signal / link gate。
- QGC 合约测试覆盖核心命令、状态、门控、Plan/Action 边界。
- 文档中不再夸大 PX4 对完整采样闭环的支持范围。
- `.ai-bridge/agent-status.md` 记录执行摘要、测试结果和未解决项。
