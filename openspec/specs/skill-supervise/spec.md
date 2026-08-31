# skill-supervise Specification

## Purpose
Supervisor-side feedback on raw student submissions: normalize whatever arrives, curate the most pressing findings into a draft feedback letter with a continuable artifact, and steer the student into the proposal toolchain.
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

The skill SHALL derive findings from the same sources the student-facing skills use — the mechanical check and the content-level review rubric, judged against the workspace guidelines override where one exists — and SHALL NOT introduce a separate quality rubric of its own. For the letter, the skill SHALL curate the combined findings to the three to five points that most block a viable thesis, each phrased as a direction rather than a prescribed fix. The letter SHALL name load-bearing strengths — parts that are sound and must be kept — and SHALL NOT contain generic praise.

#### Scenario: Many findings, few points
- **WHEN** check and review together yield a dozen findings
- **THEN** the letter carries at most five curated points, ranked by how much each blocks a viable thesis, and the remaining findings appear only in the professor-side review file

#### Scenario: Supervisor override respected
- **WHEN** the workspace carries a guidelines override with the professor's own requirements
- **THEN** findings are judged against the override, matching what the student-facing skills would report

#### Scenario: Strength named, flattery absent
- **WHEN** the submission contains a workable core design amid weak surroundings
- **THEN** the letter states what is sound and should be kept, and contains no generic praise of the student or the material

### Requirement: Verdict expressed as proposal state

The letter SHALL open with a verdict expressed as the state of the proposal and never as a commitment on the professor's behalf. The student-facing tiers are: **ready**, phrased as requiring no substantial revisions; **needs revision**, directing the student to address the enumerated points and resubmit; and **idea stage** (German: Ideenphase), stating that the material is an idea that has not yet reached the proposal stage. The idea-stage tier SHALL couple the standard a proposal must meet with an assurance anchored in a named, true strength of the submission and a feed-forward to ideation as the designed next step — never framed as failure, never softened into revision advice. The professor-side review file SHALL keep the review skill's blunt three-tier vocabulary unchanged.

The idea-stage tier SHALL only be assigned automatically when the failure is evidence-clear: at least three of the five substance tests fail decisively, each with a stated reason why no single revision round can repair it. When the internal review reaches no-viable-core without meeting that bar, the verdict decision SHALL be deferred to the professor rather than taken by the skill. The skill SHALL NOT promise meetings, approvals, deadlines, or any other supervisor action.

#### Scenario: Ready without commitment
- **WHEN** the submission passes review with no substantial findings
- **THEN** the letter states that no substantial revisions are needed from the reviewer's side and leaves the next step to the professor

#### Scenario: Evidence-clear idea stage
- **WHEN** at least three substance tests fail decisively and no single revision round could repair them
- **THEN** the letter opens with the idea-stage verdict, names the proposal standard, anchors an assurance in a true strength, and directs the student to ideation — without asking the professor first

#### Scenario: Blunt vocabulary stays professor-side
- **WHEN** the internal review concludes no viable thesis core
- **THEN** the review file says so in those words while the letter renders the tier as idea stage

### Requirement: Student-facing letter with disclosure and steering

The letter SHALL be the only student-facing artifact: a paste-ready draft, written professor-side as a letter file named after the proposal slug, that the professor delivers as text through their own channel — an email reply or a learning platform's feedback field. The skill SHALL NOT assemble a send-package and SHALL NOT ask the professor to attach any file. The letter SHALL be written in the language of the submission, SHALL disclose in plain language that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student — and SHALL claim no more than that: in particular no claim that the assistant follows the program's guidelines. The letter SHALL name for each curated point the skill that addresses it, and SHALL close with a getting-started blurb — maintained as a shared verbatim snippet in English and German — consisting of a single sentence that links the skill installation source and notes that the guide there assumes no prior AI-assistant experience. The blurb SHALL NOT name specific assistants, quote install commands, or prescribe the student's next step.

For idea-stage and borderline outcomes, the skill SHALL offer the professor — never run unasked — a starter-literature step: finding two or three verified relevant papers via the literature-search sibling and naming them in the letter as where the conversation already is. The offer SHALL be declined silently when the sibling is not installed or the professor does not accept; entries SHALL only ever come from real, verified lookups.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the letter, its skill pointers, and the getting-started blurb are in German

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it

#### Scenario: Disclosure is plain-language
- **WHEN** the letter is assembled
- **THEN** it states that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student, in wording that assumes no prior AI exposure and makes no claim about guideline compliance

#### Scenario: Blurb stays minimal
- **WHEN** the letter closes with the getting-started blurb
- **THEN** the blurb is the shared one-sentence snippet linking the repository, with no install command, no assistant names, and no prescribed next step

#### Scenario: Starter literature offered, not imposed
- **WHEN** the outcome is idea-stage and the literature-search sibling is installed
- **THEN** the skill offers the starter-literature step and adds papers only after the professor accepts, from verified lookups only

### Requirement: Draft-only delivery and letter separation

The skill SHALL NOT send, publish, or transmit anything; the letter SHALL be presented as a draft for the professor to edit and deliver as text through their own channel — an email reply or a learning platform's feedback field. The full review file and the normalized proposal file SHALL remain professor-side beside the letter and SHALL NOT be presented as student-facing; nothing beyond the letter text reaches the student.

#### Scenario: Run completes
- **WHEN** the skill finishes a submission
- **THEN** nothing has left the machine, and the chat summary tells the professor to review and edit the draft letter before delivering it as text through their own channel

#### Scenario: Learning-platform delivery
- **WHEN** the submission arrived through a learning platform and the professor returns feedback in that platform's feedback field
- **THEN** the letter works as pasted text with nothing to attach, and no artifact assumes an email reply

#### Scenario: Professor-only content stays out
- **WHEN** the letter is drafted
- **THEN** the blunt review vocabulary and the review file's contents are absent from it, and no send-package directory is produced

### Requirement: Borderline verdict deferred to the supervisor

When the internal review reaches no-viable-core but the evidence bar is not met, the skill SHALL pause before writing the letter and put the decision to the professor as a guided choice: a needs-revision letter emphasizing re-grounding, an idea-stage letter, or reading the professor-side review file first and deciding after. The question SHALL summarize the split evidence — which substance tests failed, which are uncertain, with a finding excerpt each — so the professor can decide without leaving the chat. Evidence-clear cases (either direction) SHALL NOT trigger the question. When the professor cannot be asked (a non-interactive run, or the user declines to decide), the skill SHALL default to the needs-revision letter — in doubt, for the student.

#### Scenario: Borderline pauses for the professor
- **WHEN** the review concludes no-viable-core but only two substance tests fail decisively
- **THEN** the skill presents the split evidence and the three choices, and writes the letter only after the professor picks

#### Scenario: Clear case skips the question
- **WHEN** the evidence bar is met
- **THEN** the letter is written without a deferral question

#### Scenario: Undecidable defaults constructive
- **WHEN** the deferral cannot be answered
- **THEN** the letter takes the needs-revision path
