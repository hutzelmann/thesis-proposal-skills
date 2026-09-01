# skill-write delta

## ADDED Requirements

### Requirement: Level-aware contribution close and research questions
The skill SHALL read the degree level from the subtitle wording — the same inference path as language, no other source — and honor it when drafting the contribution section's close and the research questions: at Master's level the close names what will be new and for whom; at Bachelor's level a promise to apply or evaluate something competently in a named setting is a complete close, and the skill SHALL NOT push a novelty claim into it, while preserving one the author states. Research questions follow the same grading: deriving them from a given topic is level-appropriate at Bachelor's level; at Master's level they are grounded in the gap the contribution section argues. When the subtitle carries a TODO marker, the skill SHALL ask for the level exactly once, at the moment it first drafts the contribution close, and SHALL proceed level-neutrally if the author declines.

#### Scenario: Master close without a novelty claim
- **WHEN** the subtitle declares a Master's thesis and the drafted contribution close only promises competent application
- **THEN** the skill raises the missing statement of what will be new before considering the section complete

#### Scenario: Bachelor close not pushed toward novelty
- **WHEN** the subtitle declares a Bachelor's thesis and the author's close promises a competent evaluation in a named setting
- **THEN** the skill treats the close as complete and adds no novelty demand

#### Scenario: Level TODO triggers one deferred question
- **WHEN** the subtitle is a TODO marker and the skill reaches the contribution close
- **THEN** it asks for the degree level once, writes the canonical subtitle on an answer, and continues level-neutrally without repeating the question if the author declines
