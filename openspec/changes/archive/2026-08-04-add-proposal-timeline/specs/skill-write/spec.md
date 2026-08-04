## MODIFIED Requirements

### Requirement: Guidance-driven writing
The skill SHALL follow the default guidance combined with any workspace `guidelines.md` overrides (structure, forbidden content, writing rules, language conventions) when creating or refining a proposal.

#### Scenario: Workspace override active
- **WHEN** the workspace selects the detailed timeline mode
- **THEN** written output may include a phase table in the timeline section and other defaults still apply

## ADDED Requirements

### Requirement: Timeline written, never invented
Created proposals SHALL carry the canonical timeline section as their final section. When the start and submission months are known, the skill SHALL state them in one short sentence; when the writer has said the work begins as soon as possible, the skill SHALL state that instead.

When the timeframe is not known, the skill SHALL write a visible TODO marker and SHALL NOT fall back to an as-soon-as-possible statement, because that is a claim only the writer can make and a writer with a registered submission date would be misrepresented by it. In an interactive session the skill SHALL ask for the timeframe once; a session that runs without the writer present SHALL produce the TODO marker rather than block.

#### Scenario: Dates known
- **WHEN** the writer has said the thesis starts in October and is submitted in March
- **THEN** the created proposal ends with a timeline section naming both months

#### Scenario: Writer states no fixed dates
- **WHEN** the writer says there is no registered date and the work starts once the supervisor approves
- **THEN** the timeline section states that the thesis begins as soon as possible

#### Scenario: Timeframe never supplied
- **WHEN** a draft is produced without the writer supplying a timeframe
- **THEN** the timeline section carries a visible TODO marker and asserts nothing about timing
