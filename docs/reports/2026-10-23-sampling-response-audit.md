# 2026-10-23 采样响应审计修复与回归

## 交付范围

继续更新三个草稿 PR，分支均为 `codex/sampling-response-recovery`。

| 仓库 / PR | 修复前提交 | 本轮源码提交 | PR base |
|---|---|---|---|
| [usv_ros #97](https://github.com/MIGO-OvO/usv_ros/pull/97) | `a856513b7e00fdc499f5ae24ae7cd6c43b825112` | `fa2e0edfc1a393b21b797f0946acf0c7b229f3e3` | `main` |
| [QGC #21](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/pull/21) | `2d3e0bf7657e13a9eea841c8675a2c32e4b1ce10` | `2a063f7379d54af618a309694628b577655299f3` | `codex/manual-sampling-first-cause`（#20） |
| [usv_ws #30](https://github.com/MIGO-OvO/usv_ws/pull/30) | `9bd09eb14a8f3f1d9370ed50240b0d60c8642f56` | 本报告所在提交 | `codex/pid-separation-log-fixes`（#29） |

本轮未修改飞控、检测板、MAVLink 协议、命令 ID 或设备控制语义。原有未跟踪的根 `.codex/`、`USV_Cross_End_Audit_2026-10-18/` 与 QGC `.workbuddy/` 保留。

## 修复根因

### USVE1 长事件占用发送状态

旧实现固定续发 `_active_event_send`；超过 1 秒组包期限时直接换 id 从头发送，却不重新选择事件。普通长事件在持续背压下反复重播，后续 STOP 即使可完整发出也一直排队。

`scripts/usv_mavlink_router_bridge.py` 复用现有 pending 队列和优先级。在完整帧边界发现更高优先级事件，或当前组包已经过期时，释放活动发送状态并重新调度。STOP 先发；被中断事件仍在 pending 中，再次获调度时用新 chunk id 从 0 重播。请求身份、事件 seq、内容和去重规则不变。

TCP transport 可在零字节延期、完整帧完成或会话退役时交回控制。调度不会在已写入半帧时插入 STOP；部分帧无法完成仍触发现有断线停止保护。

### 启动上下文未及时绑定请求

手动和 FCU 采样原先先公开上下文，再绑定位置，之后才补齐请求与采样状态。位置绑定期间断线，STOP 能清理上下文，却找不到关联请求；启动线程随后还可能重新写入 `is_sampling=True`，最终回执退化为 `command_rejected_or_cancelled`。

`scripts/mavlink_trigger_node.py` 在创建上下文时即写入 `mavlink_request`，并在现有 `state_lock` 内一起发布上下文、采样标志和 mission 状态。断线取消沿用原停止、RequestLedger 终态和恢复路径，保留 `transport_session_lost`，不增加执行或重试机制。

### Windows 部署参数错误

Qt 6.10.1 `windeployqt --help` 不包含 `--no-texttospeech`，原 Windows CI 在链接后的部署阶段报 `Unknown option 'no-texttospeech'.`。

`cmake/platform/Windows.cmake` 和 `cmake/install/Install.cmake` 删除该参数，保留 `DISABLE_SPEECH` 条件下的 `--skip-plugin-types texttospeech`。现有编译时语音禁用逻辑不变。

### MockLink 断开时释放仍在使用的通道

旧 Linux Debug 日志的主线程在 `MockLink::disconnect()` 发出 `disconnected` 后，由 LinkManager 释放 MAVLink 通道；worker 同时还在 `_sendADSBVehicles()`，最终以 `chan=255`、空 status 指针进入 `mavlink_finalize_message_buffer()`，退出码 139。

MockLink/MockLinkWorker 在 master、#20 和原 #21 的源码一致，属于既有竞态。#20 对应那次测试通过，未触发此竞态。修复在 `disconnected` 前以 `BlockingQueuedConnection` 调用已有 `MockLinkWorker::stopWork()`，等待当前回调完成并停下定时器，再释放通道。

新增 `VehicleLinkManagerTest::_disconnectWaitsForMockWorker`，在 worker 发送回调中用信号量暂停，检查 `disconnected` 不早于回调完成。

## 修改文件

| 仓库 | 文件 | 用途 |
|---|---|---|
| ROS | `scripts/usv_mavlink_router_bridge.py` | 帧边界重调度 |
| ROS | `scripts/mavlink_trigger_node.py` | 启动上下文原子发布 |
| ROS | `tests/test_payload_transport_recovery.py` | 持续背压、优先级、手动/FCU 启动竞态 |
| ROS | `tests/test_bridge_qml_event_chain.py` | 真实 MAVLink 短写期间 STOP 到达、旧事件重播 |
| QGC | `cmake/platform/Windows.cmake`、`cmake/install/Install.cmake` | 支持的语音插件排除参数 |
| QGC | `src/Comms/MockLink/MockLink.cc` | 释放通道前等待 worker 停止 |
| QGC | `test/Vehicle/VehicleLinkManagerTest.cc`、`.h` | 确定性断开并发回归 |
| QGC | `src/MAVLink/StatusTextHandler.cc`、`src/Vehicle/Vehicle.cc` | 只格式化本 PR 新增的诊断语句 |
| QGC | `deploy/linux/org.mavlink.qgroundcontrol.appdata.xml.in` | 用可访问的源图替换失效截图地址 |
| 根仓库 | `docs/current/40_interfaces.md`、`50_build_update_runbook.md`、`70_verification.md`、本报告 | 接口、部署、验证和 CI 证据 |

## 回归结果

修复前运行新增 ROS 测试，确认 STOP 无法出队、启动窗口断线结果退化；修复后通过。本地原始日志位于 `D:\usv_ws\.codex\audit-20261023\`。

| 验证 | 结果 | 日志 / 说明 |
|---|---|---|
| ROS 非地图回归 | 751 项，735 通过、16 跳过；地图相关 130 项排除 | `ros-nonmap-final.log`；`python -B tests/run_non_map_tests.py` |
| Linux/WSL 定向 | transport 7、真实 TCP 2、恢复 12、真实 bridge 字节流 2；共 23 通过，0 跳过 | Python 3.12.3，真实 pymavlink，各测试文件独立进程运行 |
| 事件优先级 / 泵启动调用链 | 7 + 5 项通过 | 生产状态机，模拟串口与 ROS 边界；覆盖 STOPALL 和恢复不重启泵 |
| QGC QML | 88 通过，0 失败/跳过 | `qml.txt`；Qt 6.10.1，offscreen/software |
| QGC Python 契约 | 37 通过 | `custom/tests/test_usv_qgc_contract.py` |
| QGC 原生 C++ | 28 通过，0 失败/跳过；进程 exit 0 | `native-final.txt`：VehicleLinkManager 8、SendMavCommandWithSignalling 13、StatusTextHandler 7 |
| ROS → QGC 原生跨端 | 同一组 28 项通过，0 失败/跳过；进程 exit 0 | `native-cross-end.txt`；真实 bridge/pymavlink 生成 CRC 合法分片，按日志中的 sysid 147 生成，未改写帧身份 |
| 根文档与跨仓契约 | Source contracts match；docs/tools 11 项通过 | 文档修改后复核 |
| Python 语法 / diff | 变更 Python 文件语法检查、三个仓库 `git diff --check` 通过 | 未使用硬件 |
| C++ 改动行格式 | clang-format 21.1.7 检查四个 C++ 文件的 PR 改动行通过 | 未整文件格式化 |
| 元数据 | XML 解析通过；新截图地址 HTTP 200、image/jpeg | 原 AppImage 日志中的 404 已修正 |
| Windows 构建 | 完整 Debug 编译、链接、构建后部署 exit 0 | `windows-build.log`、`windows-build-final.log`；Qt 6.10.1 / MSVC 14.44.35207 / Ninja，并行度 2 |
| Windows 安装 / 打包 | 新 staging 的 `cmake --install`、windeployqt 和 NSIS 3.11 exit 0；7-Zip 校验 2528 文件通过 | `windows-install.log`、`installer-test.txt`；未执行系统安装/卸载 |
| 语音禁用 / 部署启动 | staging 中 TextToSpeech DLL 与插件目录均为 0；部署程序 `--simple-boot-test` exit 0 | `staging-boot.err`；Qt 插件从 staging 加载，未设置 SDK `QT_PLUGIN_PATH` |

本地 Debug 测试安装包为 `WQ-USV-QGroundControl/build/audit-debug-20261018-v2/QGroundControl-installer-AMD64.exe`，153470568 字节，SHA256 `52f57b679691fc90a9bc1b5f43d7262da3041d714ed4b1f55eed1815d8e9b70f`。NSIS 提示既有未使用标签 `done`；部署提示缺少可选 dxcompiler/dxil 及未设置 VCINSTALLDIR，未导致失败。干净 Windows 机器上的 Release 安装、卸载和 GPU/视频运行仍需验证。

关键断言：零字节预算耗尽延期；部分帧失败退役；分片续发身份与完整性；持续背压下 STOP 有限周期送达；启动断线实际触发停止；恢复和同身份重试不重复 START；旧会话事件不影响新任务；QGC 显示“载荷通信中断，采样已取消”或“载荷通信中断，停止未确认，请核验设备”。

## CI 调查

### 修复前日志

| 检查 | 实际失败 | 分类 / 处理 |
|---|---|---|
| [Windows 39850321936](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850321936) | windeployqt 不支持 `--no-texttospeech` | 已修两个部署入口 |
| [Linux 39850322385](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850322385) Debug | MockLink 定时发送与通道释放并发，SIGSEGV 139 | 已修既有竞态并增加同步回归 |
| 同次 Linux Release / AppImage | 旧哈希截图地址 404，AppStream `Validation failed: warnings: 1` | 已替换稳定源图 URL |
| [pre-commit 39850322267](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850322267) | `--ci` 检查全仓；JSON、whitespace/EOF、clang-format、缺编译数据库的 clang-tidy、Python、Shell、CMake、Markdown 等失败 | 已修本 PR 新增日志格式；其余既有全仓问题保留记录，未批量改写或绕过 workflow |
| [Android 39850322366](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850322366) emulator | Google APIs system image `Error on ZipFile unknown archive`；模拟器未启动，adb connection refused | 外部 SDK 下载故障；同 head 的 Android 构建成功，未改应用源码 |
| [Docker 39850322250](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39850322250) Linux | apt 下载 `libusb-1.0-0-dev_1.0.27-1_amd64.deb`，连接 archive.ubuntu.com:80 超时，exit 100 | 软件源网络故障，未改 Dockerfile 或放宽检查 |

### 修复提交的检查

以下为北京时间 2026-10-23 16:40 的快照，只记录 QGC `2a063f7379d54af618a309694628b577655299f3` 的检查，运行中不计通过。

| 检查 | 状态 / 链接 |
|---|---|
| PR Checks / Check Links | 通过 |
| Windows | [运行中](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923648677) |
| Android | [PR run](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923648830) / [push run](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923642303) 运行中 |
| Linux / AppImage | [工作流运行中](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923648961)：x64 Release 的 Checkout repo 已失败，构建与 AppImage 未执行，日志尚未开放；ARM64 Release 构建中，x64 Debug 安装依赖中 |
| Docker | [运行中](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923648571) |
| pre-commit | [失败](https://github.com/MIGO-OvO/WQ-USV-QGroundControl/actions/runs/39923648815)；已取得完整日志 `precommit-after-full.log`，按文件/行号可定位的诊断没有落入本 PR 新增行，全仓检查尚未通过 |

本机全套改动文件 pre-commit 在初始化 Vale 的 Go/tree-sitter 环境时失败（`build constraints exclude all Go files` / `undefined: Node`），未执行完整 hooks，记录为未完成。单独运行 merge-conflict、mixed-line-ending、added-large-files 三个 hook 通过；本 PR 新增 C++ 行另按 clang-format 21.1.7 检查。未修改工作流以绕过失败。

## 尚待验证

- Windows Release、ARM64 和 ARM64 cross 的当前 head CI；本地主机为 x64 Debug。
- Linux runner 的当前 head MockLink 全套回归及 AppImage；Windows 原生通过不能代替它们。
- pre-commit 全仓历史告警。未为本轮修复扩大到全仓格式化、重构或检查配置变更。
- Jetson、飞控、检测装置台架和实船未部署验收；真实输出停止、无线链路、router 转发须按 `docs/current/70_verification.md` 留存同窗证据。

STOP 优先级测试的送达前提是传输仍健康，且 STOP 帧有可写机会。真实断线、半帧无法完成或所有数据都无法写入时，仍退役会话并执行停止保护，不能把队列调度当作物理送达证明。
