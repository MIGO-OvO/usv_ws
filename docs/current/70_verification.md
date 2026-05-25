# 验证矩阵

Updated: 2026-05-25

## 静态验证

| 项 | 命令/方法 | 通过标准 |
|---|---|---|
| current 文件集 | `Get-ChildItem docs/current` | 仅编号当前文档 |
| 归档存在 | `Test-Path docs/archive/2026-05-20-current-pre-restructure` | 返回 true |
| 本地路径引用 | 手动/脚本检查反引号路径 | 根仓库内路径存在；外部子仓库路径明确 |
| 旧入口污染 | 搜索旧入口名、旧字段数、旧频率说法 | current 不出现过时说法 |
| MAVLink 字段 | 对照 `GCS_MAVLink_Rover.cpp`、`sensors.cpp`、`Rover.h` | 17 字段名称一致 |
| Mission 采样指令 | 对照 `mode_auto.cpp`、QGC `MavCmdInfoRover.json` | 航线定点采样为 `MAV_CMD_NAV_SCRIPT_TIME`，不使用 mission `31010` |
| COMMAND_LONG | 对照 `mavlink_trigger_node.py`、`usv_mavlink_router_bridge.py` | 手动 `31010..31019` 一致 |
| 串口握手 | 对照 `pump_control_node.py`、`DetFirmware/src/main.cpp` | `HELLO?` / `DET_ID` 一致 |

## ROS 离线验证

| 项 | 命令 | 通过标准 |
|---|---|---|
| Python 语法 | `python3 -m py_compile src/usv_ros/scripts/*.py` | 无语法错误 |
| Launch 参数 | `roslaunch usv_ros usv_bringup.launch --dump-params` | 参数可展开 |
| 单元测试 | `python3 -m unittest discover -s src/usv_ros/tests -p 'test_*.py'` | 全部通过 |
| 前端构建 | `cd src/usv_ros/frontend && npm run build` | 构建成功；产物写入 `static/dist` |

## MAVLink 联调

| 场景 | 步骤 | 通过标准 |
|---|---|---|
| router 启动 | `usvon` 后 `usvstatus` | router pid 存在，TCP 5760 可用 |
| MAVROS 连接 | `rostopic echo -n 1 /mavros/state` | `connected: True` |
| QGC 手动命令 | QGC 发送 `COMMAND_LONG 31010` | `/usv/mavlink_cmd_rx` 收到，trigger 发布状态，ACK 返回 |
| 校准命令 | QGC 发送 `31014` | `/usv/pump_command` 出现 `CALXYZA` |
| 遥测字段 | 运行 bridge | QGC 显示 17 字段；固件 2 Hz 转发 |
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
| 基线 | Web 或 MAVLink `31017` | `USV_BSET=1`，`USV_BASE` 更新 |
| 自动化 | 启动采样序列 | step/total/sample_count 递增 |

## 现场验证记录模板

| 时间 | 固件 commit | ROS commit | QGC commit | 场景 | 结果 | 备注 |
|---|---|---|---|---|---|---|
|  |  |  |  | QGC 31010 定点采样 |  |  |
|  |  |  |  | NAV_SCRIPT_TIME 闭环 |  |  |
|  |  |  |  | 走航采样 |  |  |
|  |  |  |  | 分光基线 |  |  |
|  |  |  |  | 电台链路 |  |  |
