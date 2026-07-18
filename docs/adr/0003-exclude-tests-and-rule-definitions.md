# 0003. Exclude test files and rule definitions from pattern scanning

**Status:** Accepted

## Context

The first self-audit graded this repository F at 54/100 with two critical findings. All eight security findings were false positives:

- Test fixtures contained a fake AWS key and a fake password, because they assert those patterns are detected
- The rule-definition module contained `eval(` and `exec(`, because those are the regex literals that detect them
- The README contained `shell=True`, because it documents the rule

Every one of these is a file that is *about* a pattern rather than a file that *contains* the pattern as real code. This would fire against every consumer's test suite, not just ours.

## Decision

Pattern-based rules skip three path classes:

1. **Test files** -- matched on `test_`, `_test.`, `/tests/`, `conftest.py`, `.spec.`
2. **Rule-definition modules** -- any path under `auditor/agents/`
3. **Non-source files** for code-specific rules -- documentation describing a pattern is not an instance of it

Secret detection still scans configuration files, since a credential in `config.yml` is a real finding. Filesystem-level checks such as a committed `.env` are unaffected, because they inspect the path list rather than file contents.

## Consequences

**Accepted:** A real credential committed inside a test file will not be flagged. This is a deliberate trade. Test directories are where fake credentials belong, and the alternative — flagging every project's fixtures — makes the tool noisy enough to be ignored.

**Gained:** The tool can gate CI without generating findings that reviewers learn to dismiss. False positives in a gating tool are more damaging than missed findings, because they train people to disable the gate.

**Verification:** The self-audit moved from F/54 to A/98 while all five other audited repositories held their exact prior scores, confirming the exclusions were narrow rather than blanket.