## ADDED Requirements

### Requirement: A routing case is measured in the workspace its utterance implies
The workspace staged for a routing measurement SHALL contain the files that case's utterance names, and SHALL NOT contain unrelated fixture files staged for other cases. An utterance naming no file SHALL be measured against a single proposal, so the workspace still resembles a user's rather than an empty directory. A measurement whose utterance names a file the suite cannot stage SHALL fail rather than run against a workspace missing it.

#### Scenario: Utterance names one file
- **WHEN** a case's utterance names a proposal file
- **THEN** that file is present in the workspace and the other cases' fixtures are not

#### Scenario: Ambiguity is not manufactured
- **WHEN** a case's utterance refers to the user's work without naming a file
- **THEN** the workspace holds exactly one proposal, so the reference has one referent

#### Scenario: Unstageable file named
- **WHEN** an utterance names a file no fixture provides
- **THEN** the run reports it instead of measuring against an incomplete workspace

### Requirement: Uniform epoch coverage across routing cases
Every routing case SHALL be measured at the same epoch count by default, so that a failure is reported as a rate rather than as a single event and no class of case carries less evidence than another. A run MAY override the count, and the report SHALL state the count used.

#### Scenario: Single failure is not read as settled
- **WHEN** a case fails in some epochs and passes in others
- **THEN** the report shows the rate rather than a pass or fail

#### Scenario: Epoch count recorded
- **WHEN** a report is generated
- **THEN** it states the epochs each case was measured at

### Requirement: A conditions change invalidates comparison
When a routing run is produced under changed measurement conditions — workspace staging, epoch policy, case set, or model — the report SHALL NOT present the previous score as a comparable predecessor. It SHALL instead record that conditions changed, so a movement caused by the rig is never read as a movement caused by the skills.

#### Scenario: Staging changed between runs
- **WHEN** a run follows a change to how workspaces are staged
- **THEN** the report marks the earlier score as measured under different conditions rather than as superseded
