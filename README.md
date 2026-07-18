# code-compliance-auditor

> A deterministic multi-agent compliance auditor for GitHub repositories. Security, governance, and technical debt scoring with prioritized remediation.

![CI](https://github.com/brianpelow/code-compliance-auditor/actions/workflows/ci.yml/badge.svg)

## Why deterministic

An audit tool that hallucinates findings is worse than no audit tool. Every rule here is pattern-based and reproducible: the same repository snapshot always produces the same findings, the same severities, and the same score.

An optional language model writes the executive summary. It never creates, removes, or reweights a finding.

## Install and run

```bash
uv sync
uv run audit brianpelow/orbit-platform
```

Works with no credentials. A `GITHUB_TOKEN` only raises the API rate limit. An `OPENROUTER_API_KEY` only enables the prose summary.

```bash
uv run audit brianpelow/orbit-platform --markdown
uv run audit brianpelow/orbit-platform --out reports/orbit.md
uv run audit brianpelow/orbit-platform --fail-under 80   # exits 1 below threshold
```

The `--fail-under` flag makes this usable as a CI gate on your own repositories.

## The agents

| Agent | What it checks | Weight |
|-------|---------------|--------|
| `SecurityAgent` | Committed credentials, `eval`/`exec`, `shell=True`, string-built SQL, disabled TLS verification, bare excepts, untracked `.env` | 45% |
| `ComplianceAgent` | CODEOWNERS, LICENSE, CI workflow, tests, README depth, CHANGELOG, CONTRIBUTING, ADRs | 35% |
| `DebtAgent` | TODO density, oversized files, deep nesting, unpinned dependencies, sparse type annotations | 20% |
| `VerdictAgent` | Weighted score, letter grade, top-five prioritized remediation | -- |

Any critical finding caps the grade at D regardless of the weighted score. A committed credential is not offset by a good CHANGELOG.

## Scoring

Each agent starts at 100 and subtracts a fixed weight per finding: critical 30, high 15, medium 7, low 3, info 0. Scores are clamped to 0-100 and combined using the weights above.

| Grade | Score |
|-------|-------|
| A | 93-100 |
| B | 85-92 |
| C | 75-84 |
| D | 65-74 |
| F | below 65 |

## Control mapping

Compliance rules map to widely published control expectations rather than any organization's internal standards:

- **Change authorization and segregation of duties** -- CODEOWNERS plus CI gating provides reviewer evidence (SOX ITGC)
- **Documented ownership and traceability** -- CODEOWNERS, CHANGELOG, ADRs (SOC 2 CC-series)
- **Secure SDLC documentation** -- CONTRIBUTING, SECURITY.md, automated verification (PCI-DSS Requirement 6)

Every rule is reconstructable from public sources.

## Nightly scorecard

A scheduled agent audits a set of repositories every night and commits the results to [reports/](./reports/), including a rolled-up scorecard with average score across the portfolio.

## Related work

| Repo | What it is |
|------|-----------|
| [orbit-platform](https://github.com/brianpelow/orbit-platform) | The control plane that enforces these standards at deploy time |
| [cab-automation](https://github.com/brianpelow/cab-automation) | Change advisory automation with risk scoring |
| [platform-maturity-assessment](https://github.com/brianpelow/platform-maturity-assessment) | Organization-level maturity scoring across six domains |

## License

Apache 2.0