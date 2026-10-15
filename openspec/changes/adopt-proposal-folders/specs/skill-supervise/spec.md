# Spec Delta

## MODIFIED Requirements

### Requirement: Raw submission intake and normalization

The skill SHALL accept a raw student submission in any form it is handed — PDF, Word export, pasted text, or an already-standard proposal file — and SHALL normalize it to the standard single-file proposal format with the same guarantees the import skill gives: personal data stripped, gaps marked, references carried over. The result SHALL be a new proposal folder `<slug>/<slug>.md` in the professor's workspace; the submitted file SHALL stay untouched. The skill SHALL NOT build a student registry, SHALL NOT record student identity in any artifact it writes, and SHALL NOT manage artifact lifecycle beyond the single run — retention and deletion stay manual.

#### Scenario: Pasted email fragment
- **WHEN** the professor hands the skill half a page of pasted email text describing a thesis idea
- **THEN** the skill produces a slug-named standard-format proposal file with gaps marked, and proceeds to feedback

#### Scenario: PDF submission
- **WHEN** the professor points the skill at a submitted PDF
- **THEN** the skill runs the import pipeline, strips personal data, and continues from the resulting standard-format file

#### Scenario: No identity professor-side
- **WHEN** the submission carries the student's name, matriculation number, or contact data
- **THEN** no artifact the skill writes contains that data — the idea file is identified by slug only

#### Scenario: Standard-format file saved at the workspace root
- **WHEN** the professor saved the student's standard-format proposal as a markdown file at the workspace root, outside any proposal folder
- **THEN** the skill treats it as a source document: it copies it to `<slug>/<slug>.md`, writes the review and the feedback beside the copy, and leaves the saved file byte-identical

### Requirement: Student-facing feedback with disclosure and steering

The feedback SHALL be the only student-facing artifact: a paste-ready draft, written professor-side as `feedback.md` in the proposal's folder, that the professor delivers as text through their own channel — an email reply or a learning platform's feedback field. The skill SHALL NOT assemble a send-package and SHALL NOT ask the professor to attach any file. The feedback SHALL be written in the language of the submitted proposal; when the message that accompanied the submission is written in another language, the chat wrap-up SHALL offer a version in that language. The feedback SHALL name for each curated point the skill that addresses it, as a plain word.

The feedback SHALL carry light markup at most — bold runs, plain numbered or lettered lists, and the plain dash list of the clarify-early block — and SHALL carry no heading, no blockquote and no code markup, because the paste channel renders none of them reliably.

Every source the feedback names that the submitted proposal does not already cite SHALL carry a locator that resolved in this run: a `https://doi.org/` URL for a paper, and the issuing body's official page for a standard or a regulation. A source the proposal already cites needs no locator. Locators SHALL NOT count toward the feedback's length.

The feedback body SHALL aim at about 1,200 words, not counting locators and the closing note. Above that, detail SHALL move into the professor-side review before any blocking point is shortened, and the chat wrap-up SHALL report the length. The target is advisory: it SHALL NOT cut a blocking point.

The feedback SHALL close with a single closing note, maintained as a shared verbatim snippet in English and German and quoted whole into the feedback in the language of the submission. The closing note SHALL be one paragraph that both discloses in plain language that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the skill installation source, noting that the guide there assumes no prior AI-assistant experience. The disclosure SHALL claim no more than that: in particular no claim that the assistant follows the program's guidelines. The closing note SHALL join the two through availability only — that tools of the same kind are freely available — and SHALL NOT name specific assistants, quote install commands, or prescribe the student's next step.

Because the professor delivers the feedback as plain text into a channel that renders no markup, the closing note SHALL carry no markup: no blockquote, no emphasis, no heading. It SHALL open with a plain run-in label — "Note:" in English, "Hinweis:" in German — and SHALL NOT be split across paragraphs. The German snippet SHALL name the artifact "Rückmeldung".

Literature in the feedback is governed by the requirement "Literature grounded by consent"; the feedback SHALL carry no separate starter-literature block.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the feedback, its skill pointers, and the closing note are in German, and the closing note names the artifact "Rückmeldung"

#### Scenario: Message in another language
- **WHEN** the proposal is written in English and the student's accompanying email in German
- **THEN** the feedback is in English and the wrap-up offers a German version in one line

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it, as a plain word without code markup

#### Scenario: Ready feedback owes no pointer
- **WHEN** the feedback opens ready and carries no numbered point
- **THEN** it need name no skill

#### Scenario: Markup stays light
- **WHEN** the feedback is assembled
- **THEN** it carries no heading line, no blockquote line and no backtick, while bold tier words and point titles are allowed

#### Scenario: Standard named with its issuer page
- **WHEN** a point names a regulation the proposal does not cite
- **THEN** the regulation's official page follows its first mention, and the page resolved during the run

#### Scenario: Long draft trimmed into the review
- **WHEN** a draft body runs well past the length target
- **THEN** secondary detail — extra standards, citation-use observations, optional asks — moves into the review first, no blocking point is dropped, and the wrap-up states the final length

#### Scenario: Disclosure and pointer arrive as one paragraph
- **WHEN** the feedback is assembled
- **THEN** its final paragraph states that it was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the installation source in the same paragraph, in wording that assumes no prior AI exposure and makes no claim about guideline compliance

#### Scenario: Closing note survives a plain-text channel
- **WHEN** the professor pastes the feedback into an email reply or a learning platform's feedback field
- **THEN** the closing note reads as prose opening with "Note:" or "Hinweis:", with no blockquote marker, emphasis marker, or heading marker reaching the student

