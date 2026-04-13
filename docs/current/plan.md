# 技术计划
Updated: 2026-04-13T13:01:44Z

## 1. 当前目标
- 新增根目录脚本 `bootstrap_workspace.sh`，用于在空工作区内拉取 `ardupilot-usv`、`WQ-USV-QGroundControl`、`src/usv_ros` 三个外部源码仓库。
- 新增根目录脚本 `bootstrap_workspace.ps1`，为 Windows PowerShell 提供等价的 clone/bootstrap 入口。
- 新增根 `README.md`，说明总管理仓库 clone、bootstrap、三端构建入口与 Git 管理策略。
- 新增根 `.gitignore`，确保总管理仓库仅跟踪文档与入口脚本，不纳入三方源码与本地构建产物。
- 更新 `docs/current/overview.md`、`INTERFACE.md`、`TREE.md`、`task.md`，记录工作区引导入口、忽略策略、执行命令与验证结果。

## 2. 影响文件
- `bootstrap_workspace.sh`
- `bootstrap_workspace.ps1`
- `README.md`
- `.gitignore`
- `docs/current/overview.md`
- `docs/current/plan.md`
- `docs/current/task.md`
- `docs/current/INTERFACE.md`
- `docs/current/TREE.md`

## 3. 受影响符号与范围
- `bootstrap_workspace.sh:usage L19-L39 ~0`
- `bootstrap_workspace.ps1:Show-Usage L18-L39 ~+22`
- `bootstrap_workspace.ps1:Clone-Repo L61-L92 ~+32`
- `bootstrap_workspace.ps1:Print-NextSteps L94-L113 ~+20`
- `README.md §1-§7 ~+100`
- `.gitignore L1-L14 ~0`
- `docs/current/overview.md §4-§7 ~+2`
- `docs/current/INTERFACE.md “总管理仓库入口”段 ~+3`
- `docs/current/TREE.md 根目录树增加 `README.md` 与 `bootstrap_workspace.ps1` ~+2`
- `docs/current/task.md 追加本次证据、命令输出、remeber 条目 ~+20`

## 4. 执行步骤
1. 以 `bootstrap_workspace.sh` 为单一行为基线，实现 PowerShell 等价版本 `bootstrap_workspace.ps1`，保持 URL/REF 输入、clone/submodule 流程和目标目录一致。
2. 新增根 `README.md`，明确根仓库职责、bootstrap 两种入口、三端构建命令与 `.gitignore` 策略。
3. 更新 `overview.md` 与 `INTERFACE.md`：补充 PowerShell 入口与根 README 入口。
4. 更新 `TREE.md` 与 `task.md`：登记新增文件、验证命令与证据。
5. 验证：`powershell -ExecutionPolicy Bypass -File .\bootstrap_workspace.ps1 -?` 不适用；改为 `diagnostics(bootstrap_workspace.ps1,README.md,docs/current/*.md)` 与 `view` 抽查内容一致性。

## 5. 验收条件
- `bootstrap_workspace.ps1` 存在且参数/环境变量命名与 `bootstrap_workspace.sh` 对齐。
- `README.md` 存在并覆盖 clone、bootstrap、ROS/QGC/ArduPilot 构建入口、Git 管理策略。
- `docs/current/overview.md`、`plan.md`、`task.md`、`INTERFACE.md`、`TREE.md` 更新时间戳为本次执行。
- diagnostics 结果 `0` 条。
- `TREE.md` 与根目录实际新增文件一致：`README.md`、`bootstrap_workspace.ps1`。

## 6. 回滚
```bash
git restore docs/current/overview.md docs/current/plan.md docs/current/task.md docs/current/INTERFACE.md docs/current/TREE.md
if git ls-files --error-unmatch .gitignore >/dev/null 2>&1; then git restore .gitignore; else rm -f .gitignore; fi
if git ls-files --error-unmatch bootstrap_workspace.sh >/dev/null 2>&1; then git restore bootstrap_workspace.sh; else rm -f bootstrap_workspace.sh; fi
if git ls-files --error-unmatch bootstrap_workspace.ps1 >/dev/null 2>&1; then git restore bootstrap_workspace.ps1; else rm -f bootstrap_workspace.ps1; fi
if git ls-files --error-unmatch README.md >/dev/null 2>&1; then git restore README.md; else rm -f README.md; fi
```

## remeber.plan.1
label=scope|fact=本次新增 Windows PowerShell 入口和根 README|impact=根仓库对跨平台 bootstrap 的可用性提升|next=同步 docs/current 入口文档

## remeber.plan.2
label=compat|fact=PowerShell 版必须与 bash 版参数和目录布局一致|impact=避免多设备文档与脚本行为分叉|next=复用同样的 URL/REF 命名

## remeber.plan.3
label=docs|fact=根 README 现在是新成员进入总管理仓库的第一入口|impact=需要写清 clone/bootstrap/build/git ignore 四类信息|next=补 TREE 与 overview 引用
