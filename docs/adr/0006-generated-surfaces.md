# 0006. The public surfaces are generated, not hand-maintained

**Status:** Accepted

## Context

ADR 0004 established that portfolio state is generated. It stopped short of the two surfaces anyone actually reads: the dashboard at `brianpelow.github.io` and the profile README. Both continued to carry hand-maintained copies of an inventory the portfolio already generated nightly, and every categorization and counting error the portfolio shipped lived in one of those copies.

An audit of both surfaces found:

- Three of six dashboard stat tiles had drifted. It claimed 26 scheduled agents against 35 measured, 4 MCP servers against 5, and 4 agentic systems against 43 repos catalogued.
- `genai-trace-conformance` and `otel-pipeline-workbench` were filed under MCP servers. Neither is an MCP server. There was no Observability section at all, though the category existed upstream.
- Four sections of the profile README had a bullet list adjacent to a table header with no blank line between them, so those tables rendered as raw pipe characters. Technology strategy carried two consecutive tables with identical headers where an insertion had split one.
- The README asserted 428 passing tests across 25 repos, and that every repo has a nightly agent. Both were false.
- The maturity section labelled itself "self-assessed nightly" and set its date from `new Date()` in the browser. The six levels were hardcoded and had never changed, but every visitor was told they were assessed that morning.

The last one is the sharpest. A portfolio whose stated discipline is that findings must be reproducible from rules was fabricating a freshness signal on its own front page.

The common cause is not carelessness. It is that adding a repo required four manual edits across three repositories, and manual steps are where the errors were.

## Decision

`generate_state.py` and `generate_catalog.py` each emit structured JSON alongside their markdown. A third generator, `generate_blocks.py`, is a pure function over that JSON and renders three regions: the dashboard catalog, the dashboard stat tiles, and the README catalog. It performs no network calls, so it is tested with literals.

Each consumer surface owns a marker-delimited region and a workflow that fetches the published block over `raw.githubusercontent.com` and splices it in, committing with its own `GITHUB_TOKEN`. No cross-repo token exists anywhere in the design.

Repo cards carry the measured audit grade instead of a `CI passing` badge. The badge asserted something the page had never checked; the grade is produced by a deterministic auditor for every repo.

The dashboard gains a proof band naming the three findings that changed a conclusion. It is hand-written and deliberately so: those are editorial judgments, not measurements, and generating them would repeat the error this ADR closes in a new costume.

The maturity levels stay hand-set but are labelled with a fixed review date, and the browser-clock line is deleted.

The two surfaces present the same categories in different orders, so each declares its own sequence and a test asserts every category appears in both.

## Consequences

**Gained:** Adding a repo is one edit to the category map. The catalog, the counts, the grades, and the ordering follow automatically on both surfaces. The classes of defect listed above cannot recur, because nothing asserts them.

**Accepted:** Two order lists now exist and can disagree with the category map. Tests fail loudly when a category is missing from either. The maturity review date must be bumped by hand when a review actually happens; that is the honest cost of not fabricating it.

**Accepted:** The surfaces now depend on a generator in another repository. If `code-compliance-auditor` stops publishing, the splice aborts rather than writing a partial region, so a stale catalog is served instead of a blank one.

**Design note:** the splice asserts pure ASCII before writing. The dashboard's CI guard already fails on non-ASCII in `index.html`; asserting at the point of generation names the offending block rather than reporting a byte offset in a 41,000-character file.
