## MODIFIED Requirements

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

#### Scenario: No result event
- **WHEN** the host exits without emitting a result event
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Recorded shape pinned
- **WHEN** the host renames a result-event field the telemetry reads
- **THEN** the L0 test against the recorded result event fails naming the field

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration holding only settings and linked credentials, kept outside the workspace, and the summary labels the run as isolated and names that directory; without the flag it labels the run as ambient
