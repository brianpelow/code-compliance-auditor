# Contributing

## Setup

```bash
uv sync --all-extras
uv run pytest
uv run ruff check src tests
```

## Adding a rule

Every rule must be deterministic. A rule that depends on a language model, wall-clock time, or network state does not belong in a scanning agent.

1. Add the pattern and severity to the relevant agent
2. Assign the next available rule ID in that agent's namespace (`SEC`, `CMP`, `DBT`)
3. Write both a positive and a negative test -- one that fires, one that confirms a legitimate pattern is not flagged
4. False positives are worse than missed findings. Prefer conservative patterns.