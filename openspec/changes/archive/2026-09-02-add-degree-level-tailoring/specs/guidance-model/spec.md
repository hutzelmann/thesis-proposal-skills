# guidance-model delta

## ADDED Requirements

### Requirement: Degree-level guidance
The guidelines SHALL carry a degree-level section stating where the level shows in a proposal, covering exactly four graded dimensions — contribution expectation, research-question origin, literature stance, and scope relative to the available months — in brief prose, and framing everything else as identical across levels by design, with `docs/degree-level-sources.md` named as provenance. The section SHALL state the both-directions bar: demanding a novelty claim from a Bachelor's proposal is the same error as accepting its absence from a Master's proposal. Bachelor-side statements SHALL be phrased as expectations not required, never as prohibitions — incipient novelty in a Bachelor's proposal remains welcome. The section SHALL NOT require an explicit methodology-justification statement at either level: a proposal declares one methodology and the proposal as a whole is its support; methodology fit remains a review-side judgement. The document skeleton, `structure.json`, and all mechanical checks SHALL remain level-blind.

#### Scenario: Four dimensions, nothing structural
- **WHEN** the guidelines' degree-level section is compared with `structure.json` and the check rules
- **THEN** the section names contribution expectation, research-question origin, literature stance, and scope-per-months as the graded dimensions, and no structured key or mechanical check varies by degree level

#### Scenario: Bachelor phrasing stays permissive
- **WHEN** the section describes the Bachelor's-level expectation on any dimension
- **THEN** the wording says what is not required at that level and never forbids exceeding it

#### Scenario: No justification requirement
- **WHEN** the section describes methodology at either level
- **THEN** it requires no explicit justification prose and locates methodology fit in review judgement
