# Spec Delta

## ADDED Requirements

### Requirement: Dev-runner host adapters
The dev runner SHALL drive the model under test on one of its host CLIs, selected per invocation. Its hosts are:

- Claude Code, the default;
- Codex, under the operator's ChatGPT plan.

An invocation that selects no host SHALL keep every behaviour of the Claude runner as it was before this requirement, with two additions: its summary records the host and the host's label, and a summary-log path inside the directory the support report reads is refused (requirement: Inverted-hybrid runners). Codex has no ambient mode. Every Codex run executes in the Codex harness home (requirement: Harness-owned host logins).

**One core.** Every host SHALL share:

- the scenario set and the workspace staging;
- the L1 verdicts;
- the summary and its exit statuses;
- the saved event stream;
- the re-grading of kept workspaces;
- the judge machinery.

Five parts SHALL differ per host, each behind one adapter per host: the host's command, its run, its stream readers, its isolation and its login. No second runner SHALL copy the shared core. Each run's summary SHALL record its host.

**Canonical tool calls.** The verdicts and the route reader SHALL see tool calls under one set of names on every host. The completed items of a Codex stream SHALL be read as follows:

- a shell command as `Bash`. When the command reads the `SKILL.md` of a `proposal-*` skill, it is also read as a `Skill` call naming that skill;
- a file change as `Edit`;
- a subagent spawn as `Agent`, carrying the spawn prompt;
- an MCP tool call as `mcp__<server>__<tool>`;
- a web search as `WebSearch`.

**The model on Codex.**

- A Codex run SHALL require the model on the command line and pass it on unchanged. It SHALL refuse a provider-qualified identifier before staging.
- The registry SHALL hold no Codex role, the runner SHALL supply no default model, and the model-currency check SHALL raise no alert for Codex.
- A reasoning effort MAY be requested, from the host's explicit levels, but never the level that hands work to subagents.
- The effort the host served SHALL be recorded. A requested effort that the host did not serve SHALL make the run untested.

**Invocation.** A Codex run SHALL:

- run the host's non-interactive mode with its JSON event stream, the prompt on standard input, and the workspace as its working root. The workspace lies outside any git repository;
- validate its configuration strictly, so that an unknown configuration key fails the run rather than being ignored;
- sandbox the run to the workspace. Network access is granted only to scenarios that need it: those whose skill or sibling skills include import, literature search or reverse, and those that serve a fixture over localhost;
- enable subagents only for scenarios that declare a helper allowance;
- disable every other host feature that is on by default and adds a tool, a surface or reach beyond the shell and the workspace, through the host's validated feature switch. A default-on feature that adds none of these MAY stay on only when the allowlist names it with its reason. Before the run, it SHALL refuse when the host's feature listing still shows a feature enabled outside that allowlist; a feature the listing marks as removed and reading enabled SHALL be ignored by that check only when a pinned list of removed features measured reading enabled names it, and no feature the run disables is on that list. A listing row is a name, a stage of one or more words and an on/off state; the run SHALL refuse on any listing line it does not read that way, or whose stage is not one the host is known to print;
- keep the host's session record while the run lasts, read it after the run, and then delete it.

**Isolation.** A Codex run SHALL see only the skills under test, installed in the workspace where Codex discovers repository skills. Its home directory and XDG base directories SHALL be scratch directories belonging to the run, so the operator's user-scope skills, shell start-up files and key files are not visible to it. After the run, it SHALL count as untested in either of these cases:

- its session record lists a skill outside the workspace's skill directory, or shows a call of the host's cloud-skill tools;
- its stream shows an MCP tool call. The home configures no MCP server, so any call is foreign.

After the run, before the runner reads or writes anything in the workspace, it SHALL check that the workspace is still the directory the run started in and holds no link, no FIFO, socket or device, and no file with a second name elsewhere: the sandbox lets the run write the workspace, and a link it makes there never touches its target, so the runner, which is not sandboxed, would otherwise act on the target. The check SHALL fail closed: the workspace and every directory in it must still be open to their owner for reading, writing and search, and every entry must be examinable, because a directory the runner cannot list would hide a link from the check while the runner could still open a fixed name in it. Each such entry SHALL be removed without being followed, a directory closed to its owner is left as it is and never reopened, and the run SHALL be untested for isolation with an isolation stop recorded in the Codex home; no verdict reads its files. While that stop is recorded, every later Codex run SHALL be refused as untested for isolation before any Codex process starts, naming the stop's cause and its one remedy: reading the run's findings, then clearing the stop with the login command's clear option (requirement: Harness-owned host logins). A stop record that cannot be read SHALL count as a recorded stop. The status command reports the stop and is not refused by it.

**Scope.**

- The install-prompt scenarios SHALL be refused on Codex with a usage error.
- No registered smoke task SHALL run on Codex, because the host offers no hard budget cap.
- The routing rig stays Claude-only.
- The Codex runner SHALL refuse to start on a platform without POSIX file locks.

#### Scenario: Claude stays the default host
- **WHEN** the dev runner is invoked without a host
- **THEN** it runs the Claude host as before this requirement, apart from the two additions it names, and the summary records the host as Claude

#### Scenario: Codex run without a model
- **WHEN** a Codex run is requested without a model
- **THEN** the runner exits with a usage error before staging, and no Codex process is started

#### Scenario: Codex skill staged where Codex discovers it
- **WHEN** a Codex run stages a scenario
- **THEN** the skill under test and its siblings are installed under `<ws>/.agents/skills/`, the workspace lies outside any git repository, and a skill in the operator's `~/.agents/skills` cannot be discovered by the run

#### Scenario: Skill read through the shell
- **WHEN** a Codex stream shows a shell command reading `.agents/skills/proposal-check/SKILL.md`
- **THEN** the tool calls carry a `Skill` call naming `proposal-check`, and the route reader returns it

#### Scenario: Codex subagent spawn
- **WHEN** a Codex stream shows a subagent spawn in a scenario that allows none
- **THEN** the tool calls carry an `Agent` call with the spawn prompt, and the single-context verdict fails naming it

#### Scenario: Network only where needed
- **WHEN** the command is built once for a scenario with no network need and once for a scenario whose sibling is the literature-search skill
- **THEN** only the second grants the sandbox network access, and both confine writes to the workspace

#### Scenario: Subagents only where allowed
- **WHEN** the command is built for a scenario without a helper allowance, and for a supervise scenario
- **THEN** the first disables the subagent feature and the second does not

#### Scenario: Feature outside the allowlist
- **WHEN** the host's feature listing shows a feature enabled outside the allowlist
- **THEN** the run is refused as untested before any Codex run starts, and the message names the feature

#### Scenario: Multi-word feature stage
- **WHEN** the host's feature listing prints a row whose stage has several words, such as `under development`
- **THEN** the row is read as its name, that stage and its state, and a listing whose other rows pass does not refuse the run

#### Scenario: Removed feature reading enabled
- **WHEN** the host's feature listing shows a feature outside the allowlist enabled at the removed stage, after the run's disable switches
- **THEN** the check ignores it only when the pinned list of removed features measured reading enabled names it; an unpinned removed feature reading enabled, a disabled feature reading enabled at any stage, and a feature outside the allowlist enabled at any other stage each refuse the run and are named

#### Scenario: Feature listing line the parser does not read
- **WHEN** the host's feature listing contains a line that is not one name, one known stage and one on/off state, such as a header, an annotated state or a row of five fields
- **THEN** the run is refused as untested before any Codex run starts, and the message quotes the line

#### Scenario: Effort not served
- **WHEN** a Codex run requested an effort and its session record reports another
- **THEN** the run is untested and names both efforts

#### Scenario: Foreign skill offered
- **WHEN** a Codex session record lists a skill whose file lies outside the workspace's skill directory
- **THEN** the run is untested, names the skill's path, and no verdict is computed

#### Scenario: Install scenario on Codex
- **WHEN** an install-prompt scenario is requested on Codex
- **THEN** the runner exits with a usage error and starts nothing

#### Scenario: Codex workspace entry the runner must not follow
- **WHEN** a Codex run leaves the proposal in its workspace as a link to a file outside it and the event stream file's name as a link to another, or replaces the workspace itself
- **THEN** each link is removed without being followed, the run is untested for isolation, no verdict reads its files, an isolation stop is recorded in the Codex home, the event stream is saved to a new file, neither target is read or changed, and the message names the entries

#### Scenario: Recorded Codex stop refuses later runs
- **WHEN** a Codex run starts while an isolation stop is recorded in the Codex home, or while its stop record cannot be read
- **THEN** the run is refused as untested for isolation before any Codex process starts, naming the stop's cause and the login command's clear option; the status command reports the stop and is not refused by it; the clear option, run from a terminal outside an agent session, removes the stop and changes nothing else in the home

#### Scenario: Codex workspace directory the runner cannot list
- **WHEN** a Codex run leaves its workspace, or a directory in it, open for writing and search but not for listing, with a link inside it
- **THEN** the run is untested for isolation, an isolation stop is recorded in the Codex home, no verdict reads its files and no fixed name in the workspace is opened, the directory is not reopened, and the message names it

#### Scenario: Codex reset keeps the isolation stop
- **WHEN** the operator resets the Codex harness home while an isolation stop is recorded in it
- **THEN** the reset logs out, wipes and seeds the home and logs in, and the stop is recorded again in the reseeded home with its cause and time, so the next Codex run is still refused until the operator clears it

### Requirement: Codex plan billing guard
A Codex run SHALL bill the operator's ChatGPT plan quota and nothing else. The account keeps money out: the operator holds the plan's credit balance at zero, with automatic reload off. The checks below are the backstop, and each one fails closed. A run that any of them refuses:

- is untested and exits with the untested status;
- starts no further Codex process;
- is reported in the one refusal template (requirement: Harness-owned host logins).

**Environment.** These Codex children are covered: the run, the login-status check, the feature listing and the quota read. Each SHALL receive an environment built from the Codex record by the same function that builds the isolated Claude child's environment (requirement: Isolated child environment). That requirement's allowlist, configuration-directory variable and account-surface variables govern Claude children only; this requirement prescribes the Codex child's environment. It holds:

- only the machine plumbing the allowlist admits, without the Claude long-lived token;
- the Codex home variable, set to the harness home;
- for a run, the home directory and the XDG base directories, set to scratch directories belonging to the run.

Every inherited variable whose name begins with `CODEX_`, `OPENAI_` or `OPENROUTER_`, or ends in `_API_KEY`, SHALL be dropped. The run's summary SHALL name the dropped variables, never their values.

Immediately before starting any Codex child, the harness SHALL check again the final environment that child will receive, after every variable the harness sets has been applied. It SHALL refuse to start the child if that environment carries any variable of the dropped families other than the Codex home variable. The Codex home variable is the one such name the harness sets, and the exemption covers that name and no other. The reason: Codex's non-interactive mode honours an API-key variable above every stored login, and its login restriction would then log the harness home out.

**Before every run.** While holding the run lock, the runner SHALL read the plan quota through the client's own rate-limit read, which makes no model call. It SHALL refuse the run in any of these cases:

- **The read is unavailable.** The reader cannot start, its handshake or the read fails, it gives no answer within a bounded time, or its answer carries no quota window or no credits state.
- **Credits are present.** The answer reports a credit balance above zero, credits available, or unlimited credits.
- **The plan is not an allowed one.** The answer reports no plan type, or a plan type other than Plus or Pro. A free-plan login therefore refuses every run.
- **A window is nearly used up.** Either quota window is at 90 % or more of its limit.
- **A limit has been reached**, according to the answer.

The runner SHALL keep the last quota snapshot in the harness home. The snapshot holds only window usage, reset times and the plan type.

**After every run.** The runner SHALL read these from the session record:

- **Another provider.** A provider other than OpenAI's own SHALL make the run untested. The message names the provider and the CLI version.
- **Plan use unconfirmed.** No quota report, no credits state, or no plan type SHALL make the run untested, because plan use cannot be confirmed.
- **Plan not allowed.** A plan type other than Plus or Pro SHALL make the run untested, and the message names the plan.
- **Credits drawn.** Credits drawn during the run, a credit balance above zero, credits available, or unlimited credits SHALL make the run untested. The message names the credits as the cause and emptying the balance as the one remedy.
- **Limit reached.** A reached limit, or a usage-limit error, SHALL make the run untested.
- **Refresh failed.** A refresh token that was already used, has expired or was revoked SHALL make the run untested, with the harness login remedy.
- **Logged out by the restriction.** The client's login restriction logging the home out because an API key was in use SHALL make the run untested, with the harness login remedy.
- **Model rerouted.** A model reroute SHALL make the run untested. The message names the requested model and the served model.

A run that failed, or that was stopped at its time limit, is read the same way, from the session record captured before it was deleted. If that record shows another provider, a plan that is not allowed, credits, a reached limit or a model reroute, or if the run's isolation did not hold (requirement: Dev-runner host adapters), the run SHALL be untested, and the message SHALL name both the failure and that cause. Plan use unconfirmed alone does not make such a run untested: it stays a runner failure that names why it failed, its time limit included.

The summary SHALL report each quota window's usage before and after the run.

**Never in CI.** No CI workflow SHALL use a ChatGPT login.

**L0 coverage.** L0 tests SHALL cover every check above. They run over event streams and quota answers derived from the source of the pinned minimum CLI version. Until a later change replaces them with reduced recordings, the fixture directory SHALL label each of these files synthetic and name the source it follows.

#### Scenario: API keys in the launching environment
- **WHEN** a Codex run is started from an environment carrying `CODEX_API_KEY`, `OPENAI_API_KEY` and `OPENROUTER_API_KEY`
- **THEN** no Codex child receives any of them, the summary names the three variables, and no value appears in any output

#### Scenario: Leaking builder stopped before the spawn
- **WHEN** the environment builder is replaced by one that returns a Codex API-key variable
- **THEN** the harness refuses before starting any Codex process, and the run is untested

#### Scenario: Only the Codex home variable is exempt
- **WHEN** the final child environment carries the Codex home variable set to the harness home, and in a second case also carries a leaked `CODEX_ACCESS_TOKEN` or an unknown `CODEX_`-prefixed variable
- **THEN** the first child starts, and the second is refused before any Codex process starts, naming the variable but not its value

#### Scenario: Quota read unavailable
- **WHEN** the quota read fails its handshake or does not answer in time
- **THEN** the run is refused as untested, and no Codex run starts

#### Scenario: Credits state missing
- **WHEN** the quota read answers with its windows but without a credits state
- **THEN** the run is refused as untested because the read is unavailable, and no Codex run starts

#### Scenario: Credit balance present
- **WHEN** the quota read reports a credit balance above zero
- **THEN** the run is refused as untested, and the message names the balance as the cause and emptying it as the one remedy

#### Scenario: Plan outside the allowed set
- **WHEN** the quota read reports the free plan
- **THEN** the run is refused as untested, the message names the plan, and no Codex run starts

#### Scenario: Window near its limit
- **WHEN** the quota read reports a window at 92 %
- **THEN** the run is refused as untested, and the message names the window and its reset time

#### Scenario: Provider leak
- **WHEN** a run's session record reports a provider other than OpenAI's own
- **THEN** the run is untested, and the message names the provider and the CLI version

#### Scenario: Plan use unconfirmed
- **WHEN** a run's session record carries no quota report, or a quota report without a credits state
- **THEN** the run is untested, and the message says that plan use cannot be confirmed

#### Scenario: Credits drawn during a run
- **WHEN** a run's session record reports credits drawn or a credit balance above zero
- **THEN** the run is untested, and the message names the credits as the cause and emptying the balance as the one remedy

#### Scenario: Timed-out run that drew credits
- **WHEN** a Codex run is stopped at its time limit, and the session record captured before the stop reports credits drawn
- **THEN** the run is untested, not a runner failure, and the message names the time limit and the credits

#### Scenario: Refresh token reused
- **WHEN** a run fails with Codex's message that the refresh token was already used
- **THEN** the run is untested. The message names `uv run poe host-login codex` and closes with the login note (requirement: Harness-owned host logins)

#### Scenario: Logged out by the login restriction
- **WHEN** a run's stream shows Codex logging out because an API key was in use while a ChatGPT login is required
- **THEN** the run is untested, with the same remedy

#### Scenario: Model rerouted
- **WHEN** a run's stream carries a model-reroute error item
- **THEN** the run is untested and names both models

#### Scenario: Quota snapshot holds no secret
- **WHEN** a run completes
- **THEN** the harness home's quota snapshot holds window usage, reset times and the plan type, and no token, email address or account identifier

#### Scenario: Synthetic fixtures labelled
- **WHEN** the Codex stream fixtures are read
- **THEN** the directory's README lists each file as synthetic, together with the source it follows

## MODIFIED Requirements

### Requirement: Harness-owned host logins
The harness SHALL keep its own login for each host client it drives, in a login home it owns. No harness action may then share a refresh token with, write to, or log out the operator's own logins of that client: neither the CLI nor the desktop app. This requirement covers Claude and Codex. A client added later gets its own home under the same rules.

**Location.**

- The home SHALL lie under a per-user state directory for the harness, following the platform's convention:
  - Linux: the XDG state directory;
  - macOS: Application Support;
  - Windows: the local application-data directory.
- Its path SHALL be absolute, its permissions owner-only, and it SHALL lie outside the repository.
- It SHALL never equal, contain, or lie inside the operator's own configuration directory of any client.
- The Codex home SHALL also lie outside the system temporary directory, because Codex refuses to place its helper binaries there.
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
- Before the first login, the Codex home SHALL be seeded with a pinned configuration. That configuration selects OpenAI's own provider, requires the ChatGPT login, and keeps the credentials in a file in the home. It also turns off web search, the update check, history, analytics, feedback and the bundled skills.

