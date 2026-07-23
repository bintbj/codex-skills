import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git(target: Path, *args: str):
    result = subprocess.run(["git", *args], cwd=target, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def git_metadata(target: Path):
    if _git(target, "rev-parse", "--show-toplevel") is None:
        return {"base_commit": None, "working_branch": None}
    return {
        "base_commit": _git(target, "rev-parse", "HEAD"),
        "working_branch": _git(target, "branch", "--show-current") or "DETACHED",
    }


def initialize(target: Path, template_root: Path):
    target, workspace = target.resolve(), target.resolve() / ".task-orchestrator"
    if not target.is_dir():
        raise NotADirectoryError(target)
    if workspace.exists():
        raise FileExistsError(f"Refusing to overwrite {workspace}")
    shutil.copytree(template_root, workspace)
    path = workspace / "state.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    state.update(git_metadata(target))
    state["last_checkpoint_commit"] = state["base_commit"]
    state["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return workspace


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    args = parser.parse_args(argv)
    try:
        print(initialize(args.target, Path(__file__).resolve().parents[1] / "assets/workspace-template"))
        return 0
    except (FileExistsError, NotADirectoryError) as error:
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
