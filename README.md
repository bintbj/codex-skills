# Codex Skills

由 bintbj 维护的可复用 Codex Skills。

## orchestrate-long-task

使用 Git 检查点在多个 Codex 账号、对话、模型和推理强度之间迁移并继续超大任务。用 `$skill-installer` 安装 `skills/orchestrate-long-task`，然后在目标项目中使用：

- 首次接管：`$orchestrate-long-task 接管当前项目`
- 当前会话继续：`继续`
- 准备换账号：`$orchestrate-long-task 准备交接`
- 新账号接手：`$orchestrate-long-task 接手当前项目`

固定流程由 Skill 自动执行。用户只需补充仓库中无法判断的目标、验收标准、产品选择或外部操作授权。

本 Skill 不共享账号凭据、不合并额度、不读取实时用量，也不绕过任何使用限制。
