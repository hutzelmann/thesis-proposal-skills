# Grade dev runs with a subscription judge

## Why

The dev runner (`harness/claude_runner.py`) runs a skill on the Claude Max subscription, but it cannot grade the semantic (L2) rubrics. Its docstring says "No judge/L2 (use Inspect for that)" (`claude_runner.py:8`). So every rubric question about a draft goes to Inspect, and Inspect has only one backend, OpenRouter. On 2026-10-04 this cost $7.88:

- **$5.2374, a matrix run** of `write_rich_seed` and `write_repair_citations` on haiku-4.5 and sonnet-5. Both scenarios already had dev-runner twins (`claude_runner.py:275`, `:286`). They went metered only because the rubric judge lived in Inspect. The estimate was $4.16, so the actual cost was 26% higher.
- **$2.645, a re-grade** of drafts the subscription had already produced: 48 calls to the outdated `claude-sonnet-5`, sent from a scratch script started with `--env-file .env`. No cost gate saw that run. It was approved at about $0.70 and cost 3.8× as much.

`poe smoke` costs about $1.08 per run (estimated; $0.61 measured on 08-06, $2.27 at three epochs on 08-24). It checks three core tasks that the subscription runner can check at $0, except for one scenario the runner lacks (`customize_override`).

There is also a recording defect. `poe dev --model sonnet` reports the alias `sonnet` (`claude_runner.py:468`), while the run actually used `claude-sonnet-5-5`. A dev number cannot be tied to the model that produced it.

The user's decisions (2026-10-04):

- Move the dev loop to the subscription now: dev-runner judge, re-grades and smoke.
- Use `claude-sonnet-5-5` as the dev judge, by full ID, with effort pinned.
- Keep the matrix judge and persona on `openrouter/anthropic/claude-haiku-4.5` until a full re-baseline (deferred Change D).

## What Changes

- **New `harness/claude_cli.py`: pure, L0-covered plumbing for text-only calls to the official `claude` binary on the subscription.**
  - `build_command` builds `claude -p --model <full id> --safe-mode --system-prompt … --tools "" --effort <pinned> --output-format stream-json --verbose --no-session-persistence --max-turns 1`. The prompt goes on stdin, and the command never carries `--bare`.
  - `child_env` builds the child's environment from an allowlist, so no API key, gateway variable, inherited effort or host-session variable reaches the child. The only credential passed through, unread, is the subscription's own long-lived token (`CLAUDE_CODE_OAUTH_TOKEN`) when the operator exported one, because isolated runs already rely on it.
  - `parse_stream` reuses `routing.error_result_reason`. It raises a typed `SubscriptionUnavailable` for:
    - an error result, including an expired login reported as subtype `success`;
    - an empty result, zero output tokens or an empty `modelUsage`;
    - a rate-limit status that is neither `allowed` nor `allowed_warning`;
    - no rate-limit report at all, so overage cannot be ruled out;
    - overage use;
    - an API-key source, or a provider other than Anthropic's own API;
    - a served model other than the one requested.
  - It records the CLI version, the effort, the thinking tokens and the notional cost.
  - Runtime guards:
    - a fixed working directory outside every measured workspace;
    - the child is killed on timeout or cancellation;
    - a module-level `anyio.CapacityLimiter(4)`;
    - a `claude auth status` preflight: `authMethod` must be `claude.ai`, or `oauth_token` with an exported long-lived token;
    - one serialized warm-up call while the stored login is kept current.
