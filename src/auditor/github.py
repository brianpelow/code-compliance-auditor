"""GitHub REST client for collecting a repository snapshot.

Read-only. Uses the public API. A token is optional and only raises rate limits.
"""

from __future__ import annotations

import base64
import os

import httpx

from auditor.models import RepoSnapshot

API = "https://api.github.com"

# Files worth reading in full, because rules inspect their contents.
KEY_FILES = [
    "README.md",
    "LICENSE",
    "LICENSE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "package.json",
    ".gitignore",
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "docs/CODEOWNERS",
]

MAX_SOURCE_FILES = 25
SOURCE_SUFFIXES = (".py", ".js", ".ts", ".go", ".rb", ".java")

SKIP_DIR_PARTS = (
    "node_modules/",
    ".venv/",
    "venv/",
    "dist/",
    "build/",
    "site-packages/",
    "vendor/",
    ".git/",
)


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _is_skippable(path: str) -> bool:
    return any(part in path for part in SKIP_DIR_PARTS)


def fetch_snapshot(owner: str, name: str, timeout: float = 20.0) -> RepoSnapshot:
    """Collect a repository snapshot. Raises on network or 404 errors."""
    snap = RepoSnapshot(owner=owner, name=name)

    with httpx.Client(timeout=timeout, headers=_headers()) as client:
        meta = client.get(f"{API}/repos/{owner}/{name}")
        meta.raise_for_status()
        data = meta.json()
        snap.default_branch = data.get("default_branch") or "main"
        snap.description = data.get("description") or ""
        snap.topics = data.get("topics") or []
        snap.archived = bool(data.get("archived"))

        tree = client.get(
            f"{API}/repos/{owner}/{name}/git/trees/{snap.default_branch}",
            params={"recursive": "1"},
        )
        tree.raise_for_status()
        entries = tree.json().get("tree", [])
        snap.paths = [
            e["path"] for e in entries if e.get("type") == "blob" and not _is_skippable(e["path"])
        ]

        wanted: list[str] = [p for p in KEY_FILES if p in snap.paths]

        sources = [
            p
            for p in snap.paths
            if p.endswith(SOURCE_SUFFIXES) and not _is_skippable(p)
        ]
        wanted.extend(sorted(sources)[:MAX_SOURCE_FILES])

        for path in wanted:
            content = _fetch_file(client, owner, name, path)
            if content is not None:
                snap.files[path] = content

    return snap


def _fetch_file(client: httpx.Client, owner: str, name: str, path: str) -> str | None:
    try:
        r = client.get(f"{API}/repos/{owner}/{name}/contents/{path}")
        if r.status_code != 200:
            return None
        payload = r.json()
        if isinstance(payload, list):
            return None
        if payload.get("encoding") != "base64":
            return None
        raw = base64.b64decode(payload.get("content", ""))
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def parse_repo_arg(value: str) -> tuple[str, str]:
    """Accept 'owner/name' or a full GitHub URL."""
    cleaned = value.strip().rstrip("/")
    if cleaned.startswith("http"):
        parts = [p for p in cleaned.split("/") if p]
        cleaned = "/".join(parts[-2:])
    if cleaned.endswith(".git"):
        cleaned = cleaned[: -len(".git")]
    if "/" not in cleaned:
        raise ValueError(f"Expected owner/name, got: {value}")
    owner, _, name = cleaned.partition("/")
    if not owner or not name:
        raise ValueError(f"Expected owner/name, got: {value}")
    return owner, name