# Tasks

No task in this list makes a metered call. The single metered entry point this change touches is `poe smoke-inspect`, and it is verified with `--estimate-only` only. Running it for real requires showing its printed estimate to the user and an explicit approval of that amount; `--yes` is never passed on the user's behalf. Subscription calls (sections 8.1–8.3) cost no money but draw plan quota: run each one deliberately, once, never in a loop, and record its notional cost.

## 1. Preconditions and golden prompts

- [x] 1.1 Confirm that `track-model-currency` is on the branch:
  - `harness/models.toml` carries the roles table with `dev_judge`, `dev_judge_effort` and `smoke`;
  - the registry accessor exposes them;
  - its hardcoded-model-ID guard test exists.

  Note the accessor's actual name for tasks 4.x and 5.x. Verify: `grep -n '^\[roles\]' harness/models.toml` matches, and `uv run poe test` is green on the starting tree.

  Done 2026-10-05 at `138bf62`: `[roles]` at `harness/models.toml:26`; accessor `support.parse_registry(text).roles` (fields `dev_judge`, `dev_judge_effort`, `smoke`), with `support.role_model(roles, name, environ)` for the `<ROLE>_MODEL` override; guard `tests/unit/test_model_ids.py`. `poe test` green.
- [x] 1.2 Record the golden judge prompts before anything moves. For every rubric file that `skill_evals.py` passes to `judge()`, write `tests/unit/data/l2_prompts/<rubric>.txt`:
  - the rubric files are `rq_quality`, `density`, `citation_practice`, `review_quality`, `title_alarm` and `socratic`;
  - each golden file is the current formatting code's output (`template.format(question=…, answer=…, criterion=…, instructions=skill_evals.JUDGE_INSTRUCTIONS)`) with fixed synthetic values;
  - generate them with a throwaway script in the session scratchpad, run once with `uv run python`, never committed;
  - add a `README.md` there naming the inputs, the date and the commit they were recorded against.

  Verify: one file per rubric, each containing the synthetic answer verbatim and no unreplaced `{…}` placeholder.

  Note: the synthetic inputs live in `tests/unit/data/l2_prompts/inputs.json` rather than only in the README, so both parity tests read one source.
- [x] 1.3 Add the Inspect wiring parity test to `tests/unit/test_eval_wiring.py`. It monkeypatches `skill_evals.get_model` with a fake that captures the prompt, runs `skill_evals.judge()` for each golden case, and asserts the captured prompt equals the golden file byte for byte. Verify: it passes against the unmodified `skill_evals.py`, so the golden files reflect today's behaviour.
- [x] 1.4 Count the runner toward coverage (design D9). In `pyproject.toml` `[tool.coverage.run] omit`:
  - remove `harness/claude_runner.py`;
  - keep `harness/skill_evals.py`;
  - rewrite the comment above the list so it names only `skill_evals.py` (runs only under `inspect eval`, never at L0), whatever wording `steer-subscription-first` left.

  Verify: `uv run poe cov` holds the 78% floor and lists `harness/claude_runner.py`. Measured 2026-10-05 at `9c106aa`: about 84% total, runner 65%. Re-measured at `138bf62` with the omit entry removed: 85.10% total, runner 65% (228 statements, 79 missed).

## 2. Failing tests first

- [x] 2.1 Create the synthetic stream fixtures under `tests/unit/data/claude_cli_streams/`, one JSONL per shape. Use a synthetic model ID (for example `claude-fixture-1-0`) so the model-ID guard needs no allowlist entry. Shapes:
  - a success with `init.apiKeySource: none`, an `allowed` rate limit and one `modelUsage` key carrying output, thinking tokens and `provider: firstParty`, with a `GRADE: C` result;
  - `allowed_warning` with utilization;
  - overage in use;
  - a `rejected` status;
  - an unknown status;
  - zero output tokens;
  - an empty `modelUsage`;
  - an empty result;
  - an API-key source;
  - a non-first-party provider;
  - a mismatched served model;
  - an auxiliary zero-output key, which passes;
  - no `GRADE` line;
  - no result event;
  - no rate-limit event, otherwise identical to the success shape and carrying a `GRADE: C` result.

  Reuse `routing_streams/expired-login.jsonl` rather than copying it. Add a provenance `README.md` in the format of `routing_streams/README.md`. Verify: every file parses with `jq -c . <file>`.
