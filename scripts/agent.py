"""Nightly agent: audits a set of repositories and commits scorecards."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent

TARGETS = [
    "brianpelow/orbit-platform",
    "brianpelow/cab-automation",
    "brianpelow/IncidentPilot",
    "brianpelow/mcp-compliance-grc",
    "brianpelow/platform-conductor",
    "brianpelow/code-compliance-auditor",
]


def run() -> None:
    from auditor.orchestrator import audit_repo
    from auditor.render import render_markdown

    today = date.today()
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    print(f"[agent] code-compliance-auditor -- {today.isoformat()}")
    print(f"[agent] AI summary: {'enabled' if api_key else 'template mode'}")

    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    rows: list[tuple[str, int, str]] = []

    for target in TARGETS:
        print(f"[agent] Auditing {target}...")
        try:
            report = audit_repo(target)
        except Exception as exc:  # noqa: BLE001 - one failure must not stop the run
            print(f"[agent]   failed: {exc}")
            continue

        slug = target.split("/")[-1]
        (reports_dir / f"{slug}.md").write_text(render_markdown(report), encoding="utf-8")
        rows.append((target, report.overall_score, report.grade))
        print(f"[agent]   {report.grade} {report.overall_score}/100")

    if rows:
        _write_index(reports_dir, rows, today)

    print("[agent] Done.")


def _write_index(reports_dir: Path, rows: list[tuple[str, int, str]], today: date) -> None:
    rows_sorted = sorted(rows, key=lambda r: (-r[1], r[0]))
    avg = round(sum(r[1] for r in rows_sorted) / len(rows_sorted))

    lines = [
        "# Portfolio Audit Scorecard",
        "",
        f"**Last run:** {today.isoformat()}  |  **Repositories audited:** {len(rows_sorted)}  |  "
        f"**Average score:** {avg}/100",
        "",
        "| Repository | Grade | Score | Report |",
        "|------------|-------|-------|--------|",
    ]
    for name, score, grade in rows_sorted:
        slug = name.split("/")[-1]
        lines.append(f"| {name} | {grade} | {score}/100 | [report](./{slug}.md) |")

    lines.extend(
        [
            "",
            "---",
            "",
            "*All findings are deterministic. The same repository snapshot always produces "
            "the same score.*",
        ]
    )
    (reports_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()