# skill-supervise Specification

## Purpose
Supervisor-side feedback on raw student submissions: normalize whatever arrives, curate the most pressing findings into paste-ready draft feedback, and steer the student into the proposal toolchain.
## Requirements
### Requirement: Raw submission intake and normalization

The skill SHALL accept a raw student submission in any form it is handed — PDF, Word export, pasted text, or an already-standard proposal file — and SHALL normalize non-standard input to the standard single-file proposal format with the same guarantees the import skill gives: personal data stripped, gaps marked, references carried over. The normalized file SHALL be named by an idea slug and placed in the professor's workspace beside their other proposals. The skill SHALL NOT build a student registry, SHALL NOT record student identity in any artifact it writes, and SHALL NOT manage artifact lifecycle beyond the single run — retention and deletion stay manual.

#### Scenario: Pasted email fragment
- **WHEN** the professor hands the skill half a page of pasted email text describing a thesis idea
- **THEN** the skill produces a slug-named standard-format proposal file with gaps marked, and proceeds to feedback

#### Scenario: PDF submission
- **WHEN** the professor points the skill at a submitted PDF
- **THEN** the skill runs the import pipeline, strips personal data, and continues from the resulting standard-format file

#### Scenario: No identity professor-side
- **WHEN** the submission carries the student's name, matriculation number, or contact data
- **THEN** no artifact the skill writes contains that data — the idea file is identified by slug only

### Requirement: Findings reused from check and review, curated to pressing points

The skill SHALL derive findings from the same sources the student-facing skills use — the mechanical check and the content-level review rubric, judged against the workspace guidelines override where one exists — and SHALL NOT introduce a separate quality rubric of its own. For the feedback, the skill SHALL curate the combined findings to the three to five points that most block a viable thesis, each phrased as a direction rather than a prescribed fix. The feedback SHALL name load-bearing strengths — parts that are sound and must be kept — and SHALL NOT contain generic praise.

#### Scenario: Many findings, few points
- **WHEN** check and review together yield a dozen findings
- **THEN** the feedback carries at most five curated points, ranked by how much each blocks a viable thesis, and the remaining findings appear only in the professor-side review file

#### Scenario: Supervisor override respected
- **WHEN** the workspace carries a guidelines override with the professor's own requirements
- **THEN** findings are judged against the override, matching what the student-facing skills would report

#### Scenario: Strength named, flattery absent
- **WHEN** the submission contains a workable core design amid weak surroundings
- **THEN** the feedback states what is sound and should be kept, and contains no generic praise of the student or the material

### Requirement: Verdict expressed as proposal state

The feedback SHALL open with a verdict expressed as the state of the proposal and never as a commitment on the professor's behalf. The student-facing tiers are: **ready**, phrased as requiring no substantial revisions; **needs revision**, directing the student to address the enumerated points and resubmit; and **idea stage** (German: Ideenphase), stating that the material is an idea that has not yet reached the proposal stage. The idea-stage tier SHALL couple the standard a proposal must meet with an assurance anchored in a named, true strength of the submission and a feed-forward to ideation as the designed next step — never framed as failure, never softened into revision advice. The statement that revision alone will not produce a proposal SHALL be composed in the feedback's own words and grounded in what the specific submission is missing; it SHALL NOT render the skill's instruction wording as feedback text and SHALL NOT refer to the proposal standard's elements by count or as an enumerated list. The professor-side review file SHALL keep the review skill's blunt three-tier vocabulary unchanged.

The idea-stage tier SHALL only be assigned automatically when the failure is evidence-clear: at least three of the five substance tests fail decisively, each with a stated reason why no single revision round can repair it. When the internal review reaches no-viable-core without meeting that bar, the verdict decision SHALL be deferred to the professor rather than taken by the skill. The skill SHALL NOT promise meetings, approvals, deadlines, or any other supervisor action.

#### Scenario: Ready without commitment
- **WHEN** the submission passes review with no substantial findings
- **THEN** the feedback states that no substantial revisions are needed from the reviewer's side and leaves the next step to the professor

#### Scenario: Evidence-clear idea stage
- **WHEN** at least three substance tests fail decisively and no single revision round could repair them
- **THEN** the feedback opens with the idea-stage verdict, names the proposal standard, anchors an assurance in a true strength, and directs the student to ideation — without asking the professor first

#### Scenario: Plainness statement in the feedback's own words
- **WHEN** an idea-stage feedback states that revision alone will not produce a proposal
- **THEN** the statement names what this submission is missing in the feedback's own words, rather than translating the skill's instruction sentence or pointing at the standard's elements by count

#### Scenario: Blunt vocabulary stays professor-side
- **WHEN** the internal review concludes no viable thesis core
- **THEN** the review file says so in those words while the feedback renders the tier as idea stage

### Requirement: Student-facing feedback with disclosure and steering

The feedback SHALL be the only student-facing artifact: a paste-ready draft, written professor-side as a feedback file named after the proposal slug, that the professor delivers as text through their own channel — an email reply or a learning platform's feedback field. The skill SHALL NOT assemble a send-package and SHALL NOT ask the professor to attach any file. The feedback SHALL be written in the language of the submission, and SHALL name for each curated point the skill that addresses it.

