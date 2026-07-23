# 状态结构

`state.json` 必须包含：`schema_version`、`mission_status`、`phase`、`recommended_reasoning`、`current_task`、`base_commit`、`working_branch`、`last_checkpoint_commit`、`next_action`、`blocked`、`blockers`、`failed_attempts` 和 `updated_at`。允许的 `mission_status` 为 `draft|active|blocked|complete`；允许的推理强度为 `low|high`。

当前任务存在时，对应文件必须位于 `tasks/TASK-NNN.md`，且包含 `Objective`、`Prerequisites`、`Owned Paths`、`Forbidden Paths`、`Constraints`、`Acceptance Commands`、`Evidence`、`Dependencies`、`Status` 标题。
