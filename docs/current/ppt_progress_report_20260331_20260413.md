# 开发进度汇报PPT文案（2026-03-31 ~ 2026-04-13）
Updated: 2026-04-13T22:06:23+08:00

## 0. 使用说明
- 目标：作为开发进度汇报的逐页讲稿与制稿底稿。
- 时间范围：`2026-03-31 00:00:00` ~ `2026-04-13 23:59:59`
- 数据来源：`src/usv_ros/`、`WQ-USV-QGroundControl/`、`ardupilot-usv/` 三仓库 `git log --author="MIGO_12"`
- 统计口径：仅统计当前时间窗内作者为 `MIGO_12` 的提交；工作区状态均为 clean。

## 1. Slide 1｜标题页
- 标题：USV 三端协同系统两周开发进展汇报
- 副标题：QGroundControl / usv_ros / ArduRover 协同联调与稳定性收口
- 时间：2026-03-31 ~ 2026-04-13
- 汇报人：MIGO_12

## 2. Slide 2｜两周工作总览
- 本周期共提交 `73` 次：ROS `55`、QGC `12`、飞控 `6`
- 累计代码变更：`+8702 / -4571`
- 涉及文件数：ROS `48`、QGC `48`、飞控 `8`
- 重点方向：MAVLink 链路稳定、QGC 载荷交互、飞控中继机制、自动化采样闭环、Web 运维能力补齐
- 产出形态：功能开发、稳定性修复、文档与测试补齐、v0.2.0-stable 三端稳定标签

## 3. Slide 3｜三端工作量分布
- 船载 ROS 端：高频核心文件为 `scripts/usv_mavlink_router_bridge.py`(16)、`scripts/mavlink_trigger_node.py`(14)、`scripts/usv_mavlink_bridge.py`(11)、`scripts/status_usv_all.sh`(10)
- QGC 端：高频核心文件为 `custom/res/USVPayloadPanel.qml`(8)、`custom/res/USVFlyViewCustomLayer.qml`(5)、`custom/src/USVPayloadFactGroup.cc`(5)
- 飞控端：高频核心文件为 `libraries/GCS_MAVLink/MAVLink_routing.cpp`(3)、`Rover/GCS_MAVLink_Rover.cpp`(2)、`Rover/sensors.cpp`(2)
- 结论：本周期是典型的“三端协同修链路 + 前后端补观测 + 固件收口协议”的集中开发窗口

## 4. Slide 4｜阶段性目标与总体成果
- 完成载荷链路从“能通”向“稳定、可诊断、可回滚”的收口
- 建立 `v0.2.0-stable` 三端稳定版本：ROS `63ae83ec`、QGC `af6c56478`、飞控 `56741bb0fa`
- 明确当前主链路：`QGC -> 飞控 -> mavlink-routerd -> ROS` 下行，`ROS -> mavlink-routerd -> 飞控缓存/2Hz重发 -> QGC` 上行
- 形成开发路线图 `docs/current/roadmap.md`，将后续工作拆解为功能编号 #1/#2/#4/#5/#6/#8/#10

## 5. Slide 5｜ROS 端：MAVLink 主链路与桥接稳定性
- 3/31 首次落地 `COMMAND_ACK` 回传、`31014 -> CALXYZA` 标定命令、`USV_PKT` 包计数与链路健康监控
- 4/2~4/7 聚焦 `usv_mavlink_bridge.py`、`named_value_float_probe.py`、`mavlink_topic_tap.py`，建立链路探针、实机串口诊断、QGC 连接修复
- 4/7 新增本地 TCP 接入 `usv_mavlink_router_bridge.py`，开始从 MAVROS topic 模式切换到 router 中继模式
- 4/10~4/12 连续修复桥接线程死锁、诊断解析兼容、MAVROS/bridge 端点隔离、线程安全发送恢复
- 当前结果：MAVROS 使用 `UDP 14550`，bridge 使用 `TCP 5760`，避免参数下载与载荷遥测抢占同一连接

## 6. Slide 6｜ROS 端：自动化采样闭环与运维脚本增强
- `mavlink_trigger_node.py` 完成自动采样状态流转、任务完成恢复、航点到达自动触发、存在任务时自动恢复 AUTO 模式
- `automation_engine.py` 与 `pump_control_node.py` 在 4/13 集中修复 PID 完成判定逻辑
- 关键修复：pending PID 标记提前、PID timeout 触发自动停止、仅以固件 `PID_DONE/PID_TIMEOUT/PID_FAIL` 为自动化判定依据
- `common_env.sh` 增加 PID 所属校验，避免误杀 VSCode/SSH 等非 USV 进程
- `status_usv_all.sh` 增加 MAVROS 参数下载进度检测、bridge 诊断解析、router 存活检查，现场排障效率显著提升

## 7. Slide 7｜ROS 端：Web 能力扩展
- `web_config_server.py`、`store.ts`、`Settings.tsx`、`system-log-viewer.tsx` 完成 #5/#8/#10 三项能力
- 采样数据：新增任务数据保存与 CSV 导出接口
- 数传监控：解析 `RADIO_STATUS`，在 Web 端显示 RSSI、remrssi、noise 等链路指标
- 日志远程查看：新增 `/api/logs/files`、`/api/logs/<filename>`，支持日志读取、下载、告警高亮、自动滚动
- 价值：原本依赖 SSH 的运维动作被前移到 Web 页面，降低现场维护门槛

## 8. Slide 8｜QGC 端：载荷面板从“能显示”到“可操作、可反馈”
- 3/31 完成 `USVPayloadFactGroup`、`USVPayloadPanel.qml`、链路状态 UI、超时检测、包计数显示
- 4/2~4/4 修复自定义插件接入、FactGroup 注册、Vehicle 侧挂载、FlyView 自定义层布局
- 4/8 新增命令 pending 状态，面板可以反映命令发送后等待 ACK 的过程
- 4/11 将 `sendCommand(..., showError=true)` 落地，命令超时或拒绝时可直接 toast 提示，不再静默失败
- 4/13 优化 fault/offline 标签优先级，避免故障态被离线文案覆盖

## 9. Slide 9｜QGC 端：数据可视化与界面整合
- 新增 `USVSamplingChartPanel.qml`，实现电压/吸光度双 Y 轴曲线面板
- 支持 60 秒滚动窗口、2Hz 数据刷新、自动缩放、电压/吸光度统计栏、手动清空
- `USVFlyViewCustomLayer.qml`、`USVPayloadSummaryStrip.qml`、`USVPayloadDetailPanel.qml`、`USVInstrumentPanel.qml` 完成布局重构
- 结果：QGC 不再只是发命令/看数值，而是具备采样趋势观测与任务态可视化能力

## 10. Slide 10｜飞控端：协议收口与带宽控制
- 4/4 `Ver 0.1.0` 在 `Rover/GCS_MAVLink_Rover.cpp`、`Rover/sensors.cpp`、`Rover/Rover.h` 中建立载荷缓存与转发骨架
- 4/5 在 `Rover/GCS_MAVLink_Rover.cpp` 增补自定义命令处理逻辑，与 ROS/QGC 的控制命令形成对应
- 4/6~4/11 聚焦 `libraries/GCS_MAVLink/MAVLink_routing.cpp`：恢复 `NAMED_VALUE_FLOAT` 路由阻断，避免伴随计算机数据被直转发和二次重发导致带宽翻倍
- 当前飞控策略：伴随机发来的 `NAMED_VALUE_FLOAT` 先缓存到 `usv_payload`，再由 `usv_telemetry_send()` 按 `2Hz` 统一重发到 GCS
- 价值：降低 TELEM2 拥塞，保障 `PARAM_VALUE`、`COMMAND_ACK` 等关键消息的可靠到达

