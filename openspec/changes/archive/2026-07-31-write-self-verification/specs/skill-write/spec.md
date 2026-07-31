# skill-write Delta

## ADDED Requirements

### Requirement: Self-verification before reporting
The skill SHALL ship the mechanical check as a synchronized copy and SHALL run it over the produced or edited proposal before reporting a writing pass complete, fixing every error it reports and re-running until only tolerated findings remain. Two findings are explicitly not "fixed": a reference-count shortfall is reported to the user because inventing a publication is forbidden, and open `[TODO: …]` markers stay because they are the honest record of what the material did not supply.

#### Scenario: Check finds a structural error in fresh output
- **WHEN** the check reports an error on the file the skill just wrote (a drifted section title, an unterminated metadata block, a cited key missing from `references`, a missing `(RQn)` reference)
- **THEN** the skill corrects the file and re-runs the check before reporting, and the report states what the check still finds

#### Scenario: Check reports a reference shortfall
- **WHEN** the only remaining error is that the proposal cites fewer references than required
- **THEN** the skill reports the shortfall and suggests the literature-search skill instead of adding sources the material did not carry

#### Scenario: Open TODO markers remain
- **WHEN** the check warns about open `[TODO: …]` markers recording gaps the source material did not fill
- **THEN** the skill leaves the markers in place and lists them in its report

### Requirement: Methodology decision under deferred choice
When the source material leaves the methodology choice open, the skill SHALL decide: it picks the methodology from the closed set that the research questions best support, writes the canonical methodology heading for that choice, and records the uncertainty as `[TODO: confirm methodology choice]` in the section body. A section heading SHALL NOT carry a TODO marker.

#### Scenario: Seed defers the methodology choice
- **WHEN** the idea notes contain an open TODO deferring between two methodologies
- **THEN** the drafted proposal carries a canonical methodology heading for the better-supported option and a `[TODO: confirm methodology choice]` marker in the section body

#### Scenario: User states the methodology in the request
- **WHEN** the request names the methodology to use
- **THEN** the skill uses it without adding a confirmation TODO
