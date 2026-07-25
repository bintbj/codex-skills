# `orchestrate-long-task` 多 Mission 隔离设计

日期：2026-07-26

## 目标

把 `orchestrate-long-task` 从“一个仓库只能承载一个长任务”升级为可在
同一仓库并行管理多个长任务。每个任务由“仓库地址 + mission ID”唯一
定位，并在独立 Git 分支或 worktree 中执行。新账号即使没有旧对话记录，
也能只凭这两个标识取得原规划、当前进度、验证证据和下一步动作。

本次设计保持以下原则：

- Git 是跨账号共享的唯一事实源，聊天记录不是状态。
- 固定流程由 Skill 内置，用户只提供仓库无法推断的事实和授权。
- 不自动登录、共享凭据、合并额度或绕过使用限制。
- 不引入电脑级全局任务注册表，避免形成无法随仓库同步的第二状态源。

## 方案选择

采用“仓库内多 mission 命名空间 + mission 专属 Git 分支”的方案。

仅增加 mission 目录可以隔离编排文件，却不能隔离同一工作树中的代码
修改。电脑级全局注册表可以提高发现能力，但不能可靠跨电脑或跨账号同步。
专属分支或 worktree 同时隔离控制状态和代码修改，并允许通过确定性分支名
在新克隆中直接恢复任务。

## 唯一标识

### Repository ID

优先从 `origin` remote 读取仓库地址。规范化规则如下：

1. 将 `git@host:owner/repo.git` 与 `ssh://git@host/owner/repo.git` 转换为
   与 HTTPS 相同的 `host/owner/repo` 形式。
2. 主机名转为小写；移除凭据、端口的默认表示、查询参数、片段、首尾斜线
   和结尾 `.git`。
3. 本地或 `file://` remote 使用解析后的绝对路径。
4. 无法可靠规范化时停止并报告，不猜测两个地址相同。

`repository_url` 保存可供下一账号访问的原始 remote 地址；
`repository_id` 保存规范化结果并用于验证。初始化跨账号任务时必须存在
可验证的 remote；没有 remote 时要求用户先选择或添加远程仓库。

### Mission ID

mission ID 必须匹配：

```text
[a-z0-9][a-z0-9-]{0,62}
```

禁止大写字母、空格、斜线、反斜线、`.`、`..` 和绝对路径，确保 mission
ID 可以安全地同时用于目录名和分支名。

默认专属分支为：

```text
codex/mission/<mission-id>
```

目录名、`state.json` 中的 `mission_id`、请求的 mission ID 和分支后缀
必须一致。

## 仓库结构

```text
.task-orchestrator/
└── missions/
    ├── build-api-v2/
    │   ├── mission.md
    │   ├── plan.md
    │   ├── state.json
    │   ├── tasks/
    │   ├── decisions/
    │   ├── handoffs/
    │   │   └── latest.md
    │   └── archive/
    └── redesign-console/
        └── ...
```

不创建顶层 `current`, `latest` 或默认 mission 指针。此类可变指针会在并行
分支之间产生歧义。Skill 通过显式 mission ID、当前确定性分支或扫描唯一
mission 目录来定位任务。

同一集成分支可以包含多个 mission 目录；一个活跃 mission 的工作分支只需
包含自身可见的任务状态。不同 mission 不得共享 `state.json`、任务目录、
决策目录、交接文件或归档目录。

## 状态结构

每个 mission 的 `state.json` 在现有字段基础上增加：

```json
{
  "schema_version": 2,
  "mission_id": "build-api-v2",
  "repository_url": "https://github.com/example/project.git",
  "repository_id": "github.com/example/project",
  "base_branch": "main",
  "working_branch": "codex/mission/build-api-v2"
}
```

现有目标、阶段、推理强度、当前任务、检查点、阻塞和验证字段继续保留。
验证器必须确认：

