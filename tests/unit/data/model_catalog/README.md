# Recorded model catalog (L0 fixture)

Recorded on **2026-10-04, 22:02 UTC** from OpenRouter's public, unauthenticated API (no key, no credential):

- `models.json`: `GET https://openrouter.ai/api/v1/models`, trimmed to the entries the currency tests need and to the fields `id`, `canonical_slug`, `created`, `expiration_date` and `pricing` (`prompt`, `completion`, `input_cache_read`).
- `endpoints/<vendor>__<slug>.json`: `GET https://openrouter.ai/api/v1/models/<vendor>/<slug>/endpoints`, one file per model the tests price, trimmed to `name`, `provider_name`, `tag` and `pricing`.
- `registry-pre-bump.toml`: `harness/models.toml` as it stood before the bump this snapshot drove (track-model-currency, task 1.3), so the tests do not depend on the live registry.

`harness/model_currency.py --catalog models.json --endpoints endpoints/` replays this snapshot. A reviewer can reproduce a bump the same way.

Kept on purpose for the tests:

- the anthropic, openai luna/terra/sol/astra, deepseek and qwen3.x lines, including `claude-fable-5` and `claude-fable-5.1` and kimi-k2/k3;
- `:batch` and `:free` variants, `-pro`, `-prime` and `-code` siblings, and `~…-latest` aliases;
- for the new-line cases, an untracked line whose members all predate 2026-08-06 (`openai/gpt-oss-120b`) and IDs with no digit run (`openai/gpt-audio`, `openai/gpt-chat-latest`).

Synthetic entries, clearly not real models, are appended under the `lab/` namespace:

- `lab/judge-1` and the newer `lab/judge-2`: a held judge whose roster row moves on;
- `lab/fading-3`: an expiration date with no successor, and an endpoint without a cache-read price;
- `lab/thirdparty-1`: no endpoint of the vendor's own at the standard tier (only `lab/fast` and a third party).

Every model identifier in this directory is snapshot data, not an example: `tests/unit/test_model_ids.py` exempts the directory.
