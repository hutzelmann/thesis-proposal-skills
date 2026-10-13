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

When applying a review, the skill SHALL work through the review's proposal blockers and optional refinements item by item in the proposal, reporting per item what changed or why it was skipped, and SHALL record each clarify-early item — with its deferral record — under the notes file's Open Points instead of writing it into the proposal. A clarify-early item SHALL enter the proposal text only when the author asks for that item there; the skill SHALL NOT add a section, a work plan or protocol detail to carry such items.

#### Scenario: Improve research questions only
- **WHEN** the user asks to improve the research questions
- **THEN** only the research-question section (and directly dependent methodology references) changes

#### Scenario: Review applied without protocol creep
- **WHEN** the user asks to apply a review whose clarify-early section lists the exact model versions and the audit sample size
- **THEN** the proposal text gains neither, both are recorded under the notes file's Open Points with their deferral records, and the blockers and refinements are applied in the proposal

#### Scenario: Author asks for a deferred item in the text
- **WHEN** the author asks to state the model-selection rule in the methodology
- **THEN** the skill writes that one sentence and records nothing more of the item in the proposal

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

Correcting markup remains permitted where markup is the actual defect — a code identifier in prose is marked as code. Rewording the author's terminology, and deleting a reference, a citation or a sentence, SHALL NOT be used to silence a finding the skill believes is wrong: that trades a wrong finding for a real defect. The skill SHALL name the finding it is leaving, state why it is wrong, and name the troubleshoot skill as the route to a bug report.

An uncited-reference finding SHALL have exactly two admissible resolutions, and the skill SHALL choose between them on whether the proposal has a claim that needs the entry: cite the entry where a claim genuinely rests on it, or remove it from the `references:` block and record it in the notes file's Excluded Literature section with a one-line reason. Removing an entry no claim needs is a correct resolution of the finding and SHALL NOT be treated as the silencing the preceding paragraph forbids, which concerns findings the skill judges wrong. The skill SHALL NOT resolve the finding by writing a sentence whose purpose is to carry the citation: a sentence that exists so that an entry is cited fails the guidance's necessity test, and producing one trades a warning for a substance defect. Where no notes file exists, the removal is reported in chat instead, and the skill SHALL NOT create the notes file for this purpose alone.

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

#### Scenario: Uncited reference no claim needs
- **WHEN** the check warns that a merged reference is defined but never cited, and no research question, delta statement, or method step in the proposal rests on it
- **THEN** the skill removes the entry from `references:`, records it in Excluded Literature with a one-line reason, and reports the removal — and no new sentence citing that entry appears in the proposal

#### Scenario: Uncited reference a claim does need
- **WHEN** the check warns that a merged reference is uncited and the proposal already carries a claim that rests on it
- **THEN** the skill cites the entry at that claim rather than removing it

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
When a companion `<slug>.notes.md` exists for the target proposal, the write skill SHALL read it before drafting and honor its content: recorded decisions steer the draft (they are not re-litigated), and the Next Focus section informs which gaps to work on first. Decisions the writing session itself produces SHALL be recorded in the notes Decisions section. When the session resolves a proposal `[TODO: …]` marker, the skill SHALL move it to the notes Log as a done entry rather than deleting it. When no notes file exists, the skill SHALL proceed as before and MAY create one only when it has decisions, clarify-early items from an applied review, or markers the user approved moving to record — never an empty skeleton.

#### Scenario: Prior decision honored
- **WHEN** the notes Decisions section records that a user study was rejected in favor of a prototype implementation
- **THEN** the draft builds on the prototype methodology and the skill does not re-open the methodology question

#### Scenario: Resolved marker logged
- **WHEN** the writing session fills the gap behind a proposal TODO marker
- **THEN** the marker is removed from the proposal and appears in the notes Log as done, with a note of what resolved it

#### Scenario: No notes file present
- **WHEN** the target proposal has no companion notes file and the session makes no recordable decision
- **THEN** the skill writes the proposal as usual and creates no notes file

#### Scenario: Notes file created for deferred items
- **WHEN** the target proposal has no notes file and an applied review carries clarify-early items
- **THEN** the skill creates the notes file with its five canonical sections and records the items under Open Points

#### Scenario: Notes file created for approved marker moves
- **WHEN** the target proposal has no notes file and the user approves moving three execution-detail markers out of it
- **THEN** the skill creates the notes file with its five canonical sections and records the three under Open Points with their deferral records

### Requirement: Title negotiated once research questions exist
The skill SHALL judge the proposal's title against the guidance once the research questions are written, including a title inherited unchanged from an ideation seed, and SHALL NOT treat an inherited title as settled. Where the title matches an alarm class, the skill SHALL raise it in chat, state that the title is printed on the study certificate, and offer between one and three abstracted alternatives naming the contribution and its object. The skill SHALL write the student's chosen title, never a silent replacement, and where a named technology is retained the skill SHALL have the student's stated reason why the research depends on it, typically that the technology is the object of study. The skill SHALL write that reason into the contribution or the research questions, as the substance gate requires for named choices, and SHALL treat the title as settled for the session only once the proposal carries it; a name kept without a reason SHALL carry the substance gate's `[TODO: …]` marker.

