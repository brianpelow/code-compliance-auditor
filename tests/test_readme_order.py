"""The README order must account for every category the catalog can emit."""

from __future__ import annotations

from auditor.catalog_overrides import README_CATEGORY_ORDER
from auditor.state import CATEGORY_ORDER

# Uncategorized is the deliberate catch-all: a repo missing from the category
# map lands there and renders after every declared category, on both surfaces.
# It is never declared in an order list, so it is excluded from both directions.
CATCH_ALL = {"Uncategorized"}


def test_every_category_is_in_the_readme_order_list():
    missing = sorted(set(CATEGORY_ORDER) - set(README_CATEGORY_ORDER) - CATCH_ALL)
    assert not missing, (
        "Categories missing from README_CATEGORY_ORDER: "
        + ", ".join(missing)
        + ". They will still render, but after the declared ones."
    )


def test_readme_order_names_no_unknown_category():
    unknown = sorted(set(README_CATEGORY_ORDER) - set(CATEGORY_ORDER) - CATCH_ALL)
    assert not unknown, "Unknown categories in README_CATEGORY_ORDER: " + ", ".join(unknown)


def test_the_catch_all_is_never_declared():
    """If Uncategorized were declared, a stray repo would sort mid-list unnoticed."""
    assert not CATCH_ALL & set(README_CATEGORY_ORDER)
