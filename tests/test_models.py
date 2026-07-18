"""Tests for scoring and grading primitives."""

from auditor.models import (
    Finding,
    Severity,
    grade_from_score,
    prioritize,
    score_from_findings,
)


def f(rule_id: str, severity: Severity) -> Finding:
    return Finding(rule_id=rule_id, title=rule_id, severity=severity, detail="")


def test_score_no_findings_is_100() -> None:
    assert score_from_findings([]) == 100


def test_score_subtracts_severity_weight() -> None:
    assert score_from_findings([f("X1", Severity.HIGH)]) == 85


def test_score_clamps_at_zero() -> None:
    findings = [f(f"X{i}", Severity.CRITICAL) for i in range(10)]
    assert score_from_findings(findings) == 0


def test_info_findings_do_not_reduce_score() -> None:
    assert score_from_findings([f("X1", Severity.INFO)]) == 100


def test_grade_boundaries() -> None:
    assert grade_from_score(100) == "A"
    assert grade_from_score(93) == "A"
    assert grade_from_score(92) == "B"
    assert grade_from_score(85) == "B"
    assert grade_from_score(75) == "C"
    assert grade_from_score(65) == "D"
    assert grade_from_score(64) == "F"


def test_prioritize_orders_by_severity() -> None:
    findings = [
        f("B1", Severity.LOW),
        f("A1", Severity.CRITICAL),
        f("C1", Severity.MEDIUM),
    ]
    result = prioritize(findings)
    assert [x.rule_id for x in result] == ["A1", "C1", "B1"]


def test_prioritize_is_stable_within_severity() -> None:
    findings = [f("Z1", Severity.HIGH), f("A1", Severity.HIGH)]
    assert [x.rule_id for x in prioritize(findings)] == ["A1", "Z1"]


def test_prioritize_respects_limit() -> None:
    findings = [f(f"X{i}", Severity.HIGH) for i in range(10)]
    assert len(prioritize(findings, limit=3)) == 3