# Spec Delta

## MODIFIED Requirements

### Requirement: Isolated measurement environment
A routing run SHALL execute against an isolated host configuration that contains only the skills under measurement. It SHALL contain no operator-specific skills, hooks, plugins or agents. It SHALL also contain none of the surfaces the operator's claude.ai account carries: the skills and plugins the account syncs, and its claude.ai MCP connectors. Results then reproduce on any machine and describe a user's install rather than the developer's. A run that cannot establish that isolation SHALL fail with a message naming what is missing, and SHALL NOT fall back to the ambient configuration.

An isolated configuration — the routing rig's, or the dev runner's in isolated mode — SHALL authenticate in one of two ways. If a long-lived token is in the environment, the configuration SHALL hold no credentials of its own. Otherwise it SHALL hold a link to the operator's stored login, never a copy.

While such a link exists, a login refresh the host performs inside the isolated configuration SHALL reach the stored login. The host refreshes by replacing the link with a file of its own. When the replacement expires later than the stored login, the harness SHALL write it to the stored location with owner-only permissions, within a second of the replacement, and SHALL check once more when the run ends. Credentials that do not expire later SHALL never be written. Credential values SHALL NOT be printed, logged, or kept anywhere other than the stored location and the isolated configuration.

The host serializes refreshes only within one configuration directory. A run that starts while the stored login has expired, or is about to, SHALL therefore first hold an exclusive refresh claim beside the stored login. A run that finds the claim held SHALL wait a bounded time for the refreshed login, then proceed with it. If the wait ends without one, the run SHALL refuse with a message naming the cause. A claim left behind by a run that ended without releasing it SHALL stop blocking after a bounded age.

A login the host rejects only once a case is running cannot be detected before the run starts. A routing case that the host ends for that reason SHALL produce no routing verdict, and its recorded error SHALL carry the host's reason and the re-login instruction the dev runner gives for the same failure.

Account surfaces follow the login, not the configuration directory. Every isolated configuration SHALL therefore carry settings that hold exactly three opt-outs and nothing else: claude.ai skill sync off, claude.ai plugin sync off, and claude.ai connectors disabled. Before a run starts, the harness SHALL refuse an isolated configuration in either of these cases, with a message naming what is wrong:

- its settings are not exactly that object;
- it already holds synced skills or synced plugins.

This applies to a configuration the harness creates and equally to one an operator prepared and passed in.

Whether the host takes its Anthropic profiles only from the profile-directory variable (requirement: Isolated child environment) is unverified. Unless a long-lived token is in the environment, the harness SHALL therefore also refuse an isolated run before it starts while the default Anthropic profile directory holds any entry or cannot be listed. That directory is the one the run's host children would resolve: the user's XDG configuration directory, or `~/.config` without one, followed by `anthropic`. The message SHALL name that directory, never its contents, and SHALL name both remedies: moving the profiles aside, or token mode.

After a run, an isolated measurement SHALL count as invalid in either of these cases:

- the host's stream shows an account surface, in its initialization event or in any later change to its command list. An account surface is any of these:
  - an MCP server, whatever its source;
  - a plugin other than the host's built-in plugins;
  - a skill or command that the host tags as synced from claude.ai, or names under the claude.ai skills namespace;
- the isolated configuration holds synced skills or synced plugins after the run.

An invalid measurement is reported as follows:

- **Dev runner.** The runner SHALL read the host's stream as the host writes it, and SHALL stop the host at the first event that shows a surface, rather than finding the surface after the run. It SHALL send a termination request first and kill the host only if it is still running after a bounded grace. An invalid run SHALL exit with the untested status. Its message SHALL name each surface by kind and name, say that the configuration's opt-outs did not hold, and also name any billing reason the stream shows (requirement: Dev-runner cost and helper-agent telemetry). It SHALL compute no verdict and make no judge call.
- **Routing case.** A case whose stream shows a surface SHALL be stopped as soon as the surface appears. It SHALL be recorded as an error naming the surface, whether or not a route was recorded.
- **Routing sweep.** A routing run whose shared isolated configuration holds synced skills or synced plugins after its cases SHALL record every case of the run as such an error. A case started after the content appeared may have loaded it without any tag in its stream.

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

#### Scenario: Account surfaces opted out
- **WHEN** the harness prepares an isolated configuration
- **THEN** its settings hold exactly the opt-outs for claude.ai skill sync, plugin sync and connectors, and nothing else

#### Scenario: Prepared configuration without the opt-outs
- **WHEN** an operator-prepared configuration passed to the harness holds empty settings, or already holds synced skills
- **THEN** the run is refused before any host process starts, the message names what is missing or present, and the ambient configuration is not used

#### Scenario: Anthropic profile in the default directory
- **WHEN** an isolated run is about to start, no long-lived token is in the environment, and the default Anthropic profile directory holds an entry
- **THEN** the run is refused before any host process starts, the message names the directory and not its entries, and the ambient configuration is not used

