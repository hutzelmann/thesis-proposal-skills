# Make the Write Skill Verify Its Own Output

## Why

`write_from_seed` is the only check-gated eval whose skill cannot run the check: proposal-write ships no script and its SKILL.md only *suggests* the check skill to the user. The failure modes this leaves open are diverse — a `[TODO: …]` methodology heading when the seed defers the choice, a metadata block left unterminated by an edit, fabricated citation keys, missing `(RQn)` references — but every one of them is an error the mechanical check names precisely. Experiments confirm the asymmetry is load-bearing: haiku failed 3/3 baseline dev runs and passed 2/2 once told to run the check and fix what it reports. A second, independent defect sits in the harness: both runners grade a hardcoded filename while SKILL.md licenses creating a fresh `<slug>.md`, so a compliant run that drafts into a new file is graded against the untouched seed ("four missing canonical sections").

## What Changes

- proposal-write ships its own synchronized copies of the check script and the structure skeleton (same packaging path as proposal-import: core-function asset → synchronized copy, entering the sync map and the drift check).
- proposal-write's SKILL.md gains a "Verify before you report" run–fix–rerun section mirroring proposal-import's, including its two don't-fix carve-outs: a reference-count shortfall is reported, not padded with invented sources; honest open `[TODO: …]` markers stay.
- proposal-write's SKILL.md gains a decision rule for material that defers the methodology choice: pick the methodology from the closed set that the research questions best support, keep the section heading canonical, and record the uncertainty as `[TODO: confirm methodology choice]` in the section body — a heading never carries a TODO marker.
- Both harness runners stop grading `write_from_seed` against the staged seed filename and instead locate the produced proposal, the way the import scenario already judges a file whose name the skill chooses.
- The `write_from_seed` eval task stops staging the check script as harness-side extras — the skill now ships its own copies, so standard skill staging provides them to model and scorer alike.

No breaking changes. The seed fixture, its oracle, and the tolerated-error set are untouched.

## Capabilities

### New Capabilities

None. This change extends existing capabilities.

### Modified Capabilities

- `skill-write`: gains a self-verification requirement (run the shipped check before reporting, fix what it names, with the two explicit carve-outs) and a methodology-decision requirement for source material that defers the choice (decide from the closed set, canonical heading, TODO in the body).
- `testing-harness`: the produced-file-location requirement, currently stated for the import scenario, generalizes — a verdict over a scenario whose skill may choose the produced file's name SHALL locate that file rather than assume a staged name.

## Impact

- `shared/` sync: `scripts/sync_shared.py` map gains `skills/proposal-write/scripts/check.py` and `skills/proposal-write/references/structure.json`; commit hook and drift check cover them automatically.
- `skills/proposal-write/SKILL.md`: verify-before-report section, methodology-decision rule, script path addressing per the packaging rules.
- `harness/claude_runner.py`: `write_from_seed` verdict locates the produced proposal instead of reading `scenario["proposal"]` only.
- `harness/skill_evals.py`: `write_l1`/`write_l2_rq_quality` scorers locate the produced proposal; `write_from_seed` task drops the `extra_skill_files` staging of check.py/structure.json.
- `harness/l1_checks.py`: produced-file selection becomes a pure, L0-testable helper shared by both runners.
- New L0 tests for the selection helper; existing sync drift test covers the new copies.
- Not touched: fixtures, oracles, `DRAFT_ALLOWED_ERRORS`, proposal-check, proposal-import.
