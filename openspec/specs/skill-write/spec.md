# skill-write Specification

## Purpose
Writes a proposal from scratch or refines an existing one, following the guidance model and grounding claims in the proposal's literature.
## Requirements
### Requirement: Guidance-driven writing
The skill SHALL follow the default guidance combined with any workspace `guidelines.md` overrides (structure, forbidden content, writing rules, language conventions) when creating or refining a proposal.

#### Scenario: Workspace override active
- **WHEN** the workspace selects the detailed timeline mode
- **THEN** written output may include a phase table in the timeline section and other defaults still apply

### Requirement: Timeline written, never invented
Created proposals SHALL carry the canonical timeline section as their final section. When the start and submission months are known, the skill SHALL state them in one short sentence; when the writer has said the work begins as soon as possible, the skill SHALL state that instead.

When the timeframe is not known, the skill SHALL write a visible TODO marker and SHALL NOT fall back to an as-soon-as-possible statement, because that is a claim only the writer can make and a writer with a registered submission date would be misrepresented by it. In an interactive session the skill SHALL ask for the timeframe once; a session that runs without the writer present SHALL produce the TODO marker rather than block.

#### Scenario: Dates known
- **WHEN** the writer has said the thesis starts in October and is submitted in March
- **THEN** the created proposal ends with a timeline section naming both months

#### Scenario: Writer states no fixed dates
- **WHEN** the writer says there is no registered date and the work starts once the supervisor approves
- **THEN** the timeline section states that the thesis begins as soon as possible

#### Scenario: Timeframe never supplied
- **WHEN** a draft is produced without the writer supplying a timeframe
- **THEN** the timeline section carries a visible TODO marker and asserts nothing about timing

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
The skill SHALL ship the mechanical check as a synchronized copy and SHALL run it over the produced or edited proposal before reporting a writing pass complete, fixing every error it reports and re-running until only tolerated findings remain. Three findings are explicitly not "fixed": a reference-count shortfall is reported to the user because inventing a publication is forbidden; open `[TODO: …]` markers stay because they are the honest record of what the material did not supply; and a finding the skill can demonstrate is a false positive is reported rather than worked around, because the author's content is correct as written.

Correcting markup remains permitted where markup is the actual defect — a code identifier in prose is marked as code. Rewording the author's terminology, and deleting a reference, a citation or a sentence, SHALL NOT be used to silence a finding: that trades a wrong finding for a real defect. The skill SHALL name the finding it is leaving, state why it is wrong, and name the troubleshoot skill as the route to a bug report.

#### Scenario: Check finds a structural error in fresh output
- **WHEN** the check reports an error on the file the skill just wrote (a drifted section title, an unterminated metadata block, a cited key missing from `references`, a missing `(RQn)` reference)
- **THEN** the skill corrects the file and re-runs the check before reporting, and the report states what the check still finds

#### Scenario: Check reports a reference shortfall
- **WHEN** the only remaining error is that the proposal cites fewer references than required
- **THEN** the skill reports the shortfall and suggests the literature-search skill instead of adding sources the material did not carry

#### Scenario: Open TODO markers remain
- **WHEN** the check warns about open `[TODO: …]` markers recording gaps the source material did not fill
- **THEN** the skill leaves the markers in place and lists them in its report

#### Scenario: Check reports a demonstrable false positive
- **WHEN** the check reports a code identifier written in prose as an undefined citation key
- **THEN** the skill marks the identifier as code, leaves the author's wording intact, and neither invents a reference nor deletes an existing one

#### Scenario: A finding cannot be resolved by markup
- **WHEN** a finding is wrong and no markup correction resolves it
- **THEN** the skill leaves the document as written, reports which finding it is leaving and why, and names the troubleshoot skill

### Requirement: Methodology decision under deferred choice
When the source material leaves the methodology choice open, the skill SHALL decide: it picks the methodology from the closed set that the research questions best support, writes the canonical methodology heading for that choice, and records the uncertainty as `[TODO: confirm methodology choice]` in the section body. A section heading SHALL NOT carry a TODO marker; the leading `# <title>` line is not a section heading and MAY carry one, per the file-format contract.

#### Scenario: Seed defers the methodology choice
- **WHEN** the idea notes contain an open TODO deferring between two methodologies
- **THEN** the drafted proposal carries a canonical methodology heading for the better-supported option and a `[TODO: confirm methodology choice]` marker in the section body

#### Scenario: User states the methodology in the request
- **WHEN** the request names the methodology to use
- **THEN** the skill uses it without adding a confirmation TODO

#### Scenario: Unsettled title carries its marker in the title line
- **WHEN** the draft's title is not yet settled
- **THEN** the leading `# ` line carries the TODO marker and no section heading gains one in its place

