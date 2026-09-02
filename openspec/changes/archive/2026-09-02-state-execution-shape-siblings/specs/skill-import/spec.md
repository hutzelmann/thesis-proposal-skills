## ADDED Requirements

### Requirement: Single-context execution

An import SHALL be performed by one agent in one context: the same agent reads the source once, maps its content onto the canonical sections, converts the references, and writes `<slug>.md` and the notes file. The skill SHALL NOT spawn one helper agent per section, per reference, per citation, or per figure, because reordering into canonical order and the personal-data strip need the whole document in view, every helper would read the source again, and the two output files have one writer. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would map the source through one helper per section or convert the bibliography through one helper per reference
- **THEN** the import is performed in one context, the source is read once, and both output files are written by that one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference
