## Context

See proposal.md — Why. The review findings are wording-level; the mechanism (first section, whole-section pin, position-and-equality test) is unchanged and does the work of making each reword a paired diff.

## Goals / Non-Goals

**Goals:** every sentence in a pinned section is true for every path of its skill, has a subject, and states each rule once.

**Non-Goals:** no change to the cap number, the helper roles, or the contract's field list.

## Decisions

- **The writer counts.** "Three agents including you: you are the full review" resolves the ambiguity the review found and the tension the first assessment noted (a full-review helper capped at five findings cannot feed a review file that must carry every finding). The helpers are the adversarial check and the citation read, both of which return verdicts on tests they examined — hence "per substance test it examined".
- **Blanket no-write rule in both contracts.** "A helper writes no file" precedes the enumeration in supervise as it already did in review; the enumeration gains the notes file. The reason is the 2026-08-31 scratchpad failure: a subagent runs under its own system prompt.
- **Sibling clause only where a sibling is followed.** Supervise follows import and lit-search; reverse applies import's conversion rules; review and write follow nothing in-context and lose the clause. One rule, seven files.
- **Check names the digest re-run.** The re-run is the mandate's own mechanical proof; a first sentence that contradicts it is the worst kind of pinned sentence, since the position was chosen so that it is read first.
- **AGENTS.md documents the convention.** The report-offer block is documented beside its test; the execution-shape section now is too, so the next per-item skill learns the rule from the instructions rather than from a failing test.

## Risks / Trade-offs

- [Seven pins rewritten in one change] → each is a byte copy of its section; the review question per file is whether the section reads right, which the paired diff shows.
