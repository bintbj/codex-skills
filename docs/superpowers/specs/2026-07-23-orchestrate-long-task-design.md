# Orchestrate Long Task Skill Design

Date: 2026-07-23

## Purpose

Create a reusable Codex Skill named `orchestrate-long-task` that converts an
already-running, very large task into a durable Git-backed workflow. The
workflow must survive changes in account, chat, model, and reasoning effort
without depending on access to the previous account's conversation history.

The first account may use high reasoning effort to plan, switch to lower
reasoning effort for bounded execution, and hand work to another account when
usage is running low. Roles belong to workflow phases, not to accounts.

## Repository

Publish the Skill in a new public GitHub repository:

```text
bintbj/codex-skills
```

The repository will use the MIT license and initially contain:

```text
codex-skills/
├── README.md
├── LICENSE
├── tests/
│   └── test_orchestrate_long_task.py
└── skills/
    └── orchestrate-long-task/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── scripts/
        │   ├── init_workspace.py
        │   ├── validate_workspace.py
        │   └── render_handoff.py
        ├── references/
        │   ├── orchestration-protocol.md
        │   └── state-schema.md
        └── assets/
            └── workspace-template/
                ├── mission.md
                ├── state.json
                ├── plan.md
                ├── tasks/
                │   └── TASK-template.md
                ├── decisions/
                │   └── ADR-template.md
                └── handoffs/
                    └── latest.md
```

Files such as `README.md` and `LICENSE` belong to the repository root, not to
the Skill folder.

## Design Principles

1. **Git is the source of truth.** Chats are disposable execution contexts.
2. **Failure must be bounded.** Unexpected quota exhaustion may lose the
   current small step, but not the plan or completed work.
3. **Accounts do not own roles.** Any account may plan, execute, verify,
   integrate, or resume.
4. **Reasoning effort follows uncertainty.** High effort is reserved for
   planning, ambiguity, repeated failure, architectural changes, integration,
   and final acceptance.
5. **Execution tasks are atomic.** A worker receives a bounded scope, owned
   paths, dependencies, verification commands, and a definition of done.
6. **State transitions are explicit.** The Skill does not infer completion from
   prose alone.
7. **No hidden machine-local handoff state.** Portable commits and files are
   preferred over Git stash or uncommitted changes.
8. **No quota circumvention automation.** The Skill coordinates authorized
   accounts and supported usage; it does not automate login, credential
   sharing, or rate-limit bypass.

## Runtime Workspace

When initialized inside a target project, the Skill creates:

```text
.task-orchestrator/
├── mission.md
├── state.json
├── plan.md
├── tasks/
├── decisions/
├── handoffs/
│   └── latest.md
└── archive/
```

### `mission.md`

Contains the stable objective, scope, constraints, non-goals, and measurable
completion criteria. A replan may clarify the mission but must not silently
expand it.

### `state.json`

Contains the machine-readable current state. Its required fields are:

```json
{
  "schema_version": 1,
  "mission_status": "active",
  "phase": "execute",
  "recommended_reasoning": "low",
  "current_task": "TASK-001",
  "base_commit": "0123456789abcdef",
  "working_branch": "agent/task-001",
  "last_checkpoint_commit": "0123456789abcdef",
  "next_action": "Implement the validated TASK-001 contract.",
  "blocked": false,
  "blockers": [],
  "failed_attempts": 0,
  "updated_at": "2026-07-23T12:00:00Z"
}
```

The implementation will document allowed enum values and validate field types,
cross-field invariants, referenced task files, Git state, and commit existence.

### `plan.md`

Contains the task graph, dependencies, task status, integration order, and the
reason each task boundary is safe.

### `tasks/TASK-NNN.md`

Each task contract contains:

- objective;
- prerequisites and base commit;
- owned paths;
- forbidden paths;
- implementation constraints;
- acceptance commands;
- expected evidence;
- dependency and integration notes;
- completion status.

### `decisions/`

Stores durable architecture decisions that future accounts must not
re-litigate without an explicit replan.

