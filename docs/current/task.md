# 项目任务记录
Updated: 2026-04-13T13:34:06Z

> 说明：本文件为按时间追加的历史记录，旧条目保留原始事实，不代表当前现状；如需获取当前状态，请优先阅�?`overview.md`、`INTERFACE.md`、`agent_context.md` 与本文件最新时间段记录�?
## 2025-02-14T00:00:00Z intake
- codebase-retrieval.hit1=`WQ-USV-QGroundControl/src/Vehicle/Vehicle.cc L10-L83`
- codebase-retrieval.hit2=`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.h L12-L46`
- codebase-retrieval.hit3=`WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml L18-L233`
- root.dir=`WQ-USV-QGroundControl, src/usv_ros, build, devel, docx, reference`
- code-examples.dir=`missing`
- docs.existing=`WQ-USV-QGroundControl/custom/README.md, src/usv_ros/README.md, docx/USV水质监测项目_现状与开发路径计�?md`

## 2025-02-14T00:10:00Z audit.qgc
- evidence=`custom/README.md L1-L219`
- evidence=`custom/src/USVPlugin.cc L62-L130, L180-L340, L353-L407`
- evidence=`custom/src/FirmwarePlugin/USVFirmwarePlugin.cc L20-L103`
- evidence=`custom/src/AutoPilotPlugin/USVAutoPilotPlugin.cc L20-L145`
- evidence=`custom/src/USVPayloadFactGroup.cc L32-L72`
- conclusion=`QGC custom layer 已实现插件注入、QML覆盖、FactGroup注册、UI裁剪、动作文件默认配置`

## 2025-02-14T00:20:00Z audit.ros
- evidence=`src/usv_ros/README.md L50-L223`
- evidence=`src/usv_ros/launch/usv_bringup.launch L18-L99`
- evidence=`src/usv_ros/config/usv_params.yaml L4-L129`
- evidence=`src/usv_ros/scripts/pump_control_node.py L273-L327`
- evidence=`src/usv_ros/scripts/usv_mavlink_bridge.py L50-L214`
- evidence=`src/usv_ros/scripts/mavlink_trigger_node.py L56-L320`
- evidence=`src/usv_ros/scripts/web_config_server.py L380-L620`
- conclusion=`ROS链路已覆盖泵控、分�?JSON 发布、Web、航点触发、配置与任务数据管理`

## 2025-02-14T00:30:00Z findings
- gap1=`未在已读 ROS 代码中发�?NAMED_VALUE_FLOAT 上行发送实现`
- gap2=`mavlink_trigger_node._cmd_cb �?pass，QGC 自定义动作接收链路未完成`
- gap3=`mission_coordinator_node �?mavlink_trigger_node 存在任务流重复`
- gap4=`frontend/store.ts 监听 angles；web_config_server emit pump_angles，事件名可能不一致`

## 2025-02-14T00:40:00Z deliverables
- created=`docs/current/overview.md`
- created=`docs/current/plan.md`
- created=`docs/current/agent_context.md`
- created=`docs/current/INTERFACE.md`
- pending=`docs/current/TREE.md`
- created=`docs/current/qgc_payload_bridge_plan.md`

## 2025-02-14T01:00:00Z plan.qgc_bridge
- target=`QGC按钮触发ROS自动化并回传最小遥测`
- focus.file1=`src/usv_ros/scripts/mavlink_trigger_node.py`
- focus.file2=`src/usv_ros/scripts/usv_mavlink_bridge.py (建议新增)`
- focus.file3=`src/usv_ros/launch/usv_bringup.launch`
- evidence=`USVPayloadPanel.qml L71-L73 sendCommand(1, cmdId, true)`
- evidence=`mavlink_trigger_node.py L108-L115 _cmd_cb is pass`
- evidence=`pump_control_node.py L542-L563 automation services exist`
- evidence=`USVPayloadFactGroup.cc L32-L72 expects NAMED_VALUE_FLOAT`
- output=`docs/current/qgc_payload_bridge_plan.md`

## remeber.plan.4
label=bridge|fact=QGC发送端已存在而ROS接收端未闭环|impact=优先改mavlink_trigger_node而非QGC UI|next=实现真实命令接收

## remeber.plan.5
label=telemetry|fact=QGC FactGroup已支持NAMED_VALUE_FLOAT|impact=应新增ROS到QGC的telemetry bridge|next=先回传状态和电压角度

## remeber.docs.1
label=deliverable|fact=已新增qgc_payload_bridge_plan文档|impact=可直接交给编程agent执行|next=按文档阶段推�?

## 2025-02-14T02:00:00Z implementation.qgc_bridge
- phase_a=`mavlink_trigger_node.py 重写命令接收`
  - changed=`imports: CommandCode->Mavlink, 移除CommandLong/CommandLongRequest`
  - changed=`订阅 /mavros/mavlink/from 替代 /mavros/cmd/command`
  - added=`_mavlink_from_cb(): 过滤 msgid==76 (COMMAND_LONG)`
  - added=`_handle_command_long_payload(): struct 解析 payload64 -> command/param1/param2`
  - changed=`handle_mavlink_command(): 增加 31014 校准占位，增�?bool 返回值`
  - changed=`run(): 重构 trigger_srv 为实例方�?_trigger_srv_cb`
  - diff=`+80/-25`
- phase_b=`新增 usv_mavlink_bridge.py`
  - created=`src/usv_ros/scripts/usv_mavlink_bridge.py`
  - subscribers=`/usv/spectrometer_voltage, /usv/pump_angles, /usv/pump_status, /usv/trigger_status`
  - publishes=`/mavros/mavlink/to (mavros_msgs/Mavlink)`
  - telemetry=`USV_VOLT, PUMP_X, PUMP_Y, PUMP_Z, PUMP_A, USV_STAT @2Hz`
  - compid=`191 (MAV_COMP_ID_ONBOARD_COMPUTER)`
  - lines=`190`
- phase_c=`launch/CMakeLists更新`
  - changed=`usv_bringup.launch: 新增 usv_mavlink_bridge 节点�?enable_mavlink_bridge 开关`
  - changed=`CMakeLists.txt: 注册 usv_mavlink_bridge.py`
  - note=`mission_coordinator_node.py 保留�?CMakeLists �?launch 不启动`
- docs_updated=`INTERFACE.md, TREE.md, task.md`

## remeber.exec.1
label=bridge_down|fact=mavlink_trigger_node 现在通过 /mavros/mavlink/from 接收原始 COMMAND_LONG|impact=QGC 按钮命令可被 Jetson 接收|next=实机验证 QGC->Jetson 链路

## remeber.exec.2
label=bridge_up|fact=usv_mavlink_bridge.py �?2Hz 发�?6 �?NAMED_VALUE_FLOAT|impact=QGC USVPayloadPanel 应能显示实时数据|next=实机验证 QGC 面板刷新

## remeber.exec.3
label=launch|fact=launch 新增 bridge 节点并保�?enable 开关|impact=可独立启�?bridge 而不影响其他节点|next=验证 catkin_make �?roslaunch


## remeber.intake.1
label=scope|fact=主模块为QGC定制端与Jetson ROS端|impact=后续文档需突出双端协同|next=分别梳理入口与接�?
## remeber.intake.2
label=docs|fact=已有三份较完整说明文档|impact=可用现有事实交叉验证代码|next=抽取统一上下文文�?
## remeber.intake.3
label=risk|fact=code-examples目录缺失|impact=无法按样例对齐|next=以仓库README与实现作为唯一依据

## remeber.audit.1
label=qgc|fact=USVPlugin含QML拦截和设置裁剪|impact=后续QGC改动优先从custom目录入手|next=保留覆盖机制说明

## remeber.audit.2
label=ros|fact=web_config_server集成配置/数据/WebSocket|impact=它是船载侧网关入口|next=在接口文档中单列API与事�?
## remeber.audit.3
label=integration|fact=QGC期待MAV_CMD+NAMED_VALUE_FLOAT桥接|impact=跨端闭环问题集中在MAVLink桥|next=在上下文文档中明确这是优先缺�?
## remeber.summary.1
label=summary|fact=项目是QGC+ROS双端USV系统|impact=阅读应始终按双端与链路思维进行|next=新agent先看agent_context

## remeber.summary.2
label=summary|fact=QGC定制代码主要在custom目录|impact=避免直接在上游QGC核心乱改|next=优先检查custom.qrc与USVPlugin

## remeber.summary.3
label=summary|fact=ROS核心调度在pump_control/web_config/mavlink_trigger|impact=排障时优先从这三处看|next=结合launch和yaml参数定位

## remeber.summary.4
label=summary|fact=当前最大缺口是MAVLink桥未闭环|impact=QGC面板可能只有UI没有实时联动|next=后续优先实现命令接收与遥测回�?
## remeber.summary.5
label=summary|fact=已生成集中式上下文文档|impact=后续新对话可减少重复阅读成本|next=补充TREE并持续更�?

## 2025-02-14T03:00:00Z intake.injection_pump
- codebase-retrieval.hit1=`reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L132-L154`
- codebase-retrieval.hit2=`reference/MotorControlApp_Pyside6/lowerDevice/src/main.cpp L341-L356`
- codebase-retrieval.hit3=`src/usv_ros/scripts/pump_control_node.py L48-L66`
- code-examples.dir=`missing`
- reference.scope=`GUI 串口处理 + ESP32 固件协议 + ROS pump_control_node`

## 2025-02-14T03:10:00Z audit.injection_pump_reference
- evidence=`reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L550-L553`
- evidence=`reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L631-L647`
- evidence=`reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L842-L859`
- evidence=`reference/MotorControlApp_Pyside6/lowerDevice/src/main.cpp L311-L328`
- evidence=`reference/MotorControlApp_Pyside6/lowerDevice/src/main.cpp L432-L467`
- conclusion=`参考工程将进样泵作为独立PWM执行器，通过PUMP:*文本协议控制，并在自动化步骤中单独处�?step.pump`

## 2025-02-14T03:20:00Z audit.ros_injection_gap
- evidence=`src/usv_ros/scripts/pump_control_node.py L311-L326`
- evidence=`src/usv_ros/scripts/pump_control_node.py L446-L488`
- evidence=`src/usv_ros/scripts/pump_control_node.py L490-L506`
- gap1=`_on_text_received() 当前仅处�?PID_DONE，未解析 PUMP_OK/PUMP_ERR/PUMP_STATUS`
- gap2=`_step_callback() 当前仅通过 command_generator 处理四路步进泵命令`
- gap3=`当前未见 injection pump 专用 topic/service/status cache`

## 2025-02-14T03:30:00Z docs.injection_pump
- created=`docs/current/injection_pump_reference.md`
- updated=`docs/current/overview.md`
- updated=`docs/current/plan.md`
- updated=`docs/current/task.md`
- updated=`docs/current/INTERFACE.md`
- updated=`docs/current/TREE.md`
- result=`文档已记录参考协议、ROS最小接入点、建议topic/service与自动化步骤格式`

## remeber.intake.4
label=scope|fact=参考工程覆盖GUI与下位机两端进样泵逻辑|impact=ROS分析可直接对照串口协议和步骤字段|next=输出最小接入方�?
## remeber.audit.4
label=protocol|fact=固件已支持PUMP:SET并返回PUMP_STATUS|impact=ROS只需补解析和封装即可|next=建议新增状态topic与service

