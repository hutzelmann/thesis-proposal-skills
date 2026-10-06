# Spec Delta

## ADDED Requirements

### Requirement: Copilot plan billing guard
A Copilot run SHALL draw only on the included AI credits of the operator's Copilot plan, and nothing else. The account keeps money out: the operator keeps no Copilot budget of any kind, and a budget is deleted rather than set to zero. The checks below are the backstop, and each one fails closed. A run that any of them refuses:

- is untested and exits with the untested status. The one exception is a run whose session record holds no shutdown record, which is a runner failure (requirement: Dev-runner cost and helper-agent telemetry) and still records a billing stop;
- starts no further Copilot process;
- is reported in the one refusal template (requirement: Harness-owned host logins).

**Stops.** Some findings are not settled by the next run's checks. For each of them the runner SHALL record a stop in the harness home, naming the cause and the time. A stop is one of three kinds:

- **A billing stop**, for a finding after a run that shows the run may have drawn more than its bound. The cases are listed under "After every run". Its one remedy is checking the account's billing page and then clearing the stop.
- **An isolation stop**, for a run whose sandbox was ignored or not reported active, or whose output carried the token's value (requirement: Dev-runner host adapters). Its one remedy is reading the run's findings and then clearing the stop.
- **The approval stop**, which the login command records whenever it writes a token file, a reset included. It holds back the first model call after every login until the operator approves it. Its one remedy is clearing the stop, which is that approval.

While a stop is recorded, every later Copilot run SHALL be refused before any Copilot process starts. The refusal names the stop's cause and its remedy. A stop record that cannot be read SHALL count as a recorded billing stop. Only the operator clears a stop, with the login command's clear option or a reset; a reset records a new approval stop. Both carry the login command's terminal and agent-marker refusals (requirement: Harness-owned host logins). A stop SHALL NOT refuse the status command or the preflight-only option (requirement: Dev-runner host adapters), which make no model call; both report it.

**Environment.** These Copilot children are covered: the run, the version check, the status read, the confinement probe, and the skill and MCP listings. Each SHALL receive one final environment. The same function that builds the isolated Claude child's environment builds it from the Copilot record (requirement: Isolated child environment), and the token is added after that function. That requirement's allowlist, configuration-directory variable and account-surface variables govern Claude children only; this requirement prescribes the Copilot child's environment. The one exception is the status command's on-request read without the token (requirement: Harness-owned host logins), whose child receives the same environment less the token variable. It holds:

- only the machine plumbing the allowlist admits, without the Claude long-lived token, plus a dumb terminal type and the no-colour switch;
- the Copilot home variable, set to the harness home;
- the client's package-cache variable, set to a persistent cache directory that the harness owns outside the home;
- the client's auto-update switch, set to off;
- the home directory and the XDG base directories, the runtime directory among them, set to scratch directories belonging to the run or the call;
- the session-bus address, set to a disabled value rather than dropped. The GitHub CLI's bus library falls back to the fixed per-user bus when the variable is empty, and the operator's keyring is reachable there;
- the GitHub CLI's configuration-directory variable, set to an empty directory in the home;
- the token variable, `COPILOT_GITHUB_TOKEN`, read from the token file (requirement: Harness-owned host logins).

Every inherited variable whose name begins with `COPILOT_`, `GITHUB_`, `GH_`, `CAPI_`, `OTEL_`, `OPENAI_`, `ANTHROPIC_` or `AZURE_OPENAI_`, or ends in `_TOKEN` or `_API_KEY`, SHALL be dropped. So SHALL `BASH_ENV` and `SSH_AUTH_SOCK`. The run's summary SHALL name the dropped variables, never their values.

Immediately before starting any Copilot child, the harness SHALL check again the final environment that child will receive, after every variable the harness sets has been applied. It SHALL refuse to start the child in either of these cases:

- the environment carries a variable of the dropped families that the Copilot record does not set itself and that is not the token variable;
- it carries a token-shaped variable other than the token variable. A variable is token-shaped when its name ends in `_TOKEN` or `_API_KEY`, or when its value begins with a GitHub token prefix.

The refusal names the variable, never its value. The reason: an environment token outranks every other credential in the client, so a leaked one would bill, and act, as whichever account owns it. A provider variable would route the run to a third-party key.

**Status read.** The runner SHALL read the account's state through the client's own headless server mode: its current-authentication call and its model listing. Neither makes a model call. It reads the state before every run and again after it, under one hold of the run lock (requirement: Harness-owned host logins).

- It SHALL read the raw quota snapshots the client receives, never the client's mapped quota values, which turn a missing field into "no overage".
- It SHALL choose the snapshot as the client does: the chat snapshot when the access SKU names the free limited plan, otherwise the premium-interactions snapshot.
- It SHALL keep only these values:
  - the auth type and host, and the number of auth errors;
  - the plan, the access SKU, whether billing is token based, and the quota reset date;
  - the chosen snapshot's overage permission, overage count, overage entitlement, remaining percentage, and has-quota and unlimited flags;
  - each listed model's identifier, policy state and supported efforts.
- The raw reply SHALL never be stored or logged, a refusal for a runner bug included, because it carries the token, the login and the organization list.

Before the run, the runner SHALL refuse in any of these cases:

- **The read is unavailable.** The reader cannot start, its handshake or a call fails, it gives no answer within a bounded time, or the answer carries no Copilot user record or no chosen snapshot. Remedy: report it, because the client's server interface does not match the pinned version.
- **A budget is possible.** The overage permission is missing, is not a boolean, or is true; or the overage entitlement is missing, is not a number, or is above zero. Remedy: delete the Copilot budget, or, on an organization seat, ask its administrator.
- **Overage already drawn.** The overage count is missing or above zero. Remedy: check the account's billing page, and rerun after the reset date.
- **Legacy billing.** Billing is not token based. A legacy plan reports no consumption in credits, which would leave the credit cap unenforced. Remedy: report it.
- **Quota low.** The remaining percentage is missing or below 10, or the snapshot reports no quota. Remedy: rerun after the reset date.

The runner SHALL keep the last status snapshot in the harness home. It holds only the plan class, whether billing is token based, the chosen snapshot's overage and remaining values, the reset date, and any stop.

**Per-run bound.**

- Every Copilot run SHALL carry the client's AI-credit cap, which the operator names on the command line, at 30 credits or more. A run without it, or with less, SHALL be refused with a usage error before staging.
- The cap is soft: one model call can overshoot it. It is therefore not the hard per-run cap that a smoke task requires (requirement: Dev-runner host adapters).

**After every run.** The runner SHALL read the run's consumption, in credits, from the session's shutdown record, and it SHALL read the status again. The run SHALL be untested, and the runner SHALL record a billing stop, in any of these cases:

- the overage count grew, or appeared, between the two reads;
- the status read after the run is unavailable, so overage growth cannot be ruled out;
- the shutdown record carries no readable consumption;
- the run consumed more than twice its cap;
- the shutdown record reports zero consumption while the per-model usage reports tokens;
- the stream reports that the session limit or the credit cap was reached.

A check after the run that does not complete SHALL record a billing stop as well, after the token's value has been scrubbed from the workspace.

A session record that holds no shutdown record leaves the consumption unreadable. Such a run SHALL be a runner failure rather than untested (requirement: Dev-runner cost and helper-agent telemetry), and the runner SHALL record a billing stop for it as well.

A quota or rate-limit error SHALL make the run untested as a limit reached, not a result. The two reads compare overage only, never consumption, because the operator's other Copilot clients draw on the same pool outside the lock.

