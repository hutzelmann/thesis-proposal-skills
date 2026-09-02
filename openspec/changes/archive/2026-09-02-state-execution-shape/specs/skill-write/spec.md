## ADDED Requirements

### Requirement: One writer per file

A writing pass SHALL be performed by one agent in one context: the canonical sections are drafted in sequence, review findings are applied item by item by the same agent, and the density pass reads the whole file. The skill SHALL NOT spawn one helper agent per section or per review finding, because parallel edits to one file break the surgical-edit rule, the `(RQn)` cross-references, and the whole-file density pass. Following a sibling skill's instructions in the same context is not a helper. The SKILL.md SHALL state this shape before its ground rules, and its opening sentence SHALL be pinned offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would draft the five sections or apply a review's findings through parallel helpers
- **THEN** the pass is written by one agent in sequence, and the file is never edited by more than one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords the execution-shape section without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the sentence