## remeber.audit.5
label=automation|fact=参考GUI在步骤级单独处理step.pump而非复用角度命令|impact=ROS也应在pump_control_node层做旁路发送|next=不要把进样泵混入PID目标管理

## remeber.docs.2
label=deliverable|fact=已新增injection_pump_reference.md|impact=后续实现可直接按该文档落地|next=编码前先核对web与mavlink是否需要同步扩�?
## remeber.docs.3
label=constraint|fact=本次仅更新文档未修改ROS功能代码|impact=系统暂不具备新进样泵控制入口|next=如需实装应按文档逐步开�?
## remeber.summary.6
label=summary|fact=新增进样泵属于PWM速度执行器而非角度闭环泵|impact=设计时必须与四路步进泵控制链路隔离|next=优先在pump_control_node增加独立状态机

## 2025-02-14T04:00:00Z implementation.injection_pump
- changed=`src/usv_ros/scripts/lib/automation_engine.py`
  - added=`on_step_command hook at L42-L55`
  - changed=`_send_step_command() 支持节点注入步骤级旁路发送`
- changed=`src/usv_ros/scripts/pump_control_node.py`
  - added=`/usv/injection_pump_status publisher`
  - added=`/usv/injection_pump_on /off /get_status services`
  - added=`inject_pump_enabled/speed/last_response/last_error state cache`
  - added=`PUMP_OK/PUMP_ERR/PUMP_STATUS text parser`
  - added=`step.pump manual/auto handling and automation hook`
  - changed=`stop_all_pumps() 同时关闭进样泵`
- changed=`src/usv_ros/scripts/web_config_server.py`
  - added=`订阅 /usv/injection_pump_status`
  - added=`Socket.IO event: injection_pump_status`
- verify=`python -m py_compile src/usv_ros/scripts/pump_control_node.py src/usv_ros/scripts/lib/automation_engine.py src/usv_ros/scripts/web_config_server.py -> rc=0`

## remeber.exec.4
label=hook|fact=AutomationEngine新增on_step_command步骤钩子|impact=进样泵旁路逻辑无需侵入command_generator|next=实机验证自动化步骤同步发�?
## remeber.exec.5
label=state|fact=pump_control_node已发�?usv/injection_pump_status并缓存最近响应|impact=Web和外部节点可直接读取进样泵状态|next=前端补状态展�?
## remeber.exec.6
label=verify|fact=py_compile�?个Python文件返回0|impact=本次改动通过基础语法门|next=进行串口联调与ROS话题验收


## 2025-02-14T05:00:00Z implementation.web_injection_pump_ui
- changed=`src/usv_ros/frontend/src/store.ts`
  - added=`InjectionPumpStatus state + refresh/set/on/off actions`
  - changed=`Socket.IO 监听兼容 angles �?pump_angles`
  - added=`injection_pump_status socket event`
- created=`src/usv_ros/frontend/src/components/injection-pump-card.tsx`
  - added=`进样泵状态卡片、速度输入、开�?刷新按钮、最近响�?错误显示`
- changed=`src/usv_ros/frontend/src/pages/Monitor.tsx`
  - added=`InjectionPumpCard 侧栏布局`
  - added=`页面首次 refreshInjectionPumpStatus()`
- changed=`src/usv_ros/frontend/src/pages/Automation.tsx`
  - added=`Step.pump { enable, speed }`
  - added=`页面�?InjectionPumpCard`
  - added=`步骤编辑区进样泵配置列`
- changed=`src/usv_ros/scripts/web_config_server.py`
  - added=`/api/injection-pump/status|on|off|set`
  - added=`socket connect emit injection_pump_status`
  - fixed=`删除重复 /api/calibration/zero|reset|offsets 路由，仅保留 calibration_manager 版本`
- verify=`diagnostics(web/python)=0`
- verify=`python -m py_compile src/usv_ros/scripts/web_config_server.py src/usv_ros/scripts/pump_control_node.py src/usv_ros/scripts/lib/automation_engine.py -> rc=0`
- note=`未执行环境依赖型前端构建作为最终验收；按用户要求仅做静态收尾`

## remeber.exec.7
label=ui|fact=Monitor与Automation均已接入InjectionPumpCard|impact=Web端已有独立进样泵显示与控制入口|next=实机确认按钮触发链路

## remeber.exec.8
label=api|fact=web_config_server已暴�?api/injection-pump四类接口并透传socket状态|impact=前端无需直接接ROS即可控制进样泵|next=联调响应文案与错误提�?
## remeber.exec.9
label=cleanup|fact=已删除旧zero_offsets版本重复校准路由|impact=Settings页将统一走calibration_manager偏移文件|next=后续如需增强只改保留的单一路由�?
## remeber.docs.4
label=interface|fact=INTERFACE已补充进样泵REST与socket事件清单|impact=后续联调可直接据此核对前后端|next=必要时补充请�?响应样例

## remeber.docs.5
label=plan|fact=plan已切换为代码落地+静态收尾状态|impact=当前阶段目标已从方案分析转为接口收口|next=等待用户选择是否实机联调

## remeber.docs.6
label=constraint|fact=当前环境不作为可靠前端构建验收环境|impact=本轮以diagnostics+py_compile+人工审阅作为收尾标准|next=在目标运行环境再做页面联�?
## 2025-02-14T06:00:00Z docs.readme_refresh
- changed=`src/usv_ros/README.md`
  - refactor=`按GitHub风格重写章节结构(简�?架构/准备/启动/验证/排障)`
  - added=`系统架构分层图与关键数据流`
  - added=`环境准备与硬件启动前检查清单`
  - added=`启动参数覆盖示例与常用验证命令`
  - added=`进样泵服务调用与Web API快速检查`
- created=`src/usv_ros/README.en.md`
  - content=`与中文README同步的英文版本（结构与启动步骤对齐）`
- verify=`diagnostics(markdown)=0`

## remeber.docs.7
label=readme|fact=README已从概述型改为运维可执行手册型结构|impact=新成员可按步骤完成部署与启动|next=如需再补充实机截图可放到docs附件

## remeber.docs.8
label=architecture|fact=文档已更新为QGC/Pixhawk/MAVROS/Jetson/Hardware分层架构|impact=接口边界和链路责任更清晰|next=后续可补充时序图

## remeber.docs.9
label=bilingual|fact=新增README.en.md并与中文版本保持一致章节|impact=支持英文协作与外部交付|next=版本变更时双语同步维�?

## 2026-03-15T00:00:00Z docs.readme_startup_sequence_patch
- changed=`src/usv_ros/README.en.md`
  - added=`Section 5.2 Multi-Terminal Startup Sequence with explicit roscore -> roslaunch order`
  - renumbered=`5.2->5.4 subsection indexes to keep startup flow consistent`
  - evidence=`README.en.md L185-L237`
- confirmed=`src/usv_ros/README.md already contains multi-terminal startup sequence`
  - evidence=`README.md L188-L214`
- verify=`diagnostics(markdown)=0`

## 2026-04-13T12:47:09Z intake.workspace_bootstrap
- codebase-retrieval.hit1=`src/usv_ros/scripts/common_env.sh L4-L18, L59-L69`
- codebase-retrieval.hit2=`src/usv_ros/README.md L128-L130, L215-L257`
- codebase-retrieval.hit3=`docs/current/ardupilot_firmware_guide.md L42-L49`
- codebase-retrieval.hit4=`WQ-USV-QGroundControl/justfile L24-L56`
- code-examples.dir=`missing`
- scope=`根仓库新增 bootstrap 脚本 + .gitignore + docs/current 更新`

## 2026-04-13T12:47:09Z audit.workspace_bootstrap
- evidence=`bootstrap_workspace.sh L1-L127`
- evidence=`.gitignore L1-L14`
- evidence=`src/usv_ros/scripts/start_usv_all.sh L1-L50`
- evidence=`WQ-USV-QGroundControl/Makefile L49-L69`
- evidence=`ardupilot-usv/BUILD.md L30-L33, L82-L89`
- conclusion=`根脚本仅负责 clone/submodule/bootstrap，后续构建命令直接对齐现有 README/Makefile/waf 文档入口`

## 2026-04-13T12:47:09Z implementation.workspace_bootstrap
- changed=`bootstrap_workspace.sh`
  - verified=`参数输入支持 3 个 URL 或环境变量`
  - verified=`clone_repo() 执行 git clone --recursive 与 git -C <dir> submodule update --init --recursive`
  - verified=`print_next_steps 输出 catkin_make / make configure+build / ./waf configure --board Pixhawk6C && ./waf rover`
- created=`.gitignore`
  - entries=`/ardupilot-usv/ /WQ-USV-QGroundControl/ /src/usv_ros/ /build/ /devel/ /log/ /.usv_run/ /ardurover.apj`
- updated=`docs/current/overview.md`
- updated=`docs/current/plan.md`
- updated=`docs/current/INTERFACE.md`
- updated=`docs/current/TREE.md`

## 2026-04-13T12:47:09Z verify.workspace_bootstrap
- command=`bash -n bootstrap_workspace.sh`
- result=`rc=0`
- command=`diagnostics bootstrap_workspace.sh .gitignore docs/current/overview.md docs/current/plan.md docs/current/task.md docs/current/INTERFACE.md docs/current/TREE.md`
- result=`issues=0`
- command=`view bootstrap_workspace.sh`
- result=`根脚本 128 行；usage/clone_repo/print_next_steps 段落齐全`

## remeber.intake.5
label=scope|fact=本次变更位于根仓库入口层而非三端源码内部|impact=不应改动 ardupilot-usv/QGC/usv_ros 业务代码|next=只维护 bootstrap 与 docs

## remeber.intake.6
label=constraint|fact=工作区缺少 code-examples 目录|impact=需要以现有 shell 脚本、README、BUILD.md、Makefile 为唯一依据|next=在 task/plan 中记录来源

## remeber.audit.6
label=ros|fact=src/usv_ros/README.md 已定义 rosdep install + catkin_make|impact=根脚本只需输出后续命令无需重新发明 ROS 构建流程|next=保持 print_next_steps 与 README 对齐

## remeber.audit.7
label=qgc|fact=WQ-USV-QGroundControl/justfile 与 Makefile 已提供 submodules/configure/build|impact=根脚本应复用 make configure/build 作为 QGC 入口|next=文档写明不要在根仓库直接构建 QGC

## remeber.audit.8
label=firmware|fact=docs/current/ardupilot_firmware_guide.md 要求 WSL Ubuntu + ./waf configure --board Pixhawk6C|impact=根脚本只能提示后续命令，不能在 Windows 根仓库直接代替固件构建|next=保持 guide 为固件单一事实源

## remeber.exec.10
label=ignore|fact=.gitignore 已忽略三方源码与工作区产物|impact=总管理仓库可安全只提交 docs 和入口脚本|next=用户初始化 GitHub 仓库后直接提交根目录文件

## remeber.exec.11
label=bootstrap|fact=bootstrap_workspace.sh 允许 URL/REF 组合输入|impact=不同设备可按相同结构快速复原工作区|next=实际填入三个远端仓库地址执行

## remeber.exec.12
label=verify|fact=bash -n 与 diagnostics 均为零错误|impact=脚本和文档达到最小可交付状态|next=如需可再补 PowerShell 版本

