# Tasks

## 0. Base

- [x] 0.1 Confirm the branch carries `main` at fefeced or later, which includes `route-polish-to-write`, `record-polish-routing-boundary` and `isolate-child-environment`. Verify:
  - `/usr/bin/git merge-base --is-ancestor fefeced HEAD` exits 0;
  - `grep -c '^\[\[cases\]\]' harness/routing_cases.toml` prints 46;
  - `uv run poe test` passes.

## 1. Routing cases

- [x] 1.1 Append `troubleshoot-report-collision` (kind `collision`) and `troubleshoot-report-oblique` (kind `oblique`) to the troubleshoot section of `harness/routing_cases.toml`, worded as in proposal.md.
  - Both expect `proposal-troubleshoot`, with `lang = "en"`.
  - A comment above the collision case says that it is the 6.1 request minus its model identifier (Rule A).

  Verify:
  - `uv run pytest tests/unit/test_routing.py tests/unit/test_model_ids.py` passes;
  - the case count is 48.
- [x] 1.2 In `harness/README.md`, change the routing case count in the `poe routing` example from 46 to 48. Verify by grep that no other routing case count is stale.
  - Found while implementing: the block's other three examples passed a literal `--` (`poe routing -- --model haiku`), which poe hands to the rig and argparse rejects. The first run 1 attempt failed this way, before any model call. Those three lines now pass their flags directly, and grep finds no other `poe … -- -` form in `README.md`, `AGENTS.md`, `harness/README.md`, `docs/` or `openspec/specs/`.

## 2. Pre-run record

- [x] 2.1 Record `claude --version` in `measurement.md`, and note that the rig's children start from `routing.isolated_env`, so no billing variable and no `CLAUDE_EFFORT` reaches them. Verify: the line is in `measurement.md`.

## 3. Haiku control (run 1)

- [x] 3.1 With the description as on `main`, run:

  ```
  uv run poe routing --model haiku --no-report --keep-events --case <15 ids>
  ```

  The 15 ids are the five troubleshoot cases plus `review-canonical`, `review-oblique`, `review-collision`, `review-canonical-de`, `review-ready-collision`, `write-canonical`, `write-oblique`, `write-collision`, `write-oblique-de` and `write-polish-collision`, for 45 measurements. Exit 1 is expected while haiku misroutes.

  Verify:
  - the run log `logs/routing/<stamp>.json` exists;
  - the D4 stream checks pass on the kept `events-*.jsonl`;
  - the resolved model is read from the `init` event's `model` field;
  - errored measurements are listed, and stay under a third of the run.

  Copy the per-case routes into `measurement.md`. A failed stream check records the run as untested and stops the measurement; it is not repeated.

## 4. Description edit (run 2, optional run 3)

- [x] 4.1 Replace the trigger clause of `skills/proposal-troubleshoot/SKILL.md` with the proposal's wording, leaving the what-clause byte-identical. Verify:
  - the description is 425 characters;
  - it contains "a skill misbehaved" once;
  - `uv run pytest tests/unit/test_skill_frontmatter.py tests/unit/test_skill_header_pattern.py` passes, including the combined metadata at 4472 of 4500.
- [x] 4.2 Run 2: the 3.1 command, unchanged, against the edited description. Verify as in 3.1, and record it beside run 1.
- [x] 4.3 Apply the D3 rule to runs 1 and 2, including its error rule, and write the arithmetic into `measurement.md`.
  - Under outcome 3, narrow the clause that stole (the "ignored the user's instructions" clause first), re-run 4.1's checks, run the 3.1 command once more as run 3, and apply D3 again.
  - Verify: `measurement.md` names the haiku-side outcome, 1, 2 or 4, with the counts that decide it.

## 5. Sonnet scan (run 4, optional run 5)

- [x] 5.1 Only under the haiku-side outcome 2, run on the edited description:

  ```
  uv run poe routing --model sonnet --epochs 1 --no-report --keep-events
  ```

  Verify:
  - all 48 cases were measured;
  - `docs/skill-routing.md` is unchanged (`git diff --stat`);
  - the D4 stream checks pass;
  - `measurement.md` lists every case whose route differs from the 138/138 report, and the sonnet routes of both new cases.

  Under outcomes 1 and 4, run 4 measures the final state with the original description. The change then rests on the 138/138 report plus the two new cases, so run it with `--case` limited to the five troubleshoot cases, which saves quota.
  - Done under outcome 4: five troubleshoot cases, 1 epoch. 4/5 correct, 0 errors, stream checks pass, `docs/skill-routing.md` untouched. The miss was `troubleshoot-report-oblique` in its first wording (measurement.md, Run 4).