- [x] 2.2 Write `tests/unit/test_claude_cli.py`. Cover:
  - `build_command`: the exact flag list from design D2, the full ID, effort from the argument (an invalid level raises), no `--bare`, and no prompt text in argv;
  - `child_env`: the allowlist is kept; `ANTHROPIC_*`, `*_API_KEY` including `OPENROUTER_API_KEY`, `CLAUDE_CODE_USE_*`, `CLAUDE_EFFORT`, `CLAUDECODE`, the other `CLAUDE_CODE_*` and `MAX_THINKING_TOKENS` are dropped; `CLAUDE_CODE_OAUTH_TOKEN` passes through; `os.environ` is not mutated;
  - `parse_stream` on every fixture from 2.1, including the expired-login fixture: the raised reason carries `/login`;
  - the no-rate-limit-event fixture raises `SubscriptionUnavailable` despite its grade line, and the reason says the rate limit was not reported and overage cannot be ruled out (design D5, check 4). The expired-login fixture, which also lacks the event, still raises the `/login` reason, which pins the check order;
  - `check_auth_status`: `claude.ai` passes; `oauth_token` passes with the token present; an API key, `loggedIn: false` and a non-first-party provider raise; the email and organization values never appear in a message;
  - the limiter: ten concurrent calls against a fake process never exceed four in flight, and the warm-up call completes before any other starts;
  - a timeout kills the fake child, which is reaped;
  - the working directory is created on first use, at a fixed path outside `tmp_path` workspaces.

  Verify: the file fails because `claude_cli` does not exist.
- [x] 2.3 Write `tests/unit/test_l2_rubrics.py`. Cover:
  - `judge_prompt` matches every golden file from 1.2 byte for byte;
  - `read_grade` returns `True`, `False` and `None` (no line, and the last line wins);
  - every `DEV_RUBRICS` key is a `CRITERIA` key and its rubric file exists;
  - write scenarios take the visible request as the question, review scenarios the oracle `semantic` list;
  - the module imports nothing from `inspect_ai`, checked with an `ast` scan.

  Verify: the file fails because `l2_rubrics` does not exist.
- [x] 2.4 Add L0 tests for `verdict_l2_grades` in `l1_checks.py` to `tests/unit/test_dev_runner_probe.py`: all criteria `C` passes; one `I` fails and names the criterion; an empty mapping fails as nothing graded. Verify: they fail against the current code, and `test_repo_conventions.py` will see a test for the new `verdict_*`.
- [x] 2.5 Add `is_subscription_model` cases to `tests/unit/test_support_matrix.py`. Use synthetic IDs, or read the registry's roles:
  - true for a dashed full ID and for a dated full ID;
  - false for a bare alias, a `claude-` without a digit, a provider-qualified OpenRouter ID and a catalog `anthropic/…` ID.

  Verify: they fail.
