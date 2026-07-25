import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/orchestrate-long-task"
sys.path.insert(0, str(SKILL / "scripts"))
import init_workspace
import migrate_workspace
import render_handoff
import validate_workspace
import workspace

TEMPLATE = SKILL / "assets/workspace-template"


class WorkspaceTests(unittest.TestCase):
    def git(self, path, *args):
        return subprocess.run(["git", *args], cwd=path, check=True, text=True, capture_output=True).stdout.strip()

    def repo(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)
        self.git(path, "init", "-b", "main")
        self.git(path, "config", "user.email", "test@example.com")
        self.git(path, "config", "user.name", "Test")
        (path / "seed").write_text("seed\n")
        self.git(path, "add", "seed")
        self.git(path, "commit", "-m", "seed")
        self.git(path, "remote", "add", "origin", "https://github.com/example/project.git")
        return path

    def mission(self, path, mission_id="build-api-v2", base_branch="main", commit=False):
        self.git(path, "switch", base_branch)
        self.git(path, "switch", "-c", workspace.branch_for(mission_id))
        root = init_workspace.initialize(path, TEMPLATE, mission_id, base_branch)
        if commit:
            self.git(path, "add", ".task-orchestrator")
            self.git(path, "commit", "-m", f"initialize {mission_id}")
        return root

    def activate(self, path, mission_id="build-api-v2"):
        root = workspace.mission_root(path, mission_id)
        task = root / "tasks/TASK-001.md"
        task.write_text((TEMPLATE / "tasks/TASK-template.md").read_text().replace("TASK-NNN", "TASK-001"))
        state_path = root / "state.json"
        state = json.loads(state_path.read_text())
        state.update({"mission_status": "active", "phase": "execute", "recommended_reasoning": "low", "current_task": "TASK-001", "next_action": "Execute TASK-001."})
        state_path.write_text(json.dumps(state))
        return root

    def test_initialize_and_validate(self):
        path = self.repo()
        root = self.mission(path)
        self.assertEqual(root, workspace.mission_root(path, "build-api-v2"))
        self.assertEqual(validate_workspace.validate_workspace(path, "build-api-v2"), [])

    def test_two_missions_have_isolated_state(self):
        path = self.repo()
        first = self.mission(path, "build-api-v2", commit=True)
        second = self.mission(path, "redesign-console")
        self.assertNotEqual(first, second)
        self.assertTrue((second / "state.json").is_file())
        first_state = self.git(path, "show", f"{workspace.branch_for('build-api-v2')}:.task-orchestrator/missions/build-api-v2/state.json")
        self.assertEqual(json.loads(first_state)["mission_id"], "build-api-v2")
        self.assertEqual(workspace.discover_missions(path), ["redesign-console"])
        self.assertEqual(validate_workspace.validate_workspace(path, "redesign-console"), [])

    def test_invalid_or_duplicate_mission_is_refused(self):
        path = self.repo()
        with self.assertRaises(ValueError):
            init_workspace.initialize(path, TEMPLATE, "../escape", "main")
        self.mission(path, commit=True)
        with self.assertRaises(FileExistsError):
            init_workspace.initialize(path, TEMPLATE, "build-api-v2", "main")

    def test_remote_normalization(self):
        self.assertEqual(workspace.normalize_repository_url("git@github.com:Example/project.git"), "github.com/Example/project")
        self.assertEqual(workspace.normalize_repository_url("https://github.com/Example/project.git"), "github.com/Example/project")
        self.assertEqual(workspace.normalize_repository_url("ssh://git@github.com/Example/project.git"), "github.com/Example/project")
        self.assertEqual(workspace.normalize_repository_url("ssh://git@github.com:2222/Example/project.git"), "github.com:2222/Example/project")

    def test_mission_repository_and_branch_mismatches_are_reported(self):
        path = self.repo()
        root = self.mission(path)
        state_path = root / "state.json"
        state = json.loads(state_path.read_text())
        state["mission_id"] = "other-mission"
        state_path.write_text(json.dumps(state))
        self.assertIn("Requested mission differs from state mission_id", validate_workspace.validate_workspace(path, "build-api-v2"))
        state["mission_id"] = "build-api-v2"
        state["working_branch"] = "main"
        state_path.write_text(json.dumps(state))
        self.assertIn("working_branch differs from mission branch", validate_workspace.validate_workspace(path, "build-api-v2"))
        state["working_branch"] = workspace.branch_for("build-api-v2")
        state_path.write_text(json.dumps(state))
        self.git(path, "remote", "set-url", "origin", "https://github.com/example/other.git")
        self.assertIn("Recorded repository differs from origin remote", validate_workspace.validate_workspace(path, "build-api-v2"))

    def test_handoff_is_scoped_to_one_mission(self):
        path = self.repo()
        root = self.mission(path)
        self.activate(path)
        handoff = render_handoff.render_handoff(path, "build-api-v2")
        text = handoff.read_text()
        self.assertIn("Mission ID: build-api-v2", text)
        self.assertIn("mission=build-api-v2", text)
        self.assertEqual(len(list((root / "archive").glob("*.md"))), 1)

    def test_require_clean(self):
        path = self.repo()
        self.mission(path)
        (path / "dirty").write_text("x")
        self.assertIn("working tree is not clean", validate_workspace.validate_workspace(path, "build-api-v2", True))

    def test_migrate_legacy_workspace(self):
        path = self.repo()
        legacy = path / ".task-orchestrator"
        shutil.copytree(TEMPLATE, legacy)
        state_path = legacy / "state.json"
        state = json.loads(state_path.read_text())
        state["schema_version"] = 1
        for key in ("mission_id", "repository_url", "repository_id", "base_branch"):
            state.pop(key)
        state["working_branch"] = workspace.branch_for("build-api-v2")
        state_path.write_text(json.dumps(state))
        self.git(path, "add", ".task-orchestrator")
        self.git(path, "commit", "-m", "legacy workspace")
        self.git(path, "switch", "-c", workspace.branch_for("build-api-v2"))
        destination = migrate_workspace.migrate(path, "build-api-v2", "main")
        self.assertTrue((destination / "state.json").is_file())
        self.assertFalse((legacy / "state.json").exists())
        self.assertEqual(validate_workspace.validate_workspace(path, "build-api-v2"), [])

    def test_clone_can_resume_mission_branch(self):
        path = self.repo()
        remote_dir = tempfile.TemporaryDirectory()
        self.addCleanup(remote_dir.cleanup)
        remote = Path(remote_dir.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        self.git(path, "remote", "set-url", "origin", str(remote))
        self.git(path, "push", "-u", "origin", "main")
        self.mission(path)
        self.git(path, "add", ".task-orchestrator")
        self.git(path, "commit", "-m", "initialize mission")
        self.git(path, "push", "-u", "origin", workspace.branch_for("build-api-v2"))
        clone_dir = tempfile.TemporaryDirectory()
        self.addCleanup(clone_dir.cleanup)
        clone = Path(clone_dir.name) / "clone"
        subprocess.run(["git", "clone", "--branch", workspace.branch_for("build-api-v2"), str(remote), str(clone)], check=True, capture_output=True)
        self.assertEqual(validate_workspace.validate_workspace(clone, "build-api-v2"), [])

    def test_skill_declares_double_locator(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertIn("repo=<repository-url>", text)
        self.assertIn("mission=<id>", text)
        self.assertIn("codex/mission/<mission-id>", text)


if __name__ == "__main__":
    unittest.main()
