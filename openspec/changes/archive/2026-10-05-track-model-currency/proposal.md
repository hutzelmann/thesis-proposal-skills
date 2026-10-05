# Track model currency and bump the roster to current pins

## Why

The matrix pins are a generation old, and nothing in the repository notices. As of the 2026-10-04 catalog snapshot:

- **The Anthropic pins are outdated.**
  - The roster pins `anthropic/claude-sonnet-5` and `anthropic/claude-opus-5`. OpenRouter has listed `anthropic/claude-sonnet-5.5` since 2026-09-28, at the same $2/$10, and `anthropic/claude-opus-5.5` since 2026-09-22, at $4/$20/$0.20 instead of $5/$25/$0.50.
  - The subscription aliases already resolve to `claude-sonnet-5-5` and `claude-opus-5-5`. So `poe dev --model sonnet` measures Sonnet 5.5, while the verdicts shipped to users are keyed to Sonnet 5.
  - The same lag cost money before: the July and August metered runs used sonnet-4.5 after Sonnet 5 was out, about $0.93 extra.
- **The prices are stale.** They were cached on 2026-08-06, and nothing records their age.
  - `gpt-5.6-sol` is pinned at $5/$30. No endpoint charges that any more, so its estimate is about 2.5× too high.
  - `deepseek-v4-pro` is pinned below its current price, and DeepSeek now serves only the `-0813` snapshot.
- **One pin floats.** `qwen/qwen3.8-max` is no longer in the catalog. OpenRouter silently resolves it to `qwen/qwen3.8-max-0902`. That is exactly the runtime "latest" resolution the registry requirement forbids.
- **Model IDs are hardcoded outside the registry.**
  - `harness/skill_evals.py:75` hardcodes the judge, and `:589` derives the persona from it. `[tasks.judge]` in `harness/models.toml` repeats the judge.
  - Two examples are outdated: `harness/README.md:15` uses `deepseek-v4-flash`, and the issue template uses `claude-sonnet-5`.
  - Each copy goes stale on its own.

Repricing a full default matrix with the pins below moves the estimate from **$100.23 to $95.42**. That comes from the `--estimate-only` path, with no model call:

| Row | Change |
|---|---|
| Opus | −$3.29 |
| sol | −$10.55 |
| terra | +$6.85, from correcting its price basis |
| deepseek | +$2.22 |

The user wants the newest models at all times and deliberate pins. A weekly bump pull request gives both: the PR is the review.

## What Changes

- **Roster bump in `harness/models.toml`.** IDs and prices come from the free public catalog, snapshot 2026-10-04 (22:02 UTC):

  | From | To | $/Mtok in/out/cache read |
  |---|---|---|
  | `anthropic/claude-sonnet-5` | `anthropic/claude-sonnet-5.5` | 2 / 10 / 0.20 (unchanged) |
  | `anthropic/claude-opus-5` | `anthropic/claude-opus-5.5` | 4 / 20 / 0.20 (was 5 / 25 / 0.50) |
  | `openai/gpt-5.6-luna` | `openai/gpt-6-luna` | 0.10 / 0.50 / 0.01. The Azure quarantine note is kept, reworded as not yet re-probed. |
  | `openai/gpt-5.6-sol` | `openai/gpt-6.1-sol` | 2 / 10 / 0.10 (was 5 / 30 / 0.50) |
  | `deepseek/deepseek-v4-pro` | `deepseek/deepseek-v4-pro-0813` | 0.66 / 1.98 / 0.022 (was 0.435 / 0.87 / 0.0036; the price rises) |
  | `qwen/qwen3.8-max` | `qwen/qwen3.8-max-0902` | 2 / 6 / 0.25 (the floating pin becomes explicit) |
  | `openai/gpt-5.6-terra` | unchanged | 2 / 12 / 0.20 (was 1 / 6 / 0.10, the discounted flex-tier row) |
  | `anthropic/claude-haiku-4.5`, `moonshotai/kimi-k3` | unchanged | unchanged |

  - **Price basis.** Prices come from the model vendor's own OpenRouter endpoint at its standard tier. An entry may name the endpoint when the vendor's provider slug differs (qwen is served by `alibaba`).
  - **Price date.** A `prices_as_of` key records the snapshot date.
