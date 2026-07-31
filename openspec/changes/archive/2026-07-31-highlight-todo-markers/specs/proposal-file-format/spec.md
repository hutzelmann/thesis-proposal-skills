## MODIFIED Requirements

### Requirement: Visible TODO markers
Placeholders for missing information SHALL use the visible form `[TODO: <3–10 word hint>]` in the body text. The `title` and `subtitle` metadata MAY carry a marker in the same form; no other metadata key SHALL carry one, and a marker inside the `references` block is not a placeholder and carries no meaning. A marker SHALL be rendered by the build as a distinguishable annotation rather than as prose, so that the promise of visibility holds in the compiled document and not only in the source file.

#### Scenario: Missing reference
- **WHEN** a writing step lacks a needed source
- **THEN** it inserts `[TODO: add key reference for X]` instead of fabricating one

#### Scenario: Undecided degree level
- **WHEN** a proposal is created before the degree level is settled
- **THEN** the `subtitle` may hold a marker, and the built document shows it as an annotation in the title block

#### Scenario: Marker survives the build as a marker
- **WHEN** a proposal containing markers is built into a document
- **THEN** each marker is visually distinguishable from the surrounding prose rather than typeset as an ordinary sentence
