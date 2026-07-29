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
The default installation SHALL work fully without any API key. Optional keys, supplied via environment, only improve rate limits, abstracts, or coverage. The skill SHALL detect missing/exhausted keys (including quota errors) and degrade cleanly. When a free key would help, the skill SHALL offer agent-guided setup: state the concrete benefit, point to the signup location, say exactly where to put the key, and validate it with a test call.

#### Scenario: No keys configured
- **WHEN** the user runs a search with zero keys configured
- **THEN** the search succeeds on keyless sources and mentions what an optional key would add

#### Scenario: Quota exhausted
- **WHEN** a keyed source returns a quota-exhausted error
- **THEN** the skill continues with the other sources and reports the limitation

### Requirement: CSL-YAML output into the proposal
Accepted findings SHALL be written as CSL-YAML entries into the proposal's `references` block, deduplicated against existing entries. Each entry carries abstract, authors, year, and DOI when available; a URL is included only when no DOI exists.

#### Scenario: Entry with DOI
- **WHEN** a selected paper has a DOI
- **THEN** the stored entry contains the DOI and no URL field

