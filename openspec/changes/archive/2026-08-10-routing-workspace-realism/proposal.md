## Why

Five of sixty routing measurements fail, and the event streams say at least three of them are the rig's fault rather than the descriptions'.

Every case is measured in a workspace holding all four fixture files — two English proposals, a German one, and a student's submission email. No user's workspace looks like that. For `litsearch-collision` ("Is my idea already published somewhere?") the agent glob-reads the directory, finds three proposal drafts, and asks which one "my idea" refers to. It never selects a skill, and the case is scored as a description failure. The clarifying question is the correct behaviour; the workspace is the defect.

The second problem is statistical. Only the contested cases run three epochs, so a single failure elsewhere cannot be told apart from a coin flip: `litsearch-oblique` failed in the sweep and passed on re-measurement the same evening. Two of the five outstanding failures may be noise that a description edit would then be credited with fixing.

## What Changes

- Stage per case: a measurement workspace SHALL contain the files that case's utterance actually names, and a single proposal when it names none — never the union of every fixture the dataset mentions.
- Run every case at the same epoch count by default, so a failure is a rate rather than an event, and no case class is quietly measured with less evidence than another.
- Re-baseline under the corrected conditions, stating plainly that the new figure is not comparable to the previous one and why.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `testing-harness`: the routing measurement's workspace becomes a property of the case rather than of the suite, and epoch coverage becomes uniform.

## Impact

- Modified: `harness/routing.py` (staging, epoch default), `tests/unit/test_routing.py`, `docs/skill-routing.md` (re-measured), `harness/README.md` (the recorded reading about `litsearch-collision` is superseded by its fix).
- No skill file changes. Whether the descriptions need further work is exactly what this change makes measurable.
