## 1. Guidance data

- [x] 1.1 `shared/structure.json`: add `timeline` to `sections.order` (last) and `sections.titles` (`en: "Timeline"`, `de: "Zeitplan"`)
- [x] 1.2 `shared/structure.json`: remove `timeline` and `zeitplan` from `forbidden_heading_patterns`; add `gantt`, `workpackage`, `arbeitspaket`; keep `schedule`, `time plan`, `work plan`, `workplan`, `milestones`, `arbeitsplan`, `meilensteine`
- [x] 1.3 `shared/structure.json`: add the timeline size constraint (max non-empty lines = 3; no table, list, or subsection) and the `work_plan_patterns` subset that `timeline_detail = "detailed"` un-forbids
- [x] 1.4 `shared/guidelines/guidelines.md`: add the fifth section to §Proposal Structure with its one-sentence rule and the as-soon-as-possible alternative; add the `Timeline | Zeitplan` row to the canonical-titles table
- [x] 1.5 `shared/guidelines/guidelines.md`: rewrite the must-not sentence (line 16) — work plans, phase breakdowns and milestone tables stay forbidden, a coarse start/submission statement does not; note that section order is now enforced
- [x] 1.6 `shared/guidelines/guidelines.md`: document `timeline_detail` in the override paragraph (line 4)
- [x] 1.7 Run `python3 scripts/sync_shared.py` and confirm `--check` is clean

## 2. Check script

Source of truth is `skills/proposal-check/scripts/check.py`; the `proposal-write` and `proposal-import` copies are vendored by sync.

- [x] 2.1 Read `timeline_detail` from overrides (default `"simple"`); reject an unknown value with a parse-style error rather than silently defaulting
- [x] 2.2 Section-order check: compare canonical titles found in `headings()` document order against the expected sequence; report `section out of order: X before Y` as an error. Match methodology by its title prefix
- [x] 2.3 Expected order resolution: `sections.order` by default, the `required_sections` override list's own order when present
- [x] 2.4 Timeline body guard: within `section_text(body, <timeline title>)` report an error for a table row, a list item, a subsection heading, or more than three non-empty lines. Name which one was found
- [x] 2.5 `timeline_detail = "detailed"`: skip the body guard and drop the work-plan patterns from the effective forbidden list
- [x] 2.6 Verify no surviving forbidden pattern is a substring of `Timeline` or `Zeitplan` (regression guard, since matching is substring-based) — pinned as a test in 7.5
- [x] 2.7 Run `python3 scripts/sync_shared.py` to re-vendor the two copies

## 3. Skills

- [x] 3.1 `proposal-write/SKILL.md`: "four canonical sections" → five (line 32); state that the timeline is written from a supplied timeframe, that an unknown timeframe becomes `[TODO: state start month and submission month, or "as soon as possible"]`, and that as-soon-as-possible is never a default
- [x] 3.2 `proposal-check/SKILL.md`: extend the Step 2 agent pass (lines 36-41) with the positive timeframe check — accept semester/quarter/season phrasings in both languages, flag a section that names no timeframe, and flag a Gantt chart supplied as an image
- [x] 3.3 `proposal-import/SKILL.md`: "four canonical sections" → five (line 79); rewrite the strip rule (line 87) to distill first/last month from a source work plan into the timeline section, strip the phase detail, and report both in the removal note; TODO stub when nothing is recoverable. Also added the Timeline section to the shape template
- [x] 3.4 `proposal-import/SKILL.md`: add the explicit reorder step, since section order is now an error
- [x] 3.5 `proposal-customize/SKILL.md`: document `timeline_detail` in the TOML key list (line 21-22) and its merge semantics; replace the timeline example with the detailed-work-plan example at lines 3, 8, and 29
- [x] 3.6 `proposal-ideate/SKILL.md`: at the seeding step (line 41-46) ask for the timeframe once and record it as a body note, explicitly not as a section; leave the Socratic part unchanged
- [x] 3.7 Confirm `tests/unit/test_skill_header_pattern.py` still passes — no mandate text changed, so no pinned copy under `tests/unit/data/skill_mandates/` should need editing

## 4. Fixtures — clean proposals gain the section

Add a real one-sentence timeline as the final section.

- [x] 4.1 English (`# Timeline`): `f00-clean-en`, `f05-slr-interviews`, `f06-prototype-testbed`, `f13-pure-slr`, `f16-figures-import`, `f17-theoretical`, `f18-broken-refs`, `f19-drift-alert-validity`, `w03-snowball-seed`
- [x] 4.2 German (`# Zeitplan`): `f11-migration-architecture`, `f12-clean-de`, `f14-user-study`
- [x] 4.3 Confirm all twelve still report `exit_code: 0` with unchanged warning lists. `f18` and `f14` use the as-soon-as-possible form; `f19` uses the TODO form, so it now carries a fifth intentional marker

## 5. Fixtures — broken proposals gain the missing-section error

Bodies stay as they are; only `expected.json` changes.

- [x] 5.1 English, add `required section missing: \`Timeline\``: `f03-compliance-audit`, `f07-network-pathfinding`, `f09-llm-compliance-docs`, `f10-risk-scoring`, `f15-format-broken`, `w01-ideate-seed`
- [x] 5.2 German, add `required section missing: \`Zeitplan\``: `f01-narrative-sketch`, `f04-dsr-vendor-heavy`, `f08-concept-sketch`
- [x] 5.3 `f02-tool-comparison` special case: its `# Zeitplan` heading (with a five-phase Gantt table under it) is now the canonical German title. Remove `forbidden section: \`Zeitplan\` (matches \`zeitplan\`)` from the oracle, add no missing-section error, and add the body-guard error the table now triggers
- [x] 5.4 Confirm `f01`, `f03`, `f09`, `f10` still report their existing forbidden-heading errors — `arbeitsplan`, `milestones`, `work plan` all survive the pattern surgery. The new `work package` pattern additionally catches `f03`'s `2 Objectives and Work Packages`, which the old list missed; pinned in its oracle

## 6. Fixtures — new and repurposed

- [x] 6.1 New fixture isolating the body guard: `f20-timeline-gantt`, otherwise-clean English proposal whose `# Timeline` section carries a phase table. Oracle pins exactly the two guard errors. Row added to `tests/fixtures/README.md`
- [x] 6.2 Repurpose `w02-override-workspace`: `guidelines.md` TOML becomes `min_references = 8` plus `timeline_detail = "detailed"`, prose rewritten to a supervisor demanding a work plan; proposal body gains a phase table under `# Timeline`; oracle keeps the reference-count error and asserts no timeline error; semantic note rewritten
- [x] 6.3 `tests/fixtures/README.md`: update the forbidden-content row and the `f02` row to match the new behavior

## 7. Unit tests

- [x] 7.1 `tests/unit/test_check.py`: replace the timeline-un-forbidding override test (around line 60) with a `timeline_detail = "detailed"` test — plus tests that the detailed mode un-forbids work-plan headings, that the default keeps them forbidden, and that an unknown mode value is reported
- [x] 7.2 `tests/unit/test_harness_helpers.py`: replace the `Timeline` forbidden-section sample strings (lines 41-43) with a still-forbidden heading. Also retargeted the relay-count pin from `1/5` to `1/6`, since f15's oracle gained the missing-Timeline error
- [x] 7.3 New tests: missing timeline section is an error; each body-guard violation (table, list, subsection, four lines) is an error individually; three lines passes; `timeline_detail = "detailed"` suppresses the guard
- [x] 7.4 New tests: section-order violation is an error; correct order passes; a `required_sections` override supplies its own order; order check ignores non-canonical headings
- [x] 7.5 New test (pins 2.6): no forbidden pattern is a substring of any canonical title in either language; `work_plan_heading_patterns` is a subset of the forbidden list; `schedule` and `time plan` are excluded from it. All in `tests/unit/test_timeline_section.py`

## 8. Harness

- [x] 8.1 `harness/skill_evals.py` (lines 421-434): rewrite the customize task prompt to the detailed-work-plan requirement and the scorer to assert `timeline_detail = "detailed"` plus `min_references = 8`, replacing the `"timeline still forbidden"` verdict
- [x] 8.2 `harness/sources.py` (line 22): adjust the synthetic source heading so it still exercises a forbidden work-plan pattern — now `3 Work Plan and Milestones`, and absolute months were added so the import scenario exercises the distill path rather than only the TODO-stub path
- [x] 8.3 Run the rewritten customize eval task once to confirm it scores (metered — single run, not a loop). `openrouter/anthropic/claude-haiku-4.5`, accuracy 1.000: the model reached for `timeline_detail = "detailed"` rather than editing `forbidden_sections`, which is what the rewritten guidance intends

## 9. Documentation

- [x] 9.1 `README.md` "For supervisors": drop "The defaults forbid timelines"; state that the defaults require a one-sentence timeline and forbid work plans and Gantt charts
- [x] 9.2 `README.md` skill table: replace the `proposal-customize` row's `"timeline required"` example with the detailed-work-plan one
- [x] 9.3 `docs/getting-started.md` line 46: replace the *"My supervisor wants a timeline"* prompt with the detailed-work-plan prompt

## 10. Demo re-run (last — requires implementation complete)

- [x] 10.1 Run a real session on the existing synthetic drift topic through `proposal-write` → `proposal-check`, so the output reflects the five-section structure. Two turns, `claude -p --model sonnet`, in a fresh workspace holding the turn-5 proposal verbatim: the check reported the missing Timeline and the agent explicitly refused to invent a timeframe; once given the start condition it wrote the sentence and left the submission month as a TODO
- [x] 10.2 Append the trimmed raw output to `docs/demo/harvest.log` as turns 8-9, with a header note recording the date, model, and starting file state
- [x] 10.3 Re-condense `README.md` demo block 3 from that output: the section list gains Timeline, and the `proposal-check` quote no longer claims "no timelines". Every shown line must trace to the log. Also dropped the stale "author name" TODO from the write beat — proposals have been anonymous since before this change, and the session confirms only four TODOs existed
- [x] 10.4 Align `f19-drift-alert-validity` with the session it claims to derive from: the fixture now carries the timeline sentence turn 9 actually produced, and its oracle pins the fifth TODO warning

## 11. Verification

- [x] 11.1 `uv run pytest` — 371 passed
- [x] 11.2 `uv run ruff check .` — clean
- [x] 11.3 `python3 scripts/sync_shared.py --check` — in sync
- [x] 11.4 `openspec validate --all --strict` — 14 passed
- [x] 11.5 Build one English and one German fixture PDF via `proposal-publish` to confirm the fifth heading renders and does not orphan at a page break — f00 renders §5 Timeline on a single page, f12 renders §5 Zeitplan with only the bibliography spilling to page 2
