"""Optional curated blurbs and category overrides for the portfolio catalog.

The catalog auto-discovers every repo and uses its GitHub description by
default, so a new repo always appears with no action here. This file is only
for cases where a curated blurb reads better than the GitHub description, or
where a repo needs a category the map does not yet have.

Everything here is optional. An empty file produces a complete catalog.
"""

from __future__ import annotations

# repo name -> curated one-line blurb (overrides the GitHub description)
BLURB_OVERRIDES: dict[str, str] = {
    "genai-trace-conformance": (
        "Deterministic conformance validator for GenAI/agent telemetry. Checks "
        "real OTLP traces against the OpenTelemetry GenAI semantic conventions: "
        "required gen_ai.* attributes, token/cost observability, content-capture "
        "safety (flags secrets in telemetry), and agent-trace structure. Graded, "
        "CI-gateable, no LLM."
    ),
    "otel-pipeline-workbench": (
        "Deterministic workbench for OpenTelemetry Collector configs: lint them "
        "for correctness, security, and cost-safety, and simulate telemetry flow "
        "to see what a config drops, samples, and transforms before prod. "
        "CI-gateable, no LLM."
    ),
    "mcp-evidence-ledger": (
        "MCP server providing an append-only, hash-chained evidence ledger for "
        "agent actions. Tamper-evident receipts over human-readable local state; "
        "verify pinpoints any altered record. Deterministic, no LLM."
    ),
    "mcp-governance-gateway": (
        "Write-path MCP server: every governance action routes through a "
        "deterministic policy engine and produces an immutable, hash-sealed "
        "decision record."
    ),
    "compliance-chaos-engineer": (
        "Chaos engineering for governance controls. Injects governance failures "
        "and scores detection, honestly reporting a designed blind spot rather "
        "than a rigged 100 percent."
    ),
    "ai-model-autopsy": (
        "Agentic post-mortem investigator for AI failures. Deterministic "
        "governance analysis with a live LLM-written narrative that never alters "
        "a finding."
    ),
    "dependency-sentinel": (
        "Scheduled, async enterprise dependency-triage agent. Deterministic "
        "security findings from OSV.dev, delta reporting since last run, two "
        "schedulers, offline-capable."
    ),
}

# repo name -> category (overrides the CATEGORIES map if present)
CATEGORY_OVERRIDES: dict[str, str] = {}