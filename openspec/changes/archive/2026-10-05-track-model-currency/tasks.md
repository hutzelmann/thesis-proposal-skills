# Tasks

**Model calls in this change.**

- No task requires a model call. Every catalog read is an unauthenticated GET against OpenRouter's public catalog: free, with no key and no credential in the command.
- `poe matrix --estimate-only` exits before the confirmation prompt and calls no model.
- The only metered step is optional (6.5). It shows its estimate first and runs only after the user's explicit approval in chat. Nobody passes `--yes` on the user's behalf.

## 0. Preconditions

- [x] 0.1 Confirm the cross-change order:
  - `steer-subscription-first` is archived (`ls openspec/changes/archive | grep steer-subscription-first`);
  - this branch contains its `AGENTS.md` bullet "**Metered model calls**".

  Record whether `fix-troubleshoot-model-match` has landed (`grep -c normalize_model_id skills/proposal-troubleshoot/scripts/collect.py`). It must land before task 6.1; tasks 1–5 may run before it. The answer decides the token-pair spelling in 4.2 and whether 6.1 waits. Verify: both facts are noted in this task.

  Noted 2026-10-05: `2026-10-05-steer-subscription-first` is archived and `AGENTS.md` carries the "**Metered model calls**" bullet. `fix-troubleshoot-model-match` has landed on `main` (archived as `2026-10-05-fix-troubleshoot-model-match`; the grep counts 4), so 4.2 writes the `claude-haiku-4-5-20251001` spelling and 6.1 does not wait.

## 1. Roles table and registry parsing

- [x] 1.1 Write failing L0 tests in `tests/unit/test_support_matrix.py`. First edit `REGISTRY_TOML`: add `prices_as_of`, `lines_reviewed_as_of` and a `[roles]` table with synthetic `lab/` IDs, and drop `[tasks.judge].model`. Then add tests that:
  - parse every role;
  - check that `persona` defaults to `judge`;
  - check that `TaskConfig.judge_model` is filled from `roles.judge`;
  - reject a leftover `[tasks.judge].model` with a message naming `[roles].judge`;
  - reject `sonnet`, `~lab/x-latest` and `lab/x-latest`, in the roster and in roles;
  - reject `smoke` naming a disabled or unknown entry;
  - reject an unknown `dev_judge_effort`;
  - accept `track` as a string or `false`, and accept `price_endpoint`;
  - for `support.role_model`, check that an environment override applies to its own role only (judge override, persona unchanged);
  - **role prices (D4):**
    - a judge whose ID has no roster row parses when a `[role_prices]` entry carries it, and `support.model_price` returns that entry;
    - `model_price` prefers the roster row, includes disabled rows, and returns `None` for an unknown ID;
    - `estimate_cost` prices the judge from a `[role_prices]` entry;
    - parsing fails, naming the role, when the judge or persona is priced by neither;
    - parsing fails, naming the entry, for a `[role_prices]` entry no role names and for one that duplicates a roster ID.

  Verify: the new tests fail against today's `support.py`.
- [x] 1.2 Implement in `harness/support.py`:
  - a frozen `Roles` dataclass on `Registry`, and `Registry.role_prices`;
  - the parsing and validation from D4;
  - `role_model(roles, name, environ)`;
  - `model_price(registry, model_id)`, used by `estimate_cost` and by every other price lookup in `support.py`.

  Stay stdlib-only, with mccabe ≤ 12 per function. Verify: `uv run pytest tests/unit/test_support_matrix.py` and `uv run ruff check harness/support.py` are green.
- [x] 1.3 Edit `harness/models.toml` as shown in design D4, with no model ID changed yet:
  - add `prices_as_of = 2026-08-06` (the honest current date), `lines_reviewed_as_of = 2026-08-06` (D2) and `[roles]` with `judge`, `smoke`, `dev_judge = "claude-sonnet-5-5"` and `dev_judge_effort = "medium"`. No `[role_prices]` entry: the judge is on the roster;
  - remove `model` from `[tasks.judge]`;
  - add `price_endpoint = "alibaba"` to the qwen entry (D3);
  - rewrite the header comment to state the price basis (D3) and the roles rule.

  Verify:
  - the registry parses;
  - `uv run poe matrix --estimate-only` (no model call) still totals $100.23, so pricing is unchanged.
