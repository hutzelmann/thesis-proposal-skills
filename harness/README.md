# Eval Harness

L1/L2 skill evals over the fixture corpus (see `openspec/specs/testing-harness/spec.md`). L0 unit tests live in `tests/unit/` and never call models.

## Runs

Authoritative runs go through OpenRouter and are metered; export `OPENROUTER_API_KEY` first.

```sh
uv run inspect eval harness/skill_evals.py@check_report \
    --model openrouter/anthropic/claude-haiku-4.5 --log-dir logs/evals

# model matrix in one invocation (one log per model):
uv run inspect eval harness/skill_evals.py@review_fixture \
    --model "openrouter/anthropic/claude-haiku-4.5,openrouter/deepseek/deepseek-v4-flash"
```

Judge model: `JUDGE_MODEL` env, default `openrouter/anthropic/claude-haiku-4.5`.
Dev loop on the Max subscription (not the source of record): `harness/claude_runner.py`.
View transcripts: `uv run inspect view --log-dir logs/evals`.

## Tasks

- `write_from_seed`: w01 ideate seed to full draft. L1: file survives and check is clean (the missing-references error is tolerated for a one-reference seed). L2: RQ-quality rubric.
- `review_fixture`: f05 to `<slug>-review.md`. L1: review file exists, enumerated, proposal byte-identical. L2: finds the seeded mixed-methodology defect, stays format-agnostic, grammar only as a hint.
- `check_report`: f15 to chat report. L1: at least 3 of 5 oracle errors relayed in assistant chat AND the proposal stays byte-identical (an advisory skill must not edit).
- `harness/rq_quality_task.py` is the minimal S1 spike example, kept as reference.

## Findings log

- 2026-07-29, `check_report`: DeepSeek v4-flash and Claude Haiku 4.5 both relayed the check report faithfully (5/5 errors) but then **edited the proposal unprompted**, violating the advisory mandate. The byte-identity assert caught it. Partly induced by the harness's original "work autonomously until done" framing (since neutralized to "fulfil exactly this request"); SKILL.md was also hardened ("Never edit the proposal during a check run"). A post-fix pass has not been demonstrated yet; rerun the command above to validate.
