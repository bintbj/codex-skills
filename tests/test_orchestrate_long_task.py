import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/orchestrate-long-task"
sys.path.insert(0, str(SKILL / "scripts"))
import init_workspace
import render_handoff
import validate_workspace

TEMPLATE = SKILL / "assets/workspace-template"

class WorkspaceTests(unittest.TestCase):
    def repo(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup); path = Path(directory.name)
        for command in (["git", "init", "-b", "main"], ["git", "config", "user.email", "test@example.com"], ["git", "config", "user.name", "Test"]): subprocess.run(command, cwd=path, check=True, capture_output=True)
        (path / "seed").write_text("seed\n"); subprocess.run(["git", "add", "seed"], cwd=path, check=True); subprocess.run(["git", "commit", "-m", "seed"], cwd=path, check=True, capture_output=True)
        return path
    def activate(self, path):
        root = init_workspace.initialize(path, TEMPLATE); task = root / "tasks/TASK-001.md"; task.write_text((TEMPLATE / "tasks/TASK-template.md").read_text().replace("TASK-NNN", "TASK-001"))
        state_path = root / "state.json"; state = json.loads(state_path.read_text()); state.update({"mission_status":"active", "phase":"execute", "recommended_reasoning":"low", "current_task":"TASK-001", "next_action":"Execute TASK-001."}); state_path.write_text(json.dumps(state))
        return root
    def test_initialize_and_validate(self):
        path = self.repo(); init_workspace.initialize(path, TEMPLATE); self.assertEqual(validate_workspace.validate_workspace(path), [])
    def test_overwrite_refused(self):
        path = self.repo(); init_workspace.initialize(path, TEMPLATE)
        with self.assertRaises(FileExistsError): init_workspace.initialize(path, TEMPLATE)
    def test_missing_task_reported(self):
        path = self.repo(); root = init_workspace.initialize(path, TEMPLATE); state_path = root / "state.json"; state = json.loads(state_path.read_text()); state.update({"mission_status":"active", "phase":"execute", "recommended_reasoning":"low", "current_task":"TASK-001", "next_action":"Execute TASK-001."}); state_path.write_text(json.dumps(state)); self.assertIn("Missing active task file: TASK-001.md", validate_workspace.validate_workspace(path))
    def test_handoff_archives_and_renders(self):
        path = self.repo(); root = self.activate(path); handoff = render_handoff.render_handoff(path); self.assertIn("TASK-001", handoff.read_text()); self.assertEqual(len(list((root / "archive").glob("*.md"))), 1)
    def test_require_clean(self):
        path = self.repo(); init_workspace.initialize(path, TEMPLATE); (path / "dirty").write_text("x")
        self.assertIn("working tree is not clean", validate_workspace.validate_workspace(path, True))

if __name__ == "__main__": unittest.main()
