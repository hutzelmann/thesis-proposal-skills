# Harden the execution-shape pins

## Why

`2026-09-02-state-execution-shape` pinned each `## Execution shape` section by its heading and opening sentence only. A rewrite can therefore drop the helper-contract paragraph while keeping the pinned line, and nothing asserts the section stays first in the body — the position the design argued for, because a fan-out is planned when the agent reaches the assessment list, and a section at the end is read after the workflow exists. Both gaps are the kind a well-meaning tidy-up opens.

## What Changes

- The four pins become whole-section verbatim pins: each `tests/unit/data/pinned_sentences/<skill>--execution-shape.txt` holds the section from its heading to the end of its last paragraph. No new mechanism — the pin test already does strip-and-substring on multi-line files — and it is the mandate mechanism applied to a section, which is what the section is: an agent-facing operational rule.
- A small L0 test discovers the skills carrying an execution-shape pin from the pin filenames and asserts two things per skill: the first `##` heading of the body is `## Execution shape`, and the pinned text equals the whole section (heading through the paragraph before the next `##`). The second assertion stops a whole-section pin from silently degrading back to a partial one; the first carries the position.
- The four capability requirements say so: the section SHALL be the first section of the body and SHALL be pinned verbatim, replacing "its opening sentence … SHALL be pinned".

Discovering the skill set from the pin files means the tracked sibling sweep (reverse, import, lit-search) extends coverage by adding a pin, with no test edit.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-review`: "Single-context execution" — section pinned verbatim as a whole and required to be the first section.
- `skill-supervise`: "Single-context execution" — same.
- `skill-check`: "Single-agent execution" — same.
- `skill-write`: "One writer per file" — same.

## Impact

- `tests/unit/data/pinned_sentences/proposal-{review,supervise,check,write}--execution-shape.txt` (content replaced)
- `tests/unit/test_execution_shape.py` (new)
- Spec deltas for the four capabilities. No SKILL.md text changes, no `shared/`, no scripts.