- mission 路径、请求参数和状态字段一致；
- 当前仓库的规范化 remote 与 `repository_id` 一致；
- 当前分支与 `working_branch` 一致；
- `base_branch` 不属于 `codex/mission/*`；
- `base_commit` 和 `last_checkpoint_commit` 存在；
- 当前任务只从该 mission 的 `tasks/` 读取；
- `--require-clean` 时不存在未提交修改；
- 高推理阶段仍使用 `recommended_reasoning=high`。

## 操作与数据流

### 初始化新 Mission

用户在目标仓库输入：

```text
$orchestrate-long-task 接管当前项目 mission build-api-v2
```

Skill 执行：

1. 验证当前目录属于 Git 仓库、工作区干净且 `origin` 可识别。
2. 验证 mission ID，并拒绝已存在的 mission 目录或远程专属分支。
3. 确认当前分支是用户选择的集成基线分支；如果当前分支已经匹配
   `codex/mission/*`，停止并要求选择基线，禁止从另一个活跃 mission
   派生新 mission。
4. 从该基线创建或切换到 `codex/mission/build-api-v2`，并记录
   `base_branch` 与 `base_commit`。Git 分支操作由 Codex 明确执行，辅助
   脚本不隐式切换分支。
5. 在 `.task-orchestrator/missions/build-api-v2/` 创建模板。
6. 写入 repository ID、mission ID、基线分支、基线提交和工作分支。
7. 根据仓库证据形成 mission、计划、首个任务契约和初始交接。
8. 验证、提交并推送专属分支。

如果 mission ID 未提供，Skill 可以根据明确目标建议一个 ID，但必须在创建
目录和分支前让用户确认，因为该 ID 是持久化外部标识。

### 当前账号继续

用户输入：

```text
$orchestrate-long-task 继续 mission build-api-v2
```

选择规则按以下顺序执行：

1. 显式 mission ID；
2. 当前分支名中的 `codex/mission/<mission-id>`；
3. 当前仓库中唯一的 mission 目录；
4. 如果仍有多个候选，只列出 ID 并询问一次，不自动选择。

定位后验证双重标识，读取 mission、计划、状态、当前任务、决策和交接，再按
原计划继续。只有协议规定的失败、矛盾、接口变化或范围变化才进入重新规划。

### 原账号准备交接

用户输入：

```text
$orchestrate-long-task 准备交接 mission build-api-v2
```

Skill 完成最小安全步骤，更新该 mission 的证据和状态，生成仅属于该 mission
的 `handoffs/latest.md`，运行验证，提交并推送专属分支。只有确认远程分支已
包含最新 checkpoint 后，才返回：

```text
$orchestrate-long-task 接手 repo=<repository-url> mission=build-api-v2
```

交接命令不得省略 repository URL 或 mission ID。

### 新账号或新电脑接手

用户输入完整定位命令。Skill 根据环境执行：

- 当前目录已是目标仓库：获取远程专属分支并安全切换；
- 本地已有目标仓库但不在当前目录：在用户允许的工作区中定位后打开；
- 本地没有仓库：按 repository URL 克隆或创建 worktree，默认检出
  `codex/mission/<mission-id>`；目标路径存在冲突时询问一次；
- 没有仓库地址或 mission ID：只询问缺失的定位信息。

随后执行 `git fetch` 和可快进更新，禁止用 reset 覆盖本地状态。验证
repository ID、mission ID、分支、提交和工作区后，读取持久化规划并从
`next_action` 继续。认证失败时要求用户完成正常 Git 认证，不处理凭据。

### 多 Mission 并行

每个 mission 使用独立分支。需要在同一台电脑同时工作时，为每个分支创建
独立 worktree。不同 mission 可以并行修改相同源文件，但在最终集成时必须
通过正常 Git 合并解决冲突；Skill 不把目录隔离描述成无冲突保证。

进入集成前使用高推理，逐个验证 mission 的验收证据、基线关系和变更范围。
控制状态随各自分支保留，便于审计。

## CLI 与模块边界

保持三个现有脚本名称，并统一增加必需的 mission 参数：

```text
init_workspace.py TARGET --mission MISSION_ID
validate_workspace.py TARGET --mission MISSION_ID [--require-clean]
render_handoff.py TARGET --mission MISSION_ID
```

