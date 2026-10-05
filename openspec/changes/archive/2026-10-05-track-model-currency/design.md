# Design

## Context

The proposal (Why) gives the evidence. The parts of the current state that shape the design:

- **`harness/models.toml` is the roster.**
  - `harness/support.py` parses it; this module is pure and uses only the standard library (`tomllib`, `dataclasses`).
  - `harness/matrix.py` runs the cost gate and Inspect.
  - `harness/report.py` builds the README summary, `docs/model-support.md` and `shared/model-support.json` from the newest log per (roster ID, task). Logs whose model is not on the roster are ignored (`report.py:50`). A re-pinned row therefore shows as untested and never mixes old and new measurements.
  - `logs/` is gitignored, so only a machine that holds the logs can regenerate those files.
- **The judge's model ID lives in three places.** `[tasks.judge].model` in the registry prices it (`support.py:243`). `skill_evals.py:75` hardcodes it. `skill_evals.py:589` copies the judge, environment override included, into the persona. `skill_evals.py` is on the coverage omit list, so any logic placed there is invisible to L0.
- **`harness/` and `scripts/` are both on the test `pythonpath`.** At runtime, `python harness/matrix.py` sees only `harness/`.
- **Two existing L0 tests call `matrix.main` against the real registry and inject nothing:** `test_matrix_gate_declined_makes_no_metered_call` (`matrix.main([])`) and `test_matrix_estimate_only_exits_clean` (`matrix.main(["--estimate-only", "--tier", "cheap"])`), at `tests/unit/test_support_matrix.py:420-436`. `add-dev-runner-judge` (its 2.7) and `fix-openrouter-caching` (its 3.3) add more. `tests/conftest.py` is the only conftest.
- **No main spec names a model ID today** (checked with grep). Archiving a change syncs its scenarios into `openspec/specs/**`, and a main spec changes only through a change record.
- **CI** (`.github/workflows/ci.yml`) runs on `push` to main and on `pull_request`. GitHub creates no new workflow run for events caused by `GITHUB_TOKEN`, except `workflow_dispatch` and `repository_dispatch`. A PR the bot opens therefore gets no CI unless something dispatches it.
- **OpenRouter's public catalog** (`GET /api/v1/models`, no key) returns `id`, `created`, `expiration_date`, `canonical_slug` and a headline `pricing` for every model.
  - The headline price belongs to an endpoint OpenRouter picks, and for open-weight models it moves between third-party providers. On 2026-10-04, kimi-k3's headline was InferenceNet fp4 (0.72/14) and deepseek-v4-pro-0813's was Wafer (0.55/4.2/0.45).
  - The per-model `GET /api/v1/models/{id}/endpoints`, also free, lists every endpoint with its provider tag and price.
  - Both shapes were recorded on 2026-10-04 in the scratchpad (`currency/or_models_fresh.json`, `currency/ep_*.json`).
- **The subscription CLI reports dashed IDs.** Claude Code 2.1.284 resolves `sonnet`, `opus` and `haiku` to `claude-sonnet-5-5`, `claude-opus-5-5` and `claude-haiku-4-5-20251001`. The catalog keys the same models as `anthropic/claude-sonnet-5.5`, and so on.
- **The parallel changes fix the boundaries** (cross-change contract):
  - `steer-subscription-first` lands first and hands over specific lines.
  - `add-dev-runner-judge` consumes `roles.dev_judge`, `roles.dev_judge_effort` and `roles.smoke`.
  - `fix-openrouter-caching` owns how the cost estimate charges the judge and persona, overrides included, and the `[tasks.judge]` token budget. The held-role price source is this change's (D4).
  - `fix-troubleshoot-model-match` owns `skills/proposal-troubleshoot/**` and `tests/unit/test_troubleshoot_collect.py`.

## Goals / Non-Goals

**Goals:**

- Every model ID the harness uses comes from one file, and an L0 guard keeps it that way.
- The roster carries the newest model of each tracked line at a documented price basis. A proposal to change that arrives weekly as a reviewable PR, never as a silent runtime change.
- A stale pin is visible exactly where money is about to be spent: the matrix cost gate.
- The changes needed after a bump (report regeneration, docs that name the outgoing ID) are enforced by CI, not left to the PR description.

**Non-Goals:**

- **Moving the matrix judge or persona** to another model or backend. That is deferred Change D. Here they are only moved into the roles table, with their values unchanged.
- **Cost-estimate recalibration, role-override pricing and token budgets, caching, and provider pinning.** These belong to `fix-openrouter-caching`. The price source for held roles (`[role_prices]`, `support.model_price`) is this change's, under D4.
- **Matching model names in the troubleshoot skill.** This belongs to `fix-troubleshoot-model-match`.
- **Adding new lines to the roster automatically**, such as `anthropic/claude-fable-5.1` or `openai/gpt-6-astra`. The checker writes only to lines the registry already has. It reports a new line in a roster vendor namespace as an informational `new_line` finding (D2), so the roster decision is prompted but stays the maintainer's.
- **Running any model from CI, and auto-merging.**

