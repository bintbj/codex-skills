import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import workspace


def initialize(target: Path, template_root: Path, mission_id: str, base_branch: str):
    target = target.resolve()
    if not target.is_dir():
        raise NotADirectoryError(target)
    mission_id = workspace.validate_mission_id(mission_id)
    if not base_branch or base_branch.startswith(workspace.MISSION_PREFIX):
        raise ValueError("base branch must not be a mission branch")
    metadata = workspace.repository_metadata(target)
    git_data = workspace.git_metadata(target)
    expected_branch = workspace.branch_for(mission_id)
    if git_data["working_branch"] != expected_branch:
        raise ValueError(f"current branch must be {expected_branch}")
    if workspace.legacy_workspace_exists(target):
        raise ValueError("legacy workspace exists; run migrate_workspace.py explicitly")
    root = workspace.mission_root(target, mission_id)
    if root.exists():
        raise FileExistsError(f"Refusing to overwrite {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template_root, root)
    state_path = root / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(metadata)
    state.update(git_data)
    state.update({
        "mission_id": mission_id,
        "base_branch": base_branch,
        "working_branch": expected_branch,
        "last_checkpoint_commit": git_data["base_commit"],
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return root


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--base-branch", required=True)
    args = parser.parse_args(argv)
    try:
        print(initialize(args.target, Path(__file__).resolve().parents[1] / "assets/workspace-template", args.mission, args.base_branch))
        return 0
    except (FileExistsError, NotADirectoryError, ValueError) as error:
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
