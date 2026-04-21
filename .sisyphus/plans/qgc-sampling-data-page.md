# QGC 采样数据独立顶层页面

## TL;DR

> **Quick Summary**: 在 USV 定制 QGC 中新增一个与航行/规划/配置同级的"采样数据"独立顶层页面，包含实时曲线、任务概览、泵组状态、统计分析四大模块。同时扩展 MAVLink 遥测字段并删除飞行视图中的旧迷你图表面板。
> 
> **Deliverables**:
> - QGC 顶层"采样数据"页面（USVSamplingDataView.qml）
> - USVPayloadFactGroup 扩展（新增 stepCurrent/stepTotal/sampleCount/pidError/pidMode 等 Fact）
> - ROS 端 usv_mavlink_router_bridge.py 新增遥测字段上报
> - 删除 USVSamplingChartPanel.qml 及其飞行视图引用
> - USVSelectViewDropdown.qml 新增入口按钮
> 
> **Estimated Effort**: Medium-Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 3 → Task 5 → Task 7 → Task 9 → F1-F4

---

## Context

### Original Request
用户指出 roadmap #6 中的 QGC 采样数据图表页不应是 AnalyzeView 的子页面，而应是一个与航行(Fly)/规划(Plan)/配置(Configure) 同级的独立顶层页面，用于展示更详细的采样数据。

### Interview Summary
**Key Discussions**:
- 页面功能模块: 实时数据曲线 + 采样任务概览 + 泵组状态详情 + 统计分析
- 迷你面板处置: 删除飞行视图中的 USVSamplingChartPanel，所有数据集中到新页面
- 数据来源: 主要来自 MAVLink 遥测（USVPayloadFactGroup），需新增部分字段
- 图表组织: 电压+吸光度用曲线图，泵角度用文字数值展示
- PID 状态: 需要新增 MAVLink 字段支持

**Research Findings**:
- QGC 使用 `mainWindow.showTool(title, source, icon)` 加载顶层工具页面到 toolDrawer
- USVSelectViewDropdown.qml 已是 qrc 覆盖版本，可直接添加按钮
- QML 必须遵循: `import QGroundControl`（不单独 import ScreenTools/Palette），用 ScreenTools 尺寸、QGCPalette 颜色
- QtCharts 已在现有 USVSamplingChartPanel.qml 中使用

### Metis Review
**Identified Gaps** (addressed):
- 任务概览缺少 MAVLink 字段 → 用户确认新增 stepCurrent/stepTotal/sampleCount
- PID 状态无独立字段 → 用户确认新增 pidError/pidMode
- 6 路信号图表过密 → 用户确认电压+吸光度画曲线，泵角度用文字
- 飞控无需参与转发 → 新字段走 companion→router→QGC 直达通路（sysid=1/compid=191）
- 页面空状态处理 → 无载具/无载荷数据时显示占位提示

---

## Work Objectives

### Core Objective
在 QGC USV 定制构建中创建独立的"采样数据"顶层页面，提供实时曲线、任务概览、泵组状态、统计分析四大功能模块，替代飞行视图中的迷你图表面板。

### Concrete Deliverables
- `custom/res/USVSamplingDataView.qml` — 页面主视图
- `custom/res/USVSamplingDataTokens.js` — 页面布局常量
- `custom/src/USVPayloadFactGroup.h/cc` — 扩展 Fact 字段
- `custom/res/USVPayloadFactGroup.json` — 更新 Fact 元数据
- `src/usv_ros/scripts/usv_mavlink_router_bridge.py` — 新增遥测字段
- 修改 `custom/res/USVSelectViewDropdown.qml` — 新增入口按钮
- 修改 `custom/res/USVFlyViewCustomLayer.qml` — 删除迷你面板
- 修改 `custom/CMakeLists.txt` — 注册新 QML 文件

### Definition of Done
- [ ] QGC 视图选择菜单中有"采样数据"按钮，点击可进入全屏页面
- [ ] 页面包含 4 个功能模块且数据来自 USVPayloadFactGroup
- [ ] 飞行视图中不再有 USVSamplingChartPanel
- [ ] `cmake --build build` 零编译错误
- [ ] ROS 端 `python -m py_compile usv_mavlink_router_bridge.py` → rc=0

