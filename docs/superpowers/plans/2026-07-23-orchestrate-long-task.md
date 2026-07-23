# Orchestrate Long Task 实施计划

> **供智能体执行者使用：**必须使用 `superpowers:subagent-driven-development`
>（推荐）或 `superpowers:executing-plans`，逐项执行本计划。所有步骤使用
> checkbox（`- [ ]`）追踪。

**目标：**创建并公开发布 `orchestrate-long-task` Skill，使超大任务能够在
不同账号、对话和推理强度之间通过 Git 检查点安全迁移和持续执行。

**架构：**Skill 通过精简的 `SKILL.md` 定义编排协议，通过三个仅依赖 Python
标准库的脚本初始化、验证和生成交接状态。目标项目中的
`.task-orchestrator/` 是持久化控制平面，Git 提交是跨账号共享的唯一事实
来源。

**技术栈：**Markdown、YAML、Python 3.10+ 标准库、`unittest`、Git、GitHub
CLI。

## 全局约束

- Skill 名称必须是 `orchestrate-long-task`。
- 远程仓库必须是公开的 `bintbj/codex-skills`。
- 仓库必须使用 MIT 许可证。
- 运行时状态必须写入目标项目的 `.task-orchestrator/`。
- 脚本不得依赖任何第三方 Python 包。
- 脚本不得自动提交、推送、切换分支或登录账号。
- 不得发布凭证、令牌、私钥或本地任务数据。
- 不得把未通过验证的任务标记为完成。
- 高推理用于规划、重规划、重复失败、集成和最终验收；边界明确的执行默认
  使用低推理。

---

## 文件职责

- `README.md`：说明仓库用途、安装入口、快速开始与安全边界。
- `LICENSE`：MIT 许可证全文。
- `skills/orchestrate-long-task/SKILL.md`：触发条件和工作流指令。
- `skills/orchestrate-long-task/agents/openai.yaml`：Skill UI 元数据。
- `skills/orchestrate-long-task/references/orchestration-protocol.md`：完整状态
  机、角色、推理强度和升级规则。
- `skills/orchestrate-long-task/references/state-schema.md`：`state.json`、任务
  契约和交接文件的结构约束。
- `skills/orchestrate-long-task/assets/workspace-template/`：初始化到目标项目的
  模板。
- `skills/orchestrate-long-task/scripts/init_workspace.py`：安全复制模板并记录
  Git 元数据。
- `skills/orchestrate-long-task/scripts/validate_workspace.py`：验证文件结构、
  状态约束及 Git 一致性。
- `skills/orchestrate-long-task/scripts/render_handoff.py`：归档旧交接并确定性
  生成新交接。
- `tests/test_orchestrate_long_task.py`：三个脚本的单元和端到端测试。

---

### Task 1：建立公开 Skills 仓库骨架和 Skill 契约

**文件：**

- 创建：`README.md`
- 创建：`LICENSE`
- 创建：`skills/orchestrate-long-task/SKILL.md`
- 创建：`skills/orchestrate-long-task/agents/openai.yaml`
- 创建：`skills/orchestrate-long-task/references/orchestration-protocol.md`
- 创建：`skills/orchestrate-long-task/references/state-schema.md`
- 修改：`docs/superpowers/specs/2026-07-23-orchestrate-long-task-design.md`

**接口：**

- 输入：已经批准的中文设计文档。
- 产出：能够被 Codex 发现的 Skill 元数据、运行协议和状态结构说明。

- [ ] **Step 1：用官方初始化脚本创建 Skill 骨架**

运行：

```bash
python3 /Users/tangbin/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  orchestrate-long-task \
  --path skills \
  --resources scripts,references,assets \
  --interface 'display_name=Orchestrate Long Task' \
  --interface 'short_description=Safely continue large tasks across accounts' \
  --interface 'default_prompt=Use $orchestrate-long-task to migrate or resume this large task with Git-backed checkpoints.'
```

预期：创建 `skills/orchestrate-long-task/`，包含 `SKILL.md`、
`agents/openai.yaml` 和三个资源目录。

