## MODIFIED Requirements

### Requirement: Academic sources with judged relevance
The skill SHALL search academic literature only and SHALL judge actual relevance to the topic/proposal rather than returning keyword hits. Peer-reviewed venues SHALL be preferred over preprints when both versions exist.

Relevance SHALL be judged as a merge precondition, not as a presentation filter: an entry enters the proposal's `references:` block only when the claim it will support in this proposal can be named — a research question it grounds, a delta it evidences, or a method choice it supports. A candidate that is academic, correct, and topically adjacent but supports no such claim SHALL be rejected rather than merged, and rejected candidates are recorded as the Excluded Literature requirement specifies. The skill SHALL NOT merge an entry on the expectation that a use for it will be found later: after merging, an entry no claim needs leaves the proposal only through the writing skill's removal path, and the intervening state pulls the proposal's text toward the entry.

#### Scenario: Keyword-matching but irrelevant paper
- **WHEN** a source API returns a paper matching the query terms but unrelated to the research focus
- **THEN** the skill excludes it from the results

#### Scenario: Adjacent paper with no claim to support
- **WHEN** a returned paper is peer-reviewed and shares the proposal's domain but supports no research question, delta statement, or method choice the proposal makes
- **THEN** the skill rejects it, states that no claim in the proposal needs it, and does not merge it into `references:`

#### Scenario: Accepted entry names its claim
- **WHEN** the skill merges a candidate into `references:`
- **THEN** its report names the claim in the proposal that the entry supports
