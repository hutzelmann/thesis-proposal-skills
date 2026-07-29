# Delta: skill-ideate

## Purpose

Socratic idea-development skill that helps a student refine a thesis idea into an academically grounded starting point, seeding the proposal file.

## ADDED Requirements

### Requirement: Socratic interaction style
The skill SHALL NOT ask directly for missing input. It lets the user talk about their idea and offers hints, observations, and suggestions that lead the user to refine the missing aspects themselves.

#### Scenario: Missing methodology
- **WHEN** the user's idea lacks any notion of scientific method
- **THEN** the skill raises method-shaped considerations ("how would one know this worked?") rather than asking "which methodology do you want?"

### Requirement: Literature-grounded ideation
During ideation the skill SHALL consult academic literature to test whether the idea is already solved, whether relevant literature exists, and how the idea differs from prior work — and SHALL use findings to sharpen the idea academically. When literature lookup is unavailable, the skill SHALL continue and state explicitly that it is working ungrounded.

#### Scenario: Idea already solved
- **WHEN** literature lookup surfaces work that substantially covers the user's idea
- **THEN** the skill presents the overlap and steers the conversation toward a differentiating angle

#### Scenario: Lookup unavailable
- **WHEN** literature sources are unreachable
- **THEN** ideation continues with an explicit ungrounded-mode notice

### Requirement: Seeds the proposal file
The skill SHALL end by creating the proposal file (per proposal-file-format): working title, problem sketch, candidate research-question directions as notes, open questions as `[TODO: …]` markers, and a metadata block containing any starter references found.

#### Scenario: Session ends after ideation
- **WHEN** the ideation session concludes
- **THEN** a slug-named proposal file exists containing the captured idea state, consumable by the write skill