### Requirement: Notes file consumed and maintained while writing
When a companion `<slug>.notes.md` exists for the target proposal, the write skill SHALL read it before drafting and honor its content: recorded decisions steer the draft (they are not re-litigated), and the Next Focus section informs which gaps to work on first. Decisions the writing session itself produces SHALL be recorded in the notes Decisions section. When the session resolves a proposal `[TODO: …]` marker, the skill SHALL move it to the notes Log as a done entry rather than deleting it. When no notes file exists, the skill SHALL proceed as before and MAY create one only when it has decisions to record — never an empty skeleton.

#### Scenario: Prior decision honored
- **WHEN** the notes Decisions section records that a user study was rejected in favor of a prototype implementation
- **THEN** the draft builds on the prototype methodology and the skill does not re-open the methodology question

#### Scenario: Resolved marker logged
- **WHEN** the writing session fills the gap behind a proposal TODO marker
- **THEN** the marker is removed from the proposal and appears in the notes Log as done, with a note of what resolved it

#### Scenario: No notes file present
- **WHEN** the target proposal has no companion notes file and the session makes no recordable decision
- **THEN** the skill writes the proposal as usual and creates no notes file

### Requirement: Title negotiated once research questions exist
The skill SHALL judge the proposal's title against the guidance once the research questions are written, including a title inherited unchanged from an ideation seed, and SHALL NOT treat an inherited title as settled. Where the title matches an alarm class, the skill SHALL raise it in chat, state that the title is printed on the study certificate, and offer between one and three abstracted alternatives naming the contribution and its object. The skill SHALL write the student's chosen title, never a silent replacement, and where a named technology is retained the skill SHALL have the student's stated reason that the technology is the object of study.

#### Scenario: Seed title inherited unchanged
- **WHEN** the draft is written from a seed whose working title names a product carried as the instrument
- **THEN** the skill raises the title, names the certificate consequence, and offers abstracted alternatives before reporting the draft finished

#### Scenario: Student picks an alternative
- **WHEN** the student chooses one of the offered titles
- **THEN** the leading `# ` line carries that title and the slug is left alone unless the student asks for a rename

#### Scenario: Student keeps a named technology
- **WHEN** the student states that the named technology is the object of study
- **THEN** the title is written as the student chose it and the point is not raised again in that session

#### Scenario: Title already academic
- **WHEN** the title names a contribution and its object with no alarm class matched
- **THEN** the skill leaves it alone and spends no turn on it

### Requirement: Substance gate
Where the collected material (seed, notes, user input, references) does not support a substantive statement, the skill SHALL NOT generate generic prose to fill the gap: the gap becomes a visible `[TODO: …]` marker or the affected content is omitted, and the closing report SHALL state plainly which sections rest on thin material and point to the ideation skill (for missing idea substance) or the review skill (for the substance verdict). Text the skill generates SHALL be traceable to the material; well-sounding filler that would survive the guidance's swap test in reverse — text equally true of any thesis in the area — SHALL NOT be written.

#### Scenario: Hollow seed drafted honestly
- **WHEN** the seed carries a topic phrase but no delta, no object of study, and no method substance
- **THEN** the drafted sections carry TODO markers for the missing substance, no generic filler prose is produced, and the closing report names the gaps

#### Scenario: Material supports the section
- **WHEN** the notes record a concrete evaluation design for the methodology section
- **THEN** the skill writes the section from that material without any substance TODO

### Requirement: Density pass binding per writing pass
After every writing pass, before reporting, the skill SHALL re-read the produced or edited text against the guidance's information-density rule and delete sentences that carry no information essential to this thesis — scene-setting openers, truisms, restatements. This pass is binding like the mechanical error list: a writing pass is not complete while removable filler the skill itself can identify remains. When refining author-written text, density findings in untouched sections are reported as suggestions, never silently deleted, consistent with the surgical-edit rule.

#### Scenario: Own draft carries a truism
- **WHEN** the skill's fresh draft opens a section with a general claim true of any project in the field
- **THEN** the sentence is deleted before the pass is reported complete

#### Scenario: Author's filler in an untouched section
- **WHEN** a refinement pass notices removable filler in a section the request did not touch
- **THEN** the skill reports the sentences as removable in chat and leaves the text unchanged

### Requirement: The methodology set comes from the merged guidance
The write skill SHALL take the acceptable methodologies and their required subsections from the merged guidance — shipped defaults with the workspace declaration applied — rather than from the shipped set alone. When a proposal uses a workspace-declared branch, the skill SHALL fill its subsections from the guidance that branch declares, and SHALL NOT substitute the content contract of a shipped branch with a similar name.

#### Scenario: Writing into a workspace branch
- **WHEN** the workspace declares a methodology branch and the user chooses it
- **THEN** the skill writes that branch's declared subsections and follows the guidance declared for each

#### Scenario: Disabled branch not offered
- **WHEN** the workspace has disabled a shipped methodology
- **THEN** the skill does not offer it when the methodology is chosen

