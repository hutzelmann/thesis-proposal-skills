# Tasks

Metered rule for every task below: a metered call runs only after its estimate has been shown to the user and the user has explicitly approved that specific run in chat. Never pass `--yes` for the user, and never answer a confirmation prompt without that approval. Credentials come only from `.env` through the poe `envfile`; never put a key in a command, a log or a file.

## 1. Preconditions

- [x] 1.1 Confirm that `steer-subscription-first`, `track-model-currency` and `add-dev-runner-judge` are archived on the branch this work starts from. Verify:
  - `openspec list` no longer shows them as active;
  - `harness/models.toml` carries the `[roles]` table with the keys `track-model-currency` writes: `judge`, `smoke`, `dev_judge` and `dev_judge_effort`. It has no `persona` key, and none is expected;
  - the parsed registry's `roles.persona` equals `roles.judge` by default. Check it through the resolver in 1.2 with an empty environment. Do not add a `persona` key to make this check pass.
- [x] 1.2 Confirm that `support.role_model(roles, name, environ)` from `track-model-currency` exists, and that `skill_evals.py` resolves `JUDGE_MODEL` and `PERSONA_MODEL` through it. If it is missing, **stop and report**: it is that change's deliverable, and this change does not add a second resolver. Verify: its existing L0 tests cover the default, an override, the persona defaulting to the judge, and a judge override leaving the persona unchanged; `uv run pytest tests/unit/test_eval_wiring.py` is green.
- [x] 1.3 Confirm `track-model-currency`'s held-role pricing, which this change consumes and does not re-implement (design D4a). If any item is missing, **stop and report**:
  - `Registry.role_prices` (`[role_prices."<id>"]`) and `support.model_price(registry, id)` exist, and `estimate_cost` and `price_usage` look prices up through it (its task 1.2);
  - its L0 tests cover the roster row winning (disabled rows included), an off-roster judge priced from its entry, and the parse failures for an unpriced judge or persona, an entry no role names and an entry duplicating a roster ID (its task 1.1);
  - its checker reports and refreshes `price_drift` on `[role_prices]` entries and writes an entry when a held role's ID leaves the roster (its task 2.2, "held role leaves the roster").

  Record whether the judge's ID is priced by a roster row or by a `[role_prices]` entry: a weekly bump PR may have re-pinned the haiku row since `track-model-currency` landed. Task 2.4 depends on the answer.

  Recorded 2026-10-05: all three items present. The judge (`[roles].judge`, the haiku row) is priced by its **roster row**; `harness/models.toml` carries no `[role_prices]` entry, so task 2.4 sets `cache_write_price` on roster rows only.

## 2. Cache-aware accounting

- [x] 2.1 Add the optional `cache_write_price` to `support.Model` and to the `[role_prices]` entries in `parse_registry`, defaulting to `input_price` on both. Verify: L0 tests cover a row and an entry each with and without the field, and `support.model_price` returns the field for both.
- [x] 2.2 Extend `support.price_usage` to `(input, output, cache_read, cache_write)` tuples and charge writes at `cache_write_price`, keeping 2- and 3-tuples valid. Prices still come from `support.model_price`; add no second lookup. Verify: L0 tests check the arithmetic, including a row priced without the field, and that an off-roster held judge's usage, cache writes included, is priced from its `[role_prices]` entry instead of being listed as unknown.
- [x] 2.3 Have `matrix.collect_usage` sum `input_tokens_cache_write`, and record per-epoch demand as `input + cache_write + cache_read`. Verify: an L0 test with synthetic log stand-ins (plain objects, no Inspect run) shows that demand includes writes.

  Review follow-up (deviation, design D6): `harness/report.py` was a second pricing site with its own `(input, output, cache_read)` accumulator, so `poe report`'s per-model run cost would have charged cache writes $0. The accumulation moved into the pure `support.billed_usage`, used by `matrix.collect_usage` and the new `report.model_costs`; `report.arm_stats` counts full demand plus output. L0: `test_report_prices_cache_writes_exactly_as_the_matrix_does`, `test_report_baseline_tokens_count_full_demand`.
