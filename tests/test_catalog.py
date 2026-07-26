"""Catalog renderer tests. Pure function, fabricated data, no network."""

from __future__ import annotations

from auditor.catalog import Catalog, RepoEntry, _ascii_fold, render_catalog


def _catalog(entries):
    return Catalog(generated_at="2026-01-01T00:00:00+00:00", entries=entries)


def test_ascii_fold_maps_em_dash():
    assert _ascii_fold("a \u2014 b") == "a - b"


def test_ascii_fold_drops_remaining_non_ascii():
    out = _ascii_fold("caf\u00e9 \u2603")
    assert all(ord(c) < 128 for c in out)


def test_render_is_pure_ascii():
    entries = [RepoEntry("repo-x", description="does a thing \u2014 nicely")]
    md = render_catalog(_catalog(entries))
    assert all(ord(c) < 128 for c in md)


def test_render_groups_by_category():
    entries = [
        RepoEntry("mcp-governance-gateway", description="gateway"),
        RepoEntry("ai-model-autopsy", description="autopsy"),
    ]
    md = render_catalog(_catalog(entries))
    assert "## MCP servers" in md
    assert "## Agentic systems" in md


def test_blurb_override_wins_over_description():
    e = RepoEntry("mcp-governance-gateway", description="raw github description")
    assert "policy engine" in e.blurb
    assert "raw github description" not in e.blurb


def test_unknown_repo_uses_github_description():
    e = RepoEntry("some-new-repo", description="a fresh repo")
    assert e.blurb == "a fresh repo"


def test_uncategorized_repo_is_flagged_not_dropped():
    entries = [RepoEntry("mystery-repo", description="unknown")]
    cat = _catalog(entries)
    assert "mystery-repo" in cat.uncategorized
    md = render_catalog(cat)
    # It still appears in the output under Uncategorized, never silently dropped
    assert "mystery-repo" in md


def test_empty_description_shows_placeholder():
    e = RepoEntry("bare-repo", description="")
    assert e.blurb == "(no description)"


def test_topics_rendered_as_tags():
    entries = [RepoEntry("repo-x", description="d", topics=["python", "governance"])]
    md = render_catalog(_catalog(entries))
    assert "`python`" in md
    assert "`governance`" in md


def test_archived_repo_flagged():
    entries = [RepoEntry("old-repo", description="d", archived=True)]
    md = render_catalog(_catalog(entries))
    assert "(archived)" in md