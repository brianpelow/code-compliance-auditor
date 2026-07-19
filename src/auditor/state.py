"""Portfolio state generation.

Produces a machine-generated snapshot of live portfolio state so that no
document has to assert a number that can go stale. The dashboard already
fetches its repo count from the API rather than hardcoding it; this applies
the same principle to the project context document.

Collection is separated from rendering so the rendering half is testable
without network access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

API = "https://api.github.com"
OWNER = "brianpelow"

# Category assignment is an explicit map rather than inference. A repo the map
# does not know about is reported as uncategorized, which is how a new build
# announces that the catalog needs updating.
CATEGORIES: dict[str, str] = {
    # Technology strategy
    "integrated-strategy": "Technology strategy",
    "platform-engineering-thesis": "Technology strategy",
    "engineering-operating-model": "Technology strategy",
    "ai-governance-framework": "Technology strategy",
    # Control plane and governance
    "orbit-platform": "Control plane and governance",
    "cab-automation": "Control plane and governance",
    "code-compliance-auditor": "Control plane and governance",
    "regulatory-change-impact-agent": "Control plane and governance",
    "fintech-platform-reference": "Control plane and governance",
    "platform-conductor": "Control plane and governance",
    # Autonomous intelligence
    "ai-regulation-tracker": "Autonomous intelligence",
    "weekly-platform-intelligence": "Autonomous intelligence",
    "BoardroomBrief": "Autonomous intelligence",
    # Agentic systems
    "IncidentPilot": "Agentic systems",
    "DataPipelineAgent": "Agentic systems",
    "ai-incident-war-room": "Agentic systems",
    # MCP servers
    "mcp-incident-intel": "MCP servers",
    "mcp-compliance-grc": "MCP servers",
    "mcp-developer-portal": "MCP servers",
    # Engineering metrics
    "TeamHealthRadar": "Engineering metrics",
    "PlatformSLOBoard": "Engineering metrics",
    "TechDebtLedger": "Engineering metrics",
    # Platform patterns
    "platform-maturity-model": "Platform patterns",
    "innersource-scorecard": "Platform patterns",
    "service-catalog-sync": "Platform patterns",
    # Developer productivity
    "repoforge": "Developer productivity",
    "pr-autopilot": "Developer productivity",
    "runbook-gen": "Developer productivity",
    # Interactive tools
    "portfolio-assistant": "Interactive tools",
    "cto-interview-simulator": "Interactive tools",
    "platform-maturity-assessment": "Interactive tools",
    # Just for fun
    "vibe-check-cli": "Just for fun",
    "code-roast": "Just for fun",
    "sports-analytics-for-engineers": "Just for fun",
    # Meta
    "brianpelow": "Meta",
    "brianpelow.github.io": "Meta",
}

CATEGORY_ORDER: tuple[str, ...] = (
    "Technology strategy",
    "Control plane and governance",
    "Autonomous intelligence",
    "Agentic systems",
    "Interactive tools",
    "MCP servers",
    "Engineering metrics",
    "Platform patterns",
    "Developer productivity",
    "Just for fun",
    "Meta",
    "Uncategorized",
)

SURFACES: tuple[str, ...] = (
    "https://brianpelow.github.io/",
    "https://brianpelow.github.io/portfolio-assistant/",
    "https://brianpelow.github.io/cto-interview-simulator/",
    "https://brianpelow.github.io/platform-maturity-assessment/",
    "https://brianpelow.github.io/ai-incident-war-room/",
)

WEB_TOOLS: tuple[str, ...] = (
    "portfolio-assistant",
    "cto-interview-simulator",
    "platform-maturity-assessment",
    "ai-incident-war-room",
    "brianpelow.github.io",
)

# Repos where absent CI or tests is a structural fact, not a gap.
STRUCTURAL_EXCEPTIONS: dict[str, str] = {
    "brianpelow": "Profile README. CI and tests do not apply to one markdown file.",
    "fintech-platform-reference": "Docs-only by design.",
}


def categorize(name: str) -> str:
    return CATEGORIES.get(name, "Uncategorized")


@dataclass
class RepoState:
    name: str
    grade: str = "?"
    score: int = 0
    findings: int = 0
    error: str = ""

    @property
    def category(self) -> str:
        return categorize(self.name)

    @property
    def ok(self) -> bool:
        return not self.error


@dataclass
class SurfaceState:
    url: str
    status: int | None = None
    non_ascii: int = 0
    error: str = ""

    @property
    def healthy(self) -> bool:
        return self.status == 200 and self.non_ascii == 0 and not self.error


@dataclass
class PortfolioState:
    generated_at: str
    repos: list[RepoState] = field(default_factory=list)
    surfaces: list[SurfaceState] = field(default_factory=list)
    scheduled_agents: int = 0
    ci_status: dict[str, str] = field(default_factory=dict)

    @property
    def audited(self) -> list[RepoState]:
        return [r for r in self.repos if r.ok]

    @property
    def average_score(self) -> float:
        scored = self.audited
        return round(sum(r.score for r in scored) / len(scored), 1) if scored else 0.0

    @property
    def grade_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.audited:
            counts[r.grade] = counts.get(r.grade, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def uncategorized(self) -> list[str]:
        return sorted(r.name for r in self.repos if r.category == "Uncategorized")

    @property
    def below_b(self) -> list[RepoState]:
        return sorted(
            (r for r in self.audited if r.score < 85 and r.name not in STRUCTURAL_EXCEPTIONS),
            key=lambda r: r.score,
        )

    @property
    def unhealthy_surfaces(self) -> list[SurfaceState]:
        return [s for s in self.surfaces if not s.healthy]

    @property
    def failing_ci(self) -> list[str]:
        return sorted(k for k, v in self.ci_status.items() if v not in ("success", "unknown"))


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def list_repos(client: httpx.Client) -> list[str]:
    """All public repo names, paginated."""
    names: list[str] = []
    page = 1
    while True:
        r = client.get(
            f"{API}/users/{OWNER}/repos",
            params={"type": "public", "per_page": 100, "page": page},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        names.extend(item["name"] for item in batch)
        if len(batch) < 100:
            break
        page += 1
    return sorted(names)


def count_scheduled_agents(client: httpx.Client, repos: list[str]) -> int:
    """Workflows containing a schedule trigger, across all repos."""
    total = 0
    for name in repos:
        try:
            listing = client.get(f"{API}/repos/{OWNER}/{name}/contents/.github/workflows")
            if listing.status_code != 200:
                continue
            entries = listing.json()
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not entry.get("name", "").endswith((".yml", ".yaml")):
                    continue
                raw = client.get(entry["download_url"])
                if raw.status_code == 200 and "schedule:" in raw.text:
                    total += 1
        except Exception:
            continue
    return total


SURFACE_ATTEMPTS = 3
SURFACE_BACKOFF_SECONDS = 1.5
SURFACE_TIMEOUT = 25.0


def check_surface(url: str, client: object | None = None) -> SurfaceState:
    """Check a live surface on a connection independent of the API client.

    Two distinct failure modes are handled here.

    First, the shared client has already made hundreds of API calls to a
    different host by the time surfaces are checked. Its connection pool is
    stale, and reusing it produces connection resets that look like outages
    but are not. Each attempt therefore opens its own client.

    Second, a single reset is not evidence a surface is down, so transient
    failures are retried. A false outage in a status document teaches the
    reader to skip the whole section, which is worse than reporting nothing.

    `client` is injectable so tests can supply a stub and run without network.
    """
    import time

    last_error = ""
    for attempt in range(SURFACE_ATTEMPTS):
        try:
            if client is not None:
                r = client.get(url, headers={"Cache-Control": "no-cache"})
            else:
                with httpx.Client(
                    timeout=SURFACE_TIMEOUT,
                    follow_redirects=True,
                    headers={"User-Agent": "portfolio-state-generator"},
                ) as fresh:
                    r = fresh.get(url, headers={"Cache-Control": "no-cache"})
                    body = r.text
                    return SurfaceState(
                        url=url,
                        status=r.status_code,
                        non_ascii=sum(1 for ch in body if ord(ch) > 127),
                    )

            body = r.text
            return SurfaceState(
                url=url,
                status=r.status_code,
                non_ascii=sum(1 for ch in body if ord(ch) > 127),
            )
        except Exception as exc:
            last_error = str(exc)[:70]
            if attempt < SURFACE_ATTEMPTS - 1:
                time.sleep(SURFACE_BACKOFF_SECONDS)

    return SurfaceState(url=url, error=f"{last_error} (after {SURFACE_ATTEMPTS} attempts)")



def latest_ci(client: httpx.Client, repo: str) -> str:
    try:
        r = client.get(f"{API}/repos/{OWNER}/{repo}/actions/runs", params={"per_page": 1})
        if r.status_code != 200:
            return "unknown"
        runs = r.json().get("workflow_runs", [])
        if not runs:
            return "unknown"
        return runs[0].get("conclusion") or runs[0].get("status") or "unknown"
    except Exception:
        return "unknown"


def collect(audit_fn, timeout: float = 30.0) -> PortfolioState:
    """Gather live state. audit_fn is injected so tests can supply a stub."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    state = PortfolioState(generated_at=now)

    with httpx.Client(timeout=timeout, headers=_headers(), follow_redirects=True) as client:
        names = list_repos(client)

        for name in names:
            try:
                report = audit_fn(f"{OWNER}/{name}")
                state.repos.append(
                    RepoState(
                        name=name,
                        grade=report.grade,
                        score=report.overall_score,
                        findings=len(report.all_findings),
                    )
                )
            except Exception as exc:
                state.repos.append(RepoState(name=name, error=str(exc)[:60]))

        state.scheduled_agents = count_scheduled_agents(client, names)
        state.surfaces = [check_surface(u) for u in SURFACES]
        state.ci_status = {t: latest_ci(client, t) for t in WEB_TOOLS if t in names}

    return state