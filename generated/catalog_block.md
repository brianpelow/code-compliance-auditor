### Agentic systems

| Repo | What it does | Audit |
|------|--------------|-------|
| [ai-incident-war-room](https://github.com/brianpelow/ai-incident-war-room) | Live multi-agent AI incident simulation for regulated industries - five agents coordinate in real time to produce a complete incident response package | B 89 |
| [ai-model-autopsy](https://github.com/brianpelow/ai-model-autopsy) | Agentic post-mortem investigator for AI failures. | A 99 |
| [DataPipelineAgent](https://github.com/brianpelow/DataPipelineAgent) | Agentic ETL orchestrator - monitors data sources, detects schema drift, and auto-heals pipelines | A 99 |
| [IncidentPilot](https://github.com/brianpelow/IncidentPilot) | Multi-agent incident response orchestrator - triage, escalation, runbook generation, and post-mortems with LangGraph | A 99 |

### MCP servers

| Repo | What it does | Audit |
|------|--------------|-------|
| [mcp-compliance-grc](https://github.com/brianpelow/mcp-compliance-grc) | MCP server for GRC workflows - maps controls to code evidence and drafts compliance narratives | A 98 |
| [mcp-developer-portal](https://github.com/brianpelow/mcp-developer-portal) | MCP server wrapping Backstage - query service catalog, fetch TechDocs, and scaffold services via AI agents | A 98 |
| [mcp-evidence-ledger](https://github.com/brianpelow/mcp-evidence-ledger) | MCP server providing an append-only, hash-chained evidence ledger for agent actions. | A 99 |
| [mcp-governance-gateway](https://github.com/brianpelow/mcp-governance-gateway) | Write-path MCP server: every governance action routes through a deterministic policy engine and produces an immutable, hash-sealed decision record. | A 99 |
| [mcp-incident-intel](https://github.com/brianpelow/mcp-incident-intel) | MCP server wiring PagerDuty, Dynatrace, and runbook context for AI-driven incident response | A 98 |

### Observability

| Repo | What it does | Audit |
|------|--------------|-------|
| [genai-trace-conformance](https://github.com/brianpelow/genai-trace-conformance) | Deterministic conformance validator for GenAI/agent telemetry. | A 99 |
| [otel-pipeline-workbench](https://github.com/brianpelow/otel-pipeline-workbench) | Deterministic workbench for OpenTelemetry Collector configs: lint them for correctness, security, and cost-safety, and simulate telemetry flow to see what a config drops, samples... | A 99 |

### Engineering metrics

| Repo | What it does | Audit |
|------|--------------|-------|
| [PlatformSLOBoard](https://github.com/brianpelow/PlatformSLOBoard) | Executive-grade platform SLO dashboard aggregating PagerDuty and Dynatrace reliability signals | A 99 |
| [TeamHealthRadar](https://github.com/brianpelow/TeamHealthRadar) | Engineering team health scoring - DORA metrics, SPACE framework signals, and AI-synthesized insights | A 98 |
| [TechDebtLedger](https://github.com/brianpelow/TechDebtLedger) | Automated tech debt tracker - scans repos for complexity hotspots and surfaces a prioritized payoff roadmap | A 97 |

### Developer productivity

| Repo | What it does | Audit |
|------|--------------|-------|
| [pr-autopilot](https://github.com/brianpelow/pr-autopilot) | CLI that auto-generates PR descriptions, reviewers, and labels from your diff using AI | A 98 |
| [repoforge](https://github.com/brianpelow/repoforge) | AI-assisted repo scaffolding CLI for regulated industries engineering teams | A 93 |
| [runbook-gen](https://github.com/brianpelow/runbook-gen) | Auto-generates operational runbooks from code, alerts, and incident history using AI | A 99 |

### Platform patterns

| Repo | What it does | Audit |
|------|--------------|-------|
| [innersource-scorecard](https://github.com/brianpelow/innersource-scorecard) | Inner-source health scorecard - grades repos on discoverability, documentation, contribution friction, and adoption | A 99 |
| [platform-maturity-model](https://github.com/brianpelow/platform-maturity-model) | Open framework and CLI for assessing platform engineering maturity - 5-level model with automated evidence collection | A 98 |
| [service-catalog-sync](https://github.com/brianpelow/service-catalog-sync) | Automated Backstage catalog hydration - scans repos, infers ownership and tech stack, keeps catalog fresh via CI | A 99 |

### Technology strategy

| Repo | What it does | Audit |
|------|--------------|-------|
| [ai-governance-framework](https://github.com/brianpelow/ai-governance-framework) | AI governance in regulated industries: the replay imperative - decision record architecture, model registry, and the four actors who will demand accountability | A 93 |
| [engineering-operating-model](https://github.com/brianpelow/engineering-operating-model) | How I think about building and leading engineering organizations in regulated industries - team design, culture, career development, and operational excellence | A 93 |
| [integrated-strategy](https://github.com/brianpelow/integrated-strategy) | The integrated strategy: how platform engineering, organizational design, and AI governance fit together - the entry point to a four-document body of work on winning the AI era in... | B 91 |
| [platform-engineering-thesis](https://github.com/brianpelow/platform-engineering-thesis) | A technology strategy thesis: where platform engineering and agentic AI intersect in regulated industries, 2026-2030 | A 93 |

### Control plane and governance

| Repo | What it does | Audit |
|------|--------------|-------|
| [cab-automation](https://github.com/brianpelow/cab-automation) | Change Advisory Board automation - AI-generated CAB packages, risk scoring, and deployment gates for regulated financial services | A 96 |
| [code-compliance-auditor](https://github.com/brianpelow/code-compliance-auditor) | Deterministic multi-agent compliance auditor for GitHub repositories - security, compliance, and technical debt scoring with prioritized remediation | A 93 |
| [compliance-chaos-engineer](https://github.com/brianpelow/compliance-chaos-engineer) | Chaos engineering for governance controls. | A 100 |
| [fintech-platform-reference](https://github.com/brianpelow/fintech-platform-reference) | Reference architecture for a regulated fintech engineering platform - ADRs, system design, catalog definitions, and SLO specs | B 90 |
| [orbit-platform](https://github.com/brianpelow/orbit-platform) | Production Services Control Plane - a 6-stage image build and deployment governance framework for regulated financial services | A 99 |
| [platform-conductor](https://github.com/brianpelow/platform-conductor) | Meta-orchestrator for the brianpelow platform - coordinates agents, detects failures, and publishes weekly health summaries | A 99 |
| [regulatory-change-impact-agent](https://github.com/brianpelow/regulatory-change-impact-agent) | Takes regulatory guidance, identifies affected systems, and produces a sequenced remediation plan - deterministic impact mapping for regulated engineering organizations | A 99 |

### Autonomous intelligence

| Repo | What it does | Audit |
|------|--------------|-------|
| [ai-regulation-tracker](https://github.com/brianpelow/ai-regulation-tracker) | Nightly agent monitoring OCC, FCA, ECB, FFIEC, CFPB, and EU AI Act feeds for AI-relevant regulatory developments - published daily to GitHub Discussions | A 96 |
| [BoardroomBrief](https://github.com/brianpelow/BoardroomBrief) | Autonomous weekly engineering brief generator - pulls GitHub, JIRA, and incident data into exec-ready narratives | A 98 |
| [dependency-sentinel](https://github.com/brianpelow/dependency-sentinel) | Scheduled, async enterprise dependency-triage agent. | A 99 |
| [weekly-platform-intelligence](https://github.com/brianpelow/weekly-platform-intelligence) | Weekly executive brief on platform engineering, agentic AI, and regulated industry technology - published every Monday by an autonomous agent | A 96 |

### Interactive tools

| Repo | What it does | Audit |
|------|--------------|-------|
| [cto-interview-simulator](https://github.com/brianpelow/cto-interview-simulator) | An AI-powered CTO interview simulator - experience the interview before you sit down with the candidate | B 89 |
| [platform-maturity-assessment](https://github.com/brianpelow/platform-maturity-assessment) | Interactive platform maturity assessment for engineering leaders - 6 domains, 20 questions, scored report with recommendations | B 89 |
| [portfolio-assistant](https://github.com/brianpelow/portfolio-assistant) | AI-powered portfolio assistant - ask questions about the brianpelow engineering portfolio | B 89 |

### Just for fun

| Repo | What it does | Audit |
|------|--------------|-------|
| [code-roast](https://github.com/brianpelow/code-roast) | Paste any code and get it brutally but lovingly roasted by a senior engineer who has seen things | A 94 |
| [sports-analytics-for-engineers](https://github.com/brianpelow/sports-analytics-for-engineers) | DORA metrics for sports teams - deployment frequency, change failure rate, and MTTR applied to your favorite teams | A 97 |
| [vibe-check-cli](https://github.com/brianpelow/vibe-check-cli) | Analyzes the vibe of any GitHub repo - commit messages, PR titles, README tone - and delivers a brutally honest vibe report | A 97 |

### Meta

| Repo | What it does | Audit |
|------|--------------|-------|
| [brianpelow](https://github.com/brianpelow/brianpelow) | GitHub profile | C 76 |
| [brianpelow.github.io](https://github.com/brianpelow/brianpelow.github.io) | Live platform engineering intelligence dashboard | B 86 |

