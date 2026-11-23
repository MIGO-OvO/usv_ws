# 开发需求与状态

Updated: 2026-10-19

保留 2026-10-19 的需求与状态。现场待验项见[当前验证矩阵](../current/70_verification.md#待现场验收)。下文保留当时的文件路径和任务状态。

## 已完成

| 模块 | 状态 | 依据 |
|---|---|---|
| ROS 主启动链路 | 已完成 | `src/usv_ros/launch/usv_bringup.launch` |
| MAVLink router bridge | 已完成 | `src/usv_ros/scripts/usv_mavlink_router_bridge.py` |
| MAVLink 指令节点 | 已完成 | `src/usv_ros/scripts/mavlink_trigger_node.py` |
| 26 字段载荷遥测与独立年龄 | 源码完成，待现场验收 | `usv_mavlink_router_bridge.py`、`ardupilot-usv/Rover/USVPayload.h` |
| Jetson/ROS/ESP32 健康监测 | 已完成 | `system_health_node.py`、`pump_control_node.py`、Web 监控页 |
| 固件侧字段缓存与 2 Hz 转发 | 已完成 | `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`、`Rover/sensors.cpp` |
| 航点驻留与 31021 采样闭环 | 源码完成，待实船验收 | `ardupilot-usv/Rover/usv_sampling.cpp`、`usv_mavlink_router_bridge.py` |
| Web 控制台与 API | 已完成 | `src/usv_ros/scripts/web_config_server.py`、`src/usv_ros/frontend/` |
| 检测装置串口握手 | 已完成 | `src/usv_ros/scripts/pump_control_node.py` |
| 系统启动脚本与 `usvctl` | 已完成 | `src/usv_ros/scripts/*.sh` |

## 进行中

### safety1 安全收口

飞控采样超时或失联切到 HOLD。设备 3 秒心跳超时停机锁存，ROS 保留本地采样 owner 续约、原子步骤启动和测量过期判定。

现场验收覆盖 LOITER 驻留误差、实际 HOLD 与执行器停止时间、无线丢包、飞控重启和设备故障注入。台架完成后以各仓库提交和产物哈希锁定整船发布清单。

| 方向 | 当前目标 | 验证入口 |
|---|---|---|
| 实船联调 | 验证电台、router、MAVROS、QGC 面板全链路 | `70_verification.md` |
| 采样可靠性 | 验证航点等待、稳定判定、失败策略 | `mavlink_trigger_node.py` |
| 检测装置长期运行 | 验证串口重连、分光数据有效位、泵控反馈 | `pump_control_node.py` |
| QGC 展示一致性 | 核对 26 字段、关联事件、状态码、component id | `WQ-USV-QGroundControl/custom/` |

## 待办

| 优先级 | 项 | 说明 |
|---|---|---|
| P0 | 现场链路验证记录 | 形成一份真实设备验证表，覆盖 QGC 命令、ROS 响应、固件 ACK、遥测显示 |
| P0 | `USV_STAT` 状态码现场验收 | 源码与 QGC 契约回归已覆盖统一映射；实际链路展示仍需验收 |
| P1 | Web API 自动化检查 | 对关键 GET/POST 做离线冒烟脚本，不依赖真实硬件时使用 mock |
| P1 | 检测装置固件构建记录 | 固化 PlatformIO/Arduino 构建与刷写命令 |
| P1 | Windows 上位机与 ROS 协议联合验收 | safety1 已补黄金帧跨端回归、WATCHDOG1/测试位约束；继续补全命令及台架证据 |
| P2 | 日志保留策略 | 统一 `.usv_run/logs`、Web 日志 API、现场导出格式 |

## 不做范围

- 不在根仓库修改业务源码。
- 不整理 `docs/CGEDC/`。
- 不把历史计划继续放入 `docs/current/`。
- 不记录任何带凭证的 remote URL。

## 变更准入

MAVLink、串口协议、Web API 变更必须同步更新：

1. `40_interfaces.md`
2. `60_source_map.md` 对应源码位置
3. `70_verification.md` 对应验证项
4. 子仓库 README 或局部文档（若接口已公开）
