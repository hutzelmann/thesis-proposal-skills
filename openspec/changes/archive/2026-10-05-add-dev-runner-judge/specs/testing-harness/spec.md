## MODIFIED Requirements

### Requirement: Inverted-hybrid runners
Authoritative runs — the model matrix, release gates, and the judge and persona models those runs grade with and converse with — SHALL execute over metered API providers with native multi-model comparison and spend caps. Subscription-based CLI runs serve as the cheap everyday dev loop and are not the source of record. That includes the dev runner's own rubric judge: its grades SHALL be labelled as dev-runner results that are not comparable to matrix results, SHALL NOT be written where the support report reads its logs, and SHALL NOT stand in for an authoritative cell. CI executes only L0 and lint by default; metered eval runs are budget-capped.

Every L1 verdict SHALL be defined once as a pure function in the shared verdict module, taking plain values and returning a pass flag with an explanation, and both runners SHALL reach a scenario's verdict through it rather than reimplementing the assertions. Because the verdicts are pure, each SHALL be exercisable by L0 tests without a model call.

A verdict that asserts a produced file is in the standard format SHALL establish that by running the mechanical check over it and judging the reported errors, never by inspecting the text for characteristic substrings. Errors that follow from information the scenario's input did not carry MAY be tolerated, and the tolerated set SHALL be explicit. Where a defect makes the file unbuildable but is invisible to the mechanical check — which extracts narrowly rather than parsing YAML — the verdict SHALL assert it directly, and SHALL be narrow enough to admit the shapes that do build.

The dev-runner scenario set SHALL cover the import skill. It SHALL therefore support scenarios that stage no proposal file and instead supply a source document in the request, and that assert against a file the skill creates — whose name the skill chooses — rather than one staged in advance.

Wherever a scenario's skill is licensed to choose the produced file's name — including scenarios that stage a seed the skill may replace with a fresh `<slug>.md` — the verdict SHALL locate the produced proposal in the workspace rather than assume a staged filename. The selection SHALL be a pure function in the shared verdict module, exercisable by L0 tests without a model call, and both runners SHALL grade the file it selects.

#### Scenario: Release gate
- **WHEN** a release-gating eval is run
- **THEN** it executes on the metered authoritative path with per-model logs, not on the subscription dev runner

#### Scenario: Dev-runner grade is not a source of record
- **WHEN** a dev run is graded by the subscription judge
- **THEN** its summary labels the grades as dev-runner L2, not comparable to the matrix, and no file the support report reads has been written or changed

#### Scenario: Verdict reached from both runners
- **WHEN** a scenario's L1 assertions are evaluated on the metered path and on the dev runner
- **THEN** both call the same shared verdict function and reach the same pass flag for the same produced artifact

#### Scenario: Import iterated without metered spend
- **WHEN** import guidance is being iterated on
- **THEN** the dev runner can exercise the import skill end to end, pasting the source document into the request and judging the file the skill creates

#### Scenario: Structurally broken output rejected
- **WHEN** a produced file contains the expected substrings but leaves the metadata block unclosed and the reference list malformed
- **THEN** the verdict fails on the mechanical check's errors rather than passing on the substrings

#### Scenario: Unbuildable file the mechanical check cannot see
- **WHEN** a produced file places a TODO marker as a bare line inside the metadata block, so the document converter rejects the block while the mechanical check reports no error
- **THEN** the verdict fails on that defect

#### Scenario: Marker shapes that do build are accepted
- **WHEN** the same marker appears as the value of a key, quoted or unquoted
- **THEN** the verdict does not fail, because those shapes parse

#### Scenario: Tolerated shortfall
- **WHEN** the source document carries fewer references than the guidance requires
- **THEN** the reference-count error alone does not fail the verdict, because the skill must not invent sources

#### Scenario: Verdict logic covered without a model
- **WHEN** an L1 verdict's failure modes are tested
- **THEN** L0 tests call the pure verdict function directly and no model is invoked

#### Scenario: Draft written to a fresh filename
- **WHEN** a write scenario's model creates a new `<slug>.md` instead of editing the staged seed in place
- **THEN** the verdict grades the created file, not the untouched seed

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

