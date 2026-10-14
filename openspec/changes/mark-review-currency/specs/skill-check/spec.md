## ADDED Requirements

### Requirement: Review currency warning
The deterministic script SHALL read the review file the review skill writes for the checked proposal (skill-review, Persisted, actionable output; proposal-file-format, Proposal family under one handle), and no other file for this purpose. When that review carries a research-questions record (skill-review, Research questions recorded in the review), the script SHALL compare the record with the research questions the proposal currently declares. This read is part of the check's read-only run: the script SHALL NOT write to the review.

The proposal's questions SHALL be the items of the ordered list in its research-questions section, found exactly as the research-question count rule finds them. The record's questions SHALL be the items, ordered or bulleted, of the first list under the last heading in the review titled `Research questions reviewed` or `Begutachtete Forschungsfragen` — either title whatever the proposal's language, at any heading level, in any letter case. That list SHALL end at the next heading, at a thematic break, or at the first line after a blank line that is neither a list item nor indented, so text below the record, list-shaped or not, never counts as a recorded question. On both sides an item SHALL start at an unindented list marker of the kind that side accepts and run to the next such marker, a blank line, or the section's end; indented lines, nested list items included, continue it. Both sides SHALL be compared item by item, in order, after removing every invisible format character (Unicode general category Cf, such as the soft hyphen, the zero-width space, the word joiner and the byte-order mark), normalizing Unicode compatibility forms, collapsing every run of whitespace, line breaks included, into one space, and folding typographic variants to one form each: straight and curly single quotes, including their low-9 and reversed forms, to one single quote; straight and curly double quotes, including their low-9 and reversed forms, to one double quote; and the hyphen-minus, hyphen, non-breaking hyphen, en dash, em dash and minus sign to one dash. List-marker style, numbering, invisible format characters, and which of those quote or dash variants is used SHALL NOT count; wording, letter case, every other punctuation mark and order SHALL.

When the two lists differ, the script SHALL report exactly one warning carrying the stable identifier `review-questions-changed`. Its message SHALL name the review file and each position that differs, as changed, added or removed (for example `RQ4 removed`), SHALL say that the review may describe an earlier version of the proposal, and SHALL say that a fresh review replaces it while the review file is left as it is, so an agent that runs the check after its own pass is never steered into editing the record or reverting a question to silence the warning. It SHALL NOT quote any question's text, so a report that leaves the workspace carries no proposal wording through it. The finding SHALL be a warning, never an error: it SHALL NOT change the exit code in either output mode, and the reported digest SHALL continue to identify the proposal file alone.

The script SHALL report nothing about the review when:

- no review file exists;
- the review cannot be read, or cannot be read as UTF-8 text;
- the review carries no record, or a record with no list item — every review written before the record existed included;
- the proposal declares no ordered-list research question, which other findings already cover.

The review file SHALL never cause the script to fail.

When the user asks where the proposal stands, the check skill SHALL take this warning as settling the research-question part of its judgement whether the review still covers the text: any `review-questions-changed` warning means the review judged other research questions and is superseded, whatever the size of the difference, and the routes treat it as a superseded review (a fresh review once no earlier route applies). A review without a record SHALL be judged from its content, as before.

#### Scenario: Scope narrowed after the review
- **WHEN** the review's record lists four research questions and the proposal now declares the first three of them unchanged
- **THEN** the check reports one `review-questions-changed` warning naming RQ4 as removed, and the exit code is the one the proposal's other findings give

#### Scenario: Question reworded
- **WHEN** the record's second question differs from the proposal's second question in one word
- **THEN** the warning names RQ2 as changed and its message contains neither version of the question

#### Scenario: Same questions, different layout
- **WHEN** the record lists the proposal's questions with different line wrapping, bullet markers instead of numbers, and non-breaking spaces where the proposal has plain ones
- **THEN** no review finding is reported

#### Scenario: Quotes and dashes typeset differently
- **WHEN** the record has straight quotes and a hyphen-minus where the proposal's questions have curly quotes and an en dash, and the wording is otherwise identical
- **THEN** no review finding is reported

#### Scenario: Invisible format characters
- **WHEN** a proposal's question carries a soft hyphen inside a word and the record copies it without one, or the record carries a zero-width space the proposal's question lacks, and the wording is otherwise identical
- **THEN** no review finding is reported

#### Scenario: Letter case changed
- **WHEN** the record's first question differs from the proposal's first question only in the case of one letter
- **THEN** the warning names RQ1 as changed

#### Scenario: Nested item stays inside its question
- **WHEN** the proposal declares three research questions, the second continuing on an indented sub-bullet, and the record copies all three with the same sub-bullet beneath the second
- **THEN** no review finding is reported, and the count rule still counts three research questions

#### Scenario: Review written before the record existed
- **WHEN** a review beside the proposal carries verdict and findings but no record section
- **THEN** no review finding is reported

#### Scenario: Notes below the record
- **WHEN** the review's record matches the proposal's questions and is followed, without a heading of its own, by a paragraph of notes with a bulleted list, or by a thematic break
- **THEN** no review finding is reported

#### Scenario: German record beside an English proposal
- **WHEN** the record is titled `## Begutachtete Forschungsfragen` and lists exactly the questions of an English proposal
- **THEN** no review finding is reported

#### Scenario: Review that cannot be read
- **WHEN** a directory, or a file that is not valid UTF-8, stands at the review's path
- **THEN** no review finding is reported, the script completes, and the exit code is the one the proposal's findings give

#### Scenario: Status asked after a narrowing
- **WHEN** the user asks where the proposal stands and the script reports `review-questions-changed`
- **THEN** the handoff says the review judged other research questions and recommends a fresh review with a phrase to send, and neither the proposal nor the review file is modified

#### Scenario: Errors beside a superseded review
- **WHEN** the user asks where the proposal stands and the script reports a mechanical error together with `review-questions-changed`
- **THEN** the handoff's next step is the writing pass that fixes the errors, the review is named as superseded rather than current, and neither file is modified

#### Scenario: Typo corrected in a question
- **WHEN** the user asks where the proposal stands and the only difference behind `review-questions-changed` is a corrected typo in RQ2
- **THEN** the handoff still treats the review as superseded and recommends a fresh review
