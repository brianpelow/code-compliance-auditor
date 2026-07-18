"""VerdictAgent -- synthesizes the three scanning agents into a final report.

Scoring and grading are fully deterministic. The optional LLM pass writes only
the prose summary; it never creates, removes, or reweights a finding.
"""

from __future__ import annotations


from auditor.models import (
    AgentResult,
    AuditReport,
    Severity,
    grade_from_score,
    prioritize,
)

# Security is weighted highest: a committed credential matters more than a
# missing CHANGELOG.
WEIGHTS = {"security": 0.45, "compliance": 0.35, "debt": 0.20}


def compute_overall(security: AgentResult, compliance: AgentResult, debt: AgentResult) -> int:
    weighted = (
        security.score * WEIGHTS["security"]
        + compliance.score * WEIGHTS["compliance"]
        + debt.score * WEIGHTS["debt"]
    )
    return int(round(weighted))


def build_report(
    repo: str,
    security: AgentResult,
    compliance: AgentResult,
    debt: AgentResult,
    api_key: str = "",
) -> AuditReport:
    overall = compute_overall(security, compliance, debt)

    # Any critical finding caps the grade at D, regardless of weighted score.
    all_findings = [*security.findings, *compliance.findings, *debt.findings]
    has_critical = any(f.severity is Severity.CRITICAL for f in all_findings)
    grade = grade_from_score(overall)
    if has_critical and grade in ("A", "B", "C"):
        grade = "D"

    priorities = prioritize(all_findings, limit=5)

    report = AuditReport(
        repo=repo,
        security=security,
        compliance=compliance,
        debt=debt,
        overall_score=overall,
        grade=grade,
        priorities=priorities,
    )
    report.summary = _summary(report, api_key)
    return report


def _summary(report: AuditReport, api_key: str) -> str:
    if api_key:
        text = _llm_summary(report, api_key)
        if text:
            return text
    return _template_summary(report)


def _template_summary(report: AuditReport) -> str:
    crit = sum(1 for f in report.all_findings if f.severity is Severity.CRITICAL)
    high = sum(1 for f in report.all_findings if f.severity is Severity.HIGH)

    parts = [
        f"{report.repo} scores {report.overall_score}/100 (grade {report.grade}) "
        f"across security ({report.security.score}), compliance ({report.compliance.score}), "
        f"and technical debt ({report.debt.score})."
    ]

    if crit:
        parts.append(
            f"{crit} critical finding(s) require immediate attention and cap the grade regardless "
            "of other scores."
        )
    elif high:
        parts.append(f"{high} high-severity finding(s) should be resolved before the next release.")
    else:
        parts.append("No critical or high-severity findings were detected.")

    if report.priorities:
        parts.append(f"The highest-priority item is: {report.priorities[0].title}.")

    return " ".join(parts)


def _llm_summary(report: AuditReport, api_key: str) -> str:
    try:
        import httpx

        findings_text = "\n".join(
            f"- [{f.severity.value.upper()}] {f.rule_id} {f.title}: {f.detail}"
            for f in report.all_findings[:15]
        ) or "No findings."

        prompt = f"""You are writing the executive summary of a repository compliance audit.

Repository: {report.repo}
Overall score: {report.overall_score}/100 (grade {report.grade})
Security: {report.security.score}/100
Compliance: {report.compliance.score}/100
Technical debt: {report.debt.score}/100

Findings:
{findings_text}

Write 3-4 sentences for an engineering leader. State what the scores mean, name the most
consequential risk, and say what to fix first. Do not invent findings that are not listed.
Do not use bullet points. Plain prose only."""

        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "qwen/qwen3-8b:free",
                "max_tokens": 300,
                "transforms": ["middle-out"],
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        if r.status_code != 200:
            return ""
        data = r.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        import re

        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        return text
    except Exception:
        return ""