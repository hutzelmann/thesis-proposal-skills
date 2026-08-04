## MODIFIED Requirements

### Requirement: Seeds the proposal file
The skill SHALL end by creating the proposal file (per proposal-file-format): working title, problem sketch, candidate research-question directions as notes, open questions as `[TODO: …]` markers, and a metadata block containing any starter references found.

At this closing step — where the degree level and the language are already being settled — the skill SHALL also ask once when the thesis starts and when it is submitted, and record the answer as a note in the seeded body so the writing skill need not ask again. The seed file is a sketch, not a canonical-section proposal, so the answer SHALL be recorded as a note and SHALL NOT be written as a timeline section. The Socratic part of the session SHALL remain about the idea and SHALL NOT be interrupted by this question.

#### Scenario: Session ends after ideation
- **WHEN** the ideation session concludes
- **THEN** a slug-named proposal file exists containing the captured idea state, consumable by the write skill

#### Scenario: Timeframe captured while seeding
- **WHEN** the writer names a start and a submission month at the seeding step
- **THEN** the seed file records them as a note, carries no timeline section, and the writing skill does not ask again

#### Scenario: Timeframe not yet known
- **WHEN** the writer does not know the dates at the seeding step
- **THEN** the seed file records nothing about timing and the writing skill handles the gap
