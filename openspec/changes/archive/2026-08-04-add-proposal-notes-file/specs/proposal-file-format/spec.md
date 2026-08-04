## ADDED Requirements

### Requirement: Companion notes file
A proposal `<slug>.md` MAY have a companion working-knowledge file named `<slug>.notes.md` in the same directory. The notes file SHALL use five canonical top-level sections in this order: `## Decisions`, `## Open Points`, `## Next Focus`, `## Excluded Literature`, `## Log`. Section content is free prose or bullets; no mechanical check SHALL validate content beyond the file being markdown — the canonical sections exist so skills know where to read and write, not as a schema.

The notes file is workspace-internal: it SHALL never be built, published, or submitted, and skills that build, check, or review the proposal SHALL ignore it. A notes file SHALL NOT be treated as a proposal candidate by proposal targeting.

#### Scenario: Notes file beside its proposal
- **WHEN** a workspace holds `energy-attack-detection.md` and `energy-attack-detection.notes.md`
- **THEN** proposal targeting offers only `energy-attack-detection.md` as a candidate and the notes file is ignored by check, review, and publish

#### Scenario: Notes file alone is not a proposal
- **WHEN** a workspace holds only a `*.notes.md` file and no proposal
- **THEN** skills that need a proposal report none found rather than operating on the notes file

### Requirement: Blocking-TODO split between proposal and notes
`[TODO: …]` markers in the proposal file SHALL be reserved for submission-blocking content gaps — information the finished document cannot ship without. Working knowledge that does not block submission — decisions and their rationale, rejected alternatives, non-blocking open points, next steps — SHALL live in the companion notes file, not as proposal TODOs. When a proposal TODO is resolved, the resolving skill SHALL move it to the notes file's Log section as a done entry (original marker text plus what resolved it) instead of deleting it silently.

#### Scenario: Non-blocking knowledge kept out of the proposal
- **WHEN** a session decides between two candidate methodologies and records why the loser was rejected
- **THEN** the rationale lands in the notes Decisions section and the proposal carries no TODO about it

#### Scenario: Resolved TODO leaves a trace
- **WHEN** a skill fills the gap behind `[TODO: state the delta to prior work]`
- **THEN** the marker disappears from the proposal and the notes Log gains a done entry naming that marker and its resolution