The summary SHALL report the overage count and the remaining percentage before and after the run, the cap, and the credits consumed.

**Never in CI.** No CI workflow SHALL use a Copilot token.

**L0 coverage.** L0 tests SHALL cover every check above. They run over event streams and status replies derived from the package of the pinned CLI version. Until a later change replaces them with reduced recordings, the fixture directory SHALL label each of these files synthetic and name the version and the source it follows.

#### Scenario: Token variables in the launching environment
- **WHEN** a Copilot run is started from an environment carrying `GH_TOKEN`, `GITHUB_TOKEN`, an exported `COPILOT_GITHUB_TOKEN` and `COPILOT_PROVIDER_BASE_URL`
- **THEN** no Copilot child receives any of the inherited values. The only token variable a child carries is `COPILOT_GITHUB_TOKEN` read from the home's token file. The summary names the dropped variables, and no value appears in any output

#### Scenario: Leaked GitHub token stopped before the spawn
- **WHEN** the environment builder is replaced by one that returns `GH_TOKEN`
- **THEN** the harness refuses before starting any Copilot process, names the variable but not its value, and the run is untested

#### Scenario: Only the record's own names are exempt
- **WHEN** the final child environment carries the variables the Copilot record sets and the token variable, and in a second case also carries `COPILOT_PROVIDER_BASE_URL` or a second variable whose value begins with a GitHub token prefix
- **THEN** the first child starts, and the second is refused before any Copilot process starts, naming the variable but not its value

#### Scenario: Status read unavailable
- **WHEN** the status read fails its handshake, does not answer in time, or answers without a Copilot user record
- **THEN** the run is refused as untested, and no Copilot run starts

#### Scenario: Missing overage field refuses
- **WHEN** the chosen snapshot carries no overage permission, a case that the client's mapped value would report as "no overage"
- **THEN** the run is refused as untested because a budget cannot be ruled out, and no Copilot run starts

#### Scenario: Budget present
- **WHEN** the chosen snapshot reports the overage permission as true, or an overage entitlement above zero
- **THEN** the run is refused as untested, and the message names deleting the Copilot budget as the one remedy

#### Scenario: Missing entitlement field refuses
- **WHEN** the chosen snapshot carries no overage entitlement, or one that is not a number
- **THEN** the run is refused as untested because a budget cannot be ruled out, and no Copilot run starts

#### Scenario: Overage already drawn
- **WHEN** the chosen snapshot reports an overage count above zero
- **THEN** the run is refused as untested, and the message names the reset date

#### Scenario: Legacy billing refused
- **WHEN** the status read reports billing that is not token based
- **THEN** the run is refused as untested, and the message says that consumption in credits cannot be read

#### Scenario: Snapshot chosen as the client chooses it
- **WHEN** the access SKU names the free limited plan, and in a second case names another plan
- **THEN** the guard reads the chat snapshot in the first case and the premium-interactions snapshot in the second

#### Scenario: Quota low
- **WHEN** the chosen snapshot reports 8 % remaining
- **THEN** the run is refused as untested, and the message names the reset date

#### Scenario: Credit cap required
- **WHEN** a Copilot run is requested without a credit cap, or with a cap of 20
- **THEN** the runner exits with a usage error before staging, and no Copilot process is started

#### Scenario: Soft cap reached records a stop
- **WHEN** a run's stream reports that its credit cap was exhausted
- **THEN** the run is untested as a limit reached, not a result, and a billing stop naming the cap is recorded in the harness home

#### Scenario: Overage grew during a run
- **WHEN** the status read after a run reports a higher overage count than the read before it
- **THEN** the run is untested, the message names the overage, and a billing stop is recorded

#### Scenario: Consumption out of bounds
- **WHEN** a run's shutdown record reports more than twice its cap, or zero consumption while its per-model usage reports tokens
- **THEN** the run is untested, the message names the consumption and the cap, and a billing stop is recorded

#### Scenario: Status read after the run unavailable
- **WHEN** the status read after a run fails its handshake or does not answer in time
- **THEN** the run is untested, the message says that overage growth cannot be ruled out, and a billing stop is recorded

#### Scenario: Recorded stop refuses later runs
- **WHEN** a Copilot run starts while a billing stop is recorded in the harness home
- **THEN** the run is refused as untested before any Copilot process starts. The message names the stop's cause, and its one remedy is checking the account's billing page and then clearing the stop with the login command

#### Scenario: First run after a login waits for approval
- **WHEN** the login command writes a token file, and a Copilot run is then started without the stop having been cleared
- **THEN** the run is refused before any Copilot process starts, naming the approval stop and its one remedy, clearing the stop with the login command's clear option. The status command and the preflight-only option still run and report the stop

#### Scenario: Only the operator clears a stop
- **WHEN** the login command's clear option is started with a standard input that is not a terminal, or from an environment that carries an agent-session marker
- **THEN** it refuses, and the stop stays recorded. Run from a terminal outside an agent session, it removes the stop and changes nothing else in the home

#### Scenario: Status snapshot holds no secret
- **WHEN** a run completes
- **THEN** the harness home's status snapshot holds the plan class, the billing flag, the overage and remaining values, the reset date and any stop, and no token, login name or organization

#### Scenario: Synthetic Copilot fixtures labelled
- **WHEN** the Copilot stream and status-reply fixtures are read
- **THEN** the directory's README lists each file as synthetic, together with the CLI version and the source it follows

## MODIFIED Requirements

### Requirement: Harness-owned host logins
The harness SHALL keep its own login for each host client it drives, in a login home it owns. No harness action may then share a refresh token with, write to, or log out the operator's own logins of that client: neither the CLI nor a desktop app or editor integration. This requirement covers Claude, Codex and GitHub Copilot. A client added later gets its own home under the same rules.

**Credential kinds.** Each client's record SHALL name the kind of credential its harness login is:

- **Client login** (Claude, Codex): the client's own subscription login, run inside the home. A refreshed Claude login reaches the home through the harness write-back (requirement: Isolated measurement environment); Codex keeps its own login current there.
- **Token file** (Copilot): a fine-grained personal access token. The operator creates it on GitHub with the "Copilot Requests" permission and no other, and with an expiry date. The login command stores it in one file, the token file. That file lies beside the home under the harness state directory, never inside the home, so that no access the client grants its sandbox to its own home can cover it.

For a token-file record, the harness SHALL:

- read exactly one credential, the token file, and no other credential store;
- hand its value only to that client's children, under the one variable the record names, and never on a command line;
- inspect only its prefix, and otherwise use the value only to scrub it, as the next item says;
- before it saves, prints or forwards anything a child of that client produced (its standard error, a runner-failure message, the saved events, the judge's input), replace every occurrence of the value. An occurrence SHALL make the run untested for isolation and record an isolation stop (requirement: Copilot plan billing guard);
- never print, log or copy it, and never write it anywhere but the token file. Only the login command writes that file, with owner-only permissions.

**Location.**

- The home SHALL lie under a per-user state directory for the harness, following the platform's convention:
  - Linux: the XDG state directory;
  - macOS: Application Support;
  - Windows: the local application-data directory.
- Its path SHALL be absolute, its permissions owner-only, and it SHALL lie outside the repository.
- It SHALL never equal, contain, or lie inside the operator's own configuration directory of any client. For Copilot, those are `~/.copilot`, the directory an inherited `COPILOT_HOME` names, and `~/.config/github-copilot`.
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
- Before the first login, the Copilot home SHALL be seeded with a pinned settings file and an empty GitHub CLI configuration directory.
  - The settings turn off auto-update, the switch to automatic model selection, hooks, memory, editor auto-connect and experimental features, and they keep custom agents local.
  - They keep any token the client stores in a file in the home rather than in the OS keyring.
  - They pin the OS sandbox: enabled, no bypass, no git or GitHub CLI credentials inside it, and no developer-tool grants.
  - Its deny list is built by construction, not picked entry by entry. It names, by their real paths, the operator's whole home directory, the per-user runtime directory that holds the session bus and the agent sockets, the harness state directory where it lies outside that home, and the token file. Those paths are resolved from the account's entry in the password database, never from a child's scratch home. The workspace and the scratch home lie outside all of them (requirement: Dev-runner host adapters).

**Commands.**

- **Login.**
  - For a client-login record, it SHALL run the client's own subscription login inside the home, never a console or API-billing login: for Codex, never an API-key login or an access-token login. For Codex, it MAY use the client's device-code login.
  - For the token-file record, it SHALL run no client login. It SHALL:
    1. read the token from the terminal without echoing it;
    2. before writing anything, refuse a token whose prefix is not the fine-grained token's prefix, a classic token included;
    3. write the token file, and record the approval stop (requirement: Copilot plan billing guard);
    4. run the status read (requirement: Copilot plan billing guard). The login reports ready only when that read passes the preflight, the approval stop it has just recorded apart.
  - Only the operator runs it, never an agent. It SHALL refuse when its standard input is not a terminal. It SHALL also refuse when its environment carries a marker of an agent session: a variable that a Claude Code session, or a Codex or Copilot shell, exports to the commands it runs. The refusal names the marker variables, never their values. Both refusals are speed bumps, not guards: an agent with a terminal tool has a terminal, and a marker can be unset. The rule that agents never log in is the guard.
  - For a client-login record, its environment, the login environment, is the operator's own, so that a browser can open. Every billing variable and every host-session variable of that client is removed, and the configuration directory is set to the home. For Claude, the profile directory is also set to the home's empty one. A token-file login opens no browser. Its status read runs in that client's child environment (requirement: Copilot plan billing guard).
  - On a home that already holds a login, it SHALL first log out of that login in the home. Where the login is no file in the home, the host's own status decides whether the home holds one. For a token file, logging out means deleting the file.
  - If that logout fails, the login SHALL stop, naming the logout's exit status, and neither log in nor wipe: replacing a login whose logout did not go through could orphan a live grant.
  - For Copilot, a clear option SHALL instead remove a recorded stop of any kind (requirement: Copilot plan billing guard), holding the run lock, and change nothing else. It carries the same terminal and agent-marker refusals. Clearing the approval stop is the operator's approval of the next model call.
- **Reset.** A reset option SHALL log out, wipe the marked home, seed it again and log in. A failed logout stops a reset as it stops a login.
- **Logout.**
  - A logout command SHALL run the client's own logout in the home and nowhere else.
  - For the token-file record, the logout SHALL instead delete the token file and nothing else, run no client logout, and name the page where the operator revokes the token.
  - Every logout of a client-login record SHALL run in the login environment: the logout command's own, the one before a login, and the one in a reset. No inherited token, profile directory or configuration directory can then steer it at another login.
  - Live check L3 shows whether the harness logout leaves the operator's other Claude sessions working. Live check X8 shows the same for Codex, whose logout revokes the home's refresh token, and whose login revokes the previous one held in the home. Until a client's check has passed, the logout command, a reset and a login over an existing login of that client SHALL say, before they log out, that this is unverified. A token-file login and logout touch only the token file, so no such check applies to them, and their messages carry no such caveat.
- **Status.**
  - It SHALL make no model call.
  - It SHALL print only:
    - the home's path;
    - whether the home carries its marker;
    - whether the home is logged in; for Copilot, whether the token file is present;
    - the auth method and, for Claude, the API provider; for Copilot, the auth type the status read reports, and whether the host is GitHub's public host;
    - for Claude, whether the host reports the home as its configuration directory;
    - whether the home is clean, naming any offending entry; for Codex, also whether its configuration equals the pinned one; for Copilot, also whether its settings equal the pinned ones;
    - for Claude, how long the access token remains valid; for Codex, how long ago its stored login was last written, by login or refresh;
    - for Codex, the installed CLI version against the pinned minimum, and whether the feature allowlist holds;
    - for Copilot, the installed CLI version against the pinned version, and whether the OS sandbox is available;
    - for Codex, the last quota snapshot the home keeps and, only on request, a fresh plan quota from the client's rate-limit read;
    - for Copilot, from the status read: the plan class, whether billing is token based, the chosen snapshot's overage permission, overage count, overage entitlement and remaining percentage, and the reset date;
    - for Copilot, whether a stop is recorded, and its kind and cause;
    - for Copilot, only on request, either of two more reads:
      - the model listing, giving each model's identifier, policy state and supported efforts;
      - whether the client reports a login when the token is withheld;
    - which login runs would use.
  - It SHALL never print a credential value, any part of an API key or token, an email address, a login name or an organization.
  - The Claude status check SHALL run without the long-lived token, so that it reports the home's own login even when a token is exported.
  - Agents MAY run it.
- **Default profile directory.** Whether the Claude host ignores the default Anthropic profile directory when the profile directory is set to the home's empty one is unverified. No Claude login, logout or status check SHALL therefore start a client while the default profile directory holds an entry or cannot be listed, whether or not a long-lived token is exported: none of them carries the token. The refusal names that directory, never its contents, and its remedy is to move the profiles aside. A Codex or Copilot client reads no Anthropic profile, so its commands are not held to this rule.
- **Locking.** Logout, reset, and a login over an existing login SHALL hold, while they log out and wipe, the lock the client's runs take: for Claude, the same refresh claim that isolated runs take; for Codex and Copilot, the run lock. None of them may then interleave with a run that is writing a refreshed login back or running in the home.
- **Run lock (Codex and Copilot).**
  - Runs of each of these clients SHALL execute one at a time per home.
  - Each of these SHALL hold an exclusive lock on a file in the home:
    - each run;
    - the reads around it: Codex's quota read before the run, and Copilot's status reads before and after it, which one hold covers together with the run;
    - every login, logout and reset;
    - every status command that reads the account: for Codex, a status command asked for a fresh plan quota; for Copilot, every status command, because each one runs the status read.
  - The running child SHALL hold that lock for as long as it lives, even when the harness process is killed. On Linux, the child SHALL also be signalled when the harness process dies.
  - A run that cannot take the lock within a bounded wait SHALL be refused as untested.

**Preflight.** The harness SHALL confirm the conditions below without a model call. For Claude, it does so before any isolated configuration links the harness login. For Codex and Copilot, it does so before any run. If one fails, it SHALL refuse the run as untested and start no host process for it. It SHALL never fall back to the operator's own login. Each failing condition names one remedy.

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

For Copilot:

- **The installed CLI is not the pinned version.** The version is read with auto-update off. Remedy: install the pinned version through the package manager, or bump the pin in a change of its own.
- **The home is missing, or has wider permissions than owner-only.** Remedy: `uv run poe host-login copilot`.
- **A directory at the home's path lacks the marker.** The harness did not create it and does not adopt it. Remedy: move it aside, then run `uv run poe host-login copilot`.
- **The token file is missing or empty.** Remedy: `uv run poe host-login copilot`.
- **The token's prefix is not the fine-grained token's prefix.** Remedy: create a fine-grained token that carries only Copilot Requests, then run `uv run poe host-login copilot --reset`.
- **The status read reports auth errors, or no login.** The token was rejected, has expired or was revoked. Remedy: the same as for the prefix.
- **The status read reports an auth type other than the environment token.** Remedy: report it, because another credential reached the client.
- **The status read reports a host other than GitHub's public host.** Remedy: report it.
- **A stop is recorded** (requirement: Copilot plan billing guard). Remedy, by its kind: for a billing stop, check the account's billing page, then run `uv run poe host-login copilot --clear-stop`; for an isolation stop, read the run's findings, then run the same command; for the approval stop, run that command to approve the next run.
- **The home is not clean.** Any of these makes it unclean:
  - its settings differ from the pinned ones in any key;
  - the client's own state file carries a top-level key outside the managed-state set fixed at the pinned version;
  - it holds any entry outside the allow-list. The allow-list is: the settings and state files, the session store, an empty session-state directory, the empty GitHub CLI configuration directory, the marker, the run lock and the status snapshot.

  Remedy: remove the named entry, or run `uv run poe host-login copilot --reset`.

Every refusal message SHALL follow one template:

- the word untested;
- the cause;
- exactly one remedy;
- the login note.

It SHALL carry no credential value, email address or organization.

The login note is the sentence that the operator's own login of that client is not affected. While a client's revocation check has not passed (L3 for Claude, X8 for Codex), a message whose remedy is that client's harness login command, with or without its reset option, SHALL carry in its place the sentence that whether that command logs out the operator's other sessions of that client is unverified. The runners' login-failure messages for a harness login close with the same note (requirement: Dev-runner cost and helper-agent telemetry). A token-file client has no revocation check, because its login and logout touch only the token file. Its note is always the not-affected sentence.

A long-lived Claude token in the environment SHALL bypass the Claude harness login entirely. The preflight is not run, and nothing is linked (requirement: Isolated measurement environment).

**Credentials.**

- The harness SHALL read no field of a stored Claude login other than its expiry.
- It SHALL never open a stored Codex login. The time of its last write is read from the file's modification time.
- It SHALL print or log no credential value.
- It SHALL write Claude credentials only through the write-back that the requirement "Isolated measurement environment" prescribes.
- It SHALL never write a Codex login. The client keeps that login current in its home.
- For Copilot, it SHALL keep the limits of a token-file record (Credential kinds). It SHALL never read, write or delete the client's own stored logins: the OS keyring, the operator's Copilot configuration directories and the GitHub CLI's configuration.

**Stopping a host child.** This applies whenever the harness stops a host child it started:

- a dev run at its time limit;
- a judge call at its time limit;
- a routing case after its route, or at its limit;
- the harness login's status check and logout at their limit;
- the advisory audit pre-flight's call at its limit, which runs on the operator's own login;
- a Codex run at its time limit, and a Codex quota read at its limit;
- a Copilot run at its time limit, and a Copilot status read or listing at its limit.

The harness SHALL first send the client's own stop request: a termination request to Claude and to Copilot, and an interrupt to Codex, which ends the turn. It SHALL kill the child only if the child has not exited after a bounded grace, so that a host part-way through writing a refreshed login can finish. On a platform whose termination request is itself a kill, the kill is the request.

#### Scenario: Default home location
- **WHEN** the harness resolves the homes on Linux with no override and no XDG state directory set
- **THEN** the Claude home is `~/.local/state/thesis-proposal-dev/hosts/claude`, the Codex home is `~/.local/state/thesis-proposal-dev/hosts/codex`, and the Copilot home is `~/.local/state/thesis-proposal-dev/hosts/copilot`. Each has owner-only permissions once created and carries the marker, and none is `~/.claude`, `~/.codex` or `~/.copilot`

#### Scenario: Override overlapping the operator's configuration
- **WHEN** the state-directory override equals the user's home directory, lies inside `~/.claude`, `~/.codex`, `~/.copilot` or `~/.config/github-copilot`, or contains the configuration directory named by `CLAUDE_CONFIG_DIR`, `CODEX_HOME` or `COPILOT_HOME`
- **THEN** every host-login command and every isolated, Codex or Copilot run refuses, naming the override, and nothing is created

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
- **THEN** every host-login command and every isolated, Codex or Copilot run refuses, naming the override, and nothing is created

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

#### Scenario: Copilot settings seeded before the token is read
- **WHEN** the login command creates a Copilot home
- **THEN** the home's settings equal the pinned ones before the token prompt appears. That includes the sandbox block, whose deny list names the operator's real home directory and per-user runtime directory rather than paths under a scratch home. The home's GitHub CLI configuration directory exists and is empty

#### Scenario: Token stored only in the token file
- **WHEN** the operator enters a fine-grained token at the Copilot login's prompt
- **THEN** the token file, beside the home and not inside it, holds it with owner-only permissions, the approval stop is recorded, and no client login runs. The OS keyring and the operator's Copilot and GitHub CLI configuration are unchanged, and the token appears in no output

#### Scenario: Token value scrubbed from a child's output
- **WHEN** a Copilot child's standard error or events carry the synthetic token's value
- **THEN** the value appears in no saved event, printed message or judge input, the run is untested for isolation, and an isolation stop is recorded

#### Scenario: Classic token refused
- **WHEN** the token entered at the Copilot login's prompt begins with the classic token prefix, or with any prefix other than the fine-grained one
- **THEN** the login refuses before writing anything. The message names the kind of token required, and no part of the entered value appears in it

#### Scenario: Copilot logout deletes only the token file
- **WHEN** the Copilot logout command runs
- **THEN** the token file is deleted and no client logout runs. The operator's keyring and configuration are untouched. The message names the page where the token is revoked and carries no unverified-logout caveat

#### Scenario: Copilot status reveals no account details
- **WHEN** the status command runs against a Copilot home whose status reply carries a login name, an organization list and a token
- **THEN** its output carries none of them, no model call is made, and the raw reply is not stored

#### Scenario: Copilot token rejected
- **WHEN** the status read before a Copilot run reports an auth error
- **THEN** the run is refused as untested. The message names creating a fine-grained token that carries only Copilot Requests and running `uv run poe host-login copilot --reset`, and it closes with the sentence that the operator's own Copilot login is not affected

#### Scenario: Wrong auth source on Copilot
- **WHEN** the status read reports an auth type other than the environment token, for example a stored login or the GitHub CLI's login
- **THEN** the run is refused as untested, the message names the auth type, and no Copilot run starts

#### Scenario: Copilot CLI not the pinned version
- **WHEN** the installed Copilot CLI reports a version other than the pinned one, older or newer
- **THEN** the run is refused as untested, and the message names both versions

#### Scenario: Copilot home not clean
- **WHEN** a Copilot run starts while the home's settings differ from the pinned ones in a key, the client's state file carries a key outside the managed-state set, or the home holds a custom-instructions file
- **THEN** the run is refused as untested, and the message names the key or the entry and the reset remedy

#### Scenario: Copilot reads and run under one hold
- **WHEN** a Copilot run starts
- **THEN** the status read before it, the run and the status read after it all happen under one hold of the run lock. A second Copilot run, login or reset started meanwhile waits a bounded time and is then refused as untested, naming the held lock

### Requirement: Dev-runner host adapters
The dev runner SHALL drive the model under test on one of its host CLIs, selected per invocation. Its hosts are:

- Claude Code, the default;
- Codex, under the operator's ChatGPT plan;
- GitHub Copilot CLI, under the operator's Copilot plan.

An invocation that selects no host SHALL keep every behaviour of the Claude runner as it was before this requirement, with two additions: its summary records the host and the host's label, and a summary-log path inside the directory the support report reads is refused (requirement: Inverted-hybrid runners). No host but Claude has an ambient mode. Every Codex run executes in the Codex harness home, and every Copilot run in the Copilot harness home (requirement: Harness-owned host logins).

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

The tool events of a Copilot stream SHALL be read as follows:

- a call of a shell tool as `Bash`;
- a file creation, edit or patch as `Edit`;
- a file view as `Read`. A view of the `SKILL.md` of a `proposal-*` skill is also flagged as a skill-file read, but is not a `Skill` call;
- a file-pattern search as `Glob`, and a content search as `Grep`;
- a call of the client's skill tool as a `Skill` call naming the requested skill, without a plugin prefix. A call whose completion reports failure is an attempt, not an invocation;
- a call of the client's task tool as `Agent`, carrying its prompt;
- a web fetch as `WebFetch`, and a web search as `WebSearch`;
- an MCP tool call as `mcp__<server>__<tool>`.

The client's internal bookkeeping tools are not tool calls. A tool name that is neither offered to the run nor one of those internal tools SHALL make the run untested.

**The model on Codex.**

- A Codex run SHALL require the model on the command line and pass it on unchanged. It SHALL refuse a provider-qualified identifier before staging.
- The registry SHALL hold no Codex role, the runner SHALL supply no default model, and the model-currency check SHALL raise no alert for Codex.
- A reasoning effort MAY be requested, from the host's explicit levels, but never the level that hands work to subagents.
- The effort the host served SHALL be recorded. A requested effort that the host did not serve SHALL make the run untested.

**The model on Copilot.**

- A Copilot run SHALL require the model on the command line and pass it on unchanged. Before staging, it SHALL refuse a provider-qualified identifier and the client's automatic model selection.
- The registry SHALL hold no Copilot role, the runner SHALL supply no default model, and the model-currency check SHALL raise no alert for Copilot.
- Before the run, the run SHALL be refused as untested when the client's model listing does not offer the model, or offers it under a policy other than enabled. Remedy: enable the model in the account's Copilot settings, or name another model.
- A reasoning effort MAY be requested, but only one that the listing reports for the model. Any other is refused before the run.
- The run SHALL be untested, naming both models, in any of these cases:
  - a top-level message was served by a model other than the requested one;
  - the session reports usage by another model in a scenario without a helper allowance;
  - the client switched the model because of a rate limit.
- The summary SHALL record as the served model the models the top-level messages and the per-model usage name, or "unreported" when they name none. The session's record of its creation options SHALL never count as evidence of the served model or effort.
- A requested effort that the client reports as left unapplied SHALL make the run untested. Until a recorded run pins the event that reports it, the summary SHALL say that the effort was requested and not verified.

**Invocation on Codex.** A Codex run SHALL:

- run the host's non-interactive mode with its JSON event stream, the prompt on standard input, and the workspace as its working root. The workspace lies outside any git repository;
- validate its configuration strictly, so that an unknown configuration key fails the run rather than being ignored;
- sandbox the run to the workspace. Network access is granted only to scenarios that need it: those whose skill or sibling skills include import, literature search or reverse, and those that serve a fixture over localhost;
- enable subagents only for scenarios that declare a helper allowance;
- disable every other host feature that is on by default, through the host's validated feature switch. Before the run, it SHALL refuse when the host's feature listing still shows a feature enabled outside that allowlist;
- keep the host's session record while the run lasts, read it after the run, and then delete it.

**Invocation on Copilot.** A Copilot run SHALL:

- run the client's prompt mode with its JSON event stream, streaming off and colour off. It starts a new session under an identifier the harness chooses, for which no session folder may already exist in the home. The workspace is the working directory and lies outside any git repository;
- carry the client's AI-credit cap (requirement: Copilot plan billing guard) and the flag that runs its shell in the OS sandbox;
- offer only an allowlisted tool set, chosen per scenario:
  - every run gets the shell, file, search and skill tools and the client's internal bookkeeping tools;
  - the task and agent tools are offered only to scenarios that declare a helper allowance;
  - the web-fetch tool is offered only to scenarios that need the network, the same scenarios the Codex invocation grants network access. It comes with a URL approval for each host the scenario needs: a served fixture's local host, and the hosts its skills' scripts contact. No run approves every URL;
- approve every offered tool without prompting, and deny memory, the built-in GitHub MCP server, the GitHub CLI in the shell, and `git push`;
- disable, from the command line:
  - the built-in MCP servers, custom instructions and questions to the user;
  - remote sessions and their export;
  - login from stored or GitHub CLI credentials;
  - auto-update, the shell's start-up file and the temporary-directory grant;
- mark the token variable as a secret, and write its logs to a scratch directory that is never saved;
- never pass an extra directory, a plugin directory, approval of every path, memory, sharing, a custom agent, or a resume or continue option;
- after the run, read the session's event file in the home, and then delete the session's folder.

**Isolation on Codex.** A Codex run SHALL see only the skills under test, installed in the workspace where Codex discovers repository skills. Its home directory and XDG base directories SHALL be scratch directories belonging to the run, so the operator's user-scope skills, shell start-up files and key files are not visible to it. After the run, it SHALL count as untested in either of these cases:

- its session record lists a skill outside the workspace's skill directory, or shows a call of the host's cloud-skill tools;
- its stream shows an MCP tool call. The home configures no MCP server, so any call is foreign.

**Isolation on Copilot.** A Copilot run SHALL see only the skills under test, installed under `<ws>/.agents/skills/`. That is the project skill directory a student's folder install writes, where the client lists the skills as project skills. Its home directory and XDG base directories SHALL be scratch directories belonging to the run. Before the run, and without a model call, it SHALL be refused as untested in any of these cases:

- the workspace lies inside the operator's home directory or inside the repository;
- the workspace, or any of its parent directories up to the filesystem root, holds a skill directory other than the staged one, or an instruction, agent, rule, hook, MCP or client settings file that the client reads;
- a machine-wide managed settings file of the client exists;
- the client's skill listing, taken in the run's environment and working directory, names anything other than the staged skills and the client's bundled skills;
- the client's MCP listing names a server outside the built-in names pinned for the CLI version, or one whose source is not built-in.

After the run, it SHALL count as untested in any of these cases:

- its stream carries no loaded-skills report, or a report that differs from the listing. Until a recorded stream shows whether that report reaches the stream, its absence counts;
- a skill invocation in its session record names a source other than the workspace's project skills or the client's bundled skills, or a file outside the workspace's skill directory;
- its stream shows an MCP tool call, or reports an MCP server as connected;
- its session record shows a hook event.

**Sandbox on Copilot.** Only the client's OS sandbox confines the model's shell. A Copilot run SHALL therefore run under it, with the home's pinned sandbox settings (requirement: Harness-owned host logins). When the sandbox cannot start, earlier client versions only warned that it was ignored and ran the shell unconfined, and the pinned version warns and fails sandboxed commands; no personal setting turns either into a refusal, so the runner checks confinement before the run as well as after it. The runner SHALL:

- refuse to start on Windows with a usage error, because the sandbox cannot enforce its deny list there;
- refuse the run as untested when any tool the platform's sandbox needs, as the pinned package names them, is not installed. Remedy: install the named tool;
- before every run, and without a model call, run a confinement probe in a session that carries the run's sandbox settings. Its commands are fixed in the harness; each discards its own output and reports only whether its target was denied or readable, or its exit code. The run SHALL be refused as untested for isolation when the probe can read the token file, the environment of the client process or of the harness's own process, the operator's GitHub CLI configuration or SSH directory, or can obtain the GitHub CLI's token through the per-user session bus or git's stored credentials for GitHub. It SHALL be refused as untested for a precondition when the probe cannot run the skills' interpreter in the workspace, because the deny list would then fail the skill rather than confine it;
- count the run as untested for isolation, and record an isolation stop (requirement: Copilot plan billing guard), when its stream or session record carries the client's warning that the sandbox was ignored, or lacks the client's report that the sandbox is active. Until a recorded run confirms which event reports it, the runner uses the event the pinned package's source names.

Limiting the sandboxed shell's network per scenario is not part of this requirement.

**Scope.**

- The install-prompt scenarios SHALL be refused on every host but Claude, with a usage error.
- No registered smoke task SHALL run on a host that offers no hard budget cap. Codex offers none, and Copilot's credit cap is soft.
- The routing rig stays Claude-only.
- The Codex and Copilot runners SHALL refuse to start on a platform without POSIX file locks.
- No scenario prompt SHALL contain a slash command naming a skill, because Copilot invokes a skill named that way without a tool call.
- On Copilot, a preflight-only option SHALL run every check that comes before the run and print each result. A refusal goes on to the later checks, except one that would make starting them unsafe, which ends the option there: the location, the home, its clean state, the token, the client version, a machine-wide managed policy and the workspace's parent folders. It SHALL start no prompt-mode child and make no model call, and it SHALL refuse, with a usage error, any option it would otherwise ignore.

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

#### Scenario: Effort not served
- **WHEN** a Codex run requested an effort and its session record reports another
- **THEN** the run is untested and names both efforts

#### Scenario: Foreign skill offered
- **WHEN** a Codex session record lists a skill whose file lies outside the workspace's skill directory
- **THEN** the run is untested, names the skill's path, and no verdict is computed

#### Scenario: Install scenario on Codex
- **WHEN** an install-prompt scenario is requested on Codex
- **THEN** the runner exits with a usage error and starts nothing

#### Scenario: Copilot run without a pinned model
- **WHEN** a Copilot run is requested without a model, or with the client's automatic model selection
- **THEN** the runner exits with a usage error before staging, and no Copilot process is started

#### Scenario: Copilot skill staged where a folder install puts it
- **WHEN** a Copilot run stages a scenario
- **THEN** the skill under test and its siblings are installed under `<ws>/.agents/skills/`, and no installed copy contains an eval definition file. The workspace lies outside any git repository, the operator's home directory and the repository. A skill in the operator's `~/.agents/skills` cannot be discovered by the run

#### Scenario: Skill tool call read as Skill
- **WHEN** a Copilot stream shows a call of the skill tool naming `proposal-check`, whose completion succeeds
- **THEN** the tool calls carry a `Skill` call naming `proposal-check`, and the route reader returns it

#### Scenario: Failed skill call is an attempt
- **WHEN** a Copilot stream shows a call of the skill tool whose completion reports failure
- **THEN** the tool calls carry no `Skill` call for it, and the attempt is recorded

#### Scenario: Skill file viewed on Copilot
- **WHEN** a Copilot stream shows a file view of `.agents/skills/proposal-check/SKILL.md`
- **THEN** the tool calls carry a `Read` flagged as a skill-file read, and no `Skill` call

#### Scenario: Copilot subagent spawn
- **WHEN** a Copilot stream shows a call of the task tool in a scenario that allows no helper
- **THEN** the tool calls carry an `Agent` call with its prompt, and the single-context verdict fails naming it

#### Scenario: Copilot tools by scenario
- **WHEN** the command is built for three scenarios: one with no helper allowance and no network need, a supervise scenario, and a scenario that serves a fixture
- **THEN** the first offers neither the task tools nor the web-fetch tool, and the second offers the task tools. The third offers the web-fetch tool, with a URL approval for the fixture's local host only. None approves every URL. Every one of them:
  - denies memory, the GitHub MCP server, the GitHub CLI in the shell and `git push`;
  - disables the built-in MCP servers, custom instructions, remote sessions, login from stored credentials and auto-update;
  - carries the sandbox flag and the credit cap

#### Scenario: Instruction file above the workspace
- **WHEN** a parent directory of the workspace holds an `AGENTS.md` file or a `.agents/skills` directory
- **THEN** the run is refused as untested before any Copilot child starts, and the message names the path

#### Scenario: Skill roster off
- **WHEN** the client's skill listing, in the run's environment and working directory, names a skill beyond the staged skills and the bundled ones
- **THEN** the run is refused as untested, the message names the skill, and no prompt-mode child starts

#### Scenario: Loaded skills unreported
- **WHEN** a Copilot stream carries no loaded-skills report
- **THEN** the run is untested, and the message says that the loaded skills could not be confirmed

#### Scenario: Foreign skill invoked on Copilot
- **WHEN** a Copilot session record shows a skill invocation from a personal or inherited source
- **THEN** the run is untested, names the skill and its source, and no verdict is computed

#### Scenario: MCP server on Copilot
- **WHEN** a Copilot stream reports an MCP server as connected, or shows an MCP tool call
- **THEN** the run is untested, names the server, and no verdict is computed

#### Scenario: Served model differs on Copilot
- **WHEN** a top-level message of a Copilot run reports a model other than the requested one
- **THEN** the run is untested and names both models. In a supervise scenario, by contrast, a helper's usage on another model is reported and does not make the run untested

#### Scenario: Model switched by a rate limit
- **WHEN** a Copilot session record reports a model switch caused by a rate limit
- **THEN** the run is untested and names both models

#### Scenario: Creation options are not evidence
- **WHEN** the session's creation record echoes the requested model and effort, and no message or usage record names a model
- **THEN** the summary records the served model as unreported and the effort as requested and not verified

#### Scenario: Unknown Copilot tool
- **WHEN** a Copilot stream shows a tool name that was neither offered to the run nor is one of the client's internal tools
- **THEN** the run is untested and names the tool

#### Scenario: Sandbox ignored
- **WHEN** a Copilot run's stream carries the client's warning that the sandbox was ignored, or lacks its report that the sandbox is active
- **THEN** the run is untested, the message names the sandbox, and an isolation stop is recorded, so the next run is refused until the operator clears it

#### Scenario: Sandbox tool missing
- **WHEN** a Copilot run starts on Linux while one of the tools the platform's sandbox needs is not installed
- **THEN** the run is refused as untested before any Copilot child starts, and the remedy is installing the named tool

#### Scenario: Confinement probe reaches a credential
- **WHEN** the confinement probe before a Copilot run reports the token file, the client process's or the harness process's environment, the operator's GitHub CLI configuration or SSH directory as readable, or obtains the GitHub CLI's token through the session bus or git's stored credentials for GitHub
- **THEN** the run is refused as untested for isolation before any prompt-mode child starts, the message names the target, and no output of the probe's commands appears in it

#### Scenario: Copilot on Windows
- **WHEN** a Copilot run is requested on Windows
- **THEN** the runner exits with a usage error naming the sandbox, and starts nothing

#### Scenario: Install scenario on Copilot
- **WHEN** an install-prompt scenario is requested on Copilot
- **THEN** the runner exits with a usage error and starts nothing

#### Scenario: Copilot dev run labelled by host
- **WHEN** a dev run on the Copilot host completes
- **THEN** its summary records the host and the label "dev-runner (copilot), not comparable to matrix". No file the support report reads has been written or changed, and no matrix cell takes its result

#### Scenario: Copilot preflight only
- **WHEN** a Copilot run is requested with the preflight-only option
- **THEN** every check that comes before the run runs and is printed, a recorded stop among them, no prompt-mode child starts, and the home holds no new session

### Requirement: Isolated child environment
An isolated Claude host child SHALL receive an environment built from an allowlist. This covers every Claude host child that runs in an isolated configuration:

- every routing-rig run;
- the model-under-test child of every Claude dev-runner run in isolated mode;
- the dev judge's child, together with its login check.

It also covers the Claude harness login's status checks (requirement: Harness-owned host logins). Such a child SHALL NOT receive the launching process's environment with only the configuration directory overridden. One function SHALL build that environment for all of them, so that no second allowlist can drift from the first. The status check alone then drops the long-lived token from it, so that it reports the home's own login rather than the token's.

A host child of a client added later is outside the allowlist, the configuration-directory variable and the account-surface variables of this requirement. The requirement that adds the client prescribes that child's environment, and the same function SHALL build it from that client's own description. That function SHALL read no credential.

Some clients' harness logins are a token file (requirement: Harness-owned host logins). For such a client, the harness SHALL add exactly one variable to what the function returns: the record's token variable, read from the client's token file immediately before that client's child starts, unless the requirement that adds the client runs that child without it. No other child the harness starts SHALL receive that variable, or any value read from the token file. That excludes:

- every Claude child;
- the dev judge's child and its login check;
- another client's child;
- the audit pre-flight's child.

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
- the audit pre-flight's environment;
- the token variable a token-file client's child receives, and its absence from every other child.

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

#### Scenario: Token added after the builder
- **WHEN** the environment of a Copilot child is built while the Copilot token file holds a synthetic token
- **THEN** the function's own output for the Copilot record carries no token. The child's final environment carries exactly one token-shaped variable, `COPILOT_GITHUB_TOKEN`, and its value equals the token file's content

#### Scenario: Token never reaches another child
- **WHEN** a Copilot run with judging completes, and the judge grades it
- **THEN** neither the judge's child nor its login check receives `COPILOT_GITHUB_TOKEN` or the token's value, and neither does any Claude child the invocation starts. The Copilot home and its token file appear in none of the judge's arguments or environment

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output, and SHALL save that stream into the run's workspace, so that a kept workspace carries the run's tool calls and narration for later reading. On Codex, the stream is the JSON event stream together with the records the runner reads from the host's session record, saved in the same file. On Copilot, it is the prompt mode's JSON event stream together with the records the runner reads from the session's event file in the home. Those records are reduced to the fields the readers use and saved in the same file. Beside each run's L1 verdict, the runner SHALL report:

- the model the host served, by the full ID the host reports, beside the name the run requested, and the host CLI version.
  - On Codex, the served model reads "unreported" unless the host reports a reroute, and the CLI version comes from the session record.
  - On Copilot, the served model is read as the requirement "Dev-runner host adapters" prescribes, and the CLI version comes from the session record;
- the run's cost, number of turns and duration.
  - Codex reports no cost. On Codex the cost SHALL be absent, never zero. A notional figure is given only where the registry's roster prices the same model name under OpenAI's provider; otherwise the run is labelled unpriced.
  - Copilot reports AI credits, not money. On Copilot the cost SHALL be absent, never zero. The notional figure SHALL be the credits consumed at one cent each, labelled as notional Copilot credits that were not billed;
- the input and output token counts, with the cache read and cache write counts.
  - On Codex, the input count excludes the cached input, and the reasoning token count is added.
  - On Copilot, the counts come from the per-model usage in the session's shutdown record, and the reasoning token count is added;
- on Codex, each plan quota window's usage before and after the run;
- on Copilot, the overage count and the remaining percentage before and after the run, the credit cap and the credits consumed;
- the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`). A Codex subagent spawn and a Copilot task-tool call are both reported as `Agent`;
- for scenarios that produce a supervise feedback, the feedback body's word count, excluding URLs and the closing note;
- for a run graded by the subscription judge: each rubric criterion's grade, the judge's served model ID, its effort and CLI version, its thinking tokens, and the cumulative notional cost of the judge calls. All of these appear under a label saying the grades are dev-runner L2 and not comparable to the matrix.

A dedicated verdict function SHALL pass when a run spawned no more helper agents than its scenario allows. A scenario allows none unless it declares an allowance, as a supervise scenario does for its single verifier. The verdict SHALL name the spawning calls when the run exceeds the allowance. The runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status.

For the supervise scenarios, the verifier is part of the scored L1 verdict, not only of the advisory probe. A run SHALL fail in either of these cases:

- it spawned no helper whose task carries the skill's verifier brief;
- its review's verification section does not state who verified.

Every host offers a subagent tool to a supervise run. Codex has its subagent feature enabled for scenarios with a helper allowance, and Copilot offers its task tool to them. A run that checks inline has therefore skipped the verifier rather than fallen back.

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

On Copilot, the run's command SHALL deny memory, the built-in GitHub MCP server, the GitHub CLI in the shell and `git push`. It SHALL disable the built-in MCP servers and the remote sessions and their export, and it SHALL never pass a sharing option. The home configures no MCP server. A Copilot run whose stream nevertheless shows an MCP tool call SHALL be untested (requirement: Dev-runner host adapters).

The account's claude.ai MCP connectors publish too. Their tool names depend on the account, so no fixed list can deny them. Instead:

- every Claude run SHALL start with the connector switch off (requirement: Isolated child environment);
- a Claude run in either mode whose stream nevertheless shows an MCP server sourced from claude.ai SHALL be stopped at the event that shows it, as the requirement "Isolated measurement environment" prescribes for a dev run, and SHALL be untested;
- an isolated Claude run SHALL also be held to the wider account-surface check of the requirement "Isolated measurement environment".

The runner SHALL accept a hard budget cap and pass it through to the host, where the host offers one. For a host that offers none, such as Codex, the runner SHALL refuse a budget cap rather than ignore it. A Codex run is bounded instead by its wall-clock limit and by the pre-run quota read (requirement: Codex plan billing guard). Copilot offers only a soft cap, in AI credits. On Copilot, the runner SHALL therefore refuse a budget cap in dollars and require the credit cap instead. That cap bounds the run together with its wall-clock limit and the status reads around it (requirement: Copilot plan billing guard).

The runner SHALL label each run with its host, and as measuring either the ambient host configuration or an isolated one prepared for the run.

- For an isolated Claude run, the label SHALL name the isolated directory and the login it links: the harness login, the operator's login under the explicit opt-in, or a long-lived token. For a linked login, the label SHALL also name that login's directory, which is the one place a refresh is written back. The label SHALL follow how the configuration was prepared, never the link's state after the run: while the host refreshes, its own file stands where the link was until the harness restores it. A run that always isolates, such as the install probe, SHALL be labelled with the login it would have linked when its configuration could not be prepared.
- Every run on a non-Claude host, Codex among them, is isolated. Its label SHALL name that host's harness home and the harness login.

The runner SHALL remove from the Claude model-under-test child's environment every inherited variable that can route the host's billing away from the subscription login, in ambient and isolated mode alike. That means every inherited `ANTHROPIC_`-prefixed variable, which covers the API key, the gateway base URL and its auth token, and every `CLAUDE_CODE_USE_` cloud-provider switch. The child environment of every non-Claude host follows that host's billing-guard requirement: for Codex, the requirement "Codex plan billing guard", and for Copilot, the requirement "Copilot plan billing guard".

- **Ambient mode.** The runner SHALL leave every other inherited variable in place, apart from setting the connector switch to off, so that the operator's effort and session settings remain part of what an ambient run measures.
- **Isolated mode.** The child SHALL receive the isolated child environment instead (requirement: Isolated child environment). Its allowlist admits none of those billing variables and no effort or session setting of the launching process, so that an isolated run measures the default host. The one `ANTHROPIC_`-prefixed variable an isolated child carries is the profile directory, which the harness sets to an empty directory and which routes no billing.

Failures SHALL be reported as follows:

- **An error result.** A host result event marked as an error SHALL end the run as a runner failure; a budget overrun is one such event. On Codex, the equivalent is a failed turn or a fatal error event, and on Copilot a session error event. The message SHALL carry the host's subtype or message, its errors, and the cost and turns so far where the host reports them. The Copilot client's exit code SHALL never decide the outcome on its own, because the client can exit 0 after a failed child task or a failed model call.
- **A failure to authenticate.** When that error is a failure to authenticate, the message SHALL also say that the login the run used is no longer valid, and SHALL name the one remedy for that login:
  - for the Claude harness login: running `uv run poe host-login claude`, closing with the login note (requirement: Harness-owned host logins);
  - for the Codex harness login: running `uv run poe host-login codex`, closing with the login note of the same requirement;
  - for the Copilot harness token: creating a fine-grained token that carries only Copilot Requests, then running `uv run poe host-login copilot --reset`, closing with the login note of the same requirement;
  - for an ambient run or the opted-in login: running `claude` and entering `/login`;
  - for a long-lived token: generating a new one with `claude setup-token`.
- **The time limit.** A run still going at its time limit SHALL be stopped as the requirement "Harness-owned host logins" prescribes, and SHALL end as a runner failure naming the limit.
- **A non-zero exit without such an event.** The runner SHALL report the host's stderr. On Copilot, it reports it only after scrubbing the token's value from it (requirement: Harness-owned host logins).
- **A missing closing event.** A stream with no result event SHALL be a runner failure, never a silent success with empty telemetry. On Codex, the closing event is a completed turn. On Copilot, it is the stream's closing result line. A Copilot run whose session record holds no shutdown record SHALL also be a runner failure, because its consumption cannot be read, and it records a billing stop (requirement: Copilot plan billing guard).

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
    - a Copilot run refused by its plan billing guard, before or after the run, a recorded billing stop included, or ended by a quota, rate, session or credit-cap limit (requirement: Copilot plan billing guard);
    - a judge call that produced no grade;
  - its isolation did not hold. This covers:
    - a claude.ai account surface that reached an isolated run (requirement: Isolated measurement environment);
    - a claude.ai connector that reached an ambient run;
    - a foreign skill or an MCP tool call in a Codex run (requirement: Dev-runner host adapters);
    - in a Copilot run (requirement: Dev-runner host adapters), any of these:
      - a workspace or parent-folder finding, a machine-wide managed settings file, or a skill or MCP listing that differs from what was staged;
      - loaded skills not confirmed, or a foreign skill;
      - an MCP server or tool call, or a hook event;
      - a confinement probe that reached a credential, or a sandbox that was ignored or not reported active;
      - the token's value found in the child's output (requirement: Harness-owned host logins);
      - a recorded isolation stop (requirement: Copilot plan billing guard);
  - a non-Claude run's own preconditions or served settings did not hold. This covers:
    - the run lock not taken within its bounded wait (requirement: Harness-owned host logins);
    - on Codex, an installed CLI below the pinned minimum, or a feature outside the allowlist that reads enabled, even where the preflight reports them;
    - a requested effort the host did not serve (requirement: Dev-runner host adapters);
    - on Copilot (requirement: Dev-runner host adapters), any of these:
      - an installed CLI other than the pinned version, a tool the sandbox needs that is not installed, or a confinement probe that could not run the skills' interpreter;
      - a model the listing does not offer, or offers under a policy other than enabled;
      - a served model other than the requested one, or a model switched because of a rate limit;
      - an effort reported as left unapplied, or an unknown tool name;
      - the approval stop a login records, until the operator clears it (requirement: Copilot plan billing guard);
- any other runner failure.

A run that is untested because its isolation did not hold SHALL also name in its message any API-key source, overage use, or refused or unknown rate-limit status that its stream shows, so that a surface never hides a billing problem.

The chat the verdicts read SHALL be the closing event's final text and nothing else. On Codex, that is the last completed agent message. On Copilot, it is the content of the last top-level assistant message. All of this logic SHALL be covered by L0 tests against recorded and synthetic event streams:

- the verdicts;
- the event parsing and the telemetry;
- the command the runner builds and the judge command;
- the judge's child environment and the model-under-test child's environment;
- the stream checks that mark a call unavailable, the account-surface checks, and the stop at the first surface;
- the login-failure remedy for each kind of login;
- the login label, and that a refresh is written back only into the labelled login's directory;
- the exit-status mapping;
- the summary it prints.

The telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so that a host field rename fails a test rather than blanking the line. Until a later change records a Codex stream, the Codex readers are pinned against synthetic streams derived from the source of the pinned minimum CLI version, labelled synthetic. Until a later change records a Copilot stream, the Copilot readers are likewise pinned against synthetic streams derived from the package of the pinned version, labelled synthetic.

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

#### Scenario: Copilot run reports credits, not cost
- **WHEN** a Copilot run completes
- **THEN** the summary carries:
  - no cost, and a notional figure labelled as notional Copilot credits that were not billed;
  - the token counts from the per-model usage, the reasoning count included;
  - the credits consumed and the credit cap;
  - the overage count and the remaining percentage before and after the run;
  - the served model and the CLI version

#### Scenario: Dollar budget cap refused on Copilot
- **WHEN** a Copilot run is requested with a budget cap in dollars
- **THEN** the runner exits with a usage error naming the credit cap as Copilot's only cap, before staging and before any Copilot process starts

#### Scenario: Copilot token rejected during a run
- **WHEN** a Copilot run's stream carries a session error whose type is authentication or authorization
- **THEN** the runner failure carries the client's reason. It names creating a fine-grained token that carries only Copilot Requests and running `uv run poe host-login copilot --reset` as the one remedy, it closes with the sentence that the operator's own Copilot login is not affected, and the run exits with the untested status

#### Scenario: Copilot limit reached is not a result
- **WHEN** a Copilot run's stream carries a quota or rate-limit error, and in a second case a session-limit or credit-cap error
- **THEN** each run exits with the untested status as a limit reached, not a result. The second also records a billing stop

#### Scenario: Copilot exit code not trusted
- **WHEN** the Copilot client exits 0, while its stream carries a session error or a failed model call
- **THEN** the outcome follows the event, not the exit code, and no passing verdict is reported for the run

#### Scenario: No result line on Copilot
- **WHEN** the Copilot client exits without emitting its closing result line
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Copilot session without a shutdown record
- **WHEN** a Copilot run's session record holds no shutdown record, after a timeout or otherwise
- **THEN** the run ends as a runner failure saying that its consumption cannot be read, and a billing stop is recorded

#### Scenario: Copilot helper spawn counted
- **WHEN** a Copilot supervise run's stream shows one task-tool call whose prompt carries the verifier brief
- **THEN** the helper-call list reports one `Agent` call, the single-context verdict passes, and the verifier part of the L1 verdict passes

#### Scenario: Copilot precondition is untested, not a runner failure
- **WHEN** a Copilot run is refused because the run lock stayed held past its wait or the installed CLI is not the pinned version, or ends with a served model other than the requested one or an effort reported as left unapplied
- **THEN** the run exits with the untested status, not the runner-failure status, and its summary names the precondition that did not hold