- [x] 2.6 Add runner tests to `tests/unit/test_dev_runner_probe.py`. Use in-process calls of `main(argv)` with `run_claude` and `claude_cli.call` monkeypatched, so there are no model calls. Cover:
  - the summary carries `model_requested`, the served `model` and `cli_version` from `init`;
  - the exit-status mapping and its precedence (design D7);
  - `RunnerFailure` is untested for a login failure and status 4 for a budget overrun, with messages unchanged;
  - an overage, API-key-source or no-rate-limit-event model stream gives untested, with the judge not called. Where an existing test drives a stream through these checks, give it a synthetic copy with an `allowed` rate-limit event; never edit a recorded fixture;
  - `model_env` (design D3) drops every `ANTHROPIC_*` variable (API key, auth token, base URL, model remaps) and every `CLAUDE_CODE_USE_*` switch, in ambient and isolated mode. It keeps `CLAUDE_EFFORT`, `CLAUDECODE`, `CLAUDE_CODE_OAUTH_TOKEN`, other `*_API_KEY` names and `PATH`, sets `CLAUDE_CONFIG_DIR` only when isolated, and does not mutate `os.environ`. A `main(argv)` test with `subprocess.run` monkeypatched asserts that the environment handed to the host is the stripped one;
  - `--judge` without `--isolated` exits 2 before staging;
  - `--judge` on a scenario without a rubric exits 2;
  - a dev-judge role failing `is_subscription_model` is refused before any call;
  - a judged summary carries the `l2` block, the label and `self_graded`;
  - a missing artifact gives "not judged" with no call;
  - the notional cap stops further calls;
  - `--rejudge` over `tmp_path` workspaces never calls `run_claude`, and the over-cap projection stops the batch;
  - `--summary-log` appends on the success and failure paths;
  - `--summarize` prints one row per scenario, exits non-zero unless all passed, and removes the log;
  - the `customize_override` scenario passes and fails on staged synthetic workspaces.

  Verify: the new tests fail.
- [x] 2.7 Add `matrix.py --smoke` tests to `tests/unit/test_support_matrix.py` (or a sibling test file). `--smoke` selects the roles' smoke model × the `core` tasks × 1 epoch. It is refused with `--models`, `--tier`, `--tasks`, `--core` or `--epochs`, and allowed with `--estimate-only` and `--yes`. With `confirm_spend` monkeypatched to decline, it returns 1 and `run_matrix` is never called. Verify: the tests fail.
- [x] 2.8 Add a smoke-task test to `tests/unit/test_dev_runner_probe.py` that reads `pyproject.toml` with `tomllib`. It asserts that `[tool.poe.tasks.smoke]`:
  - has `default_item_type = "cmd"` and `ignore_fail = "return_non_zero"`, and no `envfile`;
  - has steps that name the `core` scenarios, each with `--isolated` and `--max-budget-usd`, all appending to the same `--summary-log`;
  - ends with `--summarize` over that log.

  It also asserts that `smoke-inspect` keeps `envfile = ".env"`. Verify: the test fails against today's `smoke` task.

## 3. Shared pieces

- [x] 3.1 Add `anyio` as an explicit dev dependency with `uv add --dev anyio`. Verify: `pyproject.toml` and `uv.lock` change, and `uv tree --depth 1 | grep anyio` lists it at the top level.
- [x] 3.2 Implement `support.is_subscription_model()`: a `claude-` prefix, no `/`, and at least one digit. Do not add a `[[models]]` row. Verify: the tests from 2.5 pass.
- [x] 3.3 Create `harness/l2_rubrics.py` and move into it `RUBRICS`, `JUDGE_INSTRUCTIONS`, `CITATION_SCOPE`, `CITATION_SYNTHESIS` and `CRITERIA`. Add `JUDGE_SYSTEM`, `judge_prompt`, `read_grade` and `DEV_RUBRICS`. Make `skill_evals.py` import them, keep `skill_evals.CRITERIA` importable, and have `skill_evals.judge()` build its prompt with `judge_prompt`. Verify:
  - the tests from 2.3 and 1.3 pass;
  - `uv run python harness/eval_export.py --check` reports no drift;
  - `tests/unit/test_eval_projection.py` is green.

  Note: `skill_evals.py` imports only what it still uses (`CITATION_SCOPE`, `CITATION_SYNTHESIS`, `CRITERIA`, `judge_prompt`); `RUBRICS` and `JUDGE_INSTRUCTIONS` are no longer importable from it, since no caller read them there. `l2_rubrics.py` also carries `DevCriterion` and `question_for`, the question source design D6 names.
- [x] 3.4 Add `verdict_l2_grades(grades: dict[str, bool]) -> tuple[bool, str]` to `harness/l1_checks.py`. Verify: the tests from 2.4 and `tests/unit/test_repo_conventions.py` pass.

## 4. `harness/claude_cli.py`