**Commands.**

- **Login.**
  - It SHALL run the client's own subscription login inside the home, never a console or API-billing login: for Codex, never an API-key login or an access-token login. For Codex, it MAY use the client's device-code login.
  - Only the operator runs it, never an agent. It SHALL refuse when its standard input is not a terminal. It SHALL also refuse when its environment carries a marker of an agent session: a variable that a Claude Code session or a Codex shell exports to the commands it runs. The refusal names the marker variables, never their values. Both refusals are speed bumps, not guards: an agent with a terminal tool has a terminal, and a marker can be unset. The rule that agents never log in is the guard.
  - Its environment, the login environment, is the operator's own, so that a browser can open. Every billing variable and every host-session variable of that client is removed, and the configuration directory is set to the home. For Claude, the profile directory is also set to the home's empty one.
  - On a home that already holds a login, it SHALL first log out of that login in the home. Where the login is no file in the home, the host's own status decides whether the home holds one.
  - If that logout fails, the login SHALL stop, naming the logout's exit status, and neither log in nor wipe: replacing a login whose logout did not go through could orphan a live grant.
- **Reset.** A reset option SHALL log out, wipe the marked home, seed it again and log in. A failed logout stops a reset as it stops a login.
- **Clear (Codex).** A clear option of the login command SHALL instead remove a recorded Codex isolation stop (requirement: Dev-runner host adapters), holding the run lock, and change nothing else in the home. It carries the login's terminal and agent-marker refusals, and runs no client login. A Codex reset SHALL keep a recorded isolation stop, recording it again in the reseeded home with its cause and time: a reset replaces the login, not the run's findings, so the clear option stays the stop's one remedy.
- **Logout.**
  - A logout command SHALL run the client's own logout in the home and nowhere else.
  - Every logout SHALL run in the login environment: the logout command's own, the one before a login, and the one in a reset. No inherited token, profile directory or configuration directory can then steer it at another login.
  - Live check L3 shows whether the harness logout leaves the operator's other Claude sessions working. Live check X8 shows the same for Codex, whose logout revokes the home's refresh token, and whose login revokes the previous one held in the home. Until a client's check has passed, the logout command, a reset and a login over an existing login of that client SHALL say, before they log out, that this is unverified.
- **Status.**
  - It SHALL make no model call.
  - It SHALL print only:
    - the home's path;
    - whether the home carries its marker;
    - whether the home is logged in;
    - the auth method and, for Claude, the API provider;
    - for Claude, whether the host reports the home as its configuration directory;
    - whether the home is clean, naming any offending entry; for Codex, also whether its configuration equals the pinned one;
    - for Claude, how long the access token remains valid; for Codex, how long ago its stored login was last written, by login or refresh;
    - for Codex, the installed CLI version against the pinned minimum, and whether the feature allowlist holds;
    - for Codex, the last quota snapshot the home keeps and, only on request, a fresh plan quota from the client's rate-limit read;
    - for Codex, whether an isolation stop is recorded, and its cause;
    - which login runs would use.
  - It SHALL never print a credential value, any part of an API key, an email address or an organization.
  - The Claude status check SHALL run without the long-lived token, so that it reports the home's own login even when a token is exported.
  - Agents MAY run it.
- **Default profile directory.** Whether the Claude host ignores the default Anthropic profile directory when the profile directory is set to the home's empty one is unverified. No Claude login, logout or status check SHALL therefore start a client while the default profile directory holds an entry or cannot be listed, whether or not a long-lived token is exported: none of them carries the token. The refusal names that directory, never its contents, and its remedy is to move the profiles aside. A Codex client reads no Anthropic profile, so its commands are not held to this rule.
- **Locking.** Logout, reset, and a login over an existing login SHALL hold, while they log out and wipe, the lock the client's runs take: for Claude, the same refresh claim that isolated runs take; for Codex, the run lock. None of them may then interleave with a run that is writing a refreshed login back or running in the home.
- **Run lock (Codex).**
  - Codex runs SHALL execute one at a time per home.
  - Each of these SHALL hold an exclusive lock on a file in the home:
    - each run;
    - the quota read before it;
    - every login, logout and reset, and every clear;
    - every status command that reads the account, that is, a status command asked for a fresh plan quota.
  - The running Codex child SHALL hold that lock for as long as it lives, even when the harness process is killed. On Linux, the child SHALL also be signalled when the harness process dies.
  - A run that cannot take the lock within a bounded wait SHALL be refused as untested.

**Preflight.** The harness SHALL confirm the conditions below without a model call. For Claude, it does so before any isolated configuration links the harness login. For Codex, it does so before any run. If one fails, it SHALL refuse the run as untested and start no host process for it. It SHALL never fall back to the operator's own login. Each failing condition names one remedy.

For Claude:

- **The home is missing, or has wider permissions than owner-only.** Remedy: `uv run poe host-login claude`.
- **A directory at the home's path lacks the marker.** The harness did not create it and does not adopt it. Remedy: move it aside, then run `uv run poe host-login claude`.
- **The default Anthropic profile directory holds an entry or cannot be listed.** Remedy: move the profiles aside.
- **The host reports no login, or the status check yields no login state.** Remedy: `uv run poe host-login claude`.
- **The home is not clean.** Its settings differ from the pinned opt-outs, or it holds any of these: skills, agents, commands, output styles, a user memory file, or an installed plugin. Marketplace caches are allowed. Remedy: remove the named entry, or run `uv run poe host-login claude --reset`.
- **The auth method is not the subscription login, or the API provider is not Anthropic's own API.** Remedy: `uv run poe host-login claude --reset`.
- **The host reports a configuration directory other than the home.** Remedy: remove the wrapper or managed setting that redirects it.
- **The host reports no configuration directory at all.** Remedy: update the host to a version that reports it.

For Codex:

