"""Tests for SecurityAgent. Deterministic, fixture-driven."""

from auditor.agents import SecurityAgent
from auditor.models import RepoSnapshot, Severity


def rule_ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def test_clean_repo_has_no_critical(clean_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(clean_repo)
    assert result.critical_count == 0


def test_detects_hardcoded_password(messy_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(messy_repo)
    assert "SEC004" in rule_ids(result)


def test_detects_bare_except(messy_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(messy_repo)
    assert "SEC010" in rule_ids(result)


def test_detects_shell_true(messy_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(messy_repo)
    assert "SEC013" in rule_ids(result)


def test_detects_committed_env_file(messy_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(messy_repo)
    assert "SEC021" in rule_ids(result)
    env_finding = next(f for f in result.findings if f.rule_id == "SEC021")
    assert env_finding.severity is Severity.CRITICAL


def test_placeholder_values_are_not_flagged() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["config.py"],
        files={"config.py": "api_key = 'your_api_key_here_placeholder'\n"},
    )
    result = SecurityAgent().run(snap)
    assert "SEC003" not in rule_ids(result)


def test_env_var_lookup_is_not_flagged() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["config.py"],
        files={"config.py": "password = os.environ['DB_PASSWORD_VALUE']\n"},
    )
    result = SecurityAgent().run(snap)
    assert "SEC004" not in rule_ids(result)


def test_detects_aws_key() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["c.py"],
        files={"c.py": "key = 'AKIAIOSFODNN7EXAMPLQ'\n"},
    )
    result = SecurityAgent().run(snap)
    assert "SEC001" in rule_ids(result)


def test_detects_eval() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["c.py"], files={"c.py": "result = eval(user_input)\n"}
    )
    assert "SEC011" in rule_ids(SecurityAgent().run(snap))


def test_detects_tls_verification_disabled() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["c.py"], files={"c.py": "requests.get(url, verify=False)\n"}
    )
    assert "SEC015" in rule_ids(SecurityAgent().run(snap))


def test_missing_security_policy_is_low_severity(empty_repo: RepoSnapshot) -> None:
    result = SecurityAgent().run(empty_repo)
    finding = next(f for f in result.findings if f.rule_id == "SEC030")
    assert finding.severity is Severity.LOW


def test_is_deterministic(messy_repo: RepoSnapshot) -> None:
    first = SecurityAgent().run(messy_repo)
    second = SecurityAgent().run(messy_repo)
    assert first.score == second.score
    assert rule_ids(first) == rule_ids(second)