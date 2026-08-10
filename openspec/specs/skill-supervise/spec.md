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

The letter SHALL open with a verdict reusing the review skill's three tiers, expressed as the state of the proposal and never as a commitment on the professor's behalf: ready SHALL be phrased as requiring no substantial revisions, needs-revision SHALL direct the student to address the enumerated points and resubmit, and no-viable-core SHALL state honestly that the idea needs re-grounding before a proposal makes sense and SHALL redirect constructively to ideation. The skill SHALL NOT promise meetings, approvals, deadlines, or any other supervisor action, and SHALL NOT soften a no-viable-core verdict into needs-revision phrasing.

#### Scenario: Ready without commitment
- **WHEN** the submission passes review with no substantial findings
- **THEN** the letter states that no substantial revisions are needed from the reviewer's side and leaves the next step to the professor

#### Scenario: No viable core, constructive
- **WHEN** the substance tests fail in a way no in-place edit can repair
- **THEN** the letter says so plainly, without crushing phrasing, and directs the student to start with ideation using the toolchain

### Requirement: Student-facing package with disclosure and steering

The skill SHALL assemble a send-package containing the feedback letter and the normalized proposal file. The letter SHALL be written in the language of the submission, SHALL disclose in plain language that the feedback was prepared with an AI assistant, SHALL name for each curated point the skill that addresses it, and SHALL close with a getting-started blurb — maintained as a shared snippet in English and German — that links the skill installation source and tells the student to place the attached file in their workspace and continue with the writing skill.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the letter, its skill pointers, and the getting-started blurb are in German

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it

#### Scenario: Disclosure is plain-language
- **WHEN** the letter is assembled
- **THEN** it states that an AI assistant following the proposal guidelines prepared the feedback, in wording that assumes no prior AI exposure

### Requirement: Draft-only delivery and package separation

The skill SHALL NOT send, publish, or transmit anything; the letter SHALL identify itself as a draft for the professor to edit and deliver through their own channel. The full review file SHALL be written professor-side beside the slug-named proposal file and SHALL NOT be part of the send-package; the send-package SHALL contain nothing beyond the letter and the normalized proposal file.

#### Scenario: Run completes
- **WHEN** the skill finishes a submission
- **THEN** nothing has left the machine, and the chat summary tells the professor to review and edit the draft letter before sending it themselves

#### Scenario: Professor-only content stays out
- **WHEN** the send-package is assembled
- **THEN** it contains exactly the letter and the normalized proposal file — the full review file is absent