#### Scenario: Account surface in an isolated dev run
- **WHEN** an isolated dev run's initialization event lists a claude.ai MCP server, or a later command-list change in its stream adds a skill tagged as synced from claude.ai
- **THEN** the host is stopped at that event, the run exits with the untested status, its message names each surface and says the opt-outs did not hold, no verdict is computed and no judge call is made

#### Scenario: Synced content left in the configuration
- **WHEN** an isolated dev run finishes, or reaches its time limit, and its configuration holds synced skills or synced plugins
- **THEN** the run exits with the untested status and names what was found, ahead of any host failure or time limit

#### Scenario: Built-ins are not account surfaces
- **WHEN** an isolated run's initialization event lists no MCP server, only the host's built-in plugins, and skills without a claude.ai sync tag or namespace
- **THEN** no account surface is reported and the run is measured

#### Scenario: Account surface in a routing case
- **WHEN** a routing case's stream shows a claude.ai account surface, before or after a route is recorded
- **THEN** the case is stopped and recorded as an error naming the surface, it counts neither as unrouted nor toward any kind's total, and a negative case does not pass on it

#### Scenario: Synced content found after a sweep
- **WHEN** a routing run's shared isolated configuration holds synced skills or synced plugins after its last case
- **THEN** every case of the run is recorded as an error naming that content, the raw per-case results are persisted, the tracked report is left unchanged, and the run exits with a failure status

### Requirement: A conditions change invalidates comparison
When a routing run is produced under changed measurement conditions, the report SHALL NOT present the previous score as a comparable predecessor. The conditions are workspace staging, epoch policy, case set, model, and the isolation of the host configuration. The report SHALL instead record that conditions changed, so that a movement caused by the rig is never read as a movement caused by the skills.

The report and the run's raw results SHALL record the isolation conditions they were measured under. When the outgoing report records no isolation conditions, or records different ones, the run SHALL treat the earlier score as measured under different conditions, without the operator having to declare it. The operator's own declaration of a conditions change SHALL still apply for every other condition.

#### Scenario: Staging changed between runs
- **WHEN** a run follows a change to how workspaces are staged
- **THEN** the report marks the earlier score as measured under different conditions rather than as superseded

#### Scenario: Earlier report measured with account surfaces present
- **WHEN** a routing run is measured with the claude.ai account surfaces closed, and the outgoing report records no isolation conditions
- **THEN** the new report marks the earlier score as measured under different conditions rather than as superseded, although the operator declared no conditions change

#### Scenario: Same isolation conditions
- **WHEN** the outgoing report records the same isolation conditions as the new run, and the operator declares no conditions change
- **THEN** the new report states the earlier score as the one it supersedes

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

The account's claude.ai MCP connectors publish too. Their tool names depend on the account, so no fixed list can deny them. Instead:

- every run SHALL start with the connector switch off (requirement: Isolated child environment);
- a run in either mode whose stream nevertheless shows an MCP server sourced from claude.ai SHALL be stopped at the event that shows it, as the requirement "Isolated measurement environment" prescribes for a dev run, and SHALL be untested;
- an isolated run SHALL also be held to the wider account-surface check of the requirement "Isolated measurement environment".

The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run, naming the isolated directory.

The runner SHALL remove from the model-under-test child's environment every inherited variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike. That means every inherited `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch.

- **Ambient mode.** The runner SHALL leave every other inherited variable in place, apart from setting the connector switch to off, so that the operator's effort and session settings remain part of what an ambient run measures.
- **Isolated mode.** The child SHALL receive the isolated child environment instead (requirement: Isolated child environment). Its allowlist admits none of those billing variables and no effort or session setting of the launching process, so that an isolated run measures the default host. The one `ANTHROPIC_`-prefixed variable an isolated child carries is the profile directory, which the harness sets to an empty directory and which routes no billing.

Failures SHALL be reported as follows:

- a host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far;
- when that error is a failure to authenticate, the message SHALL also tell the operator that the stored login is no longer valid and must be renewed by running `claude` and entering `/login`;
- a non-zero host exit without such an event SHALL report the host's stderr;
- a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry.

The runner's exit status SHALL distinguish four outcomes, so that only a failed verdict reads as a failure of the skill:

- every verdict the run computed passed;
- a verdict failed — L1, or a graded L2 criterion;
- the run is untested, for one of two reasons:
  - the subscription could not serve it: a login the host rejected; a stream reporting overage use, a refused or unknown rate-limit status, or an API-key source; a stream that reports no rate-limit status at all, so overage cannot be ruled out; or a judge call that produced no grade;
  - its isolation did not hold: a claude.ai account surface reached an isolated run (requirement: Isolated measurement environment), or a claude.ai connector reached an ambient run. Such a run's message SHALL also name any API-key source, overage use, or refused or unknown rate-limit status that its stream shows, so that a surface never hides a billing problem;
- any other runner failure.

The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic SHALL be covered by L0 tests against recorded and synthetic event streams:

- the verdicts;
- the event parsing and the telemetry;
- the command the runner builds and the judge command;
- the judge's child environment and the model-under-test child's environment;
- the stream checks that mark a call unavailable, the account-surface checks, and the stop at the first surface;
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

