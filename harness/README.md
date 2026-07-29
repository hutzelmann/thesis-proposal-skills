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

- 2026-07-29, `ideate_socratic` (Haiku 4.5 as skill, judge-model as persona, 5 rounds): the multi-turn machinery works end to end — the persona stayed in character, the dialogue was judged Socratic and literature-grounded, and a seed file was created. Red on one gap: the seed lacked the `references:` key when grounding found no starter entries. SKILL.md now mandates `references: []`; re-run to validate.

- 2026-07-29, `check_report`, five runs across escalating mitigations: DeepSeek v4-flash, Claude Haiku 4.5 (original framing), Haiku (neutralized "fulfil exactly this request" framing), Haiku (read-only prohibition as the first bold line of SKILL.md), Claude Sonnet 4.5 (same). **Every model relayed the report faithfully and then edited the proposal anyway** (8-9 edit calls each), caught by the byte-identity assert. Conclusion: in an autonomous harness with edit tools, prompt-level prohibitions do not stop models from fixing what they diagnose, regardless of tier. The eval stays red as a true positive. Implications: (a) in real interactive use the user's presence is the effective guard — the report arrives in chat before any edit could be confirmed; (b) skill-design lesson recorded: advisory-only behavior cannot be guaranteed by SKILL.md text alone; a future hardening could run check via a read-only wrapper. Model recommendation lists must weigh this finding.