## remeber.docs.10
label=overview|fact=overview 已加入根 bootstrap 能力与总管理仓库约束|impact=新成员能先理解根仓库职责边界|next=后续如增加更多入口脚本继续在 overview 收口

## remeber.docs.11
label=interface|fact=INTERFACE 新增总管理仓库入口段|impact=可直接查看 URL/REF 参数与忽略策略|next=如脚本参数扩展需同步此段

## remeber.docs.12
label=tree|fact=TREE 已加入 .gitignore 与 bootstrap_workspace.sh|impact=目录树与当前根仓库状态一致|next=后续新增根文件时同步刷新 TREE

## remeber.summary.7
label=summary|fact=usv_ws 根仓库现在承担文档聚合与外部源码引导入口|impact=三端源码可独立 clone 而不纳入该仓库版本历史|next=用户可将根目录单独 git init 并推送 GitHub

## 2026-04-13T13:01:44Z intake.workspace_bootstrap_windows
- codebase-retrieval.hit1=`bootstrap_workspace.sh L11-L17, L62-L86`
- codebase-retrieval.hit2=`docs/current/INTERFACE.md L4-L11`
- codebase-retrieval.hit3=`src/usv_ros/README.md L128-L130`
- codebase-retrieval.hit4=`WQ-USV-QGroundControl/Makefile L49-L69`
- scope=`新增 bootstrap_workspace.ps1 与根 README.md，并刷新 docs/current`

## 2026-04-13T13:01:44Z audit.workspace_bootstrap_windows
- evidence=`bootstrap_workspace.ps1 L1-L133`
- evidence=`README.md L1-L106`
- evidence=`docs/current/ardupilot_firmware_guide.md L42-L49`
- evidence=`WQ-USV-QGroundControl/justfile L31-L56`
- conclusion=`PowerShell 版保持与 Bash 版同构；README 只聚合现有三端构建入口，不新增虚构流程`

## 2026-04-13T13:01:44Z implementation.workspace_bootstrap_windows
- created=`bootstrap_workspace.ps1`
  - added=`PowerShell param + env 变量输入`
  - added=`Clone-Repo() / Invoke-Git() / Print-NextSteps()`
  - added=`目标目录 ardupilot-usv / WQ-USV-QGroundControl / src/usv_ros`
- created=`README.md`
  - added=`总管理仓库目标`
  - added=`Bash/PowerShell bootstrap 用法`
  - added=`ROS/QGC/ArduPilot 构建入口`
  - added=`Git 管理策略与忽略目录`
- updated=`docs/current/overview.md`
- updated=`docs/current/plan.md`
- updated=`docs/current/INTERFACE.md`
- updated=`docs/current/TREE.md`
- updated=`docs/current/task.md`

## 2026-04-13T13:01:44Z verify.workspace_bootstrap_windows
- command=`diagnostics bootstrap_workspace.ps1 README.md docs/current/overview.md docs/current/plan.md docs/current/task.md docs/current/INTERFACE.md docs/current/TREE.md`
- result=`issues=0`
- command=`view README.md bootstrap_workspace.ps1 docs/current/TREE.md`
- result=`README/PowerShell/tree 三者入口与文件名一致`

## remeber.intake.7
label=scope|fact=用户追加要求 Windows PowerShell 入口与根 README|impact=根仓库现在需要覆盖双入口脚本 + 单一说明文档|next=同步 overview 与 interface

## remeber.audit.9
label=windows|fact=当前工作区已有 PowerShell 终端能力但无现成 bootstrap ps1 示例|impact=实现必须直接对齐 bootstrap_workspace.sh 行为|next=保持 URL/REF 与 clone 逻辑一致

## remeber.audit.10
label=readme|fact=根 README 之前不存在|impact=需要把 clone/bootstrap/build/git 策略集中写入根入口|next=后续所有总仓入口说明优先收敛到 README

## remeber.exec.13
label=powershell|fact=bootstrap_workspace.ps1 已提供 git clone --recursive 与 submodule update 流程|impact=Windows 设备可不依赖 bash 完成工作区拉取|next=如需可再补参数示例仓库地址模板

## remeber.exec.14
label=readme|fact=README 已写明 Bash/PowerShell 两种 bootstrap 与三端构建命令|impact=新设备部署可先看根 README 再进入子仓库|next=如后续增加 docker/worktree 入口需继续补充

## remeber.exec.15
label=verify|fact=本轮以 diagnostics + 文档一致性抽查通过|impact=新增文件已达到可提交状态|next=如需可再加 PSScriptAnalyzer 规则

## remeber.docs.13
label=entry|fact=overview 与 INTERFACE 已新增 README.md 和 bootstrap_workspace.ps1 入口|impact=文档导航从单脚本升级为双脚本 + 根说明|next=根入口变化时同步两份文档

## remeber.docs.14
label=tree|fact=TREE 已纳入 README.md 与 bootstrap_workspace.ps1|impact=目录树反映当前根仓库真实状态|next=后续新增根文件继续刷新 TREE

## remeber.docs.15
label=trace|fact=task.md 已记录 PowerShell 版和根 README 的证据与验证|impact=后续审计可区分 bash 首版与 windows 增补批次|next=如提交 git 时补 commit id

## remeber.summary.8
label=summary|fact=usv_ws 根仓库现已具备 Bash + PowerShell 双 bootstrap 入口和根 README|impact=跨 Windows/WSL/Linux 设备可按统一结构恢复工作区|next=用户可直接提交根仓库并在新设备执行 bootstrap

## 2026-04-13T13:34:06Z intake.workspace_bootstrap_bat_only
- codebase-retrieval.hit1=`bootstrap_workspace.ps1 L1-L138`
- codebase-retrieval.hit2=`README.md L11-L16, L23-L64`
- codebase-retrieval.hit3=`docs/current/INTERFACE.md L4-L13`
- codebase-retrieval.hit4=`docs/current/TREE.md L5-L10`
- scope=`删除 bootstrap_workspace.sh / bootstrap_workspace.ps1，改为唯一 bootstrap_workspace.bat 并写死 GitHub URL`

## 2026-04-13T13:34:06Z implementation.workspace_bootstrap_bat_only
- created=`bootstrap_workspace.bat`
  - fixed_url1=`https://github.com/MIGO-OvO/ardupilot-usv.git`
  - fixed_url2=`https://github.com/MIGO-OvO/WQ-USV-QGroundControl.git`
  - fixed_url3=`https://github.com/MIGO-OvO/usv_ros.git`
- removed=`bootstrap_workspace.sh`
- removed=`bootstrap_workspace.ps1`
- updated=`README.md`
- updated=`docs/current/overview.md`
- updated=`docs/current/plan.md`
- updated=`docs/current/INTERFACE.md`
- updated=`docs/current/TREE.md`
- updated=`docs/current/task.md`

## 2026-04-13T13:34:06Z verify.workspace_bootstrap_bat_only
- command=`diagnostics bootstrap_workspace.bat README.md docs/current/overview.md docs/current/plan.md docs/current/task.md docs/current/INTERFACE.md docs/current/TREE.md`
- result=`issues=0`
- command=`view README.md docs/current/INTERFACE.md docs/current/TREE.md`
- result=`根入口统一为 bootstrap_workspace.bat`

## remeber.intake.8
label=scope|fact=用户要求删除 .sh/.ps1，只保留一个 Windows bat 脚本|impact=根仓库入口必须从多脚本收口到单脚本|next=核对 README/TREE/INTERFACE 无旧引用

## remeber.audit.11
label=url|fact=用户已明确提供 3 个 GitHub 仓库地址|impact=bat 脚本应直接写死 URL，不再保留输入参数|next=README 同步写明内置地址

## remeber.audit.12
label=cleanup|fact=旧 bootstrap_workspace.sh / bootstrap_workspace.ps1 已删除|impact=后续提交时不会再带入多余入口文件|next=检查 git status 中仅保留 bat 与文档变更

## remeber.exec.16
label=bat|fact=bootstrap_workspace.bat 已能按固定 URL 拉取三端仓库并执行 submodule update|impact=Windows 侧用户可直接双击或命令行执行|next=如需可再补 pause 或日志文件输出

## remeber.exec.17
label=docs|fact=README 与 docs/current 已全部切换为 bat 唯一入口|impact=部署说明与实际文件状态一致|next=用户重新提交 git 验证

## remeber.exec.18
label=verify|fact=本轮 diagnostics 为零问题|impact=收口后的根仓库达到可提交状态|next=执行 git add/commit

## remeber.docs.16
label=tree|fact=TREE 顶部根文件列表已去除 sh/ps1，仅保留 README 与 bat|impact=目录树不再误导用户使用旧脚本|next=后续若再加根工具文件需同步 TREE

## remeber.docs.17
label=interface|fact=INTERFACE 入口段已改为 bat + 固定 URL|impact=接口文档已不再暴露旧参数式入口|next=若 URL 变更需同步 README 与 bat

## remeber.docs.18
label=plan|fact=plan 已切换为 bat-only 收口方案|impact=当前有效技术计划与根仓库状态一致|next=如用户再要求包装器只需在此基础增量修改

## remeber.summary.9
label=summary|fact=usv_ws 根仓库现在只保留 README + bootstrap_workspace.bat 作为入口|impact=Windows 部署路径最简，减少多脚本混淆|next=用户重新执行 git commit


## 2026-03-15T00:20:00Z implementation.startup_scripts
- created=`src/usv_ros/scripts/common_env.sh`
  - added=`ROS Noetic + workspace setup loading`
  - added=`roscore presence check for business launch scripts`
  - added=`workspace/package path resolution`
- created=`src/usv_ros/scripts/start_ros_master.sh`
  - added=`single-purpose ROS Master startup entry`
- created=`src/usv_ros/scripts/start_usv_system.sh`
  - added=`full usv_ros launch wrapper`
  - added=`launch argument passthrough`
- created=`src/usv_ros/scripts/start_usv_minimal.sh`
  - added=`pump+web minimal launch wrapper`
  - added=`disable_spectrometer + disable_mavlink nodes via launch args`
- changed=`src/usv_ros/README.md`
  - added=`Section 5.3 startup script usage and chmod examples`
- changed=`src/usv_ros/README.en.md`
  - added=`Section 5.3 startup script usage and chmod examples`
- verify=`diagnostics(shell,markdown)=0`

## remeber.exec.10
label=ops|fact=已新�?个可执行启动入口�?个公共环境脚本|impact=Linux现场可直接用脚本替代手敲命令|next=如需可继续补停止脚本与tmux方案

## remeber.exec.11
label=safety|fact=业务启动脚本在无roscore时会阻止继续启动|impact=减少错误启动顺序导致的故障定位成本|next=现场验证提示文案是否足够明确

## remeber.docs.13
label=readme_ops|fact=README中英文均已补充chmod和脚本调用示例|impact=新用户无需翻代码即可直接使用脚本|next=如有部署规范可再补systemd章节

## 2026-03-15T00:40:00Z implementation.one_click_start_stop
- changed=`src/usv_ros/scripts/common_env.sh`
  - added=`RUN_DIR/LOG_DIR/PID helper functions`
  - added=`background process start + graceful/forced stop helpers`
