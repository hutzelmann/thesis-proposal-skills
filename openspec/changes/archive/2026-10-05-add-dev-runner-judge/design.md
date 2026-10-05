# Design

## Context

The proposal (Why) covers the motivation. The design rests on the following state.

**Current code:**

- `claude_runner.py` runs the model under test synchronously with `subprocess.run`.
  - It parses stream-json and judges L1 through `l1_checks.py`.
  - It ends host failures with `sys.exit(message)`, which gives exit status 1, the same status as a skill FAIL.
  - `summary()` records `args.model`, the alias (`:468`).
  - `--isolated` enters `routing.isolated_config`, whose `host_login.keep_login` keeps the stored login current. A refresh claim serializes concurrent refreshes; it is taken only when the stored token is about to expire.
- The L2 judge exists only inside Inspect.
  - `skill_evals.judge()` (`:311`) formats `harness/rubrics/<file>.txt` with `question`, `answer`, `criterion` and `JUDGE_INSTRUCTIONS`, then calls `get_model(JUDGE_MODEL)`.
  - For the write tasks, `question` is `state.input_text`: the whole skill prompt, SKILL.md included.
  - For the review tasks, it is the fixture oracle's `semantic` list.
  - `CRITERIA` (`:100`) feeds the `evals/evals.json` projection through `eval_export.py`.
- `track-model-currency` (landed before this change) adds a `[roles]` table to `harness/models.toml` with the keys `judge`, `smoke`, `dev_judge` (`claude-sonnet-5-5`) and `dev_judge_effort`. There is no `persona` key: `persona` resolves to `judge` when absent, through `support.role_model`. It also adds a guard test that forbids hardcoded model IDs outside an allowlist.

**Host 2.1.284 behaviour the design relies on**, recorded 2026-10-04 (scratchpad `cc/`, `mv/`, dossier §A):

- `--bare` never reads OAuth. `--safe-mode` keeps auth and disables CLAUDE.md, skills, plugins, hooks, MCP and output styles: 658 input tokens with it against 7,029 without on the same prompt.
- Passing the prompt on stdin works (validity reviewer, two calls).
- `--max-turns` is accepted although `--help` does not list it.
- `--effort` takes `low|medium|high|xhigh|max`.
- The stream's `system/init` event carries `model`, `apiKeySource` (`none` under OAuth) and `claude_code_version`.
  - `rate_limit_event.rate_limit_info` carries `status` and `isUsingOverage`. A recorded probe shows `status: allowed_warning` at 0.82 seven-day utilization (`mv/probe1.jsonl`).
  - The `result` event carries `modelUsage[<id>]` with `outputTokens`, `thinkingTokens` and `provider: firstParty`, plus `total_cost_usd`, which is notional.
  - A full agent session can list an auxiliary model in `modelUsage` beside the main one: haiku beside sonnet in `logs/routing/events-litsearch-collision.jsonl`.
- An expired login arrives as `is_error: true`, `subtype: success`, with the reason in `result`. `routing.error_result_reason` already composes it, and `host_login.login_remedy` adds `/login`.
- `claude auth status --json` reports `loggedIn`, `authMethod` (`claude.ai`, or `oauth_token` with `CLAUDE_CODE_OAUTH_TOKEN`) and `apiProvider`. It also carries email and organization fields, which are never printed.

## Goals / Non-Goals

**Goals:**

- Dev-loop rubric grading, re-grading and smoke cost $0 in money and draw a bounded, visible amount of plan quota.
- No subscription failure mode can turn into a FAIL, and none can silently fall back to metered billing.
- Matrix L2 is provably unchanged: same prompts, same judge, same backend.
- The text-call module can be reused unchanged when Change D wraps it as an Inspect provider.

**Non-Goals:**

- Moving the matrix judge or persona (Change D, deferred by decision 1), or any change to `report.py`, `matrix.py` gating or `record_spend`.
- Multi-turn dev-runner scenarios. Persona dialogues stay on Inspect.
- Re-judging Inspect `.eval` logs. Replaying recorded matrix prompts belongs to Change D's agreement check.
- Pricing subscription IDs inside the matrix estimate. No subscription model reaches Inspect in this change.
- Allowlisting the model-under-test child's environment. The validity review (V6) proposed it, and final.md accepted V6 only in part. Stripping the inherited `CLAUDE_EFFORT` from model runs changes dev-run measurement conditions and deserves its own change. Here the model run gets a narrow strip of billing variables only (Decision 3, last part) and the post-hoc stream checks (Decision 5).
- The routing rig's child environment (`routing.py:486`). It inherits the launching environment too. The same billing strip would fit there, but routing is not otherwise touched by this change.

## Decisions

### 1. A plain text-call module over the official binary, not an Inspect provider

`harness/claude_cli.py` holds pure functions (`build_command`, `child_env`, `parse_stream`, `check_auth_status`) and one async runner, `call(...)`. The runner spawns the child with `anyio.open_process`, writes the prompt to stdin, reads stdout, and returns a `JudgeCall` dataclass (text, served model, CLI version, effort, thinking tokens, notional cost, rate-limit window). Failures raise `SubscriptionUnavailable(reason)`.

Alternatives considered:

- **A `claude-code/<id>` Inspect `ModelAPI` now.** That is Change D's shape. Registering it now invites a matrix judge switch without `model_roles`, report filtering or a re-baseline: validity blocker V1, which was accepted. The async `call()` keeps D a thin adapter.
- **The Agent SDK.** It needs an SDK dependency, and its docs steer to API-key auth.
- **The OAuth token in Inspect's `anthropic/` provider.** That is a policy violation: token handling by a third-party client.
- **`--bare`.** It cannot use the subscription.

### 2. Command shape

```
claude -p --model <full id> --safe-mode --system-prompt <JUDGE_SYSTEM> --tools ""
       --effort <pinned> --output-format stream-json --verbose
       --no-session-persistence --max-turns 1          (prompt on stdin)
```

