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
The skill SHALL choose between the two citation syntaxes by the role the cited authors play in the sentence, consistently across a proposal: the author-in-text form wherever the authors belong in the running text — as the grammatical subject or agent, or as the possessor of the artifact under discussion ("the detector of @key") — and the bracketed form where the citation is evidence attached to a claim and no author is named. The skill SHALL NOT type an author name next to a bracketed citation by hand, because the rendered author label is derived from the reference entry.

#### Scenario: Authors act in the sentence
- **WHEN** a sentence states what the cited researchers propose, show, or argue
- **THEN** the citation is written in the author-in-text form

#### Scenario: Authors possess the artifact under discussion
- **WHEN** a sentence refers to "the detector of" or "the approach of" the cited authors, so the name belongs in the prose without being the subject
- **THEN** the citation is written in the author-in-text form in place of the typed name, which renders the same text

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

### Requirement: Self-verification before reporting
The skill SHALL ship the mechanical check as a synchronized copy and SHALL run it over the produced or edited proposal before reporting a writing pass complete, fixing every error it reports and re-running until only tolerated findings remain. Two findings are explicitly not "fixed": a reference-count shortfall is reported to the user because inventing a publication is forbidden, and open `[TODO: …]` markers stay because they are the honest record of what the material did not supply.

#### Scenario: Check finds a structural error in fresh output
- **WHEN** the check reports an error on the file the skill just wrote (a drifted section title, an unterminated metadata block, a cited key missing from `references`, a missing `(RQn)` reference)
- **THEN** the skill corrects the file and re-runs the check before reporting, and the report states what the check still finds

#### Scenario: Check reports a reference shortfall
- **WHEN** the only remaining error is that the proposal cites fewer references than required
- **THEN** the skill reports the shortfall and suggests the literature-search skill instead of adding sources the material did not carry

#### Scenario: Open TODO markers remain
- **WHEN** the check warns about open `[TODO: …]` markers recording gaps the source material did not fill
- **THEN** the skill leaves the markers in place and lists them in its report

### Requirement: Methodology decision under deferred choice
When the source material leaves the methodology choice open, the skill SHALL decide: it picks the methodology from the closed set that the research questions best support, writes the canonical methodology heading for that choice, and records the uncertainty as `[TODO: confirm methodology choice]` in the section body. A section heading SHALL NOT carry a TODO marker.

#### Scenario: Seed defers the methodology choice
- **WHEN** the idea notes contain an open TODO deferring between two methodologies
- **THEN** the drafted proposal carries a canonical methodology heading for the better-supported option and a `[TODO: confirm methodology choice]` marker in the section body

#### Scenario: User states the methodology in the request
- **WHEN** the request names the methodology to use
- **THEN** the skill uses it without adding a confirmation TODO

