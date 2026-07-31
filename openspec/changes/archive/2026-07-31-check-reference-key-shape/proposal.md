## Why

The guidance fixes a reference-key convention — `AuthorYearFirstWordOfTitle`, under 20 characters — and nothing verifies it. An import eval produced `RiveraYearSurvey` and `TanakaYearLoRA`, keys carrying the literal word "Year" instead of a year, and every layer accepted them.

The convention is worth keeping mechanical rather than repeated in prose. Import currently restates the key shape in its own instructions precisely because no check enforces it; once the check does, that instruction can go, continuing the removal of guidance that duplicates a mechanical rule.

Tested against the whole fixture corpus, the shape flags 2 of 78 keys: `on`, the deliberate boolean-literal fixture already reported as an error, and `Bacchelli13Expectations` at 23 characters — a real violation of the documented limit.

## What Changes

- The check warns when a reference id does not match the documented key shape, or reaches the length limit.
- Import stops restating the key shape, since the check now reports it.
- The one corpus violation is fixed rather than pinned: `Bacchelli13Expectations` becomes `Bacchelli13Expect`, keeping the fixture's purpose — a real, correctly-cited paper serving as the VERIFIED control.

Warning class, never an error: an unusual author name can legitimately produce an unusual key, and a proposal carrying one still builds and still resolves.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-check`: the warning-class checks gain reference-key shape and length.
- `skill-import`: the instructions drop the key-shape rule, which the check now makes.

## Impact

- `skills/proposal-check/scripts/check.py`: one rule over the ids already extracted.
- `skills/proposal-import/SKILL.md`: one bullet removed.
- `tests/fixtures/f18-broken-refs/`: key renamed in the body, the reference entry, and the oracle's semantic note.
- `tests/unit/test_check.py`: the malformed shapes the eval actually produced, and the legitimate ones that must stay silent.