- [x] 1.4 In `harness/skill_evals.py`:
  - resolve `JUDGE_MODEL` and `PERSONA_MODEL` through `support.role_model` over the parsed registry;
  - rewrite the docstring at `:8-13` to name `[roles]` as the source and the two overrides, with no model ID in it (guard Rule A).

  In `tests/unit/test_eval_wiring.py`, assert that `skill_evals.JUDGE_MODEL` and `skill_evals.PERSONA_MODEL` equal `support.role_model(...)` for the test environment. Verify: `uv run pytest tests/unit/test_eval_wiring.py` is green.

## 2. Currency checker (`harness/model_currency.py`)

- [x] 2.1 Record the catalog fixture under `tests/unit/data/model_catalog/`:
  - `models.json`: the 2026-10-04 snapshot trimmed to the entries the tests need, with fields `id`, `created`, `expiration_date`, `canonical_slug` and `pricing`. Required entries:
    - the anthropic lines including `claude-fable-5` and `claude-fable-5.1`, the openai luna/terra/sol/astra lines, deepseek v4 and qwen3.x-max lines;
    - kimi-k2/k3;
    - `:batch` and `:free` variants;
    - `-pro`, `-prime` and `-code` siblings;
    - `~…-latest` aliases;
    - for the new-line cases: an untracked line whose members all predate `2026-08-06` (not reported), and an ID with no digit run (ignored).
  - `endpoints/<vendor>__<slug>.json` for each roster vendor.
  - a `README.md` naming the source URLs and the recording date.

  Source the files from `currency/or_models_fresh.json` and `currency/ep_*.json` in this session's scratchpad. If they are gone, re-fetch them with an unauthenticated GET and record the new date. Add clearly synthetic `lab/` entries for the expiring-without-successor, no-vendor-endpoint and held-role-leaves-the-roster cases (a `lab/judge-1` roster row named by the judge role, with a newer `lab/judge-2` and an endpoint for each). Verify: `jq '.data | length' tests/unit/data/model_catalog/models.json` is under 150, and the README states the date.

  Done from the scratchpad files (recorded 2026-10-04 22:02 UTC): 111 entries, 14 endpoint files (10 recorded, 4 synthetic `lab/`). Addition: `registry-pre-bump.toml`, a copy of the registry after task 1.3, so the currency tests replay a stale roster without depending on the live `harness/models.toml`, which task 6.2 bumps.
