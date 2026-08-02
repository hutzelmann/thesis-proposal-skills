## ADDED Requirements

### Requirement: Credential resolution without directory traversal
Credentials SHALL resolve per key, in this order: the process environment, the file named by `$THESIS_PROPOSAL_KEYS`, `api-keys.env` in the working directory, then a user-global `api-keys.env` under the user's config directory. Scripts SHALL NOT search ancestor directories or any other location for key files. Resolution SHALL proceed to the next location when a file exists but does not define the requested key, so that a workspace file and a global file compose rather than shadow one another. Key files SHALL remain one `KEY=VALUE` per line with `#` comments, and a missing or unreadable file SHALL NOT be an error. A key-related error message SHALL name every location that was consulted.

#### Scenario: Script run from the workspace root
- **WHEN** a script runs in a directory whose `api-keys.env` defines the requested key
- **THEN** the key resolves from that file

#### Scenario: Script run from a workspace subdirectory
- **WHEN** a script runs from a subdirectory while `api-keys.env` sits only at the workspace root and neither the environment nor `$THESIS_PROPOSAL_KEYS` supplies the key
- **THEN** the key does not resolve and the affected source degrades with the documented error naming the consulted locations

#### Scenario: Workspace and global files compose
- **WHEN** the workspace file defines only the API key and the global file defines only `CONTACT_EMAIL`
- **THEN** both values resolve

#### Scenario: Key file in an ancestor directory
- **WHEN** an `api-keys.env` exists in a parent of the working directory and nowhere else
- **THEN** it is not consulted

### Requirement: Static source registry
The orchestrator scripts SHALL resolve literature sources from a fixed registry compiled into the scripts. Source selection input SHALL be validated against that registry: a request naming an unknown source SHALL be rejected with an error listing the valid names, and SHALL NOT cause any module loading, code execution, or network access derived from the unknown name.

#### Scenario: Unknown source requested
- **WHEN** a search is invoked with `--sources dblp,evilmodule`
- **THEN** the run fails before any search with an error naming `evilmodule` as unknown and listing the valid sources

#### Scenario: Valid subset requested
- **WHEN** a search is invoked with `--sources dblp,crossref`
- **THEN** exactly those sources run

## REMOVED Requirements

### Requirement: Credential resolution independent of working directory
**Reason**: Ancestor-directory traversal for credential files is an insecure-credential-discovery pattern (flagged HIGH by the skills.sh Snyk audit): a script run in an arbitrary directory could read key files belonging to unrelated projects anywhere up the tree. Working-directory independence is preserved for the cases that need it via the process environment, `$THESIS_PROPOSAL_KEYS`, and the user-global config file.
**Migration**: Keep `api-keys.env` at the workspace root and run scripts from there (the standard agent setup — the agent's working directory is the workspace root). For any other layout, set `$THESIS_PROPOSAL_KEYS` to the file's path or use `~/.config/thesis-proposal/api-keys.env`.