- [ ] **Step 2：写入精简的 Skill 主流程**

将 `skills/orchestrate-long-task/SKILL.md` 写为：

```markdown
---
name: orchestrate-long-task
description: Migrate, coordinate, resume, checkpoint, hand off, replan, verify, and integrate very large Codex tasks across accounts, chats, models, or reasoning levels using Git-backed durable state. Use when a task is already in progress and may outlast one account's available usage, when the user asks to prepare or resume a cross-account handoff, or when multiple Codex workers must share one auditable task plan. Do not use for small self-contained tasks.
---

# Orchestrate Long Task

Treat Git and `.task-orchestrator/` as the source of truth. Treat chat history as
temporary context.

## Choose the operation

- No `.task-orchestrator/`: initialize the ongoing task.
- Existing state and a new account or chat: resume.
- Completed atomic task: checkpoint.
- Usage warning or requested account switch: hand off.
- Two failures, contradictory state, interface change, or scope change: replan.
- All required tasks complete: integrate and perform final verification.

Read `references/orchestration-protocol.md` before initialize, resume, replan,
or integrate. Read `references/state-schema.md` before writing coordination
files.

## Initialize

1. Inspect conversation context, repository instructions, Git history, working
   tree, plans, tests, and existing evidence.
2. Separate verified facts, inferences, and missing information.
3. Run `python3 scripts/init_workspace.py <target-project>`.
4. Replace bootstrap content with the verified mission, plan, task contracts,
   decisions, state, and initial handoff.
5. Run `python3 scripts/validate_workspace.py <target-project>`.

Do not initialize Git without user authorization. Do not overwrite an existing
`.task-orchestrator/`.

## Resume

1. Read `AGENTS.md`, `mission.md`, `state.json`, `handoffs/latest.md`, the
   active task, and referenced decisions.
2. Run `python3 scripts/validate_workspace.py <target-project> --require-clean`.
3. Stop on unexplained branch, commit, task, or working-tree divergence.
4. Continue only the recorded `next_action`.

## Execute and checkpoint

Execute one ready task contract at a time. Respect owned and forbidden paths.
Run every acceptance command. After a task, decision, interface change, or
verification change, update state and create a portable Git commit.

Use low reasoning for bounded execution and specified verification. Recommend
high reasoning for initial planning, dependency or interface design, two
failures of the same criterion, architecture changes, integration, and final
acceptance.

## Hand off

On a usage warning or account switch:

1. Finish the smallest safe step.
2. Record verification evidence and unresolved risks.
3. Create a clearly labeled WIP commit if valuable work is incomplete.
4. Run `python3 scripts/render_handoff.py <target-project>`.
5. Run the validator again and return a compact resume prompt.

Never wait for hard quota exhaustion before the first durable checkpoint.
Never place credentials, tokens, private keys, or private chat transcripts in
coordination files.

## Complete

Mark the mission complete only after dependency, ancestry, conflict, full-test,
mission-criterion, and blocker checks all have recorded evidence.
```

- [ ] **Step 3：写入协议和状态结构参考**

在 `references/orchestration-protocol.md` 中完整记录设计文档的状态机、四种
逻辑角色、推理强度选择、操作流程、两次失败升级规则和故障处理。不得复制
`SKILL.md` 的触发描述。

在 `references/state-schema.md` 中记录：

```text
mission_status: draft | active | blocked | complete
phase: bootstrap | plan | execute | verify | checkpoint | handoff |
       replan | integrate | final_verify | complete | blocked
recommended_reasoning: low | high
current_task: null | "TASK-NNN"
base_commit: null | Git commit
working_branch: null | branch name | "DETACHED"
last_checkpoint_commit: null | Git commit
next_action: non-empty string
blocked: boolean
blockers: array of strings
failed_attempts: non-negative integer
updated_at: UTC ISO-8601 string ending in Z
```

同时规定任务文件必须含有 `Objective`、`Prerequisites`、`Owned Paths`、
`Forbidden Paths`、`Constraints`、`Acceptance Commands`、`Evidence`、
`Dependencies` 和 `Status` 标题。

- [ ] **Step 4：创建仓库说明和 MIT 许可证**

`README.md` 必须包含：

```markdown
# Codex Skills

Reusable personal Codex Skills maintained by bintbj.

## Available skills

### orchestrate-long-task

Safely migrate and continue very large tasks across Codex accounts, chats,
models, and reasoning levels using Git-backed checkpoints.

Install from:
https://github.com/bintbj/codex-skills/tree/main/skills/orchestrate-long-task

Ask Codex to install that path with `$skill-installer`, then invoke
`$orchestrate-long-task` inside the project that owns the task.

The Skill does not share credentials, automate account login, combine account
quotas, or bypass rate limits.
```

`LICENSE` 使用标准 MIT License，并将版权行写为：

```text
Copyright (c) 2026 bintbj
```

- [ ] **Step 5：验证 Skill 元数据**

运行：

```bash
python3 /Users/tangbin/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/orchestrate-long-task
```

预期：输出验证成功，且不存在 YAML frontmatter、命名或目录错误。

- [ ] **Step 6：提交骨架和契约**

```bash
git add README.md LICENSE skills/orchestrate-long-task \
  docs/superpowers/specs/2026-07-23-orchestrate-long-task-design.md
git commit -m "add orchestrate long task skill contract"
```

---

### Task 2：用测试驱动实现运行时模板和安全初始化

**文件：**

- 创建：`skills/orchestrate-long-task/assets/workspace-template/mission.md`
- 创建：`skills/orchestrate-long-task/assets/workspace-template/plan.md`
- 创建：`skills/orchestrate-long-task/assets/workspace-template/state.json`
- 创建：`skills/orchestrate-long-task/assets/workspace-template/tasks/TASK-template.md`
- 创建：`skills/orchestrate-long-task/assets/workspace-template/decisions/ADR-template.md`
- 创建：`skills/orchestrate-long-task/assets/workspace-template/handoffs/latest.md`
- 创建：`skills/orchestrate-long-task/scripts/init_workspace.py`
- 创建：`tests/test_orchestrate_long_task.py`

**接口：**

- 产出：`initialize(target: Path, template_root: Path) -> Path`
- 产出：`git_metadata(target: Path) -> dict[str, str | None]`
- 产出：CLI `init_workspace.py TARGET`，成功返回 0，冲突返回 1。

- [ ] **Step 1：写初始化失败测试**

在 `tests/test_orchestrate_long_task.py` 中创建
`InitWorkspaceTests(unittest.TestCase)`，至少加入：

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL_DIR = (
    Path(__file__).resolve().parents[1] / "skills" / "orchestrate-long-task"
)
SCRIPTS_DIR = SKILL_DIR / "scripts"
TEMPLATE_ROOT = SKILL_DIR / "assets" / "workspace-template"
sys.path.insert(0, str(SCRIPTS_DIR))

import init_workspace

def test_initialize_copies_template_and_records_git(self):
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"],
                       cwd=target, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"],
                       cwd=target, check=True)
        (target / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "seed.txt"], cwd=target, check=True)
        subprocess.run(["git", "commit", "-m", "seed"], cwd=target, check=True,
                       capture_output=True, text=True)

        workspace = init_workspace.initialize(target, TEMPLATE_ROOT)
        state = json.loads((workspace / "state.json").read_text())

        self.assertEqual(workspace, target / ".task-orchestrator")
        self.assertEqual(state["phase"], "bootstrap")
        self.assertEqual(state["working_branch"], "main")
        self.assertRegex(state["base_commit"], r"^[0-9a-f]{40}$")

def test_initialize_refuses_to_overwrite(self):
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        (target / ".task-orchestrator").mkdir()
        with self.assertRaises(FileExistsError):
            init_workspace.initialize(target, TEMPLATE_ROOT)
```

- [ ] **Step 2：运行测试并确认失败**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.InitWorkspaceTests -v
```

预期：因为 `init_workspace.py` 或所需函数尚不存在而失败。

- [ ] **Step 3：写入可解析的 bootstrap 模板**

`state.json` 使用以下完整初始状态：

```json
{
  "schema_version": 1,
  "mission_status": "draft",
  "phase": "bootstrap",
  "recommended_reasoning": "high",
  "current_task": null,
  "base_commit": null,
  "working_branch": null,
  "last_checkpoint_commit": null,
  "next_action": "Capture the verified mission and create the first task contract.",
  "blocked": false,
  "blockers": [],
  "failed_attempts": 0,
  "updated_at": "1970-01-01T00:00:00Z"
}
```

其余 Markdown 模板必须包含设计规定的完整标题。初始正文使用可验证的状态
陈述，例如 `Status: draft; verified content has not been captured.`，不得使用
未完成占位标记。

- [ ] **Step 4：实现最小初始化脚本**

`init_workspace.py` 使用：

```python
def _git(target: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args], cwd=target, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None

def git_metadata(target: Path) -> dict[str, str | None]:
    root = _git(target, "rev-parse", "--show-toplevel")
    if root is None:
        return {"base_commit": None, "working_branch": None}
    commit = _git(target, "rev-parse", "HEAD")
    branch = _git(target, "branch", "--show-current")
    return {
        "base_commit": commit,
        "working_branch": branch or "DETACHED",
    }

def initialize(target: Path, template_root: Path) -> Path:
    target = target.resolve()
    workspace = target / ".task-orchestrator"
    if workspace.exists():
        raise FileExistsError(f"Refusing to overwrite {workspace}")
    if not target.is_dir():
        raise NotADirectoryError(target)
    shutil.copytree(template_root, workspace)
    state_path = workspace / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(git_metadata(target))
    state["last_checkpoint_commit"] = state["base_commit"]
    state["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return workspace
```

`main()` 使用 `argparse`，默认模板路径为脚本上一级目录下的
`assets/workspace-template`，捕获预期的文件系统错误并返回 1。

- [ ] **Step 5：运行初始化测试并确认通过**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.InitWorkspaceTests -v
```

预期：两个测试均为 `ok`。

- [ ] **Step 6：提交初始化功能**

```bash
git add skills/orchestrate-long-task/assets \
  skills/orchestrate-long-task/scripts/init_workspace.py \
  tests/test_orchestrate_long_task.py
git commit -m "add durable task workspace initialization"
```

---

### Task 3：用测试驱动实现状态和 Git 一致性验证

**文件：**

- 创建：`skills/orchestrate-long-task/scripts/validate_workspace.py`
- 修改：`tests/test_orchestrate_long_task.py`

**接口：**

- 产出：`validate_workspace(target: Path, require_clean: bool = False) -> list[str]`
- 产出：CLI `validate_workspace.py TARGET [--require-clean]`；无错误返回 0，
  有错误逐行输出并返回 1。

- [ ] **Step 1：写验证器失败测试**

增加 `ValidateWorkspaceTests`，覆盖：

```python
def test_valid_bootstrap_workspace_has_no_errors(self):
    target = self.make_initialized_repo()
    self.assertEqual(validate_workspace.validate_workspace(target), [])

def test_missing_active_task_is_reported(self):
    target = self.make_initialized_repo()
    state_path = target / ".task-orchestrator/state.json"
    state = json.loads(state_path.read_text())
    state.update({
        "mission_status": "active",
        "phase": "execute",
        "recommended_reasoning": "low",
        "current_task": "TASK-001",
        "next_action": "Execute TASK-001.",
    })
    state_path.write_text(json.dumps(state), encoding="utf-8")
    errors = validate_workspace.validate_workspace(target)
    self.assertIn("Missing active task file: TASK-001.md", errors)

