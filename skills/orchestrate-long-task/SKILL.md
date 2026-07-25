---
name: orchestrate-long-task
description: Migrate, coordinate, resume, checkpoint, hand off, replan, verify, and integrate very large Codex tasks across accounts, chats, models, or reasoning levels using Git-backed, mission-isolated durable state. Use when a task may outlast one account's usage, when several long tasks share a repository, or when a worker must resume a task by repository address and mission ID. Do not use for small self-contained tasks.
---

# Orchestrate Long Task

Treat Git and `.task-orchestrator/missions/<mission-id>/` as the source of
truth; chats are temporary. Each mission uses the deterministic branch
`codex/mission/<mission-id>`. Do not let missions share a state directory or
working branch.

Resolve `SKILL_ROOT` to the directory containing this `SKILL.md`. Run bundled
scripts from `SKILL_ROOT/scripts/`; never expect them to exist in the target
project.

Read `references/orchestration-protocol.md` before initialize, resume, replan,
integrate, or migrate. Read `references/state-schema.md` before editing
coordination files.

## Locate the mission

Use this priority order:

1. Explicit `mission=<id>`.
2. Current branch name `codex/mission/<id>`.
3. The only directory under `.task-orchestrator/missions/`.
4. If multiple missions remain, list their IDs and ask which one to use.

For a new account with no local clone, require both `repo=<repository-url>` and
`mission=<id>`. Clone or fetch the repository normally, check out
`codex/mission/<id>`, then run the validator. Never guess a repository or
mission from chat history. Stop on a dirty tree, non-fast-forward update,
repository mismatch, mission mismatch, branch mismatch, or missing checkpoint.

## Operations

- **Initialize:** Require `mission=<id>`. Start from a non-mission base branch,
  create `codex/mission/<id>`, then run
  `python3 "$SKILL_ROOT/scripts/init_workspace.py" <project> --mission <id> --base-branch <base>`.
  Inspect evidence and write the verified mission, plan, task contracts, state,
  decisions, and initial handoff.
- **Resume:** Read `AGENTS.md`, the selected mission's mission, state, handoff,
  active task, and decisions. Run
  `python3 "$SKILL_ROOT/scripts/validate_workspace.py" <project> --mission <id> --require-clean`.
  Continue only the recorded `next_action`.
- **Execute:** Perform one ready task in the selected mission. Honor owned and
  forbidden paths, run acceptance commands, then checkpoint a portable commit.
- **Handoff:** On a usage warning or requested account switch, finish the
  smallest safe step, record evidence, run
  `python3 "$SKILL_ROOT/scripts/render_handoff.py" <project> --mission <id>`,
  validate, commit, push the mission branch, and return the generated complete
  resume command.
- **Migrate:** For an old single-task layout, first create and check out its
  mission branch, then run
  `python3 "$SKILL_ROOT/scripts/migrate_workspace.py" <project> --mission <id> --base-branch <base>`.
  Never silently move legacy files.
- **Replan:** Use high reasoning after two failures of one criterion, a
  contradiction, an interface change, or a scope change.
- **Integrate:** Use high reasoning and mark complete only after all criteria
  have evidence and branch integration is verified.

Do not ask the user to restate this workflow. Inspect the repository and infer
all discoverable facts. Ask only for a missing repository address or mission
ID, a missing mission or acceptance criterion, an unresolved product choice,
permission for an external or destructive action, or a real state conflict.

Use low reasoning for bounded implementation and specified checks. Use high
reasoning for planning, replan, integration, and final verification. Never
store credentials or private chat transcripts in coordination files. Do not
automate login or quota bypass.