### `handoffs/latest.md`

Provides the single entry point for a new account. It records:

- mission and current phase;
- branch and commit identities;
- completed work;
- verification results;
- unresolved risks;
- exact next action;
- files that must be read;
- whether high or low reasoning is recommended and why.

Previous handoffs are copied to `archive/` before `latest.md` is replaced.

## State Machine

```text
bootstrap
    ↓
plan (high reasoning)
    ↓
execute (low reasoning by default)
    ↓
verify (low reasoning by default)
    ↓
checkpoint
    ├── next bounded task → execute
    ├── ambiguity or repeated failure → replan (high reasoning)
    ├── usage warning or account switch → handoff
    └── all tasks complete → integrate (high reasoning)
                                      ↓
                                  final verify
                                      ↓
                                    complete
```

Allowed phases are `bootstrap`, `plan`, `execute`, `verify`, `checkpoint`,
`handoff`, `replan`, `integrate`, `final_verify`, `complete`, and `blocked`.

Every phase transition updates `state.json`. Transitions that complete work
also require verification evidence and a Git commit.

## Role and Reasoning Policy

The Skill supports four logical roles within one workflow:

- **Coordinator:** reconstructs the task, establishes the mission, decomposes
  work, and selects safe task boundaries.
- **Worker:** implements exactly one task contract.
- **Verifier:** runs the contract's acceptance checks and records evidence.
- **Integrator:** combines completed tasks, resolves cross-task conflicts, and
  performs final acceptance.

Use high reasoning effort for:

- initial planning or reconstruction;
- dependency and interface design;
- contradictory repository or task state;
- two failed attempts at the same acceptance criterion;
- changes to an approved architecture decision;
- integration and final acceptance.

Use low reasoning effort for:

- implementing an approved atomic task;
- adding bounded tests or documentation;
- running specified verification commands;
- updating checkpoints and handoff records.

The Skill recommends reasoning effort in `state.json` and the handoff, but does
not claim to change account settings automatically.

## Operations

### Initialize

1. Inspect the current conversation context, repository, Git history, working
   tree, existing plans, and tests.
2. Distinguish verified facts from inferred or missing information.
3. Refuse to mark unverified work complete.
4. Create `.task-orchestrator/` from the bundled template.
5. Write the mission, current state, initial plan, first task contracts, and
   initial handoff.
6. Validate the workspace before proceeding.

Initialization must preserve existing user changes and must not initialize Git
inside a target project without user authorization.

### Resume

1. Read `AGENTS.md` and repository-local instructions.
2. Read `mission.md`, `state.json`, `handoffs/latest.md`, the active task, and
   relevant decisions.
3. Compare the recorded branch and commits with actual Git state.
4. Run the workspace validator.
5. Stop on unexplained divergence rather than overwriting either side.
6. Continue the recorded `next_action` using the recommended reasoning effort.

### Execute

1. Select only a ready task whose dependencies are satisfied.
2. Confirm owned and forbidden paths.
3. Make the minimum scoped change.
4. Run the task's acceptance commands.
5. Route to `checkpoint`, `replan`, or `blocked` based on evidence.

### Checkpoint

A lightweight checkpoint is required after:

- an atomic task completes;
- an acceptance result changes;
- a durable decision is made;
- a plan or interface changes;
- a risky operation is about to begin.

The checkpoint records the current diff, verification evidence, state, and
next action. Completed work must be committed. Incomplete but valuable work may
use a clearly labeled WIP commit when an account switch is imminent.

### Handoff

A full handoff is triggered when:

- the user requests account switching;
- the user reports a usage warning;
- the current account is about to stop;
- execution is blocked;
- the workflow enters replan or integration.

The Skill validates the workspace, archives the previous handoff, renders a
new `latest.md`, commits portable state when authorized, and returns a compact
resume prompt for the next account.

### Replan

Replan is required after two failed attempts at the same acceptance criterion,
an invalid task contract, a discovered dependency conflict, or a requested
scope change. Replanning must preserve evidence and explain which previous
assumption changed.

