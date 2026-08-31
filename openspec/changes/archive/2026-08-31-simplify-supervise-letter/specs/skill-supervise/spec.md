# skill-supervise delta

## RENAMED Requirements

- FROM: `### Requirement: Student-facing package with disclosure and steering`
- TO: `### Requirement: Student-facing letter with disclosure and steering`

- FROM: `### Requirement: Draft-only delivery and package separation`
- TO: `### Requirement: Draft-only delivery and letter separation`

## MODIFIED Requirements

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
