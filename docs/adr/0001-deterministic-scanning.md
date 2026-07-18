# 0001. Scanning agents are deterministic

**Status:** Accepted

## Context

The auditor could use a language model to scan source for security and quality issues. Language models catch patterns that rules miss and adapt to unfamiliar codebases without new rules.

They are also non-reproducible. The same repository can produce different findings on different runs, and a model can assert a finding that does not exist in the source.

An audit artifact is evidence. Evidence that changes between runs is not evidence.

## Decision

The three scanning agents are purely rule-based. No language model participates in detecting, scoring, or weighting a finding.

A language model may write the executive summary prose, and only after all findings are fixed. Its prompt includes the finding list and instructs it not to invent findings. If the call fails, a deterministic template summary is produced instead.

## Consequences

**Accepted:** Coverage is limited to patterns explicitly encoded. Novel issue classes are missed until a rule is written.

**Gained:** Any finding can be verified by reading the rule and the flagged line. Two people auditing the same commit get identical results. The tool can gate CI, because the score is stable.

**Follow-on:** Rules must be conservative. A false positive in a gating tool trains people to ignore it.