## MODIFIED Requirements

### Requirement: Personal data stripped on import
The skill SHALL remove personal data (the writer's own name, matriculation numbers, postal addresses, emails, supervisor names/contacts) and forbidden content (work plans, phase breakdowns, milestone tables, chapter outlines) from the imported result, and SHALL list what was removed. The imported file SHALL NOT carry the writer's name in the metadata block or in body text.

A source work plan SHALL NOT be discarded outright: the start and end months it states SHALL be carried over into the canonical timeline section before the phase detail is removed, and the removal note SHALL record that the detail went and the dates stayed. When no timeframe can be recovered, the timeline section SHALL carry a visible TODO marker rather than an invented statement.

#### Scenario: Cover page with matriculation number
- **WHEN** the source PDF carries a matriculation number and supervisor emails
- **THEN** the output contains neither and the removal note names both

#### Scenario: Cover page with the student's name
- **WHEN** the source PDF names its author on the cover page
- **THEN** the imported file carries no `author` metadata key and no name in the body, and the removal note reports the dropped name

#### Scenario: Source carries a phase table
- **WHEN** the source contains a five-phase work plan spanning October to February
- **THEN** the imported timeline section states October and February, the phase rows are gone, and the removal note reports the dropped work plan and the retained dates

#### Scenario: Source states no dates
- **WHEN** the source has no timeline and no dates anywhere
- **THEN** the imported timeline section carries a visible TODO marker and no timeframe is asserted

## ADDED Requirements

### Requirement: Imported sections placed in canonical order
The skill SHALL emit the canonical sections in the order the guidance declares, regardless of the order the source used, because that order is now checked.

#### Scenario: Source orders sections differently
- **WHEN** the source presents its methodology before its research questions
- **THEN** the imported file presents the canonical sections in the declared order, and the mechanical check reports no ordering error
