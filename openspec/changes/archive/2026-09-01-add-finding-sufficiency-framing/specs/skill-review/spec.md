# skill-review delta

## MODIFIED Requirements

### Requirement: Persisted, actionable output
The review SHALL be written to `<slug>-review.md` next to the proposal (overwritten per run), in the proposal's declared language, as an enumerated list of issues each with an actionable suggestion. Where a finding concerns an exceeded limit or forbidden content, the suggestion SHALL state what suffices and where the surplus content goes — never only that the content does not belong.

#### Scenario: German proposal reviewed
- **WHEN** the proposal declares `lang: de`
- **THEN** the review file is written in German

#### Scenario: Work plan in the timeline section
- **WHEN** the proposal's timeline section carries a phase breakdown or Gantt-style work plan
- **THEN** the finding's suggestion states that one sentence naming start and submission month suffices and that the phase detail belongs in the writer's own working notes, rather than only declaring the plan forbidden
