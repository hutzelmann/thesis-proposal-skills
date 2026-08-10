## MODIFIED Requirements

### Requirement: Routing reported as a confusion matrix
A routing run SHALL persist its raw per-case results and SHALL generate a tracked report presenting expected skill against selected skill, so that a failure names the skill that wrongly claimed the utterance. A single aggregate pass rate SHALL NOT be the only reported figure. The report SHALL record the model and case count the run used. A case whose expected skill was never selected and a case claimed by the wrong skill SHALL be reported as distinct outcomes, since one says a description is too narrow and the other says it reaches too far. The report SHALL state the result it supersedes, so a later run is read as a movement rather than as an isolated figure.

#### Scenario: Mis-route is attributable
- **WHEN** cases expected to select one skill are routed to another
- **THEN** the report shows that pairing and the utterances involved

#### Scenario: Run provenance recorded
- **WHEN** a report is generated
- **THEN** it names the model used and the number of cases measured

#### Scenario: Silence distinguished from theft
- **WHEN** a case's expected skill is never selected
- **THEN** the report marks it as not selected rather than as mis-routed

#### Scenario: Comparison against the previous result
- **WHEN** a report replaces an earlier one
- **THEN** it states the earlier score it is being compared against
