## ADDED Requirements

### Requirement: Methodology-opening coverage
The harness SHALL fail a drafted proposal whose methodology section has no prose before its first subsection, or whose opening gives the methodology a suitability verdict, in English or German. Every write task's L1 verdict and the dev runner's write scenarios SHALL apply this check, and it SHALL be tested offline against fixed inputs.

#### Scenario: Suitability verdict fails the draft
- **WHEN** a drafted proposal's methodology section opens with "A controlled experiment fits these questions because …" or "Eine Fallstudie eignet sich, weil …"
- **THEN** the write task's L1 verdict fails and its explanation names the methodology opening

#### Scenario: Missing opening fails the draft
- **WHEN** a drafted proposal's methodology heading is followed directly by its first subsection
- **THEN** the write task's L1 verdict fails and its explanation names the missing opening

#### Scenario: Confident opening passes
- **WHEN** the opening states what the research questions demand and what the methodology does that meets it, without a suitability verdict
- **THEN** the methodology-opening check passes, and the verdict depends on the remaining L1 conditions alone

#### Scenario: Fixtures model the target
- **WHEN** the offline suite runs the methodology-opening check over every fixture proposal whose methodology section has an opening
- **THEN** every such opening passes
