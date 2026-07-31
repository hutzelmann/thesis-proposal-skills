# Design: Write Self-Verification and Produced-File Grading

## Context

See proposal.md — Why. Constraints that shape the approach:

- The packaging spec's self-containment rule: an asset required for a skill's core function ships as a synchronized copy, never as a sibling fallback. proposal-import is the template — it ships `scripts/check.py` and `references/structure.json` as sync-map copies and its SKILL.md documents the run–fix–rerun loop.
- The testing-harness spec: every L1 verdict is a pure function in `harness/l1_checks.py`, reached by both runners, exercisable by L0 tests. The import scenario already grades a file whose name the skill chooses (`produced_proposal()` in `claude_runner.py`, glob in `import_l1`), but that selection logic lives runner-side and is duplicated.
- `harness/skill_evals.py` currently papers over the missing skill scripts by staging proposal-check's `check.py`/`structure.json` into `skill/` via `extra_skill_files` — scorer-only plumbing the model was never told about.

## Goals / Non-Goals

**Goals**

- One shared, pure produced-file selection helper; both runners grade the file it picks.
- proposal-write self-contained: its own check copy, its own structure skeleton, instructions that address them per the packaging path rules.
- Failure explanations that tell the truth: an untouched seed reads "no draft produced", not "four sections missing".

**Non-Goals**

- No new check rules, no changes to `DRAFT_ALLOWED_ERRORS`, no fixture or oracle edits.
- No self-verification for review/ideate/customize — their L1 verdicts are not check-gated, so the asymmetry this change removes does not exist there.
- No dev-runner scenario matrix changes beyond the write verdict path.

## Decisions

**D1 — Synchronized copy, not sibling fallback.** The verify loop is core to the new skill-write requirement; the packaging spec therefore forces the synchronized-copy path. `SYNC_MAP` gains `skills/proposal-check/scripts/check.py → skills/proposal-write/scripts` and `shared/structure.json → skills/proposal-write/references`. Alternative — sibling fallback on proposal-check — rejected: selective install of write alone must keep the loop functional, and the packaging spec says core assets ship as copies.

**D2 — Selection helper in `l1_checks.py`.** New pure function `select_draft(files, seed_name, seed_original)` where `files` maps workspace markdown names to contents. Returns `(chosen_name, why)` with `chosen_name = None` when nothing was produced. Preference order:

1. A file that was not staged (fresh `<slug>.md`), excluding the workspace override (`guidelines.md`) and skill artifacts (`*-review.md`, `*-handout.md`). Multiple fresh files: lexicographically first, with the candidate list in `why` so a surprising pick is visible.
2. Otherwise the staged seed, if its content changed (in-place edit — the common case).
3. Otherwise `None` — the verdict fails with "no draft produced (seed untouched)" instead of the misleading per-section errors.

`verdict_draft(text, check_output)` itself is unchanged; runners select first, then run the check over the selected file, then call the verdict. `claude_runner.produced_proposal()` (import path) collapses into the same helper so selection is defined once, per the spec's single-definition rule.

**D3 — Eval staging via the skill itself.** `write_from_seed` drops `extra_skill_files`; `stage_files` already stages any skill's `scripts/` and `references/`, so the same copies now serve model and scorer. The scorer's `skill/scripts/check.py` invocation path is unchanged. The dev runner keeps grading with the host-side proposal-check copy — the copies are sync-verified identical, so which one grades is immaterial.

**D4 — SKILL.md shape mirrors proposal-import.** A "Verify before you report" section with the same voice and the same two carve-outs (reference shortfall; honest open TODOs), the workspace-resolvable invocation `python3 .claude/skills/proposal-write/scripts/check.py <slug>.md` plus the skill-relative location and Windows `py` note, and the script-missing rule (say it did not run, name what went unverified). The methodology-decision rule lands in "From scratch" where the closed-set sentence already lives. "Finishing a pass" reports what the check still finds instead of only suggesting the check skill.

**D5 — Decision rule places the TODO in the body, never the heading.** The check's closed-set match is on the heading; a marker there is structurally unparseable as a methodology. The rule gives the model a legal way to be honest: decide from the closed set by what the research questions need, mark `[TODO: confirm methodology choice]` in the body. This codifies what sonnet does unprompted and what haiku, told only "mark anything missing as TODO", does not infer.

## Risks / Trade-offs

- [Model writes several fresh markdown files; helper picks the wrong one] → deterministic order plus candidate list in the explanation; L0 tests pin the tie-break.
- [Verify loop pressures the model to "fix" the reference shortfall by inventing sources] → the carve-out is stated in the same imperative form that holds in proposal-import's evals ("inventing a publication is the one unforgivable error").
- [Inspect's `message_limit=40` clips the run–fix–rerun loop] → observed loops cost 2–3 tool calls; the selfcheck experiment runs finished well inside headless-CLI budgets. If clipping appears, raise the limit for this task rather than weakening the loop.
- [Sync copies drift] → existing commit hook and drift check cover the two new map entries automatically; the L0 sync test fails on drift.

## Migration Plan

Sync map first, then SKILL.md, then harness — each step leaves the eval green or strictly more honest. No rollback complexity: all edits are additive or single-file rewrites in one repo.
