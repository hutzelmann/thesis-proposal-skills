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
The default installation SHALL work fully without any API key. Optional keys only improve rate limits, abstracts, or coverage. The skill SHALL detect missing/exhausted keys (including quota errors) and degrade cleanly. When a free key would help, the skill SHALL offer agent-guided setup: state the concrete benefit, point to the signup location, say exactly where to put the key, and validate it with a test call. An error caused by a missing key SHALL name every location that was consulted.

#### Scenario: No keys configured
- **WHEN** the user runs a search with zero keys configured
- **THEN** the search succeeds on keyless sources and mentions what an optional key would add

#### Scenario: Quota exhausted
- **WHEN** a keyed source returns a quota-exhausted error
- **THEN** the skill continues with the other sources and reports the limitation

#### Scenario: Key is missing
- **WHEN** a keyed source is reached with no key available
- **THEN** the reported error names the environment variable and every key-file location that was searched

### Requirement: CSL-YAML output into the proposal
Accepted findings SHALL be written as CSL-YAML entries into the proposal's `references` block, deduplicated against existing entries. Each entry carries abstract, authors, year, and DOI when available; a URL is included only when no DOI exists.

#### Scenario: Entry with DOI
- **WHEN** a selected paper has a DOI
- **THEN** the stored entry contains the DOI and no URL field

### Requirement: Credential resolution independent of working directory
Credentials SHALL resolve per key, in this order: the process environment, the file named by `$THESIS_PROPOSAL_KEYS`, `api-keys.env` in the working directory and each ancestor directory, then a user-global `api-keys.env` under the user's config directory. Ancestor search SHALL NOT continue above the user's home directory. Resolution SHALL proceed to the next location when a file exists but does not define the requested key, so that a workspace file and a global file compose rather than shadow one another. Key files SHALL remain one `KEY=VALUE` per line with `#` comments, and a missing or unreadable file SHALL NOT be an error.

#### Scenario: Script run from a workspace subdirectory
- **WHEN** a script runs from any directory below a workspace whose root holds `api-keys.env`
- **THEN** the key resolves from that file exactly as it would from the workspace root

#### Scenario: Workspace and global files compose
- **WHEN** the workspace file defines only the API key and the global file defines only `CONTACT_EMAIL`
- **THEN** both values resolve

#### Scenario: Key file outside the user's tree
- **WHEN** an `api-keys.env` exists in a directory above the user's home directory
- **THEN** it is not consulted

