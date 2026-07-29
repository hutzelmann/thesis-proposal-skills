# Proposal: s1-eval-harness-spike

## Why

The testing-harness capability spec requires a three-layer pyramid with an authoritative metered runner (OpenRouter, native multi-model comparison, spend caps) and a subscription-based dev runner. Which eval engine carries this (Inspect AI vs. fallback DeepEval vs. plain pytest glue) and how the two runners are wired is undecided — spike S1 from the rewrite plan. This change de-risks that decision with working code before any skill implementation depends on it.

## What Changes

- Set up the `uv`-managed dev environment (`pyproject.toml`) with the candidate eval stack.
- Build a minimal end-to-end eval: one toy task, model under test via OpenRouter, model-graded scorer via OpenRouter judge, spend-capped smoke run.
- Validate the subscription dev runner: a thin `claude -p` wrapper produces output consumable by the same scoring path.
- Record the framework decision (Inspect AI adopted / fallback chosen) with evidence in `design.md`.
- No skill behavior changes; `skip_specs: true` (tooling/dev infrastructure — the testing-harness spec already defines the behavior this implements).

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New: `pyproject.toml`, `harness/` (eval task + runners), `.venv` (untracked).
- Spend: a few cents on OpenRouter (spend-capped smoke runs, cheap models).
- Outcome feeds the design of the full testing-harness implementation change.