- **The installed CLI is older than the pinned minimum version.** Remedy: update the Codex CLI through the package manager.
- **The home is missing, or has wider permissions than owner-only.** Remedy: `uv run poe host-login codex`.
- **A directory at the home's path lacks the marker.** The harness did not create it and does not adopt it. Remedy: move it aside, then run `uv run poe host-login codex`.
- **The client reports no login, or a login other than the ChatGPT login.** Because the home's configuration requires the ChatGPT login, an API-key login reads as no login. Remedy: `uv run poe host-login codex`.
- **The home is not clean.** Its configuration differs from the pinned one in any key, or it holds any of these: an agents instruction file or its override, an environment file the client loads at start-up, a hooks file, skills other than the client's bundled system skills, or memories. Remedy: remove the named entry, or run `uv run poe host-login codex --reset`.
- **A feature outside the allowlist reads enabled.** Remedy: report it, because the pinned feature list does not match this CLI.

Every refusal message SHALL follow one template:

- the word untested;
- the cause;
- exactly one remedy;
- the login note.

It SHALL carry no credential value, email address or organization.

The login note is the sentence that the operator's own login of that client is not affected. While a client's revocation check has not passed (L3 for Claude, X8 for Codex), a message whose remedy is that client's harness login command, with or without its reset option, SHALL carry in its place the sentence that whether that command logs out the operator's other sessions of that client is unverified. The runners' login-failure messages for a harness login close with the same note (requirement: Dev-runner cost and helper-agent telemetry).

A long-lived Claude token in the environment SHALL bypass the Claude harness login entirely. The preflight is not run, and nothing is linked (requirement: Isolated measurement environment).

**Credentials.**

- The harness SHALL read no field of a stored Claude login other than its expiry.
- It SHALL never open a stored Codex login. The time of its last write is read from the file's modification time.
- It SHALL print or log no credential value.
- It SHALL write Claude credentials only through the write-back that the requirement "Isolated measurement environment" prescribes.
- It SHALL never write a Codex login. The client keeps that login current in its home.

**Stopping a host child.** This applies whenever the harness stops a host child it started:

- a dev run at its time limit;
- a judge call at its time limit;
- a routing case after its route, or at its limit;
- the harness login's status check and logout at their limit;
- the advisory audit pre-flight's call at its limit, which runs on the operator's own login;
- a Codex run at its time limit, and a Codex quota read at its limit.

The harness SHALL first send the client's own stop request: a termination request to Claude, and an interrupt to Codex, which ends the turn. It SHALL kill the child only if the child has not exited after a bounded grace, so that a host part-way through writing a refreshed login can finish. On a platform whose termination request is itself a kill, the kill is the request.

#### Scenario: Default home location
- **WHEN** the harness resolves the homes on Linux with no override and no XDG state directory set
- **THEN** the Claude home is `~/.local/state/thesis-proposal-dev/hosts/claude` and the Codex home is `~/.local/state/thesis-proposal-dev/hosts/codex`. Each has owner-only permissions once created and carries the marker, and neither is `~/.claude` or `~/.codex`

#### Scenario: Override overlapping the operator's configuration
- **WHEN** the state-directory override equals the user's home directory, lies inside `~/.claude` or `~/.codex`, or contains the configuration directory named by `CLAUDE_CONFIG_DIR` or `CODEX_HOME`
- **THEN** every host-login command and every isolated or Codex run refuses, naming the override, and nothing is created

#### Scenario: Login refused without a terminal
- **WHEN** the login command is started with a standard input that is not a terminal
- **THEN** it refuses with a message saying the operator must run it in a terminal, and no login of the client is started

#### Scenario: Login refused inside an agent session
- **WHEN** the login command is started with a terminal, from an environment that carries a Claude Code session marker
- **THEN** it refuses, naming the marker variable but not its value, and no login of the client is started

#### Scenario: Opt-outs seeded before the login
- **WHEN** the login command creates a Claude home
- **THEN** the home's settings hold exactly the account-surface opt-outs, and its empty profile directory exists, before the client's login starts

#### Scenario: Login never bills per token
- **WHEN** the login command runs from an environment carrying an API key, a gateway base URL with an auth token, a cloud-provider switch and a long-lived token
- **THEN** the client's login receives none of them, its configuration directory is the home, and it is never a console login

#### Scenario: Status reveals no account details
- **WHEN** the status command runs against a logged-in home whose host status reports an email address and an organization
- **THEN** its output carries neither, and no model call is made

#### Scenario: Relative override refused
- **WHEN** the state-directory override is a relative path
- **THEN** every host-login command and every isolated or Codex run refuses, naming the override, and nothing is created

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
- **WHEN** the Claude login, logout or status command runs while the default Anthropic profile directory holds an entry, with or without a long-lived token exported
- **THEN** it refuses, naming that directory and not its entries, and starts no client

#### Scenario: Logout stays in the home
- **WHEN** the Claude logout command runs, or a Claude reset or a login over an existing Claude login logs out, from an environment carrying a long-lived token, an API key, a profile-directory variable and another configuration directory
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

#### Scenario: Codex home in the temporary directory
- **WHEN** the state directory resolves inside the system temporary directory
- **THEN** every Codex host-login command and every Codex run refuses, naming the directory, and nothing is created

#### Scenario: Codex configuration seeded before the login
- **WHEN** the login command creates a Codex home
- **THEN** the home's configuration equals the pinned configuration before the client's login starts

#### Scenario: Codex login never by API key
- **WHEN** the Codex login runs from an environment carrying `CODEX_API_KEY` and `OPENAI_API_KEY`
- **THEN** the client receives neither, its home variable names the harness home, and no API-key or access-token login is started

#### Scenario: Codex status reveals no key
- **WHEN** the status command runs against a Codex home whose client status reports an API-key login with a masked key
- **THEN** the output reports the method as an API key, carries no fragment of the key, and no model call is made

#### Scenario: Codex stored login never opened
- **WHEN** the status command reports how long ago the Codex login was last written
- **THEN** it takes that time from the stored login file's modification time, and the file is never opened

