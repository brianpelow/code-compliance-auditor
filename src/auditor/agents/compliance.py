"""ComplianceAgent -- deterministic repository governance checks.

Checks map to widely published control expectations: change authorization and
segregation of duties (SOX ITGC), documented ownership and traceability
(SOC 2 CC-series), and secure SDLC documentation (PCI-DSS Requirement 6).
Only public standards are referenced. No organization-specific controls.
"""

from __future__ import annotations

from auditor.models import AgentResult, Finding, RepoSnapshot, Severity, score_from_findings
from auditor.licenses import identify as identify_license

CI_DIR = ".github/workflows"

TEST_HINTS = ("test_", "_test.", "/tests/", "spec.", ".spec.")


class ComplianceAgent:
    """Scans for governance and auditability artifacts."""

    name = "ComplianceAgent"

    def run(self, snap: RepoSnapshot) -> AgentResult:
        findings: list[Finding] = []
        checks = 0

        checks += self._check_ownership(snap, findings)
        checks += self._check_license(snap, findings)
        checks += self._check_ci(snap, findings)
        checks += self._check_tests(snap, findings)
        checks += self._check_docs(snap, findings)
        checks += self._check_adrs(snap, findings)
        checks += self._check_archived(snap, findings)

        return AgentResult(
            agent=self.name,
            score=score_from_findings(findings),
            findings=findings,
            checks_run=checks,
        )

    def _check_ownership(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        if not snap.has_path("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"):
            findings.append(
                Finding(
                    rule_id="CMP001",
                    title="No CODEOWNERS file",
                    severity=Severity.HIGH,
                    detail=(
                        "No named owner for changes. Reviewer assignment cannot be enforced, "
                        "which weakens segregation-of-duties evidence."
                    ),
                    remediation="Add .github/CODEOWNERS and require owner review on protected branches.",
                )
            )
        return 1

    def _check_license(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        if not snap.has_path("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
            findings.append(
                Finding(
                    rule_id="CMP002",
                    title="No LICENSE file",
                    severity=Severity.MEDIUM,
                    detail="Absent license terms create downstream legal ambiguity.",
                    remediation="Add an explicit LICENSE file.",
                )
            )
            return 1
        return 1 + self._check_license_content(snap, findings)

    def _check_license_content(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        """A LICENSE file that is not a license text grants nothing.

        CMP002 checks that the file exists. Existence is not a grant: a pointer
        to a URL, or a four-line summary, leaves recipients without the terms
        the project claims to offer. Apache-2.0 section 4(a) requires that
        recipients be given a copy of the License itself.
        """
        text = None
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
            for path, content in snap.files.items():
                if path.lower() == name.lower():
                    text = content
                    break
            if text is not None:
                break

        if text is None:
            return 0

        verdict, _spdx = identify_license(text)
        if verdict == "stub":
            findings.append(
                Finding(
                    rule_id="CMP011",
                    title="LICENSE file is not a recognized license text",
                    severity=Severity.MEDIUM,
                    detail=(
                        "A LICENSE file is present but does not contain a recognized "
                        "license text. A pointer or summary does not convey the terms, "
                        "so downstream recipients have no grant to rely on and automated "
                        "license detection reports the project as unlicensed."
                    ),
                    remediation=(
                        "Replace the file with the full, unmodified license text. Put "
                        "the copyright line in a separate NOTICE file so the license "
                        "text stays byte-identical and remains machine-detectable."
                    ),
                )
            )
        return 1

    def _check_ci(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        workflows = snap.find_paths(lambda p: p.startswith(CI_DIR) and p.endswith((".yml", ".yaml")))
        if not workflows:
            findings.append(
                Finding(
                    rule_id="CMP003",
                    title="No CI workflow",
                    severity=Severity.HIGH,
                    detail="No automated verification runs on change.",
                    remediation="Add a CI workflow that runs linting and tests on every pull request.",
                )
            )
        return 1

    def _check_tests(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        has_tests = any(
            any(hint in p.lower() for hint in TEST_HINTS) for p in snap.paths
        )
        if not has_tests:
            findings.append(
                Finding(
                    rule_id="CMP004",
                    title="No test files detected",
                    severity=Severity.HIGH,
                    detail="No test files found by path convention.",
                    remediation="Add a tests directory with automated tests wired into CI.",
                )
            )
        return 1

    def _check_docs(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        checks = 0

        readme = snap.files.get("README.md", "")
        if not snap.has_path("README.md", "README.rst", "readme.md"):
            findings.append(
                Finding(
                    rule_id="CMP005",
                    title="No README",
                    severity=Severity.MEDIUM,
                    detail="No entry-point documentation.",
                    remediation="Add a README describing purpose, setup, and usage.",
                )
            )
        elif len(readme.strip()) < 200:
            findings.append(
                Finding(
                    rule_id="CMP006",
                    title="README is minimal",
                    severity=Severity.LOW,
                    detail=f"README is {len(readme.strip())} characters.",
                    path="README.md",
                    remediation="Expand the README to cover purpose, setup, usage, and architecture.",
                )
            )
        checks += 1

        if not snap.has_path("CHANGELOG.md", "CHANGELOG"):
            findings.append(
                Finding(
                    rule_id="CMP007",
                    title="No CHANGELOG",
                    severity=Severity.LOW,
                    detail="No release history for traceability.",
                    remediation="Add a CHANGELOG following Keep a Changelog.",
                )
            )
        checks += 1

        if not snap.has_path("CONTRIBUTING.md", ".github/CONTRIBUTING.md"):
            findings.append(
                Finding(
                    rule_id="CMP008",
                    title="No CONTRIBUTING guide",
                    severity=Severity.LOW,
                    detail="No documented contribution process.",
                    remediation="Add CONTRIBUTING.md describing setup, standards, and review expectations.",
                )
            )
        checks += 1

        return checks

    def _check_adrs(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        adrs = snap.find_paths(
            lambda p: ("adr" in p.lower() or "decision" in p.lower()) and p.endswith(".md")
        )
        if not adrs:
            findings.append(
                Finding(
                    rule_id="CMP009",
                    title="No architecture decision records",
                    severity=Severity.MEDIUM,
                    detail="No ADRs found. Design rationale is undocumented.",
                    remediation="Add docs/adr/ and record significant decisions with context and consequences.",
                )
            )
        return 1

    def _check_archived(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        if snap.archived:
            findings.append(
                Finding(
                    rule_id="CMP010",
                    title="Repository is archived",
                    severity=Severity.INFO,
                    detail="Archived repositories are read-only and receive no maintenance.",
                    remediation="Confirm archival is intentional and that dependents are aware.",
                )
            )
        return 1