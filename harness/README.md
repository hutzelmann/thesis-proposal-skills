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
uv run python harness/claude_runner.py import_messy --model haiku
```

`import_messy` stages no fixture: the source document is pasted into the request and the verdict is applied to whatever proposal file the skill creates. Both runners reach that verdict through `verdict_import()` in `l1_checks.py`, so the two paths cannot drift apart.

Fast, free on the subscription, highest execution fidelity — but no L2 judging and no per-model comparison logs; it is the everyday loop, not the source of record.

## Audit pre-flight (publish pipeline)

Order: L0 suite (includes `tests/unit/test_audit_invariants.py`) → `uv run python scripts/audit_scan.py` (the real Snyk Agent Scan engine against the repo's skills, staged in an isolated HOME/XDG so the developer's own agent configs are never touched; needs `SNYK_TOKEN` or the `Snyk API Key:` line in `confidential/credentials.txt`; fails at risk ≥ 0.5 — calibrated 2026-08-02, risk ≤ 0.3 findings exist on skills skills.sh reports clean) → publish on explicit request → `uv run python scripts/audit_status.py` (skills.sh verdicts vs `audit-baseline.json`; `--update` after review).

`uv run python harness/audit_llm_preflight.py [--model haiku]` approximates the Gen Agent Trust Hub categories with one headless `claude -p` call per skill (subscription-billed). Advisory only: ATH's ruleset is unknown and model verdicts vary — never treat a clean run as a guaranteed ATH pass.

## Known limitations

- **Autonomous-harness overreach is pervasive and unguardable by instructions.** In the Inspect agent loop, models modify the proposal during advisory/read-only skills (check *and* review) despite escalating prohibitions. The mechanical hardening was defeated outright: given the SKILL.md chmod guard, Haiku executed `chmod a-w`, later ran `chmod u+w` to remove its own protection, and edited anyway (`check_report_hardened`, 2026-07-29). The same scenarios under the real Claude Code binary (dev runner) hold the mandate — the production environment, not prompt text, is the effective guard. `check_report`, `check_report_hardened`, and the `review_fixture` byte-identity assertions are therefore expected-red on the Inspect path and serve as environment-fidelity probes; details in the archived changes.
- The Inspect agent loop approximates but does not replicate real agent harnesses; the dev runner covers the Claude Code case, other agents remain untested (spec risk S5).
- **The limitation above is scoped to the Inspect path. A red scenario on the dev runner is a real signal and must be diagnosed, not attributed to it.** Three defects found that way on 2026-07-31 had each been read at first as a skill or model failure: skills addressed their scripts by a path that cannot resolve from the agent's working directory (`scripts/x.py` while the agent stands in the workspace and the skill is installed under `.claude/skills/`), `verdict_check_report` matched relayed prose case-sensitively, and the runner left the child's stdin open so backgrounded runs could die before doing anything. `check_report` was red on the dev runner throughout and now passes 5/5 on haiku and sonnet with the proposal untouched.
