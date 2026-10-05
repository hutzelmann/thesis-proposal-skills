# Spec Delta

## ADDED Requirements

### Requirement: Isolated child environment
An isolated host child SHALL receive an environment built from an allowlist. This covers every routing-rig run and every dev-runner run in isolated mode. It SHALL NOT receive the launching process's environment with only the configuration directory overridden. One function, shared by both runners, SHALL build that environment.

The allowlist SHALL admit only:
- `PATH` and `HOME`;
- `CLAUDE_CODE_OAUTH_TOKEN`, the long-lived OAuth token variable;
- variables that describe the machine rather than configure the host: user identity and login shell, locale, temporary directories, XDG base directories, proxy and certificate-trust settings, and the process basics Windows requires.

The configuration-directory variable SHALL be set to the isolated directory, replacing any inherited value.

Every other variable SHALL be dropped. That includes:
- the variables a launching desktop-app or SDK session sets to bind a child to itself: entrypoint, session identifiers, messaging socket and token, host auth refresh, and OAuth scopes;
- the variables that tune the host: effort, tool enablement, compaction, timeouts, API endpoint, and MCP connection settings;
- variables that no list names yet. A host that adds one would otherwise leak it into measurement without any sign.

A runner in ambient mode SHALL keep passing the operator's environment to the child, less only the billing variables the dev runner removes from every model-under-test run (requirement: Dev-runner cost and helper-agent telemetry).

Building the isolated environment SHALL print nothing, and no runner output SHALL carry the value of any variable, admitted or dropped. L0 tests with synthetic values SHALL cover how the environment is built and both places that use it.

#### Scenario: Desktop session variables dropped
- **WHEN** a runner is launched from a desktop-app session that exports its entrypoint, session identifiers, messaging socket and token, auth-refresh flag, and OAuth scopes
- **THEN** the isolated child's environment carries none of them, and its configuration directory is the isolated one

#### Scenario: Host tuning outside the host's own prefix dropped
- **WHEN** the launching environment sets the API base URL, an API timeout, a compaction or auto-updater switch, or MCP connection settings
- **THEN** the isolated child receives none of them

#### Scenario: Unknown variable dropped
- **WHEN** the launching environment holds a variable that no list names
- **THEN** the isolated child does not receive it

#### Scenario: Long-lived token kept
- **WHEN** `CLAUDE_CODE_OAUTH_TOKEN` is set in the launching environment
- **THEN** the isolated child receives it unchanged, together with `PATH` and `HOME`

#### Scenario: Machine plumbing kept
- **WHEN** the launching environment sets locale, temporary-directory, proxy, or certificate-trust variables
- **THEN** the isolated child receives them unchanged

#### Scenario: Ambient run keeps the operator's environment
- **WHEN** the dev runner runs without isolated mode
- **THEN** the child inherits the operator's environment, its effort and session variables included, except the billing variables

#### Scenario: No values printed
- **WHEN** the isolated environment is built from an environment holding a messaging token
- **THEN** nothing is printed, and the token's value appears in no output

## MODIFIED Requirements

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL save that stream into the run's workspace so a kept workspace carries the run's tool calls and narration for later reading. Beside each run's L1 verdict it SHALL report:

- the model the host served, by the full ID the host reports, beside the name the run requested, and the host CLI version;
- the run's cost, number of turns and duration;
- the input and output token counts, with the cache read and cache write counts;
- the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`);
- for scenarios that produce a supervise feedback, the feedback body's word count, excluding URLs and the closing note;
- for a run graded by the subscription judge, each rubric criterion's grade, the judge's served model ID, its effort and CLI version, its thinking tokens, and the cumulative notional cost of the judge calls, all under a label saying the grades are dev-runner L2 and not comparable to the matrix.

A dedicated verdict function SHALL pass when a run spawned no more helper agents than its scenario allows — none unless the scenario declares an allowance, which a supervise scenario does for its single verifier — and SHALL name the spawning calls when it exceeds the allowance. The runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status.

For the supervise scenarios the verifier is part of the scored L1 verdict, not only of the advisory probe: a run SHALL fail when it spawned no helper whose task carries the skill's verifier brief, and when its review's verification section does not state who verified. The headless host offers a subagent tool, so a run that checks inline has skipped the verifier rather than fallen back.

Because the runner starts the host without permission prompts, it SHALL deny the host's outward-facing tools on every run — publishing artifacts and their comments or data, messaging other sessions, push notifications, remote triggers, scheduling, and design sync — so that no test run can publish, send or schedule anything, whatever the model decides. The routing rig SHALL deny the same tools, from the same list.

The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run, naming the isolated directory.

The runner SHALL remove from the model-under-test child's environment every variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike: every `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch. In ambient mode it SHALL leave every other inherited variable in place, so that the operator's effort and session settings remain part of what an ambient run measures. In isolated mode the child SHALL receive the isolated child environment instead (requirement: Isolated child environment), whose allowlist admits none of those billing variables and no effort or session setting of the launching process, so that an isolated run measures the default host.