- `--safe-mode`, not `--system-prompt` alone. A replaced system prompt still leaked about 6.4k tokens of plugin and hook context and changed the output style (dossier call #1).
- stream-json with `--verbose`, not `json`. Only the stream carries `rate_limit_event` (cost-policy C2), and `init` carries the CLI version and the API-key source.
- `--effort` is pinned from `roles.dev_judge_effort` and validated against the CLI's five levels. `MAX_THINKING_TOKENS=0` is not used: "non-reasoning parity" is void for 5.5-generation judges (V3), so thinking tokens are recorded instead.
- `JUDGE_SYSTEM` is one fixed neutral sentence in `l2_rubrics.py`. The Inspect judge has no system prompt. This difference is one of the reasons the dev L2 is labelled not comparable.
- stdin rather than an argument. Linux caps a single argument at about 128 KiB, and drafts plus rubric approach that.

### 3. Child environments: an allowlist for the judge, a billing strip for the model run

Keep `PATH`, `HOME`, `USER`, `LOGNAME`, `LANG`, `LC_*`, `TMPDIR`, `XDG_*` and `CLAUDE_CONFIG_DIR`, plus `CLAUDE_CODE_OAUTH_TOKEN` when present. Everything else is dropped. That covers `ANTHROPIC_*`, every `*_API_KEY` (`OPENROUTER_API_KEY` reaches the runner's environment whenever `.env` is loaded), `CLAUDE_CODE_USE_*`, `CLAUDE_EFFORT`, `CLAUDECODE`, the other `CLAUDE_CODE_*` and `MAX_THINKING_TOKENS`.

- **Deviation from final.md, recorded:** the plan dropped all `CLAUDE_CODE_*`. `CLAUDE_CODE_OAUTH_TOKEN` is the subscription's own long-lived login. `prepare_config` already supports it for isolated runs (spec "Isolated measurement environment"), and dropping it would break judging for an operator who uses `setup-token`. It is passed through by name, and its value is never read.
- **Alternative: denylist `ANTHROPIC_API_KEY` only.** Rejected under feasibility F4. Gateway variables (`ANTHROPIC_AUTH_TOKEN` with `ANTHROPIC_BASE_URL`, Bedrock switches) would silently move calls to metered billing, and the launching session's effort and session coupling would leak in.

**The model-under-test child: billing variables stripped, nothing else.** `run_claude` today passes `dict(os.environ, …)`, or the bare inherited environment in ambient mode (`claude_runner.py:388`). An exported `ANTHROPIC_API_KEY`, or an `ANTHROPIC_BASE_URL` plus `ANTHROPIC_AUTH_TOKEN` gateway, would therefore bill the model run with no cap. The stream checks would only mark it untested afterwards. A pure `model_env(environ, config)` now drops every `ANTHROPIC_*` variable and every `CLAUDE_CODE_USE_*` provider switch, in ambient and isolated mode alike. It sets `CLAUDE_CONFIG_DIR` when isolated, and keeps everything else.

- `CLAUDE_EFFORT`, `CLAUDECODE`, the other `CLAUDE_CODE_*` (including `CLAUDE_CODE_OAUTH_TOKEN`) and every other `*_API_KEY` stay. Effort and session coupling remain part of what a dev run measures (the Non-Goal above). Skills may legitimately read their own literature-search keys, and the host reads no `*_API_KEY` but its own.
- Here, unlike the judge, a prefix denylist is the right shape. The judge is a fixed text call, so it can be given exactly what it needs. The model run is the measurement, and only its billing route is out of bounds. The two prefix families cover the gateway and cloud-provider routes that F4 named.
- Residual routes are a settings `apiKeyHelper` (ambient mode only; isolated settings are emptied) and a stored Console login. Neither is an environment variable. Both surface as an `apiKeySource` other than `none`, so check 3 marks the run untested. `--max-budget-usd` bounds what such a run can spend, and the smoke passes it on every step (D8).
- Alternative: an allowlist for the model run, as for the judge. Rejected for this change; see the Non-Goal.

### 4. Preflight, warm-up and concurrency

- **Preflight.** Run `claude auth status --json` with the child environment and the judge's config directory. Require `loggedIn`, an `authMethod` of `claude.ai` (or `oauth_token` with the long-lived token exported) and `apiProvider: firstParty`. Read only those three fields.
- **Warm-up.** The first real judge call of an invocation runs alone; it is the warm-up. It runs inside `isolated_config`, and that config's `keep_login` holds the refresh claim when the token is due. One process refreshes, and the write-back lands before any fan-out (F3).
  - Alternative: a dedicated throwaway ping call. Rejected because it spends quota and proves nothing the first real call does not.
- **Concurrency.** A module-level `anyio.CapacityLimiter(4)` wraps every child process (F2). anyio 4 creates the limiter lazily outside an event loop. The runner calls `anyio.run` once per invocation. `anyio` becomes an explicit dev dependency instead of riding on Inspect's.
- **Isolation.** `--judge` requires `--isolated` and is refused before staging. The judge reuses the run's isolated config. `--rejudge` always enters its own `isolated_config("devjudge-config-")`. The judge therefore never reads the operator's ambient config, even apart from `--safe-mode` (V6, accepted in part).
- **Working directory.** One fixed directory, `<tempdir>/thesis-proposal-devjudge`, created on first use. Nothing is ever written into it. Its fixed path keeps the host's injected environment block stable between runs.

### 5. Fail-closed stream parsing

`parse_stream(events, requested)` raises `SubscriptionUnavailable` in these cases, checked in this order:

1. `routing.error_result_reason(events)`, passed through `login_remedy`. Reusing it, rather than writing a third copy, follows "extract at the third repetition".
2. No `result` event, a non-string or empty `result`, zero output tokens, or an empty `modelUsage`.
3. `init.apiKeySource` other than `none`, or any `modelUsage` entry whose `provider` is not `firstParty`.
4. No `rate_limit_event` at all, any `rate_limit_event` with `isUsingOverage: true`, or one with a `status` outside `{allowed, allowed_warning}`.
5. A `modelUsage` key other than `requested` with output tokens above zero, or `requested` absent.

**Refinement of C2, recorded:** final.md said "status not `allowed`". The recorded `allowed_warning` at 82% weekly utilization is a legitimate allowed state. Failing closed on it would block judging for the last quarter of every week. It counts, and its window and utilization are reported. Any unknown status still fails closed.

**An absent rate-limit event fails closed.** The stream's `rate_limit_event` is the only signal that a call stayed out of overage. Without it, "$0" would rest on the account setting alone. Host 2.1.284 emitted one in every stream on record: both probe streams in the dossier, and both full agent sessions under `logs/routing/` (one event each, checked 2026-10-05). A stream without one is therefore untested, with the reason "rate limit not reported, overage cannot be ruled out" and the CLI version named. If a host stops emitting the event, every judged criterion and every dev run reads untested. That is loud and visible. The fix is a harness change that reads whatever replaced the event, never a relaxed rule.

- Alternative: grade it, and flag "overage not detectable" in the summary. Rejected. The goal is that no failure mode falls back to metered billing silently, and a flag in a JSON summary that nobody reads is silent in practice.
- Check 1 runs first, so an expired-login stream, which carries no rate-limit event, still yields the `/login` reason rather than this one.

A response without a `GRADE:` line also counts as unavailable (untested). Inspect's `parse_grade` reads it as I. For the dev runner, a limit or refusal text would otherwise be a silent FAIL (C2). `l2_rubrics.read_grade()` returns `True`, `False` or `None`. The aggregate `verdict_l2_grades()` lives in `l1_checks.py`, per the convention that verdicts sit beside their L0 tests.

Checks 3 and 4 also run over the model-under-test stream, the absent-event rule included. A dev run that spilled into overage, that was billed to an API key, or that does not report its rate limit is untested and is not judged. By then the money is already spent, bounded by `--max-budget-usd`, but the run cannot be mistaken for a subscription result. The billing strip from Decision 3 keeps the common routes from opening at all.

### 6. Rubric material shared, matrix prompts pinned

`harness/l2_rubrics.py`, free of Inspect imports, takes over the following from `skill_evals.py`:

- `RUBRICS`, `JUDGE_INSTRUCTIONS`, `CITATION_SCOPE`, `CITATION_SYNTHESIS` and `CRITERIA`;
- a new `JUDGE_SYSTEM`;
- `judge_prompt(rubric, question, answer, criterion)`;
- `read_grade`;
- `DEV_RUBRICS`. It maps a dev scenario to its criteria by the same `(task, scorer)` keys, so a criterion cannot diverge between runners. Each entry also names the rubric file and the question source: the visible request for the write scenarios, the oracle `semantic` list for the review scenarios.

`skill_evals.py` imports these, and `CRITERIA` stays importable from it, so `eval_export.py` and the projection are untouched. The criteria text is unchanged and the projection drift test proves it. The Inspect scorers keep passing `state.input_text`.

**Parity.** Before the move, a task records golden prompts. For every rubric file, it captures the output of the current formatting code with synthetic question, answer and criterion values, and stores them in `tests/unit/data/l2_prompts/`. After the move:

- `test_l2_rubrics.py` compares `judge_prompt` with the golden prompts byte for byte;
- `test_eval_wiring.py` runs `skill_evals.judge()` against a fake model and asserts that it sends exactly the golden prompt.

Alternative: one question for both runners, the visible request. The feasibility minor suggested it. Rejected for now because it would change matrix L2 prompts and so shift shipped verdicts, which is Change D's re-baseline problem. The dev judge's question differs, and the label says so.

Dev scenarios with a rubric twin:

| Scenario | Criteria |
|---|---|
| `write_from_seed` | RQ quality, density |
| `write_rich_seed` | citation scope, synthesis |
| `write_repair_citations` | citation scope, synthesis |
| `review_fixture` | review quality |
| `review_hollow` | hollow review |

`--judge` on any other scenario is a usage error, so nobody believes they received L2. When the graded artifact is missing (no draft selected, no review file), L2 reads "not judged: no artifact" and no call is made.

### 7. Runner integration and exit statuses

| Status | Meaning |
|---|---|
| 0 | every computed verdict passed |
| 1 | a verdict failed (L1, or a graded L2 criterion) |
| 2 | usage error (argparse) |
| 3 | untested: the subscription could not serve the run or the judge |
| 4 | other runner failure |

- `run_claude` raises a typed `RunnerFailure(message, untested)` instead of calling `sys.exit`, and starts the host with `model_env` (D3). Untested covers a login failure, detected by `host_login.LOGIN_FAILURE`, and checks 3 and 4 from D5 on the model stream: an API-key source, overage, a refused or unknown rate-limit status, and no rate-limit event at all. Everything else is status 4. Messages are unchanged.
- Precedence: 4, then 1, then 3, then 0. A real FAIL outranks an ungraded criterion.
- Summary keys:
  - `model_requested` is the alias.
  - `model` is the served ID, from `init.model` and checked against `modelUsage`.
  - `cli_version`.
  - With judging: an `l2` block (per-criterion grade or untested reason, judge model, effort, CLI version, thinking tokens, notional cost), `l2_label: "dev-runner L2, not comparable to matrix"`, and `self_graded: true` when the served model under test equals the judge's ID (validity minor: self-graded row noted).
- `--max-notional USD`, default 5.00, caps the judge calls' cumulative `total_cost_usd` for the invocation. The model run keeps its own `--max-budget-usd`.
- `--rejudge DIR [DIR …]` takes the positional scenario and kept workspaces of it. It selects each artifact with the same selection functions the L1 verdicts use, grades it, and prints one summary per workspace. After the warm-up it prints the projection and refuses the batch above the cap.
- `--summary-log PATH` appends the run's summary as one JSON line on every exit path, failures included. `--summarize PATH` prints one row per scenario (latest line), exits non-zero unless every row passed, and removes the log. The row logic is a pure function with L0 tests.
- The dev judge ID is validated with `support.is_subscription_model()`: a `claude-` prefix, no `/`, and a digit. That rejects aliases and provider-qualified metered IDs alike. It is a prefix rule rather than a registry row, so it never becomes a matrix row (feasibility minor). It is not wired into `estimate_cost` or `price_usage` here, because no subscription ID reaches them until Change D.

### 8. Smoke

```toml
[tool.poe.tasks.smoke]
sequence = [
  "python harness/claude_runner.py write_from_seed --isolated --max-budget-usd 2 --judge --summary-log logs/devrun/smoke.jsonl",
  "python harness/claude_runner.py import_messy --isolated --max-budget-usd 2 --summary-log logs/devrun/smoke.jsonl",
  "python harness/claude_runner.py customize_override --isolated --max-budget-usd 2 --summary-log logs/devrun/smoke.jsonl",
  "python harness/claude_runner.py --summarize logs/devrun/smoke.jsonl",
]
default_item_type = "cmd"
ignore_fail = "return_non_zero"
```

- `default_item_type = "cmd"` is required. poethepoet 0.48 reads a plain string in a `sequence` as a reference to another task (`default_array_item_task_type = "ref"`, `poethepoet/config/partition.py:248`). The repository sets no project-wide override, and `setup = ["_sync_dev", …]` relies on the `ref` reading. Without the option, `python harness/claude_runner.py …` would be looked up as a task name. Setting it on the task rather than project-wide leaves `setup` and `test` untouched. An L0 test reads the task with `tomllib` and pins the option (tasks 2.8).
- `--max-budget-usd 2` on every model run. On the subscription it caps notional spend, which is plan quota. On any residual billing route that the strip in Decision 3 cannot close (a stored Console login), it caps money. The value follows the runner docstring's own example and sits above the ~$0.3–1 notional figure for a haiku write run. A step that hits it is a runner failure (status 4) and shows as such in the summary, never as a pass. Task 8.3 checks that no step comes near the cap.
- No `envfile`. The subscription needs no key, and not loading `.env` keeps `OPENROUTER_API_KEY` out of the process entirely. A key the operator exported in the shell is removed from the model run by the billing strip (Decision 3) and from the judge by its allowlist. So "no metered call" rests on three things, all stated in the spec: the strip, the cap, and the post-hoc checks that report any other billing as untested.
- `customize_override` gets a runner scenario: fixture `f00-clean-en`, the Inspect request, and `verdict_customize_override` over the untouched proposal and `guidelines.md`.
- `logs/` is gitignored.
- `smoke-inspect` keeps `envfile = ".env"` and runs `python harness/matrix.py --smoke`. That new flag only selects: `roles.smoke` × `[tasks] core` × 1 epoch. It is refused with `--models`, `--tier`, `--tasks`, `--core` or `--epochs`, and the existing estimate and confirmation run unchanged.
- Alternative: multi-scenario support inside `claude_runner.main`. Rejected because the cross-change contract fixes a poe sequence, and one scenario per process keeps each isolated config and login claim scoped to one run.
- Alternative: soften the smoke promise to "billing detected and reported untested" without the strip and the cap. Rejected. Detecting billing after the fact is the weaker half, and closing the route costs one pure function and one flag per step.

### 9. The runner counts toward coverage

`pyproject.toml` omits `harness/claude_runner.py` from coverage, beside `skill_evals.py`. The omit comment calls both "metered-only … never at L0". That is false for the runner. `tests/unit/test_dev_runner_probe.py` already imports and runs `summary`, `telemetry`, `parse_events`, `host_command` and more. This change also adds in-process `main(argv)` tests of the exit-status mapping, the billing strip, the summary log and `--rejudge`. While the file stays omitted, the floor never sees any of it, which is the failure mode AGENTS.md names under "Scripts expose `main(argv…)`".

- The runner comes off the omit list. `skill_evals.py` stays on it, because it runs only under `inspect eval`. The comment is rewritten to name only `skill_evals.py`, whatever wording `steer-subscription-first` left. Its D5 keeps the list unchanged and calls the omission of new files this change's own decision.
- Measured on 2026-10-05 against the working tree at `9c106aa`, with a scratch coverage config that counts the runner: total 84% (4,496 statements, 732 missed), runner 65% (228 statements, 79 missed). The 78% floor holds before any new test.
  - Uncovered today: `run_claude`'s subprocess call, parts of staging, `containment_verdict`, `draft_verdict` and the `verdict` dispatch, and all of `main`.
  - The new in-process `main(argv)` tests reach `main` and the dispatch, with `run_claude` monkeypatched. The subprocess call itself stays uncovered, because it needs a live host.
- Alternative: keep it omitted and record why. Rejected. No reason survives the measurement.

### Critique dispositions carried by this change

| Point | How this change honours it |
|---|---|
| V3 env/effort/thinking | allowlist (D3), `--effort` pinned, `--safe-mode`, thinking tokens recorded |
| V4 / F1 errors become FAIL | typed `SubscriptionUnavailable` → status 3; no retries anywhere on this path |
| V6 different system (partly) | `--isolated` required, label, nothing written to `logs/evals`; confirmation on Inspect stays the route for shipped verdicts |
| F2 dead `max_connections` | module-level `CapacityLimiter(4)` with an L0 concurrency test |
| F3 concurrent refresh | warm-up first call under `keep_login`'s claim; ordered after keep-isolated-login (now on `main`) |
| F4 forwarded credentials | judge: allowlist plus `auth status` plus `apiKeySource`/`provider` checks; model run: `ANTHROPIC_*` and `CLAUDE_CODE_USE_*` stripped (D3), same stream checks |
| F5 smoke stops at first FAIL, no safe mode | `--isolated` sequence with `default_item_type = "cmd"`, `ignore_fail`, a per-step `--max-budget-usd` and a summary |
| C1 quota never sized | `--max-notional`, batch projection, notional figures in proposal and README |
| C2 no rate-limit or overage detection | stream-json; fail closed on overage, unknown status and an absent rate-limit event (refined for `allowed_warning`) |
| C3 policy | personal, local, unmodified binary, low volume, no token handling; matrix-scale use stays deferred (D) |
| Minors | resolved ID + CLI version + mismatch check + fixed cwd; kill on timeout and lazy cwd; ruff-clean; `error_result_reason` reused; matrix question kept by the parity test; self-graded flag; `/login`, never an API key, as the remedy |

V1, V2 and V5, and the report-side minors, concern the matrix judge and persona. They stay with Change D.

## Risks / Trade-offs

- **[`--max-turns` is undocumented]** → The L0 test pins it in the command. If a host drops it, the call fails visibly as untested with the CLI version recorded, never as a grade.
- **[`--bare` may become the default for `-p`]** → The call would then fail with a login error even though `auth status` passes. The untested message carries the CLI version, and the README tells the operator to re-check `claude --help` after a host upgrade. Adding an API key is never the fix.
- **[Injected context even in safe mode]** → About 480–640 tokens: an identity line, the date, the account email, the environment block. This is why the dev L2 is labelled not comparable. The fixed working directory keeps the block stable, so dev runs stay comparable with each other.
- **[`claude-sonnet-5-5` has no dated snapshot]** → The served-ID check catches an alias drift to another ID. A silent weight update under the same ID cannot be detected. Accepted; the CLI version and date are recorded.
- **[Plan quota shared with interactive use]** → Concurrency 4, the notional cap, no automatic retries, and README caveats on the 5-hour and weekly windows. Effort is pinned so the inherited `xhigh` cannot inflate usage. "$0" holds only while extra usage stays off. The parser fails closed on overage and on a stream that does not report its rate limit.
- **[A host stops emitting `rate_limit_event`]** → Every judged criterion and every dev run then reads untested, with the CLI version named. Dev L2 stops until the harness reads whatever replaced the event. Accepted as the price of not trusting the account setting alone (D5).
- **[The smoke's budget cap is too tight]** → A step that hits `--max-budget-usd 2` ends as a runner failure, and the smoke goes red without a skill defect. Task 8.3 records each step's notional cost against the cap. Raising the value is a one-line `pyproject.toml` edit, with no spec change.
- **[The billing strip changes alias resolution]** → `ANTHROPIC_DEFAULT_*_MODEL` variables are `ANTHROPIC_*` too, so an operator who remaps `sonnet` through them gets the host's own mapping in dev runs. The served-ID record shows which model ran. A run that resolves to the host default is the intended measurement.
- **[Self-grading]** → A Sonnet model under test graded by the Sonnet judge is flagged `self_graded` in the summary.
- **[Re-grade uses current rubric and request text]** → That is the purpose of a re-grade. A scenario whose request was edited since the run changes the question; the summary records the scenario name and the rubric file, and the README states the caveat.
- **[Exit status 1 → 4 for runner failures]** → No repository caller reads the runner's status apart from the new smoke sequence (checked in tasks). The README documents the table.
- **[Existing L0 streams lack a rate-limit event]** → The synthetic and recorded fixtures under `tests/unit/data/routing_streams/` carry none. A test that drives one through the new model-stream checks would read untested. Such tests get a synthetic copy with an `allowed` event; recorded fixtures are never edited.
- **[Policy grey area]** → The volume is tens of calls per loop, from the user's own unmodified binary, with no token handling. Hundreds of calls per matrix run are what decision 1 deferred.

## Migration Plan

No data migration. The order is `track-model-currency`, then this change, then `fix-openrouter-caching`.

Rollback is a revert. `poe smoke-inspect` keeps the former metered smoke available throughout, and the matrix path is untouched, so a revert affects only the dev loop.

## Open Questions

- **Roles accessor.** This change assumes `track-model-currency` exposes `dev_judge`, `dev_judge_effort` and `smoke` through `support.parse_registry(...)`. A different accessor name is a mechanical rename in tasks 3.x and 5.x.
- **Effort value.** It is whatever the registry pins in `dev_judge_effort`; this change validates only that it is a CLI level. After the first judged runs, compare thinking tokens and notional cost per call against the ~$0.055 assumption and adjust the registry value if needed. That is a registry edit, with no spec change.
- **`apiKeySource` under `setup-token`.** It is UNVERIFIED that a `CLAUDE_CODE_OAUTH_TOKEN` login reports `apiKeySource: none`. Until a live check, the rule stays strict. An operator on that path sees untested with the source named, and the fix is to confirm the value and widen the rule.
- **Is `rate_limit_event` always emitted?** Decided in D5: its absence fails closed. What stays open is whether a long agent session always emits one; the two recorded full sessions each carry one. Task 8.1 checks the judged dev run's stream for it before the rule is relied on.
- **Smoke budget value.** `--max-budget-usd 2` per step is an assumption taken from the runner docstring's example and the ~$0.3–1 notional figure for a haiku write run. `import_messy` and `customize_override` have no recorded notional cost yet. Task 8.3 measures them.
- **Coordination with `steer-subscription-first`.** It labels `poe smoke` as metered. Whatever wording steer left, this change rewrites:
  - the two smoke lines (`AGENTS.md` Commands block, `harness/README.md` matrix block);
  - the path table's smoke row, which becomes `poe smoke-inspect`, plus a subscription `poe smoke` row;
  - the path table's L2 row;
  - the coverage omit comment (D9).

  Steer's D7 assigns the first three to this change. The comment is steer's text, but this change edits the list it describes. Steer's D7 also hands over the `ideate_scoped` paragraph's "a one-shot `claude -p` cannot hold the dialogue". This change reviews it and keeps it: `--judge` grades a finished single-turn run, and multi-turn dev-runner scenarios stay a Non-Goal, so the sentence stays true (task 6.1).