- **Roles table `[roles]` in the registry.** It is the single source for every model ID used outside the roster:
  - `judge`: the matrix L2 judge, `openrouter/anthropic/claude-haiku-4.5`, unchanged;
  - `persona`: defaults to `judge`;
  - `smoke`: the metered smoke model, which must be an enabled roster entry;
  - `dev_judge`: `claude-sonnet-5-5`, consumed by `add-dev-runner-judge`;
  - `dev_judge_effort`.

  Further rules:
  - The registry rejects floating aliases (`sonnet`, `~…-latest`).
  - **Held role prices.** The judge and persona must always be priced. When the weekly bump re-pins a roster row a held role still names (the next Haiku), `--write` adds a `[role_prices]` entry for the held ID in the same edit and refreshes it weekly. Without it, `fix-openrouter-caching`'s unpriced-role stop would make every metered matrix run exit 2. `support.model_price` is the one price lookup.
  - **BREAKING (registry format):** `[tasks.judge]` keeps only its token budget. A leftover `[tasks.judge].model` fails parsing and points to `[roles].judge`.
  - `skill_evals.py` reads its judge and persona defaults from the registry. The `JUDGE_MODEL` and `PERSONA_MODEL` overrides keep working.
  - Behaviour change: overriding the judge no longer moves the persona with it.
- **New `harness/model_currency.py`.** It uses only the standard library, so CI runs it with plain `python3`. It exposes `main(argv)` and returns findings as dataclasses.
  - **Version line.** For each roster pin and role, it derives the vendor line by wildcarding the version number and ignoring a trailing snapshot date. It skips `:batch`, `:free` and other `:` variants. An entry may set its own `track` pattern or opt out with `track = false`.
  - **What it reports:**
    - a newer model in the line;
    - a pin missing from the catalog;
    - a non-empty `expiration_date`;
    - price drift against the first-party endpoint;
    - informational only, never written: new lines in a vendor namespace the roster uses, created after a maintainer-moved `lines_reviewed_as_of` date. On the 2026-10-04 snapshot that is 12 lines, among them `anthropic/claude-fable-5.1`, which the subscription's `fable` alias already serves.
  - **Subscription IDs** are mapped to catalog IDs: `claude-sonnet-5-5` becomes `anthropic/claude-sonnet-5.5`.
  - **Modes:**
    - `--json` prints the findings as JSON.
    - `--write` edits the registry for the bump PR. It never rewrites the matrix `judge` or `persona`; they are reported as held until a full re-baseline (critique V1).
  - **New poe task:** `poe models` (networked, read-only).
- **New `.github/workflows/model-currency.yml`.** It runs weekly and on manual dispatch, and opens or updates one bump PR from the fixed branch `model-currency/bump` using `GITHUB_TOKEN`.
  - PRs opened with `GITHUB_TOKEN` trigger no `pull_request` runs. So `ci.yml` gains a `workflow_dispatch` trigger, and the currency workflow dispatches CI on the bump branch.
  - The PR body tells the maintainer to run `uv run poe report` and `python3 scripts/sync_shared.py` locally, because `logs/` is gitignored. It also says that new IDs show as untested until a cost-gated run.
  - The workflow never force-pushes over maintainer commits.
- **Stale-model warning at the matrix cost gate (`harness/matrix.py`).** It makes one free catalog request. A network failure prints "model currency unknown". The warning never blocks the run and never changes the estimate. An autouse fixture in `tests/conftest.py` disables the checker's network access for every L0 test, so the two existing `matrix.main` tests, and those parallel changes add, stay offline.
- **New L0 guards:**
  - `tests/unit/test_model_ids.py`:
    - no model ID in harness or scripts code or config outside the registry;
    - no stale or unregistered model ID anywhere else;
    - an explicit allowlist with a reason per entry, including change records and the main specs (scenarios carry illustrative IDs and arrive there by archive);
    - an entry that exempts nothing fails.
  - A test that the shipped verdict data and the README summary list exactly the registry roster.
  - Currency tests over a recorded catalog snapshot in `tests/unit/data/model_catalog/`, with no network.
