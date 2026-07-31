# Tasks: Write Self-Verification and Produced-File Grading

## 1. Packaging — write ships its own check

- [x] 1.1 Add `skills/proposal-check/scripts/check.py → skills/proposal-write/scripts` and `shared/structure.json → skills/proposal-write/references` to `SYNC_MAP` in `scripts/sync_shared.py`, with a comment stating the reason (write verifies its own output; packaging spec's core-asset rule)
- [x] 1.2 Run `scripts/sync_shared.py`; confirm the copies materialize with generated-file markers and `scripts/sync_shared.py --check` passes

## 2. Skill instructions

- [x] 2.1 Add a "Verify before you report" section to `skills/proposal-write/SKILL.md` mirroring proposal-import's: run `python3 .claude/skills/proposal-write/scripts/check.py <slug>.md` (skill-relative location and Windows `py` named), fix every error and re-run, the two don't-fix carve-outs, the script-missing rule
- [x] 2.2 Add the methodology-decision rule to the "From scratch" section: source material defers the choice → pick the best-supported methodology from the closed set, canonical heading, `[TODO: confirm methodology choice]` in the body; headings never carry TODO markers
- [x] 2.3 Rework "Finishing a pass" to report what the check still finds; reconcile the existing "suggest the check skill" sentence with the new loop
- [x] 2.4 Sweep `docs/` and `AGENTS.md` for statements the change invalidates (write has no scripts; which skills self-verify) and correct them

## 3. Harness — grade the produced file

- [x] 3.1 Add pure `select_draft(files, seed_name, seed_original)` to `harness/l1_checks.py` per design D2 (fresh-file preference, in-place edit fallback, `None` → "no draft produced (seed untouched)", artifact exclusions, deterministic tie-break with candidate list)
- [x] 3.2 Use it in `harness/claude_runner.py`'s `write_from_seed` verdict path; collapse `produced_proposal()` (import path) into the shared helper
- [x] 3.3 Use it in `harness/skill_evals.py` `write_l1` and `write_l2_rq_quality` (list workspace markdown, select, grade the selection)
- [x] 3.4 Drop the `extra_skill_files` staging of `check.py`/`structure.json` from the `write_from_seed` task — the skill's own copies now stage via `stage_files`

## 4. Tests

- [x] 4.1 L0 tests for `select_draft`: in-place edit, fresh file with seed untouched, fresh file plus edited seed, nothing produced, exclusion of `guidelines.md`/`*-review.md`/`*-handout.md`, multi-candidate tie-break
- [x] 4.2 Confirm the sync drift check covers the two new copies (break one locally, watch it fail, restore)
- [x] 4.3 Full L0 suite green: `uv run pytest`

## 5. Model-in-the-loop validation

- [x] 5.1 Dev runner `write_from_seed --model haiku` at least 3×: expect PASS with a decided canonical methodology heading, intact metadata block, TODO-confirm marker in the body — 3/3 PASS (was 0/3 before the change)
- [x] 5.2 Dev runner `write_from_seed --model sonnet` 1× as regression control — PASS; `import_messy` haiku also re-run PASS (its verdict path now shares `select_draft`)
- [x] 5.3 Inspect one kept haiku workspace end to end: check runs visible in behavior (decided heading, closed metadata block), no invented references, carve-outs respected — verified in all three workspaces; residual variance: one run padded the reference list with all-TODO placeholder entries instead of reporting the shortfall (structurally legal, nothing fabricated; candidate for a later check warning or L2 rubric point)
