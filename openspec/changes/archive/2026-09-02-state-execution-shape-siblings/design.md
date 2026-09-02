## Context

See proposal.md — Why. The mechanism is the one `2026-09-02-state-execution-shape` and `2026-09-02-harden-execution-shape-pins` established: a hand-maintained first `##` section per skill, a whole-section verbatim pin, and `tests/unit/test_execution_shape.py` discovering covered skills from the pin filenames. The header regions of the three skills are closed by the header-pattern tests, so the section goes after the mandate (and, for reverse, after its pinned successor paragraph) and before the current first section.

## Goals / Non-Goals

**Goals:**

- One execution-shape statement per exposed sibling, in that skill's own vocabulary and with that skill's own reason.
- Coverage by the existing position-and-equality test with no test edit.

**Non-Goals:**

- No helper contract paragraph: these skills produce one file from one source and have no findings to return; the contract exists where a helper's output shape can truncate a deliverable (review, supervise).
- No sections for ideate, troubleshoot, customize, publish: their mandates already sequence the run (one question per turn; stop at the first rung), or the task is a dialogue or a script.

## Decisions

- **Per-skill reason, not a shared sentence.** Reverse's reason is the knowledge cut (plan and outcome sentences must be seen together); import's is canonical reordering and the personal-data strip (whole document in view); lit-search's is preprint-and-published pairing and key uniqueness (whole-set properties). A generic "one agent" sentence would be true and unconvincing; the reason is what an agent weighs against a host's standing instruction.
- **Sibling carve-out only where a sibling is followed.** Reverse applies import's conversion rules and keeps the "not a helper" sentence; import and lit-search follow no sibling, so the sentence would be noise there. Ideate follows lit-search and has no section, which is consistent: it never had a fan-out shape.
- **Sections stay short.** One paragraph each, well inside the body caps; reverse and import are the two largest bodies after ideate and gain about sixty words.

## Risks / Trade-offs

- [A future harvest-record redesign in reverse makes "one reader" too strong] → the section and its pin change together under review, which is the mechanism's purpose.
- [Still unmeasurable] → same as the parent change: no harness path observes a fan-out; the dev-runner cost probe (`add-dev-runner-cost-probe`) adds a dev-loop signal.
