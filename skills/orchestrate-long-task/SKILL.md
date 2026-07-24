---
name: orchestrate-long-task
description: Migrate, coordinate, resume, checkpoint, hand off, replan, verify, and integrate very large Codex tasks across accounts, chats, models, or reasoning levels using Git-backed durable state. Use when a task may outlast one account's usage or when workers must share an auditable plan. Do not use for small self-contained tasks.
---

# Orchestrate Long Task

Treat Git and `.task-orchestrator/` as the source of truth; chats are temporary.

Resolve `SKILL_ROOT` to the directory containing this `SKILL.md`. Run bundled
scripts from `SKILL_ROOT/scripts/`; never expect them to exist in the target
project.

Read `references/orchestration-protocol.md` before initialize, resume, replan, or integrate. Read `references/state-schema.md` before editing coordination files.

## Infer the operation

Infer the operation from the user's short request and repository state:

- **Initialize:** “接管当前项目”, “初始化跨账号协作”, or no `.task-orchestrator/`.
- **Resume:** “继续”, “接手当前项目”, “resume”, or an existing `.task-orchestrator/`.
- **Handoff:** “准备交接”, “切换账号”, “handoff”, or the first usage warning.
- **Replan:** “重新规划”, “replan”, or a protocol replan trigger.
- **Integrate:** “收尾”, “完成任务”, “integrate”, or all task contracts are complete.

Do not ask the user to restate this workflow. Inspect the repository and infer
all discoverable facts. Ask only for a missing mission or acceptance criterion,
an unresolved product choice, permission for an external or destructive action,
or a real state conflict. Ask one concise question at a time.

## Operations

- **Initialize:** inspect evidence, run `python3 "$SKILL_ROOT/scripts/init_workspace.py" <project>`, then write a verified mission, task contracts, state, and handoff.
- **Resume:** read `AGENTS.md`, mission, state, handoff, active task, and decisions; run `python3 "$SKILL_ROOT/scripts/validate_workspace.py" <project> --require-clean`; stop on unexplained divergence.
- **Execute:** perform one ready task, honor owned/forbidden paths, run acceptance commands, then checkpoint a portable commit.
- **Handoff:** after a usage warning or requested account switch, finish the smallest safe step, record evidence, run `python3 "$SKILL_ROOT/scripts/render_handoff.py" <project>`, validate again, and return the single-line resume prompt `$orchestrate-long-task 接手当前项目`.
- **Replan:** use high reasoning after two failures of one criterion, a contradiction, an interface change, or a scope change.
- **Integrate:** use high reasoning and mark complete only after all criteria have evidence.

Use low reasoning for bounded implementation and specified checks. Use high reasoning for planning, replan, integration, and final verification. Never store credentials or private chat transcripts in coordination files. Do not automate login or quota bypass.