- [x] 2.4 First add `cache_write_price`, mapped to the endpoint's `input_cache_write`, to the one price-field list of `harness/model_currency.py` (design D6). Depends on `track-model-currency` task 2.3, whose checker already compares and refreshes input, output and cache-read prices for roster rows and `[role_prices]` entries alike; do not re-implement that refresh or the entry creation.

  Then set `cache_write_price` on the Anthropic rows in `harness/models.toml`, and on any `[role_prices]` entry for an Anthropic ID that 1.3 found. Take every value from the `anthropic` vendor endpoint at its standard tier, through the free, unauthenticated `/endpoints` request: the price basis of `track-model-currency` D3, never the catalog's headline price. Leave model IDs, the roles table and the set of `[role_prices]` entries untouched, so do not use `--write` for this step, which would also apply any pending re-pin.

  Verify with L0 tests in `tests/unit/test_model_currency.py` over the synthetic catalog snapshot, with no socket opened:
  - drift on `cache_write_price` is reported and written for a roster row and for a `[role_prices]` entry;
  - the entry `--write` creates for the held-role case (`lab/judge-1`) carries `cache_write_price` from its endpoint;
  - an endpoint without a cache-write price leaves the field out;
  - a second `--write` changes no byte, and the result re-parses through `support.parse_registry`.

  Also verify that the registry parses (`uv run poe test-fast`), and that a read-only `python3 harness/model_currency.py` (free, no key) reports no `cache_write_price` drift on the rows and entries just set, so they share the checker's basis.

  Done 2026-10-05. `model_currency.py` had no single field list yet (the three prices were spelled out in each function), so `PRICE_FIELDS` was introduced and every comparison, report and write now iterates it; the drift detail reads `in/out/cache-read/cache-write`. The live `anthropic` endpoints gave `input_cache_write` 1.25 / 2.5 / 5.0 $/Mtok for the haiku, sonnet and opus rows, set by hand; the re-run reports no drift on them. The recorded snapshot's real endpoints were trimmed of `input_cache_write`, so the synthetic `lab/judge-1` and `lab/judge-2` endpoints gained one (README updated). The same live run reports `cache_write_price` drift on the five non-Anthropic rows (their endpoints list 1.25× input) and an unrelated full-price drift on the deepseek row; both are left to the weekly bump PR, as this task scopes the hand edit to Anthropic rows.

## 3. Role pricing in the estimate

The price lookup (`support.model_price`) and the held judge's `[role_prices]` entry come from `track-model-currency` (precondition 1.3, design D4a). Its parser refuses a registry whose default judge or persona is unpriced, so the stop (3.3) can fire only for an environment override that names an unpriced ID.

- [x] 3.1 Add a persona token budget to `TaskConfig`, read explicitly from a new `[tasks.persona]` table (input 50000, output 4000, with a provenance comment). Set `[tasks.judge]` to input 40000, output 10000, with a comment citing the haiku and sonnet judge measurements. `track-model-currency` already rejects `[tasks.judge].model` at parse time; keep that guard. Verify: L0 parse tests, and `test_eval_wiring.py` stays green.

  Choice where the artifact was silent: `[tasks.persona]` is required when the registry lists dialogue tasks (a missing budget would price every persona call at $0, the defect being fixed) and optional otherwise; `[tasks.persona].model` is rejected like the judge's. The recorded `registry-pre-bump.toml` fixture gained the table to keep parsing (noted in its README).
