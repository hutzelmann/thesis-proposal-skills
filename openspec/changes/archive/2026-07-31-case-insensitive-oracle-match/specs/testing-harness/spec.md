## ADDED Requirements

### Requirement: Prose-relaying verdicts match without regard to case

A verdict that judges whether a skill relayed given content into its chat answer SHALL match case-insensitively. Sentence capitalisation is a property of prose, not of the finding being relayed, so a correct relay SHALL NOT fail on it.

#### Scenario: Relay begins a sentence with the finding

- **WHEN** the skill reports a finding as "Duplicate reference id `Lee24Index`" and the oracle records it as "duplicate reference id"
- **THEN** the verdict counts it as relayed

#### Scenario: Finding genuinely absent

- **WHEN** the skill's answer never mentions a finding the oracle records
- **THEN** the verdict does not count it, and enough missing findings still fail the scenario
