# 整船 safety1 修复与验证报告

日期：2026-09-17。AI 辅助实现；未 commit/push、未刷写设备、未启动真实执行器。
这是软件候选，不是已完成现场验收的整船发布。

## 范围与已执行修改

- ArduRover：USV 采样脚本超时/伴随链路失联默认 HOLD；增加匹配 ID 的双向 `USV_FAIL`；限制控制/载荷来源，拒绝非法 ID 和非有限值；保持非 USV Lua 脚本原有行为。
- ROS：原子步骤装载启动；一次性配置与 attempt_id；owner 心跳、故障锁存；停止/重连取消当前自动化；阻止旧话题/服务绕过；模式请求等待实际状态确认；单线程 MAVLink 发送与安全结果优先发送。
- 数据链路：分光错误/静默及时置无效；健康指标过期回未知；上下文在生命周期同一发布流传递；任务窗口保存真实来源、飞控 ID、attempt_id；禁止固件 FULL 压测数据进入真实记录。
- DetFirmware：`WATCHDOG1` 会话、500 ms 主机心跳约定、3000 ms 超时停机锁存、`STOPALL`；测试帧独立状态位；固定平台与 TMCStepper 版本。
- Windows：两套串口入口均要求安全能力、续约与关闭前停机；退出会话停止自动化/优化器；收到 watchdog 错误关闭会话；分光测试位在解析/分析中排除。
- ROS/Windows 共同修复 `0x55` 恰好位于读取块尾部时被误当文本丢弃的问题，补同一黄金字节流跨端比较。
- QGC：更新 Plan 超时语义说明，链路超时清除分光有效位；22 个显示遥测字段与 31010..31019 手动命令保持不变。
- Web：远程默认只读；API 写操作需要部署配置的令牌；跨站/跨源控制拒绝；重复/并发启动不会抢占旧 owner，停止不被启动锁阻塞。
- 总仓库：只读协议检查、五端候选快照、发布门槛工具及当前接口/运行/验收文档。

## 实际验证

| 验证 | 结果 | 边界 |
|---|---|---|
| ROS 全量 unittest | 446 项：443 通过、2 个已存在失败、1 跳过 | Windows Python 3.14，ROS/MAVLink 主要为模拟传输 |
| 新 ROS 系统安全回归 | 20 通过 | 覆盖停止、锁存、步骤事务、owner、模式确认、过期、来源及 FAIL 发送 |
| 新采样上下文回归 | 5 通过 | 包括 Web 急停、重复启动保留 owner、真实/测试数据隔离 |
| Web 写访问回归 | 3 通过 | 本机跨站、远程无令牌、正确令牌 |
| ROS/Windows 黄金串口流 | 1 通过 | 真实两端解析器，混合文本、分片、错误校验和及测试状态位；无串口设备 |
| QGC 契约 | 21 通过 | 源码/元数据检查，不是 Qt 应用完整构建 |
| Windows 全套测试 | 46 通过、1 跳过 | Qt offscreen；11 条旧测试返回非 None 的 pytest 告警仍存在 |
| DetFirmware 源码/宿主入口 | Windows 18 通过、1 跳过 | native g++ 测试在 WSL 另跑通过；源码检查不代替固件运行 |
| ESP32 主机看门狗 C++ | WSL 1 通过 | 真实头文件，deadline、锁存、无心跳解锁、计时器回绕 |
| ESP32 PlatformIO | `nodemcu-32s` 编译成功 | RAM 24676/327680，Flash 331401/1310720；未烧录 |
| ArduRover verifier C++ | WSL 1 通过 | 编译实际 verifier 函数体，含超时/失联/正常完成/非 USV 脚本 |
| ArduRover 完整 SITL 构建 | 成功 | `build/usv-safety-sitl/sitl/bin/ardurover`；不是 Pixhawk6C APJ |
| 隔离 Rover SITL | 4 场景通过 | 见下表；不包含真实 ROS/router/ESP32 或船体物理验收 |
| 发布检查器回归 | 3 通过 | 验证候选不等于发布，SITL 产物不能替代硬件固件 |
| 本轮差异检查 | 通过 | 未处理原有 `.ai-bridge/pro-context.md` 空白问题 |

