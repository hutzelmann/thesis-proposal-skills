# Tasks: s1-eval-harness-spike

## 1. Environment

- [x] 1.1 Create `pyproject.toml` (uv-managed, Python ≥ 3.11) with dev deps: inspect-ai, pytest
- [x] 1.2 `uv sync` and verify `inspect --version` runs

## 2. Authoritative path (OpenRouter)

- [x] 2.1 Write minimal eval task in `harness/`: toy RQ-quality question, `model_graded_qa` scorer with judge model override
- [x] 2.2 Smoke run: model under test + judge both via `openrouter/`, `--limit 1`, verify score + per-model log produced
- [x] 2.3 Verify multi-model comparison: same task, two models in one invocation, two logs

## 3. Dev runner (subscription)

- [x] 3.1 Write `harness/claude_runner.py`: subprocess wrapper around `claude -p --model <tier>` returning text
- [x] 3.2 Smoke run: wrapper output scored by the same judge path

## 4. Decision & wrap-up

- [x] 4.1 Record framework decision + evidence in design.md "Spike Results"
- [x] 4.2 Update rewrite.md S1 status; commit
