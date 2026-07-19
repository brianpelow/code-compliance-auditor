"""Audit every public repo in the portfolio."""
import subprocess, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auditor.orchestrator import audit_repo

out = subprocess.run(
    ["gh", "repo", "list", "brianpelow", "--limit", "100",
     "--visibility", "public", "--json", "name"],
    capture_output=True, text=True, shell=True,
)
repos = sorted(r["name"] for r in json.loads(out.stdout))
print(f"Auditing {len(repos)} repositories\n")

rows, failures = [], []
for name in repos:
    try:
        r = audit_repo(f"brianpelow/{name}")
        rows.append((name, r.grade, r.overall_score, len(r.all_findings)))
    except Exception as exc:
        failures.append((name, str(exc)[:60]))

rows.sort(key=lambda r: (r[2], r[0]))

print(f"{'REPO':<38} {'GRADE':<6} {'SCORE':<6} FINDINGS")
print("-" * 62)
for name, grade, score, findings in rows:
    print(f"{name:<38} {grade:<6} {score:<6} {findings}")

if rows:
    avg = sum(r[2] for r in rows) / len(rows)
    below = [r for r in rows if r[2] < 85]
    print(f"\nAverage: {avg:.1f}/100 across {len(rows)} repos")
    print(f"Below B (85): {len(below)}")
    for name, grade, score, _ in below:
        print(f"   {name} - {grade} {score}")

if failures:
    print(f"\nFailed to audit ({len(failures)}):")
    for name, err in failures:
        print(f"   {name}: {err}")