## Decisions

### D1. The checker lives at `harness/model_currency.py`, uses only the standard library, and reuses `support.parse_registry`

The brief suggested `scripts/model_currency.py`. The checker moves to `harness/` because the cost gate (`harness/matrix.py`) must call it in-process, and at runtime `python harness/matrix.py` can import only from `harness/`.

`support.py` is already pure and stdlib-only. The checker therefore reuses the registry parser instead of growing a second one, and CI still runs it with plain `python3 harness/model_currency.py` (ubuntu-latest ships Python 3.12, and `tomllib` needs 3.11). An L0 test asserts that `model_currency.py` and `support.py` import only `sys.stdlib_module_names` plus each other, so the "plain python3" property cannot erode.

Structure, following the repository's conventions:

- `main(argv)` is the entry point, and findings are a frozen dataclass:
  - `subject`: `roster:<id>`, `role:<name>` or `line:<glob>`;
  - `kind`: `newer`, `missing`, `expiring`, `price_drift`, `no_vendor_endpoint`, `held`, `untracked` or `new_line`;
  - `pinned`, `proposed`, `detail`, `writable`.
- Pure functions handle line derivation, comparison, price comparison and the text edit. One thin function, `fetch_json(url, timeout)`, does the network IO, behind an injectable `fetch`. Callers resolve the default at call time through the module attribute, never by binding it at import, so the L0 conftest fixture (D9) reaches every path.
- Exit status: 0 when the roster is current or there are only informational findings (`held`, `untracked`, `new_line`), 1 when there are actionable findings, 2 when currency is unknown (catalog unreachable or malformed).
- `--json` prints `{source, fetched_at, findings[]}`.
- `--write` applies the writable findings.
- `--pr-body FILE` writes the Markdown description the workflow uses.
- `--catalog FILE` and `--endpoints DIR` replay a recorded snapshot. The L0 tests and a reviewer reproducing a PR both use them.

Rejected alternatives:

- `scripts/` plus `sys.path` manipulation in `matrix.py`, which `eval_export.py` does today. It is the pattern the conventions are trying to stop.
- `scripts/` plus `matrix.py` spawning the script as a subprocess. That puts a second process and a JSON hop on a warning, and the warning path would be invisible to coverage.
- A uv-managed script with dependencies such as `httpx` or `tomlkit`. CI would need `uv sync` for a weekly catalog read.

### D2. The version line is derived by wildcarding the first version number, and successors are ordered by (version, catalog `created`)

For a pin `vendor/name`:

1. Drop the `openrouter/` prefix. Map a subscription-form ID to its catalog form: turn each dash between two digits into a dot, drop a trailing `-YYYYMMDD`, and prefix `anthropic/`. For example, `claude-haiku-4-5-20251001` becomes `anthropic/claude-haiku-4.5`.
2. Strip a trailing snapshot token, one of `-\d{4}`, `-\d{6}`, `-\d{8}` or `-\d{2}-\d{2}`, and keep it as the snapshot.
3. Replace the first maximal `\d+(\.\d+)*` run with a wildcard. The result is the line, for example `openai/gpt-*-luna`, `deepseek/deepseek-v*-pro`, `qwen/qwen*-max` or `moonshotai/kimi-k*`.
4. The line's members are the catalog IDs in the same vendor namespace that match the line after their own step 2. IDs with a `:` suffix (`:batch`, `:free`, …) and `~`-prefixed floating aliases are excluded.
5. A member is newer if its version tuple is higher, or if the version is equal and its `created` is later than the pin's. The newest member is proposed.

Using `created` for snapshot order avoids parsing MMDD tokens, whose year is ambiguous. A pin that is missing from the catalog (the qwen case) is reported as `missing`, with the newest member of its line proposed.

On the 2026-10-04 snapshot this gives:

- sol → `gpt-6.1-sol`, chosen over `gpt-6-sol`;
- luna → `gpt-6-luna`;
- deepseek → `deepseek-v4-pro-0813`;
- qwen → `qwen3.8-max-0902`;
- sonnet and opus → 5.5;
- terra, haiku and kimi-k3 stay current.

Siblings such as `-pro`, `-prime`, `-code` and `-thinking` fall outside each line by construction.

An entry may override the derived line with `track = "<glob with one *>"`, or opt out with `track = false`. An opted-out entry is reported as `untracked` on every run. This is the durable way to decline a bump, because closing the PR alone would bring it back the following week.

**New lines are reported, never written.** The same derivation (steps 2–4) applied to every catalog ID in a vendor namespace the registry uses gives the namespace's lines. A line is *known* when a registry entry or role derives it, opted out or not. An unknown line with at least one member created after the top-level `lines_reviewed_as_of` date is reported once, as `new_line` with subject `line:<glob>` and its newest member as `proposed`. It is informational and never writable. IDs with no digit run derive no line and are ignored.

