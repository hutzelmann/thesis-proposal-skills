## MODIFIED Requirements

### Requirement: Routing reported as a confusion matrix
A routing run SHALL persist its raw per-case results and SHALL generate a tracked report presenting expected skill against selected skill, so that a failure names the skill that wrongly claimed the utterance. A single aggregate pass rate SHALL NOT be the only reported figure. The report SHALL record the model and case count the run used. A case whose expected skill was never selected and a case claimed by the wrong skill SHALL be reported as distinct outcomes, since one says a description is too narrow and the other says it reaches too far. The report SHALL state the result it supersedes, so a later run is read as a movement rather than as an isolated figure.

The model SHALL be recorded as what the host served, not only as what the run requested, because an alias resolves to whatever the host currently maps it to. Each raw per-case result SHALL carry the full model ID the host reported serving and the host CLI version, both read from that case's own event stream. A stream that reports neither leaves them empty. The report SHALL name the requested alias, beside each served model ID with the number of measurements it served, and each CLI version with its count. Measurements whose stream reported no served model SHALL be counted as not reported. A report rebuilt from a raw log written before the served model was recorded, whose results carry no served-model field, SHALL say that the served model was not recorded.

A run in which any measurement ended in an error SHALL exit with a failure status, whatever the completed measurements scored. A run in which no measurement completed SHALL leave the tracked report unchanged, so that the report never carries a score no case produced and the next run is still compared against the last real one.

#### Scenario: Mis-route is attributable
- **WHEN** cases expected to select one skill are routed to another
- **THEN** the report shows that pairing and the utterances involved

#### Scenario: Run provenance recorded
- **WHEN** a report is generated
- **THEN** it names the requested model, each served model ID with its measurement count, the CLI version, and the number of cases measured

#### Scenario: Served model recorded per case
- **WHEN** a case is measured with the alias `haiku`
- **THEN** its raw result carries the full model ID from the stream's initialization event and the CLI version, beside the run's requested alias

#### Scenario: Alias re-pointed within a sweep
- **WHEN** the measurements of one sweep report two different served model IDs
- **THEN** the report lists both, each with its measurement count, and the raw results show which case each one served

#### Scenario: Stream without a served model
- **WHEN** a case's stream ends before the host reported its initialization event
- **THEN** the case's served model and CLI version are recorded as empty, and the report counts the measurement as not reported

#### Scenario: Report rebuilt from an older raw log
- **WHEN** a report is rebuilt from a raw log written before the served model was recorded, whose results carry no served-model field
- **THEN** the report says that the served model was not recorded, and does not present the alias as the served model

#### Scenario: Silence distinguished from theft
- **WHEN** a case's expected skill is never selected
- **THEN** the report marks it as not selected rather than as mis-routed

#### Scenario: Comparison against the previous result
- **WHEN** a report replaces an earlier one
- **THEN** it states the earlier score it is being compared against

#### Scenario: Errored measurement fails the run
- **WHEN** any measurement of a run ends in an error and every completed measurement is correct
- **THEN** the run exits with a failure status

#### Scenario: Nothing measured
- **WHEN** every measurement of a run ends in an error
- **THEN** the tracked report is left unchanged, the raw per-case results are still persisted, and the run exits with a failure status

### Requirement: A conditions change invalidates comparison
When a routing run is produced under changed measurement conditions, the report SHALL NOT present the previous score as a comparable predecessor. The conditions are workspace staging, epoch policy, case set, model, and the isolation of the host configuration. The report SHALL instead record that conditions changed, so that a movement caused by the rig is never read as a movement caused by the skills.

The report and the run's raw results SHALL record the isolation conditions they were measured under. When the outgoing report records no isolation conditions, or records different ones, the run SHALL treat the earlier score as measured under different conditions, without the operator having to declare it.

The model condition SHALL be detected in the same way, from the served model IDs rather than from the requested alias. When the outgoing report records no served model, or a different set of served model IDs than the new run, the run SHALL treat the earlier score as measured under different conditions, without the operator having to declare it. The host CLI version SHALL be recorded, but a different version SHALL NOT on its own make the earlier score incomparable. The operator's own declaration of a conditions change SHALL still apply for every other condition, including a CLI change the operator judges relevant.

#### Scenario: Staging changed between runs
- **WHEN** a run follows a change to how workspaces are staged
- **THEN** the report marks the earlier score as measured under different conditions rather than as superseded