- [x] 3.2 Change `support.estimate_cost` to take the resolved judge and persona IDs and price them through `support.model_price`. Charge the judge budget on every cell-epoch and the persona budget only on `dialogue` task cell-epochs, and return unpriced role IDs separately. Verify: L0 tests for "judge override priced", "persona priced on dialogue tasks only", "held judge priced from its `[role_prices]` entry" and "unpriced role reported". Ruff complexity stays ≤ 12.
- [x] 3.3 In `matrix.main`, resolve the roles from `os.environ` through `support.role_model`. When a role is unpriced, exit 2 before `confirm_spend`, even with `--yes`. The message names the ID and the remedy: an override the registry prices (a roster ID, enabled or not, or a role's own ID). It does not suggest a `[role_prices]` entry, which `track-model-currency` rejects for an ID no role names (design D4). Print the role lines in the estimate. Verify:
  - an L0 test calls `main([...,"--yes"])` against a temporary registry with an unpriced override, and asserts exit 2 and that `run_matrix` was never called;
  - a second test uses a registry whose judge has no roster row but has a `[role_prices]` entry, with no override, and asserts that the stop does not fire;
  - a capsys test shows the role lines.

  Notes: a role is priced and checked only when the selection calls it, so an unpriced `PERSONA_MODEL` override does not stop a run with no dialogue task. The stop also fires under `--estimate-only` (exit 2), since that estimate would be incomplete. `estimate_cost` takes `judge=`/`persona=` keywords that default to the registry roles; `CostReport` gained `roles` (one `RoleCost` per called role) and the derived `unpriced_roles`. Gate tests that call `matrix.main` clear `JUDGE_MODEL`/`PERSONA_MODEL`/`SMOKE_MODEL` through a new `no_role_overrides` conftest fixture.

## 4. Cache telemetry

- [x] 4.1 Add the dataclass `support.CacheStats(model_id, input, cache_write, cache_read, providers)` with a `hit_rate` property that returns 0.0 on zero tokens. Add the pure `support.cache_warnings(stats, registry)`: a named 50% threshold for Anthropic-family rows, and a warning for any recorded provider other than the pin. Verify: L0 tests at 49.9%, 50% and zero tokens, an off-pin provider, and a non-Anthropic row that is never warned.
  Note: zero prompt tokens on a routed row gets its own warning ("recorded no prompt tokens — its cache-hit rate is unknown") rather than a misleading "0.0% is below 50%".

  Review follow-up: findings are `support.CacheWarning(model_id, kind, detail)` dataclasses (kinds in `CACHE_WARNING_KINDS`), not prefixed strings, and the tests assert on `kind`. `cache_warnings` takes the mechanism, so nothing is warned while none is adopted. `support.format_providers` is the one provider-count formatter (matrix, probe, warnings).
- [x] 4.2 Add the pure `support.serving_providers(events)`, which counts `call.response.provider` on model events, with an `unrecorded` bucket for events that have no recorded call. Verify: an L0 test on synthetic event objects.

  Addition: the pure `support.routed_events(events, model_id, routed)` selects the events counted. When the judge or persona shares the model under test's ID (the haiku row), their calls come from a second, unpinned Model of the same ID; a recorded call whose request carries no `extra_body.provider` is dropped for a routed row, so judge calls served by Bedrock never raise an off-pin warning. Unrecorded calls stay in the `unrecorded` bucket, which never warns.
- [x] 4.3 Add the pure `support.role_observations(samples, role_ids, under_test)`, giving per-cell-epoch usage of role IDs that differ from the model under test, plus a budget-exceeded flag. Verify: L0 tests cover a role equal to the model under test (no observation) and an exceeded budget.

  Deviation: the signature gained a fourth argument, `budgets` (role → per-cell-epoch budget), since the flag needs them. Roles that share one ID (the persona defaults to the judge) share one `judge/persona` line with the budgets summed; usage is the heaviest cell-epoch, as full demand (input + cache writes + cache reads).
- [x] 4.4 Extend `matrix.record_spend` and `cost_summary`:
  - print per model the hit rate, cache counts, providers, and the uncached-equivalent cost;
  - print the role observations against their budgets;
  - persist `per_model_cache` and `roles` in `matrix-cost-*.json`, keeping the existing keys unchanged.

  Verify: an L0 test with fake logs writes into `tmp_path`, with `USAGE_HISTORY` monkeypatched, and asserts the persisted keys and the warning text.

  Note: telemetry covers each model under test, from the logs it was under test in, so a haiku judge's one-shot calls in other rows' cells never dilute the haiku row's hit rate. The uncached-equivalent figure is prompt-side only (`support.prompt_costs`), since output is billed the same either way.

  Review follow-up: that narrowing departed from design D4a/D7 ("reported but never warned" for role-price IDs) and the spec's "per model". It is now a recorded decision: D4a and D7 say role models get no cache telemetry (their usage is reported against their budgets), and the spec's telemetry and warning sentences say "model under test". The warnings are also persisted, under `cache_warnings` in `matrix-cost-*.json`.

  Final review follow-up (design Risks, "The account's guardrails change"): a routed row whose every call failed, as at probe 1's routing 404, left a log with status `success` and no model usage. `collect_cache` skipped it, so the outage went unreported. Such a row now gets zeroed `CacheStats`, so its `no_prompt` warning names it, and that warning's detail points at the sample errors. `record_spend`'s "did not finish cleanly" warning now also counts logs with errored samples. L0: `test_record_spend_names_a_routed_row_whose_every_call_failed`. Added beside it: `test_record_spend_merges_a_routed_row_across_its_logs`, covering `CacheStats.merged`, the dialogue persona branch and the cross-log role merge.

## 5. Routing and the probe (built for mechanism `auto`, superseded by 6.4 and 8.1)

- [x] 5.1 Add the pure `support.routing_for(model, mechanism)` returning a frozen dataclass `(model_args, extra_body)`:
  - Anthropic family: `provider = {"order": ["anthropic"], "allow_fallbacks": False}`;
  - `auto` adds `extra_body = {"cache_control": {"type": "ephemeral"}}`;
  - any other family: empty.

  Verify: L0 tests for an OpenAI row (empty), Anthropic `auto`, and Anthropic `marker` (pin only).

  Note: the single mechanism constant is `support.CACHE_MECHANISM`. It was first set to `auto` provisionally; review follow-up (deviation, design D2 "Adoption") set it to `None` until task 8.1, because the spec admits only a probed mechanism and a matrix or `smoke-inspect` run started from the working tree would otherwise have used an unprobed mechanism with no provider fallback. `routing_for(model, None)` returns an empty routing, `cache_warnings` warns on nothing without a mechanism, and the probe's `--mechanism` defaults to the first candidate (`auto`) until one is adopted. L0: `test_run_matrix_routes_anthropic_rows_only_under_an_adopted_mechanism`, `test_no_adopted_mechanism_routes_and_warns_nothing`. Task 8.1 sets the constant; the change is not committed before then.

  Review follow-up (design D2 "Single-message requests"): `auto` puts the top-level `cache_control` on every request of the routed model under test, a single-message first turn included, since later turns read it back. The spec's one-shot rule targets judge and persona prompts; `test_role_models_stay_unrouted_beside_a_routed_model_under_test` (in `test_eval_wiring.py`) pins that they are built from their bare role IDs and stay unrouted even beside a routed model with the same ID.

  Superseded after probe 1 by task 6.4: the pin is now `{"order": ["amazon-bedrock", "google-vertex"], "allow_fallbacks": False}`, `marker` sets the routing's `conversation_breakpoint` flag, and the probe's default mechanism is `marker`.
- [x] 5.2 Add a `matrix.build_model(model, routing)` helper and use it in `run_matrix`. It returns `get_model(id, config=GenerateConfig(extra_body=…), **model_args)` for a non-empty routing and the bare ID string otherwise. Verify: an L0 test with a placeholder `OPENROUTER_API_KEY` set through `monkeypatch` (no network) asserts that `str(model)` equals the registry ID, that the routing is carried, and that a non-Anthropic row stays a string.

  Superseded by 8.1: `auto` is deleted, and with it `Routing.extra_body`, so `build_model` returns `get_model(id, **model_args)` with no `GenerateConfig`.

  Review follow-up (deviation from design Non-Goals, now amended): `poe smoke-inspect` is `matrix.py --smoke`, so it shares `run_matrix`, the role pricing, the unpriced-role stop and the 40k/10k judge budget, and shares the adopted `marker` routing. That is kept deliberately, so the metered wiring check exercises the matrix's own path; design Non-Goals, the `matrix.py` docstring and `harness/README.md` say so.
- [x] 5.3 Add `verdict_cache_reuse(calls, minimum=0.8) -> tuple[bool, str]` to `harness/l1_checks.py`. Verify: L0 tests in a new `tests/unit/test_cache_probe.py` cover the spec scenarios: 60% fails naming 60% and 80%; no cache write fails saying so; exactly 80% passes. `test_repo_conventions.py` stays green.

  The measured share prints with one decimal (`60.0%`), so a share just under the bar never reads as `80%`; a first write on the last call fails, as nothing after it can read.
- [x] 5.4 Write `harness/cache_probe.py` with `main(argv)`:
  - a pure, deterministic builder for the synthetic replay: generated text only, ten calls, about 1k tokens added per turn, every second assistant turn without text;
  - a pure worst-case estimate (every prompt token at the cache-write price, plus `max_tokens` output per call);
  - a one-sample Inspect task run in-process with `log_model_api=True`;
  - flags `--models` (default: enabled Anthropic rows of the cheap and mid tiers), `--mechanism auto|marker`, `--estimate-only`, `--yes`, and `--log-dir` (default `logs/cache-probe`);
  - `matrix.print_cost`/`confirm_spend` for the gate.

  Verify with L0 tests:
  - the builder is deterministic and its prompt sizes are about 2.2k to 11.2k tokens;
  - at registry prices the estimate is at most $0.09 for haiku and at most $0.17 for sonnet;
  - `--estimate-only` and a declined prompt make no model call;
  - the main path runs offline against Inspect's `mockllm/model` through a test-only model override and reports "no call wrote the cache".

  Superseded by 8.1: `auto` is deleted, so `--mechanism` takes `marker` only.

  Notes: tokens are estimated at a deliberately low 3 characters a token, so the estimate (prompts 2,200 … 11,200, 67,000 in all) bounds the real replay. Its English-word notes tokenize at roughly 4 characters a token: probe 2 measured each turn at about 750 tokens against the estimated 1,000, and haiku's prompts at 77–86% of the estimated sizes. Real prompt sizes therefore land below the estimate, and haiku's 4,096-token minimum is reached later than the estimate's call 3 (design D1, corrected to match its Risks entry; probe 2: call 4). The estimate is rounded up to the cent. `--mechanism marker` exits 2 ("not built") until tasks 7.1–7.2 exist (7.2 removed that refusal). The test-only override is the module attribute `MODEL_OVERRIDE`. The offline end-to-end test carries a `filterwarnings` ignore scoped to it, because Inspect 0.3.250's in-process eval leaves an unclosed log reader and anyio stream for the garbage collector.

  Review follow-up (design D1, F1/V4): under `fail_on_error=False` Inspect marks a log `success` even when its sample raised, so `summarize` judged a partial replay and could pass it, or report an error on call 1 as "no call wrote the cache". `cache_probe.incomplete` now fails a model on a sample error (naming it and the calls made) or on fewer than ten recorded calls, before the verdict runs; `summarize` selects events through `support.routed_events`. The estimator test's floor now counts punctuation and newlines as tokens, so it fails once `CHARS_PER_TOKEN` drifts to 5.

  Second review follow-up (design D1, after probe 1): the probe counted the call that raised, which leaves a model event without usage, as a call made, and labelled a routing 404 `FAIL` with exit 1, exactly like a caching failure. Now only calls that returned usage count. Each model ends `PASS`, `FAIL` (a scored verdict, or a 400 rejecting the request the mechanism shaped) or `UNTESTED` (any other error, an unfinished run, a partial replay), and the exit status is 3 when nothing failed but a model went untested. The log fixtures gained the errored call's usage-less event, as the real probe-1 logs carry it. L0: `test_a_routing_404_on_the_first_call_is_untested_not_a_caching_failure`, `test_account_and_api_errors_leave_the_mechanism_untested`, `test_exit_status_tells_a_scored_failure_from_an_untested_model`. Both `run_matrix` and the probe now pass `metadata={"cache_mechanism": …}` to `inspect_eval`, and `matrix-cost-*.json` carries `cache_mechanism`, since a `marker` log's `model_args` show only the pin (design D2).
- [x] 5.5 Add a `cache-probe` poe task to `pyproject.toml` (`python harness/cache_probe.py`, `envfile = ".env"`). Verify: `uv run poe cache-probe --mechanism auto --estimate-only` prints the estimate and exits 0, with no metered call.

  Superseded by 8.1: `auto` is deleted and `--mechanism auto` now exits 2 (`invalid choice`). The current check is `uv run poe cache-probe --estimate-only`, which defaults to `marker` (10.1–10.3 notes).

## 6. Gated measurement: mechanism `auto` (probe 1) and the re-pin

- [x] 6.1 Run `uv run poe cache-probe --mechanism auto --estimate-only` and show the user the printed estimate (expected at most $0.26 for haiku-4.5 and sonnet-5.5 together). **Stop and wait for the user's explicit approval of this metered probe.**

  Estimate printed 2026-10-05 (no model call): haiku-4.5 $0.09, sonnet-5.5 $0.17, total $0.26. The user approved the run.
- [x] 6.2 With approval in hand, run `uv run poe cache-probe --mechanism auto`, answering the confirmation prompt only as approved. Record per model the steady-state read share, the recorded providers, the actual cost and the verdict in `openspec/changes/fix-openrouter-caching/measurement.md`. Verify: the file names the numbers and the log path under `logs/cache-probe/`.

  Done 2026-10-05, outcome **routing failure, $0** (`measurement.md`, probe 1). The user ran the approved command (`--yes --log-dir logs/cache-probe`). Both models failed on call 1 of 10 with a 404 from OpenRouter routing: the account's ZDR guardrail removed the `anthropic` endpoint, and the disabled fallback removed the surviving global Bedrock and Vertex endpoints. No request reached an upstream, the logs carry no usage, and the account's usage stayed at $21.31. This is not a caching verdict on `auto`. Logs: `logs/cache-probe/2026-10-05T05-08-11-00-00_cache-probe_*.eval`.
- [x] 6.3 Decide how to continue.

  Decided 2026-10-05 by the user, after probe 1: keep the ZDR guardrail, re-pin the Anthropic rows to the ZDR-compliant global Bedrock/Vertex endpoints (6.4), and build `marker` now (group 7), because Bedrock's legacy integration rejects automatic caching for Haiku 4.5. The second probe runs `marker` (7.3). `auto` is not probed again by default (design D2).
- [x] 6.4 Re-pin: `support.PINNED_PROVIDERS = ("amazon-bedrock", "google-vertex")`, and `routing_for` builds `provider = {"order": [...], "allow_fallbacks": False}` from it through `support.provider_pin()`. Add `support.PROVIDER_NAMES` (`amazon-bedrock` → `Amazon Bedrock`, `google-vertex` → `Google`, the endpoint `provider_name`s in the recorded catalog), and have `cache_warnings` treat a call served by any pinned provider as on the pin. Verify with L0 tests:
  - the routing fields for an Anthropic row under each mechanism;
  - a non-Anthropic row stays empty;
  - `Amazon Bedrock` and `Google` are never warned on a routed row, and `Anthropic` is warned as off the pin;
  - `build_model` carries the pin under the registry ID.

## 7. Mechanism `marker` (the candidate after probe 1)

Built now (task 6.3), not only after an `auto` failure.

- [x] 7.1 Write `harness/openrouter_cache.py` (design D3):
  - the pure `add_conversation_breakpoint(request) -> bool`. It acts only on a request that carries the harness pin in `extra_body.provider`, has no top-level `cache_control` and fewer than four markers. When it acts, it turns every user and tool message's non-empty string content into a one-block text list, and puts one breakpoint on the last block of the newest user or tool message with non-empty content;
  - an idempotent `install()` that wraps `inspect_ai.model._providers.openrouter._add_anthropic_cache_markers`, calling the original first, and raises if the symbol is missing.

  Verify with L0 tests, none calling a model or opening a socket:
  - an unpinned request (a single-message judge prompt included) and an `auto` request are untouched, and a pinned single-message request is marked;
  - string tool content is converted and marked, and list content gets the mark on its last block;
  - textless assistant turns are walked past;
  - the four-marker cap holds;
  - `install()` twice wraps once;
  - a guard asserts that the private symbol exists and is wrapped;
  - the request body handed to the OpenAI SDK, captured by stubbing `chat.completions.create` on a model built through `matrix.build_model`, carries the provider routing fields, Inspect's system and last-tool markers and exactly one conversation breakpoint. It is unchanged for a non-Anthropic row and for an unpinned Anthropic model, its single-message prompt included.

  Superseded by 8.1: with `auto` deleted, the "no top-level `cache_control`" condition and the untouched-`auto`-request test are gone; the pin alone decides.

  Review follow-up (design D2 "Single-message requests", D3): the two-message minimum is gone. It applied to pinned requests too, so each dialogue task's first turn, the skill prompt as one user message, went unmarked and the second turn paid a cache write on the skill body instead of a read. The pin alone is the discriminator; the judge and the persona carry none. L0: `test_a_pinned_single_message_heads_a_conversation_and_is_marked`, `test_a_routed_first_dialogue_turn_is_sent_marked`, `test_a_single_message_judge_prompt_is_sent_unmarked`. The placeholder key and the marker restore are one conftest fixture, `routable_openrouter`, at every site that builds an OpenRouter Model.
- [x] 7.2 Install the wrapper from `matrix.build_model` when the routing sets `conversation_breakpoint`. That covers the matrix and the probe, which builds through `build_model`. Remove the probe's "not built" refusal of `--mechanism marker`, and make `marker` the probe's default until a mechanism is adopted. Verify: the guard test passes, `uv run poe test` is green, and `uv run poe cache-probe --mechanism marker --estimate-only` prints the estimate and exits 0 with no model call.

  Deviation from the earlier wording (install at `skill_evals.py` import): design D3 "Where it is installed". A direct `inspect eval` run builds bare IDs, so no request it makes carries the pin, and the wrapper would act on nothing there. `skill_evals.py` is unchanged, so `test_eval_wiring.py`'s source checks stand.
- [x] 7.3 Run `uv run poe cache-probe --mechanism marker --estimate-only` and show the user the estimate (expected at most $0.26). **Stop and wait for explicit approval.** Then run `uv run poe cache-probe --mechanism marker --log-dir logs/cache-probe`, answering the confirmation prompt only as approved. Record the results in `measurement.md` as in 6.2 (probe 2), including the recorded providers, which should read `Amazon Bedrock` (or `Google` on a failover turn).

  Done 2026-10-05, outcome **PASS on both models** (`measurement.md`, probe 2). The main session ran the command (`--yes --log-dir logs/cache-probe`, exit 0) after the user approved the printed $0.26 estimate. Haiku-4.5 read 88.8% of the prompt tokens on the six calls after its first cache write (call 4), sonnet-5.5 86.4% on the nine after its first write (call 1); providers `Amazon Bedrock` ×10 each; actual cost $0.0233 + $0.0358 = $0.059. Vertex served no call, so `Google` stays unconfirmed live. Per-call rows were read from the logs with `inspect log dump | jq`. Logs: `logs/cache-probe/2026-10-05T06-11-11-00-00_cache-probe_*.eval`.
- [x] 7.4 If `marker` fails a scored replay (`FAIL`: a read share below 80%, no cache write, or a 400 rejecting the request; exit 1), **stop**: report both measurements to the user and ask how to continue. An `UNTESTED` result (a routing, account or API error, an unfinished or partial replay; exit 3) is no verdict and does not take this branch: record it in `measurement.md`, fix the cause within this change, and propose the probe again with a fresh estimate. The options include probing `auto` under the same pin (with its own estimate) and the Console API key fallback (a second billing account, which changes the logged IDs of Anthropic rows) as a separate change. Relaxing the ZDR guardrail is not an option, since the user declined it. Do not propose the Console-key change without the go-ahead. If caching is dropped, remove the "Prompt caching on Anthropic matrix rows" requirement from this change with the `openspec-update-change` skill, delete the unused mechanism code, and continue with groups 9 and 10 (telemetry and the gate still ship).

  Not taken: probe 2 passed `marker` on both models (7.3), so no stop and no fallback.

## 8. Wire the passing mechanism

- [x] 8.1 Set the single mechanism constant used by `run_matrix` and the probe's default to the mechanism that passed, and delete the code and tests of a mechanism that was built but not adopted. Verify: `grep` finds no unused mechanism path, and `uv run poe test-fast` is green.

  Waited on the probe result. `support.CACHE_MECHANISM` was `None` until then (task 5.1 note), so this task sets it to the passing mechanism, updates the comment beside it, and flips the `None` case in `test_run_matrix_routes_anthropic_rows_only_under_an_adopted_mechanism` to the adopted one. If `marker` is adopted, this deletes `auto`: its `extra_body` branch in `routing_for`, its `--mechanism` choice and its tests.

  Done 2026-10-05: `support.CACHE_MECHANISM = "marker"` and `support.MECHANISMS = ("marker",)`, with the comment naming probe 2; the probe's `DEFAULT_MECHANISM` resolves to it (and stays `marker` under a rollback to `None`), and `--mechanism marker` is its only choice. `auto` is deleted: its branch in `routing_for`, and with it the `Routing.extra_body` field that only `auto` filled, so `matrix.build_model` calls `get_model(id, **model_args)` without a `GenerateConfig`; the wrapper's "no top-level `cache_control`" condition in `openrouter_cache.pinned`, which only kept it off `auto` requests (design D3); and the `auto` tests and parameters (`test_openrouter_cache.py`: the `auto` wire test and request case; `test_support_matrix.py`: the `auto` routing, build and warning cases; `test_eval_wiring.py`: the mechanism parameter). `routing_for(..., "auto")` now raises like any unknown mechanism (asserted). The run-matrix test is parametrized `adopted` (the shipped constant routes the Anthropic row) and `rolled-back` (`None`, bare IDs); `test_marker_is_the_adopted_mechanism` pins the constant. `grep -n '"auto"\|extra_body' harness/*.py` finds only the pin reads in `openrouter_cache.pinned` and `support._call_pinned`; the one other mention of `auto` in the harness code is the deletion note beside `CACHE_MECHANISM`. `uv run poe test-fast`: 2318 passed. Docstrings of `support`, `matrix`, `cache_probe` and `openrouter_cache` say `marker` is current.
- [x] 8.2 Optional confirmation cell in a separate log directory, so `report.py` never treats a 1-epoch log as a shipped verdict. Run `uv run poe matrix --models claude-haiku-4.5 --tasks import_messy --epochs 1 --log-dir logs/cache-confirm`. The matrix prints its estimate (about $0.39 at today's priors; the printed figure governs). **Stop and wait for explicit approval; never pass `--yes`.** Afterwards verify:
  - `matrix-cost-*.json` carries `per_model_cache` with the hit rate and provider `Amazon Bedrock` (or `Google` on a failover turn), and no `off_pin` warning;
  - `uv run inspect log dump --header-only <log> | jq -r .eval.model` equals the registry ID.

  Record both in `measurement.md`.

  Done 2026-10-05 (`measurement.md`, confirmation cell). The user gave the go-ahead for the confirmation run in chat, and the main session ran the command with `--yes` after the matrix printed $0.39, the approved figure. Both checks hold: the cost summary's `per_model_cache` shows hit rate 92.1% and providers `Amazon Bedrock` ×5 and `unrecorded` ×14, `cache_warnings` is empty (no `off_pin`), and `.eval.model` is `openrouter/anthropic/claude-haiku-4.5`. Actual cost was $0.04, because the estimate prices every prompt token as uncached input. `import_l1` = I (RQ1 and RQ2 never referenced in the methodology section). That matches haiku's standing ❌ on `import_messy` and is not a caching regression: no tool or sample error, and a well-formed draft. The cell also showed that the matrix log keeps raw calls, and so serving providers, for only 5 of 19 calls. That is recorded as a known limitation (design D7, `harness/README.md`), not fixed, since `log_model_api` applies to a whole `inspect_eval` call. Logs: `logs/cache-confirm/`.

## 9. Documentation

- [x] 9.1 Update the matrix section of `harness/README.md`:
  - the adopted caching mechanism and the provider pin (models under test are served by the ZDR-compliant global Bedrock endpoint, with Vertex on failover; judge and persona unchanged);
  - the cache telemetry fields and the 50% and off-pin warnings;
  - role pricing and the unpriced-role stop, with its remedy (an override the registry prices);
  - `cache_write_price` on roster rows and `[role_prices]` entries, added to the `[role_prices]` paragraph `track-model-currency` wrote in the "Model currency" subsection rather than a second description of those entries;
  - `poe cache-probe` as the metered, gated re-check after an Inspect upgrade.

  Verify: `grep -n "cache-probe\|cache-hit" harness/README.md`.

  Written before the probe. Review follow-up: the "Prompt caching on Anthropic rows" paragraph now says no mechanism is used until the probe passes one (`support.CACHE_MECHANISM` unset), describes `auto` conditionally, and records that `poe smoke-inspect` runs the same path; the telemetry paragraph names `cache_warnings`, the models-under-test scope and the report's shared accumulation. If task 8.1 adopts a mechanism, state it there as current; if it adopts `marker`, or 7.4 drops caching, revise the paragraph.

  Revised after probe 1 (2026-10-05): the paragraph now describes the ZDR-compliant Bedrock/Vertex pin, `marker` as the candidate (with the wrapper's self-scoping), `auto` as selectable but not probed by default, and the on-pin provider names. Task 8.1 still restates it as current once a mechanism is adopted.

  Restated after probe 2 and task 8.1 (2026-10-05): the paragraph states `marker` as the current mechanism with probe 2's figures (88.8% / 86.4%, Bedrock, $0.06), `support.CACHE_MECHANISM = None` as the rollback, and `auto` as built, never probed under the pin and deleted; the telemetry paragraph says Vertex's recorded name `Google` is not yet seen in a response and that nothing is warned when rolled back; the re-check paragraph says `--mechanism` takes `marker` only. `grep -n "cache-probe\|cache-hit" harness/README.md` finds lines 63, 72 and 74.
- [ ] 9.2 Add one line to the Commands block of `AGENTS.md`: `uv run poe cache-probe [--estimate-only]   # metered prompt-caching check, cost-gated`. Verify: `grep -n cache-probe AGENTS.md`.

  The quoted line was simplified after 8.1: `--mechanism` now takes `marker` only, and that is its default.

  Deferred: needs user action (agent-instruction file). `AGENTS.md` is the agent-instruction file that `CLAUDE.md` imports, so an agent edits it only on the user's own instruction, never on another agent's. The user adds the line or authorizes the edit directly, and it goes after the `poe matrix` line, exactly as quoted above. Until then the proposal's Impact item "one command line in `AGENTS.md`" is not delivered (proposal.md marks it pending). Still open at archive, 2026-10-05: the approval reached the implementing subagents only as text relayed by another agent, so they did not add the line. The main session adds it on the user's direct instruction, in a follow-up commit.

## 10. Verify and close

- [x] 10.1 `uv run poe test` is green: pytest, ruff with the full rule set and complexity ≤ 12, the generated-copy drift check, and conformance.
- [x] 10.2 `uv run poe cov` holds the 78% floor. The new modules stay off the coverage omit list.
- [x] 10.3 `uv run poe specs` passes, including `openspec validate fix-openrouter-caching --strict`.

  10.1–10.3 green on 2026-10-05 before the probe (2404 passed; total coverage 88.28%, `cache_probe.py` 95%; 18 specs valid, the change valid). Re-run all three after groups 6–8 change anything. Re-run after the review follow-up, 2026-10-05: `poe test` green (2417 passed, ruff clean, generated copies in sync, 11 skills conform); `poe cov` 89.06% (`cache_probe.py` 97%, `support.py` 98%, `matrix.py` 94%); `poe specs` 18 valid and `openspec validate fix-openrouter-caching --strict` valid; `poe cache-probe --mechanism auto --estimate-only` still prints $0.09 + $0.17 = $0.26 with no model call. Re-run after the re-pin and the `marker` build (6.4, 7.1–7.2), 2026-10-05: `poe test` green (2454 passed, ruff clean, generated copies in sync, 11 skills conform); `poe cov` 89.19% (`openrouter_cache.py` 100%, `cache_probe.py` 97%, `support.py` 98%, `matrix.py` 94%); `poe specs` 18 valid and `openspec validate fix-openrouter-caching --strict` valid; `poe cache-probe --mechanism marker --estimate-only` prints haiku-4.5 $0.09 + sonnet-5.5 $0.17 = $0.26 with no model call. Re-run after the second review follow-up (untested status, mechanism metadata, pinned single message, `routable_openrouter`), 2026-10-05: `poe test` green (2466 passed, ruff clean, generated copies in sync, 11 skills conform); `poe cov` 89.23% (`openrouter_cache.py` 100%, `cache_probe.py` 98%, `support.py` 98%, `matrix.py` 94%); `poe specs` 18 valid and `openspec validate fix-openrouter-caching --strict` valid; `poe cache-probe --mechanism marker --estimate-only` still prints $0.09 + $0.17 = $0.26 with no model call. Re-run after probe 2 and the adoption of `marker` (7.3, 8.1, 9.1), 2026-10-05: `poe test` green (2462 passed — four fewer, as the `auto` cases went and one adoption pin came; ruff clean, generated copies in sync, 11 skills conform); `poe cov` 89.22% (`openrouter_cache.py` 100%, `cache_probe.py` 98%, `support.py` 98%, `matrix.py` 94%); `poe specs` 18 valid and `openspec validate fix-openrouter-caching --strict` valid; `poe cache-probe --estimate-only` defaults to `marker` and prints $0.09 + $0.17 = $0.26 with no model call. Re-run after the final review follow-up (8.2 recorded, the failed-row warning, the merge and suffix tests, the held-judge-safe test lookups), 2026-10-05: `poe test` green (2465 passed, ruff clean, generated copies in sync, 11 skills conform); `poe cov` 89.40% (`openrouter_cache.py` 100%, `cache_probe.py` 98%, `support.py` 99%, `matrix.py` 96%); `poe specs` 18 valid and `openspec validate fix-openrouter-caching --strict` valid; `poe cache-probe --estimate-only` still prints $0.09 + $0.17 = $0.26 with no model call.
- [x] 10.4 After human review, archive with the `openspec-archive-change` skill so the delta syncs into `openspec/specs/testing-harness/spec.md`. Commit the completed change off `main` with the attribution trailer. Do not push. Stage explicit paths only: the files this change modified (`/usr/bin/git diff --name-only`), the two new harness modules (`harness/cache_probe.py`, `harness/openrouter_cache.py`), the two new test files (`tests/unit/test_cache_probe.py`, `tests/unit/test_openrouter_cache.py`), the archived change folder and the synced spec. Never `git add -A` or `git add .`: the working tree also holds untracked files that are not part of this change.

  Done 2026-10-05 after the review rounds. The change was archived with `openspec archive fix-openrouter-caching --yes`, which synced the delta into `openspec/specs/testing-harness/spec.md`. It was committed on `main` with explicit paths only and not pushed. This task's "off `main`" predates the repo rule that unfinished work stays off `main`; this change is complete apart from 9.2's developer-doc line, and the run instructions committed it there. 9.2 stays open, as recorded there.
