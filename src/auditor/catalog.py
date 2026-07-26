"""Portfolio catalog generator.

Emits PORTFOLIO.md: a running manifest of every public repo, grouped by
category, auto-discovered from the GitHub API. It reuses the collection
primitives and category map from state.py so the two generators never disagree.

Same discipline as the state generator:
- Collection (network) is separated from rendering (pure function), so the
  renderer is tested with fabricated data and no network.
- The rendered output is asserted pure-ASCII.
- A new repo is discovered automatically and always appears; if it lacks a
  category it lands in Uncategorized rather than being dropped, so the gap is
  visible rather than silent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import unicodedata
from datetime import datetime, timezone

import httpx

from auditor.catalog_overrides import BLURB_OVERRIDES, CATEGORY_OVERRIDES
from auditor.state import (
    API,
    CATEGORY_ORDER,
    _headers,
    categorize,
    list_repos,
)


def _ascii_fold(text: str) -> str:
    """Fold external text (GitHub descriptions/topics) to ASCII.

    Descriptions come from the GitHub API and may contain em-dashes or other
    non-ASCII punctuation. Since the catalog output is asserted pure-ASCII,
    external text is normalized: common punctuation is mapped, then anything
    remaining non-ASCII is dropped. Curated blurbs in the overrides file are
    already ASCII and bypass this.
    """
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00b7": "-",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if ord(c) < 128)


@dataclass
class RepoEntry:
    """One repo's catalog record."""

    name: str
    description: str = ""
    topics: list[str] = field(default_factory=list)
    language: str = ""
    is_fork: bool = False
    archived: bool = False

    @property
    def category(self) -> str:
        if self.name in CATEGORY_OVERRIDES:
            return CATEGORY_OVERRIDES[self.name]
        return categorize(self.name)

    @property
    def blurb(self) -> str:
        if self.name in BLURB_OVERRIDES:
            return BLURB_OVERRIDES[self.name]
        return _ascii_fold(self.description) or "(no description)"


@dataclass
class Catalog:
    generated_at: str
    entries: list[RepoEntry] = field(default_factory=list)

    @property
    def by_category(self) -> dict[str, list[RepoEntry]]:
        grouped: dict[str, list[RepoEntry]] = {}
        for e in self.entries:
            grouped.setdefault(e.category, []).append(e)
        for cat in grouped:
            grouped[cat].sort(key=lambda r: r.name.lower())
        return grouped

    @property
    def uncategorized(self) -> list[str]:
        return sorted(e.name for e in self.entries if e.category == "Uncategorized")


def _fetch_repo_meta(client: httpx.Client, owner: str, name: str) -> RepoEntry:
    """Fetch description, topics, and language for one repo."""
    try:
        resp = client.get(f"{API}/repos/{owner}/{name}", headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return RepoEntry(
            name=name,
            description=(data.get("description") or "").strip(),
            topics=data.get("topics", []) or [],
            language=data.get("language") or "",
            is_fork=data.get("fork", False),
            archived=data.get("archived", False),
        )
    except Exception:
        return RepoEntry(name=name)


def collect(owner: str = "brianpelow", timeout: float = 30.0) -> Catalog:
    """Discover every repo and gather its catalog metadata."""
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    catalog = Catalog(generated_at=generated)
    with httpx.Client(timeout=timeout) as client:
        names = list_repos(client)
        for name in names:
            entry = _fetch_repo_meta(client, owner, name)
            # Forks (e.g. an upstream repo cloned for a PR) and the scratch
            # git_test repo are not portfolio artifacts.
            if entry.is_fork or entry.name == "git_test":
                continue
            catalog.entries.append(entry)
    return catalog


def render_catalog(catalog: Catalog) -> str:
    """Render the catalog to markdown. Pure function; no network."""
    lines: list[str] = [
        "# Portfolio Catalog",
        "",
        "> Auto-generated manifest of every public repository. Regenerated nightly "
        "from the GitHub API by the portfolio's own catalog generator. Do not edit "
        "by hand; changes are overwritten on the next run.",
        "",
        f"**Generated:** {catalog.generated_at}  ",
        f"**Total public repositories:** {len(catalog.entries)}",
        "",
        "---",
        "",
    ]

    grouped = catalog.by_category
    for category in CATEGORY_ORDER:
        entries = grouped.get(category)
        if not entries:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for e in entries:
            url = f"https://github.com/brianpelow/{e.name}"
            tags = ""
            if e.topics:
                tags = "  \n  " + " ".join(f"`{_ascii_fold(t)}`" for t in e.topics[:6])
            flag = ""
            if e.archived:
                flag = " *(archived)*"
            lines.append(f"- **[{e.name}]({url})**{flag} - {e.blurb}{tags}")
        lines.append("")

    if catalog.uncategorized:
        lines.append("---")
        lines.append("")
        lines.append("> **Note:** the following repos are not yet in the category map "
                     "and appear under Uncategorized: "
                     + ", ".join(catalog.uncategorized)
                     + ". Add them to CATEGORIES in state.py to file them.")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*This catalog is generated, not maintained by hand. "
                 "The generator lives in code-compliance-auditor and runs nightly.*")
    lines.append("")

    text = "\n".join(lines)
    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii:
        raise AssertionError(f"Catalog contains {non_ascii} non-ASCII characters")
    return text