"""Render the generated catalog regions spliced into the portfolio's surfaces.

The dashboard (brianpelow.github.io) and the profile README both used to carry
a hand-maintained copy of the repo inventory. Hand-maintained copies of a
generated list drift, and every categorization error the portfolio has shipped
lived in one of those copies. These renderers produce the regions instead, from
the same JSON the catalog and state generators emit.

Discipline, matching the other generators:

- Pure functions over plain dicts. No network, no imports beyond the stdlib,
  so the tests need no fakes and no fixtures beyond a literal.
- Output is asserted pure-ASCII. The dashboard's CI guard fails on any
  non-ASCII byte in index.html, so a block that smuggled one in would break
  the build rather than corrupt silently.
- Repo badges carry the MEASURED audit grade, not an asserted "CI passing".
  A badge the portfolio cannot verify is the same defect class as a
  hand-maintained list.
"""

from __future__ import annotations

MAX_BLURB = 150

_ENTITIES = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
}


def escape(text: str) -> str:
    """Escape HTML-significant characters. Ampersand first, or entities double-escape."""
    out = text.replace("&", "&amp;")
    for char, entity in _ENTITIES.items():
        if char == "&":
            continue
        out = out.replace(char, entity)
    return out


def assert_ascii(text: str, label: str) -> str:
    offenders = sorted({c for c in text if ord(c) > 127})
    if offenders:
        codes = ", ".join(f"U+{ord(c):04X}" for c in offenders)
        raise AssertionError(f"{label} contains non-ASCII characters: {codes}")
    return text


def short_blurb(blurb: str, limit: int = MAX_BLURB) -> str:
    """First sentence of a blurb, capped.

    Catalog blurbs run long because PORTFOLIO.md has room for them. A dashboard
    card does not. Truncation is deterministic: first sentence boundary, else a
    word boundary under the cap.
    """
    text = " ".join(blurb.split())
    if not text:
        return ""
    for stop in (". ", "? ", "! "):
        idx = text.find(stop)
        if 0 < idx <= limit:
            return text[: idx + 1]
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0]
    return clipped.rstrip(",;:-") + "..."


def _grades(state: dict) -> dict[str, dict]:
    return {r["name"]: r for r in state.get("repos", []) if not r.get("error")}


def _ordered(catalog: dict, order_key: str = "category_order") -> list[tuple[str, list[dict]]]:
    """Group entries by category, following a declared order.

    The dashboard and the README present the same categories in different
    sequences, so each names its own order key. Any category not in the
    declared order still appears, sorted after the declared ones, because a
    silently dropped repo is the failure this whole module exists to prevent.
    """
    grouped: dict[str, list[dict]] = {}
    for entry in catalog.get("entries", []):
        grouped.setdefault(entry.get("category", "Uncategorized"), []).append(entry)
    for entries in grouped.values():
        entries.sort(key=lambda e: e["name"].lower())

    ordered: list[tuple[str, list[dict]]] = []
    declared = list(catalog.get(order_key) or catalog.get("category_order", ()))
    for category in declared:
        if grouped.get(category):
            ordered.append((category, grouped[category]))
    for category in sorted(grouped):
        if category not in declared:
            ordered.append((category, grouped[category]))
    return ordered


