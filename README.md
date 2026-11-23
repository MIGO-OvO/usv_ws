# usv_ws 水质监测无人船

从这里拉取和管理整船工作区。地面站、船载 ROS、飞控、检测固件和 Windows 上位机各有独立仓库。

- [按任务查文档](docs/current/00_index.md)
- [系统与源码入口](docs/current/20_system_overview.md)
- [构建、更新与运行](docs/current/50_build_update_runbook.md)
- [现场验收](docs/current/70_verification.md)
- [开发约定](AGENTS.md)

## 拉取工作区

在 Windows 工作区根目录运行以下命令。

```bat
bootstrap_workspace.bat
```

脚本负责拉取和更新各仓库。`DetFirmware/` 来自授权访问的私有仓库 [MIGO-OvO/DetFirmware](https://github.com/MIGO-OvO/DetFirmware)，默认分支为 `main`。旧工作区的 `DetFirmware/` 若没有独立 `.git`，先备份本地改动，再迁移或另行克隆。根仓库历史仍保留迁移前的版本。

## 整船版本检查

```text
python docs/tools/check_workspace_compatibility.py
```

成套更新、候选快照和发布条件见[构建与运行](docs/current/50_build_update_runbook.md#safety1-成套发布要求)。现场验收记录见[验证矩阵](docs/current/70_verification.md#safety1-安全回归与发布门槛)。
