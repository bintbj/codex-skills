# 编排协议

每个 mission 的状态流为：`bootstrap → plan → execute → verify → checkpoint`；
随后进入下一任务、`handoff`、`replan` 或 `integrate`。`plan`、`replan`、
`integrate` 和 `final_verify` 使用高推理；边界清晰的执行和验证使用低推理。
每个任务、决定或验收变化后创建检查点；首次额度警告时创建完整交接，不等待
硬性限额。

## 双重定位与隔离

mission 的唯一定位为规范化 Git `origin` remote 加 mission ID。控制状态位于
`.task-orchestrator/missions/<mission-id>/`，工作分支为
`codex/mission/<mission-id>`。不同 mission 不得共享状态目录、交接文件、
任务目录、归档目录或工作分支。

新账号必须先取得仓库、fetch 并检出目标 mission 分支，再读取 `AGENTS.md`、
mission、state、handoff、当前任务和决策，最后运行带 `--mission` 的验证器。
repository ID、mission ID、目录、分支、提交或工作区状态存在无法解释的差异时
停止。更新只能 fast-forward；不得以 reset 覆盖本地工作。

当前会话选择 mission 的优先级是显式 ID、分支后缀和唯一 mission 目录。存在
多个候选时只列出 ID 并询问一次。新电脑或新账号没有本地仓库时必须提供
`repo=<repository-url> mission=<mission-id>`；不得从旧聊天或用户目录猜测。

## 创建、并行和交接

创建 mission 必须从明确的非 mission 基线分支开始。若当前分支已匹配
`codex/mission/*`，先停止并要求选择基线，避免将一个活跃任务作为另一个任务
的隐式祖先。需要同时处理多个 mission 时使用独立 Git worktree；同一源文件的
最终冲突仍在集成阶段按正常 Git 合并处理。

交接前完成最小安全步骤、更新本 mission 的证据和 `handoffs/latest.md`、验证、
提交并推送目标 mission 分支。新账号的恢复命令必须同时包含仓库地址和 mission
ID。两次相同验收失败、状态矛盾或接口变化必须重新规划。

## 旧布局

旧 `.task-orchestrator/{mission.md,state.json,...}` 不能与新布局混用。只有显式
`migrate_workspace.py` 可以迁移它；迁移要求工作区干净、remote 可验证、目标目录
不存在且已检出对应 mission 分支。任一前置检查失败时不得修改文件。
