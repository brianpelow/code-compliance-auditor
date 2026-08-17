"""CMP011: a LICENSE file must contain a license, not a pointer to one.

The stub fixture below is the exact text this portfolio carried in all 44
repositories while passing CMP002. A rule that finds nothing on the corpus it
was written for is untested, so the corpus is reconstructed here.
"""

from __future__ import annotations

from pathlib import Path

from auditor.agents.compliance import ComplianceAgent
from auditor.licenses import blob_sha, identify
from auditor.models import RepoSnapshot

APACHE = Path("LICENSE").read_text(encoding="utf-8")

STUB = (
    "Apache License 2.0\n"
    "Copyright 2026 Brian Pelow\n"
    "Licensed under the Apache License, Version 2.0. You may obtain a copy at\n"
    "http://www.apache.org/licenses/LICENSE-2.0\n"
)

BOILERPLATE = (
    "Apache License\n"
    "Version 2.0, January 2004\n"
    "Licensed under the Apache License, Version 2.0 (the \"License\");\n"
    "you may not use this file except in compliance with the License.\n"
    "You may obtain a copy of the License at\n"
    "    http://www.apache.org/licenses/LICENSE-2.0\n"
)


def rule_ids(result) -> set[str]:
    return {f.rule_id for f in result.findings}


def snap_with(license_text: str | None) -> RepoSnapshot:
    paths = ["README.md"]
    files = {"README.md": "# Project\n\nSubstantial readme content here.\n"}
    if license_text is not None:
        paths.append("LICENSE")
        files["LICENSE"] = license_text
    return RepoSnapshot(owner="e", name="e", paths=paths, files=files)


def test_canonical_apache_is_identified() -> None:
    assert identify(APACHE) == ("canonical", "Apache-2.0")


def test_blob_sha_matches_git() -> None:
    assert blob_sha(APACHE) == "d645695673349e3947e8e5ae42332d0ac3164cd7"


def test_crlf_checkout_produces_same_blob() -> None:
    """A Windows checkout must not change the verdict."""
    assert blob_sha(APACHE.replace("\n", "\r\n")) == blob_sha(APACHE)


def test_stub_is_identified_as_stub() -> None:
    assert identify(STUB) == ("stub", None)


def test_boilerplate_appendix_is_a_stub() -> None:
    """The 'how to apply' appendix is not the license."""
    assert identify(BOILERPLATE) == ("stub", None)


def test_variant_with_substituted_copyright_is_not_flagged() -> None:
    variant = APACHE.replace("[yyyy] [name of copyright owner]", "2026 Brian Pelow")
    verdict, spdx = identify(variant)
    assert verdict in ("canonical", "variant")
    assert spdx == "Apache-2.0"


def test_cmp011_fires_on_stub() -> None:
    assert "CMP011" in rule_ids(ComplianceAgent().run(snap_with(STUB)))


def test_cmp011_silent_on_canonical() -> None:
    assert "CMP011" not in rule_ids(ComplianceAgent().run(snap_with(APACHE)))


def test_cmp011_not_raised_when_license_absent() -> None:
    """Absence is CMP002's finding. CMP011 must not double-report it."""
    ids = rule_ids(ComplianceAgent().run(snap_with(None)))
    assert "CMP002" in ids
    assert "CMP011" not in ids
