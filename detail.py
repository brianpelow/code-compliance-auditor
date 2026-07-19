import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from auditor.orchestrator import audit_repo

for name in ["git_test", "brianpelow", "brianpelow.github.io",
             "portfolio-assistant", "cto-interview-simulator",
             "platform-maturity-assessment"]:
    r = audit_repo(f"brianpelow/{name}")
    print(f"\n{'='*58}\n{name}  {r.grade} {r.overall_score}/100")
    print(f"  security {r.security.score}  compliance {r.compliance.score}  debt {r.debt.score}")
    for f in r.all_findings:
        print(f"   [{f.severity.value:<8}] {f.rule_id}  {f.title}")