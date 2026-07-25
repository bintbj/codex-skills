# 状态结构

schema v2 的 `state.json` 必须包含：`schema_version`、`mission_id`、
`repository_url`、`repository_id`、`base_branch`、`mission_status`、`phase`、
`recommended_reasoning`、`current_task`、`base_commit`、`working_branch`、
`last_checkpoint_commit`、`next_action`、`blocked`、`blockers`、`failed_attempts`
和 `updated_at`。

- `schema_version` 必须为 `2`。
- `mission_id` 必须匹配目录名和 `codex/mission/<mission-id>` 的分支后缀。
- `repository_id` 必须等于当前 `origin` remote 的规范化值。
- `base_branch` 不能为空，且不得以 `codex/mission/` 开头。
- `working_branch` 必须是 `codex/mission/<mission-id>`。
- `mission_status` 为 `draft|active|blocked|complete`；推理强度为 `low|high`。

当前任务存在时，对应文件必须位于该 mission 的 `tasks/TASK-NNN.md`，且包含
`Objective`、`Prerequisites`、`Owned Paths`、`Forbidden Paths`、`Constraints`、
`Acceptance Commands`、`Evidence`、`Dependencies`、`Status` 标题。
