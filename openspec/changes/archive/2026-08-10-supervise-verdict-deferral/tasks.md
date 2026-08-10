# Tasks: supervise-verdict-deferral

## 1. Skill

- [x] 1.1 Rewrite the SKILL.md verdict item: three student-facing tiers with idea stage (en/de), evidence bar (≥3 decisive substance-test failures, per-test irreparability), wise-feedback shape for the idea-stage letter (standard + anchored assurance + feed-forward to ideation), review file keeps blunt vocabulary.
- [x] 1.2 Add the borderline-deferral step: split-evidence summary, three guided choices, needs-revision default on decline/non-interactive.
- [x] 1.3 Add the starter-literature offer for idea-stage/borderline outcomes (lit-search sibling, offer-and-approve, verified entries, postscript placement, silent skip without sibling).

## 2. Harness

- [x] 2.1 Extend `SUPERVISE_TIER_PATTERN` with the idea-stage phrasings (en/de), keeping the existing phrases; L0 tests for both languages.
- [x] 2.2 Append the deferral pre-answer to the Inspect task request and the dev-runner request.

## 3. Verification

- [x] 3.1 `uv run poe test` and `uv run poe specs` green; one `poe dev supervise_feedback --model sonnet` run passes. Outcome: sonnet letter came out in the full wise-feedback shape (idea stage, standard, anchored assurance, feed-forward), all five verdicts pass; tier explanation improved to report all matched phrases.
