# 0004. Portfolio state is generated, not asserted

**Status:** Accepted

## Context

Portfolio state was documented by hand in several places: a dashboard with hardcoded counts, a project context file, a profile README. Every one of them drifted.

The dashboard claimed 37 repos while listing 25. A context document asserted a test count that predated roughly 170 tests. The numbers were correct when written and wrong within a week, because a hand-maintained number decays the moment anything is built.

The dashboard was fixed by fetching its repo count from the GitHub API rather than hardcoding it. This applies the same principle to everything else.

## Decision

A generator collects live portfolio state and emits `STATE.md` on a nightly schedule. Every figure is measured at generation time: repo count and grades from the auditor, scheduled agents from workflow files, surface health from live HTTP checks, CI status from the Actions API.

Documents that need current state link to it rather than restating it. `STATE.md` carries a header instructing readers not to edit it by hand.

Collection and rendering are separate modules so rendering is testable with fixtures and no network.

## Consequences

**Gained:** State cannot drift, because nothing asserts it. A new repo appears in the catalog automatically and is flagged as uncategorized until the map is updated, so builds cannot silently fall out of the record.

**Accepted:** The generator is now a dependency of the documentation. If it breaks, state goes stale silently rather than loudly. It runs on the same nightly workflow as the audit, so a failure surfaces as a failed Action.

**Design note:** surface checks open their own connection rather than reusing the API client. The first implementation shared one client across hundreds of API calls and then the surface checks, and the stale connection pool produced connection resets that were reported as outages. Two live surfaces were flagged as down while serving HTTP 200. A false outage in a status document trains the reader to skip the section, which is the same failure mode as ADR 0003 arriving from a different direction.