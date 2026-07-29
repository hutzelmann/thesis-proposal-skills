# Proposal: lint-ci-drift

## Why

The testing-harness spec promises "CI executes only L0 and lint by default" — neither a CI workflow nor a linter exists. The S3 design promised an L0 test tying rq-filter.lua's heading matching to structure.json once it existed; never written.

## What Changes

- ruff as dev dependency with pyproject config; codebase lint-clean.
- .github/workflows/ci.yml: L0 pytest, ruff, sync --check, openspec validate --all --strict. No model calls, no secrets.
- tests/unit/test_rq_filter_drift.py: the heading names hardcoded in rq-filter.lua must match structure.json's research-questions titles (en and de).
- skip_specs: true — tooling implementing existing spec statements.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

CI on GitHub once pushed; local `uv run ruff check` joins the loop.
