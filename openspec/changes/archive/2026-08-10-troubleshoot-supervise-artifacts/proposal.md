# Troubleshoot covers supervisor sessions

## Why

`proposal-supervise` produces artifacts no other skill does — `<slug>-review.md` beside the proposal and a `<slug>-package/` send-package — and a supervise defect (a letter missing its tier, personal data surviving into the package) is invisible to the current bug-report bundle: the collector describes only the proposal and the notes log. An audit of the rest of the ladder found it already generic (skill discovery by `proposal-*` glob, unevaluated-model rung, offer block present in supervise), so the gap is the collector plus one student-assuming sentence in the rung-2 wording.

## What Changes

- The collector inventories companion artifacts beside the named proposal — the review file and the send-package — at hash level (names slug-redacted, byte counts, hashes) at every disclosure level. Their content never enters the report at any level: the letter derives from a student's unpublished submission, and hashes are what a maintainer needs to see whether the artifacts exist and changed.
- Rung 2's wording generalizes: the guidelines override wins whether the user is the student who received it or the supervisor who wrote it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-troubleshoot`: new requirement — companion artifacts inventoried at hash level, content excluded at every disclosure level.

## Impact

- `skills/proposal-troubleshoot/scripts/collect.py`: `sibling_artifacts()` + report section wiring.
- `skills/proposal-troubleshoot/SKILL.md`: one rung-2 sentence.
- `tests/unit/test_troubleshoot_collect.py`: inventory coverage.
