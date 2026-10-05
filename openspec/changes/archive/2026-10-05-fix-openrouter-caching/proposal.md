# Proposal: fix-openrouter-caching

## Why

After the subscription-first changes, metered OpenRouter calls on Anthropic models remain for one job: the Anthropic rows of the support matrix, the source of record. On that path prompt caching barely works, and the cost gate understates spend.

**Caching.** Re-pricing the 1,188 logged Anthropic calls with working caching shows that **$11.48 of the $14.93 billed for input was avoidable** (haiku $6.68, sonnet-5 $2.69, sonnet-4.5 $2.11). There are three causes:
- Inspect 0.3.250 places its rolling cache markers only on messages whose content is a list (`inspect_ai/model/_providers/openrouter.py:438-450`). Inspect itself always sends tool and assistant messages as strings (`_openai.py:270-301`), so only the ~1,189-token system and tools prefix is ever marked. Upstream main has the same code, so upgrading Inspect will not fix it.
- Haiku 4.5 does not cache a prefix shorter than 4,096 tokens. That prefix is below the minimum, so haiku cached nothing at all: on 10-04, 0 cache reads out of 1.03M input tokens. Sonnet-5 read 74k of 1.69M.
- Every sampled call was served by Amazon Bedrock. OpenRouter chose the upstream, and the legacy Bedrock integration rejects automatic (top-level) caching for Haiku 4.5.

**Constraint found by probe 1.** The account's zero-data-retention (ZDR) guardrail rules out first-party Anthropic serving. Probe 1 (2026-10-05, `measurement.md`) pinned the rows to `anthropic` and failed at OpenRouter routing with a 404, at $0: the guardrail removed the `anthropic` endpoint, and only the global Amazon Bedrock and Google Vertex endpoints were left.

**Cost gate.** The gate also misprices runs:
- Today's matrix run was estimated at $4.16 and cost $5.24 (+26%).
- A judge given through the `JUDGE_MODEL` environment variable is never priced (`harness/support.py:243`). The 10-04 re-grade used a sonnet-5 judge, at about 4.7k output tokens per call (two calls per cell-epoch, about 9.4k), against a 3,000-token budget per cell-epoch (`harness/models.toml:196-197`).
- The persona on dialogue tasks has no budget at all.
- Once caching works, cache writes would also go unpriced. Inspect takes them out of `input_tokens`, and `price_usage` charges only input, output and cache reads.

Expected effect on a full matrix: about −$23 from caching on the Anthropic rows (final analysis §5). Probe 1 cost $0, because it failed at routing. Probe 2 (2026-10-05, `measurement.md`) ran the `marker` mechanism under the ZDR-compliant pin after you approved its $0.26 estimate: both haiku-4.5 (88.8% cache reads after the first write) and sonnet-5.5 (86.4%) passed, served by Amazon Bedrock, for $0.059. A one-epoch confirmation cell (haiku-4.5 × `import_messy`, approved at its printed $0.39) then cached 92.1% of its prompt tokens through the matrix's own path, for $0.04.

## What Changes

- **Probe first.** A metered, cost-gated probe (`poe cache-probe`) replays a fixed synthetic multi-turn tool conversation. It builds the model the same way the matrix does and measures cache reads per call. It runs only after printing a worst-case estimate and getting explicit approval. It passes when cache reads cover at least 80% of prompt tokens on the calls after the first cache write.
- **Provider pin, ZDR-compliant.** Each Anthropic row is pinned to the global Amazon Bedrock and Google Vertex endpoints, the only ones the account's ZDR guardrail and OpenRouter's default regional-surcharge filter both keep (probe 1): `provider = {"order": ["amazon-bedrock", "google-vertex"], "allow_fallbacks": false}`. Bedrock serves first and Vertex only when Bedrock fails, and no provider outside the list is ever used. The bare slugs never select a regional-surcharge endpoint. The first-party pin (`order = ["anthropic"]`) is dropped, because it cannot route under the guardrail, and relaxing the guardrail was declined.
- **Mechanism `marker`, adopted after probe 2.** The pin, plus a small, self-scoping wrapper around Inspect's OpenRouter marker function. It puts one cache breakpoint on the growing conversation, also when the last message's content is a plain string, as Inspect sends tool results. It acts only on requests that carry the harness's provider pin, so the judge, the persona, every other family and every matrix request sent while the mechanism is rolled back stay untouched. It never marks a judge or persona prompt; it does mark the model under test's single-message first turn of a dialogue, which the later turns read back.
- **Mechanism `auto`, deleted.** The pin, plus automatic caching (a top-level `cache_control`) in the model's own `GenerateConfig.extra_body`. It was selectable in the probe but never probed under the pin: Bedrock, which serves first under the pin, rejects automatic caching for Haiku 4.5 in its legacy integration. Adopting `marker` deleted it (task 8.1).
- **Scoping.** Routing and caching settings are applied **per model, to Anthropic rows only**. `matrix.py` passes `Model` objects for those rows and keeps bare IDs for every other family. The logged `eval.model` stays equal to the registry ID, so `report.py:50` keeps counting the logs. The judge and the persona keep their current serving setup (critique V1/V2), and no one-shot judge or persona prompt ever gets a breakpoint. Only a mechanism the probe has passed is used; setting it back to none rolls the Anthropic rows back to unrouted, uncached requests.
- **Fallback (needs your go-ahead).** If no mechanism passes, work stops and you decide on a Console API key with Inspect's native `anthropic/` provider. Its caching is proven in code (`anthropic.py:452-460`). It would be a second billing account and would change the logged IDs of Anthropic rows, so it becomes its own change. In that case this change archives the telemetry and gate work without the caching requirement.
- **Cache telemetry.** `record_spend` and `matrix-cost-*.json` report, per model, the cache-hit rate (cache reads ÷ all prompt tokens), cache writes and reads, the serving providers recorded in the log, and what caching saved. The summary and each log's metadata name the caching mechanism in use, which the logged model arguments alone cannot show. A warning appears when an Anthropic row's hit rate falls below 50%, or when a call was served by a provider outside the pin. Amazon Bedrock and Google Vertex are both on the pin.
- **Cost-gate recalibration:**
  - The estimate prices the judge on every cell-epoch, and the persona on dialogue cell-epochs. Their model IDs are resolved exactly as the eval resolves them: the registry roles table from `track-model-currency`, then the `JUDGE_MODEL`/`PERSONA_MODEL` overrides.
  - One price lookup serves the estimate and the actual spend: `support.model_price` from `track-model-currency` (the roster row, enabled or not, else the `[role_prices."<id>"]` entry). This change adds no second lookup.
  - A role model without registry pricing stops the run before the confirmation prompt. `--yes` does not bypass this.
  - **Held roles stay priced through `track-model-currency`, which owns the case.** Its weekly bump re-pins roster rows in place but holds the judge and persona. When the next Haiku ships, its `--write` adds a `[role_prices."<id>"]` entry for the judge's ID in the same edit and refreshes that entry's prices weekly. Its parser also refuses a registry whose judge or persona is unpriced. So the stop above fires only for an environment override that names an unpriced ID, never for the held judge.
  - The judge budget per cell-epoch rises to 40k input / 10k output, sized to cover a sonnet-class judge. A new persona budget applies to dialogue tasks.
  - After each run, the observed judge usage is printed against the budget.
  - Roster rows and `[role_prices]` entries gain an optional `cache_write_price`, which defaults to the input price. The currency checker compares and writes it like the other price fields, and actual spend prices cache writes. The usage history records full context demand: input + cache writes + cache reads.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`:
  - MODIFIED "Cost-gated matrix execution": role models are priced, including environment overrides, through the one lookup `track-model-currency` introduces, shared with the actual spend; an unpriced role stops the run before the prompt; cache writes are priced on roster and role-price entries; cache telemetry is persisted. Held-role pricing itself stays in `track-model-currency`'s "Pinned model registry" and "Model currency check".
  - ADDED "Prompt caching on Anthropic matrix rows".
  - ADDED "Cache reuse probe".

## Impact

- **Code:**
  - `harness/support.py`: `cache_write_price` on roster rows and `[role_prices]` entries, role pricing through `track-model-currency`'s `role_model` and `model_price`, `CacheStats`, routing spec.
  - `harness/model_currency.py`: `cache_write_price` joins the price fields the checker compares and writes, for roster rows and `[role_prices]` entries alike. Creating and refreshing role-price entries stays `track-model-currency`'s.
  - `harness/matrix.py`: model construction, telemetry, role gate.
  - `harness/report.py`: the per-model run cost prices cache writes through the accumulation the matrix uses, and the baseline token delta counts full demand.
  - `harness/cache_probe.py`: new, with `main(argv)`.
  - `harness/l1_checks.py`: `verdict_cache_reuse`.
  - `harness/openrouter_cache.py`: new, the `marker` mechanism.
  - `harness/matrix.py` installs the marker wrapper when it builds a model whose routing asks for the breakpoint. `harness/skill_evals.py` is not touched: no request it builds on its own carries the pin.
- **Registry (`harness/models.toml`):** `cache_write_price` on the Anthropic rows and on any `[role_prices]` entry for an Anthropic ID, the `[tasks.judge]` token budget, and a new `[tasks.persona]` budget. Model IDs, the roles table and the `[role_prices]` entries themselves belong to `track-model-currency`, and this change adds or removes none of them.
- **Tasks and docs:** a `pyproject.toml` `cache-probe` poe task; the matrix section of `harness/README.md`; one command line in `AGENTS.md`, pending task 9.2 (it waits for the user's own instruction, since `AGENTS.md` is the agent-instruction file).
- **Tests:** `tests/unit/test_support_matrix.py`, `tests/unit/test_model_currency.py` (`cache_write_price` compared and written, including on the entry `--write` creates for a held ID, over a synthetic catalog), a new `tests/unit/test_cache_probe.py`, and a new `tests/unit/test_openrouter_cache.py`, which pins the request body the marker sends. None of them call a model or open a socket.
- **Spend:** probe 1 (`auto`, first-party pin) cost $0, because it failed at routing. Probe 2 (`marker`, Bedrock/Vertex pin) cost $0.059 against its approved worst case of $0.26. The optional confirmation cell (task 8.2) printed an estimate of $0.39. You approved it, and it cost $0.04, because the estimate prices every prompt token as uncached input.
- **Order:** this change runs after `steer-subscription-first`, `track-model-currency` and `add-dev-runner-judge`. It does not touch the dev runner, the subscription roles, or the matrix judge/persona choice (deferred Change D).