The runner SHALL remove from the model-under-test child's environment every variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike: every `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch. It SHALL leave every other inherited variable in place, so that the operator's effort and session settings remain part of what a dev run measures.

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
- **WHEN** the runner is launched, in ambient or isolated mode, from an environment carrying an API key, a gateway base URL with an auth token, a cloud-provider switch and an effort setting
- **THEN** the model-under-test child's environment carries none of the first three and still carries the effort setting

#### Scenario: No result event
- **WHEN** the host exits without emitting a result event
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Recorded shape pinned
- **WHEN** the host renames a result-event field the telemetry reads
- **THEN** the L0 test against the recorded result event fails naming the field

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration kept outside the workspace that holds only settings and, unless a long-lived token is in the environment, linked credentials; the summary labels the run as isolated and names that directory; without the flag it labels the run as ambient

## ADDED Requirements

### Requirement: Subscription text roles (dev runner)

The dev runner's text-only role, its rubric judge, SHALL run through the unmodified official host CLI under the operator's subscription login. The judge SHALL be one single-turn text call per rubric criterion, issued under the following constraints.

**Invocation:**

- The model is named by the full model ID that the registry's roles table assigns to the dev judge, never by an alias. An ID that names a metered provider SHALL be refused before any call.
- The effort is passed explicitly, from the same roles table.
- Host customizations are disabled, no tools are offered, the call is limited to one turn, and no session is persisted.
- The host's minimal mode SHALL NOT be used, because it bypasses the subscription login.
- The prompt is delivered on standard input. The content under grading travels only in the prompt and is never written into a measured workspace.
- The child runs in a fixed working directory outside every measured workspace.

**Environment and login:**

- The child environment SHALL be built from an allowlist. No API key, no gateway or provider-routing variable, no inherited effort setting and no host-session variable reaches the child.
- The one credential that MAY reach the child is the subscription's own long-lived login token, when the operator has exported one. The isolated configuration relies on that token, and it is passed through unread. Apart from that token, the harness SHALL NOT read, copy or forward a credential.
- Before the first call of an invocation, the runner SHALL confirm that the host is logged in with the subscription login: the stored login, or the subscription's long-lived token. Otherwise it SHALL stop with the re-login instruction (`claude`, then `/login`). The remedy for a missing login SHALL never be an API key.
- Judging SHALL require the isolated configuration, inside which the stored login is kept current.
- The first judge call of an invocation runs alone. Later calls run at most four at a time across the process.

**Failing closed.** A judge call SHALL count as unavailable, never as a failing grade, when any of the following holds:

- the host's result is marked as an error;
- the result has no text, zero output tokens or no per-model usage;
- the host reports a rate-limit status other than `allowed` or `allowed_warning`;
- the stream carries no rate-limit report at all, so overage cannot be ruled out;
- overage is in use;
- the session used an API-key source;
- the call was served through a provider other than Anthropic's own API;
- the served model differs from the requested one;
- the call exceeds its time limit, in which case the child process SHALL be killed;
- the response carries no grade line.

An unavailable call SHALL stop further judge calls in the same invocation.

**Bounding and records:**

- The runner SHALL keep a cumulative notional-cost total of the judge calls and SHALL stop issuing calls once an operator-set cap is reached; criteria left ungraded then count as untested.
- Before a batch re-grade fans out, the runner SHALL print a notional estimate projected from the first call's measured cost. It SHALL NOT start the batch when the projection exceeds the cap.
- Each call SHALL record the host CLI version, the effort, the served model, its thinking tokens and its notional cost. A warning-level rate limit SHALL be reported with its window and utilization.

**Rubrics:**

- The dev judge and the matrix judge SHALL read the same rubric templates and criteria. Each rubric template and criterion SHALL be defined once, and the prompts the matrix judge sends SHALL stay byte-identical to the prompts it sent before that sharing existed.
- The dev judge's question SHALL be the visible user request. Where the matrix judge's question is an oracle list rather than the request, both judges SHALL use the same list.
- Kept dev-runner workspaces SHALL be re-gradable without re-running the model under test.

**Smoke:**

- The registered smoke task SHALL run the core scenarios on the dev runner in isolated mode, loading no key file. Its spend SHALL be kept off metered billing in three ways:
  - no billing variable reaches any host process it starts;
  - each scenario's model run carries a hard budget cap;
  - a scenario whose stream shows billing other than through the subscription (an API-key source, overage, or no rate-limit report) is reported untested, never passed.