- [x] 2.2 Write failing tests in `tests/unit/test_model_currency.py`, covering:
  - **line derivation** for every current roster ID and for `claude-sonnet-5-5` and `claude-haiku-4-5-20251001`;
  - **successors:** sol proposes `gpt-6.1-sol` (not `gpt-6-sol`); the dated `deepseek-v4-pro-0813` counts as newer by `created`; the missing `qwen3.8-max` proposes `qwen3.8-max-0902`; terra, haiku and kimi-k3 are current;
  - **exclusions:** `:batch`, `-pro`, `-prime` and `~…-latest`;
  - **tracking overrides:** a `track` glob override, and `track = false` reported as `untracked`;
  - **prices:**
    - drift on terra against the `openai` endpoint, with no drift within 0.5%;
    - `price_endpoint = "alibaba"` for qwen;
    - `no_vendor_endpoint` for the old `deepseek-v4-pro`;
    - an omitted cache-read price;
  - **alerts:** an `expiring` alert;
  - **held roles:** `judge` and `persona` are reported `held` and never written;
  - **new lines (D2):**
    - with `lines_reviewed_as_of = 2026-08-06`, the Fable line is reported once as `new_line` with `proposed = anthropic/claude-fable-5.1`, not writable, and the exit status is what it would be without it;
    - the untracked line whose members all predate the date is not reported, nor is the digit-less ID, nor any line a registry entry derives (including a `track = false` entry);
    - moving `lines_reviewed_as_of` past `claude-fable-5.1`'s `created` clears the finding;
  - **write mode:**
    - it bumps the roster ID, the matching `smoke` role and `dev_judge` (to `claude-sonnet-<v>` form), but not `judge`;
    - it updates prices and `prices_as_of`, and never changes `lines_reviewed_as_of`;
    - **held role leaves the roster:** on the synthetic `lab/judge-1` case, the roster row becomes `lab/judge-2`, the judge stays `lab/judge-1`, a `[role_prices."lab/judge-1"]` entry is written at its endpoint price in the same edit, the result re-parses, and `support.estimate_cost` prices the judge from it; a later run with a changed endpoint price reports and refreshes drift on that entry;
    - it preserves comments and the luna note;
    - the result re-parses through `support.parse_registry`;
    - a second run changes no byte;
  - **interface:**
    - `--json` matches the D1 schema;
    - `--pr-body` content: each finding, the held roles and any `[role_prices]` entry written, the new lines with the two ways to clear them, `uv run poe report` plus `python3 scripts/sync_shared.py` with the gitignored-logs reason, the untested-until-gated-run sentence, the subscription resolved-ID check, and the close/reopen fallback;
    - an unreachable or malformed catalog exits 2 and writes nothing;
  - **imports:** an import test that `model_currency.py` and `support.py` import only `sys.stdlib_module_names` plus each other.

  No test opens a socket: the fetch is injected, and the conftest fixture from 3.1 makes any omission raise instead of connecting. Verify: the tests fail (ImportError).

  Verified: collection failed with `ModuleNotFoundError: model_currency`. The conftest fixture from 3.1 step 1 was added together with 2.3, since the tests that pin the refused fetch need it.
- [x] 2.3 Implement `harness/model_currency.py` per D1–D4. It needs `main(argv: list[str] | None = None) -> int`, a frozen `Finding` dataclass, pure functions for line, compare, new lines, price and edit, and one IO function `fetch_json(url, timeout)` using `urllib.request`, resolved through the module attribute at call time (D1). Verify:
  - `uv run pytest tests/unit/test_model_currency.py` is green;
  - `uv run ruff check harness/model_currency.py` is clean, with no per-file ignore;
  - `tests/unit/test_repo_conventions.py` passes (main takes argv).

  Clarifications made while implementing, all within D1–D4:
  - `--json` carries one additive key beside `{source, fetched_at, findings[]}`: `alerts`, the subjects that are `missing` or `expiring` with no writable successor. The workflow fails the run on it (D8 step 2) without re-deriving the rule in `jq`.
  - A `[role_prices]` entry's findings use the subject `role_price:<id>`. An entry can serve both the judge and the persona, so `role:<name>` would name only one of them.
  - Two more flags: `--registry PATH`, so tests and reviewers can point at a copy, and `--as-of DATE` (default: today, UTC), the snapshot date written to `prices_as_of`. `prices_as_of` moves only when a price or ID edit is applied, so an unchanged week produces no diff and no PR.
  - A `track` glob that the pin itself does not fit (a rename) sorts the pin below every member of that line, so the newest member is proposed.
  - For a vendor with no exactly matching tag, a single quantization tag under the vendor (`moonshotai/mxfp4` for kimi-k3) is its endpoint. `/fast` and `/flex` are never chosen, and two candidates mean none.
- [x] 2.4 Add `models = "python3 harness/model_currency.py"` to `[tool.poe.tasks]`, commented "networked, read-only; not part of `test`". Verify: `uv run poe models` (free, no key) exits 1 and lists exactly the proposal table's re-pins and repricings:
  - six bumps, all `newer` except qwen's `missing`, each priced at its successor's vendor endpoint;
  - terra's `price_drift`;
  - informational `new_line` findings: the 12 lines design D2 lists on the 2026-10-04 snapshot (the live catalog may have added more), Fable 5.1 among them.

  It reports no drift on outgoing pins (D3), no `held` finding and no `[role_prices]` entry, because no newer Haiku exists.

  Verified live at 2026-10-05 00:47 UTC (free, keyless GETs): exit 1, the six bumps (qwen `missing`, the rest `newer`) at sonnet 2/10/0.2, opus 4/20/0.2, luna 0.1/0.5/0.01, sol 2/10/0.1, deepseek 0.66/1.98/0.022 and qwen 2/6/0.25 (alibaba), terra `price_drift` 1/6/0.1 → 2/12/0.2, and exactly the 12 `new_line` findings of D2. No outgoing-pin drift, no `held`, no `[role_prices]`.

