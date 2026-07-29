# Delta: skill-customize

## Purpose

Dialog-driven management of the workspace `guidelines.md` override file, translating supervisor requirements into the guidance model safely.

## ADDED Requirements

### Requirement: Dialog-driven override management
The skill SHALL create or edit `guidelines.md` from a conversation about the user's or supervisor's requirements, writing the machine-readable TOML block and prose sections per the guidance model.

#### Scenario: Page limit request
- **WHEN** the user says the supervisor wants at most 3 pages
- **THEN** the skill writes `page_limit = 3` into the TOML block

### Requirement: Conflict validation with consequences
When a requested customization conflicts with defaults (e.g. requiring a default-forbidden section), the skill SHALL apply it only after explaining the conflict and its consequences for checks and reviews.

#### Scenario: Timeline requirement
- **WHEN** the user asks for a required timeline section
- **THEN** the skill explains it is forbidden by default, applies the override on confirmation, and notes that checks will now require it
