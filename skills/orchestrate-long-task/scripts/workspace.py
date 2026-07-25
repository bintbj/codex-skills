import re
import subprocess
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse


MISSION_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\Z")
MISSION_PREFIX = "codex/mission/"
LEGACY_ITEMS = ("mission.md", "plan.md", "state.json", "tasks", "decisions", "handoffs", "archive")


def validate_mission_id(mission_id: str) -> str:
    if not MISSION_RE.fullmatch(mission_id):
        raise ValueError("mission ID must match [a-z0-9][a-z0-9-]{0,62}")
    return mission_id


def branch_for(mission_id: str) -> str:
    return f"{MISSION_PREFIX}{validate_mission_id(mission_id)}"


def control_root(target: Path) -> Path:
    return target.resolve() / ".task-orchestrator"


def mission_root(target: Path, mission_id: str) -> Path:
    return control_root(target) / "missions" / validate_mission_id(mission_id)


def git(target: Path, *args: str) -> Optional[str]:
    result = subprocess.run(["git", *args], cwd=target, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def is_git_repository(target: Path) -> bool:
    return git(target, "rev-parse", "--show-toplevel") is not None


def remote_url(target: Path) -> Optional[str]:
    return git(target, "remote", "get-url", "origin")


def normalize_repository_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("repository URL is empty")
    if value.startswith("git@") and ":" in value:
        host, path = value[4:].split(":", 1)
        return _host_path(host, path)
    parsed = urlparse(value)
    if parsed.scheme == "file":
        return str(Path(parsed.path).resolve())
    if parsed.scheme:
        if not parsed.hostname:
            raise ValueError("repository URL has no host")
        host = parsed.hostname
        default_ports = {"http": 80, "https": 443, "ssh": 22}
        if parsed.port and parsed.port != default_ports.get(parsed.scheme.lower()):
            host = f"{host}:{parsed.port}"
        return _host_path(host, parsed.path)
    if value.startswith("/") or value.startswith("."):
        return str(Path(value).resolve())
    raise ValueError("repository URL is not a supported Git remote")


def _host_path(host: str, path: str) -> str:
    normalized = path.strip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if not normalized:
        raise ValueError("repository URL has no path")
    return f"{host.lower()}/{normalized}"


def repository_metadata(target: Path) -> dict[str, str]:
    if not is_git_repository(target):
        raise ValueError("target is not a Git repository")
    url = remote_url(target)
    if url is None:
        raise ValueError("origin remote is required for cross-account missions")
    return {"repository_url": url, "repository_id": normalize_repository_url(url)}


def git_metadata(target: Path) -> Dict[str, Optional[str]]:
    if not is_git_repository(target):
        raise ValueError("target is not a Git repository")
    return {
        "base_commit": git(target, "rev-parse", "HEAD"),
        "working_branch": git(target, "branch", "--show-current") or "DETACHED",
    }


def discover_missions(target: Path) -> list[str]:
    root = control_root(target) / "missions"
    if not root.is_dir():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_dir() and MISSION_RE.fullmatch(path.name))


def legacy_workspace_exists(target: Path) -> bool:
    root = control_root(target)
    return any((root / item).exists() for item in LEGACY_ITEMS)
