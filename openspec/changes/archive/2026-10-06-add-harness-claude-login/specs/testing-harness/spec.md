# Spec Delta

## ADDED Requirements

### Requirement: Harness-owned host logins
The harness SHALL keep its own login for each host client it drives, in a login home it owns. No harness action may then share a refresh token with, write to, or log out the operator's own logins of that client: neither the CLI nor the desktop app. This requirement covers Claude. A client added later gets its own home under the same rules.

**Location.**

- The home SHALL lie under a per-user state directory for the harness, following the platform's convention:
  - Linux: the XDG state directory;
  - macOS: Application Support;
  - Windows: the local application-data directory.
- Its path SHALL be absolute, its permissions owner-only, and it SHALL lie outside the repository.
- It SHALL never equal, contain, or lie inside the operator's own configuration directory of any client.
- A test override of the state directory SHALL be refused in any of these cases:
  - it is not an absolute path;
  - it equals or contains the user's home directory;
  - it equals, contains or lies inside a client's own configuration directory;
  - it lies inside the repository.

**Creation and wipes.**

- When the harness creates a home, it SHALL write a marker into it.
- It SHALL delete a home only when the home carries that marker and is not a symbolic link.
- It SHALL seed only a home that does not exist yet. A login SHALL never adopt a directory at the home's path that lacks the marker, or a symbolic link there: it refuses, naming the directory, and writes, logs out and deletes nothing in it.
- Before the first login, the Claude home SHALL be seeded with two things: the account-surface opt-out settings that every isolated configuration carries (requirement: Isolated measurement environment), and an empty profile directory. The seeding comes first because account content synced once stays on disk.

**Commands.**

- **Login.**
  - It SHALL run the client's own subscription login inside the home, never a console or API-billing login.
  - Only the operator runs it, never an agent. It SHALL refuse when its standard input is not a terminal. It SHALL also refuse when its environment carries a marker of an agent session: a variable that a Claude Code session or a Codex shell exports to the commands it runs. The refusal names the marker variables, never their values. Both refusals are speed bumps, not guards: an agent with a terminal tool has a terminal, and a marker can be unset. The rule that agents never log in is the guard.
  - Its environment, the login environment, is the operator's own, so that a browser can open. Every billing variable and every host-session variable is removed, the configuration directory is set to the home, and the profile directory is set to the home's empty one.
  - On a home that already holds a login, it SHALL first log out of that login in the home. Where the login is no file in the home, the host's own status decides whether the home holds one.
  - If that logout fails, the login SHALL stop, naming the logout's exit status, and neither log in nor wipe: replacing a login whose logout did not go through could orphan a live grant.
- **Reset.** A reset option SHALL log out, wipe the marked home, seed it again and log in. A failed logout stops a reset as it stops a login.
- **Logout.**
  - A logout command SHALL run the client's own logout in the home and nowhere else.
  - Every logout SHALL run in the login environment: the logout command's own, the one before a login, and the one in a reset. No inherited token, profile directory or configuration directory can then steer it at another login.
  - Live check L3 shows whether the harness logout leaves the operator's other Claude sessions working. Until L3 has passed, the logout command, a reset and a login over an existing login SHALL say, before they log out, that this is unverified.
- **Status.**
  - It SHALL make no model call.
  - It SHALL print only:
    - the home's path;
    - whether the home carries its marker;
    - whether the home is logged in;
    - the auth method and the API provider;
    - whether the host reports the home as its configuration directory;
    - whether the home is clean, naming any offending entry;
    - how long the access token remains valid;
    - which login runs would use.
  - It SHALL never print a credential value, an email address or an organization.
  - Its status check SHALL run without the long-lived token, so that it reports the home's own login even when a token is exported.
  - Agents MAY run it.
- **Default profile directory.** Whether the host ignores the default Anthropic profile directory when the profile directory is set to the home's empty one is unverified. No login, logout or status check SHALL therefore start a client while the default profile directory holds an entry or cannot be listed, whether or not a long-lived token is exported: none of them carries the token. The refusal names that directory, never its contents, and its remedy is to move the profiles aside.
- **Locking.** Logout, reset, and a login over an existing login SHALL hold, while they log out and wipe, the same refresh claim that isolated runs take. None of them may then interleave with a run that is writing a refreshed login back.

**Preflight.** Before any isolated configuration links the harness login, the harness SHALL confirm the conditions below, without a model call. If one fails, it SHALL refuse the run as untested and start no host process for it. It SHALL never fall back to the operator's own login. Each failing condition names one remedy:

- **The home is missing, or has wider permissions than owner-only.** Remedy: `uv run poe host-login claude`.
- **A directory at the home's path lacks the marker.** The harness did not create it and does not adopt it. Remedy: move it aside, then run `uv run poe host-login claude`.
- **The default Anthropic profile directory holds an entry or cannot be listed.** Remedy: move the profiles aside.
- **The host reports no login, or the status check yields no login state.** Remedy: `uv run poe host-login claude`.
- **The home is not clean.** Its settings differ from the pinned opt-outs, or it holds any of these: skills, agents, commands, output styles, a user memory file, or an installed plugin. Marketplace caches are allowed. Remedy: remove the named entry, or run `uv run poe host-login claude --reset`.
- **The auth method is not the subscription login, or the API provider is not Anthropic's own API.** Remedy: `uv run poe host-login claude --reset`.
- **The host reports a configuration directory other than the home.** Remedy: remove the wrapper or managed setting that redirects it.
- **The host reports no configuration directory at all.** Remedy: update the host to a version that reports it.

Every refusal message SHALL follow one template:

- the word untested;
- the cause;
- exactly one remedy;
- the login note.

It SHALL carry no credential value, email address or organization.

The login note is the sentence that the operator's own login is not affected. While live check L3 has not passed, a message whose remedy is the harness login command, with or without its reset option, SHALL carry in its place the sentence that whether that command logs out the operator's other Claude sessions is unverified. The runners' login-failure messages for the harness login close with the same note (requirement: Dev-runner cost and helper-agent telemetry).

A long-lived token in the environment SHALL bypass the harness login entirely. The preflight is not run, and nothing is linked (requirement: Isolated measurement environment).

**Credentials.** The harness SHALL read no field of a stored login other than its expiry. It SHALL print or log no credential value. It SHALL write credentials only through the write-back that the requirement "Isolated measurement environment" prescribes.

**Stopping a host child.** This applies whenever the harness stops a host child it started:

- a dev run at its time limit;
- a judge call at its time limit;
- a routing case after its route, or at its limit;
- the harness login's status check and logout at their limit;
- the advisory audit pre-flight's call at its limit, which runs on the operator's own login.

The harness SHALL first send a termination request. It SHALL kill the child only if the child has not exited after a bounded grace, so that a host part-way through writing a refreshed login can finish. On a platform whose termination request is itself a kill, the kill is the request.

#### Scenario: Default home location
- **WHEN** the harness resolves the Claude home on Linux with no override and no XDG state directory set
- **THEN** the home is `~/.local/state/thesis-proposal-dev/hosts/claude`, it has owner-only permissions once created and carries the marker, and it is not `~/.claude`

#### Scenario: Override overlapping the operator's configuration
- **WHEN** the state-directory override equals the user's home directory, lies inside `~/.claude`, or contains the configuration directory named by `CLAUDE_CONFIG_DIR`
- **THEN** every host-login command and every isolated run refuses, naming the override, and nothing is created

#### Scenario: Login refused without a terminal
- **WHEN** the login command is started with a standard input that is not a terminal
- **THEN** it refuses with a message saying the operator must run it in a terminal, and no login of the client is started

#### Scenario: Login refused inside an agent session
- **WHEN** the login command is started with a terminal, from an environment that carries a Claude Code session marker
- **THEN** it refuses, naming the marker variable but not its value, and no login of the client is started

#### Scenario: Opt-outs seeded before the login
- **WHEN** the login command creates a home
- **THEN** the home's settings hold exactly the account-surface opt-outs, and its empty profile directory exists, before the client's login starts

#### Scenario: Login never bills per token
- **WHEN** the login command runs from an environment carrying an API key, a gateway base URL with an auth token, a cloud-provider switch and a long-lived token
- **THEN** the client's login receives none of them, its configuration directory is the home, and it is never a console login

#### Scenario: Status reveals no account details
- **WHEN** the status command runs against a logged-in home whose host status reports an email address and an organization
- **THEN** its output carries neither, and no model call is made

#### Scenario: Relative override refused
- **WHEN** the state-directory override is a relative path
- **THEN** every host-login command and every isolated run refuses, naming the override, and nothing is created

#### Scenario: Reset deletes only a marked home
- **WHEN** a reset finds the home without its marker, or finds the home path to be a symbolic link
- **THEN** it deletes nothing and refuses, naming the directory

#### Scenario: Unmarked directory never adopted
- **WHEN** the login command, without the reset option, finds a directory at the home's path that carries no marker, whether or not it holds a login
- **THEN** it refuses, naming the directory and the remedy of moving it aside, starts no client, and writes no marker or settings into it

#### Scenario: Failed logout stops a re-login
- **WHEN** the logout that a login over an existing login, or a reset, runs first exits with a failure
- **THEN** no login starts, nothing in the home is wiped, and the refusal names the logout's exit status

