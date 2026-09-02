## MODIFIED Requirements

### Requirement: Single-agent execution

A check run SHALL be two steps by one agent: the shipped script runs once — and a second time only for the digest comparison the read-only mandate requires of a non-interactive run — and the agent pass is one reading of the file by the same agent. Nothing in a check run SHALL be delegated to helper agents — not per finding category, per section, or per finding — and the fallback of performing the script's checks by hand when Python is missing is likewise that agent's own single reading. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the agent pass as one helper per category
- **THEN** the run performs the script step once (twice non-interactively, for the digest) and the agent pass once, in one context, and reports both in one chat message

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference
