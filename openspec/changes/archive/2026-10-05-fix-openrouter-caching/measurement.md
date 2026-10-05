# Measurements: fix-openrouter-caching

Every metered run of this change is recorded here: the command, the date, the per-model result, the actual cost with its evidence, and what was concluded. A run happens only after its estimate was shown and the user approved that run in chat (tasks.md, metered rule).

## Probe 1: mechanism `auto`, first-party pin (2026-10-05)

**Command** (user-approved after the printed estimate of $0.26: haiku-4.5 $0.09, sonnet-5.5 $0.17):

```sh
uv run poe cache-probe --mechanism auto --yes --log-dir logs/cache-probe
```

**Routing sent** (recorded in each log's `eval.model_args` and `eval.model_generate_config`, and in the one recorded request's `extra_body`): `provider = {"order": ["anthropic"], "allow_fallbacks": false}`, plus the top-level `cache_control = {"type": "ephemeral"}`.

**Result: both models failed on their first call with HTTP 404 from OpenRouter routing. No call reached an upstream.** The probe's `incomplete` check reported the sample error instead of scoring the replay, which is what it was built for (design D1, F1/V4). Each log holds one model event, no usage, and empty `stats.model_usage`. The probe's code at the time still counted that errored event as a call made and labelled the result `FAIL` ("the replay errored after 1 of 10 call(s): Error code: 404 …", exit 1), exactly as it would a caching failure. After the review follow-up the same logs read `UNTESTED`, after 0 of 10 answered calls, exit 3 (design D1).