## 3. Currency warning at the cost gate

- [x] 3.1 Make L0 offline by construction (design D9), then write failing gate tests:
  1. In `tests/conftest.py`, add an autouse fixture that monkeypatches `model_currency.fetch_json` with a function raising `OSError("network disabled in L0 tests")`, and a `catalog_snapshot` fixture that substitutes the recorded catalog from 2.1. Import `model_currency` through the configured `pythonpath`, never `sys.path`.
  2. Update the two existing tests that call `matrix.main` without a substitute, in `tests/unit/test_support_matrix.py:420-436`:
     - `test_matrix_gate_declined_makes_no_metered_call` (`matrix.main([])`);
     - `test_matrix_estimate_only_exits_clean` (`matrix.main(["--estimate-only", "--tier", "cheap"])`).

     Keep their assertions, and add one that the output carries "model currency unknown (catalog unreachable: network disabled in L0 tests)". That proves the fixture reaches the gate.
  3. Add the gate tests:
     - with `catalog_snapshot`, `matrix.main(["--estimate-only"])` prints the stale-model lines after the estimate, the estimate figures are unchanged, and the exit status is 0;
     - with a fetch that raises `OSError`, it prints "model currency unknown" and the exit status is unchanged;
     - the declined-confirmation path still makes no metered call;
     - calling `model_currency.fetch_json` directly inside L0 raises the fixture's `OSError`.

  Verify: the new gate tests fail, and the two updated tests fail only on the new assertion.

  Verified before 3.2: the two updated tests failed only on the new assertion, and the `matrix.main` gate tests failed. The gate tests run against `registry-pre-bump.toml` (via `matrix.REGISTRY`), so they keep asserting stale pins after 6.2 makes the live registry current. The direct `gate_warnings` test passed from the start, because 2.3 had already added the function.
- [x] 3.2 Implement `gate_warnings(...)` in `model_currency.py` and call it from `matrix.main` before `confirm_spend`, covering the selected models plus the judge and persona roles, with a 5 s timeout. Replace the model ID in `matrix.py`'s docstring usage line (`:11`) with a placeholder (`--models <registry-id-suffix>`). Verify:
  - 3.1's tests are green;
  - `uv run poe matrix --estimate-only` (no model call) shows the warnings above where the prompt would be.

  Verified with `uv run python harness/matrix.py --estimate-only`, the same entry point as `poe matrix` without loading `.env`, since an estimate needs no key. The total is still $100.23, followed by six "model currency:" lines (five stale, qwen missing) from the live catalog.

## 4. L0 guards