#### Scenario: Codex login note until X8
- **WHEN** live check X8 has not passed, and a Codex refusal or a Codex login failure names `uv run poe host-login codex` as its remedy, with or without its reset option, or the Codex logout runs
- **THEN** the message says that whether this logs out the operator's other ChatGPT sessions is unverified, and it does not claim that the operator's own login is unaffected

#### Scenario: Codex home not clean
- **WHEN** a Codex run starts while the home's configuration carries a key the pinned configuration lacks, or the home holds an agents instruction file
- **THEN** the run is refused as untested, and the message names the key or the file and the reset remedy

#### Scenario: Codex CLI too old
- **WHEN** the installed Codex CLI reports a version below the pinned minimum
- **THEN** the run is refused as untested, and the message names both versions and the update remedy

#### Scenario: Serial Codex runs
- **WHEN** a second Codex run starts while another run holds the run lock
- **THEN** it waits a bounded time. If the lock has not been released by then, it is refused as untested, and the message names the held lock

#### Scenario: Lock outlives a killed harness
- **WHEN** the harness process is killed while its Codex child is running
- **THEN** the run lock stays held until the child exits, and no other Codex run, login or reset starts in the meantime

#### Scenario: Codex interrupted before kill
- **WHEN** a Codex run reaches its time limit
- **THEN** the child first receives an interrupt and is killed only if it is still running after the grace, and the run ends as a runner failure naming the limit

### Requirement: Inverted-hybrid runners
Authoritative runs SHALL execute over metered API providers, with native multi-model comparison and spend caps. Authoritative runs are the model matrix, the release gates, and the judge and persona models those runs grade with and converse with.

Subscription-based CLI runs serve as the cheap everyday dev loop and are not the source of record. The dev runner drives several host CLIs, each behind its own adapter (requirement: Dev-runner host adapters). A run on any of its hosts is a dev-loop result, and so is a grade from the dev runner's own rubric judge. Every such result:

- SHALL be labelled with its host as a dev-runner result that is not comparable to matrix results, for example "dev-runner (codex), not comparable to matrix";
- SHALL NOT be written where the support report reads its logs;
- SHALL NOT stand in for, or fill, an authoritative cell.

The dev runner SHALL refuse a summary-log path inside the directory the support report reads. CI executes only L0 and lint by default, and metered eval runs are budget-capped.

Every L1 verdict SHALL be defined once, as a pure function in the shared verdict module. It takes plain values and returns a pass flag with an explanation. Every runner SHALL reach a scenario's verdict through it rather than reimplementing the assertions: the metered path, and the dev runner on each of its hosts. Because the verdicts are pure, each SHALL be exercisable by L0 tests without a model call.

A verdict that asserts a produced file is in the standard format SHALL establish that by running the mechanical check over it and judging the reported errors. It SHALL never inspect the text for characteristic substrings instead.

- Errors that follow from information the scenario's input did not carry MAY be tolerated, and the tolerated set SHALL be explicit.
- Some defects make the file unbuildable but are invisible to the mechanical check, which extracts narrowly rather than parsing YAML. The verdict SHALL assert such a defect directly, and SHALL be narrow enough to admit the shapes that do build.

The dev-runner scenario set SHALL cover the import skill. It SHALL therefore support scenarios of this kind:

- they stage no proposal file;
- they supply a source document in the request instead;
- they assert against a file the skill creates, whose name the skill chooses, rather than one staged in advance.

Some scenarios license the skill to choose the produced file's name, including those that stage a seed the skill may replace with a fresh `<slug>.md`. In every such scenario, the verdict SHALL locate the produced proposal in the workspace rather than assume a staged filename. The selection SHALL be a pure function in the shared verdict module, exercisable by L0 tests without a model call, and every runner SHALL grade the file it selects.

#### Scenario: Release gate
- **WHEN** a release-gating eval is run
- **THEN** it executes on the metered authoritative path with per-model logs, not on the subscription dev runner

#### Scenario: Dev-runner grade is not a source of record
- **WHEN** a dev run is graded by the subscription judge
- **THEN** its summary labels the grades as dev-runner L2, not comparable to the matrix, and no file the support report reads has been written or changed

#### Scenario: Verdict reached from both runners
- **WHEN** a scenario's L1 assertions are evaluated on the metered path and on each of the dev runner's hosts, Codex among them
- **THEN** every one of them calls the same shared verdict function and reaches the same pass flag for the same produced artifact

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

#### Scenario: Codex dev run labelled by host
- **WHEN** a dev run on the Codex host completes
- **THEN** its summary records the host and the label "dev-runner (codex), not comparable to matrix". No file the support report reads has been written or changed, and no matrix cell takes its result

#### Scenario: Summary log where the support report reads
- **WHEN** a dev run on any host is given a summary-log path inside the directory the support report reads
- **THEN** the runner exits with a usage error before staging and writes nothing there

### Requirement: Measured environments carry no eval definitions
No runner SHALL stage eval definitions, oracles, or assertion text into the environment the model under test can read. That covers the fixture oracles, and the eval projections the skills ship for the standard's sake. A skill installed for a real user legitimately carries its eval projection. A skill installed for measurement SHALL NOT, because a model that can read what it will be graded on is not being measured.

This holds wherever a runner installs a skill: the host's skill directory in the dev runner's workspace, whichever host the run uses (for example `.claude/skills/` for Claude and `.agents/skills/` for Codex), the routing rig's isolated configuration, and an Inspect sandbox.

#### Scenario: Dev runner stages a skill
- **WHEN** the dev runner installs a skill into its temp workspace
- **THEN** the installed copy contains no eval definition file, while scripts, references, and templates copy as shipped

#### Scenario: Routing rig stages the skill set
- **WHEN** the routing rig installs the skills into its isolated configuration
- **THEN** no installed skill carries an eval definition file

#### Scenario: Inspect staging stays a whitelist
- **WHEN** an Inspect task stages a fixture and a skill's assets
- **THEN** only the skill's references, scripts, and templates enter the sandbox, and the fixture's oracle never does

