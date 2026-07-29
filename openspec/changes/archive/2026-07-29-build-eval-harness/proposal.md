# Proposal: build-eval-harness

## Why

L0 exists (54 tests); the testing-harness spec's L1 (structural, per skill × model) and L2 (rubric-judged) layers do not. The S1 spike fixed the architecture: Inspect AI, OpenRouter as the authoritative path, judges via `model_graded_qa`, `claude -p` as dev runner. This change turns that into runnable evals over the fixture corpus.

## What Changes

- `harness/skill_evals.py`: Inspect task factory — stages a fixture workspace into a sandbox, presents the skill's SKILL.md + a user request to the model under test (agent loop with bash/editor tools), then scores: L1 deterministic asserts (expected artifacts, oracle-driven check verdicts) + L2 rubric scorers (judge model, templates distilled from the guidance).
- Initial eval set: `write_from_seed` (w01 → full draft; L1: file valid + check clean-ish; L2: RQ quality rubric), `review_fixture` (f05 → review file; L1: `<slug>-review.md` exists, proposal untouched; L2: finds the mixed-methodology defect, stays format-agnostic on f10), `check_report` (f15 → agent relays the two-bucket report faithfully).
- `harness/rubrics/` — judge templates (RQ analytical quality, review actionability, Socratic compliance for later ideate evals).
- Spend caps via `--limit`/model choice; smoke-run one eval end-to-end on a cheap OpenRouter model to prove the harness.
- Replaces the S1 toy task (`rq_quality_task.py` stays as the minimal example).
- `skip_specs: true` — implements the testing-harness capability.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New: `harness/skill_evals.py`, `harness/rubrics/`, small `tests/unit` additions for pure helpers.
- Spend: cents per smoke run; full matrix runs remain deliberate, local, budget-capped.
