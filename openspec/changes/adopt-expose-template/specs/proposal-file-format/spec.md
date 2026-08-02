## MODIFIED Requirements

### Requirement: Single-file proposal with trailing metadata block
A proposal SHALL be stored as one markdown file: body text on top, followed by exactly one YAML metadata block at the end of the file carrying at least `title`, `author`, `subtitle`, `lang`, and `references` (CSL-YAML list). The file MUST be consumable by standard pandoc + citeproc without preprocessing.

The metadata block SHALL additionally carry the exposé title-page fields `student_id`, `degree_program`, `supervisor`, `second_supervisor`, and `submission_date`, plus an optional `abbreviations` mapping feeding the List of Abbreviations. These fields are the only permitted location for personal data; body text SHALL remain free of it. A field whose value is unknown SHALL hold a `[TODO: …]` placeholder rather than an invented value.

#### Scenario: Valid file renders with resolved citations
- **WHEN** a proposal file with body citations and a trailing metadata block is processed by pandoc with citeproc
- **THEN** all citations resolve against the `references` entries and a bibliography is produced

#### Scenario: Student ID belongs to the metadata, not the body
- **WHEN** an imported source carries a matriculation number on its cover page
- **THEN** the value is moved into `student_id` and removed from the body

#### Scenario: Blank line must precede the trailing block
- **WHEN** the trailing `---` block is not preceded by a blank line
- **THEN** the file is treated as malformed (metadata silently becomes body text) and tooling SHALL flag it
