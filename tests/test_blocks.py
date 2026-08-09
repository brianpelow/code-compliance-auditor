"""Tests for the surface block renderers. Fabricated data only; no network."""

from __future__ import annotations

import pytest

from auditor.blocks import (
    render_dashboard_block,
    render_readme_block,
    render_stats_block,
    short_blurb,
)

CATALOG = {
    "generated_at": "2026-08-08T04:07:24+00:00",
    "category_order": ["Technology strategy", "Observability", "MCP servers"],
    "readme_category_order": ["Observability", "Technology strategy", "MCP servers"],
    "entries": [
        {
            "name": "otel-pipeline-workbench",
            "blurb": "Deterministic workbench for OpenTelemetry Collector configs: lint them "
                     "for correctness, security, and cost-safety. CI-gateable, no LLM.",
            "category": "Observability",
            "topics": ["observability", "opentelemetry", "python"],
            "language": "Python",
        },
        {
            "name": "genai-trace-conformance",
            "blurb": "Conformance validator for GenAI telemetry.",
            "category": "Observability",
            "topics": ["genai"],
            "language": "Python",
        },
        {
            "name": "integrated-strategy",
            "blurb": "The integrated strategy: how it fits together.",
            "category": "Technology strategy",
            "topics": [],
            "language": "",
        },
        {
            "name": "surprise-repo",
            "blurb": "A repo with no category yet.",
            "category": "Uncategorized",
            "topics": [],
            "language": "Python",
        },
    ],
}

STATE = {
    "generated_at": "2026-08-08T04:05:34+00:00",
    "scheduled_agents": 35,
    "repos": [
        {"name": "otel-pipeline-workbench", "grade": "A", "score": 99, "findings": 1},
        {"name": "genai-trace-conformance", "grade": "A", "score": 99, "findings": 1},
        {"name": "integrated-strategy", "grade": "B", "score": 91, "findings": 3},
        {"name": "broken-repo", "grade": "?", "score": 0, "findings": 0, "error": "timeout"},
    ],
    "surfaces": [
        {"url": "https://brianpelow.github.io/", "status": 200, "non_ascii": 0},
        {"url": "https://brianpelow.github.io/portfolio-assistant/", "status": 500, "non_ascii": 0},
    ],
}


def test_dashboard_block_is_pure_ascii():
    html = render_dashboard_block(CATALOG, STATE)
    assert all(ord(c) < 128 for c in html)


def test_dashboard_block_follows_declared_category_order():
    html = render_dashboard_block(CATALOG, STATE)
    strategy = html.index("Technology strategy")
    observability = html.index("Observability")
    assert strategy < observability


def test_uncategorized_appears_rather_than_being_dropped():
    html = render_dashboard_block(CATALOG, STATE)
    assert "surprise-repo" in html
    assert "Uncategorized" in html


def test_declared_category_with_no_entries_is_omitted():
    html = render_dashboard_block(CATALOG, STATE)
    assert "MCP servers" not in html


def test_uncategorized_sorts_after_declared_categories():
    html = render_dashboard_block(CATALOG, STATE)
    assert html.index("Observability") < html.index("Uncategorized")


def test_grade_badge_uses_measured_score():
    html = render_dashboard_block(CATALOG, STATE)
    assert "A 99" in html
    assert "B 91" in html


def test_repo_without_audit_record_gets_no_grade_badge():
    html = render_dashboard_block(CATALOG, STATE)
    card = html[html.index("surprise-repo"):]
    card = card[: card.index("</a>")]
    assert "badge-grade" not in card


def test_errored_audit_is_not_treated_as_a_grade():
    html = render_dashboard_block(CATALOG, STATE)
    assert "broken-repo" not in html


def test_only_first_category_omits_the_margin_offset():
    html = render_dashboard_block(CATALOG, STATE)
    assert html.count('style="margin-top:1px;"') == html.count('class="category"') - 1


def test_readme_uses_its_own_category_order():
    """The dashboard leads with strategy; the README leads with the tools."""
    md = render_readme_block(CATALOG, STATE)
    assert md.index("### Observability") < md.index("### Technology strategy")
    html = render_dashboard_block(CATALOG, STATE)
    assert html.index("Technology strategy") < html.index("Observability")


def test_readme_falls_back_to_the_shared_order_when_unset():
    catalog = {k: v for k, v in CATALOG.items() if k != "readme_category_order"}
    md = render_readme_block(catalog, STATE)
    assert md.index("### Technology strategy") < md.index("### Observability")


def test_readme_block_emits_a_table_per_category():
    md = render_readme_block(CATALOG, STATE)
    assert md.count("| Repo | What it does | Audit |") == 3


def test_readme_table_headers_are_preceded_by_a_blank_line():
    """The exact defect this replaces: a table glued to the line above renders raw."""
    lines = render_readme_block(CATALOG, STATE).split("\n")
    for i, line in enumerate(lines):
        if line.startswith("| Repo |"):
            assert lines[i - 1] == ""


def test_readme_block_strips_pipes_from_blurbs():
    catalog = {**CATALOG, "entries": [
        {"name": "piped", "blurb": "Does a | thing", "category": "Observability",
         "topics": [], "language": ""}
    ]}
    md = render_readme_block(catalog, STATE)
    row = [x for x in md.split("\n") if x.startswith("| [piped]")][0]
    assert row.count("|") == 4


def test_stats_block_counts_only_healthy_surfaces():
    html = render_stats_block(CATALOG, STATE)
    assert "1/2" in html


def test_unverified_surface_is_not_counted_as_an_outage():
    """A check that did not complete is a gap in the check, not a failed surface."""
    state = {**STATE, "surfaces": [
        {"url": "https://a/", "status": 200, "non_ascii": 0},
        {"url": "https://b/", "status": None, "non_ascii": 0,
         "error": "[WinError 10054] reset (after 3 attempts)"},
    ]}
    html = render_stats_block(CATALOG, state)
    assert "1/1" in html
    assert "1 not verified" in html


def test_all_surfaces_verified_shows_the_plain_source_label():
    html = render_stats_block(CATALOG, STATE)
    assert "status and encoding" in html
    assert "not verified" not in html


def test_stats_block_average_excludes_errored_repos():
    html = render_stats_block(CATALOG, STATE)
    assert "96.3" in html


def test_stats_block_counts_categories_from_the_catalog():
    html = render_stats_block(CATALOG, STATE)
    observability = html[html.index("Observability tools") - 200: html.index("Observability tools")]
    assert ">2<" in observability


def test_stats_block_handles_an_empty_portfolio():
    html = render_stats_block({"entries": []}, {"repos": [], "surfaces": []})
    assert "0.0" in html


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("One sentence. Two sentence.", "One sentence."),
        ("Short and sweet", "Short and sweet"),
        ("", ""),
    ],
)
def test_short_blurb_prefers_the_first_sentence(raw, expected):
    assert short_blurb(raw) == expected


def test_short_blurb_falls_back_to_a_word_boundary():
    long = "word " * 60
    out = short_blurb(long)
    assert len(out) <= 153
    assert out.endswith("...")


def test_html_escaping_does_not_double_escape():
    catalog = {**CATALOG, "entries": [
        {"name": "amp", "blurb": "Risk & control <tags>", "category": "Observability",
         "topics": [], "language": ""}
    ]}
    html = render_dashboard_block(catalog, STATE)
    assert "Risk &amp; control &lt;tags&gt;" in html
    assert "&amp;amp;" not in html