- created=`src/usv_ros/scripts/start_usv_all.sh`
  - added=`auto-start roscore if missing`
  - added=`background roslaunch for usv_bringup.launch`
  - added=`PID/log output under ~/usv_ws/.usv_run/`
- created=`src/usv_ros/scripts/stop_usv_all.sh`
  - added=`stop usv_system first, then roscore`
- changed=`src/usv_ros/README.md`
  - added=`one-click start/stop usage, log path, PID path`
- changed=`src/usv_ros/README.en.md`
  - added=`one-click start/stop usage, log path, PID path`
- removed=`src/usv_ros/scripts/start_usv_all_with_master.sh`
  - reason=`merged into single start_usv_all.sh entry`
- verify=`diagnostics(shell,markdown)=0`

## remeber.exec.12
label=oneclick|fact=start_usv_all.sh 现在会自动后台拉�?roscore 和完整系统|impact=用户可真正通过单条命令完成启动|next=建议现场验证日志路径与端口状�?
## remeber.exec.13
label=shutdown|fact=stop_usv_all.sh �?PID 顺序关闭业务系统后再关闭 roscore|impact=避免粗暴 pkill 影响其他 ROS 进程|next=如需可补仅停业务不关Master的脚�?
## remeber.docs.14
label=ops_doc|fact=README 双语已从分步脚本说明升级为一键启停说明|impact=更贴近现场交付使用方式|next=如有需要可再补开机自启动章节

## 2026-03-15T01:00:00Z implementation.status_restart_and_docs_cleanup
- created=`src/usv_ros/scripts/status_usv_all.sh`
  - added=`RUNNING/STOPPED/stale pid file status output`
  - added=`log path display for roscore/usv_system`
- created=`src/usv_ros/scripts/restart_usv_all.sh`
  - added=`stop_usv_all.sh -> start_usv_all.sh wrapper`
- changed=`docs/current/overview.md`
  - updated=`current system status, delivered capabilities, runtime constraints, doc map`
- changed=`docs/current/INTERFACE.md`
  - refactor=`script/launch/topic/service/web/mavlink/log structure`
  - updated=`MAVLink bridge, injection pump, socket events, runtime constraints`
- changed=`docs/current/agent_context.md`
  - updated=`current delivered state and reading priority`
- changed=`docs/current/injection_pump_reference.md`
  - updated=`from design suggestion to current implementation record`
- verify=`diagnostics(shell,markdown)=0`

## remeber.exec.14
label=status|fact=status_usv_all.sh 通过 PID 文件输出运行状态与日志路径|impact=现场无需手查 ps 即可判断系统存活|next=可视需要再补端�?ROS topic 健康检�?
## remeber.exec.15
label=restart|fact=restart_usv_all.sh 仅复用现�?stop/start 入口|impact=重启流程一致且维护成本低|next=现场验证异常退出后重启行为

## remeber.docs.15
label=cleanup|fact=docs/current 已按现状文档与历史留档重新分工|impact=后续查阅时能区分当前接口与历史方案|next=如需可再重生�?TREE 时间戳与脚本条目

## 2026-03-15T01:20:00Z docs.testing_and_hotspot_audit
- changed=`src/usv_ros/TESTING.md`
  - refactor=`按系统功能测试链路重写为环境/启动/Web/泵控/进样�?自动�?MAVLink/热点/启停/排障结构`
  - added=`一键脚本、日志路径、通过判据、热点访问测试步骤`
- audited=`src/usv_ros/scripts/web_config_server.py`
  - conclusion=`web节点未实装热点创建逻辑，仅监听0.0.0.0:5000并可被热点网络访问`
  - evidence=`web_config_server.py L19, L598-L606`
- audited=`src/usv_ros/scripts/setup_hotspot.sh`
  - conclusion=`热点创建由独立nmcli脚本负责，默认SSID=USV_Control，默认访问地址=http://10.42.0.1:5000`
  - evidence=`setup_hotspot.sh L12-L18, L40-L65`
- verify=`diagnostics(markdown)=0`

## remeber.audit.6
label=hotspot|fact=热点能力不在web_config_server内部实现而在setup_hotspot.sh|impact=网络接入与Web服务需分开排障|next=如需可后续补systemd管理热点

## remeber.docs.16
label=testing|fact=TESTING已改为覆盖当前主链路的功能测试手册|impact=现场可按文档逐项验收ROS/Web/MAVLink/热点|next=如需可补实船测试记录模板

