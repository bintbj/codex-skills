# Codex Skills

由 bintbj 维护的可复用 Codex Skills。

## orchestrate-long-task

用 Git 检查点在多个 Codex 账号、对话、模型和推理强度之间迁移超大任务。每个
任务以“仓库地址 + mission ID”定位，状态隔离在：

```text
.task-orchestrator/missions/<mission-id>/
```

每个 mission 使用专属分支：`codex/mission/<mission-id>`。

### 安装

让 Codex 使用 `$skill-installer` 从本仓库安装
`skills/orchestrate-long-task`。每台电脑只需安装一次；新账号仍需要具有目标
仓库的正常 Git 访问权限。

### 首次创建任务

1. 打开目标 Git 仓库并确保已配置 `origin`。
2. 切换到作为基线的非 mission 分支，例如 `main`，且工作区干净。
3. 输入：

   ```text
   $orchestrate-long-task 接管当前项目 mission=build-api-v2
   ```

Skill 会创建 `codex/mission/build-api-v2`、写入该 mission 的持久化计划并要求
你在首次命名后确认不可推断的业务目标。

### 同一账号继续

在正确的 mission 分支或 worktree 中输入：

```text
$orchestrate-long-task 继续
```

如果当前仓库有多个 mission 且无法从分支判断，输入：

```text
$orchestrate-long-task 继续 mission=build-api-v2
```

### 原账号交接

在准备换账号、出现第一次额度警告时输入：

```text
$orchestrate-long-task 准备交接 mission=build-api-v2
```

Skill 会完成最小安全步骤、更新交接、验证、提交并推送 mission 分支。交接输出的
恢复命令必须保留仓库地址和 mission ID。

### 新账号或新电脑接手

先安装 Skill 并完成目标仓库的正常 Git 认证，然后输入：

```text
$orchestrate-long-task 接手 repo=https://github.com/example/project.git mission=build-api-v2
```

Skill 会克隆或更新仓库、检出 `codex/mission/build-api-v2`、验证仓库与 mission
双重标识，并按前一账号写入的 `next_action` 继续。它不会共享凭据、合并额度、
自动登录或绕过限制。

### 同仓库并行多个任务

为每个 mission 使用独立分支和 worktree，例如：

```bash
git worktree add ../project-build-api-v2 codex/mission/build-api-v2
git worktree add ../project-redesign-console codex/mission/redesign-console
```

控制状态和未提交代码因此互相隔离；若两个 mission 修改同一源文件，仍需要在最终
集成时正常处理 Git 合并冲突。

### 迁移旧版本

旧单任务结构必须显式迁移，不能直接覆盖。先创建并检出目标 mission 分支，然后：

```text
$orchestrate-long-task 迁移旧任务 mission=build-api-v2 base=main
```

迁移前置条件不满足时，Skill 不会移动任何文件。
