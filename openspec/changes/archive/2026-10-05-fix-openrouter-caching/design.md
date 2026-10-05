# Design: fix-openrouter-caching

## Context

The motivation is in proposal.md (Why). These facts about the current code shape the approach:

**Inspect 0.3.250, OpenRouter provider (`.venv/.../inspect_ai/model/_providers/openrouter.py`):**
- `_generate_completion` calls the module-level function `_add_anthropic_cache_markers(request)`. It does so only when `_cache_prompt_enabled` holds, which means an `anthropic/*` model and `cache_prompt` not set to `False` (`:313-342`).
- That function marks the last system block and the last tool definition. It adds a rolling message breakpoint only when the last message, or the one before it, already has list content (`:438-450`). A comment there says it deliberately leaves `role: "tool"` string content alone "for upstream tool_result translation".
- `_openai.py:270-301` always emits assistant content as one flattened string and tool content as a string. So in an agent loop no rolling breakpoint ever lands. Converting `ChatMessage` content to block lists in our solver would change only user messages.
- Cache markers are added after Inspect snapshots the request for the log (`:417-421`). They never appear in `.eval` files, so the usage fields are the only evidence that caching works.
- The provider takes a documented `provider` model argument, which it forwards as `extra_body.provider` (`:108-112`, `:382-393`). It forwards the dict unchanged, so `order`, `allow_fallbacks` and `only` all reach OpenRouter as given.
- `GenerateConfig.extra_body` is merged into the request body (`_openai.py:378-384`). Probe 1's one recorded request confirms both: `extra_body = {"cache_control": {...}, "provider": {"order": ["anthropic"], "allow_fallbacks": false}}`.
- The request dict that `_generate_completion` receives, and that the marker function mutates, is the one handed to the OpenAI SDK's `chat.completions.create(**request)`, whose `extra_body` the SDK merges into the JSON body (`openai_compatible.py:234-249`, `:307-326`). An L0 test can therefore pin the wire body by stubbing `create` and reading its keyword arguments, without a socket.
- The messages are rebuilt from `ChatMessage`s on every call (`openai_compatible.py:235`), so a content conversion made on one call never carries over to the next.

**OpenRouter routing (provider-selection, in-region routing and prompt-caching docs, read 2026-10-05):**
- `order` lists provider slugs to try in order. With `allow_fallbacks: false` it restricts routing "to just your chosen list": the listed providers are tried in order, and the request fails once they all have failed. `only` restricts the allowed set without fixing an order.
- A bare slug (`google-vertex`) matches all endpoints of that provider, but on the global domain default routing skips regional-surcharge endpoints whenever a standard-priced one exists, and "a bare provider slug such as `amazon-bedrock` does not pin its regional endpoints". Only a full regional slug (`amazon-bedrock/eu-west-1`) does.
- Provider sticky routing for prompt caching is not used when `provider.order` is set; the explicit order wins.
- The prompt-caching guide lists Bedrock and Vertex among the providers that accept top-level automatic `cache_control`, converting it to a trailing breakpoint on Bedrock. This contradicts the bundled claude-api note on the legacy Bedrock integration for Haiku 4.5, and nothing here has measured either. Explicit per-block breakpoints work on every Anthropic-compatible provider, according to the same guide.
- The response's `provider` field carries the endpoint's `provider_name`: `Amazon Bedrock` for every `amazon-bedrock*` endpoint, `Google` for every `google-vertex*` endpoint and `Anthropic` for first-party (recorded catalog `tests/unit/data/model_catalog/endpoints/`, and `Amazon Bedrock` in the 2026-10-04 logs).
- In the recorded catalog, the global Bedrock and Vertex endpoints of haiku-4.5 and sonnet-5.5 carry the `anthropic` endpoint's input, output and cache-read prices. The regional ones cost 10% more. So the registry prices, taken from the `anthropic` endpoint (D6), price the pinned serving correctly.
- Cache writes are moved out of `input_tokens` into `input_tokens_cache_write` (`:479-507`).
- By default Inspect records the raw model call only for the first few calls per model, plus errors. That raw call is where OpenRouter's top-level `provider` field (the serving upstream) lives.

**`harness/matrix.py`:**
- `run_matrix` passes bare model-ID strings and one shared generate configuration to each `inspect_eval` call (`:103-117`).
- `collect_usage` counts context demand as `input + cache_read` and never reads cache writes (`:121-155`).
- `record_spend` persists `matrix-cost-*.json` with dollar figures only (`:158-181`).

**`harness/support.py`:**
- `estimate_cost` prices the judge only when `[tasks.judge].model` is a registry row; otherwise it lists the judge as "unpriced" and charges it $0 (`:243-258`).
- A `JUDGE_MODEL` or `PERSONA_MODEL` override is never seen (the evals read them at `skill_evals.py:75` and `:589`).
- The persona has no budget.
- `price_usage` charges input, output and cache reads only (`:261-279`). Today it looks prices up by roster ID only (`:273-276`); `track-model-currency` moves it onto `support.model_price` (see Dependencies).

**`harness/report.py:50`** keeps a log only when `header.eval.model` equals a registry ID. For a `Model` object, Inspect logs `str(model)`, which is `"<api>/<name>"`, for example `openrouter/anthropic/claude-haiku-4.5`. Building the model with extra arguments therefore keeps the logged ID. Registering a provider under a new name would not.

**Measured on 2026-10-04:**
- Every sampled Anthropic call was served by Amazon Bedrock.
- The sonnet-5 run read one 1,189-token prefix from cache, and that prefix never grew.
- Haiku cached nothing. Its minimum cacheable prefix is 4,096 tokens (bundled claude-api `shared/prompt-caching.md:138`).
- The legacy Bedrock integration rejects top-level (automatic) `cache_control` for Haiku 4.5 (`shared/platform-availability.md`, "Automatic prompt caching" row).
- Per call, the default haiku judge used about 7k input and 1.1–1.7k output tokens: four calls each in the 10-04 haiku and sonnet `write_rich_seed` logs, two epochs × two L2 scorers. The sonnet-5 re-grade wrote 4.68k output tokens per call (`rejudge.jsonl`: 224,472 / 48).
- Haiku usage on the 2026-08-04 `ideate_longrun` logs, where the model under test was sonnet-4.5 and haiku was both persona and judge, was 45.4k in / 3.2k out and 35.4k in / 2.3k out per cell-epoch.

**Measured on 2026-10-05 (probe 1, `measurement.md`):**
- Under `order = ["anthropic"]`, `allow_fallbacks = false`, both haiku-4.5 and sonnet-5.5 failed on their first call with a 404 from OpenRouter routing, at $0.
- The account's guardrail removed the `anthropic` endpoint ("ZDR violation (account settings)"), together with `azure/global` and, for sonnet-5.5, `claude-on-aws`. The regional-surcharge filter had already removed the regional Bedrock, Vertex and Azure endpoints.
- For both models, only the global Bedrock endpoint (`amazon-bedrock/global` for haiku, `amazon-bedrock` for sonnet-5.5) and `google-vertex/global` survived both filters. The disabled fallback then removed them, because the pin did not list them.

**Measured on 2026-10-05 (probe 2, `measurement.md`):**
- Under the Bedrock → Vertex pin with mechanism `marker`, both models PASS: haiku-4.5 read 88.8% of the prompt tokens on the six calls after its first cache write (call 4), sonnet-5.5 86.4% on the nine calls after its first write (call 1). Actual cost $0.059 against the $0.26 estimate.
- Amazon Bedrock served all twenty calls and accepted the list-form tool content with its breakpoint; every call after the first write read the whole previous prompt. Vertex served none.

**Dependencies:**
- `track-model-currency` lands first and introduces the registry roles table (`judge`, `smoke`, `dev_judge`, `dev_judge_effort`). It writes no `persona` key: `roles.persona` defaults to `judge` when absent. The evals resolve both through its pure `support.role_model(roles, name, environ)`, environment overrides keep working, and each override applies to its own role only (its D5). It also rejects `[tasks.judge].model` at parse time, so the roles table is already the single source of the judge's ID (its D4).
- The model IDs in `models.toml` (sonnet-5.5 and opus-5.5 by then) belong to that change.
- That change also owns held-role pricing (its D4, "Held role IDs that leave the roster"):
  - `Registry.role_prices` holds price-only `[role_prices."<id>"]` entries, keyed by model ID, with a roster row's price fields.
  - `support.model_price(registry, id)` is the one price lookup: the roster row with that ID, enabled or not, else the `[role_prices]` entry, else `None`. `estimate_cost` and every other price lookup in `support.py`, `price_usage` included, go through it (its task 1.2).
  - Parsing fails, naming the role, when the judge or persona cannot be priced, and fails, naming the entry, for an entry no role names or one duplicating a roster ID.
  - Its `--write` replaces roster rows in place (its D10) and holds `judge` and `persona` (its D2, critique V1). When it re-pins a roster row whose outgoing ID a held role still names, it writes the `[role_prices]` entry for that ID in the same edit. Later runs report `price_drift` on the entry and `--write` refreshes it (its task 2.2, "held role leaves the roster").
- This change consumes that machinery (D4a) and adds only the optional `cache_write_price` to roster rows and role-price entries (D6).

## Goals / Non-Goals

**Goals:**
- Choose a caching mechanism for the Anthropic matrix rows by measurement. The bar is the 80% steady-state read share (spec "Cache reuse probe").
- Make a caching regression and an off-pin serving provider visible after every matrix run.
- Make the pre-run estimate cover every model the run calls, including role overrides, and price cache writes after the run, for roster rows and role-price entries alike.

**Non-Goals:**
- Pricing held roles whose ID has left the roster. `track-model-currency` owns `[role_prices]`, `support.model_price` and the checker's refresh of those entries; this change only adds `cache_write_price` to them (D4a).
- Moving the matrix judge or persona to the subscription, or changing which model they use. That is Change D (deferred, user decision 1).
- Routing the judge or persona to a different upstream. This follows critique V1/V2: the judge's input conditions stay as they are until D re-baselines them.
- Non-Anthropic rows. Their caching is provider-automatic and out of scope; their requests must stay byte-identical.
- The dev runner and the subscription text roles (`add-dev-runner-judge`), and the everyday `smoke` task, which runs on the dev runner. `smoke-inspect` is not exempt (review follow-up, recorded deviation): it is `matrix.py --smoke`, a matrix selection, so it inherits the adopted `marker` routing and caching, the role pricing, the unpriced-role stop and the raised judge budget, like any other matrix run. Exempting it would make the metered Inspect-wiring check exercise a path the matrix no longer takes.
- Implementing the Console-key fallback. If it is needed, it becomes its own change on the user's go-ahead (D9).
- Pricing expected cache hits into the estimate (D6).

## Decisions

### D1. Measure before choosing: a synthetic replay probe, gated like the matrix

`harness/cache_probe.py` (`main(argv)`, `poe cache-probe`, `envfile = ".env"`) defines a one-sample Inspect task. Its solver replays a fixed conversation. The task is run in-process through `inspect_eval`, with `log_model_api=True` (ten calls, small log) and its own log directory (`logs/cache-probe/`), so `report.py` never sees it. The replay looks like this:
- System prompt plus Inspect's real `bash`/`text_editor` tool definitions, about 1.2k tokens, the same prefix the matrix sends.
- Ten calls made one after another. Before each call the solver appends a synthetic assistant tool call and a synthetic tool result of about 1k tokens.
- Every second assistant turn carries no text, because haiku often calls tools without text.
- The model's own replies are discarded (`max_tokens = 16`), so the conversation is the same on every model and every run.
- The synthetic text is generated deterministically. It contains nothing from real proposals.

