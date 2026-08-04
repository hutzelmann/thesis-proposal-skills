# skill-lit-search Specification

## Purpose
Multi-source academic literature search producing CSL-YAML reference entries, with keyword and citation-snowballing modes, designed keyless-first for Computer Science.
## Requirements
### Requirement: Academic sources with judged relevance
The skill SHALL search academic literature only and SHALL judge actual relevance to the topic/proposal rather than returning keyword hits. Peer-reviewed venues SHALL be preferred over preprints when both versions exist.

#### Scenario: Keyword-matching but irrelevant paper
- **WHEN** a source API returns a paper matching the query terms but unrelated to the research focus
- **THEN** the skill excludes it from the results

### Requirement: Keyword and snowballing modes
The skill SHALL support (a) keyword/topic search and (b) snowballing from seed papers in the proposal's `references`: backward via their reference lists and forward via citing papers and recommendations.

#### Scenario: Snowballing from three seeds
- **WHEN** the user requests expansion from a proposal with three references
- **THEN** the skill gathers referenced and citing works for those seeds, ranks by relevance, and proposes additions

### Requirement: Multi-source federation with graceful degradation
Results SHALL be merged and deduplicated across sources by DOI or normalized title. A failing or rate-limited source SHALL degrade the search to the remaining sources with a note — it MUST NOT block the search.

#### Scenario: One source down
- **WHEN** a literature API is unreachable
- **THEN** the search completes on remaining sources and reports the degradation

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

### Requirement: CSL-YAML output into the proposal
Accepted findings SHALL be written as CSL-YAML entries into the proposal's `references` block, deduplicated against existing entries. Each entry carries abstract, authors, year, and DOI when available; a URL is included only when no DOI exists.

#### Scenario: Entry with DOI
- **WHEN** a selected paper has a DOI
- **THEN** the stored entry contains the DOI and no URL field

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

### Requirement: Excluded literature recorded in the notes file
When a companion `<slug>.notes.md` exists, the literature-search skill SHALL record rejected candidates in its Excluded Literature section — entry identifier (DOI or title) plus a one-line reason — and SHALL NOT re-propose an entry that section already lists in a later search. Acceptance bookkeeping is unchanged: accepted entries go into the proposal's `references:` block as before. When no notes file exists, rejections MAY go unrecorded; the skill SHALL NOT create the notes file for this purpose alone.

#### Scenario: Rejected candidate not proposed twice
- **WHEN** a search surfaces a paper the notes Excluded Literature section already lists
- **THEN** the skill skips it without presenting it to the user again

#### Scenario: Rejection recorded with reason
- **WHEN** the user rejects a candidate during result review and a notes file exists
- **THEN** the Excluded Literature section gains the entry's identifier and a one-line reason