- The smoke task SHALL continue past a failing scenario and end with a summary naming each scenario's outcome, exiting non-zero unless every scenario passed.
- The former metered smoke SHALL remain available as a separate registered task. It takes its model from the registry's roles table and runs behind the matrix cost gate.

#### Scenario: Judge command pinned
- **WHEN** the judge command is built for the registry's dev-judge ID and effort
- **THEN** it names that full ID, passes that effort, disables host customizations, offers no tools, limits the call to one turn, persists no session, requests the event stream, carries none of the graded content among its arguments, and never carries the minimal-mode flag

#### Scenario: Metered ID refused as dev judge
- **WHEN** the dev-judge role names a provider-qualified metered ID or an alias
- **THEN** the runner refuses before any call and names the role

#### Scenario: Credentials and session settings never forwarded
- **WHEN** the launching environment carries an API key, a gateway base URL with an auth token, a provider-routing switch, an effort setting and host-session variables
- **THEN** none of them is present in the judge child's environment, while the path, home, locale, temporary-directory and configuration-directory variables are, and so is the subscription's long-lived login token when one was exported

#### Scenario: API-key login refused
- **WHEN** the preflight finds the host logged in by any method other than the subscription login
- **THEN** no judge call is made, and the runner stops with the re-login instruction and the untested status

#### Scenario: Expired login during judging
- **WHEN** a judge call's result is marked as an error saying the login expired and could not be refreshed
- **THEN** the criterion is untested, the message carries the host's reason and the re-login instruction, and no further judge call is made

#### Scenario: Overage refuses the grade
- **WHEN** a judge call's stream reports overage in use, even with a grade line in the result
- **THEN** the grade is discarded and the criterion is untested

#### Scenario: Unreported rate limit refuses the grade
- **WHEN** a judge call's stream carries a grade line but no rate-limit report
- **THEN** the grade is discarded, the criterion is untested, and the reason says that overage could not be ruled out

#### Scenario: Warning-level rate limit still grades
- **WHEN** a judge call's stream reports the status `allowed_warning` without overage
- **THEN** the grade counts, and the summary reports the limit window and its utilization

#### Scenario: Served model differs
- **WHEN** the per-model usage shows that a model other than the requested ID produced the output
- **THEN** the criterion is untested and the message names both IDs

#### Scenario: Concurrency bounded
- **WHEN** more than four judge calls are pending in one process
- **THEN** at most four child processes run at any moment, and the first call of the invocation completed before any other started

#### Scenario: Time limit kills the child
- **WHEN** a judge call exceeds its time limit
- **THEN** the child process is no longer running, and the criterion is untested

#### Scenario: Notional cap reached
- **WHEN** the cumulative notional cost of an invocation's judge calls reaches the operator's cap
- **THEN** no further judge call is made, and the remaining criteria are reported untested with the cap named

#### Scenario: Batch projection over the cap
- **WHEN** a batch re-grade's first call projects a total above the cap
- **THEN** the runner prints the projection, makes no further call, and reports the remaining workspaces untested

#### Scenario: Judging without isolation refused
- **WHEN** judging is requested for a run in the ambient configuration
- **THEN** the runner refuses before running the model under test

#### Scenario: Re-grade without a model run
- **WHEN** kept workspaces of a scenario are re-graded
- **THEN** each workspace's produced artifact is graded by the dev judge, the model under test is not run, and no metered call is made

#### Scenario: Matrix judge prompt unchanged
- **WHEN** the matrix judge builds a prompt for a recorded rubric, question, answer and criterion
- **THEN** the prompt is byte-identical to the golden prompt recorded before the rubric material was shared

#### Scenario: Smoke continues past a failure
- **WHEN** the first core scenario of the smoke task fails
- **THEN** the remaining core scenarios still run, the closing summary lists every scenario's outcome, and the task exits non-zero

#### Scenario: Smoke cannot bill silently
- **WHEN** the smoke task is started from an environment that exports an API key
- **THEN** no host process it starts receives the key, every scenario's model run carries a budget cap, and a scenario whose stream nevertheless reports an API-key source is listed as untested in the closing summary

#### Scenario: Metered smoke behind the gate
- **WHEN** the metered smoke task is started
- **THEN** it prints a cost estimate for the registry's smoke model and waits for explicit confirmation before any metered call