- **Hardcoded-ID fixes:**
  - `harness/README.md`: the `deepseek-v4-flash` example (now a roster entry), the `JUDGE_MODEL` sentence (names the registry as the source) and the `gpt-5.6-luna` matrix example, anchored by content because `steer-subscription-first`'s opening table shifts the line numbers;
  - `skill_evals.py:8-13` docstring;
  - `matrix.py:11` docstring;
  - `.github/ISSUE_TEMPLATE/skill-defect.yml:71` becomes `claude-sonnet-5-5`, the same edit `fix-troubleshoot-model-match` makes;
  - the `AGENTS.md` currency sentence becomes "run `uv run poe models`", and the Commands list gains the task.
- **Regenerate the shipped verdict files** (`README.md` summary, `docs/model-support.md`, `shared/model-support.json` and its vendored copy) with `poe report` and `sync_shared.py`.

## Capabilities

### New Capabilities

None. Currency tracking is a testing-harness concern.

### Modified Capabilities

- `testing-harness`:
  - MODIFIED "Pinned model registry": roles table, price basis and date, aliases rejected, metered roles always priced (role-price entries for held IDs off the roster), the registry as the only source of model IDs.
  - ADDED "Model identifiers live only in the registry".
  - ADDED "Shipped verdicts list exactly the registry roster".
  - ADDED "Model currency check".
  - ADDED "Weekly model-bump pull request".
  - ADDED "Currency warning at the cost gate".

## Impact

- **Code and config:**
  - edited: `harness/models.toml`, `harness/support.py` (roles parsing), `harness/skill_evals.py` (defaults and docstring), `harness/matrix.py` (gate warning and docstring), `pyproject.toml` (`models` task), `.github/workflows/ci.yml` (`workflow_dispatch`), `AGENTS.md`, `harness/README.md`, `.github/ISSUE_TEMPLATE/skill-defect.yml`;
  - new: `harness/model_currency.py`, `.github/workflows/model-currency.yml`;
  - new tests: `tests/unit/test_model_currency.py`, `tests/unit/test_model_ids.py`, `tests/unit/test_currency_workflow.py`, and the catalog fixture;
  - updated tests: `tests/conftest.py` (offline fixture), `tests/unit/test_support_matrix.py`, `tests/unit/test_eval_wiring.py`.
- **Shipped verdicts:**
  - The six re-pinned rows show as untested.
  - Only one measurement leaves the table: deepseek-v4-pro's partial verdict, one solid task out of ten.
  - Haiku's ❌ and kimi-k3's 🟡 are unchanged.
  - The vendored troubleshoot copy changes accordingly.
- **Money:**
  - No metered call is required.
  - The only metered step is an optional luna re-probe. It is cost-gated, and the estimate is shown first and waits for explicit approval.
  - CI makes one free catalog request plus about ten free endpoint requests per week.
- **Maintainer actions, explicit request only:**
  - enable "Allow GitHub Actions to create and approve pull requests";
  - push;
  - make one `workflow_dispatch` trial run.
- **Coordination:**
  - `add-dev-runner-judge` consumes `roles.dev_judge`, `roles.dev_judge_effort` and `roles.smoke`, and removes the parked `pyproject.toml` smoke entry from the guard allowlist.
  - `fix-openrouter-caching` prices `roles.judge` and `roles.persona` through `support.model_price`, which this change introduces (roster row, then `[role_prices]`), and keeps the `[tasks.judge]` budget.
  - `fix-troubleshoot-model-match` owns `test_troubleshoot_collect.py` and the troubleshoot skill files. It must land before task 6.1 here, because its tests must stop keying on `anthropic/claude-opus-5` before the regeneration step; its tasks 1.1–1.2 do that. The troubleshoot files need no parked guard entry, because their IDs are current until the bump. This change alone swaps the eval-prompt token pair, and that change edits no allowlist entry.
  - `steer-subscription-first` hands over the README's `deepseek-v4-flash` example and the source of its `JUDGE_MODEL` default, `skill_evals.py:8-13` and the `AGENTS.md` currency sentence.