## 11. Slide 11｜三端协同的关键技术突破
- 突破 1：从“单通道混跑”改为 `MAVROS=UDP14550`、`bridge=TCP5760` 的物理隔离链路
- 突破 2：从“伴随机直转发”改为“飞控缓存 + 2Hz 中继”的受控遥测模式
- 突破 3：QGC 增强 ACK/超时/故障反馈，操作结果对用户可见
- 突破 4：自动化执行状态统一由固件文本事件驱动，消除 PID 竞态误判
- 突破 5：现场运维从 shell/SSH 排障扩展到 Web 诊断卡片与日志查看

## 12. Slide 12｜本周期难点与解决方式
- 难点 1：点击采样后链路冻结 —— 根因是 bridge 多线程同时写 TCP 连接，改为主循环单线程发送队列
- 难点 2：MAVROS 参数下载失败 —— 根因是与高频载荷遥测抢占同一 endpoint，改为 UDP/TCP 双端点隔离，并在飞控阻断 `NAMED_VALUE_FLOAT` 直转发
- 难点 3：QGC 面板静默失败 —— 根因是 UI 未展示 ACK 拒绝/超时，改为 `showError=true` + pending 状态
- 难点 4：自动化 PID 秒完成或 60 秒超时 —— 根因是本地绝对角度判断与固件累计角度逻辑不一致，改由固件 `PID_DONE` 唯一裁决

## 13. Slide 13｜可量化结果
- 三端形成统一稳定标签 `v0.2.0-stable`
- ROS 端新增/强化运维诊断：bridge 诊断、router 状态、参数下载检查、radio status、系统日志查看
- QGC 端新增：命令 pending、ACK 错误提示、曲线面板、明细/摘要/仪表重构
- 飞控端新增：载荷缓存、2Hz 中继、路由阻断恢复、自定义命令与验证脚本
- 研发流程产出：`overview.md`、`roadmap.md`、`TESTING.md`、稳定版本说明与回滚信息同步完毕

## 14. Slide 14｜源码依据（汇报时可口述）
- 飞控命令与载荷链路依据：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`ardupilot-usv/Rover/sensors.cpp`、`ardupilot-usv/libraries/GCS_MAVLink/MAVLink_routing.cpp`
- ROS 桥接与自动化依据：`src/usv_ros/scripts/usv_mavlink_router_bridge.py`、`mavlink_trigger_node.py`、`pump_control_node.py`、`scripts/lib/automation_engine.py`
- QGC 展示与交互依据：`WQ-USV-QGroundControl/custom/src/USVPayloadFactGroup.cc`、`custom/res/USVPayloadPanel.qml`、`custom/res/USVSamplingChartPanel.qml`
- 说明：本周期所有 MAVLink 行为调整均按“飞控源码定义 -> ROS/QGC 对齐”的方式推进，而非仅凭协议经验试改

## 15. Slide 15｜后续工作建议
- 在实船环境完成 `v0.2.0-stable` 的长时间链路稳定性验证：参数下载、连续遥测、命令往返、自动采样全流程
- 继续推进路线图中的数据历史页、图表增强、航点自动采样闭环、无线链路监控细化
- 对 PID 完成/失败文本再做标准化，减少前后端文案分叉
- 将本周期已收口的链路与诊断能力沉淀为标准联调 checklist

## 16. 备份页｜关键提交参考
- ROS 稳定标签：`63ae83ec26a6d205cf0a5b64175763ade2f720b4`
- QGC 稳定标签：`af6c564786a304fdfcd22e14d2bdc7b12fa5e237`
- 飞控稳定标签：`56741bb0fa0f54d6b96359c09532efe959c64fda`
- 代表性提交：`4508b49b`、`668a30f2`、`63ae83ec`、`cb1520e1`、`19bf47ec`、`594a111a`、`2deb0ea3`、`dc4c848a`、`07118b25`
