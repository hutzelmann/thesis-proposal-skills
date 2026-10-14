## ADDED Requirements

### Requirement: Research questions recorded in the review
The review file SHALL close with a record of the research questions the review judged: a section titled `## Research questions reviewed` (German: `## Begutachtete Forschungsfragen`) holding an ordered list. Its items SHALL be the items of the numbered list in the proposal's research-questions section, and nothing else: each copied verbatim, in the proposal's order. An overarching question the section states in prose before or after that list SHALL NOT enter the record. A nested item SHALL stay inside its parent item, never becoming an item of its own. No item SHALL be added, shortened, merged, reworded or translated. The record SHALL be the last section of the file, after every finding and after the grammar hint where one exists, and SHALL be plain markdown: no hidden comment, no front matter, no machine syntax beyond the heading and the list. When the research-questions section holds no numbered list, the review SHALL write no record.

The record is provenance, not a finding: the review SHALL NOT count, classify or comment on it, and the chat summary SHALL NOT mention it. A review that overwrites an earlier one SHALL carry exactly one record, listing the questions this review judged.

#### Scenario: Record closes the review
- **WHEN** the review judges a proposal whose research-questions section numbers three questions
- **THEN** the review file's last section is `## Research questions reviewed`, listing those three questions in the proposal's order, each with the proposal's own wording

#### Scenario: German proposal with an overarching question
- **WHEN** a German proposal's research-questions section states an overarching question in a sentence and then numbers four sub-questions
- **THEN** the record is titled `## Begutachtete Forschungsfragen` and lists the four numbered sub-questions verbatim in German, in their order, and not the overarching question

#### Scenario: Record after the grammar hint
- **WHEN** the review ends its findings with a grammar hint
- **THEN** the record follows the hint and is the last section of the file

#### Scenario: Later round
- **WHEN** a review overwrites an earlier review whose record lists four questions, and the current proposal numbers three
- **THEN** the new file carries exactly one record section, the last one, listing the current three questions

#### Scenario: No numbered research questions
- **WHEN** a free-form draft numbers no research question in a research-questions section
- **THEN** the review writes no record section

## MODIFIED Requirements

### Requirement: Grammar hint, never a list
If obvious grammar/spelling problems exist, the review SHALL close its findings with a brief hint including at most one or two examples — never an exhaustive enumeration. The hint SHALL follow the three finding sections; only the research-questions record comes after it.

#### Scenario: Pervasive passive voice and typos
- **WHEN** the text shows widespread language issues
- **THEN** the review closes its findings with a short hint and one or two examples, deferring the full pass to check, and the research-questions record follows the hint
