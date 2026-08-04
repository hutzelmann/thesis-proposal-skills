# skill-import Specification

## Purpose
Imports an existing proposal (usually PDF) into the standard single-file format, stripping personal data and marking gaps.
## Requirements
### Requirement: Import to standard format

Given an existing proposal document, the skill SHALL produce one proposal file in the standard format (body restructured toward the canonical sections, references converted to CSL-YAML), with unmappable or missing information marked as `[TODO: …]`.

The produced file SHALL satisfy the mechanical check apart from findings that follow from what the source did not carry, such as too few references. The skill SHALL show the target shape rather than only describing it, because a source document rarely resembles it.

The skill's instructions SHALL NOT restate rules the mechanical check enforces. Duplicated guidance is a second source of truth that drifts from the check, and the skill runs the check on every import. Instructions SHALL cover only what the check cannot see — among them one person per author entry and a TODO marker placed as a bare line in the metadata block, which leaves the YAML unparseable while the check reports the file clean.

The skill SHALL verify that conformance itself: before reporting completion it SHALL run the mechanical check over the file it wrote and resolve the errors it reports. Errors that reflect what the source did not carry SHALL be reported to the user instead, never resolved by inventing content. Because verification reads the file back, the skill SHALL NOT report a proposal it did not write.

#### Scenario: PDF with free-form structure

- **WHEN** a PDF proposal with non-canonical sections is imported
- **THEN** content is mapped to the canonical structure where possible and gaps carry TODO markers

#### Scenario: Imported file passes the mechanical check

- **WHEN** the mechanical check runs over a freshly imported proposal
- **THEN** it reports no errors other than those caused by information absent from the source

#### Scenario: Rule already enforced by the check

- **WHEN** the mechanical check already reports a structural violation, such as a methodology outside the closed set
- **THEN** the skill's instructions rely on the check for it rather than restating it as a separate rule

#### Scenario: Defect the check cannot see

- **WHEN** a rule cannot be verified mechanically, such as a TODO marker as a bare line in the metadata block
- **THEN** the skill states it explicitly, because nothing downstream will catch it

#### Scenario: Source describes an approach outside the closed methodology set

- **WHEN** the source describes its approach in its own words, such as "implementation and farm validation"
- **THEN** the import maps it onto one methodology from the closed set rather than inventing a methodology name

#### Scenario: A reference cannot be completed from the source

- **WHEN** the import cannot recover a reference field and marks it in the metadata block
- **THEN** the marker is the value of a key rather than a line of its own, so the block still parses and the file still builds

#### Scenario: Source lists references in an unstructured bibliography

- **WHEN** a bibliography is converted
- **THEN** each entry becomes a list item with an `id`, keys follow the documented key shape, and no author name carries "et al."

#### Scenario: Verification finds a fixable defect

- **WHEN** the check reports a structural error such as a research question never referenced from the methodology section
- **THEN** the skill fixes it and re-runs the check before reporting completion

#### Scenario: Verification finds a defect the source caused

- **WHEN** the check reports that the proposal cites fewer references than required, because the source carried only two
- **THEN** the skill reports that to the user and does not invent sources to satisfy it

#### Scenario: The file was never written

- **WHEN** verification cannot read the proposal file back
- **THEN** the skill reports the failure rather than describing the import as complete

### Requirement: Citation form conversion
When converting a source document, the skill SHALL choose the citation syntax by the role the citation plays in its sentence: where the source names the cited authors as the actor of the sentence, the name SHALL be removed from the prose and the citation written in the author-in-text form; where the citation stands as evidence for a claim, it SHALL be written in the bracketed form. The skill SHALL NOT leave an author name typed in the prose immediately before a bracketed citation, because such a name is a copy that stops tracking the reference entry.

#### Scenario: Source names the authors as the actor
- **WHEN** the source reads "Smith et al. [1] propose a drift detector"
- **THEN** the imported text carries the author-in-text citation alone and the typed name "Smith et al." is gone from the prose

#### Scenario: Source cites as evidence
- **WHEN** the source reads "Silent degradation is widely reported [1]."
- **THEN** the imported text carries the bracketed citation and no author name appears in the sentence

