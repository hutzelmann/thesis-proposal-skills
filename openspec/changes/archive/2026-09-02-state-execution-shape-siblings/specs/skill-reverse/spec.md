## ADDED Requirements

### Requirement: Single-context execution

A reverse run SHALL be performed by one agent in one context: the same agent reads the thesis's framing and closing, writes the harvest record from that reading, and writes the proposal from the record. The skill SHALL NOT spawn one helper agent per chapter, per harvest item, or per proposal section, because the knowledge cut is judged by seeing a plan sentence and its outcome sentence side by side and every helper would read the whole thesis again. Following the import sibling's conversion rules in the same context is not a helper. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would read the thesis through one helper per chapter or write the proposal through one helper per section
- **THEN** the run reads, harvests and writes in one context, and the thesis is read once

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference
