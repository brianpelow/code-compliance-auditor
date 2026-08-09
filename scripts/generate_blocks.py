"""Render the generated surface regions for the dashboard and profile README.

Reads the JSON emitted by generate_state.py and generate_catalog.py. Pure:
no network, no GitHub API calls. Run it after those two in the nightly
workflow, or by hand once both JSON files exist.

The rendered blocks are published in this repo under generated/. Each consumer
surface fetches its own block over raw.githubusercontent.com and splices it
between its markers, so no cross-repo token is ever needed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from auditor.blocks import (  # noqa: E402
    render_dashboard_block,
    render_readme_block,
    render_stats_block,
)


def _load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"[blocks] Missing {path}. Run generate_state.py and "
            "generate_catalog.py first; they emit the JSON this reads."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> int:
    generated = REPO_ROOT / "generated"
    catalog = _load(generated / "catalog.json")
    state = _load(generated / "state.json")

    outputs = {
        "catalog_block.html": render_dashboard_block(catalog, state),
        "catalog_block.md": render_readme_block(catalog, state),
        "stats_block.html": render_stats_block(catalog, state),
    }

    for name, content in outputs.items():
        path = generated / name
        path.write_text(content + "\n", encoding="utf-8")
        print(f"[blocks] Wrote {path} ({len(content)} chars)")

    entries = len(catalog.get("entries", []))
    print(f"[blocks] {entries} repos rendered into 3 blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
