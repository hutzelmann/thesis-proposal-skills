# skill-write Specification

## Purpose
Writes a proposal from scratch or refines an existing one, following the guidance model and grounding claims in the proposal's literature.
## Requirements
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

### Requirement: Citation form selection
The skill SHALL choose between the two citation syntaxes by grammatical role, consistently across a proposal: the author-in-text form only where the cited authors are the grammatical subject or agent of the sentence, and the bracketed form where the citation is evidence attached to a claim. The skill SHALL NOT type an author name next to a bracketed citation by hand, because the rendered author label is derived from the reference entry.

#### Scenario: Authors act in the sentence
- **WHEN** a sentence states what the cited researchers propose, show, or argue
- **THEN** the citation is written in the author-in-text form

#### Scenario: Citation supports a claim
- **WHEN** a sentence states a fact about the field and the cited work is evidence for it
- **THEN** the citation is written in the bracketed form and no author name appears in the prose

#### Scenario: Author name typed manually
- **WHEN** refining a proposal that contains a hand-typed author name immediately before a bracketed citation
- **THEN** the skill replaces the pair with the author-in-text form so the name stays derived from the reference entry

### Requirement: Bilingual writing conventions
The skill SHALL write in the proposal's declared language. German proposals use English scientific terms with German capitalization and the canonical German section titles.

#### Scenario: German proposal drafted
- **WHEN** the proposal declares `lang: de`
- **THEN** section titles are the canonical German ones and scientific terms remain English with German capitalization

