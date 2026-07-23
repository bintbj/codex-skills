---
name: orchestrate-long-task
description: Migrate, coordinate, resume, checkpoint, hand off, replan, verify, and integrate very large Codex tasks across accounts, chats, models, or reasoning levels using Git-backed durable state. Use when a task may outlast one account's usage or when workers must share an auditable plan. Do not use for small self-contained tasks.
---

# Orchestrate Long Task

Treat Git and `.task-orchestrator/` as the source of truth; chats are temporary.

Read `references/orchestration-protocol.md` before initialize, resume, replan, or integrate. Read `references/state-schema.md` before editing coordination files.

## Operations

- **Initialize:** inspect evidence, run `python3 scripts/init_workspace.py <project>`, then write a verified mission, task contracts, state, and handoff.
- **Resume:** read `AGENTS.md`, mission, state, handoff, active task, and decisions; run `python3 scripts/validate_workspace.py <project> --require-clean`; stop on unexplained divergence.
- **Execute:** perform one ready task, honor owned/forbidden paths, run acceptance commands, then checkpoint a portable commit.
- **Handoff:** after a usage warning or requested account switch, finish the smallest safe step, record evidence, run `python3 scripts/render_handoff.py <project>`, validate again, and return a resume prompt.
- **Replan:** use high reasoning after two failures of one criterion, a contradiction, an interface change, or a scope change.
- **Integrate:** use high reasoning and mark complete only after all criteria have evidence.

Use low reasoning for bounded implementation and specified checks. Use high reasoning for planning, replan, integration, and final verification. Never store credentials or private chat transcripts in coordination files. Do not automate login or quota bypass.
