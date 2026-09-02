## MODIFIED Requirements

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL report beside each run's L1 verdict the run's cost, number of turns, duration, input and output token counts with the cache read and cache write counts, and the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`). A dedicated verdict function SHALL pass when a run spawned no helper agent and SHALL name the spawning calls when it did; the runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status. The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run, naming the isolated directory. A host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far; a non-zero host exit without such an event SHALL report the host's stderr; a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry. The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic — the verdict, the event parsing, the telemetry, the command the runner builds and the summary it prints — SHALL be covered by L0 tests against recorded and synthetic event streams, and the telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so a host field rename fails a test rather than blanking the line.

#### Scenario: Telemetry printed beside the verdict
- **WHEN** a dev-runner scenario completes
- **THEN** its summary carries cost, turns, duration, token counts including the cache pair, the helper-call list, the single-context verdict, and the configuration label

#### Scenario: Helper spawn detected from a recorded stream
- **WHEN** a recorded event stream contains a `Task` or `Agent` or `Workflow` tool call
- **THEN** the single-context verdict fails and names the call, without a model run

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
