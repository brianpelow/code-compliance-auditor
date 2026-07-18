"""DebtAgent -- deterministic technical debt signals.

Uses structural proxies rather than full static analysis, so results are
reproducible from a shallow snapshot and comparable across languages.
"""

from __future__ import annotations

import re

from auditor.models import AgentResult, Finding, RepoSnapshot, Severity, score_from_findings

TODO_PATTERN = re.compile(r"(?i)#\s*(TODO|FIXME|HACK|XXX)\b|//\s*(TODO|FIXME|HACK|XXX)\b")

LARGE_FILE_LINES = 500
VERY_LARGE_FILE_LINES = 1000
DEEP_NESTING_INDENT = 24  # 6 levels at 4 spaces

PINNED_PATTERN = re.compile(r"[=~><]=|\^|~")


class DebtAgent:
    """Scans for maintainability and technical debt signals."""

    name = "DebtAgent"

    def run(self, snap: RepoSnapshot) -> AgentResult:
        findings: list[Finding] = []
        checks = 0

        checks += self._check_todos(snap, findings)
        checks += self._check_file_size(snap, findings)
        checks += self._check_nesting(snap, findings)
        checks += self._check_dependency_pinning(snap, findings)
        checks += self._check_type_hints(snap, findings)

        return AgentResult(
            agent=self.name,
            score=score_from_findings(findings),
            findings=findings,
            checks_run=checks,
        )

    def _check_todos(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        total = 0
        worst_path = None
        worst_count = 0
        for path, content in snap.files.items():
            count = len(TODO_PATTERN.findall(content))
            total += count
            if count > worst_count:
                worst_count, worst_path = count, path

        if total >= 20:
            severity = Severity.MEDIUM
        elif total >= 8:
            severity = Severity.LOW
        else:
            return 1

        findings.append(
            Finding(
                rule_id="DBT001",
                title="High TODO/FIXME density",
                severity=severity,
                detail=f"{total} TODO/FIXME/HACK markers across sampled files.",
                path=worst_path,
                remediation="Convert deferred work into tracked issues and remove stale markers.",
            )
        )
        return 1

    def _check_file_size(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        very_large: list[str] = []
        large: list[str] = []
        for path, content in snap.files.items():
            lines = content.count("\n") + 1
            if lines >= VERY_LARGE_FILE_LINES:
                very_large.append(path)
            elif lines >= LARGE_FILE_LINES:
                large.append(path)

        if very_large:
            findings.append(
                Finding(
                    rule_id="DBT002",
                    title="Very large source files",
                    severity=Severity.MEDIUM,
                    detail=f"{len(very_large)} file(s) exceed {VERY_LARGE_FILE_LINES} lines.",
                    path=sorted(very_large)[0],
                    remediation="Split large modules along clear responsibility boundaries.",
                )
            )
        elif large:
            findings.append(
                Finding(
                    rule_id="DBT003",
                    title="Large source files",
                    severity=Severity.LOW,
                    detail=f"{len(large)} file(s) exceed {LARGE_FILE_LINES} lines.",
                    path=sorted(large)[0],
                    remediation="Consider decomposing files that are growing past a single concern.",
                )
            )
        return 1

    def _check_nesting(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        deep: list[str] = []
        for path, content in snap.source_files(".py").items():
            for line in content.splitlines():
                stripped = line.lstrip(" ")
                if not stripped or stripped.startswith("#"):
                    continue
                indent = len(line) - len(stripped)
                if indent >= DEEP_NESTING_INDENT:
                    deep.append(path)
                    break
        if deep:
            findings.append(
                Finding(
                    rule_id="DBT004",
                    title="Deeply nested code",
                    severity=Severity.LOW,
                    detail=f"{len(deep)} file(s) contain blocks nested six or more levels.",
                    path=sorted(deep)[0],
                    remediation="Extract helpers or use early returns to flatten control flow.",
                )
            )
        return 1

    def _check_dependency_pinning(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        requirements = snap.files.get("requirements.txt")
        if requirements:
            lines = [
                line.strip()
                for line in requirements.splitlines()
                if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("-")
            ]
            unpinned = [line for line in lines if not PINNED_PATTERN.search(line)]
            if unpinned:
                findings.append(
                    Finding(
                        rule_id="DBT005",
                        title="Unpinned dependencies",
                        severity=Severity.MEDIUM,
                        detail=f"{len(unpinned)} of {len(lines)} requirements have no version constraint.",
                        path="requirements.txt",
                        remediation="Pin or bound every dependency so builds are reproducible.",
                    )
                )
        return 1

    def _check_type_hints(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        py_files = snap.source_files(".py")
        if not py_files:
            return 1

        defs = 0
        annotated = 0
        for content in py_files.values():
            for line in content.splitlines():
                stripped = line.strip()
                if not stripped.startswith("def "):
                    continue
                defs += 1
                if "->" in stripped or re.search(r"\(\s*\w+\s*:", stripped):
                    annotated += 1

        if defs >= 10 and annotated / defs < 0.5:
            findings.append(
                Finding(
                    rule_id="DBT006",
                    title="Sparse type annotations",
                    severity=Severity.LOW,
                    detail=f"{annotated} of {defs} sampled functions carry annotations.",
                    remediation="Add type hints and enforce them in CI to catch interface drift early.",
                )
            )
        return 1