#### Scenario: Author-date source
- **WHEN** the source uses an author-date style, naming authors in the running text as "Smith et al. (2020) propose"
- **THEN** the imported text uses the author-in-text form, with neither the typed name nor the year left in the prose

#### Scenario: Reference cannot be resolved
- **WHEN** a source citation has no reference entry that can be recovered
- **THEN** the existing TODO marker behavior applies and no author name is invented to accompany it

### Requirement: Personal data stripped on import
The skill SHALL remove personal data (the writer's own name, matriculation numbers, postal addresses, emails, supervisor names/contacts) and forbidden content (work plans, phase breakdowns, milestone tables, chapter outlines) from the imported result, and SHALL list what was removed. The imported file SHALL NOT carry the writer's name in the metadata block or in body text.

A source work plan SHALL NOT be discarded outright: the start and end months it states SHALL be carried over into the canonical timeline section before the phase detail is removed, and the removal note SHALL record that the detail went and the dates stayed. When no timeframe can be recovered, the timeline section SHALL carry a visible TODO marker rather than an invented statement.

#### Scenario: Cover page with matriculation number
- **WHEN** the source PDF carries a matriculation number and supervisor emails
- **THEN** the output contains neither and the removal note names both

#### Scenario: Cover page with the student's name
- **WHEN** the source PDF names its author on the cover page
- **THEN** the imported file carries no `author` metadata key and no name in the body, and the removal note reports the dropped name

#### Scenario: Source carries a phase table
- **WHEN** the source contains a five-phase work plan spanning October to February
- **THEN** the imported timeline section states October and February, the phase rows are gone, and the removal note reports the dropped work plan and the retained dates

#### Scenario: Source states no dates
- **WHEN** the source has no timeline and no dates anywhere
- **THEN** the imported timeline section carries a visible TODO marker and no timeframe is asserted

### Requirement: Imported sections placed in canonical order
The skill SHALL emit the canonical sections in the order the guidance declares, regardless of the order the source used, because that order is now checked.

#### Scenario: Source orders sections differently
- **WHEN** the source presents its methodology before its research questions
- **THEN** the imported file presents the canonical sections in the declared order, and the mechanical check reports no ordering error

### Requirement: Figures marked, not embedded
The skill SHALL NOT silently drop figures: each figure in the source produces a `[TODO: re-add figure from page N as img/<slug>-….png]` marker; when a local image-extraction tool is available it MAY be used to populate `img/` directly.

#### Scenario: Source with two figures, no extraction tool
- **WHEN** a two-figure PDF is imported and no extraction tool exists
- **THEN** the output contains two page-referenced figure TODO markers

### Requirement: Robustness and degradation
Import SHALL handle PDFs from different producers (word processors, LaTeX, LLM-generated) including formatting artifacts such as swallowed headings or missing title blocks. If the executing agent cannot read PDFs, the skill SHALL say so and guide the user to provide the text instead.

#### Scenario: Agent without PDF support
- **WHEN** the agent cannot ingest PDF content
- **THEN** the skill explains the limitation and requests pasted text, then proceeds normally

### Requirement: Imported references are validated and complemented
References found in the imported document SHALL be validated against the academic literature sources and complemented: DOIs verified by lookup, missing metadata (authors, year, venue, DOI, abstract) filled from the sources when the work can be identified with confidence. A reference that cannot be verified SHALL be kept but marked with a `[TODO: verify reference …]` note — never silently trusted and never silently dropped. The import summary SHALL report per reference: verified, enriched, or unverifiable. When the literature sources are unreachable, import SHALL proceed with unvalidated references and say so.

#### Scenario: Typo'd DOI
- **WHEN** an imported reference carries a DOI that resolves to nothing
- **THEN** the entry is kept, marked with a verification TODO, and listed as unverifiable in the import summary

#### Scenario: Incomplete entry completed
- **WHEN** an imported reference has only authors and title but the work is confidently identified at a source
- **THEN** the entry gains year, venue, and DOI (and abstract when available) from the source

#### Scenario: Sources unreachable
- **WHEN** no literature source can be reached during import
- **THEN** the import completes with as-found references and reports that validation was skipped

