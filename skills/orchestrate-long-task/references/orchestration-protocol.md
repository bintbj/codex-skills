# 编排协议

状态流：`bootstrap → plan → execute → verify → checkpoint`；随后进入下一任务、`handoff`、`replan` 或 `integrate`。`plan`、`replan`、`integrate` 和 `final_verify` 使用高推理；边界清晰的执行和验证使用低推理。每个任务、决定或验收变化后创建检查点；首次额度警告时创建完整交接，不等待硬性限额。

新账号必须先读取 `AGENTS.md`、`mission.md`、`state.json`、`handoffs/latest.md`、当前任务和决策，再运行验证器。两次相同验收失败、状态矛盾或接口变化必须重新规划。