### Must Have
- 实时电压+吸光度双Y轴滚动曲线（60秒窗口，2Hz）
- 采样任务概览（步骤进度、已采集点数）— 需新增遥测字段
- 泵组角度实时文字展示（pumpX/Y/Z/A）+ 连接状态 + PID 状态
- 统计面板（最大/最小/平均/标准差）
- 无载具/无载荷数据时的占位提示
- 页面入口按钮在视图选择菜单中

### Must NOT Have (Guardrails)
- 不得修改 `src/` 目录下的核心 QGC 代码（MainWindow.qml、QGCCorePlugin 等）
- 不得对接 ROS Web API（仅 MAVLink 通道）
- 不得添加数据导出/CSV/地图集成功能
- 不得修改飞控固件（新字段不经飞控转发）
- 不得硬编码尺寸或颜色（必须用 ScreenTools + QGCPalette）
- 不得使用 `import QGroundControl.ScreenTools` 或 `import QGroundControl.Palette`（用 `import QGroundControl`）
- 不得在一个 ChartView 中放 6 条曲线
- 不得过度工程化统计模块（增量计算，不引入数学库）

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (partial — `tst_USVFlyViewLayoutLogic.qml` 存在)
- **Automated tests**: Tests-after（为新 JS 逻辑模块添加 QML TestCase）
- **Framework**: QML TestCase + py_compile

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **QGC QML/C++**: 使用 `cmake --build build` 编译验证
- **ROS Python**: 使用 `python -m py_compile` 语法检查
- **QML 运行时**: 启动 QGC 检查页面加载（如可用）

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - foundation):
├── Task 1: ROS 端新增遥测字段 [quick]
├── Task 2: USVPayloadFactGroup C++ 扩展 [unspecified-high]
├── Task 3: 页面骨架 + 导航入口 [quick]

Wave 2 (After Wave 1 - page modules):
├── Task 4: 实时曲线模块 (depends: 2, 3) [visual-engineering]
├── Task 5: 采样任务概览模块 (depends: 2, 3) [unspecified-high]
├── Task 6: 泵组状态 + PID 模块 (depends: 2, 3) [unspecified-high]
├── Task 7: 统计分析模块 (depends: 2, 3) [unspecified-high]

Wave 3 (After Wave 2 - cleanup + integration):
├── Task 8: 删除旧迷你面板 (depends: 4-7) [quick]
├── Task 9: 文档同步 + 最终集成 (depends: 8) [quick]

Wave FINAL (After ALL tasks):
├── F1: Plan compliance audit (oracle)
├── F2: Code quality review (unspecified-high)
├── F3: Real manual QA (unspecified-high)
└── F4: Scope fidelity check (deep)
→ Present results → Get explicit user okay
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 5 | 1 |
| 2 | - | 4, 5, 6, 7 | 1 |
| 3 | - | 4, 5, 6, 7 | 1 |
| 4 | 2, 3 | 8 | 2 |
| 5 | 1, 2, 3 | 8 | 2 |
| 6 | 2, 3 | 8 | 2 |
| 7 | 2, 3 | 8 | 2 |
| 8 | 4, 5, 6, 7 | 9 | 3 |
| 9 | 8 | F1-F4 | 3 |

### Agent Dispatch Summary

