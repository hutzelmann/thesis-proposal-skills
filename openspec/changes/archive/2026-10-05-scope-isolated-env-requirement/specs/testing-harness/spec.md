# Spec Delta

## MODIFIED Requirements

### Requirement: Isolated child environment
An isolated host child SHALL receive an environment built from an allowlist. This covers every routing-rig run and the model-under-test child of every dev-runner run in isolated mode. It SHALL NOT receive the launching process's environment with only the configuration directory overridden. One function, shared by both runners, SHALL build that environment. The dev judge's child also runs in an isolated configuration, but its environment is governed by the requirement "Subscription text roles (dev runner)", not by this one.

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

#### Scenario: Judge child outside this requirement
- **WHEN** an isolated dev run is graded by the dev judge
- **THEN** the judge's child gets the environment that "Subscription text roles (dev runner)" prescribes, and only the model-under-test child is held to this allowlist

#### Scenario: No values printed
- **WHEN** the isolated environment is built from an environment holding a messaging token
- **THEN** nothing is printed, and the token's value appears in no output
