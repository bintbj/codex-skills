import argparse
import json
from pathlib import Path

import workspace


PHASES = {"bootstrap", "plan", "execute", "verify", "checkpoint", "handoff", "replan", "integrate", "final_verify", "complete", "blocked"}
STATUSES = {"draft", "active", "blocked", "complete"}
REQUIRED = {
    "schema_version": int,
    "mission_id": str,
    "repository_url": str,
    "repository_id": str,
    "base_branch": str,
    "mission_status": str,
    "phase": str,
    "recommended_reasoning": str,
    "current_task": (str, type(None)),
    "base_commit": (str, type(None)),
    "working_branch": str,
    "last_checkpoint_commit": (str, type(None)),
    "next_action": str,
    "blocked": bool,
    "blockers": list,
    "failed_attempts": int,
    "updated_at": str,
}
HEADINGS = ["Objective", "Prerequisites", "Owned Paths", "Forbidden Paths", "Constraints", "Acceptance Commands", "Evidence", "Dependencies", "Status"]


def validate_workspace(target: Path, mission_id: str, require_clean=False):
    target = target.resolve()
    errors = []
    try:
        mission_id = workspace.validate_mission_id(mission_id)
    except ValueError as error:
        return [str(error)]
    root = workspace.mission_root(target, mission_id)
    for name in ("mission.md", "plan.md", "state.json", "handoffs/latest.md"):
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    if errors:
        if workspace.legacy_workspace_exists(target):
            errors.append("Legacy workspace detected; run migrate_workspace.py explicitly")
        return errors
    try:
        state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"Invalid state.json: {error.msg}"]
    for name, expected in REQUIRED.items():
        if name not in state:
            errors.append(f"Missing state field: {name}")
        elif not isinstance(state[name], expected):
            errors.append(f"Invalid state field type: {name}")
    if state.get("schema_version") != 2:
        errors.append("Unsupported schema_version; expected 2")
    if state.get("mission_id") != mission_id:
        errors.append("Requested mission differs from state mission_id")
    if state.get("mission_status") not in STATUSES:
        errors.append("Invalid mission_status")
    if state.get("phase") not in PHASES:
        errors.append("Invalid phase")
    if state.get("recommended_reasoning") not in {"low", "high"}:
        errors.append("Invalid recommended_reasoning")
    if not state.get("next_action", "").strip():
        errors.append("next_action must be non-empty")
    if state.get("failed_attempts", 0) < 0:
        errors.append("failed_attempts must be non-negative")
    if state.get("blocked") != bool(state.get("blockers")):
        errors.append("blocked must match blockers")
    if state.get("phase") in {"plan", "replan", "integrate", "final_verify"} and state.get("recommended_reasoning") != "high":
        errors.append("high reasoning required for phase")
    if state.get("base_branch", "").startswith(workspace.MISSION_PREFIX):
        errors.append("base_branch must not be a mission branch")
    expected_branch = workspace.branch_for(mission_id)
    if state.get("working_branch") != expected_branch:
        errors.append("working_branch differs from mission branch")
    try:
        metadata = workspace.repository_metadata(target)
    except ValueError as error:
        errors.append(str(error))
        metadata = None
    if metadata and state.get("repository_id") != metadata["repository_id"]:
        errors.append("Recorded repository differs from origin remote")
    branch = workspace.git(target, "branch", "--show-current")
    if (branch or "DETACHED") != state.get("working_branch"):
        errors.append("Recorded branch differs from Git branch")
    for name in ("base_commit", "last_checkpoint_commit"):
        if state.get(name) and workspace.git(target, "cat-file", "-e", f"{state[name]}^{{commit}}") is None:
            errors.append(f"Recorded commit is missing: {name}")
    task = state.get("current_task")
    if task:
        path = root / "tasks" / f"{task}.md"
        if not path.is_file():
            errors.append(f"Missing active task file: {task}.md")
        else:
            text = path.read_text(encoding="utf-8")
            for heading in HEADINGS:
                if f"## {heading}" not in text:
                    errors.append(f"Task missing heading: {heading}")
    if require_clean and workspace.git(target, "status", "--porcelain"):
        errors.append("working tree is not clean")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args(argv)
    errors = validate_workspace(args.target, args.mission, args.require_clean)
    print("\n".join(errors) if errors else "Workspace valid")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