#### Scenario: Profile directory bars the login commands
- **WHEN** the login, logout or status command runs while the default Anthropic profile directory holds an entry, with or without a long-lived token exported
- **THEN** it refuses, naming that directory and not its entries, and starts no client

#### Scenario: Logout stays in the home
- **WHEN** the logout command runs, or a reset or a login over an existing login logs out, from an environment carrying a long-lived token, an API key, a profile-directory variable and another configuration directory
- **THEN** the client's logout runs in the login environment: its configuration directory is the home, its profile directory is the home's empty one, none of the inherited values reaches it, and the operator's own configuration is not touched

#### Scenario: Logout caveat until L3
- **WHEN** live check L3 has not passed, and the logout command runs or a refusal names the harness login command as its remedy
- **THEN** the message says that whether this logs out the operator's other Claude sessions is unverified, and it does not claim that the operator's own login is unaffected

#### Scenario: No harness login
- **WHEN** an isolated run starts while the home holds no login
- **THEN** the run is refused as untested. Its message names `uv run poe host-login claude` and closes with the login note. No host process is started for the run, and the operator's own login is not linked

#### Scenario: Home not clean
- **WHEN** an isolated run starts while the home holds a synced skill
- **THEN** the run is refused as untested, and the message names the entry and the reset remedy

#### Scenario: Wrong auth method
- **WHEN** the host's status for the home reports an API-key method, or a provider other than Anthropic's own API
- **THEN** the run is refused as untested with the reset remedy, and the remedy is never an API key

#### Scenario: Configuration directory redirected
- **WHEN** the host's status for the home reports a configuration directory other than the home
- **THEN** the run is refused as untested, and the message names the redirect as the cause

#### Scenario: Token bypasses the harness login
- **WHEN** an isolated run starts with a long-lived token in the environment
- **THEN** no preflight of the home runs, nothing is linked, and the home is neither read nor written

#### Scenario: Termination before kill
- **WHEN** a dev run reaches its time limit with the host still running
- **THEN** the host first receives a termination request, it is killed only if it is still running after the grace, and the run ends as a runner failure naming the limit

## MODIFIED Requirements

### Requirement: Isolated measurement environment
A routing run SHALL execute against an isolated host configuration that contains only the skills under measurement. It SHALL contain no operator-specific skills, hooks, plugins or agents. It SHALL also contain none of the surfaces the operator's claude.ai account carries: the skills and plugins the account syncs, and its claude.ai MCP connectors. Results then reproduce on any machine and describe a user's install rather than the developer's. A run that cannot establish that isolation SHALL fail with a message naming what is missing, and SHALL NOT fall back to the ambient configuration.

The rules below on authentication, on account-surface opt-outs and on account surfaces govern Claude configurations: the routing rig's, and the dev runner's in isolated mode. A configuration of a client added later is outside them. The requirements that add that client prescribe its home, its login, its child environment and its checks (requirement: Harness-owned host logins).

An isolated Claude configuration SHALL authenticate in one of three ways:

- **Long-lived token.** If a long-lived token is in the environment, the configuration SHALL hold no credentials of its own.
- **Harness login (default).** Otherwise it SHALL hold a link to the harness login (requirement: Harness-owned host logins), never a copy. It SHALL do so only after that login has passed its preflight.
- **Operator's login (explicit opt-in).** Only when the operator explicitly names another stored login's directory for the run SHALL the configuration link that login instead. The harness SHALL never take this opt-in as a fallback, and SHALL label the run with it.

A run SHALL never link the operator's own login because the harness login is missing or was refused. The harness SHALL accept no prepared configuration directory in place of the one it creates. An environment that still names one SHALL be refused with a message naming the replacement.

While such a link exists, a login refresh the host performs inside the isolated configuration SHALL reach the linked login. The host refreshes by replacing the link with a file of its own.

- When the replacement expires later than the linked login, the harness SHALL write it to the link's target with owner-only permissions. The target is the harness login, or the opted-in login. The write SHALL happen within a second of the replacement, and the harness SHALL check once more when the run ends.
- Credentials that do not expire later SHALL never be written.
- No credentials SHALL be written anywhere but the link's target.
- Credential values SHALL NOT be printed, logged, or kept anywhere other than the link's target and the isolated configuration.

The host serializes refreshes only within one configuration directory. A run that starts while the linked login has expired, or is about to, SHALL therefore first hold an exclusive refresh claim beside the linked login. A run that finds the claim held SHALL wait a bounded time for the refreshed login, then proceed with it. If the wait ends without one, the run SHALL refuse with a message naming the cause. A claim left behind by a run that ended without releasing it SHALL stop blocking after a bounded age.

