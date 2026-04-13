# 技术计划
Updated: 2026-04-13T22:06:23+08:00

## 1. 当前目标
- 汇总 `2026-03-31` 至 `2026-04-13` 三端源码仓库中作者 `MIGO_12` 的 git 变更。
- 按 ROS / QGC / ArduPilot 三端整理本周期工作成果、问题与阶段性结论。
- 生成一份可直接用于开发汇报的 PPT 文案 markdown 到 `docs/current/`。
- 更新 `docs/current/task.md`、`docs/current/TREE.md`，记录证据与新增文档索引。

## 2. 影响文件
- `docs/current/plan.md`
- `docs/current/task.md`
- `docs/current/TREE.md`
- 新增：`docs/current/ppt_progress_report_20260331_20260413.md`

## 3. 受影响符号与范围
- `docs/current/ppt_progress_report_20260331_20260413.md L1-L93 ~+93`
- `docs/current/plan.md L1-L41 ~+41/-61`
- `docs/current/task.md 文末追加 ~+20`
- `docs/current/TREE.md docs/current 段 ~+1`

## 4. 执行步骤
1. 使用 `git log --since --until --author="MIGO_12"` 分别统计 `src/usv_ros`、`WQ-USV-QGroundControl`、`ardupilot-usv`。
2. 提取提交数量、增删行、涉及文件数、高频修改文件与代表性提交。
3. 结合 `docs/current/overview.md`、`roadmap.md`、`task.md` 已有上下文，整理为逐页 PPT 文案。
4. 新建 `docs/current/ppt_progress_report_20260331_20260413.md`。
5. 追加 `task.md` 技术证据，更新 `TREE.md` 新文件索引。
6. 验证：`diagnostics(docs/current/*.md)=0`，并用 `view` 抽查新增文档内容与目录树。

## 5. 验收条件
- PPT 文案覆盖：总览、三端成果、关键突破、问题与解决、量化结果、后续计划。
- 统计口径明确为时间窗内作者 `MIGO_12` 的提交。
- 文案中的稳定版本标签与 commit 与现有 `overview.md` 一致。
- `task.md` 追加本次证据；`TREE.md` 包含新增文档。
- diagnostics 结果 `0` 条。

## 6. 回滚
```bash
git restore docs/current/plan.md docs/current/task.md docs/current/TREE.md docs/current/ppt_progress_report_20260331_20260413.md
```

## remeber.plan.1
label=scope|fact=本次任务是基于 git 历史生成汇报文档而非修改三端业务代码|impact=输出必须忠于提交事实和现有文档|next=按仓库分别统计提交与主题

## remeber.plan.2
label=data|fact=用户要求覆盖 2026-03-31 到 2026-04-13 两周窗口且只描述本人工作|impact=统计必须按 author=MIGO_12 过滤|next=记录每仓 commit 数与代表性提交

## remeber.plan.3
label=docs|fact=需把结果保存到 docs 目录下且遵守 current 文档体系|impact=应新增单一 PPT 文案文件并同步 TREE/task|next=落盘后做 diagnostics 与抽查
