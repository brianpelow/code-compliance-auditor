"""Generate PORTFOLIO.md from live GitHub state.

Run nightly by the workflow, or by hand. Collection hits the GitHub API;
rendering is pure and asserts pure-ASCII output.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from auditor.catalog import collect, render_catalog  # noqa: E402


def main() -> int:
    catalog = collect("brianpelow")
    md = render_catalog(catalog)
    out = Path("PORTFOLIO.md")
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out} with {len(catalog.entries)} repos")
    if catalog.uncategorized:
        print(f"Uncategorized (add to CATEGORIES): {', '.join(catalog.uncategorized)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())