## remeber.docs.17
label=network|fact=web节点绑定0.0.0.0因此热点建立后可直接通过10.42.0.1访问|impact=热点访问成立前提是独立热点脚本成功执行|next=现场验证wlan0 AP模式兼容�?
## 2026-03-31T00:00:00Z implementation.qgc_comm_hardening
- changed=`src/usv_ros/scripts/mavlink_trigger_node.py`
  - added=`COMMAND_ACK(msgid=77) 回传逻辑`
  - added=`/mavros/mavlink/to publisher`
  - added=`31014 -> CALXYZA\r\n` 校准执行链`
  - added=`MAVROS 连接恢复/断开状态发布`
- changed=`src/usv_ros/scripts/usv_mavlink_bridge.py`
  - added=`/mavros/state 监听`
  - added=`断链时暂停遥测发送`
  - confirmed=`USV_ABS 已纳入上行遥测集合`
  - added=`USV_PKT 遥测包计数`
- changed=`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.h/.cc`
  - added=`linkActive Fact + 5 秒超时检测`
  - added=`packetCount Fact <- USV_PKT`
- changed=`WQ-USV-QGroundControl/custom/res/USVPayloadFactGroup.json`
  - added=`linkActive / packetCount 元数据`
- changed=`WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml`
  - added=`链路超时提示条`
  - noted=`compId=1 为当前兼容策略，191 为后续协议优化项`
- verify=`python -m py_compile src/usv_ros/scripts/mavlink_trigger_node.py src/usv_ros/scripts/usv_mavlink_bridge.py -> rc=0`
- verify=`QGC custom build succeeded locally without static compile errors`
- note=`硬件链路尚未开始实机联调，当前状态以代码与静态构建为准`

## 2026-03-31T00:20:00Z docs.sync_after_qgc_comm_hardening
- changed=`docs/current/overview.md`
  - updated=`系统状态、运行约束、QGC/ROS 双端职责`
- changed=`docs/current/INTERFACE.md`
  - updated=`MAVLink 桥接、QGC Fact、链路超时提示、USV_PKT`
- changed=`docs/current/agent_context.md`
  - updated=`当前实现状态、待注意事项、联调阶段`
- changed=`docs/current/plan.md`
  - updated=`当前计划切换为“实机联调前准备”阶段`
- changed=`docs/current/task.md`
  - added=`本次通信链路增强与文档同步记录`

## remeber.exec.16
label=ack|fact=QGC 触发 31010~31014 �?companion 侧现在会回传 COMMAND_ACK|impact=地面站后续联调时可直接观察命令确认结果|next=实机验证 ACK �?autopilot NAK 的时序表�?
## remeber.exec.17
label=health|fact=ROS/QGC 两端都已具备最小链路健康检测机制|impact=现场断链时不再只看到陈旧数据|next=验证超时提示与恢复时�?
## remeber.exec.18
label=telemetry|fact=USV_ABS �?USV_PKT 已纳入上行遥测集合|impact=QGC 面板与链路观察能力更完整|next=确认现场数值刷新与带宽表现

## remeber.docs.18
label=sync|fact=docs/current 已同步到通信链路增强后的最新实现|impact=后续联调可直接以当前文档为准|next=联调结束后补充实测记�?
## 2026-03-15T01:40:00Z implementation.status_hotspot_and_launch_audit
- changed=`src/usv_ros/scripts/status_usv_all.sh`
  - added=`wlan0/USV_AP/10.42.0.1/5000端口检测`
  - kept=`roscore/usv_system PID与日志路径输出`
- changed=`src/usv_ros/launch/usv_bringup.launch`
  - added=`pump_timeout launch arg -> pump_control_node ~timeout`
  - added=`web_ui launch arg -> web_config_server ~web_ui`
  - added=`trigger_waypoints launch arg -> mavlink_trigger_node ~trigger_waypoints`
- audited=`launch completeness`
  - conclusion=`主链路节点完整；之前缺的是运维可配置参数暴露，不是节点缺失`
  - evidence=`pump_control_node.py L280-L284; web_config_server.py L374-L375,L581-L582; mavlink_trigger_node.py L65-L67`
- changed=`src/usv_ros/README.md`
  - updated=`launch 参数表与覆盖示例`
- changed=`src/usv_ros/README.en.md`
  - updated=`launch args table and override examples`
- changed=`docs/current/INTERFACE.md`
  - updated=`status脚本热点健康输出、launch参数集合`
- verify=`diagnostics(shell,xml,markdown)=0`

## remeber.audit.7
label=launch_nodes|fact=usv_bringup.launch 已包�?pump spectrometer web mavlink_trigger mavlink_bridge 五个主链路节点|impact=当前启动入口在节点层面是完整的|next=只需维护参数暴露与文档一致�?
## remeber.exec.16
label=hotspot_status|fact=status_usv_all.sh 现在会同时输出接口存在�?连接激活状�?IP 分配�?000端口监听|impact=现场可直接判断热点访问链路是�?ready|next=可再按需�?curl 级别探活

## remeber.docs.18
label=launch_args|fact=README/README.en/INTERFACE 已同步补�?pump_timeout web_ui trigger_waypoints|impact=运行说明与代码参数集重新一致|next=后续新增节点参数时继续同步滚动文�?
## 2026-03-15T02:00:00Z implementation.hotspot_open_mode_and_stop_script
- changed=`src/usv_ros/scripts/setup_hotspot.sh`
  - replaced=`nmcli dev wifi hotspot` -> `nmcli connection add/modify/up`
  - added=`802-11-wireless.mode=ap + wifi-sec.key-mgmt='' + ipv4.method=shared`
  - conclusion=`显式创建开放热点，避免默认生成密码`
- created=`src/usv_ros/scripts/stop_hotspot.sh`
  - added=`USV_AP 连接关闭 + wlan0 断开`
- changed=`src/usv_ros/TESTING.md`
  - added=`stop_hotspot.sh 权限、关闭热点步骤、密码提示原因、nmcli 验证命令`
- verify=`diagnostics(shell,markdown)=0`

## remeber.audit.8
label=nmcli|fact=nmcli dev wifi hotspot 在部�?NetworkManager 版本会默认带安全配置|impact=现场会误以为脚本失效或系统要求密码|next=统一改用显式 AP 连接配置

## remeber.exec.17
label=hotspot_stop|fact=stop_hotspot.sh 现在可一键关�?USV_AP 并释�?wlan0|impact=热点测试后可直接回收网络状态|next=如需可继续补 restart_hotspot.sh

## remeber.docs.19
label=testing_hotspot|fact=TESTING 已补充热点创建关闭验证与密码问题说明|impact=现场测试步骤更完整且可复现|next=如需可再同步 README 的热点运维章�?
## 2026-03-15T02:20:00Z implementation.web_runtime_fix_and_hotspot_runtime_alignment
- changed=`src/usv_ros/scripts/web_config_server.py`
  - added=`allow_unsafe_werkzeug=True in socketio.run()`
  - reason=`launch 模式下否则直接触�?Werkzeug 生产模式限制并退出`
- audited=`现场网络与端口状态`
  - evidence=`wlan0=10.42.0.1/24; ss -ltnp | grep 5000 => empty; curl 127.0.0.1:5000 failed before manual start`
  - conclusion=`热点链路正常�?000 不通的根因�?web 进程未保持监听`
- changed=`src/usv_ros/TESTING.md`
  - updated=`热点默认 WPA-PSK 流程、setup_hotspot.sh 参数�?000 不通根因说明`
- changed=`docs/current/plan.md`
  - updated=`目标切换�?web 运行时修�?+ 热点运行方式对齐`
- verify=`diagnostics(python,shell,markdown)=0`

## remeber.audit.9
label=web_runtime|fact=usv_system.log 已明确记�?allow_unsafe_werkzeug 缺失导致 web_config_server 退出|impact=热点再正常也无法访问 10.42.0.1:5000|next=重启 start_usv_all.sh 后复测端口监�?
## remeber.exec.18
label=manual_proof|fact=现场手工运行 web_config_server �?curl 127.0.0.1:5000/api/ui/debug 成功|impact=证明 Web 代码主逻辑可用、问题集中在 launch 启动参数/运行方式|next=验证修复�?launch 也能保持监听

## remeber.docs.20
label=runtime_alignment|fact=TESTING 已从“默认开放热点”修正为“Jetson 当前默认 WPA-PSK 热点”|impact=文档与现场行为一致|next=如稳定后可再�?README 热点运维章节

## 2026-03-15T02:35:00Z implementation.hotspot_restore_previous_wifi
- changed=`src/usv_ros/scripts/setup_hotspot.sh`
  - added=`记录 wlan0 当前活动 WiFi 连接�?-> ~/usv_ws/.usv_run/previous_wifi_connection`
  - added=`热点启动前保�?previous wifi state`
- changed=`src/usv_ros/scripts/stop_hotspot.sh`
  - added=`关闭 USV_AP 后自�?nmcli connection up <previous_wifi>`
  - kept=`热点关闭�?wlan0 断开逻辑`
- changed=`src/usv_ros/TESTING.md`
  - updated=`热点关闭后自动回连说明、状态文件路径、通过判据`
- verify=`diagnostics(shell,markdown)=0`

## remeber.exec.19
label=wifi_restore|fact=stop_hotspot.sh 现在会读�?.usv_run/previous_wifi_connection 自动回连上一�?WiFi|impact=现场热点测试完成后无需再手�?nmcli 恢复上网|next=实机验证热点前后切网流程

## remeber.audit.10
label=runtime_state|fact=common_env.sh 已定�?.usv_run 为运行时目录适合保存上一连接名|impact=状态文件不会污染系�?NetworkManager 配置|next=如需可后续加入热点密�?SSID 状态文�?
## remeber.docs.21
label=testing_restore|fact=TESTING 已补热点关闭后自动回连的验证步骤|impact=测试手册覆盖网络恢复闭环|next=如稳定可同步 README 运维章节

## 2026-03-15T02:50:00Z docs.hardware_runtime_reconfig_plan
- created=`docs/current/hardware_runtime_reconfig_plan.md`
  - added=`方案B目标/边界/文件级改造对�?后端接口/前端UI/兼容性保�?实施顺序/风险/验收标准`
  - scope=`pump serial runtime reconnect + web hardware config ui/api`
- changed=`docs/current/agent_context.md`
  - added=`方案B专项入口与阅读指向`
- changed=`docs/current/plan.md`
  - updated=`当前有效任务切换为方案B实施文档输出`
- verify=`diagnostics(markdown)=0`

## remeber.audit.11
label=hardware_gap|fact=当前仓库虽支�?pump_port 启动参数，但无运行时配置入口|impact=USB 设备变更需�?launch/yaml 不适合现场|next=按方案B�?Web + node 热切换链�?
## remeber.exec.20
label=agent_doc|fact=已将方案B固化�?docs/current/hardware_runtime_reconfig_plan.md|impact=后续 agent 可按文档分阶段实施且避免误改现有功能|next=若用户确认即可按文档开始编�?
## remeber.docs.22
label=compat_plan|fact=方案文档已明确禁止影响自动化 进样�?MAVLink PID 校准 热点脚本链路|impact=后续改动有清晰兼容性红线|next=实施时逐项对照验收

## 2026-03-15T03:00:00Z implementation.hardware_runtime_reconfig
- changed=`src/usv_ros/scripts/web_config_server.py`
  - added=`DEFAULT_CONFIG.hardware �?(pump_serial_port/baudrate/timeout + spectrometer_enabled/ads_address/mux/gain/publish_rate/auto_start)`
  - added=`GET/POST /api/hardware/config`
  - added=`GET /api/hardware/serial-ports (serial.tools.list_ports + /dev/serial/by-id)`
  - added=`POST /api/hardware/test-pump-port`
  - added=`POST /api/hardware/apply (保存 + set_param + 调用 pump_reconnect)`
- changed=`src/usv_ros/scripts/pump_control_node.py`
  - added=`/usv/pump_reconnect Trigger 服务`
  - added=`_reconnect_callback(): disconnect -> 更新属�?-> connect`
- changed=`src/usv_ros/frontend/src/pages/Settings.tsx`
  - added=`硬件连接设置卡片 (串口下拉 + 测试/保存/应用按钮)`
- changed=`docs/current/INTERFACE.md`
  - added=`/usv/pump_reconnect 服务�?/api/hardware/* 路由`
- changed=`src/usv_ros/TESTING.md`
  - added=`§11 硬件连接设置测试`
- verify=`diagnostics(python,typescript,markdown)=0`

## remeber.exec.21
label=hw_api|fact=web_config_server 新增 7 �?/api/hardware/* 路由且不影响现有 /api/config|impact=硬件配置与采样配置完全隔离|next=现场验证串口枚举与硬件配置保存链�?
## remeber.exec.22
label=pump_reconnect|fact=pump_control_node 新增 /usv/pump_reconnect 服务|impact=运行时可切换串口而不重启 roslaunch|next=现场验证切换后角度数据恢�?
## remeber.exec.23
label=spectro_reconfig|fact=pump_control_node 已整�?ADS 分光读取�?JSON 发布|impact=运行时调整分光参数不再依赖独立旧链路|next=现场验证切换后电压与吸光度数据恢�?
## remeber.exec.24
label=frontend_hw|fact=Settings.tsx 新增硬件连接设置卡片含串口下拉与测试/应用按钮|impact=现场人员可通过 Web UI 配置硬件连接|next=现场验证设备列表刷新与保存应用流�?
## remeber.docs.23
label=interface_sync|fact=INTERFACE.md 已补�?pump_reconnect �?/api/hardware/* 路由|impact=接口文档与代码同步|next=如后续增�?Socket.IO 硬件状态推送需再更�?
## 2026-03-17T16:08:13Z intake.hardware_docs_refresh
- codebase-retrieval.hit1=`src/usv_ros/scripts/web_config_server.py L288-L296, L942-L1086`
- codebase-retrieval.hit2=`src/usv_ros/frontend/src/pages/Settings.tsx L22-L40, L59-L129, L286-L375`
- codebase-retrieval.hit3=`src/usv_ros/scripts/pump_control_node.py`
- docs.scope=`docs/current/*.md, src/usv_ros/README.md, src/usv_ros/TESTING.md`
- code-examples.dir=`missing`

## 2026-03-17T16:15:00Z audit.hardware_reconfig
- evidence=`Settings.tsx 已提�?hardware config model �?刷新/测试/保存/应用按钮`
- evidence=`web_config_server.py 已提�?/api/hardware/config /serial-ports /test-pump-port /apply`
- evidence=`pump_control_node.py 已提�?/usv/pump_reconnect 运行时串口重连服务`
- evidence=`README.md �?TESTING.md 已有硬件连接设置章节但未完整记录运行时边界`
- finding=`spectrometer_auto_start �?DEFAULT_CONFIG �?Settings 模型存在`

## 2026-03-17T16:25:00Z docs.hardware_refresh
- updated=`docs/current/overview.md`
- updated=`docs/current/plan.md`
- updated=`docs/current/INTERFACE.md`
- updated=`docs/current/TREE.md`
- pending=`src/usv_ros/README.md`
- pending=`src/usv_ros/TESTING.md`
- focus=`补齐硬件配置链路、运行时服务、已实现边界、回滚命令`

## remeber.intake.5
label=scope|fact=本轮只做代码审阅与文档同步|impact=不得虚构新接口或修改实现逻辑|next=全部内容以已存在代码和文档为�?
## remeber.audit.6
label=hardware_chain|fact=硬件配置链路已经从Settings页闭环到ROS服务|impact=README和INTERFACE应按前端-网关-节点三层描述|next=补到接口与测试章�?
## remeber.audit.7
label=boundary|fact=分光配置当前通过 pump_control_node 参数链路生效，需区分串口重连即时生效与参数刷新生效路径|impact=测试手册必须明确哪些字段属于立即应用、哪些字段属于参数驱动|next=在README TESTING加入注意�?
## 2026-03-17T16:40:00Z docs.readme_testing_hardware_refresh
- updated=`src/usv_ros/README.md`
- updated=`src/usv_ros/TESTING.md`
- changed=`README.md 5.4-5.6, 6.3-6.4, 7.3, 8`
- changed=`TESTING.md 11.1-11.6, 12`
- result=`补齐 Settings 硬件连接设置�?api/hardware/*�?usv/pump_reconnect`

## remeber.exec.10
label=docs_sync|fact=README与TESTING已同步硬件连接配置链路和热切换流程|impact=部署与验收人员可按文档直接执行验证|next=运行markdown diagnostics确认无格式问�?
## remeber.docs.24
label=boundary_sync|fact=README与TESTING已显式标注旧独立分光节点已废弃，分光数据改由 pump_control_node 统一发布 JSON|impact=避免现场将旧分光链路误判为仍需部署|next=若后续代码补齐需同步更新三份文档

## remeber.docs.25
label=tree|fact=TREE.md 已补�?stop_hotspot.sh �?hardware_runtime_reconfig_plan.md|impact=当前滚动文档目录与脚本目录索引更完整|next=后续新增脚本或文档继续按同格式重生成

## remeber.summary.7
label=summary|fact=当前代码已支持Web配置泵控串口并触发运行时重连|impact=系统主要硬件连接改动已形成前后端闭环|next=建议后续做实机串口联调验�?
## remeber.summary.8
label=summary|fact=Settings页、web_config_server、pump_control_node是硬件配置主链路|impact=后续排障优先查看这三处|next=结合README 5.6和TESTING 11节执行排�?

## 2026-03-18T10:00:00Z implementation.automation_injection_pump_fixes
- phase_1=`进样泵字段标准化`
  - changed=`src/usv_ros/scripts/web_config_server.py L313-336`
    - added=`_normalize_sampling_sequence() 补齐 pump.enable/speed/duration_ms`
  - changed=`src/usv_ros/frontend/src/pages/Automation.tsx L17-57`
    - added=`InjectionPumpConfig.duration_ms, normalizeStep(), normalizeSteps()`
  - changed=`src/usv_ros/config/usv_params.yaml L51,59,67`
    - added=`pump: {enable, speed, duration_ms} 到示例步骤`
- phase_2=`串口指令时序`
  - changed=`src/usv_ros/scripts/pump_control_node.py L353-354,778-788`
    - added=`auto_injection_command_delay(150ms) + auto_injection_retry_delay(200ms)`
    - added=`电机指令与进样泵指令间延�?+ 首发失败单次重试`
- phase_3=`步骤执行语义重构`
  - changed=`src/usv_ros/scripts/lib/automation_engine.py L55,267-284,375-394`
    - added=`on_step_wait 钩子, _wait_for_step_execution() 方法`
    - refactor=`执行顺序: send �?wait_for_step �?callback �?interval`
  - changed=`src/usv_ros/scripts/pump_control_node.py L377,790-852`
    - added=`_estimate_motor_step_duration(), _wait_seconds_with_pause(), _wait_for_automation_step()`
    - added=`on_step_wait = _wait_for_automation_step 钩子绑定`
  - changed=`src/usv_ros/frontend/src/pages/Automation.tsx L258`
    - changed=`间隔标签�?间隔 (ms)"改为"步骤完成后等�?(ms)"`
  - changed=`src/usv_ros/frontend/src/pages/Automation.tsx L310-327`
    - added=`进样泵运行时长ms输入�?+ 语义说明文本`
- phase_4=`PID 目标角度修复`
  - changed=`src/usv_ros/scripts/pump_control_node.py L755-774`
    - refactor=`_send_automation_step() 改用 get_expected_angles() 代替 get_pending_targets()`
    - logic=`仅对本步骤启用的非连续电机设�?pid_target_angles`
- phase_5=`状态显示修复`
  - changed=`src/usv_ros/scripts/web_config_server.py L509-536`
    - refactor=`_status_cb() 改为增量�? pump_connected �?connect/disconnect/error 时变更`
    - added=`automation 状态解�? 运行/已完�?已停�?暂停, 同步 mission_status`
  - changed=`src/usv_ros/scripts/lib/automation_engine.py L449`
    - added=`_cleanup() 增加 _update_status("已完�?) 通知`
- verify=`diagnostics(python,typescript)=0`

## remeber.exec.25
label=injection_fix|fact=进样泵自动化5个根因全部修�? 字段缺失/串口时序/执行语义/PID目标/状态显示|impact=自动化进样泵完整可用|next=实机验证全链�?
## remeber.exec.26
label=semantic|fact=步骤执行顺序从send→interval改为send→wait_complete→interval|impact=interval语义正确且进样泵有定时关闭能力|next=验证duration_ms控制效果

## remeber.exec.27
label=status|fact=pump_connected/mission_status不再被无关消息覆盖|impact=前端状态显示准确|next=验证连接后UI状态保�?
## 2026-03-18T10:10:00Z docs.refresh
- updated=`docs/current/overview.md` Updated时间�?已落地能�?运行约束
- updated=`docs/current/plan.md` 覆盖为当前有效修复计�?- updated=`docs/current/INTERFACE.md` Socket.IO事件语义+步骤执行语义+步骤数据结构+PID目标说明
- updated=`docs/current/TREE.md` 重生�?补入store.ts/injection-pump-card.tsx/Monitor.tsx/Automation.tsx
- updated=`docs/current/agent_context.md` 当前实现状�?步骤执行语义+接口摘要
- updated=`docs/current/injection_pump_reference.md` duration_ms+自动关闭+字段标准�?执行流程

## remeber.docs.26
label=docs_sync|fact=docs/current/全部7个文档已按当前代码状态更新|impact=后续agent可直接使用最新文档|next=如有新修改继续滚动更�?
## remeber.docs.27
label=interface|fact=INTERFACE新增§10自动化步骤执行语义和§11运行约束|impact=接口文档覆盖了步骤数据结�?PID目标/串口时序|next=后续如修改执行顺序需同步

## remeber.docs.28
label=tree|fact=TREE补入了store.ts/injection-pump-card.tsx/Monitor.tsx/Automation.tsx|impact=前端关键文件在目录树中可查|next=后续新增文件继续更新

## remeber.summary.9
label=summary|fact=本轮修复5个自动化进样泵缺陷并全面更新7份文档|impact=自动化链路从发送到完成检测到状态同步全部修正|next=实机验证后可考虑提交

## remeber.summary.10
label=summary|fact=步骤执行语义是核心改�? send→wait→interval|impact=interval不再从发送时计时而是从完成后计时|next=验证进样泵duration_ms定时关闭

## 2026-03-31T09:40:00Z qgc.payload_panel_fix
- module=`WQ-USV-QGroundControl/src/FirmwarePlugin`
- changed=`src/FirmwarePlugin/FirmwarePluginManager.h L52-L53`
  - updated=`_findPluginFactory(firmwareClass, vehicleClass=VehicleClassGeneric)`
- changed=`src/FirmwarePlugin/FirmwarePluginManager.cc L50-L79`
  - refactor=`supportedVehicleClasses(firmwareClass) 改为汇总同一 firmwareClass 下全部工厂的 vehicleClass 列表`
- changed=`src/FirmwarePlugin/FirmwarePluginManager.cc L82-L125`
  - refactor=`firmwarePluginForAutopilot() 改为�?firmwareClass+vehicleClass 选择工厂`
  - refactor=`_findPluginFactory() 改为从注册表尾部向前遍历，优先命�?vehicleClass 精确匹配，失败时回退到同 firmwareClass 最后注册工厂`
- changed=`docs/current/overview.md L1-L48`
  - updated=`时间�?当前系统状�?运行约束`
- changed=`docs/current/plan.md L1-L40`
  - updated=`当前有效计划切换�?FirmwarePluginManager 修复与构建阻塞说明`
- changed=`docs/current/INTERFACE.md L1-L165`
  - updated=`QGC 载荷面板命令 compId=191 + FirmwarePluginManager 工厂选择策略`
- verify=`codebase-retrieval hits>=3`
- verify=`diagnostics(src/FirmwarePlugin/FirmwarePluginManager.h/.cc)=0`
- verify=`cmake --build WQ-USV-QGroundControl/build/Desktop_Qt_6_10_1_MSVC2022_64bit-Debug-usv_ws --parallel 6 -> fail(environment)`
- blocker=`MSVC 标准库头缺失: chrono/algorithm`
- evidence=`src/FirmwarePlugin/FirmwarePluginManager.cc L82-L125, custom/res/USVPayloadPanel.qml L28-L33,L79-L80`

## remeber.exec.28
label=factory_select|fact=根因是默认固件工厂先命中导致 USVFirmwarePluginFactory 未被选中|impact=usvPayload FactGroup 未挂�?Vehicle 因而面板无数据|next=在正�?MSVC 环境中重建后做运行验�?
## remeber.exec.29
label=compat|fact=supportedVehicleClasses 已改为聚合同 firmwareClass 全部工厂返回值|impact=避免离线 vehicle type 枚举因自定义工厂覆盖而丢失|next=重建后检查离线载具类型列�?
## remeber.docs.29
label=interface_sync|fact=INTERFACE/overview/plan 已同�?compId=191 与工厂选择策略|impact=文档与当前代码一致|next=运行态验证完成后再补 task 结果

## remeber.summary.11
label=summary|fact=QGC 采样面板无数据与按钮无响应的代码根因已定位并修复�?FirmwarePluginManager 工厂选择逻辑|impact=RoverBoat 连接�?Vehicle 应能挂载 usvPayload FactGroup|next=修复 MSVC 环境后重建并联调

## remeber.summary.12
label=summary|fact=当前阻塞不在逻辑代码而在本机 MSVC 标准�?include 环境|impact=尚不能在此机完成最终运行验证|next=使用 x64 Native Tools �?vcvars64.bat 后重新构�?
## remeber.summary.13
label=summary|fact=文档已同步实际命令发送为 vehicle.sendCommand(191, cmdId, false)|impact=后续联调可直接按 payload companion 组件验证 COMMAND_LONG 下发|next=�?Jetson 侧检�?/mavros/mavlink/from msgid=76


## 2026-04-07T21:00:00Z doc.translate
- action=`Translate ardupilot_firmware_guide.md to Chinese`
- target=`docs/current/ardupilot_firmware_guide.md`
- status=`In Progress`
- remeber.intake.1 `label=scope|fact=translating ardupilot_firmware_guide.md to Chinese|impact=improves readability for Chinese-speaking developers|next=perform translation`
- remeber.intake.2 `label=interface|fact=file has 10 sections covering environment, root cause, solution, code changes, build, SITL, flash, test, troubleshooting, and rollback|impact=ensures comprehensive translation|next=audit technical terms`
- remeber.intake.3 `label=risk|fact=replacing entire file content|impact=possible violation of "update-style only" if misapplied, but necessary for full translation|next=use str-replace-editor`

## 2026-04-08T00:30:00Z qgc.heap904_fix
- module=`WQ-USV-QGroundControl/custom/src`
- codebase-retrieval.hit1=`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc L16-L43`
- codebase-retrieval.hit2=`WQ-USV-QGroundControl/src/FactSystem/FactGroup.cc L34-L37,L122-L134`
- codebase-retrieval.hit3=`WQ-USV-QGroundControl/src/Vehicle/FactGroups/VehicleWindFactGroup.h L21-L42`
- evidence=`USVPayloadFactGroup.cc L16-L26 成员 Fact 构造传�?this，�?VehicleWindFactGroup.h L39-L41 同类 Fact 成员不设�?QObject parent`
- evidence=`FactGroup::~FactGroup() L34-L37 不负�?delete Fact；成�?Fact 若被 QObject parent-child 机制登记，将�?QObject 析构阶段�?delete，与成员对象自动析构叠加形成二次释放/非法堆指针`
- root_cause=`USVPayloadFactGroup 将成员变�?Fact 作为 QObject 子对象注册到自身，关闭程序时 QObjectPrivate::deleteChildren 试图释放非堆对象，触�?UCRT debug_heap.cpp Line 904 _CrtIsValidHeapPointer(block)`
- changed=`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc L16-L26`
  - updated=`9 �?Fact 成员构造移除第 4 个参�?this，改为与 QGC 内建 VehicleWindFactGroup 一致的值成员模式`
- expected_effect=`运行一段时间后退出或直接关闭 QGC 时，不再�?USVPayloadFactGroup 析构路径释放非法堆指针而弹�?904 断言`
- verify=`diagnostics(WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc)=0`
- verify=`剩余运行态验证待本机重建后执行：启动QGC->连接USV->保持接收遥测5min->关闭QGC，观察是否仍触发 debug_heap.cpp:904`

## remeber.intake.30
label=scope|fact=本次问题集中�?QGC custom/src/USVPayloadFactGroup 生命周期|impact=无需修改 ROS �?ArduPilot 链路|next=�?QGC 内建 FactGroup 模式校正对象 ownership

## remeber.audit.30
label=ownership|fact=FactGroup 仅保�?Fact 指针映射而不在析构中 delete 成员|impact=成员 Fact 不应再挂 QObject parent 到自�?FactGroup|next=移除构造参�?this

## remeber.exec.30
label=heap_assert|fact=904 断言对应非法堆指针释放而非普通空指针|impact=高概率是 QObject children 删除了非 new 分配对象|next=对比 VehicleWindFactGroup 等标准实现继续排查同类模�?
## remeber.docs.30
label=doc_sync|fact=plan.md 已补�?qgc heap 904 修复点|impact=后续可直接定位本轮代码变更目的|next=重建通过后补 task 验证结果

## remeber.summary.14
label=summary|fact=QGC 904 报错根因�?USVPayloadFactGroup 把栈�?成员 Fact 错误注册�?QObject 子对象|impact=退出阶段触发非法堆释放断言|next=重建并做退出场景回�?

## 2026-04-08T00:00:00Z docs.current_cleanup
- changed=`docs/current/overview.md`
  - refactor=`移除历史尝试、运行时断言分析、过时链路描述，收口为当前三端结构与 router 主链路`
- changed=`docs/current/INTERFACE.md`
  - refactor=`移除 /mavros/mavlink/to 作为当前主遥测链路的描述`
  - added=`mavlink-routerd 生命周期、router_url�?usv_run/mavlink_router.pid/log`
- changed=`docs/current/ardupilot_firmware_guide.md`
  - corrected=`usv_telemetry_send 调度频率 10Hz -> 2Hz`
  - corrected=`当前 ROS->FCU 主链路改�?usv_mavlink_router_bridge.py + mavlink-routerd`
- changed=`docs/current/plan.md`
  - refactor=`切换为本轮文档整理计划`
- changed=`docs/current/TREE.md`
  - refactor=`仅保留当前有效文档集`
- removed=`docs/current/agent_context.md`
- removed=`docs/current/frontend_audit_report.md`
- removed=`docs/current/hardware_runtime_reconfig_plan.md`
- removed=`docs/current/payload_telemetry_debug_report.md`
- removed=`docs/current/qgc_payload_bridge_plan.md`
- removed=`docs/current/QGC UI/UI/UX Audit report.md`
- removed=`docs/repo_cleanup_handoff.md`
- removed=`docs/test_log.md`
- evidence=`src/usv_ros/scripts/common_env.sh L11-L38`
- evidence=`src/usv_ros/scripts/start_usv_all.sh L40-L50`
- evidence=`src/usv_ros/launch/usv_bringup.launch L34-L47,L98-L104`
- evidence=`src/usv_ros/scripts/usv_mavlink_router_bridge.py L45-L58,L115-L148`
- evidence=`ardupilot-usv/Rover/Rover.cpp L138`
- evidence=`ardupilot-usv/Rover/sensors.cpp L100-L117`
- evidence=`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc L83-L125`
- verify=`diagnostics(docs/scripts/launch)=0`

## remeber.docs.13
label=cleanup|fact=docs/current 已收口为当前有效文档集|impact=后续阅读入口减少并避免历史尝试误导|next=同步更新 README �?TESTING 旧链路描�?
## remeber.docs.14
label=router|fact=当前主链路为 mavlink-routerd + MAVROS + usv_mavlink_router_bridge.py|impact=文档必须避免继续声明 /mavros/mavlink/to 为当前上行主通道|next=检�?README/TESTING 相关段落

## remeber.docs.15
label=frequency|fact=ArduRover usv_telemetry_send 当前调度�?2Hz|impact=旧文档中�?10Hz 说明已过时|next=后续若固件频率调整需同步更新 INTERFACE �?firmware guide

## remeber.summary.1
label=summary|fact=QGC 面板当前已能通过飞控数传看到载荷数据|impact=三端主链路已闭环|next=保持文档与代码一�?
## remeber.summary.2
label=summary|fact=ROS 当前依赖 mavlink-routerd 独占 /dev/ttyTHS1|impact=部署必须保证 router 存在且唯一占串口|next=�?README/TESTING 中强调检查点

## remeber.summary.3
label=summary|fact=载荷遥测发送已�?raw MAVROS topic 改为 pymavlink 连接 router|impact=后续新增遥测字段应修�?usv_mavlink_router_bridge.py 与固件缓存转发代码|next=同步维护字段�?
## remeber.summary.4
label=summary|fact=docs/current 已删除多个历史审�?计划文件|impact=当前文档体系更紧凑|next=如需保留历史，应转移到独�?archive 目录而非 current

## remeber.summary.5
label=summary|fact=INTERFACE �?overview 已更新为当前实现|impact=联调与运维可直接依据 docs/current|next=补齐 README �?TESTING 的剩余过时段�?

## 2026-04-08T01:30:00Z qgc.payload_panel_feedback_fix
- module=\"WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml\"
- changed=\"WQ-USV-QGroundControl/custom/res/USVPayloadPanel.qml L32, L78\"
  - updated=\"_payloadCompId: 240 -> 191 (MAV_COMP_ID_ONBOARD_COMPUTER)\"
  - updated=\"vehicle.sendCommand(_payloadCompId, cmdId, false) -> vehicle.sendCommand(_payloadCompId, cmdId, true)\"
- root_cause=\"QGC 发送 MAVLink command_long 的目标 compId 为 240，而 companion computer 端 (mavlink_trigger_node.py) 监听的是 191，导致指令被过滤。同时，QML 发送指令时 showError 参数为 false，导致 QGC 忽略了所有的指令超时和失败的 ACK，不弹出 UI 反馈。\"
- expected_effect=\"点击面板采样按钮后，若 companion computer 拒绝或超时未响应，QGC 会弹出 toast 报错；若成功接收，companion computer 将正确执行指令。\"
- verify=\"人工核实代码已更新，待真机或重新编译验证 UI toast\"

## 2026-04-08T02:30:00Z web_diagnostics_update_for_router
- module="src/usv_ros/scripts, src/usv_ros/frontend"
- changed="usv_mavlink_router_bridge.py"
  - added="tx_total, tx_named_value, tx_heartbeat, pub_errors, mavros_drops 统计与上报"
- changed="web_config_server.py"
  - added="/api/diagnostics/link 中使用 pgrep 检查 mavlink-routerd 进程状态"
- changed="store.ts"
  - updated="BridgeDiag 接口补充 router_url"
- changed="link-diagnostics-card.tsx"
  - updated="融合 MAVROS 状态与 mavlink-routerd 存活状态来综合显示链路健康颜色与文本"
  - updated="增加 mavlink-routerd 的进程存活显示红绿点"

## remeber.exec.17
label=diagnostics|fact=usv_mavlink_router_bridge.py 现在重新抛出 tx_total 等字段以兼容前端|impact=诊断页面指标恢复更新|next=实机确认各统计值的增长

## remeber.exec.18
label=router_check|fact=web_config_server 使用 pgrep -f mavlink-routerd 来判定 router 是否运行|impact=摆脱了单纯依赖 rosnode 的限制，能真实反映底层 MAVLink 管道状态|next=无

## remeber.docs.16
label=interface|fact=INTERFACE.md 已补齐 diagnostics API 与 mavros_state/bridge_diagnostics Socket.IO 事件|impact=Web 前后端通信说明与当前实现一致|next=如后续新增 router_state 事件需同步更新

## remeber.summary.6
label=summary|fact=Web 诊断链路已从“只看 MAVROS”扩展到“同时看 mavlink-routerd 进程 + bridge diagnostics + MAVROS 状态”|impact=现场排障时可区分 router 掉线与 MAVROS 掉线|next=建议上船联调验证三种状态切换

## 2026-04-08T03:00:00Z ui.monitor_layout_and_chart_scale
- changed="src/usv_ros/frontend/src/pages/Monitor.tsx"
  - updated="右侧列改为单列堆叠，通信链路诊断卡片移动到进样泵控制卡片下方"
  - added="computeAdaptiveDomain()，为分光计电压/吸光度曲线计算动态 Y 轴范围"
  - changed="电压图 domain=[voltageDomain]，吸光度图 domain=[absorbanceDomain]，并增加最小跨度与 padding"
- verify="npm run build -> rc=0"

## remeber.exec.19
label=layout|fact=Monitor 页右侧卡片已改为泵控在上、通信诊断在下|impact=操作控件与诊断信息形成同侧纵向工作流|next=现场确认大屏与窄屏阅读顺序

## remeber.exec.20
label=chart|fact=电压/吸光度图已从 auto domain 改为带最小跨度的自适应比例尺|impact=小幅波动不再贴底，趋势更容易观察|next=用真实低噪声样本验证缩放体感

## 2026-04-13T22:06:23+08:00 report.ppt_progress_collection
- codebase-retrieval.hit1=`docs/current/task.md L1-L10,L731-L735`
- codebase-retrieval.hit2=`docs/current/INTERFACE.md L1-L11`
- codebase-retrieval.hit3=`docs/current/overview.md L1-L79`
- code-examples.dir=`missing`
- git.window=`2026-03-31 00:00:00` ~ `2026-04-13 23:59:59`
- git.author=`MIGO_12`
- repo.status=`src/usv_ros clean; WQ-USV-QGroundControl clean; ardupilot-usv clean`
- stats.ros=`commits=55 insertions=5097 deletions=2128 files=48`
- stats.qgc=`commits=12 insertions=3313 deletions=2308 files=48`
- stats.firmware=`commits=6 insertions=292 deletions=135 files=8`
- hotspots.ros=`scripts/usv_mavlink_router_bridge.py(16); scripts/mavlink_trigger_node.py(14); scripts/usv_mavlink_bridge.py(11); scripts/status_usv_all.sh(10)`
- hotspots.qgc=`custom/res/USVPayloadPanel.qml(8); custom/res/USVFlyViewCustomLayer.qml(5); custom/src/USVPayloadFactGroup.cc(5)`
- hotspots.firmware=`libraries/GCS_MAVLink/MAVLink_routing.cpp(3); Rover/GCS_MAVLink_Rover.cpp(2); Rover/sensors.cpp(2)`
- representative.commits=`4508b49b,668a30f2,63ae83ec,cb1520e1,19bf47ec,594a111a,2deb0ea3,dc4c848a,07118b25`
- changed=`docs/current/ppt_progress_report_20260331_20260413.md`
- changed=`docs/current/plan.md`
- pending=`docs/current/TREE.md update`

## remeber.intake.31
label=scope|fact=用户需要基于过去两周三端 git 记录制作开发汇报文案|impact=输出必须覆盖 ROS/QGC/飞控三端且聚焦本人提交|next=按 author=MIGO_12 汇总并写成逐页讲稿
## remeber.audit.31
label=evidence|fact=三端仓库在统计时工作区均为 clean 且可直接读取 git log|impact=汇报内容可直接建立在提交历史和现有 docs/current 上|next=用提交主题归并为链路稳定/界面交互/飞控收口三类
## remeber.exec.31
label=report_doc|fact=已生成 docs/current/ppt_progress_report_20260331_20260413.md|impact=可直接作为 PPT 制作底稿和汇报讲稿|next=同步 TREE 和 diagnostics
## remeber.docs.31
label=stats|fact=本周期统计结果为 ROS55/QGC12/飞控6 共73提交|impact=汇报可量化展示工作量与三端投入分布|next=在口头汇报时突出稳定标签与链路架构收口
## remeber.summary.15
label=summary|fact=两周核心成果是把三端 MAVLink 载荷链路收口为稳定、可诊断、可回滚的 v0.2.0-stable 基线|impact=后续可在此基线上推进航点采样、数据历史和更多运维能力|next=按新文档制作正式 PPT 页面


## 2026-04-15T00:00:00Z implementation.stage1_auto_sampling_closure
- changed=`src/usv_ros/scripts/mavlink_trigger_node.py`
  - added=`MissionState / WaypointSamplingState 枚举`
  - added=`/usv/mission_status publisher`
  - added=`/mavros/local_position/velocity_local /mavros/imu/data 订阅`
  - added=`稳定判定参数: hold_settle_time / stable_check_timeout / stable_speed_threshold / stable_yaw_rate_threshold`
  - added=`航点去重状态机与 waypoint_states`
  - added=`waypoint_sampling 配置解析: enabled / loop_count / retry_count / hold_before_sampling_s / on_fail`
  - added=`失败策略: HOLD / SKIP / ABORT + retry_count`
  - changed=`_waypoint_cb() 到点后改为状态机驱动的异步采样触发`
  - changed=`_resume_auto_if_mission_exists() 增加 mission_status 阶段发布`
- changed=`src/usv_ros/scripts/web_config_server.py`
  - added=`DEFAULT_CONFIG.waypoint_sampling`
  - added=`ConfigManager._normalize_waypoint_sampling()`
  - changed=`save/load/get/update/reset 均归一化 waypoint_sampling`
  - changed=`POST /api/mission/start 支持 sampling_sequence + waypoint_sampling 覆盖当前配置`
  - changed=`_publish_steps() 透传 waypoint_sampling`
- changed=`src/usv_ros/launch/usv_bringup.launch`
  - added=`hold_settle_time / stable_check_timeout / stable_speed_threshold / stable_yaw_rate_threshold / sampling_retry_count / sampling_on_fail launch args`
  - added=`新参数下发到 mavlink_trigger_node`
- changed=`docs/current/INTERFACE.md`
  - updated=`launch 参数、waypoint_sampling 结构、/usv/mission_status 阶段语义`
- changed=`docs/current/overview.md`
  - updated=`阶段一第一轮闭环增强能力与运行约束`
- verify=`python -m py_compile src/usv_ros/scripts/mavlink_trigger_node.py src/usv_ros/scripts/web_config_server.py -> rc=0`
- verify=`diagnostics(src/usv_ros/scripts/mavlink_trigger_node.py, src/usv_ros/scripts/web_config_server.py, src/usv_ros/launch/usv_bringup.launch, docs/current/INTERFACE.md, docs/current/overview.md)=0`

## remeber.exec.32
label=stage1|fact=阶段一第一轮已在 ROS/Web 落地稳定等待 航点去重 失败策略 航点级配置|impact=自动航点采样闭环从原型升级为可调参数版|next=实船验证状态切换和阈值取值

## remeber.exec.33
label=launch|fact=usv_bringup.launch 已暴露 6 个阶段一新参数|impact=现场可无需改代码直接调节稳定窗口和失败策略|next=README/TESTING 如需可再补参数示例

## remeber.docs.32
label=interface_sync|fact=INTERFACE/overview/task 已同步阶段一新增接口与状态语义|impact=后续联调可直接以 docs/current 为准|next=如继续做 QGC 展示需补 mission_status 到 QGC 映射

## remeber.summary.16
label=summary|fact=当前自动采样链路已具备“到点-HOLD-稳定等待-采样-恢复AUTO/失败处理”的最小闭环|impact=可以进入现场阈值调参与状态观察阶段|next=继续做 README/TESTING 补充或 QGC/Web 可视化增强


## 2026-04-15T01:00:00Z implementation.stage1_bugfix_and_stage2_waypoint_editor
- phase_1=`阶段一自查修复`
  - changed=`src/usv_ros/scripts/mavlink_trigger_node.py`
    - fixed=`删除重复的 _state_cb 定义`
    - fixed=`_handle_completion 加 state_lock CAS 保护防止重复执行`
    - fixed=`run() 中 prev_mode 更新移到 if 外，采样期间模式变化不再被吞`
- phase_2=`阶段二：航点采样配置 API`
  - changed=`src/usv_ros/scripts/web_config_server.py`
    - added=`GET/POST /api/waypoint-sampling`
    - added=`GET/POST/DELETE /api/waypoint-sampling/<seq>`
    - fixed=`_status_cb 不再覆盖 mission_status`
- phase_3=`阶段二：前端航点采样编辑器`
  - created=`src/usv_ros/frontend/src/components/waypoint-sampling-card.tsx`
  - changed=`src/usv_ros/frontend/src/pages/Automation.tsx`
  - changed=`src/usv_ros/frontend/src/pages/Monitor.tsx`
- phase_4=`文档同步`
  - changed=`docs/current/INTERFACE.md`
- verify=`py_compile -> rc=0; diagnostics -> 0`

## remeber.exec.34
label=stage1_fix|fact=删除重复 _state_cb + completion 加锁 + prev_mode 修正|impact=消除竞态和模式吞没|next=实船验证

## remeber.exec.35
label=stage2|fact=新增 5 个 waypoint-sampling API + 前端编辑器|impact=航点级采样参数完整可编辑|next=阶段三 QGC/Web 同步

## remeber.summary.17
label=summary|fact=阶段一修复3缺陷 阶段二落地航点采样 CRUD+编辑器|impact=系统已具备航点级采样配置能力|next=继续完善或进入阶段三


## 2026-04-15T02:00:00Z implementation.stage2_review_and_stage3_sync
- phase_1=`阶段二自查`
  - result=`无严重逻辑 Bug`
  - note=`handleAction start 不携带 waypoint_sampling 为 UX 问题非逻辑 bug，在阶段三修复`
- phase_2=`阶段三：任务配置导入导出 API`
  - changed=`src/usv_ros/scripts/web_config_server.py`
    - added=`GET /api/mission-config/export (JSON 文件下载)`
    - added=`POST /api/mission-config/import (JSON 导入覆盖)`
- phase_3=`阶段三：前端同步增强`
  - changed=`src/usv_ros/frontend/src/pages/Automation.tsx`
    - fixed=`handleAction('start') 启动前自动 fetch waypoint_sampling 并一并下发`
    - added=`导出/导入按钮（调用 /api/mission-config/export|import）`
- phase_4=`文档同步`
  - changed=`docs/current/INTERFACE.md` added mission-config API
  - changed=`docs/current/overview.md` 补阶段二三能力
- verify=`py_compile -> rc=0; diagnostics -> 0`

## remeber.exec.37
label=stage3|fact=新增导入导出 API + 前端启动时自动同步 waypoint_sampling|impact=任务配置可跨设备迁移且启动时保证配置一致性|next=实船验证导入导出与启动流程

## remeber.summary.18
label=summary|fact=阶段一~三已全部落地：ROS 闭环/航点编辑器/配置同步导入导出|impact=系统可进入现场联调阶段|next=可选阶段四 QGC Plan 原生扩展


## 2026-04-25T15:46:29+08:00 implementation.det_firmware_handshake_latency
- codebase-retrieval.hit1=`DetFirmware/src/main.cpp setup/TaskComms/parseCommand`
- codebase-retrieval.hit2=`DetFirmware/src/protocol_packets.h packet headers`
- codebase-retrieval.hit3=`docs/current/TREE.md docs/current/task.md overview.md INTERFACE.md`
- changed=`DetFirmware/src/main.cpp`
  - added=`DET_FIRMWARE_ID/DET_FIRMWARE_VERSION/COMMS_TASK_DELAY_MS`
  - added=`HELLO?/DET? -> sendIdentity() -> DET_ID:USV_DETECTOR,FW=2026.04.25,BAUD=115200`
  - changed=`TaskComms vTaskDelay 10ms -> 1ms`
  - added=`parseCommand() handled flag + CMD_OK/CMD_ERR:UNKNOWN`
- changed=`src/usv_ros/scripts/pump_control_node.py`
  - added=`perform_detector_handshake()`
  - changed=`connect(): open serial -> reset buffers -> HELLO handshake -> start PumpSerialReader`
- changed=`src/usv_ros/scripts/web_config_server.py`
  - changed=`POST /api/hardware/test-pump-port: open serial + HELLO handshake + identity response`
- changed=`docs/current/overview.md, INTERFACE.md, plan.md, TREE.md, det_firmware_guide.md`
- verify=`python -m py_compile src/usv_ros/scripts/pump_control_node.py src/usv_ros/scripts/web_config_server.py -> rc=0`
- verify=`diagnostics(DetFirmware/src/main.cpp, pump_control_node.py, web_config_server.py, docs/current/*.md) -> 0`
- blocker=`pio run -> rc=1; pio command not found on current Windows host`
- pending=`PlatformIO build/flash + real serial HELLO handshake + Web test-pump-port + ROS reconnect`
- commit.ros=`8d2d32e6 Fix: add detector serial handshake`


## remeber.intake.32
label=scope|fact=DetFirmware 是 ESP32 PlatformIO Arduino 固件，入口为 src/main.cpp|impact=修复需同时覆盖固件、ROS 串口节点、Web 串口测试|next=实机烧录后联调

## remeber.audit.32
label=latency|fact=固件原 TaskComms 空闲轮询 10ms 且普通 J/R 命令无确认|impact=命令是否已到达固件不可观测，容易被误判为延迟数秒|next=用 CMD_OK 和串口日志确认接收时刻

## remeber.exec.38
label=handshake|fact=固件/ROS/Web 已统一 HELLO? -> DET_ID:USV_DETECTOR 协议|impact=用户可区分“串口可打开”和“确认为检测装置”|next=Web 设置页选择串口后执行测试

## remeber.docs.33
label=docs_sync|fact=overview/INTERFACE/TREE/guide/plan 已记录 DetFirmware 架构与握手协议|impact=后续开发可按 docs/current 定位固件协议|next=若实机调整版本号或超时需同步文档

## remeber.summary.19
label=summary|fact=本轮修复覆盖指令响应可观测性和串口身份识别|impact=联调时可通过 DET_ID 与 CMD_OK 快速定位错误串口/未接收/命令错误|next=安装 PlatformIO 后执行 pio run 与烧录测试

## 2026-04-25T16:30:00+08:00 implementation.win_app_handshake_sync
- changed=`MotorControlApp_Pyside6/src/config/constants.py`
  - added=`DETECTOR_HANDSHAKE_CMD/DETECTOR_ID_PREFIX/HANDSHAKE_TIMEOUT/HANDSHAKE_PROBE_INTERVAL`
- changed=`MotorControlApp_Pyside6/src/ui/mixins/serial_mixin.py`
  - added=`_perform_handshake() 静态方法`
  - changed=`open_serial(): reset buffer -> handshake -> SerialReader`
- changed=`MotorControlApp_Pyside6/src/core/serial_manager.py`
  - added=`_perform_handshake() 静态方法`
  - changed=`connect_port(): reset buffer -> handshake -> SerialReader`
- changed=`docs/current/overview.md, INTERFACE.md, TREE.md, det_firmware_guide.md, task.md`
- verify=`python -m py_compile constants.py serial_manager.py serial_mixin.py -> rc=0`
- verify=`diagnostics -> 0`

## remeber.exec.39
label=win_handshake|fact=Windows 上位机两条串口路径均已加入 HELLO 握手|impact=打开非检测装置串口时弹出明确错误|next=实机联调验证

## remeber.summary.20
label=summary|fact=检测装置握手协议已覆盖四端：固件/ROS/Web/Windows 上位机|impact=所有上位机端点打开串口前均可识别设备身份|next=烧录固件后逐端测试

