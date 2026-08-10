# Add proposal-supervise

## Why

The nine existing skills cover the student side of proposal work; the supervisor side has nothing. A professor who receives a raw submission (PDF, Word export, pasted email text) today either reviews it by hand or improvises with the student-facing skills, and the student gets feedback with no path into the toolchain. A tenth skill closes the loop: curated supervisor feedback out, a continuable artifact back to the student, and every letter steers the student into the skill set.

## What Changes

- New skill `proposal-supervise` (supervisor-side): accepts any raw submission, normalizes it via the vendored import pipeline, produces findings by reusing the check script and the review rubric, curates them to the 3–5 most thesis-blocking points, and writes a student-facing feedback package plus a professor-side full review.
- The feedback letter maps the review verdict to proposal state without committing the professor to any action, names load-bearing strengths, matches the submission language, discloses AI assistance in plain language, and closes with a getting-started blurb (en+de shared snippet) that steers the student to install the skills and continue from the attached imported file.
- The skill never sends anything; the letter is an explicit draft for the professor to edit and deliver through their own channel. No student registry and no personal data professor-side: import's personal-data strip applies, artifacts are slug-named idea files beside the professor's other proposals, lifecycle is manual.
- All nine existing skills get the updated workflow line naming the tenth skill (existing skill-packaging requirement; mechanical compliance).
- Testing: synthetic messy-submission fixtures, L0 coverage through the existing header-pattern/report-offer/sync machinery plus supervise-specific unit checks, and one L1 eval task asserting the package contract. Model-support matrix inclusion deferred to the next big metered run.

## Capabilities

### New Capabilities

- `skill-supervise`: supervisor-side feedback workflow — normalization of raw submissions, finding reuse from check and review, curation to pressing points, verdict-as-proposal-state, student-facing package with disclosure and steering, professor-side artifacts without personal data, draft-only delivery.

### Modified Capabilities

- `testing-harness`: new requirement covering the supervise L1 task — letter exists, at most five curated points, verdict present, no personal data in the send-package, skill pointers name real skills.

## Impact

- `skills/proposal-supervise/` (new): SKILL.md, vendored scripts (import pipeline, check.py), vendored references (guidelines), getting-started snippet en+de.
- `skills/proposal-*/SKILL.md` (all nine): workflow line updated to name the full ten-skill set.
- `scripts/sync_shared.py`: vendoring entries for proposal-supervise.
- `tests/unit/`: pinned mandate file, header-pattern roster grows to ten, report-offer roster, supervise-specific L0 tests.
- `tests/fixtures/`: synthetic raw-submission fixtures (pasted-email fragment, rough PDF-shaped text) with oracles.
- `harness/skill_evals.py`, `harness/l1_checks.py`: one new L1 task and its verdict functions.
- `harness/models.toml` / matrix: untouched now; supervise joins the matrix at the next metered run.