A login the host rejects only once a case is running cannot be detected before the run starts. A routing case that the host ends for that reason SHALL produce no routing verdict. Its recorded error SHALL carry the host's reason and the one remedy for the login the case used, as the dev runner names it for the same failure (requirement: Dev-runner cost and helper-agent telemetry).

Billing per token, too, shows only in a case's stream. Each routing case SHALL therefore be held to the billing checks the dev runner applies to a model-under-test stream (requirement: Dev-runner cost and helper-agent telemetry), over the part of the stream the case read:

- an API-key source;
- a provider other than Anthropic's own API, where the stream reports one;
- overage in use;
- a rate-limit status other than `allowed` or `allowed_warning`;
- a rate-limit report without its overage flag;
- no rate-limit report at all, in a case whose stream holds a model turn. A case stopped before any model turn is not held to this one, and neither is a case stopped for an account surface, which the surface cut short. An assistant event the host writes itself for a failed API call, such as a rejected login, is no model turn: no model served it.

The host may write the rate-limit report after the assistant events of the turn that routed, rather than before the first assistant event. It may also write it after that turn's tool results, and, when the route is a skill invocation, after the skill instructions the host adds to the conversation (all recorded on 2.1.284). A case whose route is recorded SHALL therefore be read on past the route, past the routing turn's tool results and past the skill's instructions. It SHALL be stopped at the first of these: the rate-limit report, the run's closing result, or the first assistant event of a later turn (a model response other than the one that routed). It SHALL NOT be read into a later turn beyond that turn's first assistant event. The case's deadline still bounds it.

A case that fails one of these SHALL produce no routing verdict, and SHALL be recorded as an error naming the reason. The rig SHALL then start no further case. It SHALL record every case of the run as such an error, persist the raw per-case results, leave the tracked report unchanged, and exit with a failure status. Detection after a case is the rig's only billing check, so it stops the rest of the run.

Account surfaces follow the login, not the configuration directory. Every isolated Claude configuration SHALL therefore carry settings that hold exactly three opt-outs and nothing else: claude.ai skill sync off, claude.ai plugin sync off, and claude.ai connectors disabled. Before a run starts, the harness SHALL refuse an isolated Claude configuration in either of these cases, with a message naming what is wrong:

- its settings are not exactly that object;
- it already holds synced skills or synced plugins.

This applies to every isolated Claude configuration.

Whether the host takes its Anthropic profiles only from the profile-directory variable (requirement: Isolated child environment) is unverified. Unless a long-lived token is in the environment, the harness SHALL therefore also refuse an isolated Claude run before it starts while the default Anthropic profile directory holds any entry or cannot be listed: before any host process starts for it, the harness login's status check included. That directory is the one the run's host children would resolve: the user's XDG configuration directory, or `~/.config` without one, followed by `anthropic`. The message SHALL name that directory, never its contents, and SHALL name both remedies: moving the profiles aside, or token mode.

After a run, an isolated measurement SHALL count as invalid in either of these cases:

- the host's stream shows an account surface, in its initialization event or in any later change to its command list. An account surface is any of these:
  - an MCP server, whatever its source;
  - a plugin other than the host's built-in plugins;
  - a skill or command that the host tags as synced from claude.ai, or names under the claude.ai skills namespace;
- the isolated configuration holds synced skills or synced plugins after the run.

An invalid measurement is reported as follows:

- **Dev runner.** The runner SHALL read the host's stream as the host writes it, and SHALL stop the host at the first event that shows a surface, rather than finding the surface after the run. It SHALL send a termination request first and kill the host only if it is still running after a bounded grace (requirement: Harness-owned host logins). An invalid run SHALL exit with the untested status. Its message SHALL name each surface by kind and name, say that the configuration's opt-outs did not hold, and also name any billing reason the stream shows (requirement: Dev-runner cost and helper-agent telemetry). It SHALL compute no verdict and make no judge call.
- **Routing case.** A case whose stream shows a surface SHALL be stopped as soon as the surface appears. It SHALL be recorded as an error naming the surface, whether or not a route was recorded.
- **Routing sweep.** A routing run whose shared isolated configuration holds synced skills or synced plugins after its cases SHALL record every case of the run as such an error. A case started after the content appeared may have loaded it without any tag in its stream.

#### Scenario: Ambient configuration excluded
- **WHEN** the operator's own configuration defines additional skills or session hooks
- **THEN** the routing run is unaffected by them

#### Scenario: Isolation cannot be established
- **WHEN** the isolated configuration cannot authenticate or cannot be created
- **THEN** the run exits with a diagnostic and produces no routing verdicts

#### Scenario: Harness login linked by default
- **WHEN** an isolated configuration is prepared with no long-lived token in the environment and no opt-in
- **THEN** its credentials link targets the harness login, and the operator's own stored login is neither linked nor read

#### Scenario: No fallback to the operator's login
- **WHEN** the harness login fails its preflight
- **THEN** the run is refused as untested, and the operator's own stored login is not linked

#### Scenario: Operator's login only by explicit opt-in
- **WHEN** the operator names their own stored login's directory for the run
- **THEN** the link targets that login, a refresh is written back there, and the run is labelled as using the operator's login

#### Scenario: Login rejected during a case
- **WHEN** the host ends a routing case on the harness login with an error result saying it failed to authenticate, after an assistant event of its own carrying the same failure
- **THEN** the case produces no routing verdict. Its error carries the host's reason, names `uv run poe host-login claude` as the remedy, and closes with the login note (requirement: Harness-owned host logins). The host's own assistant event is no model turn, so the case is not recorded as a billing signal and the run is not voided for one

#### Scenario: Rate-limit report after the route
- **WHEN** a routing case's stream records its route and then the rate-limit report, either before or after the routing turn's tool result
- **THEN** the case is not stopped at the route or at the tool result; it is read on to the report and stopped there, before the next turn's output, and it records the route and no billing reason

#### Scenario: Rate-limit report after a skill's instructions
- **WHEN** a routing case's first tool call is the skill invocation that routes, and its stream records the route, the call's tool result, the skill's instructions the host adds to the conversation, then the rate-limit report, then the next turn
- **THEN** the case is stopped at neither the tool result nor the instructions; it is read on to the report and stopped there, before the next turn's first assistant event, and it is counted with its route and no billing reason

#### Scenario: Billing signal in a routing case
- **WHEN** a routing case's stream reports overage in use, or an API-key source, whether or not a route was recorded
- **THEN** the case is recorded as an error naming the reason, no further case starts, every case of the run is recorded as such an error, the raw per-case results are persisted, the tracked report is left unchanged, and the run exits with a failure status

#### Scenario: Unreported rate limit in a routing case
- **WHEN** a routing case's stream holds a model turn but no rate-limit report by the time the case is stopped (at the first assistant event of a later turn, at the run's closing result, or at its deadline, never at an event of the routing turn), or reports a rate limit without its overage flag
- **THEN** the run is voided as for any billing signal, and the reason says that overage could not be ruled out. A case stopped for an account surface, before any model turn or after one, is recorded with the surface and not with a missing rate-limit report; it voids the run only for a billing reason its stream shows, and otherwise the next case still starts

#### Scenario: Refresh inside an isolated run reaches the stored login
- **WHEN** the host replaces the linked credentials with a login that expires later than the harness login
- **THEN** the harness login holds the refreshed credentials with owner-only permissions, the isolated configuration links to it again, and the operator's own stored login is unchanged

#### Scenario: Older credentials never written back
- **WHEN** the host's replacement expires no later than the linked login
- **THEN** the linked login is left unchanged

#### Scenario: Concurrent runs with an expired login
- **WHEN** two isolated runs start while the harness login has expired
- **THEN** only one holds the refresh claim, and the other waits until the refreshed login is written back and starts with it

#### Scenario: Refresh never arrives
- **WHEN** a run waits on a held claim and the bounded wait ends with the linked login still expired
- **THEN** the run refuses with a diagnostic naming the held refresh, and neither the ambient configuration nor the operator's own login is used

#### Scenario: Abandoned claim
- **WHEN** a claim is older than its bounded age
- **THEN** the next run that needs a refresh takes the claim over

#### Scenario: Long-lived token in the environment
- **WHEN** the environment carries a long-lived host token
- **THEN** the isolated configuration holds no credentials. The harness login is neither checked, linked nor written, and neither is the operator's own stored login

#### Scenario: Account surfaces opted out
- **WHEN** the harness prepares an isolated configuration
- **THEN** its settings hold exactly the opt-outs for claude.ai skill sync, plugin sync and connectors, and nothing else

#### Scenario: Prepared configuration without the opt-outs
- **WHEN** the environment names an operator-prepared configuration directory for the harness to use in place of its own, whether or not that directory holds the opt-outs
- **THEN** the run is refused before any host process starts. The message says that the override is no longer read and names the harness login command. The ambient configuration is not used

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

### Requirement: Isolated child environment
An isolated Claude host child SHALL receive an environment built from an allowlist. This covers every Claude host child that runs in an isolated configuration:

- every routing-rig run;
- the model-under-test child of every Claude dev-runner run in isolated mode;
- the dev judge's child, together with its login check.

It also covers the Claude harness login's status checks (requirement: Harness-owned host logins). Such a child SHALL NOT receive the launching process's environment with only the configuration directory overridden. One function SHALL build that environment for all of them, so that no second allowlist can drift from the first. The status check alone then drops the long-lived token from it, so that it reports the home's own login rather than the token's.

A host child of a client added later is outside the allowlist, the configuration-directory variable and the account-surface variables of this requirement. The requirement that adds the client prescribes that child's environment, and the same function SHALL build it from that client's own description.

The allowlist SHALL admit only:
- `PATH` and `HOME`;
- `CLAUDE_CODE_OAUTH_TOKEN`, the long-lived OAuth token variable;
- variables that describe the machine rather than configure the host: user identity and login shell, locale, temporary directories, XDG base directories, proxy and certificate-trust settings, and the process basics Windows requires.

The configuration-directory variable SHALL be set to the configuration the child runs in, replacing any inherited value.

Two account-surface variables SHALL be set by the harness rather than admitted. Each replaces any inherited value:
- the connector switch, `ENABLE_CLAUDEAI_MCP_SERVERS`, set to off, so that the host does not fetch the account's claude.ai MCP servers;
- the Anthropic profile-directory variable, `ANTHROPIC_CONFIG_DIR`, set to an empty directory that belongs to the configuration the child runs in. No Anthropic profile stored outside that configuration can then become the child's login; the user's default profile directory is one such place.

Every other variable SHALL be dropped. That includes:
- the variables a launching desktop-app or SDK session sets to bind a child to itself: entrypoint, session identifiers, messaging socket and token, host auth refresh, and OAuth scopes;
- the variables that tune the host: effort, tool enablement, compaction, timeouts, API endpoint, and MCP connection settings;
- variables that no list names yet. A host that adds one would otherwise leak it into measurement without any sign.

The connector switch SHALL reach every Claude host child the harness starts, not only the isolated ones: the ambient model-under-test child and the advisory audit pre-flight's child as well. The profile-directory variable SHALL reach every Claude child that runs in an isolated configuration. The switch's value SHALL be defined in one place and applied wherever a Claude host child is started.

A runner in ambient mode SHALL keep passing the operator's environment to the child, less only the billing variables the dev runner removes from every model-under-test run (requirement: Dev-runner cost and helper-agent telemetry), and with the connector switch set to off.

The advisory audit pre-flight's child SHALL receive that same ambient environment: the launching environment less every billing variable the dev runner removes, with the connector switch set to off. An exported API key, gateway or cloud-provider switch then cannot bill its calls per token. One function SHALL build the ambient environment for the dev runner and the audit pre-flight alike.

Building the isolated environment SHALL print nothing. No runner output SHALL carry the value of any variable, admitted or dropped. L0 tests with synthetic values SHALL cover:

- how the environment is built;
- every place that uses it: the rig, the isolated dev run, the judge's call and its login check, and the harness login's status check;
- every place the connector switch is applied;
- the audit pre-flight's environment.

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
- **THEN** the isolated child receives it unchanged, together with `PATH` and `HOME`. The harness login's status check is the one exception: it receives the same environment without the token

#### Scenario: Status check reports the home's own login
- **WHEN** the harness login's status check runs from an environment that exports a long-lived token
- **THEN** its child's environment is the allowlisted one for the home without the token, so the host reports the home's own login

#### Scenario: Machine plumbing kept
- **WHEN** the launching environment sets locale, temporary-directory, proxy, or certificate-trust variables
- **THEN** the isolated child receives them unchanged

#### Scenario: Ambient run keeps the operator's environment
- **WHEN** the dev runner runs without isolated mode
- **THEN** the child inherits the operator's environment, its effort and session variables included, except the billing variables, and its connector switch is off

#### Scenario: Judge child outside this requirement
- **WHEN** an isolated dev run is graded by the dev judge, launched from an environment that sets proxy, certificate-trust and shell variables, an effort setting and an API key
- **THEN** the judge's child is no longer outside this requirement. It and its login check receive exactly the variables the model-under-test child receives for the same configuration. Proxy, certificate trust and shell are included, and the effort setting and the key are not

#### Scenario: One allowlist for every isolated child
- **WHEN** the routing rig, an isolated dev run and the dev judge each start a child for the same configuration, from the same launching environment
- **THEN** the three child environments are identical

#### Scenario: Connector switch on every host child
- **WHEN** the isolated child, the ambient model-under-test child, the dev judge's child and the audit pre-flight's child are each started from an environment that sets the connector switch to on
- **THEN** each of them receives the switch set to off