def render_dashboard_block(catalog: dict, state: dict) -> str:
    """Render the dashboard's repository catalog as an HTML fragment."""
    grades = _grades(state)
    lines: list[str] = []
    first = True

    for category, entries in _ordered(catalog):
        style = "" if first else ' style="margin-top:1px;"'
        first = False
        lines.append(f'  <div class="category"{style}>')
        lines.append(f'    <div class="category-title">{escape(category)}</div>')
        lines.append('    <div class="repo-grid">')
        for entry in entries:
            name = entry["name"]
            url = f"https://github.com/brianpelow/{name}"
            lines.append(f'      <a class="repo-card" href="{url}" target="_blank">')
            lines.append(f'        <div class="repo-name">{escape(name)}</div>')
            desc = short_blurb(entry.get("blurb", ""))
            lines.append(f'        <div class="repo-desc">{escape(desc)}</div>')

            badges: list[str] = []
            language = entry.get("language") or ""
            if language:
                badges.append(f'<span class="badge">{escape(language)}</span>')
            for topic in entry.get("topics", [])[:2]:
                badges.append(f'<span class="badge">{escape(topic)}</span>')
            record = grades.get(name)
            if record:
                grade = escape(str(record.get("grade", "?")))
                score = int(record.get("score", 0))
                badges.append(
                    f'<span class="badge badge-grade" title="deterministic audit score">'
                    f"{grade} {score}</span>"
                )
            lines.append(f'        <div class="repo-meta">{"".join(badges)}</div>')
            lines.append("      </a>")
        lines.append("    </div>")
        lines.append("  </div>")

    return assert_ascii("\n".join(lines), "dashboard catalog block")


def render_readme_block(catalog: dict, state: dict) -> str:
    """Render the profile README's catalog as markdown tables, one per category."""
    grades = _grades(state)
    lines: list[str] = []

    for category, entries in _ordered(catalog, "readme_category_order"):
        lines.append(f"### {category}")
        lines.append("")
        lines.append("| Repo | What it does | Audit |")
        lines.append("|------|--------------|-------|")
        for entry in entries:
            name = entry["name"]
            url = f"https://github.com/brianpelow/{name}"
            blurb = short_blurb(entry.get("blurb", ""), limit=180).replace("|", "-")
            record = grades.get(name)
            audit = f"{record['grade']} {record['score']}" if record else "-"
            lines.append(f"| [{name}]({url}) | {blurb} | {audit} |")
        lines.append("")

    return assert_ascii("\n".join(lines), "readme catalog block")


def render_stats_block(catalog: dict, state: dict) -> str:
    """Render the dashboard stat tiles from measured values.

    Every tile here was hardcoded before, and three of them had drifted. A tile
    whose number cannot be traced to a generator does not belong on this page.
    """
    entries = catalog.get("entries", [])
    audited = [r for r in state.get("repos", []) if not r.get("error")]
    scores = [int(r.get("score", 0)) for r in audited]
    average = round(sum(scores) / len(scores), 1) if scores else 0.0
    surfaces = state.get("surfaces", [])
    verified = [s for s in surfaces if s.get("status") is not None]
    healthy = sum(
        1 for s in verified if s.get("status") == 200 and not s.get("non_ascii") and not s.get("error")
    )
    unverified = len(surfaces) - len(verified)
    surface_source = (
        f"{unverified} not verified" if unverified else "status and encoding"
    )
    by_category: dict[str, int] = {}
    for entry in entries:
        category = entry.get("category", "Uncategorized")
        by_category[category] = by_category.get(category, 0) + 1

    tiles = [
        (str(len(entries)), "Public repos", "auto-discovered", "accent"),
        (str(state.get("scheduled_agents", 0)), "Scheduled agents", "workflow schedules", "green"),
        (f"{average:.1f}", "Audit average", "deterministic scoring", ""),
        (f"{healthy}/{len(verified)}", "Surfaces healthy", surface_source, "green"),
        (str(by_category.get("MCP servers", 0)), "MCP servers", "model context protocol", "accent"),
        (str(by_category.get("Observability", 0)), "Observability tools", "otel and genai traces", ""),
    ]

    lines = ['  <div class="stats-bar">']
    for value, label, source, tone in tiles:
        cls = f"stat-value {tone}".strip()
        lines.append('    <div class="stat">')
        lines.append(f'      <div class="{cls}">{escape(value)}</div>')
        lines.append(f'      <div class="stat-label">{escape(label)}</div>')
        lines.append(f'      <div class="stat-source">{escape(source)}</div>')
        lines.append("    </div>")
    lines.append("  </div>")

    return assert_ascii("\n".join(lines), "stats block")