def test_require_clean_reports_dirty_tree(self):
    target = self.make_initialized_repo(commit_workspace=True)
    (target / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    errors = validate_workspace.validate_workspace(target, require_clean=True)
    self.assertTrue(any("working tree is not clean" in error for error in errors))
```

- [ ] **Step 2：运行验证器测试并确认失败**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.ValidateWorkspaceTests -v
```

预期：因为验证模块尚不存在而失败。

- [ ] **Step 3：实现结构与跨字段验证**

实现常量：

```python
MISSION_STATUSES = {"draft", "active", "blocked", "complete"}
PHASES = {
    "bootstrap", "plan", "execute", "verify", "checkpoint", "handoff",
    "replan", "integrate", "final_verify", "complete", "blocked",
}
REASONING_LEVELS = {"low", "high"}
HIGH_REASONING_PHASES = {"plan", "replan", "integrate", "final_verify"}
REQUIRED_FIELDS = {
    "schema_version": int,
    "mission_status": str,
    "phase": str,
    "recommended_reasoning": str,
    "current_task": (str, type(None)),
    "base_commit": (str, type(None)),
    "working_branch": (str, type(None)),
    "last_checkpoint_commit": (str, type(None)),
    "next_action": str,
    "blocked": bool,
    "blockers": list,
    "failed_attempts": int,
    "updated_at": str,
}
```

`validate_workspace()` 必须检查：

- `.task-orchestrator/` 和三份核心文件存在；
- JSON 可解析；
- 必填字段和类型正确；
- 枚举、非空 `next_action`、非负 `failed_attempts`；
- `blocked` 与 `blockers` 一致；
- `complete` 状态与阶段一致；
- 高推理阶段推荐值为 `high`；
- 当前任务文件存在并包含全部规定标题；
- 记录的分支与实际分支一致；
- Git 能解析记录的基础提交和检查点提交；
- `--require-clean` 时 `git status --porcelain` 为空。

- [ ] **Step 4：运行验证器测试并修到通过**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.ValidateWorkspaceTests -v
```

预期：全部测试为 `ok`。

- [ ] **Step 5：运行现有全部测试**

运行：

```bash
python3 -m unittest discover -s tests -v
```

预期：初始化与验证测试全部通过。

- [ ] **Step 6：提交验证器**

```bash
git add skills/orchestrate-long-task/scripts/validate_workspace.py \
  tests/test_orchestrate_long_task.py
git commit -m "validate durable task state and git identity"
```

---

### Task 4：用测试驱动实现确定性交接生成

**文件：**

- 创建：`skills/orchestrate-long-task/scripts/render_handoff.py`
- 修改：`tests/test_orchestrate_long_task.py`

**接口：**

- 产出：`render_handoff(target: Path) -> Path`
- 消费：`validate_workspace.validate_workspace(target)`
- 产出：CLI `render_handoff.py TARGET`；验证或文件错误返回 1。

- [ ] **Step 1：写交接生成失败测试**

增加 `RenderHandoffTests`：

```python
def test_render_handoff_uses_state_and_archives_previous_file(self):
    target = self.make_active_repo()
    handoff = render_handoff.render_handoff(target)
    content = handoff.read_text(encoding="utf-8")
    archive = target / ".task-orchestrator/archive"

    self.assertIn("# Latest Handoff", content)
    self.assertIn("TASK-001", content)
    self.assertIn("Execute TASK-001.", content)
    self.assertIn("Recommended reasoning: low", content)
    self.assertEqual(len(list(archive.glob("*.md"))), 1)

def test_render_handoff_refuses_invalid_workspace(self):
    target = self.make_active_repo()
    (target / ".task-orchestrator/tasks/TASK-001.md").unlink()
    with self.assertRaises(ValueError) as context:
        render_handoff.render_handoff(target)
    self.assertIn("Missing active task file", str(context.exception))
```

- [ ] **Step 2：运行交接测试并确认失败**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.RenderHandoffTests -v
```

预期：因为交接模块尚不存在而失败。

- [ ] **Step 3：实现归档与渲染**

实现：

```python
def _bullets(values: list[str], empty: str) -> str:
    return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"

def render_handoff(target: Path) -> Path:
    errors = validate_workspace.validate_workspace(target)
    if errors:
        raise ValueError("\n".join(errors))

    workspace = target.resolve() / ".task-orchestrator"
    state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
    handoff = workspace / "handoffs/latest.md"
    archive_dir = workspace / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    if handoff.exists() and handoff.read_text(encoding="utf-8").strip():
        stamp = re.sub(r"[^0-9]", "", state["updated_at"])[:14] or "unknown"
        archive_path = archive_dir / f"handoff-{stamp}.md"
        suffix = 1
        while archive_path.exists():
            archive_path = archive_dir / f"handoff-{stamp}-{suffix}.md"
            suffix += 1
        shutil.copy2(handoff, archive_path)

    content = f"""# Latest Handoff

Updated at: {state["updated_at"]}
Phase: {state["phase"]}
Mission status: {state["mission_status"]}
Current task: {state["current_task"] or "none"}
Working branch: {state["working_branch"] or "none"}
Base commit: {state["base_commit"] or "none"}
Last checkpoint: {state["last_checkpoint_commit"] or "none"}
Recommended reasoning: {state["recommended_reasoning"]}

## Completed work

{_bullets(state.get("completed_work", []), "No completed work recorded.")}

## Verification

{_bullets(state.get("verification", []), "No verification evidence recorded.")}

## Risks and blockers

{_bullets(state.get("risks", []) + state["blockers"], "No risks recorded.")}

## Required reads

{_bullets(state.get("required_reads", [
    "AGENTS.md",
    ".task-orchestrator/mission.md",
    ".task-orchestrator/state.json",
]), "No required reads recorded.")}

## Next action

{state["next_action"]}
"""
    handoff.write_text(content, encoding="utf-8")
    return handoff
```

- [ ] **Step 4：运行交接测试并修到通过**

运行：

```bash
python3 -m unittest tests.test_orchestrate_long_task.RenderHandoffTests -v
```

预期：两个测试均为 `ok`。

- [ ] **Step 5：运行全部测试**

运行：

```bash
python3 -m unittest discover -s tests -v
```

预期：所有测试通过。

- [ ] **Step 6：提交交接生成器**

```bash
git add skills/orchestrate-long-task/scripts/render_handoff.py \
  tests/test_orchestrate_long_task.py
git commit -m "generate portable account handoffs"
```

---

### Task 5：增加端到端跨工作区恢复测试和使用说明

**文件：**

- 修改：`tests/test_orchestrate_long_task.py`
- 修改：`README.md`
- 修改：`skills/orchestrate-long-task/references/orchestration-protocol.md`

**接口：**

- 消费：三个脚本 CLI。
- 产出：证明第二个 checkout 无需旧对话即可验证并读取下一动作的端到端测试。

- [ ] **Step 1：写端到端失败测试**

加入 `EndToEndTests.test_initialize_checkpoint_handoff_and_resume_in_clone`：

```python
def test_initialize_checkpoint_handoff_and_resume_in_clone(self):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source"
        clone = root / "clone"
        source.mkdir()
        self.init_git_repo(source)
        init_workspace.initialize(source, TEMPLATE_ROOT)
        self.activate_task(source, "TASK-001")
        self.git_commit_all(source, "checkpoint task state")

        self.assertEqual(validate_workspace.validate_workspace(source), [])
        render_handoff.render_handoff(source)
        self.git_commit_all(source, "prepare handoff")

        subprocess.run(["git", "clone", str(source), str(clone)], check=True,
                       capture_output=True, text=True)
        self.assertEqual(validate_workspace.validate_workspace(clone), [])
        handoff = (clone / ".task-orchestrator/handoffs/latest.md").read_text()
        self.assertIn("Execute TASK-001.", handoff)
```

- [ ] **Step 2：运行端到端测试并确认失败**

运行：

```bash
python3 -m unittest \
  tests.test_orchestrate_long_task.EndToEndTests.test_initialize_checkpoint_handoff_and_resume_in_clone \
  -v
```

预期：首次运行因测试辅助函数或克隆一致性尚未完善而失败。

- [ ] **Step 3：补齐测试辅助函数并修复真实缺陷**

只增加测试所需的 `init_git_repo()`、`activate_task()` 和
`git_commit_all()`。如果克隆后的分支、提交或状态验证失败，修复对应生产
代码，不得在测试中跳过检查。

- [ ] **Step 4：补充 README 快速使用流程**

添加以下流程：

```text
1. 在进行中任务的项目内调用 $orchestrate-long-task。
2. 高推理完成 initialize/plan。
3. 切换低推理执行一个原子任务。
4. 每个任务后 checkpoint。
5. 出现额度警告时 handoff 并推送提交。
6. 新账号克隆或拉取仓库后调用 $orchestrate-long-task resume。
7. 集成阶段切换高推理并执行完整验收。
```

明确说明 Codex 无法保证读取个人账号的实时剩余额度，用户应在首次额度预警
时交接，而不是等硬性限额触发。

- [ ] **Step 5：运行全部测试和 Skill 验证**

运行：

```bash
python3 -m unittest discover -s tests -v
python3 /Users/tangbin/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/orchestrate-long-task
```

预期：全部单元测试、端到端测试和 Skill 验证通过。

- [ ] **Step 6：提交端到端验证和文档**

```bash
git add README.md tests/test_orchestrate_long_task.py \
  skills/orchestrate-long-task/references/orchestration-protocol.md
git commit -m "verify cross-account task recovery"
```

---

### Task 6：最终审计并发布公开 GitHub 仓库

**文件：**

- 修改：`docs/superpowers/plans/2026-07-23-orchestrate-long-task.md`

**接口：**

- 输入：已经通过测试和 Skill 验证的本地 `main`。
- 产出：公开仓库 `https://github.com/bintbj/codex-skills`。

- [ ] **Step 1：执行秘密信息和占位符扫描**

运行：

```bash
rg -n --hidden -g '!.git' \
  'BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|ghp_[A-Za-z0-9]+|sk-[A-Za-z0-9]+|T[B]D|T[O]DO|FIXM[E]'
```

预期：没有凭证命中；没有未解决的占位符命中。

- [ ] **Step 2：执行最终验证**

运行：

```bash
python3 -m unittest discover -s tests -v
python3 /Users/tangbin/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/orchestrate-long-task
git diff --check
git status --short --branch
```

预期：测试和 Skill 验证通过，`git diff --check` 无输出，工作区仅包含实施计划
checkbox 状态更新或完全干净。

- [ ] **Step 3：提交最终计划追踪状态（仅在文件发生变化时）**

```bash
git add docs/superpowers/plans/2026-07-23-orchestrate-long-task.md
git diff --cached --quiet || \
  git commit -m "record orchestrate long task implementation status"
```

- [ ] **Step 4：重新认证 GitHub CLI**

运行：

```bash
gh auth login -h github.com
gh auth status
```

预期：账号 `bintbj` 显示为已认证。不得把认证输出写入仓库。

- [ ] **Step 5：创建并推送公开仓库**

先确认远程仓库不存在，然后运行：

```bash
gh repo create bintbj/codex-skills \
  --public \
  --source=. \
  --remote=origin \
  --push
```

预期：创建公开仓库并把本地 `main` 推送为默认分支。如果仓库已经存在，停止
并核实所有权及内容，不得覆盖远程历史。

- [ ] **Step 6：验证远程交付**

运行：

```bash
gh repo view bintbj/codex-skills \
  --json nameWithOwner,visibility,defaultBranchRef,url
git ls-remote --heads origin main
```

预期：

```text
nameWithOwner = bintbj/codex-skills
visibility = PUBLIC
defaultBranchRef.name = main
```

同时打开或读取远程 Skill 路径，确认 `SKILL.md`、三个脚本、模板、参考文件和
测试均存在。

- [ ] **Step 7：报告最终结果**

最终报告必须包含：

- 公开仓库 URL；
- 最终 commit SHA；
- 测试数量和结果；
- Skill 验证结果；
- 安装路径；
- 已知边界：不共享额度、不读取实时剩余额度、不自动登录账号。