### Integrate

Integration verifies task dependencies, commit ancestry, conflicts, full test
results, mission criteria, and unresolved blockers. The mission may be marked
complete only when every required criterion has recorded evidence.

## Deterministic Scripts

All scripts use Python's standard library and support `--help`.

### `init_workspace.py`

- takes a target project path;
- refuses to overwrite an existing `.task-orchestrator/`;
- copies the bundled template;
- records detected Git metadata when available;
- produces a concise initialization summary.

### `validate_workspace.py`

- validates JSON structure and enum values;
- validates referenced task and handoff files;
- compares recorded branch and commits with Git;
- detects missing required sections and contradictory states;
- exits nonzero with actionable messages on failure.

### `render_handoff.py`

- reads validated state and the active task;
- archives the existing handoff;
- generates `handoffs/latest.md` deterministically;
- does not commit, push, switch branches, or modify source files.

## Failure Handling

- **Unexpected quota exhaustion:** resume from the latest committed checkpoint.
- **Dirty working tree during resume:** report the diff and stop before
  overwriting or switching branches.
- **Recorded commit is missing:** enter `blocked` and request the correct remote,
  branch, or commit.
- **Task and state disagree:** validation fails; high-reasoning replan is
  required.
- **Acceptance fails once:** remain in execution and record the failure.
- **Acceptance fails twice for the same cause:** enter `replan`.
- **Concurrent workers modify overlapping paths:** stop integration and require
  explicit reconciliation.
- **No Git repository:** initialization may create coordination files, but
  portable multi-account handoff remains blocked until Git is initialized and
  a shared remote exists.
- **Secrets detected in coordination files:** stop before commit and require
  removal. Handoffs must not contain credentials, tokens, or private keys.

## Validation Strategy

### Static Skill Validation

Run the official Skill `quick_validate.py` against
`skills/orchestrate-long-task`.

### Script Tests

Use Python `unittest` to cover:

- clean initialization;
- overwrite refusal;
- valid and invalid state schemas;
- missing task references;
- branch or commit divergence;
- deterministic handoff generation;
- handoff archival;
- nonzero exits and actionable errors.

### End-to-End Smoke Test

Create a temporary Git repository and verify:

1. initialize a workspace;
2. populate a mission and atomic task;
3. validate the workspace;
4. simulate execution and create a checkpoint commit;
5. render a handoff;
6. clone or create a second worktree;
7. resume using only repository files;
8. detect an intentional divergence;
9. resolve it and complete final validation.

### Manual Trigger Tests

Confirm the Skill triggers for requests to:

- migrate an ongoing oversized task;
- continue work from another Codex account;
- prepare a quota-safe checkpoint;
- resume a multi-account task;
- replan after repeated failures;
- integrate work produced by multiple accounts.

Confirm it does not trigger for ordinary small, self-contained coding tasks.

Subagent forward-testing is outside the first implementation because no
delegation was requested. Local validation and smoke tests are required before
publication.

## Publishing Workflow

1. Implement and validate locally.
2. Review `git status` and the complete diff.
3. Create an intentional initial commit.
4. Re-authenticate GitHub CLI account `bintbj`.
5. Create `bintbj/codex-skills` as a public repository.
6. Push the validated commit to the default branch.
7. Verify repository visibility, default branch, files, and installation path.

No credentials or local task data may be published.

## Acceptance Criteria

The work is complete when:

1. `bintbj/codex-skills` exists publicly.
2. The repository contains the MIT license and the documented Skill layout.
3. `SKILL.md` has valid frontmatter and concise trigger conditions.
4. All three scripts run with only the Python standard library.
5. Unit tests and the temporary-repository smoke test pass.
6. Official Skill validation passes.
7. A fresh Codex session can initialize or resume from repository artifacts
   without access to the previous account's conversation.
8. The Skill never claims work is complete without verification evidence.
9. The Skill does not automate account login, credential sharing, or quota
   bypass.
