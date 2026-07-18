"""Runs all agents against a snapshot and produces a report."""

from __future__ import annotations

import os

from auditor.agents import ComplianceAgent, DebtAgent, SecurityAgent
from auditor.github import fetch_snapshot, parse_repo_arg
from auditor.models import AuditReport, RepoSnapshot
from auditor.verdict import build_report


def audit_snapshot(snap: RepoSnapshot, api_key: str = "") -> AuditReport:
    """Audit an already-collected snapshot. Pure function, no network."""
    security = SecurityAgent().run(snap)
    compliance = ComplianceAgent().run(snap)
    debt = DebtAgent().run(snap)
    return build_report(snap.full_name, security, compliance, debt, api_key=api_key)


def audit_repo(repo: str, api_key: str | None = None) -> AuditReport:
    """Fetch and audit a repository by 'owner/name' or URL."""
    owner, name = parse_repo_arg(repo)
    snap = fetch_snapshot(owner, name)
    key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
    return audit_snapshot(snap, api_key=key)