完整 ROS 测试中另出现 Windows shell 探测输出解码告警及旧资源未关闭告警，未将其当作 Jetson/Noetic 运行验证。目标运行环境仍需验收。

### 隔离 SITL 实测

命令（ArduPilot 仓库，WSL 现有 pymavlink 环境）：

```bash
python3 -B tests/check_usv_sitl_sampling.py --binary build/usv-safety-sitl/sitl/bin/ardurover --scenario all
```

测试只创建本机新模拟器、临时目录和独立回环 UDP 端口，不连接已有飞控。

| 场景 | sample_id | 采样后最大任务序号 | 观测 |
|---|---:|---:|---|
| success | 1 | 2 | 正确来源、匹配 ID 的 USV_DONE 放行 |
| cancel | 1 | 1 | USV_FAIL 后实际进入 HOLD，不推进后续航点 |
| timeout | 1 | 1 | 错误 component 的 DONE 不放行，6 秒脚本期限后 HOLD |
| link_loss | 1 | 1 | GCS 心跳继续、仅停止伴随载荷更新，进入 HOLD |

显式 SKIP 的分类/门控由 ROS `test_fcu_sampling_result.py` 验证；飞控看到的合法放行仍是匹配 ID 的 DONE。

## 基线中已存在的失败

1. `test_web_map_config_serves_offline_tile_proxy_without_amap_key`：测试要求 `leaflet-amap-raster`，当前 HEAD 返回 `leaflet-google-raster`。通过 `git show HEAD:scripts/web_config_server.py` 提取原始 WebConfigServer 类，在同一测试中复跑，确认修改前也失败；未 checkout 或覆盖工作树。
2. `test_frontend_declares_runnable_map_smoke_script`：smoke 脚本要求 `MAP_TILE_NATIVE_MAX_ZOOM = 18`，当前地图实现不满足。对应前端脚本/页面/lib 与 HEAD 的 `git diff --exit-code` 为 0，本轮未改变它们。

保留这些失败，不通过削弱断言或改变地图行为使全量测试表面变绿。

## 性能回归

使用现有 `tests/benchmark_history_loading.py HEAD`，临时生成 100000 点/100000 原始帧：现有合并入口冷读取约 0.3441 s、暖缓存约 0.0011 s、返回 56947 字节且不解析原始帧。原始曲线按需读取约 0.4233 s。历史性能测试 10 项、存储测试 8 项通过。

这些数据用于确认保留已有缓存/按需读取能力，不是声称本轮新增了此前已经存在的加速，也不是 Jetson 性能承诺。

## 发布与剩余风险

- 候选清单：`2026-09-17-safety1-candidate.json`，包含原始提交、当前工作树差异哈希、关键源文件哈希和已构建产物哈希。`field_verified=false`，所有业务子仓库仍有未提交修复。
- `--manifest` 源码匹配检查通过；`--require-release` 应拒绝此候选，因为尚无现场验收、干净提交和完整的硬件/应用发布产物。
- 未做 Pixhawk6C 固件构建/刷写、QGC 全平台打包、Jetson ROS 实进程联调、USB/电台/电机台架及实船验收。
- `USV_DONE/USV_FAIL` 仍不是有端到端 ACK 的持久化事务；跨飞控重启的 ID 复用尚无会话级保证。必须停任务并成套重启/更新，不允许把发送成功当作物理完成或跨重启恢复证明。
- 软件看门狗需要实测调度延迟和物理输出停止时间，不能替代独立断电手段。HOLD 不等于原地定位保持。
- 远程 HTTP 令牌认证不提供传输加密；非受控链路必须通过 TLS/VPN。读监控数据也需要网络层隔离。
- 新旧检测端不能混用：ROS/Windows 要求 `CAP=WATCHDOG1`；新固件不再接受未 ARM 的运动。远程 Web 未配置令牌时只读。
- 保留用户原有未提交文件。不要为了通过发布检查删除这些文件，应保存业务修改并在干净检出上形成正式验证清单。

代码已完成这一轮安全收口；上述验收与协议限制未被伪称为完成。
