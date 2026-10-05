# Design

## Context

See proposal.md, Why. The routing rig (`harness/routing.py`) decides a case from the first `proposal-*` Skill call, with only the frontmatter descriptions in front of the model. The dev runner (`harness/claude_runner.py`) runs the whole scenario and saves the host's event stream to `.devrun-events.jsonl` in a kept workspace. Both run on the Claude subscription. The precedent is discouraging: on 2026-10-03 a trigger-first variant of `proposal-supervise`'s description left haiku at 0/12 on the supervise cases (`2026-10-04-block-outward-tools-in-dev-runs/measurement.md`).

## Goals / Non-Goals

**Goals**
- Measure whether a description edit moves haiku onto `proposal-write` for a polishing request.
- Keep the edit only on evidence.

**Non-goals**
- No change to the write skill's body. Once loaded, its verify step already binds on haiku (3/3 `check.py` runs on `write_from_seed`, 2026-10-04).
- No change to `proposal-review`'s description. It keeps owning "ready for their supervisor" as a question about the proposal's state.
- No metered run. The Inspect twin of `write_repair_citations` is out of scope.

## Decisions

**D1. The polish case uses the scenario's request verbatim, both sentences.** The case reproduces the dev-run miss in the cheaper instrument. Trimming "I cannot answer any questions — decide and tell me what you did" would measure a different utterance from the one that failed. Alternative: the first sentence only. Rejected because a rig result and a dev-run result would then not be about the same input.

**D2. Both new cases are `collision` cases.**
- The polish case carries review's phrase ("ready for my supervisor") while its intent, changing the text, belongs to write.
- The guard case carries the moment write's new wording reaches toward ("ready for a supervisor") while its intent, a judgment on the proposal, belongs to review.

That is the dataset's definition of a collision. The ids add a qualifier (`write-polish-collision`, `review-ready-collision`) because `write-collision` and `review-collision` already exist.

**D3. The guard case names no file.** "Is my proposal ready for my supervisor?" is how a student asks. The rig stages its single default proposal for such a case, so "my proposal" has exactly one referent.

**D4. Staging extends `WORKSPACE_FIXTURES` rather than the case.** The rig derives staged files from the utterance (spec: "A routing case is measured in the workspace its utterance implies"). A `files` key per case is deliberately absent. Adding the fixture is the only way to stage a newly named file.

**D5. Ownership moves visibly.** "ready for a supervisor" in write's description does not literally collide with review's owned "ready for their supervisor", so the L0 table check would stay silent. If the edit is kept, "polishing pass" is added as a `proposal-write` phrase in `trigger_terms.json`. The boundary change then shows in review, as the table's own comment asks, and no other description may later claim the moment. "supervisor" stays a shared term.

**D6. Measurement protocol** (all on the subscription):
- **Before the edit** (cases added, description unchanged): haiku, the ten write and review cases (the eight existing plus the two new), 3 epochs, `--no-report`.
- **After the edit**: the same haiku subset, 3 epochs, `--no-report`. Then sonnet on the full set, 1 epoch, which rewrites `docs/skill-routing.md` with `--conditions-changed`. The case set grew from the 40 the report was measured on to 46, and the epoch count differs, so the earlier 119/120 is not a comparable predecessor (spec: "A conditions change invalidates comparison"). The regression comparison is therefore made case by case against that report in `measurement.md`, not through its supersedes line.
- **Dev runner**: 3 haiku runs of `write_repair_citations` with `--isolated --keep --max-budget-usd 1`, then 1 sonnet run as a guard (`--max-budget-usd 2`, so a sonnet pass is not cut off by the haiku cap). No `--judge`: L2 grading is not what the decision needs.
- **Control arm** (added during measurement): 3 more haiku runs with the original description restored in place. The dev-runner "before" figure is otherwise the 2026-10-04 one, and a day-old baseline cannot separate the edit from any other change since then. The rig had shown no movement, so the control was the only way to attribute a dev-runner movement to the edit.
- **Primary metric**: a `Skill` tool_use naming `proposal-write`, counted from each kept `.devrun-events.jsonl` with `jq`. **Secondary metric**: the run's L1 verdict.

**D7. Decision rule.** Recorded in proposal.md, What Changes. It is applied exactly as stated, and its outcome goes in `measurement.md`. On a revert, the README's haiku model note gains one sentence, and nothing else ships except the cases, the staging entry and the docs.

## Risks / Trade-offs

- [Haiku nondeterminism: 3 dev runs is a small sample] → The rule's threshold (≥ 2/3) is coarse on purpose. The routing-rig subset adds 3 epochs per case as a second, independent signal.
- [Widening write's description could pull review requests] → The guard case and the full sonnet sweep cover it, and either regression reverts the edit.
- [Subscription quota is shared with the user's interactive use] → Per-run budget caps, no loops, and a single sonnet sweep at 1 epoch.
- [The stored login expired before the runs] → The first isolated run refreshes it, and `keep_login` writes the refresh back. An authentication failure stops measurement, and the result is reported, not repaired.
