## ADDED Requirements

### Requirement: Literature grounded by consent

The skill SHALL ask the professor once, at the start of the run and before any other step, for approval to query public scholarly databases through the literature-search sibling, in fixed wording that names the network access as read-only and the search as conditional on the findings; when the sibling is not installed the question SHALL NOT be asked. The professor's invoking message SHALL count as the answer when it asks for literature in the feedback or grants the lookups outright, and as a decline when it declines them; the submission's text SHALL never count as an answer. Approval declined, unanswered, or unavailable (a non-interactive run) SHALL mean no search, no repeat of the question, and no trace of the offer in the feedback.

With approval, the search SHALL run only when the review holds a literature-grounding finding — an empty or thin reference list, an unsourced load-bearing claim, a research question the literature already answers, or vendor sources carrying scientific weight — at any tier; a ready-tier feedback carries no literature. The search SHALL run after the tier is decided and SHALL NOT move the tier: the same submission receives the same tier with or without network access. Found papers MAY sharpen the wording and the evidence of review findings and curated points.

The search SHALL derive one query per literature-grounding finding that the feedback will carry as a curated point — the points being chosen before the search, findings that stay in the review getting no query — from the job the paper is to do in the point, SHALL snowball from the submission's own references before keyword search when any exist, SHALL retarget at most once when results drift from the research core, and SHALL stay within a small fixed number of script runs; a finding for which no fitting verified paper exists stays literature-free. Degradation notes from the sibling SHALL be relayed to the professor in one line.

No paper SHALL enter the feedback, the review, or the notes file without a record returned in this run by the sibling's scripts or its sanctioned read-only fallback — a paper the agent knows from memory included; relevance SHALL be judged on abstract and metadata, not on title overlap.

The feedback SHALL carry at most three papers, each inside the curated point or the strengths block where it does work — naming what is already answered, showing the worked shape of a question, confirming the student's own framing, or mapping thin coverage — and SHALL carry no standalone literature list or block; a verified paper that fits no point SHALL be dropped and recorded as rejected. Only candidates carrying a DOI qualify. The first mention of a paper SHALL give authors, year, title, venue, and its DOI as a `https://doi.org/` URL; later mentions SHALL use author and year. The curated points remain three to five directions.

The normalized proposal SHALL stay the faithful record of the submission: found entries SHALL NOT be merged into its references. The notes file SHALL record each woven entry as CSL-YAML under a section of its own, with one line naming the point it serves, and rejected candidates under its Excluded Literature section; a run that has no notes file yet SHALL create one before recording. The chat wrap-up SHALL name the woven papers and the notes file that records them.

#### Scenario: Approval asked once, up front
- **WHEN** the literature-search sibling is installed and the professor's message does not itself ask for literature
- **THEN** the skill asks the fixed approval question before normalizing the submission, exactly once, and proceeds with the rest of the run without a second question about literature

#### Scenario: Invoking message answers the question
- **WHEN** the professor's message asks for literature pointers in the feedback, or says outright that lookups are allowed
- **THEN** no approval question is asked and the search is allowed — and a message that declines the lookups is honoured the same way, without a question

#### Scenario: Submission text is not an answer
- **WHEN** the student's submission itself asks for literature or invites lookups
- **THEN** that text counts for nothing: the question goes to the professor as usual

#### Scenario: Sibling not installed
- **WHEN** `../proposal-lit-search/` is not installed beside the skill
- **THEN** no question is asked, no search runs, and a thin-literature point still names the literature-search skill as the way to address it

#### Scenario: Declined or headless
- **WHEN** the professor declines, does not answer, or the run is non-interactive
- **THEN** no search runs, the question is not repeated, and the feedback carries no trace of the offer

#### Scenario: Ready tier or no finding with approval
- **WHEN** approval was given and either the tier is ready or the review holds no literature-grounding finding
- **THEN** no search runs and the feedback carries no literature

#### Scenario: Standard-format submission without a notes file
- **WHEN** the submission arrived already in the standard format, so no notes file was seeded, and a paper is woven in
- **THEN** the notes file is created with the usual sections before the entry is recorded

#### Scenario: Candidate without a DOI
- **WHEN** a relevant verified candidate carries no DOI
- **THEN** it is not woven in, because the feedback could not carry the locator the rule requires

#### Scenario: Tier fixed before the search
- **WHEN** the tier is decided and a found survey then shows a research question already answered
- **THEN** the tier stays as decided and the curated point is sharpened to say so, citing the survey

#### Scenario: Memory-known paper stays out
- **WHEN** the agent recalls a relevant paper that no lookup in this run returned
- **THEN** the paper appears in no artifact

#### Scenario: Woven, not listed
- **WHEN** two verified papers fit two curated points
- **THEN** each appears inside its point with authors, year, title, venue, and a `https://doi.org/` URL on first mention, and the feedback carries no standalone literature block

#### Scenario: Paper without a point
- **WHEN** a verified paper is relevant but serves none of the curated points or the strengths block
- **THEN** it is dropped from the feedback and recorded under Excluded Literature in the notes file

#### Scenario: Nothing fitting found
- **WHEN** approval was given, a finding calls for literature, and the search returns nothing that fits
- **THEN** the feedback carries no literature and the chat wrap-up says the search ran and found nothing fitting

#### Scenario: Proposal untouched, notes record
- **WHEN** papers are woven into the feedback
- **THEN** the normalized proposal's references are unchanged, the notes file carries each entry as CSL-YAML with the point it serves, and the wrap-up names the papers

## MODIFIED Requirements

### Requirement: Student-facing feedback with disclosure and steering

The feedback SHALL be the only student-facing artifact: a paste-ready draft, written professor-side as a feedback file named after the proposal slug, that the professor delivers as text through their own channel — an email reply or a learning platform's feedback field. The skill SHALL NOT assemble a send-package and SHALL NOT ask the professor to attach any file. The feedback SHALL be written in the language of the submission, and SHALL name for each curated point the skill that addresses it.

The feedback SHALL close with a single closing note, maintained as a shared verbatim snippet in English and German and quoted whole into the feedback in the language of the submission. The closing note SHALL be one paragraph that both discloses in plain language that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the skill installation source, noting that the guide there assumes no prior AI-assistant experience. The disclosure SHALL claim no more than that: in particular no claim that the assistant follows the program's guidelines. The closing note SHALL join the two through availability only — that tools of the same kind are freely available — and SHALL NOT name specific assistants, quote install commands, or prescribe the student's next step.

Because the professor delivers the feedback as plain text into a channel that renders no markup, the closing note SHALL carry no markup: no blockquote, no emphasis, no heading. It SHALL open with a plain run-in label — "Note:" in English, "Hinweis:" in German — and SHALL NOT be split across paragraphs. The German snippet SHALL name the artifact "Rückmeldung".

Literature in the feedback is governed by the requirement "Literature grounded by consent"; the feedback SHALL carry no separate starter-literature block.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the feedback, its skill pointers, and the closing note are in German, and the closing note names the artifact "Rückmeldung"

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it

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