- [x] 4.1 Implement the pure parts:
  - `build_command`, `child_env`, `check_auth_status` and `parse_stream` (reusing `routing.error_result_reason` and `host_login.login_remedy`);
  - the `SubscriptionUnavailable` exception;
  - the `JudgeCall` dataclass: text, served model, CLI version, effort, thinking tokens, notional cost, rate-limit window.

  Keep each function within complexity 12. Verify: the pure tests from 2.2 pass and `uv run ruff check harness/claude_cli.py` is clean.

  Notes: the allowlist also keeps the Windows process-start, home, config and temp variables (`SYSTEMROOT`, `COMSPEC`, `PATHEXT`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `TEMP`, `TMP`), the same categories as design D3's POSIX list, so the judge can start on a Windows host; none carries a credential. `parse_events` moved here from `claude_runner.py`, which re-exports it, so both readers are one function. `billing_problem` (checks 3 and 4) is public because the runner applies it to the model-under-test stream.
- [x] 4.2 Implement the async parts:
  - `call()`, using `anyio.open_process` with the prompt written to stdin;
  - `fail_after(timeout)`, with kill and reap in `finally`;
  - the module-level `CapacityLimiter(4)`;
  - the lazily created fixed working directory;
  - `preflight()`, which runs `claude auth status --json` with the child environment;
  - `judge_all()`, which runs the warm-up first and then fans out, stops on the first `SubscriptionUnavailable`, and enforces the notional cap and the batch projection.

  Verify: all of `tests/unit/test_claude_cli.py` passes, and `claude_cli.py` is not on the coverage `omit` list.

  Note: `judge_all` runs the preflight itself and returns a `JudgeRun` (grades in input order, cumulative notional, projection). The fan-out is a pool of at most four workers that take the next criterion only when free, so the cap and a stop reason are checked right before each call; the module-level limiter still bounds every child of the process.

## 5. `harness/claude_runner.py`, `harness/matrix.py`, `pyproject.toml`

- [x] 5.1 Replace `sys.exit(failure)` in `run_claude` with a typed `RunnerFailure(message, untested)`. Also:
  - add the exit-status constants and the pure mapping with its precedence;
  - apply checks 3 and 4 from design D5 to the model-under-test stream, including the absent-rate-limit-event rule;
  - start the host with the pure `model_env(os.environ, config)` from design D3 instead of `dict(os.environ, …)` or the inherited environment.

  Verify: the corresponding tests from 2.6 pass, and the existing host-failure tests still pass with unchanged messages.

  Notes, all in the direction of design D7's "untested is never FAIL": a model-run stream with a billing problem raises `RunnerFailure(untested=True)` with the reason prefixed "not a subscription result:"; the `RunnerFailure` carries the host's events so a kept workspace still holds them; a host that exceeds `--timeout` is a runner failure (4) instead of a traceback (1); `isolated_config`'s own refusals (no stored login, another run's refresh never arrived), which `sys.exit` with a message inside `routing.py`/`host_login.py`, are caught at the runner and reported untested (3) instead of exit 1; an unexpected crash prints its traceback and ends as a runner failure (4) with a summary-log line.
- [x] 5.2 Record `model_requested`, the served `model` (from `init`, checked against `modelUsage`) and `cli_version` in `summary()`. This fixes the alias-only record at `:468`. Verify: the summary tests pass.
- [x] 5.3 Add the `customize_override` scenario (`f00-clean-en`, `proposal-customize`, the Inspect request) and its branch in `verdict()` through `verdict_customize_override`. Verify: the scenario tests pass.

  Note: `verdict()` would have reached complexity 13 with the new branch, so the `ideate_scoped` and import branches moved into `ideate_verdict` and `import_verdict`, unchanged.
