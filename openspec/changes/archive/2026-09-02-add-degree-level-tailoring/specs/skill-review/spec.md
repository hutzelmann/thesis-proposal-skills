# skill-review delta

## ADDED Requirements

### Requirement: Degree-level review lenses
The review SHALL judge level fit through the graded dimensions when the subtitle states the level: whether the contribution close matches the level's bar (application promise sufficient at Bachelor's, statement of what is new required at Master's — in both directions, so demanding novelty of a Bachelor's proposal is flagged as a mis-set bar exactly like a Master's close missing one), whether the research questions' origin fits (derivation from a given topic acceptable at Bachelor's, gap-grounding expected at Master's), whether the literature stance fits (established anchors legitimate at Bachelor's, the gap produced by engaging current work at Master's), and whether the scope is deliverable in the stated months at that level. Methodology fit is reviewed as judgement — whether the chosen methodology follows from the research questions, and at Master's level whether the plan shows awareness of its limits — never as a demand for explicit justification prose. When the subtitle does not state a level, the review SHALL apply the level-independent core and include exactly one line naming the unset level; it SHALL NOT guess.

#### Scenario: Master proposal with application-only close
- **WHEN** the subtitle declares a Master's thesis and the contribution close promises only competent application
- **THEN** the review flags the missing statement of what will be new as a level mismatch

#### Scenario: Bachelor proposal not held to the Master bar
- **WHEN** the subtitle declares a Bachelor's thesis and the close promises a competent, well-bounded evaluation
- **THEN** the review raises no novelty finding for the close

#### Scenario: Unknown level reviewed neutrally
- **WHEN** the subtitle is a TODO marker or matches no canonical wording
- **THEN** the review applies the level-independent rules, adds one line that the level is unset so level-dependent lenses were not applied, and guesses no level