- **Wave 1**: **3** — T1 → `quick`, T2 → `unspecified-high`, T3 → `quick`
- **Wave 2**: **4** — T4 → `visual-engineering`, T5 → `unspecified-high`, T6 → `unspecified-high`, T7 → `unspecified-high`
- **Wave 3**: **2** — T8 → `quick`, T9 → `quick`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. ROS 端新增遥测字段

  **What to do**:
  - 在 `src/usv_ros/scripts/usv_mavlink_router_bridge.py` 的 `_build_telemetry_queue()` 中新增 NAMED_VALUE_FLOAT 字段:
    - `USV_STEP` — 当前步骤号 (float, 整数编码)
    - `USV_STOT` — 总步骤数 (float)
    - `USV_SCNT` — 已采集样本计数 (float)
    - `USV_PERR` — PID 误差值 (float)
    - `USV_PMOD` — PID 模式 (float, 0=idle, 1=running, 2=done, 3=error)
  - 从对应 ROS topic 订阅数据并填充队列（`/usv/pump_status` 已含部分信息，`/usv/pump_pid_error` 等）
  - key 命名必须 ≤10 字符（NAMED_VALUE_FLOAT 协议限制）
  - 发送频率与现有遥测一致（2Hz）

  **Must NOT do**:
  - 不修改飞控固件代码
  - 不更改现有字段的 key 或语义
  - 不超过 NAMED_VALUE_FLOAT 10字符 key 限制

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Task 5
  - **Blocked By**: None

  **References**:
  - `src/usv_ros/scripts/usv_mavlink_router_bridge.py:115-148` — 现有 _build_telemetry_queue() 模式，遵循相同的 queue.put() 模式
  - `src/usv_ros/scripts/usv_mavlink_router_bridge.py:45-58` — 现有 topic 订阅模式
  - `src/usv_ros/scripts/pump_control_node.py:490-506` — pump_pid_error 发布逻辑
  - `docs/current/INTERFACE.md:38-53` — 现有 ROS topic 清单

  **Acceptance Criteria**:
  - [ ] `python -m py_compile src/usv_ros/scripts/usv_mavlink_router_bridge.py` → rc=0

  **QA Scenarios**:
  ```
  Scenario: Bridge 语法验证
    Tool: Bash
    Steps:
      1. python -m py_compile src/usv_ros/scripts/usv_mavlink_router_bridge.py
    Expected Result: Exit code 0, no output
    Evidence: .sisyphus/evidence/task-1-bridge-compile.txt

  Scenario: Key 长度验证
    Tool: Bash (grep)
    Steps:
      1. grep -oP "USV_\w+" src/usv_ros/scripts/usv_mavlink_router_bridge.py | awk '{if(length($0)>10) print "TOO LONG: "$0}'
    Expected Result: No output (all keys ≤10 chars)
    Evidence: .sisyphus/evidence/task-1-key-length.txt
  ```

  **Commit**: YES
  - Message: `Feat(bridge): add step/sample/pid telemetry fields`
  - Files: `src/usv_ros/scripts/usv_mavlink_router_bridge.py`
  - Pre-commit: `python -m py_compile src/usv_ros/scripts/usv_mavlink_router_bridge.py`

- [ ] 2. USVPayloadFactGroup C++ 扩展

  **What to do**:
  - 在 `custom/src/USVPayloadFactGroup.h` 中新增 Fact 成员变量（值成员模式，不传 this）:
    - `_stepCurrentFact` — 当前步骤号
    - `_stepTotalFact` — 总步骤数
    - `_sampleCountFact` — 已采集样本数
    - `_pidErrorFact` — PID 误差
    - `_pidModeFact` — PID 模式
  - 在 `custom/src/USVPayloadFactGroup.cc` 构造函数中初始化（遵循现有值成员模式）
  - 在 `handleMessage()` 的 NAMED_VALUE_FLOAT 分支中添加 key 匹配和赋值
  - 在 `custom/res/USVPayloadFactGroup.json` 中添加新字段的元数据（shortDescription, units, decimalPlaces）

  **Must NOT do**:
  - 不将 Fact 构造参数传入 `this`（避免 heap 904 断言问题，参见 task.md 2026-04-08 修复记录）
  - 不修改 `src/` 目录下的核心 QGC 代码

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Tasks 4, 5, 6, 7
  - **Blocked By**: None

  **References**:
  - `custom/src/USVPayloadFactGroup.h:12-46` — 现有 Fact 成员声明模式
  - `custom/src/USVPayloadFactGroup.cc:16-26` — 构造函数中值成员初始化（注意不传 this）
  - `custom/src/USVPayloadFactGroup.cc:55-125` — handleMessage() 中 NAMED_VALUE_FLOAT 解析模式
  - `custom/res/USVPayloadFactGroup.json` — 现有 Fact 元数据格式
  - `docs/current/task.md:887-913` — heap 904 修复记录，解释为何不传 this

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] USVPayloadFactGroup.json 包含所有新字段定义

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds with 0 errors
    Evidence: .sisyphus/evidence/task-2-build.txt

  Scenario: JSON 字段完整性
    Tool: Bash (grep)
    Steps:
      1. grep -c "stepCurrent\|stepTotal\|sampleCount\|pidError\|pidMode" custom/res/USVPayloadFactGroup.json
    Expected Result: 5 (all fields present)
    Evidence: .sisyphus/evidence/task-2-json-fields.txt
  ```

  **Commit**: YES
  - Message: `Feat(payload): extend USVPayloadFactGroup with task/pid facts`
  - Files: `custom/src/USVPayloadFactGroup.h`, `custom/src/USVPayloadFactGroup.cc`, `custom/res/USVPayloadFactGroup.json`
  - Pre-commit: `cmake --build build`

- [ ] 3. 页面骨架 + 导航入口

  **What to do**:
  - 创建 `custom/res/USVSamplingDataView.qml`:
    - 根元素 `Rectangle { color: qgcPal.window }`
    - 包含 `signal popout()` 和 `DeadMouseArea { anchors.fill: parent }`
    - 4 个占位 Section（实时曲线、任务概览、泵组状态、统计分析）用 placeholder 文字
    - 布局: 左侧曲线区（占 60% 宽度），右侧 3 个模块纵向排列（占 40%）
    - 空状态处理: 无 vehicle 或无 usvPayload 时显示居中提示 "请连接载具以查看采样数据"
  - 创建 `custom/res/USVSamplingDataTokens.js`: 布局常量（间距、圆角、透明度等）
  - 在 `custom/res/USVSelectViewDropdown.qml` 中 "分析" 按钮后面添加 "采样数据" 按钮:
    ```qml
    SubMenuButton {
        implicitHeight: root._toolButtonHeight
        Layout.fillWidth: true
        text: qsTr(" 采样数据 ")
        imageResource: "/qmlimages/Analyze.svg"  // 暂用分析图标
        onClicked: {
            if (mainWindow.allowViewSwitch()) {
                mainWindow.closeIndicatorDrawer()
                mainWindow.showTool(qsTr("采样数据"), "qrc:/qml/USV/USVSamplingDataView.qml", "/qmlimages/Analyze.svg")
            }
        }
    }
    ```
  - 在 `custom/CMakeLists.txt` 的 QML_FILES 中注册新 QML 文件

  **Must NOT do**:
  - 不修改 MainWindow.qml 或任何 src/ 文件
  - 不实现功能逻辑（仅骨架占位）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Tasks 4, 5, 6, 7
  - **Blocked By**: None

  **References**:
  - `src/AnalyzeView/AnalyzeView.qml:17-33` — 页面根元素模式（Rectangle + popout signal + DeadMouseArea）
  - `custom/res/USVSelectViewDropdown.qml:54-66` — 现有 "分析" 按钮模式（复制并修改）
  - `src/UI/MainWindow.qml:128-134` — showTool() 函数签名
  - `custom/res/USVFlyViewLayout.js` — 现有 token 文件模式
  - `custom/CMakeLists.txt` — QML_FILES 注册位置

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 视图下拉菜单中出现 "采样数据" 按钮
  - [ ] 点击按钮加载页面（显示占位内容）

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds with 0 errors
    Evidence: .sisyphus/evidence/task-3-build.txt

  Scenario: 导航入口存在
    Tool: Bash (grep)
    Steps:
      1. grep "采样数据" custom/res/USVSelectViewDropdown.qml
    Expected Result: At least 1 match containing "采样数据"
    Evidence: .sisyphus/evidence/task-3-nav-entry.txt

  Scenario: QML 文件已注册
    Tool: Bash (grep)
    Steps:
      1. grep "USVSamplingDataView" custom/CMakeLists.txt
    Expected Result: 1 match in QML_FILES
    Evidence: .sisyphus/evidence/task-3-cmake-reg.txt
  ```

  **Commit**: YES
  - Message: `Feat(qgc): add sampling data top-level page scaffold + nav entry`
  - Files: `custom/res/USVSamplingDataView.qml`, `custom/res/USVSamplingDataTokens.js`, `custom/res/USVSelectViewDropdown.qml`, `custom/CMakeLists.txt`
  - Pre-commit: `cmake --build build`

- [ ] 4. 实时曲线模块

  **What to do**:
  - 在 USVSamplingDataView.qml 的左侧区域实现实时电压+吸光度双Y轴滚动曲线:
    - 复用 USVSamplingChartPanel.qml 的图表逻辑（Timer + LineSeries + ValueAxis）
    - X 轴: 时间滚动窗口（60s × 2Hz = 120 点）
    - 左 Y 轴: 电压 (V)，自适应范围 + 15% margin
    - 右 Y 轴: 吸光度 (AU)，自适应范围
    - 曲线颜色: 电压=#3b82f6, 吸光度=#f59e0b（取自 QGCPalette 如有合适色或保持品牌色）
    - ChartView 配置: theme=Dark, antialiasing=true, NoAnimation
    - 图表标题栏含: 点数显示 + 清空按钮 + 暂停/恢复按钮
  - 在图表下方添加当前值实时数字显示

  **Must NOT do**:
  - 不将 6 条信号全部画在图表上（仅 voltage + absorbance）
  - 不硬编码尺寸

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 7)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `custom/res/USVSamplingChartPanel.qml:58-116` — Timer + LineSeries 数据采集模式（完整复用）
  - `custom/res/USVSamplingChartPanel.qml:147-216` — ChartView 配置模式
  - `custom/res/USVPayloadDetailPanel.qml:31-37` — Fact 访问模式（vehicle.getFact）
  - `custom/res/USVFlyViewLayout.js` — 布局 token

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 图表区域占页面左侧约 60% 宽度
  - [ ] 双 Y 轴独立自适应缩放

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-4-build.txt
  ```

  **Commit**: YES (groups with 5, 6, 7)
  - Message: `Feat(qgc): add real-time voltage/absorbance chart module`
  - Files: `custom/res/USVSamplingDataView.qml`
  - Pre-commit: `cmake --build build`

- [ ] 5. 采样任务概览模块

  **What to do**:
  - 在 USVSamplingDataView.qml 右侧上部实现任务概览卡片:
    - 连接状态指示灯（linkActive → 绿/红圆点 + 文字）
    - 当前采样状态文字（从 status Fact 映射: 0=空闲, 1=采样中, 2=检测中, 3=故障, 4=校准）
    - 步骤进度: "步骤 3/8"（stepCurrent / stepTotal Fact）
    - 已采集样本数: sampleCount Fact
    - 包计数: packetCount Fact
    - QML 中追踪采样时长: status 变为 sampling 时记录开始时间，Timer 每秒更新显示

  **Must NOT do**:
  - 不对接 ROS Web API

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 6, 7)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - `custom/src/USVPayloadFactGroup.cc:83-125` — status 值定义和解析
  - `custom/res/USVPayloadPanel.qml:18-80` — 状态显示 + 呼吸灯动画模式
  - `custom/res/USVPayloadDetailPanel.qml` — 卡片布局模式

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 任务概览卡片显示 5 项数据指标

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-5-build.txt
  ```

  **Commit**: YES (groups with 4, 6, 7)
  - Message: `Feat(qgc): add task overview module`
  - Files: `custom/res/USVSamplingDataView.qml`
  - Pre-commit: `cmake --build build`

- [ ] 6. 泵组状态 + PID 模块

  **What to do**:
  - 在 USVSamplingDataView.qml 右侧中部实现泵组状态卡片:
    - 4 路步进泵角度实时数值: pumpX / pumpY / pumpZ / pumpA（单位: °）
    - 每路泵用独立行展示: 标签 + 当前值 + 单位
    - PID 模式指示: pidMode Fact → 文字+颜色（idle=灰, running=蓝, done=绿, error=红）
    - PID 误差值: pidError Fact（保留 3 位小数）
    - 连接状态: linkActive → 绿点/红点

  **Must NOT do**:
  - 不将泵角度画成曲线图

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5, 7)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `custom/res/USVPayloadDetailPanel.qml` — 泵角度显示模式（已有 pumpX/Y/Z/A 展示）
  - `custom/res/USVPayloadPanel.qml:30-60` — 状态颜色映射模式

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 4 路泵角度均有独立行展示

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-6-build.txt
  ```

  **Commit**: YES (groups with 4, 5, 7)
  - Message: `Feat(qgc): add pump status + PID detail module`
  - Files: `custom/res/USVSamplingDataView.qml`
  - Pre-commit: `cmake --build build`

- [ ] 7. 统计分析模块

  **What to do**:
  - 在 USVSamplingDataView.qml 右侧下部实现统计面板:
    - 电压统计: 最小 / 最大 / 平均 / 标准差
    - 吸光度统计: 最小 / 最大 / 平均 / 标准差
    - 统计范围: 自页面打开（或清空）以来的所有数据
    - 增量计算: 维护 sum、sumOfSquares、count、min、max，每次新数据点到来时更新
    - 标准差公式: `sqrt(sumOfSquares/count - (sum/count)^2)`（在线算法，不遍历数组）
    - 显示精度: 电压 5 位有效数字，吸光度 4 位有效数字
    - 清空按钮（与图表清空联动）

  **Must NOT do**:
  - 不引入外部数学库
  - 不使用全数组遍历计算统计量

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5, 6)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 2, 3

  **References**:
  - `custom/res/USVSamplingChartPanel.qml:89-106` — 现有 min/max/avg 计算（需替换为增量算法）
  - `custom/res/USVSamplingChartPanel.qml:218-248` — 统计显示 Repeater 模式

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 统计面板显示 8 项指标（电压 4 + 吸光度 4）

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-7-build.txt
  ```

  **Commit**: YES (groups with 4, 5, 6)
  - Message: `Feat(qgc): add statistics analysis module`
  - Files: `custom/res/USVSamplingDataView.qml`
  - Pre-commit: `cmake --build build`

- [ ] 8. 删除旧迷你面板

  **What to do**:
  - 从 `custom/res/USVFlyViewCustomLayer.qml` 中删除:
    - USVSamplingChartPanel 组件实例及其 toggle 按钮
    - 相关的 property 声明和绑定
  - 从 `custom/CMakeLists.txt` 的 QML_FILES 中移除 `USVSamplingChartPanel.qml`
  - 确认 `custom.qrc` 中无 USVSamplingChartPanel 引用（检查即可，当前应该没有）
  - 保留 `USVSamplingChartPanel.qml` 文件本身（可作为参考，但不再被引用）或直接删除

  **Must NOT do**:
  - 不影响 USVPayloadSummaryStrip 和 USVPayloadDetailPanel 的正常显示
  - 不修改 USVInstrumentPanel

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 4, 5, 6, 7

  **References**:
  - `custom/res/USVFlyViewCustomLayer.qml:145-184` — 要删除的面板实例和 toggle 按钮
  - `custom/CMakeLists.txt` — QML_FILES 列表中的 USVSamplingChartPanel.qml 条目

  **Acceptance Criteria**:
  - [ ] `cmake --build build` 零编译错误
  - [ ] 飞行视图中不再显示迷你图表
  - [ ] `grep -r "USVSamplingChartPanel" custom/res/USVFlyViewCustomLayer.qml` → 无匹配

  **QA Scenarios**:
  ```
  Scenario: QGC 编译成功
    Tool: Bash
    Steps:
      1. cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --parallel 6
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-8-build.txt

  Scenario: 无残留引用
    Tool: Bash (grep)
    Steps:
      1. grep -r "USVSamplingChartPanel" custom/res/USVFlyViewCustomLayer.qml
    Expected Result: No matches (exit code 1)
    Evidence: .sisyphus/evidence/task-8-no-ref.txt
  ```

  **Commit**: YES
  - Message: `Refactor(qgc): remove USVSamplingChartPanel from fly view`
  - Files: `custom/res/USVFlyViewCustomLayer.qml`, `custom/CMakeLists.txt`
  - Pre-commit: `cmake --build build`

