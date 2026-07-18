# 0002. A critical finding caps the grade at D

**Status:** Accepted

## Context

The overall score is a weighted average across three agents. A repository with one committed credential but excellent documentation, tests, and CI can still average into a B.

That is arithmetically correct and practically wrong. A live credential in git history is not offset by a good CHANGELOG.

## Decision

Any finding at CRITICAL severity caps the letter grade at D, regardless of the weighted score. The numeric score is unchanged so trends remain visible.

## Consequences

Grades become non-linear against score, which requires explanation in the report. In exchange, the grade communicates the thing that actually matters: whether there is something here that must be fixed today.