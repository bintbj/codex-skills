import argparse
import json
import subprocess
from pathlib import Path

PHASES = {"bootstrap", "plan", "execute", "verify", "checkpoint", "handoff", "replan", "integrate", "final_verify", "complete", "blocked"}
STATUSES = {"draft", "active", "blocked", "complete"}
REQUIRED = {"schema_version": int, "mission_status": str, "phase": str, "recommended_reasoning": str, "current_task": (str, type(None)), "base_commit": (str, type(None)), "working_branch": (str, type(None)), "last_checkpoint_commit": (str, type(None)), "next_action": str, "blocked": bool, "blockers": list, "failed_attempts": int, "updated_at": str}
HEADINGS = ["Objective", "Prerequisites", "Owned Paths", "Forbidden Paths", "Constraints", "Acceptance Commands", "Evidence", "Dependencies", "Status"]

def _git(target, *args):
    result = subprocess.run(["git", *args], cwd=target, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None

def validate_workspace(target: Path, require_clean=False):
    target, root = target.resolve(), target.resolve() / ".task-orchestrator"
    errors = []
    for name in ("mission.md", "plan.md", "state.json", "handoffs/latest.md"):
        if not (root / name).is_file(): errors.append(f"Missing required file: {name}")
    if errors: return errors
    try: state = json.loads((root / "state.json").read_text())
    except json.JSONDecodeError as error: return [f"Invalid state.json: {error.msg}"]
    for name, expected in REQUIRED.items():
        if name not in state: errors.append(f"Missing state field: {name}")
        elif not isinstance(state[name], expected): errors.append(f"Invalid state field type: {name}")
    if state.get("mission_status") not in STATUSES: errors.append("Invalid mission_status")
    if state.get("phase") not in PHASES: errors.append("Invalid phase")
    if state.get("recommended_reasoning") not in {"low", "high"}: errors.append("Invalid recommended_reasoning")
    if not state.get("next_action", "").strip(): errors.append("next_action must be non-empty")
    if state.get("failed_attempts", 0) < 0: errors.append("failed_attempts must be non-negative")
    if state.get("blocked") != bool(state.get("blockers")): errors.append("blocked must match blockers")
    if state.get("phase") in {"plan", "replan", "integrate", "final_verify"} and state.get("recommended_reasoning") != "high": errors.append("high reasoning required for phase")
    task = state.get("current_task")
    if task:
        path = root / "tasks" / f"{task}.md"
        if not path.is_file(): errors.append(f"Missing active task file: {task}.md")
        else:
            text = path.read_text()
            for heading in HEADINGS:
                if f"## {heading}" not in text: errors.append(f"Task missing heading: {heading}")
    branch = _git(target, "branch", "--show-current")
    if state.get("working_branch") and (branch or "DETACHED") != state["working_branch"]: errors.append("Recorded branch differs from Git branch")
    for name in ("base_commit", "last_checkpoint_commit"):
        if state.get(name) and _git(target, "cat-file", "-e", f"{state[name]}^{{commit}}") is None: errors.append(f"Recorded commit is missing: {name}")
    if require_clean and _git(target, "status", "--porcelain"): errors.append("working tree is not clean")
    return errors

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("target", type=Path); parser.add_argument("--require-clean", action="store_true"); args = parser.parse_args(argv)
    errors = validate_workspace(args.target, args.require_clean)
    print("\n".join(errors) if errors else "Workspace valid")
    return 1 if errors else 0

if __name__ == "__main__": raise SystemExit(main())
