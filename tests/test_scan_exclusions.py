"""Scanning exclusions.

Test fixtures, rule definitions, and documentation intentionally contain the
patterns these rules detect. Scanning them produces guaranteed false positives.
"""

from auditor.agents import SecurityAgent
from auditor.agents.security import scannable_files
from auditor.models import RepoSnapshot


def rule_ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def snap_with(path: str, content: str) -> RepoSnapshot:
    return RepoSnapshot(owner="e", name="e", paths=[path], files={path: content})


def test_test_file_credential_is_not_flagged() -> None:
    snap = snap_with("tests/test_security.py", "key = 'AKIAIOSFODNN7EXAMPLQ'\n")
    assert "SEC001" not in rule_ids(SecurityAgent().run(snap))


def test_conftest_password_is_not_flagged() -> None:
    snap = snap_with("tests/conftest.py", "password = 'supersecret123'\n")
    assert "SEC004" not in rule_ids(SecurityAgent().run(snap))


def test_underscore_test_suffix_is_excluded() -> None:
    snap = snap_with("app/handler_test.py", "result = eval(x)\n")
    assert "SEC011" not in rule_ids(SecurityAgent().run(snap))


def test_rule_definition_module_is_not_flagged() -> None:
    snap = snap_with("src/auditor/agents/security.py", "PATTERN = r'eval\\\\s*\\\\('\n")
    assert "SEC011" not in rule_ids(SecurityAgent().run(snap))


def test_readme_shell_true_is_not_flagged() -> None:
    snap = snap_with("README.md", "Detects `shell=True` in source files.\n")
    assert "SEC013" not in rule_ids(SecurityAgent().run(snap))


def test_production_code_is_still_flagged() -> None:
    snap = snap_with("src/app/handler.py", "result = eval(user_input)\n")
    assert "SEC011" in rule_ids(SecurityAgent().run(snap))


def test_production_credential_is_still_flagged() -> None:
    snap = snap_with("src/app/config.py", "key = 'AKIAIOSFODNN7EXAMPLQ'\n")
    assert "SEC001" in rule_ids(SecurityAgent().run(snap))


def test_scannable_excludes_tests() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["src/a.py", "tests/test_a.py"],
        files={"src/a.py": "x", "tests/test_a.py": "y"},
    )
    assert set(scannable_files(snap)) == {"src/a.py"}


def test_scannable_code_only_excludes_markdown() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["src/a.py", "README.md"],
        files={"src/a.py": "x", "README.md": "y"},
    )
    assert set(scannable_files(snap)) == {"src/a.py"}


def test_scannable_non_code_mode_includes_config() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["config.yml", "tests/test_a.py"],
        files={"config.yml": "x", "tests/test_a.py": "y"},
    )
    result = scannable_files(snap, code_only=False)
    assert "config.yml" in result
    assert "tests/test_a.py" not in result


def test_committed_env_file_still_detected_regardless_of_exclusions() -> None:
    snap = RepoSnapshot(owner="e", name="e", paths=[".env"], files={})
    assert "SEC021" in rule_ids(SecurityAgent().run(snap))