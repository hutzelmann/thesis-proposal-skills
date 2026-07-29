# Proposal: polish-style-and-evals

## Why

Three open ends from archived changes: the compact numeric citation style (migration step 4 follow-up; output currently author-date), the ideate multi-turn persona eval (rubric exists, task does not), and the post-fix harness validation run (finding logged in harness/README.md).

## What Changes

- `templates/compact-numeric.csl`: numeric style close to the legacy biblatex numeric-comp look (bracketed numbers, initials, up to 5 names in the bibliography, DOI shown); wired into publish.py.
- `harness/skill_evals.py` gains `ideate_socratic`: a persona-driver dialogue (simulated student model) scored L1 (seed file exists per spec) and L2 (Socratic rubric).
- Validation runs of `check_report` (post-fix) and the new task; findings logged.
- `skip_specs: true` — follow-ups of implemented capabilities.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

Publish output style changes (numeric citations); no API/spec changes.