- [ ] 9. 文档同步 + 最终集成

  **What to do**:
  - 更新 `docs/current/overview.md`: 在"已实现能力"中新增采样数据页面描述
  - 更新 `docs/current/INTERFACE.md`: 新增 MAVLink 遥测字段（USV_STEP/USV_STOT/USV_SCNT/USV_PERR/USV_PMOD）
  - 更新 `docs/current/TREE.md`: 新增 USVSamplingDataView.qml 和 USVSamplingDataTokens.js
  - 更新 `docs/current/roadmap.md`: 标记 #6 已完成，说明实现方式变更
  - 更新 `custom/README.md`: 新增"采样数据页面"章节

  **Must NOT do**:
  - 不修改功能代码
  - 不虚构未实现的功能描述

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Task 8)
  - **Blocks**: F1-F4
  - **Blocked By**: Task 8

  **References**:
  - `docs/current/overview.md` — 已实现能力章节
  - `docs/current/INTERFACE.md:129-158` — MAVLink 遥测字段章节
  - `docs/current/TREE.md` — 文件树
  - `docs/current/roadmap.md:163-217` — #6 条目
  - `custom/README.md` — 定制内容章节

  **Acceptance Criteria**:
  - [ ] 5 个文档文件已更新
  - [ ] 新遥测字段在 INTERFACE.md 中有记录

  **QA Scenarios**:
  ```
  Scenario: 文档字段覆盖
    Tool: Bash (grep)
    Steps:
      1. grep "USV_STEP\|USV_STOT\|USV_SCNT\|USV_PERR\|USV_PMOD" docs/current/INTERFACE.md
    Expected Result: At least 5 matches
    Evidence: .sisyphus/evidence/task-9-docs.txt
  ```

  **Commit**: YES
  - Message: `Docs: update INTERFACE/overview/TREE/roadmap for sampling data page`
  - Files: `docs/current/overview.md`, `docs/current/INTERFACE.md`, `docs/current/TREE.md`, `docs/current/roadmap.md`, `custom/README.md`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `cmake --build build` for QGC. Run `python -m py_compile` for ROS files. Review all changed files for: hardcoded sizes/colors, wrong imports (`import QGroundControl.ScreenTools`), missing null checks on vehicle/facts, unused imports, console.log in prod.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean build. Launch QGC. Click view dropdown → verify "采样数据" button visible. Click it → verify page loads. Verify 4 modules render. Navigate to fly view → verify no mini chart panel. Navigate back → verify page state preserved.
  Output: `Scenarios [N/N pass] | Integration [N/N] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1. Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | VERDICT`

---

## Commit Strategy

| Commit | Scope | Message | Pre-commit |
|--------|-------|---------|------------|
| 1 | ROS 端 | `Feat(bridge): add step/sample/pid telemetry fields` | `python -m py_compile usv_mavlink_router_bridge.py` |
| 2 | QGC C++ | `Feat(payload): extend USVPayloadFactGroup with task/pid facts` | `cmake --build build` |
| 3 | QGC QML | `Feat(qgc): add sampling data top-level page scaffold + nav entry` | `cmake --build build` |
| 4 | QGC QML | `Feat(qgc): add real-time voltage/absorbance chart module` | `cmake --build build` |
| 5 | QGC QML | `Feat(qgc): add task overview + pump status + statistics modules` | `cmake --build build` |
| 6 | QGC QML | `Refactor(qgc): remove USVSamplingChartPanel from fly view` | `cmake --build build` |
| 7 | docs | `Docs: update INTERFACE/overview/TREE for sampling data page` | - |

> 注意：Commit 1 在 `src/usv_ros` 仓库，Commit 2-6 在 `WQ-USV-QGroundControl` 仓库，Commit 7 在根仓库。遵循就地提交原则。

---

## Success Criteria

### Verification Commands
```bash
# QGC 构建
cmake --build D:\usv_ws\WQ-USV-QGroundControl\build --target QGroundControl  # Expected: BUILD SUCCESSFUL

# ROS Python 语法
python -m py_compile src/usv_ros/scripts/usv_mavlink_router_bridge.py  # Expected: rc=0

# 飞行视图无迷你面板引用
grep -r "USVSamplingChartPanel" WQ-USV-QGroundControl/custom/res/USVFlyViewCustomLayer.qml  # Expected: no matches
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] QGC 构建零错误
- [ ] ROS py_compile 零错误
- [ ] 视图菜单有"采样数据"入口
- [ ] 飞行视图无迷你图表面板
- [ ] 4 个功能模块均渲染