新增：

```text
migrate_workspace.py TARGET --mission MISSION_ID
```

抽取一个仅使用 Python 标准库的共享模块，负责：

- mission ID 验证；
- mission 根目录解析；
- Git remote 读取和 repository ID 规范化；
- 确定性分支名生成；
- mission 自动发现和歧义报告。

业务脚本不得自行登录、推送、删除分支、执行强制更新或猜测认证信息。

## 旧结构迁移

旧布局 `.task-orchestrator/{mission.md,state.json,...}` 不再作为可执行状态
直接读取。检测到旧布局时返回明确迁移提示，禁止静默移动。

迁移前必须满足：

- 旧工作区通过旧结构验证；
- Git 工作区干净；
- 目标 mission ID 合法且目标目录不存在；
- 当前分支已经是对应 mission 专属分支；
- 存在可验证 remote。

迁移脚本只移动已知控制文件到
`.task-orchestrator/missions/<mission-id>/`，补充 schema v2 定位字段，
保留同一提交中的可恢复历史。任何前置检查失败都不修改文件。迁移完成后必须
运行新版验证器、提交并推送。

旧短命令在新版布局只有一个 mission 或当前处于确定性 mission 分支时继续
可用；它们不绕过显式迁移。

## 错误处理

以下情况必须停止，不得自行选择或覆盖：

- mission ID 非法或目标 mission 已存在；
- 多个 mission 候选但用户未指定；
- repository ID、mission ID、目录或分支不一致；
- 本地存在无法解释的未提交修改；
- 更新不是 fast-forward；
- checkpoint 提交不存在或远程分支未包含最新交接；
- 旧布局迁移目标已存在；
- Git remote 缺失、无法解析或无权访问；
- 目标克隆目录已存在且不是同一仓库。

错误信息必须指出检测到的值、期望值和下一项安全操作，但不得输出凭据。

## Skill 交互规则

Skill 内置安装后流程、定位优先级、文件清单、状态机、推理强度和交接格式。
用户不需要重复这些内容。

可靠的最短入口为：

```text
# 首次账号
$orchestrate-long-task 接管当前项目 mission=<mission-id>

# 同账号或已打开正确 mission 分支
$orchestrate-long-task 继续

# 原账号退出前
$orchestrate-long-task 准备交接 mission=<mission-id>

# 新账号或新电脑
$orchestrate-long-task 接手 repo=<repository-url> mission=<mission-id>
```

只在 mission ID 首次命名、克隆目标路径冲突、产品决策、外部或不可逆操作
授权、认证或真实状态冲突时询问用户。

## 测试与验收

自动化测试至少覆盖：

1. 同一仓库初始化两个合法 mission，状态目录互不覆盖。
2. 非法、路径穿越和重复 mission ID 被拒绝且不产生文件。
3. SSH、HTTPS 和本地 remote 的 repository ID 规范化。
4. 请求 ID、目录 ID、状态 ID、remote 或分支不一致时验证失败。
5. 每个 mission 的任务查找、交接生成和归档互不影响。
6. 多 mission 且无显式或分支提示时报告歧义。
7. 单 mission 和确定性分支可以自动定位。
8. 旧布局迁移成功、目标冲突拒绝、前置失败不修改文件。
9. 临时 bare remote 中推送 mission 分支，再从全新 clone 恢复并验证。
10. `--require-clean`、checkpoint 和高推理阶段约束继续生效。
11. README 与 Skill 包含完整安装、初始化、继续、交接和新账号接手示例。
12. `quick_validate.py` 通过，Skill 仍不依赖 Python 第三方运行库。

完成标准：

- 所有自动化测试通过；
- 新旧布局边界明确且没有静默破坏性迁移；
- 两个并行 mission 不共享控制状态或工作分支；
- 新账号只凭可访问的仓库地址和 mission ID 能恢复原规划；
- 公开仓库、本机安装版本和验证提交一致；
- 最终向用户提供完整中文操作指南和故障处理说明。
