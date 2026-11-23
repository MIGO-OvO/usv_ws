# usv_ws 开发约定

根仓库维护跨端文档、检查工具和工作区入口。五个业务仓库各有自己的 `AGENTS.md`。

- 源码定义现行行为。改文档时对照相关源码和测试。
- 提交按 Git 仓库分开。根仓库只提交根文档、`docs/`、bootstrap、检查工具和根配置。按文件暂存，现场数据、日志、构建产物和带凭证的 URL 留在 Git 外。
- MAVLink 命令、遥测、路由、component ID 或 ACK 变更先查飞控源码，再核对 ROS 与地面站。入口见[接口速查](docs/current/40_interfaces.md#修改-mavlink-时查源码)。
- 检测装置串口变更同时核对 DetFirmware、ROS `pump_control_node.py` 和 Windows 上位机解析。污染物浓度、采样记录和热力图归 ROS/Web。
- 运行改动涉及物理动作时，保留停止保护、采样身份校验和断链后旧动作的失效规则。交付说明用中文。涉及协议时给出源码位置、对端行为和验证方法。
- 按改动范围验证。分别记录离线测试、构建、台架和实船结果。

## 按任务查阅

| 任务 | 入口 |
|---|---|
| 查系统职责或源码位置 | [系统概览](docs/current/20_system_overview.md) |
| 更新、部署或现场排障 | [构建与运行](docs/current/50_build_update_runbook.md) |
| 测试、CI 或现场验收 | [验证矩阵](docs/current/70_verification.md) |
| 改采样记录或 GPS 绑定 | [采样记录与开始位置绑定](docs/current/80_sample_gps_binding.md) |
| 浏览文档 | [文档索引](docs/current/00_index.md) |