- [x] 5.4 Add `--judge`, which requires `--isolated` and a `DEV_RUBRICS` scenario and validates the dev-judge role with `is_subscription_model`. Also:
  - the judge runs inside the run's isolation context, after L1;
  - the summary gains the `l2` block, the "dev-runner L2, not comparable to matrix" label and the `self_graded` flag;
  - add `--max-notional` with a default of 5.00.

  Verify: the judge tests from 2.6 pass.

  Notes: the dev judge is `support.role_model(roles, "dev_judge", os.environ)`, so `DEV_JUDGE_MODEL` overrides it for one invocation like every other role, and the same `is_subscription_model` refusal applies to the override (usage error, exit 2, naming `[roles].dev_judge`). `--judge` together with `--rejudge` is a usage error. The judge grades whether or not L1 passed, as the matrix does; a missing artifact costs no call. The summary keys are `l2` (`criteria`, `judge_model`, `judge_served`, `effort`, `cli_version`, `thinking_tokens`, `notional_usd`, `rate_limit`), `l2_label`, `l2_verdict`, `self_graded`, plus `outcome` and `exit_status` on every summary.
- [x] 5.5 Add `--rejudge DIR [DIR …]` (its own `isolated_config("devjudge-config-")`, artifact selection through the L1 selection functions, projection printed after the warm-up), plus `--summary-log` and `--summarize` with a pure row function. Verify: the rejudge and summary tests from 2.6 pass.

  Notes: a re-grade reads the model under test's served ID from the kept `.devrun-events.jsonl` to set `self_graded`. Summary rows are keyed by scenario and, for re-grade lines, workspace. `--summarize` on an absent log exits 4 (nothing ran), never 0.
- [x] 5.6 Rewrite the module docstring:
  - the "No judge/L2 (use Inspect for that)" line at `:8` now says that dev-runner L2 exists, is labelled, and is not the source of record;
  - add usage lines for `--judge`, `--rejudge`, `--max-notional` and `--summarize`.

  Verify: by reading it, and `uv run python harness/claude_runner.py --help` shows the new flags.
- [x] 5.7 Add the selection-only `--smoke` flag to `harness/matrix.py`. Do not touch the estimate, `confirm_spend` or `record_spend`. Verify: the tests from 2.7 pass.

  Note: `--epochs` now defaults to `None` and resolves to `support.DEFAULT_EPOCHS` without `--smoke`, so an explicit `--epochs` beside `--smoke` can be refused. The smoke model honours `SMOKE_MODEL` through `support.role_model`.
- [x] 5.8 In `pyproject.toml`:
  - replace `smoke` with the sequence from design D8: `default_item_type = "cmd"`, because poethepoet otherwise reads each string as a reference to another task; `ignore_fail = "return_non_zero"`; `--max-budget-usd 2` on every runner step; no `envfile`;
  - add `smoke-inspect` (`python harness/matrix.py --smoke`, `envfile = ".env"`);
  - remove the parked `pyproject.toml` smoke entry from the model-ID guard's allowlist, which `track-model-currency` left for this change to clear.

  Verify:
  - the test from 2.8 passes;
  - `uv run poe -d smoke` (dry run) prints the four runner commands without running them; under the `ref` reading it would fail with an unknown-task error;
  - `uv run poe --help` lists both tasks;
  - `uv run poe smoke-inspect --estimate-only` prints an estimate for the registry's smoke model × core tasks × 1 epoch and makes no metered call;
  - the guard test passes without the parked entry.

  Done 2026-10-05: the dry run prints the four commands; `poe --help` lists `smoke` and `smoke-inspect`; `poe smoke-inspect --estimate-only` printed `openrouter/anthropic/claude-haiku-4.5` × `write_from_seed, import_messy, customize_override` × 1 epoch, estimated $1.08, and stopped (no metered call; the only network request was the free catalog read of the currency warning).
- [x] 5.9 Check that nothing depends on the runner's old exit status for runner failures. Verify: `grep -rn 'claude_runner' --include='*.py' --include='*.toml' --include='*.md' . | grep -v 'openspec/changes/archive'` shows no caller that reads its exit code, apart from the new smoke sequence.

  Done: in the tracked tree the runner is referenced by docs, its tests (in-process `main(argv)`), `poe dev` (passthrough) and the smoke sequence; no CI workflow calls it. Hits under `.claude/worktrees/` are other sessions' untracked worktrees, not this tree.

## 6. Documentation

