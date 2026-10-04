## MODIFIED Requirements

### Requirement: Isolated measurement environment
A routing run SHALL execute against an isolated host configuration containing only the skills under measurement — no operator-specific skills, hooks, plugins, or agents — so that results reproduce on any machine and describe a user's install rather than the developer's. A run that cannot establish that isolation SHALL fail with a message naming what is missing, and SHALL NOT fall back to the ambient configuration.

An isolated configuration — the routing rig's, or the dev runner's in isolated mode — SHALL authenticate in one of two ways. If a long-lived token is in the environment, the configuration SHALL hold no credentials of its own. Otherwise it SHALL hold a link to the operator's stored login, never a copy.

While such a link exists, a login refresh the host performs inside the isolated configuration SHALL reach the stored login. The host refreshes by replacing the link with a file of its own. When the replacement expires later than the stored login, the harness SHALL write it to the stored location with owner-only permissions, within a second of the replacement, and SHALL check once more when the run ends. Credentials that do not expire later SHALL never be written. Credential values SHALL NOT be printed, logged, or kept anywhere other than the stored location and the isolated configuration.

The host serializes refreshes only within one configuration directory. A run that starts while the stored login has expired, or is about to, SHALL therefore first hold an exclusive refresh claim beside the stored login. A run that finds the claim held SHALL wait a bounded time for the refreshed login, then proceed with it. If the wait ends without one, the run SHALL refuse with a message naming the cause. A claim left behind by a run that ended without releasing it SHALL stop blocking after a bounded age.

#### Scenario: Ambient configuration excluded
- **WHEN** the operator's own configuration defines additional skills or session hooks
- **THEN** the routing run is unaffected by them

#### Scenario: Isolation cannot be established
- **WHEN** the isolated configuration cannot authenticate or cannot be created
- **THEN** the run exits with a diagnostic and produces no routing verdicts

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

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL save that stream into the run's workspace so a kept workspace carries the run's tool calls and narration for later reading. Beside each run's L1 verdict it SHALL report:

- the run's cost, number of turns and duration;
- the input and output token counts, with the cache read and cache write counts;
- the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`);
- for scenarios that produce a supervise feedback, the feedback body's word count, excluding URLs and the closing note.

A dedicated verdict function SHALL pass when a run spawned no more helper agents than its scenario allows — none unless the scenario declares an allowance, which a supervise scenario does for its single verifier — and SHALL name the spawning calls when it exceeds the allowance. The runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status.

For the supervise scenarios the verifier is part of the scored L1 verdict, not only of the advisory probe: a run SHALL fail when it spawned no helper whose task carries the skill's verifier brief, and when its review's verification section does not state who verified. The headless host offers a subagent tool, so a run that checks inline has skipped the verifier rather than fallen back.

Because the runner starts the host without permission prompts, it SHALL deny the host's outward-facing tools on every run — publishing artifacts and their comments or data, messaging other sessions, push notifications, remote triggers, scheduling, and design sync — so that no test run can publish, send or schedule anything, whatever the model decides. The routing rig SHALL deny the same tools, from the same list.

The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run, naming the isolated directory. Failures SHALL be reported as follows:

- a host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far;
- when that error is a failure to authenticate, the message SHALL also tell the operator that the stored login is no longer valid and must be renewed by running `claude` and entering `/login`;
- a non-zero host exit without such an event SHALL report the host's stderr;
- a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry.

The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic — the verdicts, the event parsing, the telemetry, the command the runner builds and the summary it prints — SHALL be covered by L0 tests against recorded and synthetic event streams, and the telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so a host field rename fails a test rather than blanking the line.

#### Scenario: Telemetry printed beside the verdict
- **WHEN** a dev-runner scenario completes
- **THEN** its summary carries cost, turns, duration, token counts including the cache pair, the helper-call list, the single-context verdict, and the configuration label

#### Scenario: Event stream kept
- **WHEN** a run's workspace is kept
- **THEN** it holds the run's event stream, from which the tool calls and the agent's narration can be read after the fact

#### Scenario: Outward tools denied
- **WHEN** the runner or the routing rig builds the host command
- **THEN** the command denies every tool on the shared outward-facing list, so a model that decides to publish its output as an artifact cannot

#### Scenario: Helper spawn detected from a recorded stream
- **WHEN** a recorded event stream contains a `Task` or `Agent` or `Workflow` tool call and the scenario allows none
- **THEN** the single-context verdict fails and names the call, without a model run

#### Scenario: Allowance respected
- **WHEN** a supervise scenario that allows one helper records exactly one `Agent` call
- **THEN** the single-context verdict passes, and a second call makes it fail naming both

#### Scenario: Skipped verifier fails a supervise run
- **WHEN** a supervise scenario's stream shows no helper call carrying the verifier brief
- **THEN** the scenario's L1 verdict fails and says the verifier did not run

#### Scenario: Undeclared verification fails a supervise run
- **WHEN** the review's verification section does not say whether a fresh verifier or inline checks produced the outcome
- **THEN** the scenario's L1 verdict fails and names the missing declaration

#### Scenario: Feedback length reported
- **WHEN** a supervise scenario completes
- **THEN** the summary carries the feedback body's word count, without URLs and the closing note, as information that changes no verdict

#### Scenario: Budget cap passed through
- **WHEN** the runner is invoked with a budget cap and the host ends the run with an error result for exceeding it
- **THEN** the run ends as a runner failure whose message names the host's subtype, its errors, and the cost and turns so far — not as a skill failure and not with an empty message

#### Scenario: Expired login names the remedy
- **WHEN** the host ends a run with an error result saying it failed to authenticate because the login expired and could not be refreshed
- **THEN** the runner failure carries the host's reason and tells the operator to run `claude` and enter `/login`

#### Scenario: No result event
- **WHEN** the host exits without emitting a result event
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Recorded shape pinned
- **WHEN** the host renames a result-event field the telemetry reads
- **THEN** the L0 test against the recorded result event fails naming the field

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration kept outside the workspace that holds only settings and, unless a long-lived token is in the environment, linked credentials; the summary labels the run as isolated and names that directory; without the flag it labels the run as ambient
