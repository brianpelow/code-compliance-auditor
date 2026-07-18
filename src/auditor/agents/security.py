"""SecurityAgent -- deterministic source and configuration security checks.

Every rule is pattern-based and reproducible. No network calls, no LLM.
Patterns are derived from published secure-coding guidance (OWASP, CWE).
"""

from __future__ import annotations

import re

from auditor.models import AgentResult, Finding, RepoSnapshot, Severity, score_from_findings

# Credential-shaped strings. Deliberately conservative to limit false positives:
# each requires an assignment and a quoted literal of meaningful length.
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("SEC001", "AWS access key", r"AKIA[0-9A-Z]{16}"),
    ("SEC002", "Private key block", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    ("SEC003", "Generic API key assignment", r"(?i)\b(?:api[_-]?key|apikey)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
    ("SEC004", "Hardcoded password assignment", r"(?i)\bpassword\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    ("SEC005", "Bearer token literal", r"(?i)bearer\s+[A-Za-z0-9_\-\.]{24,}"),
    ("SEC006", "Slack webhook URL", r"https://hooks\.slack\.com/services/[A-Za-z0-9/]{20,}"),
]

# Placeholder values that should never count as a real secret.
PLACEHOLDER_HINTS = (
    "your_",
    "example",
    "changeme",
    "placeholder",
    "xxxxx",
    "<your",
    "dummy",
    "sample",
    "fake",
    "redacted",
    "os.environ",
    "getenv",
    "process.env",
)

DANGEROUS_PATTERNS: list[tuple[str, str, str, Severity, str]] = [
    (
        "SEC010",
        "Bare except clause",
        r"except\s*:",
        Severity.MEDIUM,
        "Catch specific exception types so real failures are not silently swallowed.",
    ),
    (
        "SEC011",
        "Use of eval()",
        r"(?<![\w.])eval\s*\(",
        Severity.HIGH,
        "Replace eval() with explicit parsing. Evaluating dynamic input enables code injection.",
    ),
    (
        "SEC012",
        "Use of exec()",
        r"(?<![\w.])exec\s*\(",
        Severity.HIGH,
        "Replace exec() with an explicit dispatch table or import.",
    ),
    (
        "SEC013",
        "Shell execution with shell=True",
        r"shell\s*=\s*True",
        Severity.HIGH,
        "Pass an argument list instead of shell=True to avoid shell injection.",
    ),
    (
        "SEC014",
        "SQL built by string formatting",
        r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\b[^\n]*?(?:%\s*\(|\.format\(|\+\s*[a-zA-Z_])",
        Severity.HIGH,
        "Use parameterized queries. String-built SQL enables injection.",
    ),
    (
        "SEC015",
        "TLS verification disabled",
        r"verify\s*=\s*False",
        Severity.HIGH,
        "Do not disable certificate verification. Pin or supply a CA bundle instead.",
    ),
]

ENV_IGNORE_ENTRIES = (".env", "*.env", ".env.*", "env/")

# Paths excluded from pattern scanning.
#
# Test files intentionally contain the exact patterns these rules detect --
# a fixture asserting that a hardcoded password is caught must contain one.
# Rule-definition modules contain the patterns as regex literals.
# Documentation describes the patterns in prose.
#
# Scanning any of these produces guaranteed false positives, and a gating
# tool that cries wolf is a gating tool people disable.
TEST_PATH_HINTS = ("test_", "_test.", "/tests/", "tests/", "/spec/", ".spec.", "conftest.py")

RULE_DEFINITION_HINTS = ("auditor/agents/", "auditor\\agents\\")

CODE_SUFFIXES = (".py", ".js", ".ts", ".go", ".rb", ".java", ".rs", ".php")


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    return any(hint in lowered for hint in TEST_PATH_HINTS)


def _is_rule_definition(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return "auditor/agents/" in normalized


def _is_code(path: str) -> bool:
    return path.endswith(CODE_SUFFIXES)


def scannable_files(snap: RepoSnapshot, code_only: bool = True) -> dict[str, str]:
    """Files eligible for pattern scanning.

    Excludes test fixtures, rule definitions, and -- when code_only -- any
    non-source file such as documentation.
    """
    result = {}
    for path, content in snap.files.items():
        if _is_test_path(path) or _is_rule_definition(path):
            continue
        if code_only and not _is_code(path):
            continue
        result[path] = content
    return result


class SecurityAgent:
    """Scans source and configuration for security-relevant patterns."""

    name = "SecurityAgent"

    def run(self, snap: RepoSnapshot) -> AgentResult:
        findings: list[Finding] = []
        checks = 0

        checks += self._check_secrets(snap, findings)
        checks += self._check_dangerous_patterns(snap, findings)
        checks += self._check_env_ignored(snap, findings)
        checks += self._check_security_policy(snap, findings)

        return AgentResult(
            agent=self.name,
            score=score_from_findings(findings),
            findings=findings,
            checks_run=checks,
        )

    def _check_secrets(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        for rule_id, title, pattern in SECRET_PATTERNS:
            regex = re.compile(pattern)
            for path, content in scannable_files(snap, code_only=False).items():
                for line in content.splitlines():
                    if not regex.search(line):
                        continue
                    if any(hint in line.lower() for hint in PLACEHOLDER_HINTS):
                        continue
                    findings.append(
                        Finding(
                            rule_id=rule_id,
                            title=f"Possible committed credential: {title}",
                            severity=Severity.CRITICAL,
                            detail=f"A {title.lower()} pattern appears in tracked source.",
                            path=path,
                            remediation=(
                                "Rotate the credential, purge it from git history, and load it "
                                "from an environment variable or secret manager."
                            ),
                        )
                    )
                    break
        return len(SECRET_PATTERNS)

    def _check_dangerous_patterns(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        for rule_id, title, pattern, severity, remediation in DANGEROUS_PATTERNS:
            regex = re.compile(pattern)
            hits = [p for p, c in scannable_files(snap).items() if regex.search(c)]
            if hits:
                findings.append(
                    Finding(
                        rule_id=rule_id,
                        title=title,
                        severity=severity,
                        detail=f"Detected in {len(hits)} file(s).",
                        path=sorted(hits)[0],
                        remediation=remediation,
                    )
                )
        return len(DANGEROUS_PATTERNS)

    def _check_env_ignored(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        gitignore = snap.files.get(".gitignore", "")
        if gitignore and not any(entry in gitignore for entry in ENV_IGNORE_ENTRIES):
            findings.append(
                Finding(
                    rule_id="SEC020",
                    title="Environment files not gitignored",
                    severity=Severity.MEDIUM,
                    detail="No .env entry found in .gitignore.",
                    path=".gitignore",
                    remediation="Add .env and .env.* to .gitignore to prevent credential commits.",
                )
            )
        if snap.has_path(".env"):
            findings.append(
                Finding(
                    rule_id="SEC021",
                    title="Environment file committed",
                    severity=Severity.CRITICAL,
                    detail="A .env file is tracked in the repository.",
                    path=".env",
                    remediation="Remove .env from tracking, purge from history, and rotate any values.",
                )
            )
        return 2

    def _check_security_policy(self, snap: RepoSnapshot, findings: list[Finding]) -> int:
        if not snap.has_path("SECURITY.md", ".github/SECURITY.md"):
            findings.append(
                Finding(
                    rule_id="SEC030",
                    title="No security policy",
                    severity=Severity.LOW,
                    detail="No SECURITY.md defining vulnerability disclosure.",
                    remediation="Add SECURITY.md with a disclosure contact and response expectations.",
                )
            )
        return 1