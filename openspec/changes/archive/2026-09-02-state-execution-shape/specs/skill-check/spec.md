## ADDED Requirements

### Requirement: Single-agent execution

A check run SHALL be two steps by one agent: the shipped script runs once, and the agent pass is one reading of the file by the same agent. Nothing in a check run SHALL be delegated to helper agents — not per finding category, per section, or per finding — and the fallback of performing the script's checks by hand when Python is missing is likewise that agent's own single reading. The SKILL.md SHALL state this shape before the target-resolution step, and its opening sentence SHALL be pinned offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the agent pass as one helper per category
- **THEN** the run performs the script step once and the agent pass once, in one context, and reports both in one chat message

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords the execution-shape section without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the sentence
