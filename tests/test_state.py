"""Tests for portfolio state collection and rendering.

Rendering is tested entirely with fixture data and no network, which is the
reason collection and rendering are separate modules.
"""

from __future__ import annotations


from auditor.state import (
    CATEGORIES,
    CATEGORY_ORDER,
    STRUCTURAL_EXCEPTIONS,
    PortfolioState,
    RepoState,
    SurfaceState,
    categorize,
)
from auditor.state_render import render


def repo(name: str, grade: str = "A", score: int = 95, findings: int = 1, error: str = "") -> RepoState:
    return RepoState(name=name, grade=grade, score=score, findings=findings, error=error)


def surface(url: str = "https://example.com/", status: int | None = 200,
            non_ascii: int = 0, error: str = "") -> SurfaceState:
    return SurfaceState(url=url, status=status, non_ascii=non_ascii, error=error)


def state(**kw) -> PortfolioState:
    base = dict(
        generated_at="2026-07-19T04:00:00+00:00",
        repos=[repo("orbit-platform"), repo("cab-automation", score=96)],
        surfaces=[surface()],
        scheduled_agents=24,
        ci_status={"portfolio-assistant": "success"},
    )
    base.update(kw)
    return PortfolioState(**base)


# --- categorization -------------------------------------------------------

def test_known_repo_categorized() -> None:
    assert categorize("orbit-platform") == "Control plane and governance"


def test_strategy_repo_categorized() -> None:
    assert categorize("integrated-strategy") == "Technology strategy"


def test_unknown_repo_is_uncategorized() -> None:
    assert categorize("some-brand-new-repo") == "Uncategorized"


def test_every_category_is_in_the_order_list() -> None:
    """A category missing from CATEGORY_ORDER would silently vanish from output."""
    for category in set(CATEGORIES.values()):
        assert category in CATEGORY_ORDER


def test_uncategorized_is_in_order_list() -> None:
    assert "Uncategorized" in CATEGORY_ORDER


# --- aggregate properties -------------------------------------------------

def test_average_score() -> None:
    s = state(repos=[repo("a", score=90), repo("b", score=100)])
    assert s.average_score == 95.0


def test_average_ignores_failed_audits() -> None:
    s = state(repos=[repo("a", score=90), repo("b", error="404")])
    assert s.average_score == 90.0


def test_average_with_no_repos_is_zero() -> None:
    assert state(repos=[]).average_score == 0.0


def test_grade_counts() -> None:
    s = state(repos=[repo("a", grade="A"), repo("b", grade="A"), repo("c", grade="B")])
    assert s.grade_counts == {"A": 2, "B": 1}


def test_below_b_detects_low_scores() -> None:
    s = state(repos=[repo("a", score=95), repo("b", grade="C", score=80)])
    assert [r.name for r in s.below_b] == ["b"]


def test_below_b_excludes_structural_exceptions() -> None:
    name = next(iter(STRUCTURAL_EXCEPTIONS))
    s = state(repos=[repo(name, grade="C", score=76)])
    assert s.below_b == []


def test_uncategorized_listed() -> None:
    s = state(repos=[repo("orbit-platform"), repo("mystery-repo")])
    assert s.uncategorized == ["mystery-repo"]


def test_failing_ci_detected() -> None:
    s = state(ci_status={"a": "success", "b": "failure", "c": "unknown"})
    assert s.failing_ci == ["b"]


def test_unknown_ci_is_not_a_failure() -> None:
    """A repo with no runs yet should not be reported as broken."""
    assert state(ci_status={"a": "unknown"}).failing_ci == []


# --- surface health -------------------------------------------------------

def test_healthy_surface() -> None:
    assert surface().healthy


def test_non_200_is_unhealthy() -> None:
    assert not surface(status=404).healthy


def test_non_ascii_is_unhealthy() -> None:
    assert not surface(non_ascii=12).healthy


def test_error_is_unhealthy() -> None:
    assert not surface(status=None, error="timeout").healthy


def test_unhealthy_surfaces_collected() -> None:
    s = state(surfaces=[surface(), surface(url="https://b/", non_ascii=3)])
    assert len(s.unhealthy_surfaces) == 1


# --- rendering ------------------------------------------------------------

def test_render_includes_generated_timestamp() -> None:
    assert "2026-07-19T04:00:00+00:00" in render(state())


def test_render_warns_against_hand_editing() -> None:
    assert "Do not edit it by hand" in render(state())


def test_render_includes_summary_metrics() -> None:
    out = render(state())
    assert "## Summary" in out
    assert "| Public repos | 2 |" in out
    assert "| Scheduled agents | 24 |" in out


def test_render_clean_state_reports_no_actions() -> None:
    out = render(state())
    assert "## Action items" in out
    assert "None." in out


def test_render_flags_uncategorized_repo() -> None:
    out = render(state(repos=[repo("mystery-repo")]))
    assert "mystery-repo" in out
    assert "not in the category map" in out


def test_render_flags_non_ascii_surface() -> None:
    out = render(state(surfaces=[surface(non_ascii=7)]))
    assert "7 non-ASCII" in out
    assert "Encoding corruption" in out


def test_render_flags_failing_ci() -> None:
    out = render(state(ci_status={"portfolio-assistant": "failure"}))
    assert "CI is failure" in out


def test_render_flags_low_score() -> None:
    out = render(state(repos=[repo("weak", grade="C", score=78)]))
    assert "scores 78/100" in out


def test_render_flags_failed_audit() -> None:
    out = render(state(repos=[repo("gone", error="404 Not Found")]))
    assert "could not be audited" in out


def test_render_groups_by_category() -> None:
    out = render(state(repos=[repo("orbit-platform"), repo("integrated-strategy")]))
    assert "### Technology strategy" in out
    assert "### Control plane and governance" in out


def test_render_orders_categories_consistently() -> None:
    out = render(state(repos=[repo("orbit-platform"), repo("integrated-strategy")]))
    assert out.index("### Technology strategy") < out.index("### Control plane and governance")


def test_render_marks_structural_exceptions() -> None:
    name = next(iter(STRUCTURAL_EXCEPTIONS))
    out = render(state(repos=[repo(name, grade="C", score=76)]))
    assert "Structural exception" in out


def test_render_includes_surface_table() -> None:
    assert "## Live surfaces" in render(state())


def test_render_handles_empty_portfolio() -> None:
    out = render(state(repos=[], surfaces=[], ci_status={}))
    assert "| Public repos | 0 |" in out


def test_render_output_is_pure_ascii() -> None:
    """The generated file must obey the same encoding rule as every other surface."""
    out = render(state(repos=[repo("orbit-platform"), repo("brianpelow", grade="C", score=76)]))
    assert all(ord(c) < 128 for c in out)


def test_render_is_deterministic() -> None:
    s = state()
    assert render(s) == render(s)


def test_render_identical_states_produce_identical_output() -> None:
    assert render(state()) == render(state())