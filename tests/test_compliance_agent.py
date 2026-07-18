"""Tests for ComplianceAgent."""

from auditor.agents import ComplianceAgent
from auditor.models import RepoSnapshot, Severity


def rule_ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def test_clean_repo_scores_well(clean_repo: RepoSnapshot) -> None:
    result = ComplianceAgent().run(clean_repo)
    assert result.score >= 90


def test_empty_repo_flags_codeowners(empty_repo: RepoSnapshot) -> None:
    assert "CMP001" in rule_ids(ComplianceAgent().run(empty_repo))


def test_empty_repo_flags_license(empty_repo: RepoSnapshot) -> None:
    assert "CMP002" in rule_ids(ComplianceAgent().run(empty_repo))


def test_empty_repo_flags_ci(empty_repo: RepoSnapshot) -> None:
    assert "CMP003" in rule_ids(ComplianceAgent().run(empty_repo))


def test_empty_repo_flags_tests(empty_repo: RepoSnapshot) -> None:
    assert "CMP004" in rule_ids(ComplianceAgent().run(empty_repo))


def test_missing_codeowners_is_high_severity(empty_repo: RepoSnapshot) -> None:
    finding = next(f for f in ComplianceAgent().run(empty_repo).findings if f.rule_id == "CMP001")
    assert finding.severity is Severity.HIGH


def test_thin_readme_is_flagged() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["README.md"], files={"README.md": "# Hi"}
    )
    assert "CMP006" in rule_ids(ComplianceAgent().run(snap))


def test_substantial_readme_is_not_flagged(clean_repo: RepoSnapshot) -> None:
    assert "CMP006" not in rule_ids(ComplianceAgent().run(clean_repo))


def test_adr_detected_in_clean_repo(clean_repo: RepoSnapshot) -> None:
    assert "CMP009" not in rule_ids(ComplianceAgent().run(clean_repo))


def test_missing_adr_is_flagged(empty_repo: RepoSnapshot) -> None:
    assert "CMP009" in rule_ids(ComplianceAgent().run(empty_repo))


def test_archived_repo_is_info_only() -> None:
    snap = RepoSnapshot(owner="e", name="e", paths=[], files={}, archived=True)
    finding = next(f for f in ComplianceAgent().run(snap).findings if f.rule_id == "CMP010")
    assert finding.severity is Severity.INFO


def test_codeowners_detected_at_any_location() -> None:
    for location in ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"):
        snap = RepoSnapshot(owner="e", name="e", paths=[location], files={})
        assert "CMP001" not in rule_ids(ComplianceAgent().run(snap))


def test_is_deterministic(clean_repo: RepoSnapshot) -> None:
    first = ComplianceAgent().run(clean_repo)
    second = ComplianceAgent().run(clean_repo)
    assert first.score == second.score