#### Scenario: Codex dev run stages a skill
- **WHEN** the dev runner installs a skill and its siblings under `<ws>/.agents/skills/` for a Codex run
- **THEN** no installed copy contains an eval definition file, while scripts, references, and templates copy as shipped

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL save that stream into the run's workspace, so that a kept workspace carries the run's tool calls and narration for later reading. On Codex, the stream is the JSON event stream together with the records the runner reads from the host's session record, saved in the same file. Beside each run's L1 verdict, the runner SHALL report:

- the model the host served, by the full ID the host reports, beside the name the run requested, and the host CLI version. On Codex, the served model reads "unreported" unless the host reports a reroute, and the CLI version comes from the session record;
- the run's cost, number of turns and duration. Codex reports no cost. On Codex the cost SHALL be absent, never zero. A notional figure is given only where the registry's roster prices the same model name under OpenAI's provider; otherwise the run is labelled unpriced;
- the input and output token counts, with the cache read and cache write counts. On Codex, the input count excludes the cached input, and the reasoning token count is added;
- on Codex, each plan quota window's usage before and after the run;
- the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`), with a Codex subagent spawn reported as `Agent`;
- for scenarios that produce a supervise feedback, the feedback body's word count, excluding URLs and the closing note;
- for a run graded by the subscription judge: each rubric criterion's grade, the judge's served model ID, its effort and CLI version, its thinking tokens, and the cumulative notional cost of the judge calls. All of these appear under a label saying the grades are dev-runner L2 and not comparable to the matrix.

A dedicated verdict function SHALL pass when a run spawned no more helper agents than its scenario allows. A scenario allows none unless it declares an allowance, as a supervise scenario does for its single verifier. The verdict SHALL name the spawning calls when the run exceeds the allowance. The runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status.

For the supervise scenarios, the verifier is part of the scored L1 verdict, not only of the advisory probe. A run SHALL fail in either of these cases:

- it spawned no helper whose task carries the skill's verifier brief;
- its review's verification section does not state who verified.

Every host offers a subagent tool to a supervise run (Codex has its subagent feature enabled for scenarios with a helper allowance). A run that checks inline has therefore skipped the verifier rather than fallen back.

The runner starts the host without permission prompts. On Claude it SHALL therefore deny the host's outward-facing tools on every run, so that no test run can publish, send or schedule anything, whatever the model decides. Those tools are:

- publishing artifacts, and their comments or data;
- messaging other sessions;
- push notifications;
- remote triggers;
- scheduling;
- design sync.

The routing rig SHALL deny the same tools, from the same list.

On Codex there is no tool list to deny. Instead, the harness home's configuration and the run's command SHALL:

- disable apps, plugins, hooks, browser use, computer use, image generation, memories and web search;
- configure no MCP server.

A Codex run whose stream nevertheless shows an MCP tool call SHALL be untested (requirement: Dev-runner host adapters).

The account's claude.ai MCP connectors publish too. Their tool names depend on the account, so no fixed list can deny them. Instead:

- every Claude run SHALL start with the connector switch off (requirement: Isolated child environment);
- a Claude run in either mode whose stream nevertheless shows an MCP server sourced from claude.ai SHALL be stopped at the event that shows it, as the requirement "Isolated measurement environment" prescribes for a dev run, and SHALL be untested;
- an isolated Claude run SHALL also be held to the wider account-surface check of the requirement "Isolated measurement environment".

The runner SHALL accept a hard budget cap and pass it through to the host, where the host offers one. For a host that offers none, such as Codex, the runner SHALL refuse a budget cap rather than ignore it. A Codex run is bounded instead by its wall-clock limit and by the pre-run quota read (requirement: Codex plan billing guard).

The runner SHALL label each run with its host, and as measuring either the ambient host configuration or an isolated one prepared for the run.

- For an isolated Claude run, the label SHALL name the isolated directory and the login it links: the harness login, the operator's login under the explicit opt-in, or a long-lived token. For a linked login, the label SHALL also name that login's directory, which is the one place a refresh is written back. The label SHALL follow how the configuration was prepared, never the link's state after the run: while the host refreshes, its own file stands where the link was until the harness restores it. A run that always isolates, such as the install probe, SHALL be labelled with the login it would have linked when its configuration could not be prepared.
- Every run on a non-Claude host, Codex among them, is isolated. Its label SHALL name that host's harness home and the harness login.

The runner SHALL remove from the Claude model-under-test child's environment every inherited variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike. That means every inherited `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch. The child environment of every non-Claude host follows that host's billing-guard requirement: for Codex, the requirement "Codex plan billing guard".

- **Ambient mode.** The runner SHALL leave every other inherited variable in place, apart from setting the connector switch to off, so that the operator's effort and session settings remain part of what an ambient run measures.
- **Isolated mode.** The child SHALL receive the isolated child environment instead (requirement: Isolated child environment). Its allowlist admits none of those billing variables and no effort or session setting of the launching process, so that an isolated run measures the default host. The one `ANTHROPIC_`-prefixed variable an isolated child carries is the profile directory, which the harness sets to an empty directory and which routes no billing.

Failures SHALL be reported as follows:

- **An error result.** A host result event marked as an error SHALL end the run as a runner failure; a budget overrun is one such event. On Codex, the equivalent is a failed turn or a fatal error event. The message SHALL carry the host's subtype or message, its errors, and the cost and turns so far where the host reports them.
- **A failure to authenticate.** When that error is a failure to authenticate, the message SHALL also say that the login the run used is no longer valid, and SHALL name the one remedy for that login:
  - for the Claude harness login: running `uv run poe host-login claude`, closing with the login note (requirement: Harness-owned host logins);
  - for the Codex harness login: running `uv run poe host-login codex`, closing with the login note of the same requirement;
  - for an ambient run or the opted-in login: running `claude` and entering `/login`;
  - for a long-lived token: generating a new one with `claude setup-token`.
