"""Tests for DebtAgent."""

from auditor.agents import DebtAgent
from auditor.models import RepoSnapshot


def rule_ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def test_clean_repo_has_few_findings(clean_repo: RepoSnapshot) -> None:
    assert DebtAgent().run(clean_repo).score >= 90


def test_detects_todo_density(messy_repo: RepoSnapshot) -> None:
    assert "DBT001" in rule_ids(DebtAgent().run(messy_repo))


def test_low_todo_count_not_flagged() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["a.py"], files={"a.py": "# TODO: one thing\n"}
    )
    assert "DBT001" not in rule_ids(DebtAgent().run(snap))


def test_detects_very_large_file() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["big.py"], files={"big.py": "x = 1\n" * 1200}
    )
    assert "DBT002" in rule_ids(DebtAgent().run(snap))


def test_detects_large_file() -> None:
    snap = RepoSnapshot(
        owner="e", name="e", paths=["mid.py"], files={"mid.py": "x = 1\n" * 600}
    )
    assert "DBT003" in rule_ids(DebtAgent().run(snap))


def test_detects_unpinned_dependencies(messy_repo: RepoSnapshot) -> None:
    assert "DBT005" in rule_ids(DebtAgent().run(messy_repo))


def test_pinned_dependencies_not_flagged() -> None:
    snap = RepoSnapshot(
        owner="e",
        name="e",
        paths=["requirements.txt"],
        files={"requirements.txt": "requests==2.31.0\nhttpx>=0.27.0\n"},
    )
    assert "DBT005" not in rule_ids(DebtAgent().run(snap))


def test_detects_deep_nesting() -> None:
    deep = "def a():\n" + "    " * 7 + "return 1\n"
    snap = RepoSnapshot(owner="e", name="e", paths=["d.py"], files={"d.py": deep})
    assert "DBT004" in rule_ids(DebtAgent().run(snap))


def test_sparse_type_hints_flagged() -> None:
    body = "".join(f"def fn{i}():\n    return {i}\n" for i in range(12))
    snap = RepoSnapshot(owner="e", name="e", paths=["u.py"], files={"u.py": body})
    assert "DBT006" in rule_ids(DebtAgent().run(snap))


def test_annotated_functions_not_flagged() -> None:
    body = "".join(f"def fn{i}() -> int:\n    return {i}\n" for i in range(12))
    snap = RepoSnapshot(owner="e", name="e", paths=["t.py"], files={"t.py": body})
    assert "DBT006" not in rule_ids(DebtAgent().run(snap))


def test_is_deterministic(messy_repo: RepoSnapshot) -> None:
    assert DebtAgent().run(messy_repo).score == DebtAgent().run(messy_repo).score