#### Scenario: Seed title inherited unchanged
- **WHEN** the draft is written from a seed whose working title names a product carried as the instrument
- **THEN** the skill raises the title, names the certificate consequence, and offers abstracted alternatives before reporting the draft finished

#### Scenario: Student picks an alternative
- **WHEN** the student chooses one of the offered titles
- **THEN** the leading `# ` line carries that title and the slug is left alone unless the student asks for a rename

#### Scenario: Student keeps a named technology
- **WHEN** the student states that the named technology is the object of study
- **THEN** the title is written as the student chose it, the reason is written into the contribution or the research questions, and the point is not raised again in that session

#### Scenario: Student keeps a named technology without a reason
- **WHEN** the student keeps a named technology in the title and gives no reason why the research depends on it
- **THEN** the title is written as the student chose it and the contribution carries the substance gate's TODO marker asking for the dependence

#### Scenario: Title already academic
- **WHEN** the title names a contribution and its object with no alarm class matched
- **THEN** the skill leaves it alone and spends no turn on it

### Requirement: Substance gate
Where the collected material (seed, notes, user input, references) does not support a substantive statement, the skill SHALL NOT generate generic prose to fill the gap: the gap becomes a visible `[TODO: …]` marker or the affected content is omitted, and the closing report SHALL state plainly which sections rest on thin material and point to the ideation skill (for missing idea substance) or the review skill (for the substance verdict). Text the skill generates SHALL be traceable to the material; well-sounding filler that would survive the guidance's swap test in reverse — text equally true of any thesis in the area — SHALL NOT be written.

The gate SHALL cover named choices as the guidance's swap test defines them. The skill SHALL NOT introduce a tool, system, platform or application domain into the title, the purpose statement, the research focus, a research question or the contribution's statements of what the thesis adds, unless the material states what the research depends on in it. Where the author's material names one there without that dependence, the skill SHALL keep the name and SHALL place a visible `[TODO: …]` marker asking for the dependence where the contribution would state it. It SHALL NOT invent the dependence. The closing report SHALL name the open swap-test blocker with its two repairs: state the dependence, or generalize the claim. Where the student states the dependence in the session — for instance as the reason for keeping a named technology in the title — the skill SHALL write it into the contribution or the research questions, so that the proposal carries it.

#### Scenario: Hollow seed drafted honestly
- **WHEN** the seed carries a topic phrase but no delta, no object of study, and no method substance
- **THEN** the drafted sections carry TODO markers for the missing substance, no generic filler prose is produced, and the closing report names the gaps

#### Scenario: Material supports the section
- **WHEN** the notes record a concrete evaluation design for the methodology section
- **THEN** the skill writes the section from that material without any substance TODO

#### Scenario: Decorative name in the seed
- **WHEN** the seed's working title and research-question directions name an agent framework, and neither the seed nor the notes say what the research depends on in it
- **THEN** the draft keeps the name, carries a TODO marker in the contribution section asking for the dependence, and the closing report names the open swap-test blocker with both repairs

#### Scenario: Implementation choice stays in the method
- **WHEN** the notes record that the prototype is built with a particular library and nothing else ties the research to it
- **THEN** the skill names the library in the methodology only, and introduces it into no title, research question or contribution statement

#### Scenario: Reason given in the session
- **WHEN** the student says the named framework stays in the title because the thesis evaluates its default configuration for the teams that run it
- **THEN** the skill writes that dependence into the contribution section rather than leaving it in the chat

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

### Requirement: Level-aware contribution close and research questions
The skill SHALL read the degree level from the subtitle wording — the same inference path as language, no other source — and honor it when drafting the contribution section's close and the research questions: at Master's level the close names what will be new and for whom; at Bachelor's level a promise to apply or evaluate something competently in a named setting is a complete close, and the skill SHALL NOT push a novelty claim into it, while preserving one the author states. Research questions follow the same grading: deriving them from a given topic is level-appropriate at Bachelor's level; at Master's level they are grounded in the gap the contribution section argues. When the subtitle carries a TODO marker, the skill SHALL ask for the level exactly once, at the moment it first drafts the contribution close, and SHALL proceed level-neutrally if the author declines.

#### Scenario: Master close without a novelty claim
- **WHEN** the subtitle declares a Master's thesis and the drafted contribution close only promises competent application
- **THEN** the skill raises the missing statement of what will be new before considering the section complete

#### Scenario: Bachelor close not pushed toward novelty
- **WHEN** the subtitle declares a Bachelor's thesis and the author's close promises a competent evaluation in a named setting
- **THEN** the skill treats the close as complete and adds no novelty demand

#### Scenario: Level TODO triggers one deferred question
- **WHEN** the subtitle is a TODO marker and the skill reaches the contribution close
- **THEN** it asks for the degree level once, writes the canonical subtitle on an answer, and continues level-neutrally without repeating the question if the author declines

### Requirement: One writer per file

