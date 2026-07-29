# Design: s1-eval-harness-spike

## Context

Verified facts (2026-07): Inspect AI has a native `openrouter/` provider, model-graded scorers (`model_graded_qa`), and parallel multi-model eval; its official Claude Code bridge cannot use Max-subscription auth (proxy breaks OAuth), so subscription runs must be a plain `claude -p` subprocess outside Inspect (`--model none` pattern). DeepEval is the confirmed simpler fallback. See rewrite.md S1 and the testing-harness spec.

## Goals / Non-Goals

- Goals: prove the authoritative OpenRouter path end-to-end (task → model under test → judge → score); prove the `claude -p` dev wrapper; decide the framework; establish spend-cap conventions.
- Non-Goals: real skill evals, fixtures, personas, CI wiring, the full L1 structural layer — those come in the testing-harness implementation change.

## Decisions

- **D-S1-1 — Try Inspect AI first.** Rationale: native OpenRouter provider + judge + per-model logs beat hand-rolled glue; fallback to DeepEval only if the spike shows friction disproportionate to value. Evidence recorded below after the run.
- **D-S1-2 — Smoke models.** Model under test: a cheap OpenRouter model (DeepSeek chat class). Judge: a second cheap model. Rationale: spike validates plumbing, not quality; costs must stay at cents.
- **D-S1-3 — Dev runner shape.** Plain subprocess wrapper around `claude -p --model <tier>` returning text; scoring reuses the same judge path. Not routed through Inspect's provider layer (subscription constraint).
- **D-S1-4 — Keys.** Read `OPENROUTER_API_KEY` from the environment; locally sourced from the untracked credentials file. Never committed, never logged.

## Risks / Trade-offs

- Inspect's log/orchestration value may not show at spike scale — decision notes must consider full-harness needs (per-model logs, matrix runs), not just the toy task.
- Subscription runner drifts outside Inspect's accounting by design; accepted (dev loop only).

## Spike Results

**Decision: Inspect AI adopted (D12 fallback not needed).** Evidence, all runs 2026-07-29:

- Authoritative path end-to-end ✓ — `inspect eval harness/rq_quality_task.py --model openrouter/deepseek/deepseek-v4-flash --limit 1`: model under test answered, `model_graded_qa` with judge `openrouter/anthropic/claude-haiku-4.5` and custom rubric template graded with sound reasoning, per-run `.eval` log written. Only friction: `openai` package required as extra dep for the OpenRouter provider (added).
- Native multi-model matrix ✓ — comma-separated `--model` with two models produced parallel runs and one log per model in a single invocation.
- Dev runner ✓ — `harness/claude_runner.py` (≈20-line subprocess wrapper around `claude -p --model haiku`, subscription auth) produced output scored by the exact same judge template via `inspect_ai.model.get_model()`. No Inspect provider involvement needed; `--model none` pattern unnecessary for the dev loop — plain script suffices.
- Rubric validity signal — all three models (DeepSeek v4-flash, Gemini 2.5 Flash Lite, Claude Haiku 4.5) unprompted produced "How can X…" implementation-goal research questions; the judge failed each with correct step-by-step rationale. The L2 rubric dimension works and the guidance the skills encode is demonstrably load-bearing.
- Spend: < $0.01 total (≈2k tokens across all runs).

Consequences for the testing-harness implementation change: build L2 on Inspect tasks + `model_graded_qa` templates; judge model configurable, default a cheap capable model; L1 structural asserts run as plain pytest around Inspect run outputs or direct runner calls; the claude wrapper stays a dev convenience script.
