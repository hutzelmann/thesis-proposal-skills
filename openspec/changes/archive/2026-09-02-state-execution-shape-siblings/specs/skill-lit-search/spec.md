## ADDED Requirements

### Requirement: Single-context execution

A literature search SHALL be performed by one agent in one context: the shipped scripts gather the candidates, and the same agent judges the whole candidate set together and merges the accepted entries. The skill SHALL NOT spawn one helper agent per candidate, per source, or per research question, because a preprint and its published version are recognised only side by side, key uniqueness is a property of the whole references block, and the proposal and the notes file have one writer. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would judge relevance through one helper per candidate
- **THEN** the candidate set is judged together in one context and merged by that one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference
