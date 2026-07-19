import sys, json, subprocess, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from auditor.orchestrator import audit_repo

print("=" * 60)
print("LIVE SURFACES")
print("=" * 60)
urls = [
    "https://brianpelow.github.io",
    "https://brianpelow.github.io/portfolio-assistant/",
    "https://brianpelow.github.io/cto-interview-simulator/",
    "https://brianpelow.github.io/platform-maturity-assessment/",
    "https://brianpelow.github.io/ai-incident-war-room/",
]
for url in urls:
    try:
        req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
            bad = sum(1 for c in body if ord(c) > 127)
            flag = "CLEAN" if bad == 0 else f"{bad} NON-ASCII"
            print(f"  {r.status}  {flag:<16} {url}")
    except Exception as e:
        print(f"  ERR  {str(e)[:40]:<16} {url}")

print()
print("=" * 60)
print("PORTFOLIO AUDIT")
print("=" * 60)
out = subprocess.run(
    ["gh","repo","list","brianpelow","--limit","100","--visibility","public","--json","name"],
    capture_output=True, text=True, shell=True,
)
repos = sorted(r["name"] for r in json.loads(out.stdout))

rows = []
for name in repos:
    try:
        r = audit_repo(f"brianpelow/{name}")
        rows.append((name, r.grade, r.overall_score))
    except Exception:
        pass

rows.sort(key=lambda r: (r[2], r[0]))
for name, grade, score in rows[:8]:
    print(f"  {name:<36} {grade}  {score}")

if rows:
    avg = sum(r[2] for r in rows) / len(rows)
    grades = {}
    for _, g, _ in rows:
        grades[g] = grades.get(g, 0) + 1
    print(f"\n  Repos:   {len(rows)}")
    print(f"  Average: {avg:.1f}/100")
    print(f"  Grades:  {dict(sorted(grades.items()))}")
    print(f"  Below B: {sum(1 for r in rows if r[2] < 85)}")