- **The time limit.** A run still going at its time limit SHALL be stopped as the requirement "Harness-owned host logins" prescribes, and SHALL end as a runner failure naming the limit.
- **A non-zero exit without such an event.** The runner SHALL report the host's stderr.
- **A missing closing event.** A stream with no result event SHALL be a runner failure, never a silent success with empty telemetry. On Codex, the closing event is a completed turn.

The runner's exit status SHALL distinguish four outcomes, so that only a failed verdict reads as a failure of the skill:

- every verdict the run computed passed;
- a verdict failed — L1, or a graded L2 criterion;
- the run is untested, for one of three reasons:
  - the subscription could not serve it. This covers:
    - a harness login refused by its preflight;
    - a login the host rejected;
    - a stream reporting overage use, a refused or unknown rate-limit status, or an API-key source;
    - a stream that reports no rate-limit status at all, so overage cannot be ruled out;
    - a Codex run refused by the plan billing guard, before or after the run;
    - a judge call that produced no grade;
  - its isolation did not hold. This covers:
    - a claude.ai account surface that reached an isolated run (requirement: Isolated measurement environment);
    - a claude.ai connector that reached an ambient run;
    - a foreign skill or an MCP tool call in a Codex run (requirement: Dev-runner host adapters);
  - a Codex run's own preconditions or served settings did not hold. This covers:
    - the run lock not taken within its bounded wait (requirement: Harness-owned host logins);
    - an installed CLI below the pinned minimum, or a feature outside the allowlist that reads enabled, even where the preflight reports them;
    - a requested effort the host did not serve (requirement: Dev-runner host adapters);
- any other runner failure.

A run that is untested because its isolation did not hold SHALL also name in its message any API-key source, overage use, or refused or unknown rate-limit status that its stream shows, so that a surface never hides a billing problem.

The chat the verdicts read SHALL be the closing event's final text and nothing else. On Codex, that is the last completed agent message. All of this logic SHALL be covered by L0 tests against recorded and synthetic event streams:

- the verdicts;
- the event parsing and the telemetry;
- the command the runner builds and the judge command;
- the judge's child environment and the model-under-test child's environment;
- the stream checks that mark a call unavailable, the account-surface checks, and the stop at the first surface;
- the login-failure remedy for each kind of login;
- the login label, and that a refresh is written back only into the labelled login's directory;
- the exit-status mapping;
- the summary it prints.

The telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so that a host field rename fails a test rather than blanking the line. Until a later change records a Codex stream, the Codex readers are pinned against synthetic streams derived from the source of the pinned minimum CLI version, labelled synthetic.

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
- **WHEN** the runner or the routing rig builds the Claude host command
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

#### Scenario: Codex run reports no cost
- **WHEN** a Codex run completes on a model name the roster does not price under OpenAI's provider
- **THEN** the summary carries no cost, labels the run unpriced, reports the uncached input, cached input, output and reasoning token counts and the quota windows before and after, and records the served model as unreported

#### Scenario: Budget cap refused on Codex
- **WHEN** a Codex run is requested with a budget cap
- **THEN** the runner exits with a usage error naming the missing host cap, before staging and before any Codex process starts

#### Scenario: Codex login failure names the Codex remedy
- **WHEN** a Codex run fails with Codex's message that its login has expired or been revoked
- **THEN** the runner failure carries Codex's reason, names `uv run poe host-login codex` as the one remedy and closes with the login note, and the run exits with the untested status

#### Scenario: Codex precondition is untested, not a runner failure
- **WHEN** a Codex run is refused because the run lock stayed held past its wait, a feature outside the allowlist reads enabled, or the host served an effort other than the one requested
- **THEN** the run exits with the untested status, not the runner-failure status, and its summary names the precondition that did not hold

#### Scenario: Codex helper spawn counted
- **WHEN** a Codex supervise run's stream shows one subagent spawn whose prompt carries the verifier brief
- **THEN** the helper-call list reports one `Agent` call, the single-context verdict passes, and the verifier part of the L1 verdict passes

#### Scenario: MCP tool call in a Codex run
- **WHEN** a Codex run's stream shows an MCP tool call
- **THEN** the run exits with the untested status, names the server and the tool, and no verdict is computed

#### Scenario: No completed turn on Codex
- **WHEN** Codex exits without emitting a completed turn
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

### Requirement: Subscription text roles (dev runner)

The dev runner's text-only role, its rubric judge, SHALL run through the unmodified official Claude host CLI under the operator's subscription login, whichever host ran the model under test. The judge SHALL be one single-turn text call per rubric criterion, issued under the following constraints.

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
- **Where judging runs.** Judging SHALL run in an isolated Claude configuration, inside which the linked login is kept current.
  - For a Claude run in isolated mode, that is the run's own configuration.
  - For a run on another host, the runner SHALL prepare a fresh isolated Claude configuration for the judge after the model run has ended. The Claude dev judge therefore grades the runs of every non-Claude host, Codex among them.
  - The judge SHALL never run in another host's login home, and SHALL never receive another host's login or environment.
  - A Claude run in the ambient configuration SHALL NOT be judged.
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
- Kept dev-runner workspaces SHALL be re-gradable without re-running the model under test, whichever host produced them.

**Smoke:**

- The registered smoke task SHALL run the core scenarios on the dev runner's Claude host in isolated mode, loading no key file. Its spend SHALL be kept off metered billing in three ways:
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
- **WHEN** judging is requested for a Claude run in the ambient configuration
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

#### Scenario: Codex run graded by the Claude judge
- **WHEN** a Codex run with judging completes
- **THEN** the judge's calls run in a fresh isolated Claude configuration linked to the Claude harness login, prepared after the Codex child has exited. The Codex home and the Codex login appear in none of the judge's arguments or environment, and the grades carry the not-comparable label

#### Scenario: Codex workspace re-graded
- **WHEN** a kept workspace of a Codex run is re-graded on the Codex host
- **THEN** the served model is read with the Codex reader, the dev judge grades the produced artifact in a fresh isolated Claude configuration, and no Codex process is started