- [x] 6.1 In `harness/README.md`:
  - **Dev-runs section.** Document `--judge`, `--rejudge`, `--max-notional`, `--summarize`, the exit-status table, the not-comparable label and `self_graded`. Add the quota caveats: the 5-hour and weekly limits are shared with interactive use; "$0" holds only while extra usage stays off; effort is pinned so an inherited `CLAUDE_EFFORT=xhigh` does not inflate usage; re-check `claude --help` after a host upgrade, because `--bare` must never be the default path; the fix for a dead login is `/login`, never an API key. State that the runner strips `ANTHROPIC_*` and `CLAUDE_CODE_USE_*` from every model run, so a remapped alias resolves to the host default, and that a stream with no rate-limit report reads untested.
  - **Citation-scenario paragraph.** The dev runner now grades the same two criteria with `--judge`.
  - **Probe paragraph.** Add the served model, the CLI version and the L2 block.
  - **The closing "no L2 judging" sentence.** Replace it.
  - **The path table's L2 row**, added by `steer-subscription-first`. It splits into "L2 iteration: `poe dev <scenario> --isolated --judge`" (subscription) and "L2 of record: `poe matrix …`" (metered, cost-gated).
  - **The path table's smoke row**, which steer's D7 assigns here. "The Inspect wiring itself changed" now names `poe smoke-inspect` (metered, cost-gated). Add a row "Quick check of the core scenarios after a change: `poe smoke`" (subscription), or fold `poe smoke` into the first row's quick-check wording if steer kept that row's "quick check after a change".
  - **The path table's re-grade row.** It names `poe dev <scenario> --rejudge <dir>…` as the means, and keeps "subscription — never metered".
  - **The model-support block's `poe smoke` line.** It becomes the subscription smoke, plus a `poe smoke-inspect` line, metered, gated, model from the registry.
  - **The `ideate_scoped` paragraph's "a one-shot `claude -p` cannot hold the dialogue"**, which steer's D7 assigns here. Review it beside the new `--judge` text and keep it: `--judge` grades a finished single-turn run, and the dev runner stays single-turn (design Non-Goal "Multi-turn dev-runner scenarios"), so the sentence stays true.

  Verify:
  - `grep -n 'no L2 judging' harness/README.md` returns nothing;
  - `grep -n 'cannot hold the dialogue' harness/README.md` still matches the `ideate_scoped` paragraph;
  - `grep -n 'smoke-inspect' harness/README.md` matches both the table and the model-support block;
  - no line of the table pairs `` `poe smoke` `` with "metered".

  Note: the paragraph under the path table said the subscription runners pass the launching shell's environment to `claude -p`; it now says the dev runner strips the billing variables and allowlists its judge, and keeps the warning for the routing rig and the audit preflight, which still inherit the environment (design Non-Goal). The Inspect section's re-grade sentence names `--rejudge`. `poe smoke` is folded into the first row's quick-check wording, which steer kept.
- [x] 6.2 In the `AGENTS.md` Commands block, rewrite the `poe smoke` line to the subscription smoke and add the `poe smoke-inspect` line ("metered, cost-gated, only when the Inspect wiring changed"). Verify: `grep -n 'smoke' AGENTS.md` shows both lines and no "metered smoke" wording for `poe smoke`.

## 7. Verification

- [x] 7.1 Run `uv run poe test`. Verify: green, which covers pytest, ruff with complexity 12, the generated-copy drift check and conform.

  Done 2026-10-05: 2321 passed, ruff clean, generated copies in sync, all 11 skills conform.
- [x] 7.2 Run `uv run poe cov`. Verify:
  - the floor of at least 78% holds;
  - `harness/claude_cli.py`, `harness/l2_rubrics.py` and `harness/claude_runner.py` appear in the report;
  - the runner's coverage is above the 65% measured before this change, with `main` covered;
  - `harness/skill_evals.py` is the only entry left on the omit list.

  Done 2026-10-05: total 86.74% (floor 78%); `claude_cli.py` 98%, `l2_rubrics.py` 100%, `claude_runner.py` 86% (434 statements, 60 missed; was 65%), `main` and the dispatch covered (the host subprocess is faked in-process); the uncovered runner lines are verdict branches of scenarios the new tests do not drive and a few error paths.