#### Scenario: Earlier report measured with account surfaces present
- **WHEN** a routing run is measured with the claude.ai account surfaces closed, and the outgoing report records no isolation conditions
- **THEN** the new report marks the earlier score as measured under different conditions rather than as superseded, although the operator declared no conditions change

#### Scenario: Alias resolves to a different model
- **WHEN** the outgoing report records `claude-haiku-4-5-20251001` as served, and the new run's alias `haiku` is served as `claude-haiku-5-5`
- **THEN** the new report marks the earlier score as measured under different conditions, although the operator declared no conditions change

#### Scenario: Earlier report records no served model
- **WHEN** the outgoing report carries no served model
- **THEN** the new report marks the earlier score as measured under different conditions rather than as superseded

#### Scenario: Same isolation conditions
- **WHEN** the outgoing report records the same isolation conditions and the same served model IDs as the new run, and the operator declares no conditions change
- **THEN** the new report states the earlier score as the one it supersedes

#### Scenario: Same served model on a newer CLI
- **WHEN** the outgoing report records the same isolation conditions and served model IDs as the new run but an older CLI version, and the operator declares no conditions change
- **THEN** the new report states the earlier score as the one it supersedes and names its own CLI version

## ADDED Requirements

### Requirement: Measurements name the served model
Every measurement the dev runner and the routing rig take through the subscription host by an alias SHALL be recorded with the full model ID the host reported serving and with the host CLI version. The alias resolves to whatever the host currently maps it to, which need not be the registry's pin for that family. The dev-run summary (requirement: Dev-runner cost and helper-agent telemetry) and each routing case (requirement: Routing reported as a confusion matrix) record both. A re-grade SHALL record them too. Each re-grade line SHALL carry the served model ID and the CLI version of the kept run, read from the event stream saved in its workspace, beside the judge's own served model and CLI version, including the line of a re-grade that crashed. A re-grade line SHALL NOT carry a requested alias, because the kept workspace does not record one. The advisory audit preflight records no measurement and is not covered.

The citation rules below apply to citations written from this requirement on; dated citations written before it are not retrofitted, and the change that introduced it records errata for the ones it corrected.

A change record that cites a measurement SHALL name the served full model ID and the CLI version taken from the run's own record, never only the requested alias. Where the run's record carries no served model, the citation SHALL say that it was not recorded. A served model taken from other runs SHALL be labelled as inferred and SHALL state its basis.

Documentation that the model-identifier guard scans SHALL name the served model and the CLI version beside a dated measurement:

- by its full ID, where that ID resolves to a current roster entry or role;
- otherwise in prose by its version, pointing to the change record that carries the full ID.

The harness documentation SHALL state that a subscription run by alias is not a run of the matrix row of the same family.

#### Scenario: Re-grade names the kept run's model
- **WHEN** a kept workspace is re-graded
- **THEN** the re-grade line carries the served model ID and the CLI version from the workspace's saved stream, beside the judge's, and no requested alias

#### Scenario: Kept stream without an initialization event
- **WHEN** a kept workspace's saved stream carries no initialization event
- **THEN** the re-grade line records the kept run's CLI version as empty rather than omitting it or taking the judge's

#### Scenario: Re-grade that crashed
- **WHEN** a re-grade crashes and records a runner failure for each kept workspace
- **THEN** each of those lines still carries the kept run's served model ID and CLI version, empty where the saved stream cannot be read

#### Scenario: Citation in a change record
- **WHEN** a change record cites a dev-run, routing or re-grade result
- **THEN** it names the served full model ID and the CLI version from the run's record, and the alias only beside them

#### Scenario: Served model not recorded
- **WHEN** the record of a cited run carries no served model, as a routing log written before this requirement does
- **THEN** the citation says the served model was not recorded, and a model taken from same-day runs is labelled as inferred, with its basis

#### Scenario: Served model outside the roster in documentation
- **WHEN** the harness documentation cites a dated measurement whose served model no roster entry or role pins
- **THEN** it names that model in prose by its version, with the CLI version, and points to the change record holding the full ID, and the model-identifier guard passes

#### Scenario: Alias documented as the host's current model
- **WHEN** the harness documentation shows a subscription run with `--model haiku`
- **THEN** it says that the alias runs the host's current haiku and not the matrix row's pinned version
