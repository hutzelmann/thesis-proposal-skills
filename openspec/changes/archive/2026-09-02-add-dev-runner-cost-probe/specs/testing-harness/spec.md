## ADDED Requirements

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL report beside each run's L1 verdict the run's cost, number of turns, duration, input and output token counts, and the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`). A dedicated verdict function SHALL pass when a run spawned no helper agent and SHALL name the spawning calls when it did; the runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status. The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run. All of this logic SHALL be covered by L0 tests against recorded or synthetic event streams, so no model call is needed to exercise it.

#### Scenario: Telemetry printed beside the verdict
- **WHEN** a dev-runner scenario completes
- **THEN** its summary carries cost, turns, duration, token counts, the helper-call list, the single-context verdict, and the configuration label

#### Scenario: Helper spawn detected from a recorded stream
- **WHEN** a recorded event stream contains a `Task` or `Agent` or `Workflow` tool call
- **THEN** the single-context verdict fails and names the call, without a model run

#### Scenario: Budget cap passed through
- **WHEN** the runner is invoked with a budget cap
- **THEN** the host receives it as its hard cap and a run that exceeds it ends as a runner failure, not as a skill failure

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration holding only settings and linked credentials, and the summary labels the run as isolated; without the flag it labels the run as ambient