#### Scenario: Audit pre-flight drops billing variables
- **WHEN** the audit pre-flight is launched from an environment carrying an API key, a gateway base URL with an auth token and a cloud-provider switch
- **THEN** its child's environment carries none of them, keeps every other inherited variable, and has its connector switch off

#### Scenario: Profile directory emptied
- **WHEN** an isolated child, or the dev judge's child in an isolated configuration, is started from an environment that names an Anthropic profile directory
- **THEN** the child's profile-directory variable names an empty directory belonging to the configuration the child runs in, and the inherited value is not passed on

#### Scenario: No values printed
- **WHEN** the isolated environment is built from an environment holding a messaging token
- **THEN** nothing is printed, and the token's value appears in no output

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

- The child environment SHALL be the isolated child environment (requirement: Isolated child environment), built by the same function as the isolated model-under-test child's. No API key, no gateway or provider-routing variable, no inherited effort setting and no host-session variable reaches the child.
- The one credential that MAY reach the child is the subscription's own long-lived login token, when the operator has exported one. The isolated configuration relies on that token, and it is passed through unread. Apart from that token, the harness SHALL NOT read, copy or forward a credential.
- Before the first call of an invocation, the runner SHALL confirm that the host is logged in with the subscription login. That login is one of these:
  - the login linked into the isolated configuration: the harness login, or the operator's login under the explicit opt-in;
  - the subscription's long-lived token.
- Otherwise the runner SHALL stop with the one remedy for that login:
  - for the harness login, the harness login command, closing with the login note (requirement: Harness-owned host logins);
  - for the opted-in login, `claude`, then `/login`;
  - for the token, a new token from `claude setup-token`.
- The remedy for a missing login SHALL never be an API key.
- Judging SHALL require the isolated configuration, inside which the linked login is kept current.
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
- the call exceeds its time limit. The child process SHALL then first be sent a termination request, and SHALL be killed if it has not exited after a bounded grace (requirement: Harness-owned host logins);
- the response carries no grade line.

An unavailable call SHALL stop further judge calls in the same invocation. A call whose result is marked as an error, and whose stream also shows an API-key source, a provider other than Anthropic's own API, overage in use or a refused rate-limit status, SHALL name that billing reason beside the error and count as untested for billing (Smoke, below).

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
- The smoke task SHALL continue past a failing scenario, with one exception. Once a scenario is untested because its stream showed billing other than through the subscription, or could not rule it out, no later scenario SHALL start a host process. Each later scenario is listed as not run, naming the earlier scenario and its reason. Detection after a run is the only billing check a Claude run has, so it stops the rest of the task.
- The smoke task SHALL end with a summary naming each scenario's outcome, exiting non-zero unless every scenario passed.
- The former metered smoke SHALL remain available as a separate registered task. It takes its model from the registry's roles table and runs behind the matrix cost gate.

#### Scenario: Judge command pinned
- **WHEN** the judge command is built for the registry's dev-judge ID and effort
- **THEN** it names that full ID, passes that effort, disables host customizations, offers no tools, limits the call to one turn, persists no session, requests the event stream, carries none of the graded content among its arguments, and never carries the minimal-mode flag

#### Scenario: Metered ID refused as dev judge
- **WHEN** the dev-judge role names a provider-qualified metered ID or an alias
- **THEN** the runner refuses before any call and names the role

#### Scenario: Credentials and session settings never forwarded
- **WHEN** the launching environment carries an API key, a gateway base URL with an auth token, a provider-routing switch, an effort setting and host-session variables
- **THEN** none of them is present in the judge child's environment. Present are the path, home, locale, temporary-directory, proxy, certificate-trust and configuration-directory variables, and the subscription's long-lived login token when one was exported

#### Scenario: API-key login refused
- **WHEN** the preflight finds the host logged in by any method other than the subscription login
- **THEN** no judge call is made, and the runner stops with the remedy for the login in use and the untested status

#### Scenario: Expired login during judging
- **WHEN** a judge call's result is marked as an error saying the login expired and could not be refreshed
- **THEN** the criterion is untested, and no further judge call is made. The message carries the host's reason and the one remedy for the login in use: the harness login command when the harness login is linked

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
- **THEN** the child process first receives a termination request and is no longer running once the grace has passed, and the criterion is untested

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

#### Scenario: Smoke stops after a billing signal
- **WHEN** the first core scenario of the smoke task is untested because its stream reported overage in use
- **THEN** no later scenario starts a host process, the closing summary lists each of them as not run and names the overage, and the task exits non-zero

