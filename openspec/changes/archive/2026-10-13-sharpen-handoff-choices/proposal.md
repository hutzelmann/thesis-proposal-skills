## Why

`add-stage-handoffs` left two gaps on sonnet (2026-10-13 dev runs, recorded in its archived tasks.md). First, asked "What do we do now with that feedback?" after a review, sonnet names the decision a blocker needs and recommends an option, but neither quotes the student's own passage nor offers a way out — the judge fails it every round, and it is the shape the user rejected in the design conversation ("the question is not socratic and leaves the student a bit lost"). The shared block states the rule only in the abstract; the models do not pick it up from that. Second, a cold "apply the blocker from the review" request was carried out as a bare edit with no skill loaded in rounds 1 and 2. The reworded write description that landed with the change fixed it — a re-measurement passed 2/2 on sonnet, writing skill loaded — but no scenario keeps that path measured.

## What Changes

- **The anchored choice gets an operational shape and one worked example** in `shared/blocks/handoff.md`: quote the passage the choice concerns, say what it changes, offer at most three options from the student's own material, end with "or something else". The example is the one agreed in the design conversation (RQ2 "improve test quality", mutation score vs faults found). Materialized into all eleven skills; the paragraph count stays three.
- **A sixth handoff scenario, `handoff_direct_revision`**: the cold direct request over `w11-blocker-revision`, single turn, judged by the after-revision verdict without a status turn — the writing skill loaded, the blocker applied, the review untouched, the check clean, a fresh review recommended. Rubric twin as for the other five.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: "Handoff coverage" gains the direct-request scenario.

The block's example refines the existing skill-packaging rule ("quote what the student's own text already says … plus a way out") without changing it, so skill-packaging carries no delta.

## Impact

- `shared/blocks/handoff.md` and the eleven materialized `## Handing over` sections; body sizes re-checked.
- `harness/claude_runner.py` (scenario and verdict dispatch, already drafted for the measurement), `harness/l2_rubrics.py` (`HANDOFF_SCENARIOS`), `harness/README.md`, `tests/unit/test_handoff_runner.py`.
- Cost: subscription dev runs only — `handoff_review_feedback` twice and `handoff_todos` once on sonnet; haiku is out of scope by the user's decision.
