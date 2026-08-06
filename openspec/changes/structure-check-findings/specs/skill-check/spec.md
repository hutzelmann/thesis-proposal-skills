## ADDED Requirements

### Requirement: Findings carry stable identifiers

Every mechanical finding the deterministic script reports SHALL carry a stable identifier
naming the rule that produced it, in addition to its severity and its human-readable
message. Identifiers SHALL be drawn from a closed set defined by the script and SHALL remain
stable when a message is reworded, so that a consumer distinguishes "this check fired" from
"this check phrased its finding this way".

The human-readable message SHALL remain the primary output for a student, and its wording
SHALL stay free to change without notice. Consumers that need to identify a finding SHALL
use the identifier and SHALL NOT match against message text.

#### Scenario: A reworded message keeps its identifier

- **WHEN** a finding's human-readable message is rephrased without changing what it detects
- **THEN** the finding SHALL continue to report the same identifier
- **AND** a consumer keyed on that identifier SHALL be unaffected

#### Scenario: Distinct rules are distinguishable

- **WHEN** two different checks report findings whose messages share a common phrase
- **THEN** each finding SHALL carry the identifier of the rule that produced it
- **AND** a consumer SHALL be able to tell the two findings apart

### Requirement: Machine-readable output mode

The deterministic script SHALL offer an output mode that emits its findings as structured
data rather than as the human report. The structured output SHALL carry, for each finding,
its severity, its rule identifier, and its message; and SHALL carry the content digest of
the checked file and the exit code the run produced.

The structured mode SHALL be opt-in. Invoked without it, the script SHALL emit the human
report exactly as before, and the exit code SHALL be identical in both modes: non-zero only
when at least one error-level finding was reported.

#### Scenario: Structured output requested

- **WHEN** the script is invoked in its machine-readable output mode over a proposal
- **THEN** it SHALL emit the findings as structured data with severity, identifier, and
  message for each
- **AND** it SHALL include the checked file's content digest
- **AND** it SHALL NOT emit the human two-bucket report

#### Scenario: Default invocation is unchanged

- **WHEN** the script is invoked without requesting structured output
- **THEN** it SHALL emit the human two-bucket report as it did before
- **AND** the exit code SHALL match the one the structured mode reports for the same file

#### Scenario: Advisory status is preserved

- **WHEN** a run reports warning-level findings but no error-level findings
- **THEN** the exit code SHALL indicate success in both output modes,
  because the check gates nothing on warnings
