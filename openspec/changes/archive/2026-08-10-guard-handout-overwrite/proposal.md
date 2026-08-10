## Why

`publish.py --handout` writes `<slug>-handout.md` unconditionally. Every other output publish produces — the PDF and the intermediate build source — is a gitignored artifact the tool owns and regenerates freely. The handout is the exception, and deliberately so: it is not gitignored because it is a deliverable meant to be kept and sent.

That combination is a silent data-loss path. A student who fixes a sentence in the handout before emailing it, then re-runs publish, loses the fix with no message. The tool cannot tell the difference between a file it wrote and a file the student has since edited, so it must not assume.

## What Changes

- `--handout` SHALL refuse to overwrite an existing handout whose content differs from what it would write, exiting non-zero and naming both the file and the flag that proceeds anyway.
- A new `--force` flag performs the overwrite explicitly.
- Writing identical content SHALL stay silent and succeed, so re-running an unchanged build keeps costing nothing.
- The publish skill relays the refusal rather than re-deciding: a student who edited the handout by hand either renames it or accepts losing the edits, and that is the student's call, not the agent's.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-publish`: the hand-in export gains an overwrite contract.

## Impact

- `skills/proposal-publish/scripts/publish.py` — the `--handout` branch and one new flag.
- `skills/proposal-publish/SKILL.md` — one line under hand-in guidance.
- The generated copy of `publish.py` is not vendored anywhere, so no sync follows.
- New L0 tests; no fixture or oracle changes.
