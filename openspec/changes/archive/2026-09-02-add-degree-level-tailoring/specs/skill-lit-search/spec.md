# skill-lit-search delta

## ADDED Requirements

### Requirement: Level-aware literature stance
When the proposal's subtitle states the degree level, the skill SHALL weight its relevance judgement accordingly: at Bachelor's level, established anchors — textbooks, surveys, canonical papers — are legitimate results alongside current work; at Master's level, recent primary literature capable of yielding the gap the proposal must argue is prioritized. The weighting is a single self-contained rule in the skill; it adds no reference wiring, changes no source registry or query behavior, and is silently skipped when the level is unknown.

#### Scenario: Master search prioritizes gap-bearing work
- **WHEN** the subtitle declares a Master's thesis and results include both a survey and recent primary studies adjacent to the research questions
- **THEN** the relevance judgement ranks the primary studies as the results the proposal's argument needs, without discarding the survey

#### Scenario: Bachelor search accepts established anchors
- **WHEN** the subtitle declares a Bachelor's thesis
- **THEN** textbook and survey anchors are judged legitimate results, not down-ranked for being established

#### Scenario: Unknown level changes nothing
- **WHEN** the working directory's proposal states no level or no proposal is present
- **THEN** search and relevance judgement behave exactly as without this requirement
