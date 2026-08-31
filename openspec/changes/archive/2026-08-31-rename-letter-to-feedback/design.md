# Design

## Context

See proposal.md. Pure rename plus two guardrail sentences; no behavior change beyond naming. The word "feedback" already names the eval task (`supervise_feedback`) and the skill's own description, so the artifact joins existing vocabulary rather than adding a new term.

## Goals / Non-Goals

**Goals**: one noun for the student-facing artifact everywhere — file, specs, skill prose, harness, docs; the review file immune to the feedback label.

**Non-Goals**: no rename of `<slug>-review.md` (already distinct); no change to the tier phrases, blurb content, or German terminology (change `bilingual-terminology` governs those); no republish.

## Decisions

- **Artifact noun is "feedback"**, file `<slug>-feedback.md`. Chosen over "comment" (Moodle-only register), "reply" (email-only), keeping "letter" (channel-biased and the reason for the rename). Collision with the professor-side review ruled out by keeping `-review.md` and adding the never-called-feedback rule — a real run showed chat describing the review as "detailed feedback", which is exactly the paste-the-wrong-file setup.
- **Presence scorer renamed** `supervise_l1_letter` → `supervise_l1_feedback`; the other four scorer names carry no "letter". Safe now: supervise is in the extended task set, absent from the model-support report baseline, and no local eval logs reference the old name. Doing this later, after a matrix run, would cost log comparability.
- **Mandate reword ships with its pin** (`tests/unit/data/skill_mandates/proposal-supervise.txt`) in the same change, per the header-pattern rule.
- **Purpose line** of the supervise spec still says "feedback letter" and "continuable artifact" (stale since the send-package retirement); per the Purpose rule it is edited directly in the main spec, in this change's implementation.

## Risks / Trade-offs

- [Old workspaces hold `<slug>-letter.md`] → same posture as the package retirement: the collector inventories what exists; `poe identify` disambiguates old-snapshot reports.
- [README paragraph rewrite drifts from the skill] → the paragraph is reworded from the current SKILL.md text in the same change; the stale attach sentence is removed with it.
