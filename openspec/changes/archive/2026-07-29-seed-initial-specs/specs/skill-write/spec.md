# Delta: skill-write

## Purpose

Writes a proposal from scratch or refines an existing one, following the guidance model and grounding claims in the proposal's literature.

## ADDED Requirements

### Requirement: Guidance-driven writing
The skill SHALL follow the default guidance combined with any workspace `guidelines.md` overrides (structure, forbidden content, writing rules, language conventions) when creating or refining a proposal.

#### Scenario: Workspace override active
- **WHEN** the workspace un-forbids a timeline section
- **THEN** written output may include a timeline and other defaults still apply

### Requirement: No fabricated sources
The skill SHALL cite only keys present in the proposal's `references` block and SHALL NOT invent publications. Missing information or missing references produce `[TODO: …]` markers instead.

#### Scenario: Claim needs an unavailable source
- **WHEN** a statement needs literature support not present in `references`
- **THEN** the skill inserts a TODO marker rather than a fabricated citation

### Requirement: Refinement preserves author content
When refining an existing proposal, the skill SHALL make minimal, surgical edits that preserve the author's substance and voice, and SHALL NOT re-write untouched sections wholesale.

#### Scenario: Improve research questions only
- **WHEN** the user asks to improve the research questions
- **THEN** only the research-question section (and directly dependent methodology references) changes

### Requirement: Bilingual writing conventions
The skill SHALL write in the proposal's declared language. German proposals use English scientific terms with German capitalization and the canonical German section titles.

#### Scenario: German proposal drafted
- **WHEN** the proposal declares `lang: de`
- **THEN** section titles are the canonical German ones and scientific terms remain English with German capitalization
