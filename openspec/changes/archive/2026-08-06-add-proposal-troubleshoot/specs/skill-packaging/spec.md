## ADDED Requirements

### Requirement: Uniform failure-path report offer

Every shipped skill except the one that assembles reports SHALL end a run that failed in a way it cannot resolve with a single offer to assemble a bug report. The offer SHALL be worded identically across those skills, SHALL appear at most once in a session, and SHALL be an offer: no skill SHALL collect, assemble, or write report material without the user accepting.

The assembling skill SHALL NOT carry the offer at all. It is where the offer leads, so referring itself would be a loop rather than an offer, and its own unresolvable failure — a collector it cannot locate — is covered by the script-location rules that already bind every skill.

The offer SHALL fire on a script exiting non-zero, on a read-only skill detecting that the file it examined changed during its run, on a diagnostic failing repeatedly with no intervening user edit, and on a state the skill cannot proceed from. It SHALL NOT fire on ordinary findings: a proposal with errors is the diagnostic working, not a defect in it, and a skill that treats its own correct output as a bug trains users to ignore the offer.

#### Scenario: Shipped script exits non-zero

- **WHEN** a skill's script fails with a non-zero exit
- **THEN** the skill's report closes with the single offer to assemble a bug report

#### Scenario: Diagnostic reports findings

- **WHEN** a diagnostic skill completes normally and reports findings in the user's proposal
- **THEN** no report offer appears

#### Scenario: Offer declined

- **WHEN** the user does not take up the offer
- **THEN** the skill does not repeat it later in the session and collects nothing

#### Scenario: Offer wording drifts

- **WHEN** one skill's offer wording differs from the set's
- **THEN** the offline test suite fails naming that skill

#### Scenario: The assembling skill carries the offer

- **WHEN** the skill that assembles reports contains the offer wording
- **THEN** the offline test suite fails, because that skill is the offer's destination