- [x] 5.2 Only if run 4 has a miss that does not select `proposal-troubleshoot`: run 5 re-measures those cases with `--epochs 3 --no-report`, and the D3 sonnet rule is applied. Theft in run 4, or a regression in run 5, turns outcome 2 into outcome 4. Verify: `measurement.md` states the final outcome.
  - Done after rewording the case. Both models had answered that they could not see the earlier event it refers to, so the case is now self-contained.
  - Sonnet: 3/3 observed. The run is untested under D4, because the one kept stream carries no `rate_limit_event`.
  - The unused run-3 slot measured haiku on the new wording: 0/3.
  - Final outcome: 4. measurement.md states it.

## 6. Outcome edits

- [x] 6.1 Outcome 2, keep: add `"a bug they should report": "proposal-troubleshoot"` to `owned` in `tests/unit/data/trigger_terms.json`. Verify:
  - grep finds the phrase in no other `SKILL.md` description;
  - `uv run pytest tests/unit/test_skill_frontmatter.py` passes.
  - Not applicable. The outcome is 4, so `trigger_terms.json` is unchanged.
- [x] 6.2 Outcome 1 or 4, no edit: restore the description to `main`'s bytes. Verify: `/usr/bin/git diff main -- skills/proposal-troubleshoot/SKILL.md` is empty.
- [x] 6.3 Outcome 4 only: join the finding to haiku's polish `note` in `harness/models.toml` with `; ` (design.md D5), and add a TOML comment that cites `measurement.md`. The note gives the rig count and date, and the remedy of naming the skill in the request. Then regenerate the README with `uv run poe report --log-dir <main checkout>/logs/evals`. Verify:
  - the README diff is the haiku row only;
  - `docs/model-support.md` and `shared/model-support.json` are unchanged (`git diff --stat`);
  - `uv run pytest tests/unit/test_support_matrix.py tests/unit/test_model_ids.py` passes.
  - Done. The note says "0/33 on the routing rig, 2026-10-05". Its remedy is to invoke the skill by name (`/proposal-troubleshoot` in Claude Code) or use sonnet or opus, rather than to name it in the request; design.md D5 gives why.
  - The report read 10 logs, the newest from 2026-08-10. The README diff is the haiku row only, the other two outputs are unchanged, and 161 tests pass.

## 7. Record and gate

- [x] 7.1 Complete `measurement.md`:
  - setup: CLI version, resolved models, and the child-environment note;
  - one table per run;
  - the D3 arithmetic and the outcome;
  - cost: the rig reports none, because each case is killed at its route, so give any notional figure a kept stream carries;
  - the correction of the archived change's D1 follow-up (proposal.md, Why);
  - open items, including that the two new cases await the next 3-epoch sonnet sweep for the report (design.md D6).

  Verify that every run log in `logs/routing/` from this change appears in it.
- [x] 7.2 Run `uv run poe test` and `uv run poe specs`; both must exit 0. `python3 scripts/sync_shared.py --check` must report the generated copies in sync.
  - Done on a4e1b68 plus this change: 2739 passed and 2 skipped; ruff reports "All checks passed!"; all 11 skills conform; specs 19/19; the generated copies are in sync.

## 8. Archive and commit

- [x] 8.1 Archive with the `openspec-archive-change` skill; `skip_specs` means no spec is synced.
  - `.claude/settings.json` denies edits under `openspec/changes/archive/`, so tick 8.1 and 8.2 before the move.
  - Carry their results in the commit message: the post-archive `poe specs` and `poe test`, and the commit itself.

  Verify that `uv run poe specs` passes after the archive.
- [x] 8.2 Commit the change as one commit with the attribution trailer, and do not push. Merging into `main` needs the user's go-ahead, because this session runs in a worktree. Verify: `/usr/bin/git status` is clean, and `git log -1` shows the commit.
