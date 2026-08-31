# skill-write Delta

## MODIFIED Requirements

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

### Requirement: Title negotiated once research questions exist
The skill SHALL judge the proposal's title against the guidance once the research questions are written, including a title inherited unchanged from an ideation seed, and SHALL NOT treat an inherited title as settled. Where the title matches an alarm class, the skill SHALL raise it in chat, state that the title is printed on the study certificate, and offer between one and three abstracted alternatives naming the contribution and its object. The skill SHALL write the student's chosen title, never a silent replacement, and where a named technology is retained the skill SHALL have the student's stated reason that the technology is the object of study.

#### Scenario: Seed title inherited unchanged
- **WHEN** the draft is written from a seed whose working title names a product carried as the instrument
- **THEN** the skill raises the title, names the certificate consequence, and offers abstracted alternatives before reporting the draft finished

#### Scenario: Student picks an alternative
- **WHEN** the student chooses one of the offered titles
- **THEN** the leading `# ` line carries that title and the slug is left alone unless the student asks for a rename

#### Scenario: Student keeps a named technology
- **WHEN** the student states that the named technology is the object of study
- **THEN** the title is written as the student chose it and the point is not raised again in that session

#### Scenario: Title already academic
- **WHEN** the title names a contribution and its object with no alarm class matched
- **THEN** the skill leaves it alone and spends no turn on it
