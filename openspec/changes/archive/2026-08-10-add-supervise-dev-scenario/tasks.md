# Tasks: add-supervise-dev-scenario

## 1. Verdict aggregate

- [x] 1.1 Add `verdict_supervise_package(package, forbidden, installed)` to `harness/l1_checks.py`, combining letter/points/tier/personal-data/pointers into one (passed, explanation); L0 tests in `tests/unit/test_supervise_verdicts.py`.

## 2. Dev runner

- [x] 2.1 Add the `supervise_feedback` scenario to `harness/claude_runner.py`: stage `s01-raw-email` (including the `.txt` submission), install `proposal-import` as sibling, request mirroring the Inspect task, verdict via the aggregate over the produced `*-package/`.

## 3. Verification

- [x] 3.1 `uv run poe test` green; run `uv run poe dev supervise_feedback --model sonnet` on the Max subscription and record the outcome. Outcome: two verdict-function bugs found and fixed (tier paraphrase, repo-name pointer false positive), two skill-instruction tightenings (tier stated verbatim; no salutation/sign-off), then sonnet PASS twice in a row; haiku produced no package (consistent with its existing not-recommended verdict).
