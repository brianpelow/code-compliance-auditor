"""Shared fixtures. All tests run against in-memory snapshots -- no network."""

from __future__ import annotations

import pytest

from auditor.models import RepoSnapshot


@pytest.fixture
def clean_repo() -> RepoSnapshot:
    """A well-governed repository that should score highly."""
    return RepoSnapshot(
        owner="example",
        name="clean",
        paths=[
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            ".gitignore",
            ".github/CODEOWNERS",
            ".github/workflows/ci.yml",
            "docs/adr/0001-use-postgres.md",
            "src/app/main.py",
            "tests/test_main.py",
        ],
        files={
            "README.md": "# Clean\n\n" + ("Thorough documentation. " * 30),
            "LICENSE": "Apache License 2.0",
            "CHANGELOG.md": "# Changelog\n\n## [1.0.0]",
            "CONTRIBUTING.md": "# Contributing\n\nRun the tests.",
            "SECURITY.md": "# Security\n\nReport issues to security@example.com",
            ".gitignore": "__pycache__/\n.env\n.venv/\n",
            ".github/CODEOWNERS": "* @example",
            ".github/workflows/ci.yml": "name: CI",
            "docs/adr/0001-use-postgres.md": "# Use Postgres\n\n## Context",
            "src/app/main.py": (
                "def handler(event: dict) -> dict:\n"
                "    try:\n"
                "        return {'ok': True}\n"
                "    except ValueError:\n"
                "        return {'ok': False}\n"
            ),
        },
    )


@pytest.fixture
def messy_repo() -> RepoSnapshot:
    """A repository with problems across all three agents."""
    return RepoSnapshot(
        owner="example",
        name="messy",
        paths=["main.py", "requirements.txt", ".env"],
        files={
            "main.py": (
                "import subprocess\n"
                "password = 'supersecret123'\n"
                "def run(cmd):\n"
                "    try:\n"
                "        return subprocess.run(cmd, shell=True)\n"
                "    except:\n"
                "        pass\n"
                "# TODO: fix this\n" * 10
            ),
            "requirements.txt": "requests\nhttpx\npydantic\n",
        },
    )


@pytest.fixture
def empty_repo() -> RepoSnapshot:
    """A repository with nothing in it."""
    return RepoSnapshot(owner="example", name="empty", paths=[], files={})