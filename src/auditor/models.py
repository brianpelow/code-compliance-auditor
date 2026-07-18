"""Core data models for the auditor.

All findings are deterministic: the same repository snapshot always produces
the same findings, with the same severities and the same scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Finding severity, ordered from most to least urgent."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.CRITICAL: 30,
    Severity.HIGH: 15,
    Severity.MEDIUM: 7,
    Severity.LOW: 3,
    Severity.INFO: 0,
}

SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


@dataclass(frozen=True)
class Finding:
    """A single deterministic audit finding."""

    rule_id: str
    title: str
    severity: Severity
    detail: str
    path: str | None = None
    remediation: str = ""

    def weight(self) -> int:
        return SEVERITY_WEIGHTS[self.severity]


@dataclass
class RepoSnapshot:
    """An immutable view of a repository at audit time.

    Collected once and passed to every agent, so all agents evaluate
    exactly the same inputs.
    """

    owner: str
    name: str
    paths: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    default_branch: str = "main"
    description: str = ""
    topics: list[str] = field(default_factory=list)
    archived: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    def has_path(self, *candidates: str) -> bool:
        """True if any candidate path exists (case-insensitive)."""
        lowered = {p.lower() for p in self.paths}
        return any(c.lower() in lowered for c in candidates)

    def find_paths(self, predicate) -> list[str]:
        return [p for p in self.paths if predicate(p)]

    def source_files(self, suffix: str = ".py") -> dict[str, str]:
        return {p: c for p, c in self.files.items() if p.endswith(suffix)}


@dataclass
class AgentResult:
    """The output of a single scanning agent."""

    agent: str
    score: int
    findings: list[Finding] = field(default_factory=list)
    checks_run: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.HIGH)


@dataclass
class AuditReport:
    """The complete audit result for one repository."""

    repo: str
    security: AgentResult
    compliance: AgentResult
    debt: AgentResult
    overall_score: int
    grade: str
    summary: str = ""
    priorities: list[Finding] = field(default_factory=list)

    @property
    def all_findings(self) -> list[Finding]:
        return [*self.security.findings, *self.compliance.findings, *self.debt.findings]


def score_from_findings(findings: list[Finding], floor: int = 0) -> int:
    """Deterministic score: start at 100, subtract severity weights, clamp."""
    score = 100 - sum(f.weight() for f in findings)
    return max(floor, min(100, score))


def grade_from_score(score: int) -> str:
    """Map a 0-100 score to a letter grade."""
    if score >= 93:
        return "A"
    if score >= 85:
        return "B"
    if score >= 75:
        return "C"
    if score >= 65:
        return "D"
    return "F"


def prioritize(findings: list[Finding], limit: int = 5) -> list[Finding]:
    """Top findings ordered by severity, then rule_id for stable output."""
    ordered = sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule_id))
    return ordered[:limit]