A writing pass SHALL be performed by one agent in one context: the canonical sections are drafted in sequence, review findings are applied item by item by the same agent, and the density pass reads the whole file. The skill SHALL NOT spawn one helper agent per section or per review finding, because parallel edits to one file break the surgical-edit rule, the `(RQn)` cross-references, and the whole-file density pass. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would draft the five sections or apply a review's findings through parallel helpers
- **THEN** the pass is written by one agent in sequence, and the file is never edited by more than one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

### Requirement: Citation scope in writing passes
When drafting prior work, the skill SHALL group sources by the claim they support and compare them, and SHALL cite each source once per continuous use: the run opens with the author-in-text form, the following sentences refer back in words, and the source is cited again at a new paragraph, after another source or a claim of the thesis's own, and wherever a sentence would otherwise read as the thesis's own claim. These triggers are the guidance's. The skill SHALL NOT narrow them. Like the guidance's other writing rules, they are a default a workspace `guidelines.md` may override, for example where a program requires a citation on every sentence that draws on a source.

In a writing pass, the skill SHALL treat the check's repeated-citation warning as binding, the way it treats an error, unless the workspace guidance requires per-sentence citation. It SHALL resolve each warning by opening the run with the author-in-text form and referring back in words, or by merging the sentences into the comparison the paragraph is for. The skill SHALL NOT resolve the warning by deleting a citation or by dropping a source, because a sentence that loses its citation without a back-reference reads as the thesis's own claim. When refining, the surgical-edit rule governs this warning as it governs the density pass: findings in sections the request did not touch SHALL be reported as suggestions rather than rewritten.

#### Scenario: Several findings from one source
- **WHEN** the material supplies several findings from one publication
- **THEN** the draft cites it once at the start of the run and carries the following findings with back-references such as "they" or "their evaluation"

#### Scenario: Repeated-citation warning in a writing pass
- **WHEN** the check reports that a sentence in text the pass wrote or was asked to improve repeats the citation of the sentence before it
- **THEN** the skill rewrites the run before reporting the pass, and every source the paragraph cited is still cited

#### Scenario: Deletion is not a resolution
- **WHEN** removing the repeated citation would leave the sentence without a citation or a back-reference to its source
- **THEN** the skill adds the back-reference or keeps the citation instead of leaving the sentence unattributed

#### Scenario: Untouched section in a refinement
- **WHEN** a refinement asked for one section and the check reports repeated citations in another
- **THEN** the skill reports those findings as suggestions and leaves the untouched section as written

#### Scenario: Workspace requires per-sentence citation
- **WHEN** the workspace `guidelines.md` requires every sentence that draws on a source to carry its citation
- **THEN** the skill follows the workspace and does not treat the repeated-citation warning as binding

### Requirement: Writing pass hands over

A writing pass SHALL report what changed, what the check still reports and which markers remain, and SHALL close with the stage handoff (skill-packaging). Its route SHALL follow from what the pass changed, the first that applies:

- a decision the pass could not settle, which the student owes the proposal → that decision as an anchored choice, before any review, since a review would only raise it again;
- a pass that changed the research questions, the scope, the method, the contribution delta, or a passage a blocker of the review beside the proposal cites → that review is superseded, and the recommended step is a fresh review of the changed text;
- a complete draft with no review beside it → a review;
- a pass that changed wording only, beside a review that still covers the text with no blocker → the final check before the hand-in build;
- a reference shortfall the check reports → a literature search, recommended or as the alternative depending on whether it is what blocks the next milestone.

The skill SHALL NOT run a review, build or publish within the pass. Open `[TODO: …]` markers SHALL be sorted in the handoff into decisions the student owes the proposal and execution details whose deferral record (guidance-model, Readiness) can be filled. The decisions are what blocks the next milestone and are put as anchored decisions; the execution details MAY be proposed for the notes file's Open Points. Moving one is a writing step taken only on the user's approval: the marker leaves the proposal, its deferral record enters Open Points, and the Log records the move. A marker SHALL NOT otherwise be deleted to satisfy the check.

#### Scenario: Blockers applied
- **WHEN** the user asks to apply a review's blockers and the pass rewrites the passages they cite
- **THEN** the handoff says the review on file describes the earlier text and recommends a fresh review, and the review file is left unchanged

#### Scenario: Scope narrowed
- **WHEN** a pass reduces four research questions to two
- **THEN** the handoff recommends a fresh review of the narrowed draft, not merely that no current review exists

#### Scenario: Wording-only pass after a ready review
- **WHEN** a polishing pass changes sentences but no research question, scope, method, delta or blocker passage, and the review beside the proposal is ready
- **THEN** the handoff recommends the final check before the hand-in build, not another review

#### Scenario: Markers sorted after a first draft
- **WHEN** a first draft leaves a marker for the start month, one for whether indispensable data access is guaranteed, and three for model versions, audit sample size and log format
- **THEN** the handoff names the first two as decisions that block the next milestone and proposes moving the other three into the notes file, and no marker is moved in that pass

#### Scenario: Move approved
- **WHEN** the user approves moving the three execution-detail markers
- **THEN** they leave the proposal, each enters Open Points with its deferral record, and the Log records the move
