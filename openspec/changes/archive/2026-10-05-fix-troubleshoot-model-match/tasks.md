# Tasks

## 0. Preconditions

- [x] 0.1 Check the cross-change order and record the guard state.
  1. `track-model-currency` is not archived. Check: `ls openspec/changes/archive | grep track-model-currency` is empty. That change's task 6.1 waits for this one, so this change must land on `main` first.
  2. Confirm that its guard is not on `main` (`git ls-tree --name-only main tests/unit/test_model_ids.py` prints nothing). It cannot be, because that change commits once, after its task 6.1 has waited for this one. If it is there, the order was broken: stop and report it.

  Verify: both facts are noted in this task.
  - Result 2026-10-05, `main` at `d35a5d9` (steer-subscription-first archived and committed): the archive grep printed nothing (exit 1), so `track-model-currency` is unarchived and still an untracked folder; `git ls-tree --name-only main tests/unit/test_model_ids.py` printed nothing, so the guard is not on `main`. Order intact.

## 1. Failing tests first

- [x] 1.1 In `tests/unit/test_troubleshoot_collect.py`, add a `support_file` fixture that writes a synthetic `model-support.json` into `tmp_path` (same shape as the shipped file: `statuses` plus `models` → `verdict`/`skills`). Its keys:
  - `anthropic/claude-haiku-4.5`
  - `anthropic/claude-sonnet-5.5`
  - `anthropic/claude-opus-5.5`
  - `anthropic/claude-opus-5`, kept for the version guard
  - `openai/gpt-6-luna`, the non-Anthropic key, spelled as `track-model-currency` re-pins luna
  - `deepseek/deepseek-v4`, kept for the colon-form revision guard (design D3)

  Verify: the fixture is used by the tests in 1.2 and reads no repository file.
  - Done: the fixture writes through a `write_support(path, keys)` helper, which the version-guard, ambiguity and parity tests (3.3) also use. That is the third use, so the helper was extracted. It reads no repository file.
- [x] 1.2 Replace `test_resolve_model_matches_a_bare_name_by_suffix` and `test_resolve_model_accepts_the_full_key_and_a_routing_prefix` (lines 307-316, keyed on the soon-removed `anthropic/claude-opus-5`) with tests over `support_file`:
  - **exact key and routing prefix:** `anthropic/claude-opus-5.5` and `openrouter/anthropic/claude-opus-5.5` both resolve to `anthropic/claude-opus-5.5`;
  - **bare name:** `claude-opus-5.5` resolves;
  - **Claude Code spellings:**
    - `claude-haiku-4-5-20251001`, `claude-haiku-4-5` and ` Claude-Haiku-4-5 ` resolve to `anthropic/claude-haiku-4.5`;
    - `claude-sonnet-5-5` resolves to `anthropic/claude-sonnet-5.5`;
    - `claude-opus-5-5` resolves to `anthropic/claude-opus-5.5`;
  - **cloud and variant spellings:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`, `global.anthropic.claude-haiku-4-5-20251001-v1:0`, `claude-haiku-4-5@20251001` and `claude-sonnet-5-5[1m]` resolve;
  - **version guard:**
    - with a second synthetic file holding only `anthropic/claude-opus-5`, `claude-opus-5-5` resolves to `(None, {})`;
    - `claude-haiku-4` resolves to `(None, {})`;
  - **colon-form revision only:** `deepseek-v3` does not resolve to `deepseek/deepseek-v4`, and `normalize_model_id("deepseek-v4") != normalize_model_id("deepseek-v3")`;
  - **aliases name no version:** `haiku`, `sonnet` and `opus` resolve to `(None, {})`;
  - **ambiguity:** a synthetic file holding both `anthropic/claude-haiku-4.5` and `bedrock/claude-haiku-4-5` resolves `claude-haiku-4-5-20251001` to `(None, {})`.

  Verify: the new tests fail against the current code (`ImportError` on `normalize_model_id`, or the Claude Code spellings resolving to `None`). Record the failure in this task.
  - Recorded 2026-10-05, in two steps. (a) Against the unchanged module, collection stopped: `ImportError: cannot import name 'normalize_model_id' from 'collect'`. (b) A placeholder `normalize_model_id` (strip and lowercase only) was added and `resolve_model` left unchanged. 11 tests failed and 14 passed in the matching subset. The failures were all five Claude Code spellings, all four cloud and variant spellings, the shipped `anthropic/` property (1.3) and the haiku test (1.4). The version-guard, colon-form, alias, ambiguity and exact or bare-name tests passed already, because the old suffix rule gets those right. They are kept as guards.
- [x] 1.3 Add two property tests over the shipped `skills/proposal-troubleshoot/references/model-support.json`:
  - every key resolves to itself, and no two keys share a normalised spelling;
  - every `anthropic/` key resolves from its Claude Code spelling, built by dropping `anthropic/` and turning each dot between digits into a dash, both bare and with `-20251001` appended.

  Verify: both fail today (no Claude Code spelling resolves), and neither names a specific key, so the `track-model-currency` roster bump cannot break them.
  - Deviation, recorded: the Claude Code spelling property failed as expected. The self-resolution and no-collision property fails today only through the `ImportError`. On the placeholder it passed, because the exact-key step has always resolved a key to itself, and `normalize_model_id` is what it asks about. It is a regression guard for the new rule (design D4), not a red test. Neither test names a specific key. The `anthropic/` test asserts the shipped file holds at least one such key, so it cannot pass vacuously.
- [x] 1.4 Change `test_resolve_model_reports_a_known_failing_skill` to resolve `claude-haiku-4-5-20251001`, the eval prompt's spelling (task 4.1), against the shipped file, and still assert `proposal-write` is `fail`. Verify: it fails today.
  - Failed on the placeholder (resolved to `None`, then `KeyError` on `skills`). Passes after 2.2.

## 2. Implementation (user-side script: Python ≥ 3.11 standard library only)

- [x] 2.1 In `skills/proposal-troubleshoot/scripts/collect.py`, add a pure `normalize_model_id(name: str) -> str` beside `resolve_model`, applying the design's D2 steps in order:
  1. strip and lowercase;
  2. drop a trailing bracketed variant;
  3. keep what follows the last `/`;
  4. drop the `(?:[a-z]+\.)?anthropic\.` prefix;
  5. drop a colon-form `-v\d+:\d+` revision;
  6. drop a `[-@]20\d{6}` date stamp;
  7. turn each digit-dash-digit into digit-dot-digit.

  Compile the patterns as module constants. Verify: `uv run ruff check skills/proposal-troubleshoot/scripts/collect.py` is clean with no new per-file ignore, and the module still imports only standard-library modules.
  - Done: five `MODEL_*_RE` constants sit beside the other patterns. Ruff exits 0, and `pyproject.toml` has no per-file ignore for `collect.py`. The imports are unchanged (`argparse`, `hashlib`, `json`, `platform`, `re`, `shutil`, `sys`, `pathlib`).
- [x] 2.2 Rewrite `resolve_model`:
  1. keep the exact-key step, after dropping `openrouter/`;
  2. then accept exactly one key whose `normalize_model_id` equals the reported name's;
  3. return `(None, {})` on zero or several matches, and on a missing or unreadable file as today.

  Replace the docstring's `claude-opus-5` example with `claude-haiku-4-5-20251001` → `anthropic/claude-haiku-4.5`, and state the version guard and the ambiguity rule. That pair is the only model ID in `collect.py`'s docstrings and comments. Describe the cloud wrappers by their patterns, not with a full Bedrock or Vertex ID, which would fall under guard Rule B (design §Coordination). Verify:
  - the tests from 1.2–1.4 pass;
  - `test_resolve_model_returns_nothing_for_an_unknown_model` still passes;
  - `grep -nE 'claude-[a-z]+-[0-9]' skills/proposal-troubleshoot/scripts/collect.py` shows only the docstring pair.
  - Done: all 58 tests in `test_troubleshoot_collect.py` pass, including the unknown-model test. The grep hits only lines 572-573, the two halves of the docstring pair.

## 3. Skill prose

- [x] 3.1 In `skills/proposal-troubleshoot/SKILL.md`, rung 1, replace the matching sentence at line 39 with the rule from the spec delta. Proposed wording:

  > Read the shipped verdicts at `references/model-support.json` relative to this skill's directory. Look up the running model by the exact identifier your host states — not a display name, and not an alias such as `sonnet`, which names no version. When that exact string is absent, compare spellings instead: ignore letter case, everything up to the last `/`, a cloud provider's wrapping such as a leading `us.anthropic.` or a trailing `-v1:0`, a trailing date stamp, and a bracketed suffix such as `[1m]`, and read a dash between two digits as a dot. Claude Code reports `claude-haiku-4-5-20251001` where the data keys the same model as `anthropic/claude-haiku-4.5`. A different version number is a different model: never take the verdict of the nearest version, and when two entries fit equally, treat the model as having no entry.

  Leave the three bullets beneath it unchanged. Verify: the title, the header blocks (purpose, workflow line, voice, mandate) and the pinned mandate are untouched, so `tests/unit/test_skill_header_pattern.py` passes.
  - Done: the proposed wording was used verbatim, and the three bullets are unchanged. `test_skill_header_pattern.py`, `test_report_offer.py` and `test_pinned_sentences.py` pass.
- [x] 3.2 In the same file, change assembling-the-report step 4's bullet "your own model identifier and harness" to ask for the exact identifier the host states, not a display name or an alias, plus the harness. Keep the "write that you do not know it rather than guessing" sentence. Verify: the bullet reads as specified and `uv run poe conform` passes.
  - Done: the bullet reads "your own model identifier exactly as your host states it — not a display name, and not an alias such as `sonnet` — and your harness". The "write that you do not know it rather than guessing" sentence is unchanged. `uv run poe conform`: all 11 skills conform (skills-ref@0.1.5).
- [x] 3.3 Add `tests/unit/data/pinned_sentences/proposal-troubleshoot--model-match.txt`. It holds the verbatim substring from "Claude Code reports `claude-haiku-4-5-20251001`" through "never take the verdict of the nearest version". Add a parity test to `tests/unit/test_troubleshoot_collect.py` that:
  1. reads that pin;
  2. extracts its first two backticked spans;
  3. asserts that `resolve_model` maps the first to the second over a synthetic support file holding only the second.

  Verify: `tests/unit/test_pinned_sentences.py` and the parity test pass. Rewording either the sentence or the example breaks one of them.
  - Done: the pin was added, and the parity test is `test_the_pinned_rung_one_example_resolves_through_resolve_model`. Both pass, 93 tests across the two files.

## 4. Eval, projection, issue template

- [x] 4.1 In `harness/skill_evals.py`, change the `troubleshoot_model_rung` prompt's "I was running claude-haiku-4.5" to "I was running claude-haiku-4-5-20251001". Update the comment block above it (`:1031-1036`, which names `claude-haiku-4.5` today) to say that the prompt uses the spelling Claude Code reports, so the rung-1 matching rule is exercised. The comment names no model ID except `claude-haiku-4-5-20251001`: guard Rule A counts comments, and the guard's (path, token) pair exempts only that token (design D7). Leave `verdict_troubleshoot_model_rung` and the task's scorers unchanged. Verify:
  - `tests/unit/test_eval_wiring.py` passes;
  - `grep -n 'claude-haiku-4.5' harness/skill_evals.py` no longer hits the troubleshoot comment or prompt. The judge default in the module docstring and in `JUDGE_MODEL` belongs to `track-model-currency` and stays.
  - Done. The comment now says the user ran haiku and that the prompt names it as `claude-haiku-4-5-20251001`, the spelling Claude Code reports. It names no other model ID. `test_eval_wiring.py` passes (47). The scorers and `verdict_troubleshoot_model_rung` are unchanged. Note on the grep: written as given, the pattern's unescaped `.` matches the dash in `4-5`, so it also hits the new spelling at lines 1035 and 1057. The literal form, `grep -nF 'claude-haiku-4.5'`, hits only line 13 (docstring) and line 75 (`JUDGE_MODEL`), both owned by `track-model-currency`.
- [x] 4.2 Regenerate the projection with `uv run python harness/eval_export.py`. Verify: only `skills/proposal-troubleshoot/evals/evals.json` changes (the prompt line), and `uv run python harness/eval_export.py --check` exits 0.
  - Done: the script wrote only `skills/proposal-troubleshoot/evals/evals.json`, a one-line diff in the prompt, and `--check` exits 0.
- [x] 4.3 In `.github/ISSUE_TEMPLATE/skill-defect.yml`, change the `self_reported` placeholder from `claude-sonnet-5` to `claude-sonnet-5-5`. Verify: the placeholder reads `[self-reported] model: claude-sonnet-5-5`, and `git diff` shows a one-line change with unchanged indentation. No test reads this file, checked by grep on 2026-10-05.
  - Done: one line changed (`1 insertion, 1 deletion`), indentation kept at eight spaces. No file under `tests/`, `harness/` or `scripts/` names `skill-defect.yml`, re-checked by grep.

## 5. Guard hand-off and gate

- [x] 5.1 Guard hand-off (design.md §Coordination, guard table). This change edits nothing in the guard. No troubleshoot file is parked there, and `track-model-currency` alone writes the `troubleshoot_model_rung` (path, token) pair, swapping it in its task 6.1 if needed. Do not create `tests/unit/test_model_ids.py`, and do not edit that change's folder. Verify: `git diff --stat` lists no `tests/unit/test_model_ids.py`.
  - Done: `git diff --stat` lists six files: the issue template, `harness/skill_evals.py`, and in `skills/proposal-troubleshoot/` the `SKILL.md`, `evals/evals.json` and `scripts/collect.py`, plus `tests/unit/test_troubleshoot_collect.py`. The new pin is untracked. `tests/unit/test_model_ids.py` does not exist, and `openspec/changes/track-model-currency/` was not touched.
- [x] 5.2 Run `uv run poe test`, `uv run poe cov` and `uv run poe specs`. Verify:
  - all three are green;
  - ruff is clean;
  - no generated-copy drift (`references/model-support.json` is untouched);
  - coverage is at or above the 78% floor;
  - `openspec validate --all --strict` passes.

  Record the counts here. No model call, metered or subscription, happens in this step.
  - Recorded 2026-10-05:
    - `poe test`: 2016 passed; ruff "All checks passed!"; `sync_shared.py --check` "generated copies in sync"; all 11 skills conform (skills-ref@0.1.5).
    - `poe cov`: 2016 passed, total 84.73% against the 78% floor; `collect.py` 93%.
    - `poe specs`: 21 passed, 0 failed.
    - `references/model-support.json` is untouched.

## 6. Optional behavioural check of the prose (not required to archive)

- [x] 6.1 Preferred, $0 on the subscription. There are two ways to run it.
  - **If a `troubleshoot_model_rung` dev-runner scenario exists by then** (design.md, Open Questions): run `uv run poe dev troubleshoot_model_rung --model claude-haiku-4-5-20251001 --isolated`. Once `add-dev-runner-judge` has landed, the runner strips the billing variables and reports an API-billed, overage or unreported-rate-limit run as untested (exit 3). Record such a run as untested, not as an outcome.
  - **Otherwise:**
    1. make a scratch workspace in the session scratchpad, never under the repository or the private proposals directory;
    2. copy `skills/proposal-troubleshoot` into its `.claude/skills/`;
    3. copy the `f05-slr-interviews` fixture proposal into it;
    4. prepare an environment with every `ANTHROPIC_*` variable, every `CLAUDE_CODE_USE_*` switch and `OPENROUTER_API_KEY` unset. That is the billing strip of `add-dev-runner-judge` design D3: it closes the API-key, gateway (`ANTHROPIC_BASE_URL` plus `ANTHROPIC_AUTH_TOKEN`) and cloud-provider routes. In it, `claude auth status --json | jq '{authMethod, apiProvider}'` must show `claude.ai` and `firstParty`. Read only those two fields, never the email or organization. Otherwise, do not run;
    5. from the workspace, in that environment, ask the 4.1 prompt once with `claude -p --model claude-haiku-4-5-20251001 --max-budget-usd 1 --output-format stream-json --verbose`, saving the stream in the scratch workspace;
    6. check the saved stream with `jq` (`add-dev-runner-judge` design D5, checks 3 and 4): `init.apiKeySource` is `none`, and at least one `rate_limit_event` exists, none with `isUsingOverage: true` and none with a status outside `allowed` and `allowed_warning`. If any check fails, record the run as untested, because it may have been billed. Do not re-run it.

    Note in the record that the ambient user configuration was loaded.

  Verify: the answer names haiku's recorded `fail` for `proposal-write` as the cause, gives a remedy, and writes no `bug-report/`. Record the outcome, the resolved model and the CLI version here. One call, never in a loop. A failing outcome goes to the Open Questions follow-up (a lookup mode, design D1), not to a re-run.
  - Run 2026-10-05, one call, "otherwise" path: no `troubleshoot_model_rung` dev-runner scenario exists, because `add-dev-runner-judge` has not landed.
    - **Setup.** The scratch workspace was `troubleshoot-ws/` in the session scratchpad, holding the skill copy at `.claude/skills/proposal-troubleshoot/` and the f05 proposal. `evals/` and `__pycache__/` were removed from the copy, since measured environments carry no eval definitions.
    - **Environment.** The only variable present from the strip set was `ANTHROPIC_BASE_URL`, which was unset. No `CLAUDE_CODE_USE_*` variable and no `OPENROUTER_API_KEY` was present. Names were listed, never values. `claude auth status --json | jq '{authMethod, apiProvider}'` gave `claude.ai` and `firstParty`.
    - **Stream checks.** `init.apiKeySource` was `none`. There was one `rate_limit_event`, with status `allowed_warning` (seven-day window, utilisation 0.85) and `isUsingOverage: false`. All fail-closed checks passed, so the run counts as tested. The CLI's notional `total_cost_usd` was $0.029; it was not billed.
    - **Resolved model:** `claude-haiku-4-5-20251001`. **CLI:** 2.1.284. The ambient user configuration was loaded: three SessionStart hooks, plus the plugins caveman, superpowers, agents-md and telemetry (53 skills listed).
    - The stream was saved as `troubleshoot-stream.jsonl` beside the workspace, not inside it, so the agent under test could not read it. This is a deliberate small deviation from step 5.
    - **Outcome: FAIL, and rung 1 was not exercised.** `proposal-troubleshoot` was listed in `init.skills`, but haiku made no Skill or Read call (`num_turns` 1). It answered from general knowledge and asked for more detail. It did not name haiku's recorded `fail` for `proposal-write`, and its remedy was clearing a plugin cache. No `bug-report/` was written, because the workspace holds only the proposal.
    - **Reading.** This is a routing failure. The rule was never misapplied, because the skill was never loaded. It matches the earlier haiku routing finding (0/3 Skill calls on polish prompts, 2026-10-04). The design D1 lookup mode would not fix it, since that also needs the skill loaded. The follow-up that fits is routing, through the skill's description, not the matching rule. Per this task there is no re-run. The L0 tests remain the decisive coverage for the rule (design, Open Questions).
- [ ] 6.2 Metered fallback, only if 6.1 is impossible. Run `troubleshoot_model_rung` on Inspect through the cost gate. Show the estimate first and wait for the user's explicit approval of that amount. Never pass `--yes` on their behalf, and per the subscription-first policy prefer a non-Anthropic roster model as the model under test. Verify: the gate printed an estimate and the user approved it in chat before any call. Record the actual spend beside the estimate.
  - Not triggered, because 6.1 was possible and ran. Deferred: it needs explicit user approval. No estimate was computed in this session; the cost gate prints one before any call. No metered call was made.

## 7. Archive and commit

- [ ] 7.1 Archive with the `openspec-archive-change` skill (`openspec archive fix-troubleshoot-model-match`), which folds the two MODIFIED requirements into `openspec/specs/skill-troubleshoot/spec.md`. Then re-run the gate on the synced tree, because the archive writes a file that 5.2 never saw. Verify:
  - `uv run poe specs` passes after the archive;
  - `uv run poe test` passes after the archive (the model-ID guard is not in this tree, so the grep below stands in for it);
  - the main spec holds the new scenarios;
  - `grep -nE 'claude-(haiku|sonnet|opus|fable)-[0-9]|gpt-[0-9]|anthropic/' openspec/specs/skill-troubleshoot/spec.md` is empty (design D8).
  - Note written before archiving: `.claude/settings.json` denies edits under `openspec/changes/archive/`, so 7.1 and 7.2 cannot be ticked once the folder has moved. Their results (post-archive gate, grep, commit) are recorded in the commit message instead, following `steer-subscription-first`.
- [ ] 7.2 Commit the completed change as one commit, off `main` until it is complete, with the attribution trailer. Do not push. It must reach `main` before `track-model-currency` task 6.1 (task 0.1). Verify: `git status` is clean apart from the user's own untracked files, and `git log -1` shows the commit.
