"""Generate PORTFOLIO.md from live GitHub state.

Run nightly by the workflow, or by hand. Collection hits the GitHub API;
rendering is pure and asserts pure-ASCII output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from auditor.catalog import collect, render_catalog  # noqa: E402
from auditor.catalog_overrides import README_CATEGORY_ORDER  # noqa: E402
from auditor.state import CATEGORY_ORDER  # noqa: E402


def main() -> int:
    catalog = collect("brianpelow")
    md = render_catalog(catalog)
    generated = Path("generated")
    generated.mkdir(exist_ok=True)
    (generated / "catalog.json").write_text(
        json.dumps(
            {
                "generated_at": catalog.generated_at,
                "category_order": list(CATEGORY_ORDER),
                "readme_category_order": list(README_CATEGORY_ORDER),
                "entries": [
                    {
                        "name": e.name,
                        "blurb": e.blurb,
                        "category": e.category,
                        "topics": e.topics,
                        "language": e.language,
                        "archived": e.archived,
                    }
                    for e in catalog.entries
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Wrote generated/catalog.json")

    out = Path("PORTFOLIO.md")
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out} with {len(catalog.entries)} repos")
    if catalog.uncategorized:
        print(f"Uncategorized (add to CATEGORIES): {', '.join(catalog.uncategorized)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())