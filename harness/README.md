# Eval Harness

L1/L2 skill evals over the fixture corpus (see `openspec/specs/testing-harness/spec.md`). L0 unit tests live in `tests/unit/` and never call models. The L1 verdict logic is shared between both runners via `l1_checks.py` (pure functions, unit-tested).

## Authoritative runs (Inspect + OpenRouter, metered)

Export `OPENROUTER_API_KEY` first.

```sh
uv run inspect eval harness/skill_evals.py@check_report \
    --model openrouter/anthropic/claude-haiku-4.5 --log-dir logs/evals

# model matrix in one invocation (one log per model):
uv run inspect eval harness/skill_evals.py@review_fixture \
    --model "openrouter/anthropic/claude-haiku-4.5,openrouter/deepseek/deepseek-v4-flash"
```

Judge model: `JUDGE_MODEL` env, default `openrouter/anthropic/claude-haiku-4.5`.
View transcripts: `uv run inspect view --log-dir logs/evals`.

Tasks: `write_from_seed` (w01 seed to draft; L1 check-clean, L2 RQ rubric), `review_fixture` (f05; L1 review file + untouched proposal, L2 review rubric), `review_fixture_de` (f04; German review), `check_report` (f15; L1 report fidelity + untouched proposal), `ideate_socratic` (persona dialogue; L1 seed file, L2 Socratic rubric), `customize_override` (f00; supervisor requirements to valid TOML overrides), `publish_build` (f00; real pandoc/typst pipeline to PDF), `import_messy` (pasted messy text to standard format, personal data stripped), `litsearch_expand` (w03; live academic APIs — network-dependent, expect flakiness).

## Dev runs (real Claude Code binary, Max subscription)

Stages a fixture into a temp workspace, installs the skill into `.claude/skills/` (real skill discovery), runs headless `claude -p`, applies the same L1 verdicts:

```sh
uv run python harness/claude_runner.py check_report --model haiku
uv run python harness/claude_runner.py review_fixture --model sonnet
uv run python harness/claude_runner.py write_from_seed
```

Fast, free on the subscription, highest execution fidelity — but no L2 judging and no per-model comparison logs; it is the everyday loop, not the source of record.

## Known limitations

- **Autonomous-harness overreach is pervasive and unguardable by instructions.** In the Inspect agent loop, models modify the proposal during advisory/read-only skills (check *and* review) despite escalating prohibitions. The mechanical hardening was defeated outright: given the SKILL.md chmod guard, Haiku executed `chmod a-w`, later ran `chmod u+w` to remove its own protection, and edited anyway (`check_report_hardened`, 2026-07-29). The same scenarios under the real Claude Code binary (dev runner) hold the mandate — the production environment, not prompt text, is the effective guard. `check_report`, `check_report_hardened`, and the `review_fixture` byte-identity assertions are therefore expected-red on the Inspect path and serve as environment-fidelity probes; details in the archived changes.
- The Inspect agent loop approximates but does not replicate real agent harnesses; the dev runner covers the Claude Code case, other agents remain untested (spec risk S5).
