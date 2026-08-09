"""Generate STATE.md from live portfolio state."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent


def run() -> int:
    from auditor.orchestrator import audit_repo
    from auditor.state import collect
    from auditor.state_render import render

    print("[state] Collecting portfolio state...")
    state = collect(audit_fn=audit_repo)

    print(f"[state] {len(state.repos)} repos, avg {state.average_score}/100")
    print(f"[state] {state.scheduled_agents} scheduled agents")
    healthy = sum(1 for s in state.surfaces if s.healthy)
    print(f"[state] {healthy}/{len(state.surfaces)} surfaces healthy")

    if state.uncategorized:
        print(f"[state] UNCATEGORIZED: {', '.join(state.uncategorized)}")

    generated = REPO_ROOT / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "state.json").write_text(
        json.dumps(
            {
                "generated_at": state.generated_at,
                "scheduled_agents": state.scheduled_agents,
                "ci_status": state.ci_status,
                "repos": [asdict(r) for r in state.repos],
                "surfaces": [asdict(s) for s in state.surfaces],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("[state] Wrote generated/state.json")

    out = REPO_ROOT / "STATE.md"
    out.write_text(render(state), encoding="utf-8")
    print(f"[state] Wrote {out} ({out.stat().st_size} bytes)")

    failures = [r for r in state.repos if not r.ok]
    if failures:
        print(f"[state] {len(failures)} repo(s) could not be audited")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())