- [x] 7.3 Run `uv run poe specs` and `openspec validate add-dev-runner-judge --strict`. Verify: both pass.

## 8. Live subscription checks (no money, plan quota only)

- [x] 8.1 Run one judged dev run: `uv run poe dev write_from_seed --isolated --judge --keep --model haiku`. Expected notional cost is about $0.3–1 for the model run plus about $0.11 for two judge calls. Verify:
  - the summary carries the served full model ID, `cli_version`, two L2 grades, the judge's served ID equal to the roles' `dev_judge`, its effort, thinking tokens, notional cost and the label;
  - `jq` over the kept `.devrun-events.jsonl` shows `apiKeySource: none` and at least one `rate_limit_event`. A long agent session with none would make the absent-event rule (design D5) mark every dev run untested; if that happens, stop and record it rather than relaxing the rule.

  Done 2026-10-05, run with `--max-budget-usd 2 --summary-log <scratch>` added (a safety cap and a machine-readable record). The first attempt's haiku run stopped to ask about the degree level and wrote nothing: L1 FAIL, both criteria "not judged: no artifact", no judge call — the no-artifact path, live. The second attempt drafted, and both criteria were graded (figures in `measurement.md`). Both kept streams show `apiKeySource: none` and one `rate_limit_event` each, so the absent-event rule holds on full sessions.
- [x] 8.2 Re-grade the kept workspace from 8.1 with `--rejudge`. Launch the command from an environment carrying obvious placeholders: `ANTHROPIC_API_KEY=placeholder-not-a-key`, `CLAUDE_EFFORT=max`, `OPENROUTER_API_KEY=placeholder-not-a-key`. No model under test runs, so no child receives them except through the allowlist under test. Verify: both criteria are graded, the recorded effort is the pinned one, not `max`, and no run is reported as API-billed.

  Done 2026-10-05 over the second 8.1 workspace: both criteria graded (the same grades as in 8.1), effort `medium`, `apiKeySource: none` on both calls (an API-billed call would have read untested), projection printed after the warm-up.
- [x] 8.3 Run `uv run poe smoke` once, launched with `ANTHROPIC_API_KEY=placeholder-not-a-key` in its environment. If the billing strip failed, the host would try that invalid key and fail without spending, so the placeholder is a safe live check of design D3 for the model run. Verify:
  - all three scenarios run even if one fails;
  - the closing summary lists each scenario's outcome, and the exit status matches the rows;
  - no row is untested for an API-key source;
  - each step's notional cost stays well below the `--max-budget-usd 2` cap. A step at or near the cap is recorded in 8.4 with a proposed value.

  Done 2026-10-05: three steps ran past the first FAIL; closing summary FAIL / FAIL / PASS, exit 1; no untested row; every step under 10% of its cap.
- [x] 8.4 Record the figures from 8.1–8.3 in `openspec/changes/add-dev-runner-judge/measurement.md`: CLI version, served IDs, effort, thinking tokens, notional cost per judge call and per smoke step against the cap, and rate-limit status and utilization. Note whether the per-call cost confirms the ~$0.055 assumption; if not, propose a registry effort edit (an open question in design.md). Verify: the file exists, and it holds no credential value, email or organization.

  Done: the per-call cost ($0.008–0.022) is below the assumption, so no registry effort edit is proposed; the README's notional figures were updated from the plan's $0.11 / $2.6 to the measured ones.

## 9. Close

- [ ] 9.1 Archive through the `openspec-archive-change` skill, which syncs the testing-harness deltas. Then run `python3 scripts/sync_shared.py --check` and `uv run poe test`. Verify: the change sits under `openspec/changes/archive/` and both commands are green.
- [ ] 9.2 Commit the completed change, off `main` if it is not yet ready to go live, with the attribution trailer. Do not push. Verify: `/usr/bin/git status` is clean for the change's files, and `/usr/bin/git log -1` shows the commit.