Prompt sizes run from about 2.2k to 11.2k tokens, about 67k in total per replay.

**Pass rule:** `verdict_cache_reuse` takes per-call `(input, cache_write, cache_read)` and passes when the reads summed over the calls after the first cache write are at least 80% of the prompt tokens summed over those same calls. Expected values: on sonnet-5.5 (512-token minimum) reads start at call 2. On haiku-4.5 (4,096-token minimum) the first write lands around call 5 to 7 of 10, and the calls after it read about 88–91% (Risks, "Haiku's 4,096-token minimum"). The estimator's 3 characters a token, taken literally, would put it at call 3; the real notes tokenize at roughly 4 characters a token. Probe 2 measured call 4 and 88.8% on haiku-4.5 (its real prompts came to about 77–86% of the estimated sizes, each turn about 750 tokens against the estimated 1,000), and reads from call 2 at 86.4% on sonnet-5.5.

The verdict runs only on a complete replay, and each model ends `PASS`, `FAIL` or `UNTESTED`. The probe passes `fail_on_error=False`, under which Inspect marks a log `success` even when its sample raised, so the log status alone does not decide:
- Only a call that returned usage counts as made. A call that raised leaves a model event without usage, and it is not counted.
- A sample error names its message and the calls answered before it ("the replay errored after N of 10 answered call(s): …"). A 400 rejects the request the mechanism shaped, so it is a scored `FAIL` (D3). Any other error is `UNTESTED`: a routing 404 from the provider pin, a 401, 402 or 429, a 5xx, or an error with no HTTP status.
- A run that did not finish, and a replay that recorded fewer than ten calls, are `UNTESTED`.
- `FAIL` is also the verdict's own failures: a read share below 80% or no cache write.

The exit status is 0 when every model passed, 1 on any `FAIL` (or a declined prompt), and 3 when nothing failed but a model went untested (2 stays the usage error). A partial replay is never scored, and an error is never reported as "no call wrote the cache" (F1/V4; review follow-up). Probe 1 hit exactly this case: both models' first call returned the routing 404. The code of that run counted the errored call as made and labelled the result `FAIL` ("errored after 1 of 10 call(s)"). The review follow-up made the count and the label honest: the same logs now read `UNTESTED`, after 0 of 10 answered calls, exit 3. Task 7.4's stop branches on a scored `FAIL` only.

**Worst-case estimate:** a pure function charges every prompt token at the cache-write price, plus `max_tokens` output per call:
- haiku-4.5: at most $0.09 per mechanism;
- sonnet-5.5: at most $0.17;
- opus-5.5: at most $0.34, so it is not probed by default. Its mechanism is the same, and its first matrix run's telemetry covers it.

The probe prints this figure through the matrix's `print_cost` and `confirm_spend`, then waits for approval. It defaults to the enabled Anthropic rows of the cheap and mid tiers. A mechanism is adopted only if it passes on both.

**Alternatives rejected:**
- **Probing through a real matrix cell.** The conversation length depends on the model, the judge adds calls that cannot read the cache, a haiku cell costs about $0.39 (printed by `--estimate-only`, 2026-10-05), and the cell would write a newest log for a shipped verdict.
- **A bare `get_model().generate()` loop.** It yields no recorded model call, so no serving provider, and it would need a second telemetry path.

### D2. Per-model routing for Anthropic rows only, built as `Model` objects

A pure `support.routing_for(model, mechanism)` returns a small dataclass of `model_args` and a `conversation_breakpoint` flag:
- For `family == "anthropic"` rows: `model_args = {"provider": {"order": ["amazon-bedrock", "google-vertex"], "allow_fallbacks": False}}` (`support.PINNED_PROVIDERS`), and `conversation_breakpoint` set (mechanism `marker`, D3).
- For every other family: empty.

`run_matrix` and the probe call `get_model(id, **model_args)` only for a non-empty routing, and keep the bare ID string otherwise. The pin is recorded in the log's `model_args`, which holds no credentials. `marker` shows there only as the pin: its breakpoint lives in process state (D3), and Inspect copies the request for the log before the markers are added (Context). So `run_matrix` and the probe also pass `metadata={"cache_mechanism": …}` to `inspect_eval` (the log's `eval.metadata`), and `matrix-cost-*.json` carries `cache_mechanism` beside the cache telemetry (review follow-up). One gap remains: `inspect eval-retry` rebuilds the Model from the logged `model_args` and never calls `build_model`. A retried `marker` run therefore sends the pin without the breakpoint, while the copied metadata still says `marker`. Re-run a `marker` run through the matrix, never through `eval-retry`.

**Adoption.** `support.CACHE_MECHANISM` names the one adopted mechanism. It stayed `None` until the probe had passed one; probe 2 passed `marker` (2026-10-05, `measurement.md`), and task 8.1 set the constant to `"marker"` and deleted the unprobed `auto`. `routing_for(model, None)` routes nothing, so setting the constant back to `None` is the rollback: the matrix, `smoke-inspect` included, then sends every row exactly as before this change, and no cache warning fires, since nothing is pinned. The probe takes its mechanism explicitly (`--mechanism`, whose only choice and default is `marker`, also while the matrix is rolled back). Review follow-up: the implementation first pre-set the constant to `auto`, which put an unprobed mechanism with no provider fallback in front of any matrix run started from the working tree.

