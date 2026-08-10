# Add supervise dev-runner scenario

## Why

`proposal-supervise` landed with L0 coverage and an Inspect L1 task, but no model has driven the skill end to end. The dev runner (`poe dev`, Max subscription) is the cheap loop for that, and it has no supervise scenario.

## What Changes

- New `supervise_feedback` scenario in `harness/claude_runner.py`: stages the `s01-raw-email` fixture (`.txt`, so the stage step learns to copy the submission file) with `proposal-import` installed as a sibling, and applies the existing five supervise verdicts to the produced send-package.
- New aggregate `verdict_supervise_package` in `harness/l1_checks.py` combining the five package verdicts, with L0 unit tests — the runner stays an adapter, per the repo conventions.

## Capabilities

### New Capabilities

None — dev tooling only (`skip_specs`); the supervise package contract is already specified in `skill-supervise` and `testing-harness`.

### Modified Capabilities

None.

## Impact

- `harness/claude_runner.py`: scenario entry, staging of a `.txt` submission, package-based verdict branch.
- `harness/l1_checks.py`: aggregate verdict function.
- `tests/unit/test_supervise_verdicts.py`: tests for the aggregate.
