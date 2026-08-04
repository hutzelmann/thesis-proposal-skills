## ADDED Requirements

### Requirement: Notes file consumed and maintained while writing
When a companion `<slug>.notes.md` exists for the target proposal, the write skill SHALL read it before drafting and honor its content: recorded decisions steer the draft (they are not re-litigated), and the Next Focus section informs which gaps to work on first. Decisions the writing session itself produces SHALL be recorded in the notes Decisions section. When the session resolves a proposal `[TODO: …]` marker, the skill SHALL move it to the notes Log as a done entry rather than deleting it. When no notes file exists, the skill SHALL proceed as before and MAY create one only when it has decisions to record — never an empty skeleton.

#### Scenario: Prior decision honored
- **WHEN** the notes Decisions section records that a user study was rejected in favor of a prototype implementation
- **THEN** the draft builds on the prototype methodology and the skill does not re-open the methodology question

#### Scenario: Resolved marker logged
- **WHEN** the writing session fills the gap behind a proposal TODO marker
- **THEN** the marker is removed from the proposal and appears in the notes Log as done, with a note of what resolved it

#### Scenario: No notes file present
- **WHEN** the target proposal has no companion notes file and the session makes no recordable decision
- **THEN** the skill writes the proposal as usual and creates no notes file
