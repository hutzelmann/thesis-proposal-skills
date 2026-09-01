## MODIFIED Requirements

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