The feedback SHALL close with a single closing note, maintained as a shared verbatim snippet in English and German and quoted whole into the feedback in the language of the submission. The closing note SHALL be one paragraph that both discloses in plain language that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the skill installation source, noting that the guide there assumes no prior AI-assistant experience. The disclosure SHALL claim no more than that: in particular no claim that the assistant follows the program's guidelines. The closing note SHALL join the two through availability only — that tools of the same kind are freely available — and SHALL NOT name specific assistants, quote install commands, or prescribe the student's next step.

Because the professor delivers the feedback as plain text into a channel that renders no markup, the closing note SHALL carry no markup: no blockquote, no emphasis, no heading. It SHALL open with a plain run-in label — "Note:" in English, "Hinweis:" in German — and SHALL NOT be split across paragraphs. The German snippet SHALL name the artifact "Rückmeldung".

For idea-stage and borderline outcomes, the skill SHALL offer the professor — never run unasked — a starter-literature step: finding two or three verified relevant papers via the literature-search sibling and naming them in the feedback as where the conversation already is. The offer SHALL be declined silently when the sibling is not installed or the professor does not accept; entries SHALL only ever come from real, verified lookups.

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
- **THEN** the skill offers the starter-literature step and adds papers only after the professor accepts, from verified lookups only

### Requirement: Draft-only delivery and feedback separation

The skill SHALL NOT send, publish, or transmit anything; the feedback SHALL be presented as a draft for the professor to edit and deliver as text through their own channel — an email reply or a learning platform's feedback field. The full review file and the normalized proposal file SHALL remain professor-side beside the feedback file and SHALL NOT be presented as student-facing; the review file SHALL be presented under its own name — the review — and never described as feedback; nothing beyond the feedback text reaches the student.

#### Scenario: Run completes
- **WHEN** the skill finishes a submission
- **THEN** nothing has left the machine, and the chat summary tells the professor to review and edit the feedback draft before delivering it as text through their own channel

#### Scenario: Learning-platform delivery
- **WHEN** the submission arrived through a learning platform and the professor returns feedback in that platform's feedback field
- **THEN** the feedback works as pasted text with nothing to attach, and no artifact assumes an email reply

#### Scenario: Review never wears the feedback name
- **WHEN** the chat summary or any artifact refers to the professor-side review file
- **THEN** it is called the review, never the feedback, so the professor cannot mistake it for the text to paste

#### Scenario: Professor-only content stays out
- **WHEN** the feedback is drafted
- **THEN** the blunt review vocabulary and the review file's contents are absent from it, and no send-package directory is produced

### Requirement: Borderline verdict deferred to the supervisor

When the internal review reaches no-viable-core but the evidence bar is not met, the skill SHALL pause before writing the feedback and put the decision to the professor as a guided choice: needs-revision feedback emphasizing re-grounding, idea-stage feedback, or reading the professor-side review file first and deciding after. The question SHALL summarize the split evidence — which substance tests failed, which are uncertain, with a finding excerpt each — so the professor can decide without leaving the chat. Evidence-clear cases (either direction) SHALL NOT trigger the question. When the professor cannot be asked (a non-interactive run, or the user declines to decide), the skill SHALL default to the needs-revision feedback — in doubt, for the student.

#### Scenario: Borderline pauses for the professor
- **WHEN** the review concludes no-viable-core but only two substance tests fail decisively
- **THEN** the skill presents the split evidence and the three choices, and writes the feedback only after the professor picks

#### Scenario: Clear case skips the question
- **WHEN** the evidence bar is met
- **THEN** the feedback is written without a deferral question

#### Scenario: Undecidable defaults constructive
- **WHEN** the deferral cannot be answered
- **THEN** the feedback takes the needs-revision path

### Requirement: Level-calibrated feedback bar
The drafted feedback SHALL be calibrated to the degree level the submission's subtitle states: a Master's proposal missing a statement of what will be new is always asked for one; a Bachelor's proposal is never asked for a novelty claim, and one it makes is engaged on its merits rather than removed. The same calibration applies to research-question origin, literature stance, and scope-for-the-months. When the submission does not state a level, the draft SHALL apply the level-independent bar and note the unset level once — as a point for the student, not a guess.

#### Scenario: Master submission missing the delta
- **WHEN** a submission subtitled as a Master's thesis promises only competent application in its contribution close
- **THEN** the drafted letter asks for the statement of what the thesis will add

#### Scenario: Bachelor submission held to its own bar
- **WHEN** a submission subtitled as a Bachelor's thesis has a bounded application promise and level-appropriate derived research questions
- **THEN** the drafted letter raises no novelty demand and no research-question-origin concern

#### Scenario: Level unset in the submission
- **WHEN** the submission's subtitle matches no canonical wording
- **THEN** the draft judges against the level-independent bar and includes one line asking the student to state the degree level in the subtitle