#### Scenario: Smoke cannot bill silently
- **WHEN** the smoke task is started from an environment that exports an API key
- **THEN** no host process it starts receives the key, every scenario's model run carries a budget cap, and a scenario whose stream nevertheless reports an API-key source is listed as untested in the closing summary

#### Scenario: Metered smoke behind the gate
- **WHEN** the metered smoke task is started
- **THEN** it prints a cost estimate for the registry's smoke model and waits for explicit confirmation before any metered call

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

The runner SHALL accept a hard budget cap passed through to the host. It SHALL label each run as measuring either the ambient host configuration or an isolated one prepared for the run. For an isolated run, the label SHALL name the isolated directory and the login it links: the harness login, the operator's login under the explicit opt-in, or a long-lived token. For a linked login, the label SHALL also name that login's directory, which is the one place a refresh is written back. The label SHALL follow how the configuration was prepared, never the link's state after the run: while the host refreshes, its own file stands where the link was until the harness restores it. A run that always isolates, such as the install probe, SHALL be labelled with the login it would have linked when its configuration could not be prepared.

The runner SHALL remove from the model-under-test child's environment every inherited variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike. That means every inherited `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch.

- **Ambient mode.** The runner SHALL leave every other inherited variable in place, apart from setting the connector switch to off, so that the operator's effort and session settings remain part of what an ambient run measures.
- **Isolated mode.** The child SHALL receive the isolated child environment instead (requirement: Isolated child environment). Its allowlist admits none of those billing variables and no effort or session setting of the launching process, so that an isolated run measures the default host. The one `ANTHROPIC_`-prefixed variable an isolated child carries is the profile directory, which the harness sets to an empty directory and which routes no billing.

Failures SHALL be reported as follows:

- a host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far;
- when that error is a failure to authenticate, the message SHALL also say that the login the run used is no longer valid, and SHALL name the one remedy for that login:
  - for the harness login: running `uv run poe host-login claude`, closing with the login note (requirement: Harness-owned host logins);
  - for an ambient run or the opted-in login: running `claude` and entering `/login`;
  - for a long-lived token: generating a new one with `claude setup-token`;
- a run still going at its time limit SHALL be stopped as the requirement "Harness-owned host logins" prescribes, and SHALL end as a runner failure naming the limit;
- a non-zero host exit without such an event SHALL report the host's stderr;
- a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry.

The runner's exit status SHALL distinguish four outcomes, so that only a failed verdict reads as a failure of the skill:

- every verdict the run computed passed;
- a verdict failed — L1, or a graded L2 criterion;
- the run is untested, for one of two reasons:
  - the subscription could not serve it. This covers:
    - a harness login refused by its preflight;
    - a login the host rejected;
    - a stream reporting overage use, a refused or unknown rate-limit status, or an API-key source;
    - a stream that reports no rate-limit status at all, so overage cannot be ruled out;
    - a judge call that produced no grade;
  - its isolation did not hold: a claude.ai account surface reached an isolated run (requirement: Isolated measurement environment), or a claude.ai connector reached an ambient run. Such a run's message SHALL also name any API-key source, overage use, or refused or unknown rate-limit status that its stream shows, so that a surface never hides a billing problem;
- any other runner failure.

The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic SHALL be covered by L0 tests against recorded and synthetic event streams:

- the verdicts;
- the event parsing and the telemetry;
- the command the runner builds and the judge command;
- the judge's child environment and the model-under-test child's environment;
- the stream checks that mark a call unavailable, the account-surface checks, and the stop at the first surface;
- the login-failure remedy for each kind of login;
- the login label, and that a refresh is written back only into the labelled login's directory;
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
- **WHEN** an isolated run on the harness login ends with an error result saying the host failed to authenticate because the login expired and could not be refreshed
- **THEN** the runner failure carries the host's reason, names `uv run poe host-login claude` as the one remedy and closes with the login note, and the run exits with the untested status

#### Scenario: Expired ambient login names the operator's remedy
- **WHEN** an ambient run ends with an error result saying the host failed to authenticate because the login expired and could not be refreshed
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
- **THEN** the child runs against a configuration kept outside the workspace. That configuration holds only the pinned opt-out settings, an empty profile directory and, unless a long-lived token is in the environment, linked credentials. The summary labels the run as isolated and names that directory, the login it links and, for a linked login, that login's directory. Without the flag, the summary labels the run as ambient

#### Scenario: Write-back target labelled
- **WHEN** an isolated run on the harness login refreshes its login
- **THEN** the summary names the harness home as the linked login's directory, and the refreshed credentials are written there and nowhere else. The label is the same when the run ends while the host's refreshed file still stands in place of the link
