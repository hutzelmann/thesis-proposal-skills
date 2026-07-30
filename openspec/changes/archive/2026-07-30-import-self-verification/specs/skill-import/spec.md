## MODIFIED Requirements

### Requirement: Import to standard format

Given an existing proposal document, the skill SHALL produce one proposal file in the standard format (body restructured toward the canonical sections, references converted to CSL-YAML), with unmappable or missing information marked as `[TODO: …]`.

The produced file SHALL satisfy the mechanical check apart from findings that follow from what the source did not carry, such as too few references. In particular the metadata block SHALL be closed, `references` SHALL be a CSL-YAML list of entries each carrying an `id`, the methodology section SHALL name one methodology from the closed set, and the research questions SHALL be an ordered list. The skill SHALL show these shapes rather than only describing them, because a source document rarely resembles them.

The skill SHALL verify that conformance itself: before reporting completion it SHALL run the mechanical check over the file it wrote and resolve the errors it reports. Errors that reflect what the source did not carry SHALL be reported to the user instead, never resolved by inventing content. Because verification reads the file back, the skill SHALL NOT report a proposal it did not write.

#### Scenario: PDF with free-form structure

- **WHEN** a PDF proposal with non-canonical sections is imported
- **THEN** content is mapped to the canonical structure where possible and gaps carry TODO markers

#### Scenario: Imported file passes the mechanical check

- **WHEN** the mechanical check runs over a freshly imported proposal
- **THEN** it reports no errors other than those caused by information absent from the source

#### Scenario: Verification finds a fixable defect

- **WHEN** the check reports a structural error such as a research question never referenced from the methodology section
- **THEN** the skill fixes it and re-runs the check before reporting completion

#### Scenario: Verification finds a defect the source caused

- **WHEN** the check reports that the proposal cites fewer references than required, because the source carried only two
- **THEN** the skill reports that to the user and does not invent sources to satisfy it

#### Scenario: The file was never written

- **WHEN** verification cannot read the proposal file back
- **THEN** the skill reports the failure rather than describing the import as complete

#### Scenario: Source describes an approach outside the closed methodology set

- **WHEN** the source describes its approach in its own words, such as "implementation and farm validation"
- **THEN** the import maps it onto one methodology from the closed set rather than inventing a methodology name

#### Scenario: A reference cannot be completed from the source

- **WHEN** the import cannot recover a reference field and marks it in the metadata block
- **THEN** the marker is the value of a key rather than a line of its own, so the block still parses and the file still builds

#### Scenario: Source lists references in an unstructured bibliography

- **WHEN** a bibliography is converted
- **THEN** each entry becomes a list item with an `id`, keys follow the documented key shape, and no author name carries "et al."
