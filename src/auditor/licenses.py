"""Known open-source license texts, identified deterministically.

Identification is by git blob SHA-1 of the LF-normalized file, which is the
same identifier git itself stores. This makes the check independent of the
working-tree line endings a given checkout happens to use: a CRLF checkout on
Windows and an LF checkout on Linux produce the same blob SHA for the same
committed content.

Marker phrases provide a second, weaker signal. A file whose blob does not
match a canonical text but which contains a license's marker phrases is a
*variant* -- typically a canonical text with the copyright placeholder filled
in. Variants are reported, not flagged: substituting the copyright line is
permitted by the licenses themselves.
"""

from __future__ import annotations

import hashlib

# Canonical git blob SHA-1 for each license's unmodified text.
# Only SHAs verified against the actual license text appear here. An
# unverified constant is an assertion, and this tool does not ship assertions.
# MIT and BSD-3-Clause are recognized by marker phrases only until their
# canonical blobs are measured.
CANONICAL_BLOBS: dict[str, str] = {
    "d645695673349e3947e8e5ae42332d0ac3164cd7": "Apache-2.0",
}

# Phrases that must all be present for a text to be a plausible variant.
MARKERS: dict[str, tuple[str, ...]] = {
    "Apache-2.0": (
        "Apache License",
        "Grant of Copyright License",
        "Grant of Patent License",
        "Disclaimer of Warranty",
    ),
    "MIT": (
        "Permission is hereby granted, free of charge",
        "THE SOFTWARE IS PROVIDED \"AS IS\"",
    ),
    "BSD-3-Clause": (
        "Redistribution and use in source and binary forms",
        "Neither the name of the copyright holder",
    ),
}

# A real license text is long. Anything shorter is a pointer, not a grant.
MIN_LICENSE_CHARS = 1000


def blob_sha(text: str) -> str:
    """Git blob SHA-1 of text, LF-normalized -- what git would store."""
    data = text.replace("\r\n", "\n").encode("utf-8")
    header = b"blob %d\0" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def identify(text: str) -> tuple[str, str | None]:
    """Classify a license file.

    Returns (verdict, spdx_id) where verdict is one of:
      "canonical" -- byte-identical to a known license text
      "variant"   -- long enough and carries a known license's marker phrases
      "stub"      -- neither; a pointer, a summary, or something else
    """
    sha = blob_sha(text)
    if sha in CANONICAL_BLOBS:
        return "canonical", CANONICAL_BLOBS[sha]

    if len(text) >= MIN_LICENSE_CHARS:
        for spdx, markers in MARKERS.items():
            if all(m in text for m in markers):
                return "variant", spdx

    return "stub", None
