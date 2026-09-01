# skill-ideate delta

## ADDED Requirements

### Requirement: Level-steered ideation
When the degree level is known from the preamble, the skill SHALL let it steer the Socratic session: at Bachelor's level, hints steer toward a well-bounded application or evaluation of something established, and deriving the topic from the supervising group's work is named as the level-appropriate move; at Master's level, hints push toward a gap in the literature and toward what would be new. The steering SHALL add no new preamble questions, SHALL never present the level as a limit on ambition, and SHALL leave no level-related concern in the seed file. When the level was never given, ideation proceeds level-neutrally as today.

#### Scenario: Bachelor session steers toward bounded application
- **WHEN** a preamble declared a Bachelor's thesis and the student floats a direction requiring novel research to be viable
- **THEN** the skill's hints steer toward a bounded, executable variant and name derivation from the group's topics as legitimate at this level, without forbidding the ambitious direction

#### Scenario: Master session pushes for the gap
- **WHEN** a preamble declared a Master's thesis and the idea reads as pure application of established work
- **THEN** the skill asks Socratically what the thesis would add that is not already known, steering toward a gap

#### Scenario: Level never given
- **WHEN** the preamble skipped the degree-level question
- **THEN** the session runs level-neutrally and the seed's subtitle carries the TODO marker as before
