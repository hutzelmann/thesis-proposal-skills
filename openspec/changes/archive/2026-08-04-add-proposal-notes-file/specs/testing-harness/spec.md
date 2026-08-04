## ADDED Requirements

### Requirement: Notes files excluded from draft selection
The shared draft-selection function SHALL treat files ending in `.notes.md` as non-proposal markdown, alongside the existing non-proposal names, so no verdict ever grades a notes file as the produced proposal. The exclusion SHALL be covered by L0 tests without a model call. Fixtures MAY ship notes files; a notes file carries no `expected.json` oracle obligations of its own.

#### Scenario: Notes file never selected as the draft
- **WHEN** a scenario workspace contains `energy-attack.notes.md` and `energy-attack.md`
- **THEN** draft selection returns `energy-attack.md` even when the notes file sorts first

#### Scenario: Exclusion tested without a model
- **WHEN** the L0 suite runs
- **THEN** a unit test exercises the `.notes.md` exclusion through the pure selection function
