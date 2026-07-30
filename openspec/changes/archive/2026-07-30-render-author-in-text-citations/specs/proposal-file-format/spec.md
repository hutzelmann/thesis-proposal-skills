## MODIFIED Requirements

### Requirement: Citation syntax and key constraints

Citations SHALL use `[@key]` (bracketed) or `@key` (author-in-text). Citation keys MUST NOT be YAML boolean literals (`y`, `n`, `yes`, `no`, `on`, `off`, `true`, `false` in any case).

The two syntaxes carry different rendered meanings and both SHALL be available within a single proposal. The bracketed form renders as the reference number alone. The author-in-text form renders as an author label derived from the reference entry, followed by the reference number, so the cited authors can serve as the subject of a sentence. An author-in-text citation MAY carry a suffix, including a locator or a further citation, which renders after the author label.

#### Scenario: Boolean-literal key rejected

- **WHEN** a reference uses the id `on`
- **THEN** the check tooling reports it as an invalid key

#### Scenario: Bracketed form stays bare

- **WHEN** the body attaches a bracketed citation to a claim
- **THEN** the rendered output shows the reference number without an author name

#### Scenario: Author-in-text form carries the name

- **WHEN** the body opens a sentence with an author-in-text citation whose reference has three authors
- **THEN** the rendered output shows the first author's surname, "et al.", and the reference number, and the sentence is grammatical

#### Scenario: Author-in-text citation with a citation in its suffix

- **WHEN** the body writes an author-in-text citation whose suffix contains a further citation
- **THEN** the rendered output shows the author label, the first reference's number, and the suffix with the second reference's number

#### Scenario: Several author-in-text citations in one sentence

- **WHEN** a sentence names two works in a row, each in the author-in-text form
- **THEN** each renders with its own author label and reference number
