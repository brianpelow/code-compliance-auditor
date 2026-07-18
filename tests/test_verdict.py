"""Tests for verdict synthesis, orchestration, and rendering."""

from auditor.github import parse_repo_arg
from auditor.models import AgentResult, Finding, RepoSnapshot, Severity
from auditor.orchestrator import audit_snapshot
from auditor.render import render_markdown
from auditor.verdict import build_report, compute_overall

import pytest


def result(name: str, score: int, findings: list[Finding] | None = None) -> AgentResult:
    return AgentResult(agent=name, score=score, findings=findings or [])


def test_overall_is_weighted() -> None:
    overall = compute_overall(result("s", 100), result("c", 100), result("d", 100))
    assert overall == 100


def test_security_carries_most_weight() -> None:
    security_low = compute_overall(result("s", 0), result("c", 100), result("d", 100))
    debt_low = compute_overall(result("s", 100), result("c", 100), result("d", 0))
    assert security_low < debt_low


def test_critical_finding_caps_grade_at_d() -> None:
    critical = Finding(
        rule_id="SEC001", title="Committed credential", severity=Severity.CRITICAL, detail=""
    )
    report = build_report("e/e", result("s", 95, [critical]), result("c", 100), result("d", 100))
    assert report.grade == "D"


def test_no_critical_allows_high_grade() -> None:
    report = build_report("e/e", result("s", 100), result("c", 100), result("d", 100))
    assert report.grade == "A"


def test_priorities_are_capped_at_five() -> None:
    findings = [
        Finding(rule_id=f"X{i}", title=f"t{i}", severity=Severity.HIGH, detail="")
        for i in range(9)
    ]
    report = build_report("e/e", result("s", 50, findings), result("c", 100), result("d", 100))
    assert len(report.priorities) == 5


def test_summary_is_generated_without_api_key() -> None:
    report = build_report("e/e", result("s", 100), result("c", 100), result("d", 100))
    assert report.repo in report.summary


def test_audit_snapshot_end_to_end(clean_repo: RepoSnapshot) -> None:
    report = audit_snapshot(clean_repo)
    assert report.repo == "example/clean"
    assert report.grade in {"A", "B", "C", "D", "F"}
    assert 0 <= report.overall_score <= 100


def test_audit_snapshot_is_deterministic(messy_repo: RepoSnapshot) -> None:
    first = audit_snapshot(messy_repo)
    second = audit_snapshot(messy_repo)
    assert first.overall_score == second.overall_score
    assert first.grade == second.grade


def test_messy_scores_below_clean(clean_repo: RepoSnapshot, messy_repo: RepoSnapshot) -> None:
    assert audit_snapshot(messy_repo).overall_score < audit_snapshot(clean_repo).overall_score


def test_markdown_contains_key_sections(clean_repo: RepoSnapshot) -> None:
    md = render_markdown(audit_snapshot(clean_repo))
    assert "# Compliance Audit" in md
    assert "## Scores" in md
    assert "## Findings" in md


def test_parse_owner_name() -> None:
    assert parse_repo_arg("brianpelow/orbit-platform") == ("brianpelow", "orbit-platform")


def test_parse_full_url() -> None:
    assert parse_repo_arg("https://github.com/brianpelow/orbit-platform") == (
        "brianpelow",
        "orbit-platform",
    )


def test_parse_url_with_git_suffix() -> None:
    assert parse_repo_arg("https://github.com/brianpelow/orbit-platform.git") == (
        "brianpelow",
        "orbit-platform",
    )


def test_parse_rejects_bare_name() -> None:
    with pytest.raises(ValueError):
        parse_repo_arg("orbit-platform")