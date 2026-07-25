import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import validate_workspace
import workspace


REQUIRED_LEGACY = ("mission.md", "plan.md", "state.json", "handoffs/latest.md")


def migrate(target: Path, mission_id: str, base_branch: str):
    target = target.resolve()
    mission_id = workspace.validate_mission_id(mission_id)
    if not base_branch or base_branch.startswith(workspace.MISSION_PREFIX):
        raise ValueError("base branch must not be a mission branch")
    root = workspace.control_root(target)
    if not all((root / name).is_file() for name in REQUIRED_LEGACY):
        raise ValueError("legacy workspace is incomplete")
    destination = workspace.mission_root(target, mission_id)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    metadata = workspace.repository_metadata(target)
    git_data = workspace.git_metadata(target)
    expected_branch = workspace.branch_for(mission_id)
    if git_data["working_branch"] != expected_branch:
        raise ValueError(f"current branch must be {expected_branch}")
    if workspace.git(target, "status", "--porcelain"):
        raise ValueError("working tree must be clean before migration")
    try:
        legacy_state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid legacy state.json: {error.msg}") from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    try:
        for item in workspace.LEGACY_ITEMS:
            source = root / item
            if not source.exists():
                continue
            copied = destination / item
            if source.is_dir():
                shutil.copytree(source, copied)
            else:
                shutil.copy2(source, copied)
        state_path = destination / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(metadata)
        state.update(git_data)
        state.update({
            "schema_version": 2,
            "mission_id": mission_id,
            "base_branch": base_branch,
            "working_branch": expected_branch,
            "last_checkpoint_commit": state.get("last_checkpoint_commit") or git_data["base_commit"],
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        errors = validate_workspace.validate_workspace(target, mission_id)
        if errors:
            raise ValueError("\n".join(errors))
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    for item in workspace.LEGACY_ITEMS:
        source = root / item
        if source.is_dir():
            shutil.rmtree(source)
        elif source.exists():
            source.unlink()
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--base-branch", required=True)
    args = parser.parse_args(argv)
    try:
        print(migrate(args.target, args.mission, args.base_branch))
        return 0
    except (FileExistsError, ValueError) as error:
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
