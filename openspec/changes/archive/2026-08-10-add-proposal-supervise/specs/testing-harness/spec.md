# testing-harness Delta

## ADDED Requirements

### Requirement: Supervise package coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the package contract with dedicated verdict functions: a feedback letter exists, it carries at most five curated points, it opens with one of the three verdict tiers, the send-package contains no personal data from the fixture, and every skill pointer in the letter names a skill that exists in the set. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed.

#### Scenario: Package contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report letter presence, point count, verdict tier, personal-data absence, and skill-pointer validity as separate verdicts

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the send-package
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls
