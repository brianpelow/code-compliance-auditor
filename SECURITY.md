# Security Policy

## Reporting a vulnerability

Open a [security advisory](https://github.com/brianpelow/code-compliance-auditor/security/advisories/new) rather than a public issue.

Expect an initial response within seven days.

## Scope

This tool performs read-only analysis against the public GitHub API. It does not execute analyzed code, clone repositories to disk, or transmit repository contents anywhere except optionally to a language model for summary prose — and that call includes only the finding list, never source.

A `GITHUB_TOKEN` is optional and used solely to raise API rate limits. An `OPENROUTER_API_KEY` is optional and used solely for the executive summary. Neither is required for a complete audit.

## A note on findings

Findings are heuristic. A pattern match is a signal to review, not proof of a vulnerability. Conversely, a clean report is not a security guarantee — this tool checks a defined rule set, not everything that could be wrong.

Treat the output as a starting point for review, not a substitute for one.