| Model | Log | Calls made | Routing funnel (OpenRouter's `routing_funnel`) |
|---|---|---|---|
| `openrouter/anthropic/claude-haiku-4.5` | `logs/cache-probe/2026-10-05T05-08-11-00-00_cache-probe_8cN8Jcx7BW2hWTSvrvWq7C.eval` | 0 of 10 | 8 initial endpoints → **Regional Surcharge** removed `amazon-bedrock/us`, `google-vertex/us-east5`, `amazon-bedrock/eu-west-1`, `google-vertex/europe` (4 left) → **Guardrails** removed `azure/global`, `anthropic` with reason "ZDR violation (account settings)" (2 left) → **Fallback** removed `amazon-bedrock/global`, `google-vertex/global` (0 left) |
| `openrouter/anthropic/claude-sonnet-5.5` | `logs/cache-probe/2026-10-05T05-08-11-00-00_cache-probe_KTtGhJwhtaFojnpQPzzCbQ.eval` | 0 of 10 | 8 initial endpoints → **Regional Surcharge** removed `google-vertex/us`, `azure/us`, `google-vertex/europe` (5 left) → **Guardrails** removed `azure/global`, `claude-on-aws`, `anthropic` with reason "ZDR violation (account settings)" (2 left) → **Fallback** removed `google-vertex/global`, `amazon-bedrock` (0 left) |

OpenRouter's message in both: "No endpoints found for anthropic/<model>. Every candidate endpoint was removed during routing", with `failed_routing_step: "Filter by Fallback"`.

**Cost: $0.00.** Evidence:
- the OpenRouter account's usage was unchanged at $21.31 after the run (checked by the user, 2026-10-05);
- both logs carry an empty `stats.model_usage` and no usage on their single model event;
- a 404 from the routing step is raised before any upstream is called, so no token was billed.

**Conclusion.** The first-party pin (`order = ["anthropic"]`, fallbacks disabled) is incompatible with the account's zero-data-retention guardrail: OpenRouter's guardrail filter removes the `anthropic` endpoint for both models, and the disabled fallback then removes every endpoint that survived. This is a plumbing failure, not a caching verdict: no request reached an upstream, so nothing was measured about `auto`, about Bedrock or Vertex, or about cache reads.

The endpoints that survive both the regional-surcharge filter and the ZDR guardrail are the same for both models: the global Amazon Bedrock endpoint (`amazon-bedrock/global` for haiku-4.5, `amazon-bedrock` for sonnet-5.5) and `google-vertex/global`. This is the basis of the revised pin (design D2).

**User decision (2026-10-05).** Keep the account's ZDR guardrail. Pin the Anthropic rows to the ZDR-compliant global endpoints through the OpenRouter provider slugs `amazon-bedrock` and `google-vertex`, and build the explicit `marker` mechanism, because Bedrock's legacy integration rejects automatic top-level caching for Haiku 4.5, while explicit `cache_control` breakpoints served by Bedrock did produce cache reads on the system and tools prefix for sonnet in the 2026-10-04 logs. A second probe (mechanism `marker`) is proposed with a fresh estimate and runs only after the user approves it.

## Probe 2: mechanism `marker`, ZDR-compliant global Bedrock/Vertex pin (2026-10-05)

**Command** (run by the main session after the user explicitly approved the printed estimate of $0.26: haiku-4.5 $0.09, sonnet-5.5 $0.17), exit 0:

```sh
uv run poe cache-probe --mechanism marker --yes --log-dir logs/cache-probe
```

**Routing sent** (each log's `eval.model_args`): `provider = {"order": ["amazon-bedrock", "google-vertex"], "allow_fallbacks": false}`, no top-level `cache_control`; `eval.metadata.cache_mechanism = "marker"`. Both logs have status `success` and ten answered calls with no error.

**Result: both models PASS.**

| Model | Verdict | Read share after the first cache write | First write | Providers | Actual cost | Log |
|---|---|---|---|---|---|---|
| `openrouter/anthropic/claude-haiku-4.5` | PASS | 88.8% (36,199 of 40,748 prompt tokens, calls 5–10) | call 4 | Amazon Bedrock ×10 | $0.0233 | `logs/cache-probe/2026-10-05T06-11-11-00-00_cache-probe_DDfJWGtxpqzb74koLA3ZDa.eval` |
| `openrouter/anthropic/claude-sonnet-5.5` | PASS | 86.4% (49,066 of 56,795 prompt tokens, calls 2–10) | call 1 | Amazon Bedrock ×10 | $0.0358 | `logs/cache-probe/2026-10-05T06-11-11-00-00_cache-probe_XgfMSA4dDbvAFihYr7oVNv.eval` |

Threshold 80% (`verdict_cache_reuse`). Totals from `stats.model_usage`: haiku-4.5 input 8,005, cache write 8,666, cache read 36,199, output 160; sonnet-5.5 input 20, cache write 9,734, cache read 49,066, output 160.

**Per call** (`uv run inspect log dump <log> | jq`, the model events' `output.usage`; `in` is uncached input, `cw` cache writes, `cr` cache reads; every call 16 output tokens and served by `Amazon Bedrock`):

| Call | haiku-4.5 in | cw | cr | sonnet-5.5 in | cw | cr |
|---|---|---|---|---|---|---|
| 1 | 1,902 | 0 | 0 | 2 | 2,023 | 0 |
| 2 | 2,655 | 0 | 0 | 2 | 822 | 2,023 |
| 3 | 3,406 | 0 | 0 | 2 | 902 | 2,845 |
| 4 | 6 | 4,153 | 0 | 2 | 819 | 3,747 |
| 5 | 6 | 751 | 4,153 | 2 | 904 | 4,566 |
| 6 | 6 | 754 | 4,904 | 2 | 820 | 5,470 |
| 7 | 6 | 750 | 5,658 | 2 | 903 | 6,290 |
| 8 | 6 | 754 | 6,408 | 2 | 821 | 7,193 |
| 9 | 6 | 752 | 7,162 | 2 | 904 | 8,014 |
| 10 | 6 | 752 | 7,914 | 2 | 816 | 8,918 |

Haiku-4.5's first three prompts (about 1.9k to 3.4k tokens) sit below its 4,096-token minimum and cache nothing; its first write lands on call 4 at 4,153 tokens, one call earlier than the call 5 to 7 design D1 expected: haiku's real prompts came to about 77–86% of the estimator's sizes (1,902 tokens against 2,200 on call 1, 8,672 against 11,200 on call 10), not the roughly 60% that 5 characters a token would give. Each turn appended about 750 tokens against the estimated 1,000, so the notes tokenize at roughly 4 characters a token. The estimate still bounds the replay. Every later call reads the whole previous prompt and writes only the newly appended turn. Sonnet-5.5 writes on call 1 and reads from call 2 on. Each call's breakpoint therefore lands on the newest tool result, and Bedrock accepted and cached the list-form tool content (design Risks, first entry).

**Cost: $0.059 actual** (haiku-4.5 $0.0233, sonnet-5.5 $0.0358, at registry prices from the logged usage), against the $0.26 worst-case estimate. Evidence:
- the logged usage priced at the registry rows (haiku-4.5 1.0 / 5.0 / 0.1 / 1.25 $/Mtok, sonnet-5.5 2.0 / 10.0 / 0.2 / 2.5 for input / output / cache read / cache write);
- the prompt side cost $0.0225 (haiku-4.5) and $0.0342 (sonnet-5.5) against an uncached equivalent of $0.0529 and $0.1176;
- OpenRouter's own billed cost, `usage.cost` in each logged raw response (`jq '[.samples[0].events[]|select(.event=="model")|.call.response.usage.cost]|add'`), sums over the ten calls to $0.0232574 (haiku-4.5) and $0.0357882 (sonnet-5.5): identical to the registry-priced figures, so Bedrock charged the registry's cache-write prices (1.25 and 2.5 $/Mtok);
- the OpenRouter account usage endpoint, checked right after the run, still showed $21.31 with a daily usage of 0. The account view lags, so it neither confirms nor contradicts the figure; it is recorded as read. The billed `usage.cost` above is the confirming evidence.

**Not measured.** Google Vertex served no call (Bedrock served all twenty), so the recorded provider name `Google` for the `google-vertex` slug (`support.PROVIDER_NAMES`, taken from the endpoint catalog) is still unconfirmed in a live response (design, Open Questions). Opus-5.5 was not probed (design D1).

**Conclusion.** `marker` under the ZDR-compliant Bedrock → Vertex pin passes the 80% bar on both default probe models. It is adopted (tasks.md 8.1): `support.CACHE_MECHANISM = "marker"`, and the unprobed `auto` is deleted.

## Confirmation cell (task 8.2): haiku-4.5 × `import_messy` × 1 epoch (2026-10-05)

**Command** (run by the main session on the user's go-ahead for the confirmation run, after the matrix printed its estimate of $0.39, the figure the user approved), exit 0:

```sh
uv run poe matrix --models claude-haiku-4.5 --tasks import_messy --epochs 1 --log-dir logs/cache-confirm --yes
```

The separate log directory keeps `poe report` from treating a one-epoch log as a shipped verdict. Log: `logs/cache-confirm/2026-10-05T06-31-02-00-00_import-messy_Ez8hrzkzxCDQcf8vm74NH4.eval`; cost summary: `logs/cache-confirm/matrix-cost-2026-10-05T06-31-52Z.json`.

**Task 8.2's checks, both met:**
- the cost summary carries `per_model_cache` for `openrouter/anthropic/claude-haiku-4.5` with hit rate 0.9212 and providers `Amazon Bedrock` ×5, `unrecorded` ×14; `cache_warnings` is empty, so no `off_pin`, and `cache_mechanism` is `marker`;
- `uv run inspect log dump --header-only <log> | jq -r .eval.model` prints `openrouter/anthropic/claude-haiku-4.5`, the registry ID. The header's `eval.model_args` carry the Bedrock → Vertex pin and `eval.metadata.cache_mechanism` is `marker`.

**Result: caching works on a real matrix cell.** The hit rate was 92.1%: 12,354 cache-write tokens, 145,680 cache-read tokens, 109 uncached input tokens and 2,763 output tokens. The prompt side cost $0.03 against an uncached equivalent of $0.16, so caching saved $0.13 on this cell. The run went through the matrix's own path (`poe matrix` → `run_matrix` → `build_model`).

**Cost: $0.04 actual** ($0.0439, recorded usage × registry pricing), against a printed estimate of $0.39. The estimate is conservative by construction. Its history and priors record full context demand and price all of it as uncached input (design D6), so a cell that caches costs far less than its estimate. The log cannot confirm the figure through OpenRouter's billed `usage.cost` as probe 2's logs did, because only 5 of the 19 calls kept their raw response (below).

**Score.** `import_l1` = I: "(RQ1) never referenced in the methodology section; (RQ2) never referenced in the methodology section". The main session checked that this is not a caching regression. The sample has 40 messages, 19 of them tool messages, with no tool error and no sample error, and the draft is well-formed. The result matches haiku-4.5's standing ❌ on `import_messy`: its uncached 2026-08-24 runs failed all 3 epochs, there on structure. A single epoch in a separate log directory is never a verdict.

**Provider telemetry gap (found here).** The log holds 19 model events, and Inspect kept the raw call (`.call`, whose `response.provider` names the serving upstream) for only 5 of them. In Inspect 0.3.250 (`inspect_ai/log/_transcript.py`, `Transcript._process_event`), `log_model_api=True` keeps every call. The default, `None`, which the matrix uses, keeps errors plus the first `DEFAULT_LOG_MODEL_API_CALLS = 5` calls per model name per sample, and a judge or persona call on the same ID uses up one of those slots. The provider is recorded nowhere else on the event: `output` carries `choices`, `completion`, `model`, `time` and `usage`, and no metadata. The matrix's provider counts and its `off_pin` warning therefore cover each sample's first five calls. The probe runs with `log_model_api=True` and recorded all ten calls. This is recorded as a known limitation (design D7, harness README), not fixed here: `log_model_api` applies to a whole `inspect_eval` call, not to one model. Scoping it to routed rows would split them into their own call per task, which runs them after the other rows instead of beside them. Setting it for the whole call would log every row's raw calls, at about 4.4 KB each in the uncompressed dump on this cell (22 KB for the five kept), and more on long dialogues. With `allow_fallbacks: false` an off-pin call is not expected at all, so the warning stays a per-sample spot check.
