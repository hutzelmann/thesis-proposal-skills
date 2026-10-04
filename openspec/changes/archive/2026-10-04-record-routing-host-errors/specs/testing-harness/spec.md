## MODIFIED Requirements

### Requirement: Isolated measurement environment
A routing run SHALL execute against an isolated host configuration containing only the skills under measurement — no operator-specific skills, hooks, plugins, or agents — so that results reproduce on any machine and describe a user's install rather than the developer's. A run that cannot establish that isolation SHALL fail with a message naming what is missing, and SHALL NOT fall back to the ambient configuration.

An isolated configuration — the routing rig's, or the dev runner's in isolated mode — SHALL authenticate in one of two ways. If a long-lived token is in the environment, the configuration SHALL hold no credentials of its own. Otherwise it SHALL hold a link to the operator's stored login, never a copy.

While such a link exists, a login refresh the host performs inside the isolated configuration SHALL reach the stored login. The host refreshes by replacing the link with a file of its own. When the replacement expires later than the stored login, the harness SHALL write it to the stored location with owner-only permissions, within a second of the replacement, and SHALL check once more when the run ends. Credentials that do not expire later SHALL never be written. Credential values SHALL NOT be printed, logged, or kept anywhere other than the stored location and the isolated configuration.

The host serializes refreshes only within one configuration directory. A run that starts while the stored login has expired, or is about to, SHALL therefore first hold an exclusive refresh claim beside the stored login. A run that finds the claim held SHALL wait a bounded time for the refreshed login, then proceed with it. If the wait ends without one, the run SHALL refuse with a message naming the cause. A claim left behind by a run that ended without releasing it SHALL stop blocking after a bounded age.

A login the host rejects only once a case is running cannot be detected before the run starts. A routing case that the host ends for that reason SHALL produce no routing verdict, and its recorded error SHALL carry the host's reason and the re-login instruction the dev runner gives for the same failure.

#### Scenario: Ambient configuration excluded
- **WHEN** the operator's own configuration defines additional skills or session hooks
- **THEN** the routing run is unaffected by them

#### Scenario: Isolation cannot be established
- **WHEN** the isolated configuration cannot authenticate or cannot be created
- **THEN** the run exits with a diagnostic and produces no routing verdicts

#### Scenario: Login rejected during a case
- **WHEN** the host ends a routing case with an error result saying it failed to authenticate
- **THEN** the case produces no routing verdict, and its error carries the host's reason and tells the operator to run `claude` and enter `/login`

#### Scenario: Refresh inside an isolated run reaches the stored login
- **WHEN** the host replaces the linked credentials with a login that expires later than the stored one
- **THEN** the stored login holds the refreshed credentials with owner-only permissions, and the isolated configuration links to it again

#### Scenario: Older credentials never written back
- **WHEN** the host's replacement expires no later than the stored login
- **THEN** the stored login is left unchanged

#### Scenario: Concurrent runs with an expired login
- **WHEN** two isolated runs start while the stored login has expired
- **THEN** only one holds the refresh claim, and the other waits until the refreshed login is written back and starts with it

#### Scenario: Refresh never arrives
- **WHEN** a run waits on a held claim and the bounded wait ends with the stored login still expired
- **THEN** the run refuses with a diagnostic naming the held refresh, and the ambient configuration is not used

#### Scenario: Abandoned claim
- **WHEN** a claim is older than its bounded age
- **THEN** the next run that needs a refresh takes the claim over

#### Scenario: Long-lived token in the environment
- **WHEN** the environment carries a long-lived host token
- **THEN** the isolated configuration holds no credentials, and the stored login is neither linked nor written

### Requirement: Route determined by the first skill invocation
A case's route SHALL be the first invocation of a `proposal-*` skill observed in the run, and the run SHALL be terminated as soon as that route is recorded. Preparatory non-skill tool calls SHALL be tolerated up to a bounded number, and a case that exceeds that bound or its time limit SHALL be recorded as unrouted rather than retried. Skill invocations after the first SHALL NOT change the recorded route.

A case the host ends with an error result before any `proposal-*` invocation SHALL be recorded as an error carrying the host's reason — its subtype, its errors or result text, and the cost and turns so far — and SHALL NOT be recorded as unrouted. Unrouted is a finding about the descriptions; a host failure says nothing about them, and a negative case would pass on it.

#### Scenario: Route recorded and run stopped
- **WHEN** the agent invokes a `proposal-*` skill
- **THEN** that skill is the case's route and no further work is performed for that case

#### Scenario: Agent inspects before choosing
- **WHEN** the agent makes a small number of non-skill tool calls and then invokes a `proposal-*` skill
- **THEN** the invoked skill is still recorded as the route

#### Scenario: No skill chosen
- **WHEN** the bound on preparatory tool calls or the time limit is reached with no `proposal-*` skill invoked
- **THEN** the case is recorded as unrouted

#### Scenario: Skill chains into a sibling
- **WHEN** the selected skill invokes another `proposal-*` skill
- **THEN** the recorded route remains the first invocation

#### Scenario: Host ends the case with an error
- **WHEN** the host ends a case with an error result and no `proposal-*` skill was invoked
- **THEN** the case is recorded as an error naming the host's reason, it counts neither as unrouted nor toward any kind's total, and a negative case does not pass on it

#### Scenario: Unrouted answer is not an error
- **WHEN** the host ends a case with a result that is not an error and no `proposal-*` skill was invoked
- **THEN** the case is recorded as unrouted

### Requirement: Routing reported as a confusion matrix
A routing run SHALL persist its raw per-case results and SHALL generate a tracked report presenting expected skill against selected skill, so that a failure names the skill that wrongly claimed the utterance. A single aggregate pass rate SHALL NOT be the only reported figure. The report SHALL record the model and case count the run used. A case whose expected skill was never selected and a case claimed by the wrong skill SHALL be reported as distinct outcomes, since one says a description is too narrow and the other says it reaches too far. The report SHALL state the result it supersedes, so a later run is read as a movement rather than as an isolated figure.

A run in which any measurement ended in an error SHALL exit with a failure status, whatever the completed measurements scored. A run in which no measurement completed SHALL leave the tracked report unchanged, so that the report never carries a score no case produced and the next run is still compared against the last real one.

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

#### Scenario: Errored measurement fails the run
- **WHEN** any measurement of a run ends in an error and every completed measurement is correct
- **THEN** the run exits with a failure status

#### Scenario: Nothing measured
- **WHEN** every measurement of a run ends in an error
- **THEN** the tracked report is left unchanged, the raw per-case results are still persisted, and the run exits with a failure status