**Single-message requests.** The breakpoint rides on every request of the routed model under test, its first included, even when that request is a single message (a dialogue task's first turn): that request heads a conversation whose later turns read it back. The spec's one-shot rule targets the judge and persona prompts, which no later call extends. The eval builds them from their bare role IDs (`get_model(<role ID>)`), and Inspect memoizes models on config and model arguments, so they never receive the routed model's settings even when they share its ID (L0: `test_eval_wiring.py`). The pin is the one discriminator: a pinned request is always the model under test's, so the wrapper marks a pinned single message too. That is a dialogue task's first turn, the skill prompt as one user message with no system message, and marking it lets the second turn read the skill body instead of paying to write it (review follow-up). An unpinned single message, a judge or persona prompt, is never marked.

**Why this pin** (user decision 2026-10-05, after probe 1):
- **ZDR-compliant.** The account keeps its zero-data-retention guardrail. For both probed models, the global Bedrock and Vertex endpoints are the only ones that guardrail and the regional-surcharge filter both keep (Context, probe 1).
- **Bare slugs, not regional ones.** A bare slug never pins a regional-surcharge endpoint, so the request reaches exactly the standard-priced global endpoints, which the registry prices correctly. The bare slugs also cover the per-model naming: haiku-4.5's Bedrock endpoint is `amazon-bedrock/global`, but sonnet-5.5's is plain `amazon-bedrock`.
- **`order` with `allow_fallbacks: false`, not `only`.** With an explicit order, Bedrock serves every turn while it is available, so successive turns reach the cache they wrote. Vertex serves only when Bedrock fails, and nothing outside the list ever serves. A failover turn writes a fresh cache on Vertex and shows up in the recorded providers. `only` would let OpenRouter balance the conversation across both upstreams, relying on sticky routing that is undocumented in its details. Caches are isolated per upstream account, so that could scatter cache entries.
- **Bedrock first.** In the 2026-10-04 logs, explicit `cache_control` breakpoints served by Bedrock produced cache reads (on the sonnet-5 system and tools prefix). Vertex has no such evidence here.
- `allow_fallbacks: false` keeps a fallback from silently bringing back an unpinned path. An error from both upstreams surfaces as an error instead: Inspect retries transient ones, and token-free 429s cost nothing.

**Mechanism `marker` is adopted**, and `auto` was deleted without a probe under this pin. Bedrock, which serves first under this pin, rejects automatic top-level caching for Haiku 4.5 in its legacy integration (bundled claude-api `shared/platform-availability.md`). OpenRouter's guide says it converts the top-level field to a trailing breakpoint on Bedrock, but nothing here has measured that. Explicit breakpoints are the form both the guide and the 2026-10-04 Bedrock logs support, and probe 2 passed them on both models. `auto` (a top-level `cache_control` in the model's own `GenerateConfig.extra_body`) was selectable in the probe until task 8.1 deleted it with its `extra_body` routing field; re-adding it would be its own change with its own probe. The default 5-minute TTL is kept: agent turns start well under 5 minutes apart, and the 1-hour TTL doubles the write premium.

