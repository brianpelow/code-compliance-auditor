# 0005. An unverified check is not a failed surface

**Status:** Accepted

## Context

ADR 0004 recorded a false outage: surface checks reused a connection pool that had already served hundreds of API calls, and the resulting resets were reported as downtime while the surfaces served HTTP 200. The fix was a fresh connection per check plus retries.

That fix was necessary and insufficient. A later run reported 3 of 5 surfaces healthy after three attempts each, while both flagged surfaces answered 200 to an independent request seconds later. The retry loop had not eliminated the reset; it had only made it rarer.

The retry was treating a symptom. The actual defect was in the model. `SurfaceState` could express healthy or not-healthy and nothing else, so `unhealthy_surfaces` returned every surface that was not confirmed good. A check that never completed was therefore indistinguishable from a surface that was genuinely down, and the renderer had no choice but to publish it as an outage.

This is the third appearance of one pattern in this portfolio. ADR 0003 in `regulatory-change-impact-agent` found an assessment contaminated by shared state. The chaos engine first reported 100 percent detection because every injected failure had a matching control. Here, a status document reported certainty it did not have. In each case the tool was not wrong about the data it had; it was wrong about how much it knew.

## Decision

`SurfaceState` gains `verified`, true only when the check completed and produced an HTTP status. `PortfolioState.unhealthy_surfaces` excludes unverified surfaces, and `unverified_surfaces` reports them separately.

`STATE.md` reports healthy out of *checked*, with a count of surfaces not verified, rather than healthy out of total. An unverified surface appears in the action items as a gap in the check, explicitly not as a reported outage. The dashboard stat tile reads from the same distinction, so the two surfaces cannot disagree.

A transient client-side failure is now a statement about the checker, not about the thing checked.

## Consequences

**Gained:** A flaky run degrades honestly. The status document says what it does not know instead of inventing an outage, and a real HTTP 500 still reads as a failure, so the signal that matters is preserved.

**Accepted:** Two failure modes now need reading rather than one. A surface that is genuinely unreachable from the runner will report as unverified rather than down, which understates a real problem. This is the deliberate direction to err: a false outage on a public status page costs more credibility than a delayed one, because a reader who catches one false alarm discounts every subsequent claim.

**Not done:** last-known-good carry-forward. The generator could read the previous `state.json` and report "healthy as of yesterday" for an unverified surface. That adds staleness semantics worth their own decision, and reporting nothing is honest in the meantime.