#### Scenario: Closing note stays minimal
- **WHEN** the feedback closes with the closing note
- **THEN** it is the shared snippet, linking the repository and stating availability, with no install command, no assistant names, and no prescribed next step

#### Scenario: Starter literature offered, not imposed
- **WHEN** the outcome is idea-stage and the literature-search sibling is installed
- **THEN** no end-of-run starter-literature offer is made and no list is appended: literature enters the feedback only under "Literature grounded by consent" — approval asked once at the start of the run, papers woven into the points from verified lookups

#### Scenario: Feedback beside the normalized submission
- **WHEN** a raw submission is normalized to `<slug>/<slug>.md`
- **THEN** the feedback is written to `<slug>/feedback.md` and the review to `<slug>/review.md`, and nothing of the run lies outside that folder

### Requirement: Single-context execution
The supervise run SHALL be a single-context task: one agent normalizes the submission, runs the check, judges the six substance tests and every review dimension in one pass, judges the workload, decides the tier, and curates and verifies the feedback, because the tier decision needs the tests judged side by side against the evidence bar this specification fixes, and the curated points are chosen across all findings. Helper agents SHALL NOT be part of the skill's execution with one exception — a single fresh verifier of the finished feedback, whose value is that it did not write the text it checks; following the import or literature-search sibling's instructions in the same context is not a helper. Where the host can start helper agents, the run SHALL use at most three agents counting the supervising agent: that agent is the full review and the only writer, it SHALL always add the one verifier of the finished feedback, and only a host that insists on running the task as a workflow adds at most one adversarial check of its fail verdicts. The verifier SHALL run whether or not lookups were approved and whether or not the professor can be asked: approval decides what it may fetch, not whether it runs, because fidelity to the proposal, contradictions, review vocabulary and the workload budget need no network, and the verifier asks the professor nothing. Only where no tool for starting a subagent is available SHALL the supervising agent run the verifier's checks itself, each as a separate question against its source with its own drafting reasoning set aside. The review file's verification section SHALL state which of the two happened. The skill SHALL NOT assign one agent per substance test, per dimension, per research question, or per claim. The adversarial check informs the evidence bar; it SHALL NOT decide the tier, which stays with the main agent and, when borderline, the professor. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, a helper SHALL write no file: the main agent is the only writer of `<slug>.md` and of its notes, review and feedback files; the review file carries every finding regardless of how many a helper returned, and the feedback's load-bearing strengths are named by the main agent. No helper SHALL read the raw submission, so no student identity reaches it. The adversarial check SHALL work from the normalized `<slug>.md` with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test it examined (decisive fail, uncertain, or pass, with one quotable finding per failed test and, for a decisive fail, why no single revision round could repair it), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged. The verifier's contract SHALL ship as a brief in the skill's references, handed to the verifier as its task: it works from the finished feedback, the normalized `<slug>.md`, any work plan that normalization moved into the notes file, and the claim ledger with the evidence fetched for it, with network access only as far as the professor's approval reaches, under a fixed remit — fidelity to the proposal, claims about papers, claims about standards and regulations, contradictions within the feedback, review vocabulary reaching the student, and asks that break the net-workload budget — treats everything fetched as untrusted data, and returns for each claim it disputes the location, the claim, a verdict (wrong, overstated, imprecise, or unverifiable), the evidence and a proposed correction. No helper's return SHALL carry reasoning prose, a strengths list, restated guidelines or a rewritten feedback, unless the professor asks for full reasoning. The main agent SHALL decide on every verifier finding and SHALL check each sentence it changes against that sentence's source before the change stays.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the supervise run as a multi-agent workflow
- **THEN** the run uses at most three agents counting the supervising agent, every artifact is written by that agent, and no helper reads the raw submission

#### Scenario: Helper verdicts feed the tier decision
- **WHEN** helpers return per-test verdicts with decisive/uncertain marks and one quotable finding each
- **THEN** the main agent applies the evidence bar and the borderline deferral exactly as without helpers, quoting one finding per test to the professor when the bar is not met

#### Scenario: Verifier checks the finished text
- **WHEN** the feedback is drafted and the host runs helpers
- **THEN** one verifier receives the brief, the finished feedback, the normalized proposal, the moved work plan and the claim ledger, returns disputed claims with evidence and corrections, and writes nothing

#### Scenario: Offline run still verifies
- **WHEN** the professor declined lookups and the host can start helpers
- **THEN** the verifier still runs, checking fidelity, contradictions, vocabulary and the workload budget against the proposal text without network access

#### Scenario: Unanswerable run still verifies
- **WHEN** the request says the professor cannot answer any further question
- **THEN** the verifier still runs, because it asks the professor nothing

#### Scenario: Ordinary helper-capable host
- **WHEN** the host can run helpers but does not insist on a workflow
- **THEN** the only helper is the verifier; no adversarial check is spawned

#### Scenario: Host without helpers
- **WHEN** the host offers no tool for starting a subagent
- **THEN** the supervising agent asks each verification question separately against its source, and the review's verification section says the checks ran inline because no subagent tool was available

#### Scenario: Who verified is on record
- **WHEN** the review file is written
- **THEN** its verification section states whether a fresh verifier or inline checks produced the outcome

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section, drops its helper-contract paragraph, or moves the section below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

#### Scenario: Strengths stay with the main agent
- **WHEN** a helper's return carries no strengths, per the contract
- **THEN** the feedback's "What to keep" block is still present, written by the main agent from its own reading