`lines_reviewed_as_of` is the maintainer's acknowledgement. Only a hand edit moves it; `--write` never does. A new line therefore stays in every weekly summary and bump-PR body until the maintainer either adds a roster entry for it or moves the date. It is seeded at `2026-08-06`, the registry's last reconciliation. On the 2026-10-04 snapshot that reports 12 lines: `anthropic/claude-fable-*` (newest `claude-fable-5.1`, also reachable through the subscription's `fable` alias), `deepseek/deepseek-v*-flash`, `deepseek/deepseek-v*-flash-vision-exp`, `openai/gpt-*-astra`, `-astra-pro`, `-luna-pro` and `-sol-pro`, and five `qwen/qwen*-…` lines (`-flash`, `-omni-flash`, `-27b`, `-2.4t-a95b`, `-max-prime`).

Rejected alternatives:

- OpenRouter's `~vendor/…-latest` aliases. They float by definition, and the registry requirement forbids runtime "latest".
- Parsing `canonical_slug`. Its shape is inconsistent (`claude-4.5-haiku-20251001` against `claude-sonnet-5.5-20260928`).
- A hand-maintained successor map. It goes stale exactly the way the pins did.
- A vendor-family regex list in the checker. A new vendor in the roster would silently be ignored.
- **Writing new lines into the roster.** Which tier a new family occupies, and whether the matrix can afford it, is a roster decision. The weekly PR prompts it; it does not make it.
- **`prices_as_of` as the new-line cutoff.** It moves on every write, so this change's own bump (task 6.2) would hide Fable 5.1 before anyone had reviewed it.
- **Reporting every unknown line in a roster namespace.** The anthropic and openai namespaces carry dozens of legacy lines; the signal would drown.
- **Failing the scheduled run on a new line.** A new model is not a defect, and a run that is red for a non-defect teaches people to ignore red.

### D3. The price basis is the vendor's own endpoint at its standard tier

- **Source.** Prices are read from `/endpoints`, taking the endpoint whose tag equals the vendor namespace (`anthropic`, `openai`, `deepseek`; `moonshotai/…` when only one vendor tag exists). Higher tiers (`/fast`) and discounted tiers (`/flex`) are skipped.
- **Override.** `price_endpoint = "<tag>"` names the endpoint where the provider slug differs. Qwen is served by `alibaba`.
- **No vendor endpoint.** If the vendor serves the model on no endpoint of its own, the checker reports `no_vendor_endpoint` and leaves the price as it is. Old `deepseek-v4-pro` is an example: DeepSeek now serves only `-0813`.
- **Drift.** It is reported when any of input, output or cache-read differs by more than 0.5% relative. First-party prices move in discrete steps, so the tolerance only absorbs float noise.
- **Missing cache-read price.** When the endpoint has none, `cache_read_price` is omitted, and the parser already defaults it to the input price.
- **Which ID is priced.** Prices are checked for the ID an entry will carry after the run. For an entry with a writable bump, that is the successor's endpoint. Drift on the outgoing pin is not reported separately, because it is noise once the pin leaves, unless a held role still names it: then its price moves into `[role_prices]` (D4) and is checked there under the same basis.
- **Price date.** A top-level TOML date, `prices_as_of = 2026-10-04`, replaces the date in the header comment. It is parseable, so `--write` can update it.

Consequences on 2026-10-04:

- Anthropic prices are unchanged, and they match the billed spend (97.8% of all spend; haiku's $11.23 reproduces at 1/5).
- terra rises from 1/6/0.1, which is the `openai/flex` row, to 2/12/0.2 (+$6.85 on a full-matrix estimate). Whether default routing ever selects flex is UNVERIFIED, and pricing the standard tier errs toward over-estimating, the safe direction after RC5.

Rejected alternatives:

- The catalog headline price. It moves between providers from week to week, which would churn the bump PR and price a provider the account may never be routed to.
- The cheapest endpoint. That is the flex and fp4 rows, so estimates would come out low, the RC5 direction.
- The most expensive endpoint. That is the `/fast` tiers, roughly 2× too high, the same fault as the stale sol pin.

### D4. A `[roles]` table is the single source of non-roster model IDs

```toml
prices_as_of = 2026-10-04
lines_reviewed_as_of = 2026-08-06   # moved by hand only (D2 new lines)

[roles]
judge = "openrouter/anthropic/claude-haiku-4.5"   # matrix L2 judge — held (Change D)
# persona defaults to judge
smoke = "openrouter/anthropic/claude-haiku-4.5"   # must be an enabled roster entry
dev_judge = "claude-sonnet-5-5"                   # subscription CLI full ID, never an alias
dev_judge_effort = "medium"

# [role_prices."<id>"] appears only when a held role names an ID the roster has
# left; --write creates and refreshes it (see "Held role IDs that leave the roster").

[tasks.judge]          # token budget per cell-epoch only (fix-openrouter-caching recalibrates)
input = 40000
output = 3000
```

Parsing rules:

- `support.parse_registry` returns `Registry.roles`, a frozen dataclass, and `Registry.role_prices`, a mapping from ID to the same pricing fields a `[[models]]` row carries (`input_price`, `output_price`, optional `cache_read_price`). `fix-openrouter-caching` later adds an optional `cache_write_price` to rows and entries alike, and to the checker's price fields.
- `TaskConfig.judge_model` keeps its name and its callers, and is now filled from `roles.judge`.
- `support.model_price(registry, model_id)` is the one price lookup: the roster row with that ID (enabled or not), else the `[role_prices]` entry, else `None`. `estimate_cost` uses it, so a held judge that has left the roster stays priced.
- `[tasks.judge].model` is rejected with a message that names `[roles].judge`, so the duplicate cannot come back.
- Every roster and role ID is rejected if it is:
  - a bare `haiku`, `sonnet`, `opus` or `fable`;
  - `~`-prefixed;
  - ends in `-latest`.
- `smoke` must be an enabled roster ID.
- `judge` and `persona` must be priced through `model_price`. A registry whose metered roles cannot be priced fails at parse time, naming the role, instead of at the cost gate.
- A `[role_prices]` entry that no role names, or that duplicates a roster ID, is rejected. The table cannot become a second roster or keep a dead price.
- `dev_judge_effort` must be one of `low|medium|high|xhigh|max`, the values `claude --help` lists in 2.1.284.

**Held role IDs that leave the roster.** The weekly bump replaces roster rows in place (D10) but holds the judge and persona (V1). When the next Haiku ships, the haiku row moves and the judge stays on an ID with no `[[models]]` row. `fix-openrouter-caching` makes an unpriced role a hard stop that `--yes` cannot bypass, so without a price source every matrix and smoke-inspect run would exit 2. This change owns that case:

- When `--write` re-pins a roster entry whose outgoing ID a held role still names, it writes `[role_prices."<outgoing id>"]` in the same edit, priced at that ID's vendor endpoint under the D3 basis.
- Later runs check that entry for `price_drift` like a roster price, and `--write` refreshes it. Refreshing a held role's price is not moving the role: the ID stays.
- The change that eventually moves the role (Change D) deletes the entry; the parse rule above makes a forgotten one fail.
- `fix-openrouter-caching` consumes this: it reads prices through `support.model_price`, owns no price table of its own, and adds only `cache_write_price` (coordination, see Open Questions).

Resolution:

- `support.role_model(roles, name, environ)` is pure and L0-tested.
- `skill_evals.py` calls it:
  - `JUDGE_MODEL` resolves to `JUDGE_MODEL` from the environment, else `roles.judge`;
  - `PERSONA_MODEL` resolves to `PERSONA_MODEL` from the environment, else `roles.persona`.
- `test_eval_wiring.py` asserts that the module's values equal the resolver's output.

Seed values:

- `dev_judge_effort = "medium"`. It is a rubric grade with a step-by-step instruction, and pinning it blocks the inherited host `CLAUDE_EFFORT=xhigh` (critique V3). `add-dev-runner-judge` owns its calibration and changes it here if needed.
- `dev_judge = "claude-sonnet-5-5"`, per user decision 2. Anthropic publishes no dated ID for Sonnet 5.5, so this undated full ID is the most specific one there is (critique minor point "full-ID reproducibility"). `add-dev-runner-judge` fails closed when the served model differs.

Rejected alternatives:

- Keeping `[tasks.judge].model` and adding `[roles]` beside it: two sources of truth.
- Putting `dev_judge` in `[[models]]`: it would become a matrix row, which final.md §4 step 4 rules out.
- Roles as environment defaults in `.env.example`: not tracked state, and invisible to the checker.
- **`--write` declining to bump a roster row that a held role names**, reporting it `held`. No new table, but the matrix's haiku row would freeze until Change D, against user decisions 4 and 5 (always the newest models).
- **Keeping the outgoing row as `enabled = false`** to carry its price. Disabled rows still render in the README (D10).
- **Leaving the case to `fix-openrouter-caching`.** That change deferred a price-only table "until a role needs one" while this one deferred it to that change; the first Haiku bump would have found the gap as an exit 2 on every metered run.

### D5. A judge override no longer moves the persona

Today `PERSONA_MODEL` defaults to `JUDGE_MODEL` after the override is applied. So `JUDGE_MODEL=x` for a re-grade experiment also swaps the student simulator in dialogue tasks. Critique V5 (accepted) holds that a persona change changes what dialogue tasks measure. Each override now applies to its own role only. This is a behaviour change for anyone who relied on the cascade, so it is recorded in the spec.

Rejected: preserving the cascade for compatibility. It is exactly the coupling V5 warns about, and no matrix run sets either override.

### D6. The model-ID guard combines a no-literal rule for code with a must-be-current rule for prose

`tests/unit/test_model_ids.py` scans `git ls-files`. Tokens are recognized two ways:

- a base pattern of the vendor families the harness has used: `claude-(haiku|sonnet|opus|fable)-\d…`, `gpt-\d…`, `deepseek-v\d…`, `qwen\d…`, `kimi-k\d…` and `gemini-\d…`, with optional `vendor/` and `openrouter/` prefixes, matched maximally;
- the D2 line of every registry entry, so that a new vendor is covered automatically.

The rules:

- **Rule A, no literal.** In `harness/**/*.py`, `scripts/**/*.py`, `harness/**/*.toml` other than `models.toml`, `pyproject.toml` and `.github/workflows/*.yml`, any token is a violation. Docstrings and comments count too. A model name in code is either a default (a second source of truth) or an example that will rot.
- **Rule B, current or nothing.** In every other tracked file, a token must resolve to a current roster entry or role, under any accepted spelling: provider-qualified, provider-stripped, or the subscription form via the D2 mapping. Docs keep usable examples, but an example cannot outlive its pin. It fails in the bump PR's CI and names the file. That is also how the PR finds every doc still citing an outgoing ID.

The allowlist lives in the test. Each entry is a path glob, or a (path, token) pair, and carries a reason:

- **Permanent entries:**
  - `harness/models.toml`;
  - `openspec/changes/**`, because change records describe ID transitions, archive included;
  - `openspec/specs/**`, because spec scenarios carry illustrative IDs, archiving a change syncs them there (this change's own scenarios name `openai/gpt-5.6-sol` and `claude-sonnet-5-5`; `fix-troubleshoot-model-match`'s scenarios use synthetic `lab/example-*` IDs and need no exemption), and a main spec changes only through a change record, so a weekly bump PR could never fix one. Without this entry `main` would go red at this change's own archive commit;
  - the README's generated model-support region (only the region between the markers is stripped before scanning);
  - `docs/model-support.md`, `shared/model-support.json`, `skills/*/references/model-support.json` and `skills/*/evals/evals.json` (generated);
  - `tests/unit/data/model_catalog/**` (recorded catalog);
  - `tests/unit/test_troubleshoot_collect.py` (normalization test data, which deliberately keeps old IDs for its version-guard tests);
  - the token-level pair for the `troubleshoot_model_rung` prompt in `harness/skill_evals.py`. The scenario must name the model whose shipped verdict the rung looks up. After `fix-troubleshoot-model-match` the spelling is `claude-haiku-4-5-20251001`; before it, `claude-haiku-4.5`.
- **Parked entries** name the change that removes them. There is one: `pyproject.toml` `smoke` (`--models claude-haiku-4.5`), removed by `add-dev-runner-judge`, which moves it to `matrix.py --smoke` reading `roles.smoke`.
- **Hand-off with `fix-troubleshoot-model-match`.** That change must land before this change's task 6.1, because the regeneration breaks today's troubleshoot tests. Because this change commits once, at 8.5, its guard never reaches `main` before `fix-troubleshoot-model-match` does.
  - **The troubleshoot files need no entry.** Before the 6.2 bump, the old `claude-opus-5` example and the issue template's `claude-sonnet-5` resolve to current roster pins, so Rule B passes. The replacement spellings `claude-haiku-4-5-20251001` and `claude-sonnet-5-5` resolve to the haiku row and to `roles.dev_judge`. After the bump, the old example is already gone, because 6.1 waits for that change.
  - **The eval-prompt pair has one owner.** Rule A always needs the `skill_evals.py` (path, token) pair. Task 4.2 writes it with the spelling it finds. If it finds `claude-haiku-4.5`, this change swaps it to `claude-haiku-4-5-20251001` in 6.1 after merging `main`. The exhaustion check fails until the swap is done, and that failure is the reminder.
- **Exhaustion check.** A parked entry or a (path, token) entry that exempts nothing fails the test, so the allowlist cannot accumulate dead exemptions. Category globs, such as generated outputs, change records and main specs, are exempt from the check. After a regeneration the generated outputs name only current models, yet they must stay exempt for the next bump, where D7 gives the clearer failure.

Rejected alternatives:

- **Rule B alone.** It catches a hardcoded current default only at the next bump, and the contract says code carries no IDs.
- **Rule A everywhere.** The issue template has to show the reported ID (`claude-sonnet-5-5`), and docs need runnable examples.
- **Checking docs against catalog membership.** L0 has no network, and an untracked model in an example rots unseen. This is also why the README's `deepseek-v4-flash` example becomes a roster entry rather than the `deepseek-v4.1-flash` that final.md §2 suggested.
- **Synthetic `lab/` IDs in spec scenarios instead of allowlisting `openspec/specs/**`.** It would fix only this change's deltas, not those of parallel changes, and the subscription-mapping scenario needs the real `anthropic/` namespace the mapping adds. Scenarios are examples of a rule at the time it was written, the same standing as change records.

### D7. CI enforces regeneration: shipped verdicts must list exactly the roster

A new L0 test compares the keys of `shared/model-support.json` and the pinned-ID column of the README's generated region with the roster IDs minus `openrouter/`. A bump PR is therefore red until the maintainer runs `uv run poe report` and `python3 scripts/sync_shared.py` on a machine with the logs and pushes the result to the bump branch. `main` stays complete, which matters because `main` is the release channel. The PR description explains the red check, and the test carries the explanation.

Rejected: relying on the PR description alone. That is exactly the kind of instruction that gets skipped on a busy week.

### D8. The weekly workflow: one PR, a fixed branch, a token with least privilege, and dispatched CI

`.github/workflows/model-currency.yml`:

- **Triggers:** `schedule` (Mondays, after the install-check slot) and `workflow_dispatch`.
- **Settings:** `concurrency: model-currency`; permissions `contents: write`, `pull-requests: write` and `actions: write`. The last one is needed to dispatch CI.

Steps:

1. Check out main. Run `python3 harness/model_currency.py --write --json --pr-body …`, then write the findings to `$GITHUB_STEP_SUMMARY`.
2. If the registry is unchanged:
   - close an open bump PR with a comment ("main is current");
   - fail the run if an alert exists, meaning `missing` or `expiring` with no writable successor;
   - otherwise stop.
3. If the registry changed:
   - Check the remote branch `model-currency/bump` for commits not authored by `github-actions[bot]`. If it has any, leave it, comment the new findings on the PR, and stop. This mirrors Dependabot, so the maintainer's regenerated report is never overwritten.
   - Otherwise, rebuild the branch from main with one bot commit and force-push it.
4. Create or update the PR with `gh pr list --head`, then `gh pr create` or `gh pr edit`, always with `--body-file`.
5. Run `gh workflow run ci.yml --ref model-currency/bump`. `ci.yml` gains `workflow_dispatch:`, and `workflow_dispatch` is the one event a `GITHUB_TOKEN` may trigger.

The PR description lists:

- each finding with the pinned and proposed ID and the price change;
- the held roles (judge and persona, Change D), and any `[role_prices]` entry the run created because a held role's ID left the roster (D4);
- the new lines in roster vendor namespaces (D2), as a roster decision for the maintainer, with the two ways to clear them: add a roster entry, or move `lines_reviewed_as_of`;
- the tracked files that still name an outgoing ID (`git grep -l`, best effort), which the D6 guard will flag;
- the regeneration commands, with the reason that `logs/` is gitignored;
- that new IDs render untested until a cost-gated matrix run, whose estimate is shown and waits for approval;
- for a subscription-role bump, the free check that `claude -p --model <new id>` reports that same ID in `modelUsage`;
- the fallback: if CI's checks do not appear on the PR, close and reopen it.

The workflow calls no model, reads no secret beyond `GITHUB_TOKEN`, and never merges.

Rejected alternatives:

- A personal access token or GitHub App token, so that `pull_request` CI triggers normally. It needs a stored credential, against the repository's credential rule, for a convenience.
- Running `uv run poe test` inside the currency workflow. It would duplicate CI's job set (no Windows job, no build jobs) and break the rule that the gate is the poe task, not a restatement of it.
- One PR per model, as Dependabot does per dependency. Bumps are reviewed together because they share one regeneration, and nine PRs would mean nine regenerations.
- Auto-closing on a maintainer's close without a durable decline. Declines go through `track` (D2) instead.

### D9. The cost gate warns from one catalog request and never blocks

`matrix.main` calls `model_currency.gate_warnings(registry, selected_models, fetch=...)`:

- **Scope:** only the catalog list, with a 5-second timeout and no endpoint requests (no prices at the gate). It covers the selected models plus the judge and persona roles the run will use.
- **Output:** it returns plain lines, printed right after the estimate, so they sit directly above the confirmation prompt. They also print under `--estimate-only`.
- **Offline:** any exception is caught and becomes one line, "model currency unknown (catalog unreachable: <reason>)".
- **No side effects:** exit status and estimate are untouched.
- **L0 is offline by construction.** An autouse fixture in `tests/conftest.py` replaces `model_currency.fetch_json` for every test with a function that raises `OSError("network disabled in L0 tests")`. Any test that reaches the gate without its own substitute, including the two existing `matrix.main` tests (Context) and the ones `add-dev-runner-judge` and `fix-openrouter-caching` add, prints "model currency unknown (catalog unreachable: network disabled in L0 tests)" and makes no request. Tests that assert warnings substitute the recorded catalog through a `catalog_snapshot` fixture beside it.

Rejected alternatives:

- A blocking gate on stale pins. A deliberate held pin, such as the judge, would block every run.
- Caching the weekly result in the repository. It would be stale by construction, and the gate is where freshness matters.
- **Per-test injection only**, on the premise that every `matrix.main` test substitutes the fetch. Two existing tests already do not, and two parallel changes add more; each omission would be a live GET from CI on every OS, with a 5 s stall when offline.
- **A fixture that fails the test instead of raising `OSError`.** Every future `matrix.main` test in any change would then have to know about the catalog. Raising the error the gate already handles keeps them offline without that coupling, and a dedicated test pins that the fixture reaches the gate.

### D10. Roster re-pins and what they cost in shipped verdicts

- **Replace in place.** Rows are not duplicated. On this snapshot no held role's ID leaves the roster (no newer Haiku), so no `[role_prices]` entry is written.
  - `report.py` shows the six re-pinned rows as untested.
  - The only measured verdict that leaves the table is deepseek-v4-pro's partial one (one solid task of ten, 2026-08-06).
  - Haiku's ❌ and kimi-k3's 🟡 stay.
  - Rejected: keeping outgoing rows as `enabled = false` to preserve their verdicts. A verdict for a model the matrix no longer measures goes stale silently, and disabled rows still render (spec "Generated model-support report").
- **luna.** It moves to `gpt-6-luna`, keeping the quarantine but rewording the rendered note honestly: "the eval harness could not drive the previous luna pin (Azure strict tool schemas reject Inspect's tools); this pin is not yet re-probed — untested is a harness limitation, not a quality signal". The account's data policy that pins luna to Azure plausibly still applies, but whether `gpt-6-luna` is affected is UNVERIFIED. A re-probe is an optional, gated task.
- **deepseek.** It moves to `-0813` although the price rises (in +52%, out +128% against the old pin). This follows user decision 5 (latest models), and the PR states the price.
- **qwen.** It is pinned to `-0902`. This changes no price, and it ends the silent float.

### Critique dispositions that bind this change (final.md §7)

- **V1 (blocker: a judge switch silently mixes judges).** The judge and persona roles are reported as `held` and never written (D2, D8). Their values are unchanged here.
- **V5 (major: a persona change alters what is measured).** The persona is held, and overrides no longer cascade (D5).
- **V3 (major: environment and effort not pinned).** This change pins `dev_judge_effort` in the registry. `add-dev-runner-judge` enforces it.
- **Minor point "full-ID reproducibility".** Aliases are rejected at parse time. A subscription-role bump requires a resolved-ID check before merge. The CLI version is recorded by `add-dev-runner-judge`.
- **C5 (major: persistent steering outside the repo).** The `AGENTS.md` currency sentence from `steer-subscription-first` D2 now names `uv run poe models`. Memory files are outside the repository and outside this change.
- **Minor point "self-graded row noted".** The roles table makes `judge == roster id` derivable, but the report note belongs to Change D, where the judge may move. It is not added here.
- **RC4 (outdated pins).** Fixed by the bump. RC5 (the gate under-reports) belongs to `fix-openrouter-caching`.

### Review dispositions (2026-10-05)

- **Main specs not allowlisted (major).** Applied: `openspec/specs/**` is a category entry (D6), and task 8.4 re-runs `uv run poe test` on the archived tree before committing.
- **Held role leaving the roster is unpriced (major).** Applied: this change owns it through `[role_prices]` and `support.model_price` (D4). The circular deferral is removed from this document, and `fix-openrouter-caching` was aligned to consume it (Open Questions).
- **L0 gate tests reach the network (major).** Applied: autouse conftest fixture (D9); the two existing tests are named in task 3.1; the false premise is dropped.
- **Troubleshoot ordering and hand-off (minor).** Applied on this side: `fix-troubleshoot-model-match` must land before task 6.1, and this change swaps the token pair there (D6). The troubleshoot files need no parked entry, because their IDs are current until the bump. The wording in `fix-troubleshoot-model-match` belongs to that change.
- **New families never surfaced (minor).** Applied: informational `new_line` findings with a maintainer-moved `lines_reviewed_as_of` cutoff (D2); writes stay limited to known lines.

## Risks / Trade-offs

- **[The catalog's response shape changes]** → The checker treats a missing or ill-typed field as "currency unknown" (exit 2), and the scheduled run goes red, naming the parser. It never writes a guess.
- **[The version-line heuristic misreads a vendor's naming scheme]** (a rename such as `gpt-luna-7`) → The pin then shows as `missing` or keeps a stale line. Both are visible in the weekly summary. `track` fixes it per entry.
- **[A bump PR is merged with the report not regenerated]** → The D7 test fails CI on the PR, and on main if pushed anyway.
- **[Checks from a dispatched CI run do not show on the PR]** → The PR description carries the close/reopen fallback. The first trial run verifies it (Open Questions).
- **[An auto-proposed subscription ID is wrong]** (Anthropic adds a date to a future ID) → `add-dev-runner-judge`'s served-model check fails closed and counts as untested, not FAIL. The PR description requires the free resolved-ID check before merge.
- **[A held judge leaves the roster]** (the haiku row bumps while the judge stays) → `--write` writes a `[role_prices]` entry for the held ID in the same edit and refreshes it weekly (D4). The parser refuses a registry whose judge or persona cannot be priced, so the gap cannot reach `fix-openrouter-caching`'s hard stop. The PR description names the entry.
- **[Archived scenarios name model IDs]** (`openspec/specs/**` after an archive) → category allowlist entry (D6) and a `poe test` re-run after the archive (task 8.4).
- **[New-line noise]** (12 lines on the first run) → informational only, grouped by line rather than by ID, and cleared durably by one hand edit of `lines_reviewed_as_of`.
- **[The guard flags an innocent example]** → A token-level allowlist entry with a reason. The exhaustion check stops entries from outliving their cause.
- **[Weekly PR noise]** → One PR at most. The 0.5% tolerance absorbs float noise. `track = false` is the durable decline.
- **[Merge conflicts in shared docs]** (`harness/README.md`, `AGENTS.md`) → Line ownership follows `steer-subscription-first` D7. In `harness/README.md` this change edits only the `deepseek-v4-flash` example in the Inspect-runs code block, the default named in the `JUDGE_MODEL` sentence, the `gpt-5.6-luna` matrix example and a new "Model currency" subsection; in `AGENTS.md`, the currency sentence and one Commands line. These are anchored by content, because steer's opening table shifts every README line number.
- **[Ordering with `fix-troubleshoot-model-match`]** → Today's `test_troubleshoot_collect.py:307-316` keys on `anthropic/claude-opus-5` in the shipped file, so the regeneration step here breaks it. That change's tasks 1.1–1.2 move those tests to a synthetic file, so it must land before task 6.1 here. Task 6.1 stops until it has, rather than editing a file this change does not own, and then swaps the token pair (D6).
- **[Open-weight rows are served by quantized third parties]** while being priced at the vendor's endpoint → The estimate can run high for those rows. Recording the serving provider is `fix-openrouter-caching`'s job, and provider pinning for non-Anthropic rows is not decided anywhere yet.

## Migration Plan

1. Land after `steer-subscription-first` (cross-change order). `fix-troubleshoot-model-match` must land before task 6.1; tasks 1–5 may proceed before it.
2. Implement the code, tests and docs (tasks 1–5). `poe test` stays green throughout, and the parked `pyproject.toml` smoke entry covers what `add-dev-runner-judge` will fix.
3. Merge `main` (now carrying `fix-troubleshoot-model-match`), swap the eval-prompt token pair if needed, bump the roster, regenerate the shipped verdicts on the maintainer's machine (logs are local), and sync.
4. Archive, re-run the gate on the archived tree, and commit on a branch; merge to main when green. Pushing is done by the maintainer.
5. Maintainer, after pushing:
   - enable "Allow GitHub Actions to create and approve pull requests";
   - run the workflow once with `workflow_dispatch`;
   - confirm that it reports "current", or opens a PR on which the dispatched CI checks appear.

**Rollback:** revert the commit. The registry, the generated files and the workflow revert together. The workflow can also be disabled on its own from the Actions tab without a revert.

## Open Questions

- **Do check runs from a `workflow_dispatch` CI run appear in the bump PR's checks list?** It should, since the checks attach to the head SHA, but this is UNVERIFIED. The first trial run answers it. If they do not, the close/reopen fallback in the PR description stays the documented path. The design does not change either way.
- **The `dev_judge_effort` seed is `medium`.** `add-dev-runner-judge` may recalibrate it in the registry after its first judged runs. The spec only requires a pinned level.
- **Does OpenRouter's default routing ever bill the `openai/flex` tier for unpinned requests?** If it does, terra's standard-tier price over-estimates. `fix-openrouter-caching`'s serving-provider telemetry answers this.
- **Does the Azure strict-schema quarantine apply to `gpt-6-luna`?** This is answered only by the optional gated re-probe (task 6.5), an L1-only, one-epoch run with no judge call. Until then the reworded note stays.
- **Should the dev-side (D2) and user-side (`fix-troubleshoot-model-match`) normalizations share a parity table** in one L0 test? The skills cannot import harness code, so they stay two functions. A shared table could be added later without changing either spec.
- **Cron slot.** The design picks Monday after install-check. Any weekly slot satisfies the spec.
- **Coordination with `fix-openrouter-caching` — resolved 2026-10-05.** This change owns held-role pricing. That change consumes `[role_prices]` and `support.model_price`, adds an optional `cache_write_price` to roster rows and role-price entries (and to the checker's price fields), and its unpriced-role hard stop then only ever fires for an environment override naming an unpriced ID.
- **Coordination with `fix-troubleshoot-model-match` — resolved 2026-10-05.** That change now lands before task 6.1 here and has withdrawn its earlier "before or after" claim. Its task 5.1 edits nothing in `test_model_ids.py` (no troubleshoot file is parked, and this change alone swaps the token pair), and its task 5.2 is its own `poe test` gate. This matches D6.
- **Should a new line alone notify the maintainer** (open an issue, or fail the scheduled run)? Decided no for now: it appears in the run summary every week and in the next bump PR's body. Revisit if a new family goes unnoticed for more than one bump cycle.