#### Scenario: Connector in an ambient run
- **WHEN** an ambient run's stream lists an MCP server sourced from claude.ai
- **THEN** the host is stopped at the event that lists it, the run exits with the untested status and names the server and the connector switch as the opt-out that did not hold, and an MCP server the operator configured outside claude.ai is not reported and does not stop the run

#### Scenario: A surface does not hide overage
- **WHEN** an isolated run's stream shows an account surface and a rate-limit report with overage in use
- **THEN** the run exits with the untested status, and its message names both the surface and the overage

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
- **THEN** the model-under-test child's environment still carries them, and its connector switch is off

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
- **THEN** the child runs against a configuration kept outside the workspace. That configuration holds only the pinned opt-out settings, an empty profile directory and, unless a long-lived token is in the environment, linked credentials. The summary labels the run as isolated and names that directory; without the flag it labels the run as ambient

### Requirement: Isolated child environment
An isolated host child SHALL receive an environment built from an allowlist. This covers every routing-rig run and the model-under-test child of every dev-runner run in isolated mode. It SHALL NOT receive the launching process's environment with only the configuration directory overridden. One function, shared by both runners, SHALL build that environment. The dev judge's child also runs in an isolated configuration. Its environment is governed by the requirement "Subscription text roles (dev runner)", not by this one, except for the account-surface variables below, which this requirement prescribes for every host child.

The allowlist SHALL admit only:
- `PATH` and `HOME`;
- `CLAUDE_CODE_OAUTH_TOKEN`, the long-lived OAuth token variable;
- variables that describe the machine rather than configure the host: user identity and login shell, locale, temporary directories, XDG base directories, proxy and certificate-trust settings, and the process basics Windows requires.

The configuration-directory variable SHALL be set to the isolated directory, replacing any inherited value.

Two account-surface variables SHALL be set by the harness rather than admitted. Each replaces any inherited value:
- the connector switch, `ENABLE_CLAUDEAI_MCP_SERVERS`, set to off, so that the host does not fetch the account's claude.ai MCP servers;
- the Anthropic profile-directory variable, `ANTHROPIC_CONFIG_DIR`, set to an empty directory that belongs to the isolated configuration, so that no Anthropic profile stored outside that configuration can become the child's login. The user's default profile directory is one such place.

Every other variable SHALL be dropped. That includes:
- the variables a launching desktop-app or SDK session sets to bind a child to itself: entrypoint, session identifiers, messaging socket and token, host auth refresh, and OAuth scopes;
- the variables that tune the host: effort, tool enablement, compaction, timeouts, API endpoint, and MCP connection settings;
- variables that no list names yet. A host that adds one would otherwise leak it into measurement without any sign.

The connector switch SHALL reach every host child the harness starts, not only the isolated ones: the ambient model-under-test child, the dev judge's child and its login check, and the advisory audit pre-flight's child as well. The profile-directory variable SHALL reach every child that runs in an isolated configuration, the dev judge's child included. The switch's value SHALL be defined in one place and applied wherever a host child is started.

A runner in ambient mode SHALL keep passing the operator's environment to the child, less only the billing variables the dev runner removes from every model-under-test run (requirement: Dev-runner cost and helper-agent telemetry), and with the connector switch set to off.

The advisory audit pre-flight's child SHALL receive that same ambient environment: the launching environment less every billing variable the dev runner removes, with the connector switch set to off. An exported API key, gateway or cloud-provider switch then cannot bill its calls per token. One function SHALL build the ambient environment for the dev runner and the audit pre-flight alike.

Building the isolated environment SHALL print nothing, and no runner output SHALL carry the value of any variable, admitted or dropped. L0 tests with synthetic values SHALL cover how the environment is built, both places that use it, every place the connector switch is applied, and the audit pre-flight's environment.

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
- **THEN** the child inherits the operator's environment, its effort and session variables included, except the billing variables, and its connector switch is off

#### Scenario: Judge child outside this requirement
- **WHEN** an isolated dev run is graded by the dev judge
- **THEN** the judge's child gets the environment that "Subscription text roles (dev runner)" prescribes, plus the connector switch set to off and the empty profile directory, and only the model-under-test child is held to this allowlist

#### Scenario: Connector switch on every host child
- **WHEN** the isolated child, the ambient model-under-test child, the dev judge's child and the audit pre-flight's child are each started from an environment that sets the connector switch to on
- **THEN** each of them receives the switch set to off

#### Scenario: Audit pre-flight drops billing variables
- **WHEN** the audit pre-flight is launched from an environment carrying an API key, a gateway base URL with an auth token and a cloud-provider switch
- **THEN** its child's environment carries none of them, keeps every other inherited variable, and has its connector switch off

#### Scenario: Profile directory emptied
- **WHEN** an isolated child, or the dev judge's child in an isolated configuration, is started from an environment that names an Anthropic profile directory
- **THEN** the child's profile-directory variable names an empty directory belonging to the isolated configuration, and the inherited value is not passed on

#### Scenario: No values printed
- **WHEN** the isolated environment is built from an environment holding a messaging token
- **THEN** nothing is printed, and the token's value appears in no output
