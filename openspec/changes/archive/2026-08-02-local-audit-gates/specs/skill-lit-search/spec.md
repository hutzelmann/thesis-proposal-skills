## MODIFIED Requirements

### Requirement: Keyless baseline, keys as guided upgrades
The default installation SHALL work fully without any API key. Optional keys only improve rate limits, abstracts, or coverage. The skill SHALL detect missing/exhausted keys (including quota errors) and degrade cleanly. When a free key would help, the skill SHALL offer agent-guided setup around one central key file at the workspace root, shared by every proposal in that workspace: state the concrete benefit, point to the signup location, create or update the key file with a named placeholder for the key, ensure version-control ignores cover the file, have the user paste the key value into the file themselves, and validate the result with a test call that reads the file mechanically. The secret value SHALL NOT pass through the agent: the agent never asks the user to provide the value in conversation and never reads, echoes, logs, or writes it. An error caused by a missing key SHALL name every location that was consulted.

#### Scenario: No keys configured
- **WHEN** the user runs a search with zero keys configured
- **THEN** the search succeeds on keyless sources and mentions what an optional key would add

#### Scenario: Quota exhausted
- **WHEN** a keyed source returns a quota-exhausted error
- **THEN** the skill continues with the other sources and reports the limitation

#### Scenario: Key is missing
- **WHEN** a keyed source is reached with no key available
- **THEN** the reported error names the environment variable and every key-file location that was searched

#### Scenario: Guided setup hand-off
- **WHEN** the user accepts guided key setup
- **THEN** the agent creates or updates the workspace-root key file with an empty placeholder entry, directs the user to paste the key into that file, and verifies afterwards by running a search — without the key value ever appearing in the conversation or in any agent-written content

#### Scenario: User offers the key in chat
- **WHEN** the user pastes an API key value into the conversation
- **THEN** the agent does not repeat or store the value, and asks the user to put it into the key file themselves
