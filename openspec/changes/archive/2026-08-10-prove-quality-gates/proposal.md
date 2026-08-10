# Prove Quality Gates

## Why

`sharpen-proposal-quality` (archived 2026-08-10) gave the skills a substance bar: ideate refuses to converge on generalities, write refuses to pad, review renders a three-tier verdict against five named substance tests, and every skill carries a neutral-tone voice block. None of it is instrumented: no persona probes the generic-content path, no fixture is hollow-but-mechanically-clean, no scorer judges draft prose density, and no rubric checks the no-praise rule outside the Socratic dialogue. Gates that ship unverified are gates the next model regression silently removes.

## What Changes

- **Probing-student persona**: agreeable, vague, extraction-minded ("sounds good, just write it down") — the opposite failure mode of the stonewaller's refusal. A new ideate task asserts no generic proposal is seeded: the swap test is voiced, persistent genericity ends in the impasse, notes recorded, nothing generated to force convergence.
- **Hollow fixture** `f22`: passes every mechanical check with zero findings, yet fails the swap, delta, and executability tests — generic well-sounding text with no object of study. Its oracle encodes check-clean; a new review task asserts the verdict "no viable thesis core" with at least two failed substance tests cited by name, on an untouched proposal.
- **Density scorer**: a new L2 scorer on `write_from_seed` judges the full draft body against the information-density rule — scene-setting openers, truisms, and swap-test-failing filler fail the grade.
- **Tone criteria**: the review-quality rubric gains the voice-block rules (no praise of the student or the draft, no self-congratulation, neutral constructive wording); the Socratic rubric's existing no-praise rule stays.
- **L1 verdicts as pure functions** in the shared verdict module, L0-tested without model calls, consumed by both runners where applicable.
- **Registration**: new tasks enter `models.toml` (task→skill map; matrix set where they qualify), scorer names respect the `*_l1*`/`*_l2*` contract the support classifier reads.
- **Calibration**: one metered cheap-model run per new instrument, findings recorded in tasks.md.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: the ideation dialogue suite gains the probing persona probe; new requirements cover hollow-fixture substance-verdict testing, proposal-prose density scoring, and tone criteria in the artifact-quality rubrics.

## Impact

- `harness/personas/` (+1 persona), `harness/rubrics/` (+1 density rubric, review rubric edited), `harness/skill_evals.py` (+2 tasks, +2 scorers), `harness/l1_checks.py` (+2 verdict functions), `harness/models.toml` (registration).
- `tests/fixtures/f22-*` (+proposal +expected.json), `tests/unit/` (L0 tests for new verdicts, oracle calibration, eval wiring).
- Metered spend: ~3 calibration runs on a cheap model (one per instrument family), plus judge calls.