- [x] 4.1 Write `tests/unit/test_model_ids.py` per design D6:
  - token recognition, both the base families and the registry lines;
  - Rule A paths;
  - Rule B resolution over the provider-qualified, provider-stripped and subscription spellings;
  - stripping of the README's generated region;
  - the allowlist as path globs and (path, token) pairs, each with a reason, including the category entries `openspec/changes/**` and `openspec/specs/**` (spec scenarios carry illustrative IDs and arrive by archive; design D6);
  - the exhaustion check, under which a parked entry or a (path, token) entry that exempts nothing fails, while category globs are exempt from it;
  - failure messages naming the file, the line, the token and, for Rule B, the current pin of the token's line.

  Verify: run it. It fails on the expected violations only:
  - `pyproject.toml` smoke;
  - `skill_evals.py`'s troubleshoot prompt;
  - the `deepseek-v4-flash` example in `harness/README.md`'s Inspect-runs code block.

  `harness/README.md` references here are anchored by content, not line number: `steer-subscription-first` inserts its "Which path to use" table near the top of the file, which shifts every line below it.

  The issue template and the troubleshoot `SKILL.md` and `collect.py` are not violations at this point, whether or not `fix-troubleshoot-model-match` has landed. Before the 6.2 bump, `claude-sonnet-5` and `claude-opus-5` resolve to current roster pins, `claude-sonnet-5-5` resolves to `roles.dev_judge`, and `claude-haiku-4-5-20251001` resolves to the unchanged haiku row.

  Result: the three expected violations, plus one the design did not foresee. `collect.py:68` has a comment saying that a dotted cloud-prefix segment holding a digit, `` `qwen3.` ``, belongs to the model name. The `qwen\d…` base pattern reads it as the token `qwen3`, which resolves to no roster entry. The comment names no model, so it gets a permanent token-level entry with that reason (design D6, Risks: "the guard flags an innocent example"). That is not a parked entry, and the exhaustion check covers it. Its model IDs, the troubleshoot `SKILL.md` and the issue template are clean, as predicted. The `skill_evals.py` docstring (1.4) and the `matrix.py` usage line (3.2) were already fixed when the guard first ran.

  Further whole-file entries, each with its reason in the test: `tests/unit/test_model_currency.py` (its IDs are facts of the recorded snapshot) and `tests/unit/test_model_ids.py` (the guard's own fixtures). The 3.1 gate tests that assert stale pins moved into `test_model_currency.py` for the same reason, so `test_support_matrix.py` names no model.
- [x] 4.2 Resolve the violations:
  - **The `deepseek-v4-flash` example in `harness/README.md`'s Inspect-runs code block:** replace it with a roster entry such as `openrouter/moonshotai/kimi-k3`, not `deepseek-v4.1-flash` (D6).
  - **The `JUDGE_MODEL` judge sentence below that code block:** reword it (as left by `steer-subscription-first`) so its default reads "`[roles].judge` in `harness/models.toml`". Keep the `JUDGE_MODEL`/`PERSONA_MODEL` override wording.
  - **`.github/ISSUE_TEMPLATE/skill-defect.yml:71`:** set it to `claude-sonnet-5-5`. This is not a 4.1 violation; the edit keeps the line current after the 6.2 bump. Skip this if `fix-troubleshoot-model-match` already did it.
  - **Token-level allowlist** entry for the `troubleshoot_model_rung` prompt spelling: `claude-haiku-4-5-20251001` if 0.1 found `fix-troubleshoot-model-match` landed, otherwise `claude-haiku-4.5` (swapped in 6.1). Rule A always needs this pair, and only this change edits it.
  - **Parked entry:** `pyproject.toml` smoke (owner `add-dev-runner-judge`). No troubleshoot file gets a parked entry, because none is a violation before the bump (4.1).

  Verify: `uv run pytest tests/unit/test_model_ids.py` is green.

  Done. `fix-troubleshoot-model-match` had already set the issue template to `claude-sonnet-5-5`, so that edit was skipped. The token pair uses `claude-haiku-4-5-20251001`.
- [x] 4.3 Add the shipped-verdict test (design D7): `shared/model-support.json` keys and the README generated region's pinned-ID column equal the roster IDs minus `openrouter/`, with a failure message that names the extra and missing IDs and the two regeneration commands. Verify: it passes on today's tree (pre-bump), and it fails when one roster ID is edited in a `tmp_path` copy, through a parameter on the comparison function.

  Done in `tests/unit/test_support_matrix.py` (`shipped_roster_mismatch`, `registry_path` parameter). The tmp copy edits the first roster row that no role names, so the edited registry still parses.

## 5. Weekly bump workflow

- [x] 5.1 Add `workflow_dispatch:` to `.github/workflows/ci.yml`'s `on:`, with a comment saying why: `GITHUB_TOKEN` PRs trigger no `pull_request` runs, so the currency workflow dispatches CI. Verify by reading the file. `actionlint .github/workflows/ci.yml` also checks it when the tool is installed.

  Verified by reading the file. actionlint is not installed here; a one-off parse with the venv's PyYAML lists the triggers `push`, `pull_request` and `workflow_dispatch`.
- [x] 5.2 Add `.github/workflows/model-currency.yml` per design D8:
  - triggers: a weekly `schedule` after the install-check slot, plus `workflow_dispatch`;
  - `concurrency: model-currency`;
  - permissions `contents: write`, `pull-requests: write` and `actions: write`, and nothing else;
  - `python3 harness/model_currency.py --write --json --pr-body …` (no uv), with findings written to `$GITHUB_STEP_SUMMARY`;
  - the fixed branch `model-currency/bump`, rebuilt from main only while it carries no commit by anyone other than `github-actions[bot]`, otherwise a PR comment;
  - `gh pr create`/`gh pr edit --body-file`;
  - `gh workflow run ci.yml --ref model-currency/bump`;
  - an obsolete PR closed with a comment;
  - the run failing on a `missing`/`expiring` alert without a writable successor;
  - `new_line` findings written to the summary (and, through `--pr-body`, to an open PR), never opening a PR or failing the run on their own.

  Done; the cron slot is Mondays 06:47 UTC, 30 minutes after install-check. Choices within D8:
  - The bot-only rule applies while a bump PR is open. Once that PR has been merged or closed, the leftover branch is rebuilt from main. Otherwise a merged branch carrying the maintainer's regeneration commit would block every later bump.
  - The push uses `--force-with-lease` against the SHA inspected a moment earlier, or against an absent ref.
  - An alert fails the run whether or not the registry changed, as the spec says, not only in the unchanged branch of D8 step 2.
  - The alert list reaches the shell through `env`, never through `${{ }}` inside `run:`.

  Not run: the `workflow_dispatch` trial run and the repository setting. Deferred: maintainer action (8.6).
- [x] 5.3 Add `tests/unit/test_currency_workflow.py`, using narrow text extraction and no YAML parser. It pins the security-relevant properties of 5.2:
  - exactly those three permissions;
  - no `secrets.` reference other than `GITHUB_TOKEN`;
  - both triggers;
  - the fixed branch name;
  - the CI dispatch;
  - no `--yes`, no `poe matrix` and no `inspect eval`.

  It also checks that `ci.yml` declares `workflow_dispatch`. Verify: it passes, and it fails when a `secrets.OPENROUTER_API_KEY` line is added to a copy.

  Verified: green, and the parametrized tests show the check failing on an added `secrets.OPENROUTER_API_KEY` line, an added `poe matrix --yes` step, and an extra `id-token: write` permission.

## 6. Roster bump and regeneration

- [x] 6.1 Stop condition and guard hand-off (design D6).
  1. If `main` does not yet carry `fix-troubleshoot-model-match` (`grep -c normalize_model_id skills/proposal-troubleshoot/scripts/collect.py` on `main` is 0), stop and record the wait. Do not edit that change's files here.
  2. Once it has landed, merge `main` into this branch. Verify that `grep -nE 'resolve_model\("(openrouter/)?(anthropic/)?claude-opus-5"\)' tests/unit/test_troubleshoot_collect.py` is empty. That pattern matches only a lookup of an opus-5 spelling against the shipped file (no support-file argument), which is what the regeneration breaks. The synthetic fixtures that `fix-troubleshoot-model-match` adds keep the `anthropic/claude-opus-5` key for its version-guard tests, so a grep for the bare key would still hit after it lands.
  3. If 4.2 wrote the `claude-haiku-4.5` spelling, swap the `harness/skill_evals.py` (path, token) pair to `claude-haiku-4-5-20251001`. This change is the only one that edits the pair, because its guard never reaches `main` before `fix-troubleshoot-model-match` does. Do not add entries.

  Verify: `uv run pytest tests/unit/test_model_ids.py` is green, so the exhaustion check finds no dead entry.

  Done. This work runs directly on `main` (the owner's preference), which already carries `fix-troubleshoot-model-match`, so there was nothing to merge. The resolve_model grep is empty. 4.2 wrote `claude-haiku-4-5-20251001`, so no swap was needed. The guard is green.
- [x] 6.2 Run the bump:
  1. Run `python3 harness/model_currency.py --write` against the live catalog (free GET) or the recorded snapshot. The qwen `price_endpoint` is already in place from 1.3.
  2. Reword the luna note by hand to the design D10 text. The write mode never edits notes.

  Verify that `git diff harness/models.toml` matches the proposal's table:
  - six re-pins;
  - terra repriced to 2/12/0.2;
  - haiku and kimi unchanged;
  - `smoke` and `judge` still `openrouter/anthropic/claude-haiku-4.5`, and no `[role_prices]` entry (the haiku row did not move);
  - `prices_as_of` set to the snapshot date, and `lines_reviewed_as_of` still `2026-08-06`, so the new lines stay visible for the maintainer's first weekly PR.

  `uv run poe models` then exits 0 and reports only informational findings (the `new_line` set from 2.4).

  Done against the live catalog: free, keyless GETs at 2026-10-05 00:56 UTC, so `prices_as_of = 2026-10-05`, one day after the recorded fixture. The live prices equal the 2026-10-04 snapshot's. The diff matches the table: six re-pins, opus 4/20/0.2, luna out 0.5, sol 2/10/0.1, deepseek 0.66/1.98/0.022, qwen unchanged at 2/6/0.25, terra 2/12/0.2, haiku and kimi untouched. `judge` and `smoke` are unchanged, there is no `[role_prices]`, and `lines_reviewed_as_of` stays `2026-08-06`. The luna note and its comment were reworded by hand to the D10 text. `uv run poe models` then exited 0 with "0 actionable, 12 informational".
- [x] 6.3 Fix every doc the guard now names because it cites an outgoing ID. Expected: the `poe matrix --models … gpt-5.6-luna --tasks write_from_seed` example in `harness/README.md`'s model-support code block, where `gpt-5.6-luna` becomes a current, non-quarantined roster suffix. Verify: `uv run pytest tests/unit/test_model_ids.py` is green. Only the 4.3 shipped-verdict test is still red.

  Done: the guard named only that example (and the generated files, which are exempt), and `gpt-5.6-luna` became `gpt-5.6-terra`. The guard is green, and only the two 4.3 shipped-verdict tests are red.
- [x] 6.4 Regenerate on the machine that holds `logs/evals/` (no model call): run `uv run poe report`, then `python3 scripts/sync_shared.py`. Verify:
  - the README summary lists the nine current IDs: the six re-pinned rows ❔ untested (luna with the reworded note), haiku ❌, kimi-k3 🟡;
  - `shared/model-support.json` and `skills/proposal-troubleshoot/references/model-support.json` carry the same keys;
  - `python3 scripts/sync_shared.py --check` exits 0;
  - the 4.3 test is green.

  Done: regenerated from 10 local logs, newest 2026-08-10. The six re-pinned rows are ❔ untested, luna with the reworded note. Haiku ❌ and kimi-k3 🟡 are unchanged. The only measurement that left is deepseek-v4-pro's 1/1* write_from_seed cell. Both JSON files carry the same nine keys, the drift check reports "generated copies in sync", and the 4.3 tests and `test_troubleshoot_collect.py` are green.
- [ ] 6.5 Optional, metered and gated: re-probe luna's Azure quarantine. The question is only whether Inspect can drive gpt-6-luna's tool calls. So the probe uses `customize_override`, a matrix task whose single scorer is L1 (`customize_l1`) and makes no L2 judge call, at one epoch, in its own log directory so that `poe report` never counts a 1-epoch log as a shipped verdict. (`check_report` would also be L1-only, but the registry excludes it from matrix runs.)
  1. Run `uv run poe matrix --models gpt-6-luna --tasks customize_override --epochs 1 --log-dir logs/luna-probe --estimate-only`. It makes no model call.
  2. Show the user the estimate and its basis (registry pricing × token priors or history). Say that its judge share is a ceiling this L1-only task never spends, and give the reason no $0 alternative exists: the run calls no Anthropic model, only a non-Anthropic row that has no subscription route.
  3. Wait for explicit approval in chat. Only then run the same command without `--estimate-only` and without `--yes`, so the operator confirms at the prompt.
  4. If the harness now drives gpt-6-luna, remove the note and the quarantine. Otherwise keep the reworded note.

  Skipped unless approved. Verify: this task records the estimate shown, the approval or the skip, and the actual cost from `matrix-cost-*.json`.

  Deferred: needs explicit user approval (estimate: $0.08). Step 1 ran with no model call, via `uv run python harness/matrix.py … --estimate-only`. The basis is registry pricing (0.1/0.5 $/Mtok) times measured history and priors. About $0.055 of it is the judge share (40k in and 3k out at haiku's 1/5), a ceiling this L1-only task never spends, so the expected spend is about $0.03. No $0 alternative exists: the run calls no Anthropic model, only a non-Anthropic row with no subscription route. Not run, so no actual cost. The reworded note stays.

## 7. Documentation

- [x] 7.1 Add a "Model currency" subsection to `harness/README.md`'s matrix section, covering:
  - the `[roles]` table and its rules;
  - the price basis and `prices_as_of`;
  - `[role_prices]`: written by `--write` when a held role's ID leaves the roster, refreshed weekly, deleted by whoever moves the role;
  - `uv run poe models`;
  - the weekly bump PR and what the maintainer does on it (regenerate the report and sync locally, the subscription resolved-ID check, closing and reopening if CI is missing);
  - new lines: reported, never written; cleared by adding a roster entry or by moving `lines_reviewed_as_of` by hand;
  - held judge and persona until Change D;
  - declining a bump with `track = false`.

  Verify: it names no model ID other than current registry entries (the guard passes).
- [x] 7.2 In `AGENTS.md`:
  - add `uv run poe models   # model currency vs the public OpenRouter catalog (networked, read-only)` to the Commands block;
  - replace the manual currency sentence in the "Metered model calls" bullet with "run `uv run poe models`", keeping the rest of that bullet verbatim.

  Verify: `grep -n 'poe models' AGENTS.md` shows both, and `uv run poe test` still passes the pinned-sentence tests.

## 8. Gate, archive, commit

- [x] 8.1 Run `uv run poe test` (pytest, ruff, drift, conform). Verify: green, with no new per-file ignore and no new coverage omit.

  Green on 2026-10-05: 2170 passed, ruff clean, "generated copies in sync", all 11 skills conform. No per-file ignore and no coverage omit were added.
- [x] 8.2 Run `uv run poe cov`. Verify: at least the 78% floor, with `harness/model_currency.py` counted (not omitted).

  85.95% in total. `harness/model_currency.py` is counted at 94% and `harness/support.py` at 98%.
- [x] 8.3 Run `uv run poe specs` (`openspec validate --all --strict`). Verify: green.

  20 passed, 0 failed.
- [ ] 8.4 Archive through the `openspec-archive-change` skill (the CLI `openspec archive`, never a hand move). The archive syncs this change's scenarios, which name model IDs, into `openspec/specs/testing-harness/spec.md`. Before committing, re-run `uv run poe test` and `uv run poe specs` on the archived tree. Verify: both are green, and `test_model_ids.py` does not flag the synced spec (`openspec/specs/**` allowlist, design D6).
- [x] 8.5 Commit the change on a branch off `main`, one commit for this change, with the attribution lines. Do not push. Verify: `git log -1 --stat` shows the code, the regenerated files, the synced spec and the archived change folder.

  Committed directly on `main`, the owner's standing preference for this repository and the instruction for this run, instead of on a branch. One commit, not pushed.
- [ ] 8.6 Maintainer only, on explicit request (pushing and repository settings are never done by an agent):
  - push and merge;
  - enable Settings → Actions → "Allow GitHub Actions to create and approve pull requests";
  - run "Model currency" once with `workflow_dispatch`.

  Verify, and record in the archived change's notes: the run reports "current", or opens one PR whose dispatched CI checks appear on it. That answers design Open Question 1.

  Deferred: maintainer action. The commit is not pushed, the setting is unchanged, and no trial run was made, so Open Question 1 stays open. After the push, the first `workflow_dispatch` run should report "current" (0 actionable on 2026-10-05) unless the catalog moves before then.
