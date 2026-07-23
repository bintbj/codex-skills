import argparse
import json
import re
import shutil
from pathlib import Path
import validate_workspace

def _bullets(values, empty): return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"

def render_handoff(target: Path):
    errors = validate_workspace.validate_workspace(target)
    if errors: raise ValueError("\n".join(errors))
    root = target.resolve() / ".task-orchestrator"; state = json.loads((root / "state.json").read_text()); handoff = root / "handoffs/latest.md"; archive = root / "archive"; archive.mkdir(exist_ok=True)
    if handoff.read_text().strip():
        stamp = re.sub(r"[^0-9]", "", state["updated_at"])[:14] or "unknown"; path = archive / f"handoff-{stamp}.md"; index = 1
        while path.exists(): path = archive / f"handoff-{stamp}-{index}.md"; index += 1
        shutil.copy2(handoff, path)
    handoff.write_text(f"""# Latest Handoff

Updated at: {state['updated_at']}
Phase: {state['phase']}
Current task: {state['current_task'] or 'none'}
Working branch: {state['working_branch'] or 'none'}
Base commit: {state['base_commit'] or 'none'}
Last checkpoint: {state['last_checkpoint_commit'] or 'none'}
Recommended reasoning: {state['recommended_reasoning']}

## Completed work

{_bullets(state.get('completed_work', []), 'No completed work recorded.')}

## Verification

{_bullets(state.get('verification', []), 'No verification evidence recorded.')}

## Risks and blockers

{_bullets(state.get('risks', []) + state['blockers'], 'No risks recorded.')}

## Next action

{state['next_action']}
""", encoding="utf-8")
    return handoff

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("target", type=Path); args = parser.parse_args(argv)
    try: print(render_handoff(args.target)); return 0
    except ValueError as error: print(error); return 1

if __name__ == "__main__": raise SystemExit(main())
