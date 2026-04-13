# 技术计划
Updated: 2026-04-13T13:34:06Z

## 1. 当前目标
- 删除根目录脚本 `bootstrap_workspace.sh` 与 `bootstrap_workspace.ps1`，收口为唯一 Windows 批处理入口 `bootstrap_workspace.bat`。
- 在 `bootstrap_workspace.bat` 中写死外部源码仓库地址：`ardupilot-usv`、`WQ-USV-QGroundControl`、`usv_ros`。
- 更新根 `README.md`，说明总管理仓库 clone、唯一 bootstrap 入口、三端构建入口与 Git 管理策略。
- 保留根 `.gitignore`，确保总管理仓库仅跟踪文档与入口脚本，不纳入三方源码与本地构建产物。
- 更新 `docs/current/overview.md`、`INTERFACE.md`、`TREE.md`、`task.md`，移除 `.sh/.ps1` 入口引用。

## 2. 影响文件
- `bootstrap_workspace.bat`
- `README.md`
- `.gitignore`
- `docs/current/overview.md`
- `docs/current/plan.md`
- `docs/current/task.md`
- `docs/current/INTERFACE.md`
- `docs/current/TREE.md`
- 删除：`bootstrap_workspace.sh`
- 删除：`bootstrap_workspace.ps1`

## 3. 受影响符号与范围
- `bootstrap_workspace.bat L1-L53 ~+53`
- `README.md §1-§7 ~+99/-31`
- `.gitignore L1-L19 ~0`
- `docs/current/overview.md §4-§7 ~+2/-3`
- `docs/current/INTERFACE.md §0 ~+4/-6`
- `docs/current/TREE.md 头部根文件列表 ~+1/-2`
- `docs/current/task.md 追加本次证据、删除记录、验证结果 ~+20`

## 4. 执行步骤
1. 新建 `bootstrap_workspace.bat`，固定仓库 URL 为：`https://github.com/MIGO-OvO/ardupilot-usv.git`、`https://github.com/MIGO-OvO/WQ-USV-QGroundControl.git`、`https://github.com/MIGO-OvO/usv_ros.git`。
2. 删除 `bootstrap_workspace.sh` 与 `bootstrap_workspace.ps1`，根仓库只保留 `.bat`。
3. 更新 `README.md`：只保留 `.bat` 用法，移除 Bash/PowerShell 章节。
4. 更新 `overview.md`、`INTERFACE.md`、`TREE.md`：入口描述统一为 `bootstrap_workspace.bat`。
5. 更新 `task.md`：记录删除文件、固定 URL、验证输出。
6. 验证：`diagnostics(bootstrap_workspace.bat,README.md,docs/current/*.md)` 与 `view` 抽查根目录树、README、bat 一致性。

## 5. 验收条件
- 根目录只保留一个引导脚本：`bootstrap_workspace.bat`。
- `.bat` 内存在 3 个固定 GitHub URL，遗漏数 `0`。
- `README.md` 不再出现 `bootstrap_workspace.sh` 或 `bootstrap_workspace.ps1`。
- `docs/current/overview.md`、`plan.md`、`task.md`、`INTERFACE.md`、`TREE.md` 更新时间戳为本次执行。
- diagnostics 结果 `0` 条。

## 6. 回滚
```bash
git restore docs/current/overview.md docs/current/plan.md docs/current/task.md docs/current/INTERFACE.md docs/current/TREE.md README.md .gitignore
if git ls-files --error-unmatch bootstrap_workspace.bat >/dev/null 2>&1; then git restore bootstrap_workspace.bat; else rm -f bootstrap_workspace.bat; fi
```

## remeber.plan.1
label=scope|fact=用户要求只保留一个 Windows bat 引导脚本|impact=必须删除根目录 .sh 和 .ps1 入口|next=同步 README/docs 去除旧引用

## remeber.plan.2
label=url|fact=仓库地址已由用户明确提供 GitHub URL|impact=bat 脚本应直接写死地址而非再要求输入参数|next=在 README 与 INTERFACE 标明内置 URL

## remeber.plan.3
label=consistency|fact=根目录树、README、INTERFACE 必须都只出现 bootstrap_workspace.bat|impact=任何旧入口残留都会误导部署|next=用 diagnostics+view 双重核对