- **New `harness/l2_rubrics.py`, with no Inspect imports.** `CRITERIA`, the two citation criteria, the judge instructions and the prompt builder move here from `skill_evals.py`. A byte-for-byte parity test against golden prompts recorded before the move proves that matrix L2 sends exactly what it sent before. The dev runner asks the judge about the visible user request; Inspect keeps `state.input_text`.
- **`claude_runner.py`:**
  - `--judge` grades the scenarios that have a rubric twin with `roles.dev_judge` at `roles.dev_judge_effort`. It requires `--isolated`. Output is labelled "dev-runner L2, not comparable to matrix".
  - `--rejudge <workspace>…` re-grades kept workspaces at $0 and replaces the ad-hoc re-grade scripts.
  - `--max-notional` caps the cumulative notional cost of the judge calls.
  - A judge that cannot produce a grade exits with its own "untested" status, never with FAIL. Runner failures get a status distinct from FAIL too.
  - The model under test no longer inherits billing variables: every `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch is stripped from its environment. Effort and session variables stay, because they are part of what a dev run measures. A model run that still shows API billing, overage or no rate-limit report is untested.
  - The summary records the resolved model ID and the CLI version beside the requested alias.
  - The docstring at `:8` is rewritten.
  - A new `customize_override` scenario completes the core set.
- **`pyproject.toml`:**
  - `poe smoke` becomes a subscription dev-runner sequence over the core scenarios. Each step is `--isolated` with a `--max-budget-usd 2` cap, and the sequence uses `ignore_fail` and ends with a closing summary. Its steps are typed as commands (`default_item_type = "cmd"`), since poethepoet would otherwise read them as task names. `write_from_seed` is judged.
  - The old metered command moves to `poe smoke-inspect`, which takes its model from `roles.smoke` through a new selection-only `matrix.py --smoke` flag and stays behind the unchanged cost gate.
  - `harness/claude_runner.py` comes off the coverage omit list. L0 already runs much of it, and the new `main(argv)` tests run more. With it counted, the total measured 84% against the 78% floor on 2026-10-05.
  - `anyio` becomes an explicit dev dependency.
- **`support.py`:** a pure `is_subscription_model()` prefix rule. It is not a `[[models]]` row, so a subscription ID never becomes a matrix row.
- **Docs:** the `harness/README.md` and `AGENTS.md` wording that depends on `--judge` or on the new smoke. That is:

  - the citation-scenario paragraph, the probe paragraph and the "no L2 judging" sentence;
  - the path table's L2, smoke and re-grade rows (smoke row → `poe smoke-inspect`, plus a subscription `poe smoke` row);
  - both smoke lines;
  - the coverage omit comment;
  - the `ideate_scoped` paragraph's "a one-shot `claude -p` cannot hold the dialogue", which steer hands over: reviewed and kept, because the dev runner stays single-turn.

  The docs also carry the quota caveats: 5-hour and weekly plan limits shared with interactive use, "$0" only while extra usage stays off, and effort pinned so an inherited `CLAUDE_EFFORT=xhigh` cannot inflate usage.

Not in this change: moving the matrix judge or persona (deferred Change D), the cost-estimate recalibration (`fix-openrouter-caching`), and the registry roles table itself (`track-model-currency`).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`:
  - MODIFIED "Dev-runner cost and helper-agent telemetry": the summary carries the resolved model, the CLI version, the L2 grades, the judge identity and the notional cost. Untested runs and runner failures get exit statuses distinct from FAIL. Billing variables are stripped from the model run, and a model stream without a rate-limit report is untested. L0 coverage extends to the judge command, both child environments and the stream checks.
  - MODIFIED "Inverted-hybrid runners": "judge models" on the metered path now means the judge of authoritative runs. The dev runner's own judge is part of the dev loop, and its grades are never a source of record.
  - ADDED "Subscription text roles (dev runner)": how a text-only role runs on the subscription, how it fails closed, how it is bounded, and that `poe smoke` runs there.

## Impact

- **New code:** `harness/claude_cli.py`, `harness/l2_rubrics.py`, `tests/unit/test_claude_cli.py`, `tests/unit/test_l2_rubrics.py`, and synthetic stream fixtures under `tests/unit/data/claude_cli_streams/` with a README.
- **Changed code:**
  - harness: `claude_runner.py`, `skill_evals.py` (imports the moved rubric material; the scorers are unchanged), `support.py`, `matrix.py` (selection flag only), `l1_checks.py` (an aggregate L2 verdict);
  - project files: `pyproject.toml` (the smoke tasks and the coverage omit list), `harness/README.md`, `AGENTS.md`;
  - tests: `test_dev_runner_probe.py`, `test_support_matrix.py`, `test_eval_wiring.py`.
- **Generated copies:** none change. `CRITERIA` text is unchanged, so the `evals/evals.json` projection drift test stays green.
- **Depends on:**
  - `track-model-currency`, landed first: its `[roles]` table supplies `dev_judge`, `dev_judge_effort` and `smoke`, and its guard test forbids hardcoded model IDs;
  - `keep-isolated-login` and `record-routing-host-errors`, already on `main` (`host_login.keep_login`, `login_remedy`, `routing.error_result_reason`, `expired-login.jsonl`).
- **Plan usage (notional, not money):**
  - a judged write scenario is two Sonnet calls, about $0.11;
  - a 48-call re-grade is about $2.6;
  - a smoke run is one judged and two unjudged scenarios.

  All of it draws on the same 5-hour and weekly limits as interactive use. `--max-notional` bounds it.
- **Money:** metered spend for dev iteration, re-grades and smoke goes to $0. The only metered calls in this change are the optional `poe smoke-inspect` and any later confirming Inspect run, both behind the existing gate.