**Pin alternatives rejected:**
- **First-party Anthropic (`order = ["anthropic"]`).** It was the original pin. Probe 1 showed it cannot route under the account's ZDR guardrail: a 404 at OpenRouter's routing step, for both models.
- **Relaxing the account's ZDR guardrail** so first-party serving routes. Declined by the user (2026-10-05).
- **A Console API key with Inspect's native `anthropic/` provider.** It stays the deferred fallback of D9: a second billing account and new logged IDs, so its own change and only on the user's go-ahead.
- **`auto` on Bedrock.** Rejected for haiku-4.5, see above.
- **Full regional slugs** (`amazon-bedrock/global`, `google-vertex/global`). The endpoint names differ per model (sonnet-5.5's Bedrock endpoint has no `/global` suffix), so the registry would need per-model pins, while the bare slugs already exclude the surcharged regional endpoints.
- **`only` without `order`.** It allows interleaving across upstreams (see above).

**Alternatives rejected for the scoping** (critique 1.9):
- **Request-level `extra_body` on the shared `inspect_eval` configuration, or global `-M` model arguments.** These reach every family, including the Azure-pinned luna row whose strict validation already rejects inputs.
- **A repo-local provider subclass under a new name.** It changes the logged ID prefix, so `report.py:50` silently drops the logs.
- **Re-registering a subclass as `openrouter`.** It depends on registry overwrite order.

### D3. Mechanism `marker`, adopted: a self-scoping wrapper around Inspect's marker function

Built after probe 1 (user decision 2026-10-05), instead of only after an `auto` failure, and adopted after probe 2 passed it on haiku-4.5 and sonnet-5.5 (`measurement.md`). `harness/openrouter_cache.py` (new, covered by tests) provides:
- A pure function `add_conversation_breakpoint(request) -> bool`, which mutates the OpenAI-format request dict and returns whether it added a breakpoint. It acts only when all of the following hold:
  - the request's `extra_body.provider` equals the harness pin (`support.provider_pin()`). Only `routing_for` produces that pin, so the function scopes itself to routed Anthropic rows under the adopted or probed mechanism. The judge, the persona, every other family and every matrix request sent while the mechanism is rolled back carry no pin and are left byte-identical, so no one-shot judge or persona prompt is ever marked. A pinned request with a single message, a dialogue task's first turn, is marked (D2 "Single-message requests"; review follow-up removed an earlier two-message minimum that cost each dialogue a write of the skill body on its second turn). An earlier condition, no top-level `cache_control`, kept the wrapper off `auto` requests; it went with `auto` (task 8.1);
  - fewer than four `cache_control` markers are already present (Anthropic's limit; Inspect's own markers use at most three).

  When it acts, it first turns every user and tool message with non-empty string content into a one-block text list. Then it puts `cache_control` on the last block of the newest user or tool message with non-empty content. The walk back passes assistant turns, whose content Inspect flattens to a string (often empty on a tool call), and the system message, which Inspect marks itself. In an agent loop the marked message is the newest tool result, and in a dialogue turn the newest user message. The conversion runs on every call (the messages are rebuilt each time, see Context). The conversation prefix is therefore sent in the same form on every call, whichever message carried the breakpoint on the previous one. Empty strings stay strings, because Anthropic rejects empty text blocks. Assistant content stays as Inspect flattens it.
- An idempotent `install()` that replaces the module attribute `inspect_ai.model._providers.openrouter._add_anthropic_cache_markers` with a wrapper that calls the original first and then the pure function. The attribute is looked up at call time, so the replacement takes effect. It sits behind Inspect's own `anthropic/*` and `cache_prompt` gate. A missing symbol raises at install time instead of passing silently.

**Where it is installed.** `matrix.build_model` calls `install()` when the routing sets `conversation_breakpoint`. That covers the matrix and the probe, which builds through `build_model`. It is not installed at `skill_evals.py` import: a direct `inspect eval` run builds bare IDs, so no request it makes carries the pin, and the wrapper would act on nothing there. With `CACHE_MECHANISM` rolled back to `None`, only a `cache-probe` run installs it. Even if it is installed, it changes no request without the pin.

**L0 tests** pin the request body the provider hands to the OpenAI SDK, by stubbing `chat.completions.create` on a model built through `build_model` with a placeholder key:
- the `provider` routing fields;
- the system and last-tool markers Inspect adds;
- exactly one conversation breakpoint, on the last tool message's single text block for string content, or on the last block of list content;
- no change for a non-Anthropic row, or for an unpinned Anthropic model (the judge's bare ID), including its single-message prompt, all with the wrapper installed;
- a breakpoint on the routed model's single-message first turn.

A guard asserts that the private symbol exists and is wrapped. An Inspect upgrade that renames it then fails offline instead of silently dropping caching.

Converting tool content to list form is the placement Inspect avoided. Whether OpenRouter's translation to Bedrock (and, on failover, Vertex) accepts and caches it is exactly what the probe's `marker` run settles; a 400 or no reads counts as a failure, while a routing or account error leaves the mechanism untested (D1). Probe 2 settled it for Bedrock: accepted and read back on both models. Vertex served no call and stays unmeasured.

**Alternatives rejected:**
- **Marking only the last text-bearing user or assistant message.** It falls behind textless tool-call turns, which are common on haiku, because Inspect flattens assistant content.
- **Normalising `ChatMessage` content in the solver.** It only reaches user messages (see Context).
- **Converting only the marked message.** The previous call's breakpoint message would go back to string form on the next call. If OpenRouter renders a string and a one-block list differently, every read would miss. Converting all user and tool strings costs nothing and removes that question.
- **Installing at `skill_evals.py` import.** It would install the wrapper in every eval process, including those that never route, for no effect. `build_model` is the one place a pinned model is made.
- **Scoping by the `anthropic/*` gate alone** (the original D3). It would mark Anthropic conversations before any mechanism is adopted, against the spec's "until a mechanism has passed" rule.

### D4. Role models priced as resolved, through one price lookup, and an unpriced role stops the run

**Resolution.** The estimate resolves the judge and persona IDs through `support.role_model(roles, name, environ)`, the pure resolver `track-model-currency` introduces and `skill_evals.py` already calls. The environment override (`JUDGE_MODEL`/`PERSONA_MODEL`) wins, else the roles table, with `persona` defaulting to `judge` when the table has no `persona` key. `matrix.py` shares the environment in-process with the eval. Each override applies to its own role only, so a judge override leaves the persona priced at its held ID. The resolver is that change's deliverable: if it is missing when this change starts, implementation stops instead of adding a second one.

**One price lookup.** `support.model_price(registry, model_id)` from `track-model-currency` is the only place a price is found: the roster row (`[[models]]`, enabled or not) that carries the ID, otherwise the `[role_prices."<id>"]` entry for it, otherwise none. `estimate_cost` and `price_usage` already call it when this change starts (precondition 1.3). This change keeps it the only lookup: the role-aware `estimate_cost`, the cache-aware `price_usage` and the probe's estimate all go through it, and none adds a second one. The actual-spend report therefore prices an off-roster judge exactly as the estimate does. If it is missing when this change starts, implementation stops instead of adding a second one.

**Budgets.** The judge budget applies to every cell-epoch, and the persona budget to every cell-epoch of a `dialogue` task (D5).

**Stop.** A role ID for which `model_price` finds nothing makes `main` exit 2 before `confirm_spend`, and `--yes` does not bypass this. Because `track-model-currency`'s parser refuses a registry whose default judge or persona is unpriced, the stop can fire only for an environment override. The message names the ID and the remedy: an override the registry prices, meaning a roster ID (enabled or not) or a role's own ID. A `[role_prices]` entry is no remedy for an override, since `track-model-currency` rejects an entry that no role names; an experiment's override is environment state, not registry state. This replaces today's "(unpriced …)" line, which let a sonnet-judge re-grade run 3.8× over its approval.

**Alternatives rejected:**
- **Keep charging $0 and listing the ID as unpriced.** That is today's defect.
- **A separate lookup in each pricing site.** The estimate and the actual report would disagree on the off-roster judge, the D4a case.

Subscription IDs never reach the matrix while its roles stay on OpenRouter (Change D). The subscription prefix rule `is_subscription_model` therefore stays with `add-dev-runner-judge`.

### D4a. Held role pricing is consumed from `track-model-currency`, not owned here

**The case.** `track-model-currency`'s `--write` replaces roster rows in place and never re-pins the held `judge` or `persona`. When a newer Haiku ships, the `claude-haiku-4.5` row moves and the judge keeps `openrouter/anthropic/claude-haiku-4.5`, an ID with no roster row. Without a price source, D4's stop would make every matrix and `smoke-inspect` run exit 2.

**Owner.** `track-model-currency` lands first, and its own `--write` is what can strand the judge, so it owns the case (its D4). In the same edit that re-pins the row, it writes:

```toml
[role_prices."openrouter/anthropic/claude-haiku-4.5"]   # held judge; written by --write
input_price = 1.0
output_price = 5.0
cache_read_price = 0.1
cache_write_price = 1.25   # added to the checker's fields by this change (D6)
```

The figures are illustrative. Its parser guarantees the rest: the judge and persona are always priced through `model_price`, and an entry that no role names or that duplicates a roster ID fails parsing. Later checker runs report `price_drift` on the entry and `--write` refreshes it.

**What this change relies on**, verified as precondition 1.3, never re-implemented:
- `model_price` and `Registry.role_prices` exist, and `estimate_cost` and `price_usage` use them;
- the checker reports and refreshes drift on `[role_prices]` entries, and writes one when a held ID leaves the roster.

**What this change adds:**
- `cache_write_price` is accepted on role-price entries with the same default as on roster rows (D6);
- the checker compares and writes `cache_write_price` for role-price entries exactly as for roster rows, including on the entry its `--write` creates (task 2.4);
- D4's stop treats an ID priced from `[role_prices]` like any priced ID. Such an ID is always a role, so D7's cache telemetry, which covers models under test only, gives it no cache line and no warning; its usage appears in the role observations against its budget (D5) and in the actual spend, priced through `model_price`.

**Alternatives rejected:**
- **A second, array-shaped price table owned here and always seeded for `roles.judge`.** Two changes would own one case. `track-model-currency`'s parser rejects an entry that duplicates a roster ID, which an always-seeded entry would do while the haiku row is on the roster. The agreement and exhaustion tests it needed are already parse-time rules there.
- **A second lookup beside `model_price`.** The estimate and the actual report could then disagree on an off-roster judge.
- **Extending the checker's refresh of role-price entries here.** `track-model-currency` already reports and refreshes their drift; this change adds only the one price field.

### D5. Budgets set as ceilings, plus an observed-vs-budget line

The `[tasks.judge]` budget moves to input 40,000 and output 10,000 per cell-epoch. That covers a sonnet-class judge at about 4.7k output × 2 calls, and honours the accepted disposition "RC5 corrected to per cell-epoch (about 3×)".

The measurements add a nuance. The default haiku judge used about 3.3k output per cell-epoch at most, so the ceiling overstates it by at most about $0.035 per cell-epoch, about $6 across a 180-cell-epoch matrix. This is accepted, because the documented failure of the gate is understating cost.

A new `[tasks.persona]` budget of input 50,000 and output 4,000 applies per dialogue cell-epoch. It is a ceiling over the combined persona and judge usage observed on 2026-08-04, and is provisional.

`parse_registry` reads `[tasks.persona]` explicitly, since unknown keys under `[tasks]` are ignored today (critique 1.10). After each run, `record_spend` prints each role's observed usage per cell-epoch, taken from per-sample model usage of role IDs that differ from the model under test, and flags any budget it exceeds. When a role equals the model under test, its usage cannot be separated and no observation is printed for that row.

**Alternatives rejected:**
- **Budgets per judge model.** Two data points are too few.
- **Merging role observations into `matrix-usage.json` automatically.** It changes the history format, and budget changes should stay deliberate, reviewed registry edits.

### D6. Cache-aware accounting; the estimate stays a ceiling

Changes:
- Roster rows and `[role_prices."<id>"]` entries gain an optional `cache_write_price`, which defaults to `input_price`. The Anthropic rows, and any role-price entry for an Anthropic ID present when this change lands, get the `input_cache_write` value of the `anthropic` vendor endpoint at its standard tier (1.25× input at the 5-minute TTL). That is `track-model-currency`'s D3 price basis; the catalog's headline price is never used.
- `price_usage` takes `(input, output, cache_read, cache_write)`, still looking prices up through `model_price`.
- `collect_usage` sums cache writes.
- The history's per-epoch demand becomes `input + cache_write + cache_read`. Without this, the demand would shrink by the write tokens as soon as Inspect reports them.

The estimate keeps charging full demand at the input price, which is the uncached ceiling. The actual report prints the uncached-equivalent cost beside the actual cost, so the saving shows up as data.

**Both cost paths share one accumulation** (review follow-up). `poe report`'s per-model run cost had its own `(input, output, cache_read)` accumulator, which would have charged every cache write $0 from the first cached run on. The pure `support.billed_usage` now sums Inspect's model usage into `(input, output, cache_read, cache_write)` for both `matrix.collect_usage` and `report.py`, so the published run cost and the matrix's actual spend agree on the same logs. The report's baseline token delta likewise counts full demand (`context_demand`) plus output, so a cached arm no longer looks smaller than an uncached one.

**Alternative rejected:** pricing expected hits into the estimate. An undetected caching regression would then bring back understatement, the exact failure being fixed.

`track-model-currency`'s checker compares input, output and cache-read prices against the vendor endpoint (its D3), for roster rows and role-price entries alike, and writes the same fields into the role-price entry it creates for a held ID (its D4). This change adds `cache_write_price`, mapped to the endpoint's `input_cache_write`, to that one field list, so it is compared, refreshed and written wherever the other price fields are. When the endpoint lists no cache-write price, the field is omitted and the parser's default applies, as that change does for a missing cache-read price.

### D7. Telemetry as dataclasses, read from the logs

`support.CacheStats(model_id, input, cache_write, cache_read, providers)` carries a `hit_rate` property:
- Token counts come from `log.stats.model_usage`.
- Providers come from `call.response.provider` in the samples' model events, counted together with an `unrecorded` bucket.

A pure `support.cache_warnings(stats, registry, mechanism)` warns when a routed Anthropic row's hit rate is below 50%, or when a recorded provider is not one of the pinned providers. The response records a provider's display name, not its slug, so `support.PROVIDER_NAMES` maps each pinned slug to the name OpenRouter records for it: `amazon-bedrock` → `Amazon Bedrock`, `google-vertex` → `Google` (Context). A call served by either is on the pin. `Anthropic`, `Azure` or any other name is off it. The threshold sits below the probe's 80% because real cells include one-shot judge calls and, on haiku, early turns below the minimum prefix; neither can read the cache. The threshold is a named constant. With the mechanism rolled back (`None`) nothing is pinned, so nothing is warned. Its findings are `support.CacheWarning(model_id, kind, detail)` dataclasses (`kind`: `low_hit`, `no_prompt`, `off_pin`), printed through their `__str__`.

**Scope: models under test only** (review follow-up, recorded decision). Telemetry covers each model under test, from the logs it was under test in. Role models get none: their calls are one-shot and unpinned, so a hit rate would measure nothing caching is meant to fix, a warning on them would be noise, and a role sharing a model under test's ID would dilute that row's rate. Their usage is reported against their budgets instead (D5). An ID priced only from `[role_prices]` is always a role, so it gets neither a cache line nor a warning; its serving is unchanged (V1/V2). The spec's telemetry and warning sentences say "model under test" accordingly.

`matrix-cost-*.json` gains `per_model_cache`, `cache_warnings` (one object per finding: model, kind, detail), `cache_mechanism` (the adopted mechanism, `marker`; `null` when rolled back; D2) and the resolved `roles`. The existing keys are unchanged, so earlier summaries still read.

**Known limitation: providers are sampled, not counted for every call.** Inspect 0.3.250's default (`log_model_api=None`) keeps the raw call, the only place the serving provider is recorded, for errors plus the first five calls per model name per sample. A judge or persona call on the same ID uses up one of those slots. The confirmation cell (task 8.2, `measurement.md`) kept 5 of its 19 calls. The provider counts and the `off_pin` warning therefore cover each sample's first five calls, and the rest land in `unrecorded`. Logging every call (`log_model_api=True`) is left to the probe, for two reasons. The option applies to a whole `inspect_eval` call, so scoping it to routed rows would split them into their own call per task, which runs them after the other rows instead of beside them. Setting it for the whole call would log every row's raw calls, at about 4.4 KB each in the uncompressed dump on the confirmation cell. With `allow_fallbacks: false` an off-pin call is not expected at all, so a per-sample spot check is enough.

### D8. Verdict placement

`verdict_cache_reuse(calls, minimum=0.8) -> (passed, explanation)` lives in `harness/l1_checks.py`, following the convention there. `verdict_single_context` is the precedent: an advisory verdict on harness telemetry. `test_repo_conventions.py` then requires its L0 test, which goes in `tests/unit/test_cache_probe.py`.

### D9. Fallback: a Console API key with Inspect's native provider, as a separate change

Inspect's direct `anthropic/` provider sets top-level automatic caching itself (`anthropic.py:452-460`). It is the cleanest compliant metered path, but it means:
- a second billing account;
- an `ANTHROPIC_API_KEY` dev credential in `.env`;
- new logged IDs (`anthropic/claude-haiku-4-5…` instead of `openrouter/anthropic/claude-haiku-4.5`).

The new IDs edit the "Pinned model registry" requirement, which `track-model-currency` owns. They would also leave the shipped haiku verdict's logs uncounted at `report.py:50` until a re-run.

Relaxing the account's ZDR guardrail is no fallback: the user declined it (D2).

Probe 2 passed `marker`, so the fallback is not needed. Had `marker` failed a scored replay under the Bedrock/Vertex pin (`FAIL`, D1), implementation would have stopped for the user to decide, and that rule stands for any later re-probe. An `UNTESTED` result is no verdict: the error is fixed within this change and the probe is proposed again with a fresh estimate. Re-adding `auto` and probing it under the same pin is then one option among others, offered with its own estimate. On a go-ahead, the fallback is proposed as its own change. This change then drops its "Prompt caching on Anthropic matrix rows" requirement through `openspec-update-change`, and archives the telemetry, accounting and gate work.

**Alternative rejected:** OpenRouter BYOK with an Anthropic key. It moves billing but leaves the missing conversation markers unfixed.

### Critique dispositions applied here (final.md §7)

- **Feasibility 1.9.** Configuration is scoped per model, the logged ID is preserved, and the marker uses a hook rather than a renamed provider; see D2 and D3.
- **Cost-policy 2.7.** The provider is pinned in every mechanism, now to the ZDR-compliant global Bedrock and Vertex endpoints instead of `anthropic` (probe 1). Each probe run is approved separately and per model selection, and the serving provider is recorded; see D1, D2 and D7.
- **Feasibility 1.10.** Costs are per cell-epoch, the persona is wired explicitly into `TaskConfig`, and every pricing site uses the same resolution and the same price lookup; see D4, D4a and D5.
- **V1/V2.** The judge and persona keep their model and upstream.
- **F1/V4.** Unchanged here. An error never becomes a pass, and the `retry_on_error` review belongs to Change D.
- **Minor points.** "Caching config scoped per model, with the logged ID preserved" and "Bedrock / provider pinning in the probe" are both folded in.

## Risks / Trade-offs

- **[Bedrock or Vertex may not honour a breakpoint on a list-form tool result]** → OpenRouter must translate a `role: "tool"` message with list content into an Anthropic `tool_result` and keep the nested `cache_control`. Its guide shows no tool-result example, and Inspect avoided this placement. The probe's `marker` run measures acceptance and reads per model; a 400, or no reads beyond the prefix, counts as a failure. Probe 2: Bedrock accepted it and read it back on haiku-4.5 and sonnet-5.5; Vertex is unmeasured. That the model's output is unchanged is UNVERIFIED for list-form tool content (the probe discards the replies).
- **[Per-model support on the pinned upstreams]** → Bedrock's explicit breakpoints produced reads for sonnet-5 on 2026-10-04. Probe 2 measured haiku-4.5 and sonnet-5.5 on Bedrock with conversation breakpoints (both PASS); nothing is measured for opus-5.5 or for any model on Vertex. Vertex serves only on failover, so the probe may never exercise it (probe 2 did not), and a failover turn shows in the recorded providers.
- **[Haiku's 4,096-token minimum]** → The system and tools prefix (about 1.2k tokens) never caches on haiku. The replay's real prompts tokenize below the estimator's 3 characters a token, so haiku's first write lands around call 5 to 7 of 10, and only the 3 to 5 calls after it are scored. The expected steady-state share is about 88–91% if reads work. Probe 2 measured the first write on call 4 and 88.8% over the six calls after it. A first write on the last call fails the probe ("nothing after it can read"), so a replay too short for haiku would read as a failure, not as a pass.
- **[A Vertex failover costs a cache miss]** → OpenRouter does not use sticky routing under an explicit `order`. A turn Bedrock fails is served by Vertex, which holds no cache for the conversation. The turn after it returns to Bedrock, so one failover costs about one write on each side. The recorded providers make it visible, and Vertex is on the pin, so it is not warned.
- **[OpenRouter's guide contradicts the Bedrock note on `auto`]** → Not resolved here, and moot while `marker` passes: `auto` was deleted unprobed (task 8.1). Re-adding it is an option offered with its own estimate if a later re-probe fails `marker` (D9).
- **[The private Inspect symbol (marker only)]** → An L0 guard checks it, and the Inspect version is locked in `uv.lock`. An upgrade fails offline, not silently.
- **[No fallbacks beyond Bedrock and Vertex: an outage of both, or rate limits, stalls a run]** → Inspect retries transient errors, matrix runs are rare and cost-gated, and the telemetry names the provider.
- **[Serving: Bedrock keeps the model under test, Vertex on failover]** → Bedrock served every sampled Anthropic call before this change, so the verdicts' serving conditions barely move. The weights and snapshot are the same on both upstreams, and the harness README notes the pin. The judge stays as it is.
- **[The account's guardrails change]** → If they later admit fewer endpoints, the pin fails at routing with a 404, as probe 1 did. That is an error, never a silent unpinned run, and the probe's `incomplete` check reports it as `UNTESTED` (exit 3), not as a caching failure. In a matrix run, the log of a row whose every call failed reads `success` with no model usage (`fail_on_error=False`). `collect_cache` still reports the routed row with zeroed counts, so its `no_prompt` warning names it, and `record_spend` counts logs with errored samples in its "did not finish cleanly" warning. `poe report` still scores those samples as failed epochs (F1/V4, Change D), so read the warnings before regenerating the report.
- **[A 5-minute TTL across long tool steps, for example document builds]** → Some misses are possible. The hit rate is reported, and a TTL change would need data first.
- **[The ceiling budgets overstate the default haiku judge]** → Accepted (D5). The observed-vs-budget line makes recalibration a data-driven registry edit.
- **[A bump PR merges between `track-model-currency` landing and this change]** and the judge's roster row moves first → That bump's `--write` writes the judge's `[role_prices]` entry in the same edit, so the judge stays priced. The entry then lacks `cache_write_price` and is charged its input price for writes until task 2.4 adds the field; precondition 1.3 records whether such an entry exists.
- **[The 50% warning threshold may misfire on short tasks]** → It is a named constant, revisited after the first cached matrix data.

## Migration Plan

No data migration:
- `matrix-usage.json` keeps its format; only the demand computation changes.
- `harness/models.toml` gains `cache_write_price` on the Anthropic rows and on any `[role_prices]` entry for an Anthropic ID. This change adds no role-price entry; `track-model-currency`'s `--write` creates them.
- Earlier `matrix-cost-*.json` files stay readable.
- Logs keep their IDs, so `poe report` counts the same logs. Its per-model run cost now charges cache writes (previously $0) and its baseline token delta counts cache reads and writes (D6), so regenerating the report over logs that carry cache tokens changes those two figures. That is a correction, not a migration.

To roll back, set `support.CACHE_MECHANISM` back to `None`. `routing_for` then returns an empty routing, `build_model` no longer installs the marker wrapper, and an installed wrapper finds no pinned request to act on. Logs stay countable either way.

## Open Questions

- **Should the estimate show an "expected with caching" line?** That would be decided after several cached matrix runs give stable hit rates.
- **The exact `cache_write_price` values.** They are read at implementation time from the `anthropic` vendor endpoint's `input_cache_write` (the free `/endpoints` request, standard tier, `track-model-currency` D3), not from the catalog's headline price.
- **Is the 50% warning threshold and the provisional persona budget right?** Both are revisited with the observed-vs-budget and hit-rate output of the first cached runs.
- **Opus-5.5 is not probed by default.** Its first matrix run's telemetry confirms the mechanism; `--models` can include it at a bound of $0.34 per mechanism.
- **Assumption:** the response's `provider` value is `Amazon Bedrock` for the `amazon-bedrock` slug (seen in the 2026-10-04 logs) and `Google` for the `google-vertex` slug (the endpoint `provider_name` in the recorded catalog; not yet seen in a response). Probe 2 confirmed the first (`Amazon Bedrock` on all twenty calls); Vertex served none, so the second is still unconfirmed live. A Vertex-served call recorded under another name would raise an `off_pin` warning, which points straight at `support.PROVIDER_NAMES`.
- **Should `auto` be probed under the new pin?** Closed: `marker` passed probe 2 and `auto` was deleted (D2). It reopens only if a later re-probe fails `marker`.
- **Assumption:** the held judge's ID keeps a vendor endpoint in the catalog until Anthropic retires that model. When it goes, `track-model-currency`'s `missing`/`expiring` alert fires, and its role-price entry keeps its last prices, so runs stay priced. Moving the judge is then Change D's decision, and `track-model-currency`'s parse rule against an entry no role names makes that change remove the entry.