Failures SHALL be reported as follows:

- a host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far;
- when that error is a failure to authenticate, the message SHALL also tell the operator that the stored login is no longer valid and must be renewed by running `claude` and entering `/login`;
- a non-zero host exit without such an event SHALL report the host's stderr;
- a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry.

The runner's exit status SHALL distinguish four outcomes, so that only a failed verdict reads as a failure of the skill:

- every verdict the run computed passed;
- a verdict failed — L1, or a graded L2 criterion;
- the run is untested because the subscription could not serve it. That covers a login the host rejected; a stream reporting overage use, a refused or unknown rate-limit status, or an API-key source; a stream that reports no rate-limit status at all, so overage cannot be ruled out; and a judge call that produced no grade;
- any other runner failure.

The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic SHALL be covered by L0 tests against recorded and synthetic event streams:

- the verdicts;
- the event parsing and the telemetry;
- the command the runner builds and the judge command;
- the judge's child environment and the model-under-test child's environment;
- the stream checks that mark a call unavailable;
- the exit-status mapping;
- the summary it prints.

The telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so a host field rename fails a test rather than blanking the line.

#### Scenario: Telemetry printed beside the verdict
- **WHEN** a dev-runner scenario completes
- **THEN** its summary carries cost, turns, duration, token counts including the cache pair, the helper-call list, the single-context verdict, and the configuration label

#### Scenario: Served model recorded, not the alias
- **WHEN** a run is started with a model alias such as `sonnet`
- **THEN** the summary carries the alias as the requested model, the full model ID the host reported serving, and the host CLI version

#### Scenario: Judged run reports L2 beside L1
- **WHEN** a scenario with a rubric twin is run with judging and both the run and the judge succeed
- **THEN** the summary carries each criterion's grade, the judge's served model ID, effort, CLI version, thinking tokens and notional cost under the not-comparable label, and the exit status reads passed only if L1 and every graded criterion passed

#### Scenario: Ungraded judge is untested, not failed
- **WHEN** the judge call for a criterion is unavailable
- **THEN** the run exits with the untested status, its summary names the reason, and the run's exit status is not the failed-verdict status

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
- **THEN** the run ends as a runner failure whose message names the host's subtype, its errors, and the cost and turns so far — not as a skill failure and not with an empty message — and its exit status is the runner-failure status

#### Scenario: Expired login names the remedy
- **WHEN** the host ends a run with an error result saying it failed to authenticate because the login expired and could not be refreshed
- **THEN** the runner failure carries the host's reason and tells the operator to run `claude` and enter `/login`, and the run exits with the untested status

#### Scenario: Overage or API billing on the model run
- **WHEN** the model-under-test run's stream reports that overage is in use, reports that the session used an API-key source, or carries no rate-limit report at all
- **THEN** the run exits with the untested status, names the cause, and no judge call is made

#### Scenario: Billing variables never reach the model run
- **WHEN** the runner is launched, in ambient or isolated mode, from an environment carrying an API key, a gateway base URL with an auth token and a cloud-provider switch
- **THEN** the model-under-test child's environment carries none of them

#### Scenario: Ambient run keeps the operator's settings
- **WHEN** the runner is launched in ambient mode from an environment carrying an effort setting and host-session variables
- **THEN** the model-under-test child's environment still carries them

#### Scenario: Isolated run drops the operator's settings
- **WHEN** the runner is launched in isolated mode from an environment carrying an effort setting and host-session variables
- **THEN** the model-under-test child's environment carries neither, because it is the isolated child environment

#### Scenario: No result event
- **WHEN** the host exits without emitting a result event
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Recorded shape pinned
- **WHEN** the host renames a result-event field the telemetry reads
- **THEN** the L0 test against the recorded result event fails naming the field

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration kept outside the workspace that holds only settings and, unless a long-lived token is in the environment, linked credentials; the summary labels the run as isolated and names that directory; without the flag it labels the run as ambient

