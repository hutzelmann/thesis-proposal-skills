# Supervise verdict deferral

## Why

Live dev runs showed the bottom two verdict tiers flapping on a borderline submission — the boundary between "needs revision" and "no viable thesis core" is genuinely ambiguous, and forcing an automatic decision there delivers the harshest feedback inconsistently. Decision-support practice (selective prediction / learning-to-defer) and feedback pedagogy (wise feedback: high standards + assurance; feed-forward) both point the same way: raise the evidence bar for the harsh verdict, hand the boundary to the supervisor who is already in the chat, and reframe the bottom tier for the student as a stage, not a failure.

## What Changes

- **Evidence bar**: the bottom tier requires clear failure — at least three of the five substance tests failed decisively, each with a stated reason why no single revision round can repair it. Anything short of the bar is needs-revision.
- **Borderline deferral**: when the internal review says no-viable-core but the bar is not met, the skill pauses before writing the letter and asks the professor a guided multiple-choice question (needs-revision letter / idea-stage letter / show the review file first). Clear cases skip the question; the harshest letter is only ever evidence-clear or professor-chosen.
- **Idea-stage letter framing**: the student-facing rendering of the bottom tier becomes "idea stage — not yet a proposal" (de: "Ideenphase"), coupling the standard a proposal must meet with an assurance anchored in a named true strength and a feed-forward to ideation. The professor-side review file keeps the blunt three-tier vocabulary unchanged.
- **Starter literature offer**: for bottom/borderline outcomes, the skill offers (never auto-runs) to attach two or three verified starting papers via the lit-search sibling, professor-approved, as a "here is where this conversation already is" pointer.
- Harness follows: the tier verdict accepts the idea-stage phrasings, and single-turn eval/dev requests pre-answer the deferral question so headless runs cannot stall.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-supervise`: the verdict requirement gains the evidence bar and the idea-stage student-facing rendering; a new requirement covers borderline deferral to the supervisor; the package requirement gains the optional starter-literature offer.
- `testing-harness`: the supervise package coverage requirement notes that non-interactive runs pre-answer the deferral and that the tier verdict accepts the idea-stage rendering.

## Impact

- `skills/proposal-supervise/SKILL.md`: verdict section, new deferral step, letter framing, starter-literature offer.
- `harness/l1_checks.py`: tier pattern extended (idea-stage en/de); L0 tests in `tests/unit/test_supervise_verdicts.py`.
- `harness/skill_evals.py`, `harness/claude_runner.py`: requests pre-answer the deferral.
- `tests/unit/data/skill_mandates/proposal-supervise.txt`: only if the mandate wording changes (not planned).
