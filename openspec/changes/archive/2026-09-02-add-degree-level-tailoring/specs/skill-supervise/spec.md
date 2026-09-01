# skill-supervise delta

## ADDED Requirements

### Requirement: Level-calibrated feedback bar
The drafted feedback SHALL be calibrated to the degree level the submission's subtitle states: a Master's proposal missing a statement of what will be new is always asked for one; a Bachelor's proposal is never asked for a novelty claim, and one it makes is engaged on its merits rather than removed. The same calibration applies to research-question origin, literature stance, and scope-for-the-months. When the submission does not state a level, the draft SHALL apply the level-independent bar and note the unset level once — as a point for the student, not a guess.

#### Scenario: Master submission missing the delta
- **WHEN** a submission subtitled as a Master's thesis promises only competent application in its contribution close
- **THEN** the drafted letter asks for the statement of what the thesis will add

#### Scenario: Bachelor submission held to its own bar
- **WHEN** a submission subtitled as a Bachelor's thesis has a bounded application promise and level-appropriate derived research questions
- **THEN** the drafted letter raises no novelty demand and no research-question-origin concern

#### Scenario: Level unset in the submission
- **WHEN** the submission's subtitle matches no canonical wording
- **THEN** the draft judges against the level-independent bar and includes one line asking the student to state the degree level in the subtitle
