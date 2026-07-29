# skill-import Specification

## Purpose
Imports an existing proposal (usually PDF) into the standard single-file format, stripping personal data and marking gaps.
## Requirements
### Requirement: Import to standard format
Given an existing proposal document, the skill SHALL produce one proposal file in the standard format (body restructured toward the canonical sections, references converted to CSL-YAML), with unmappable or missing information marked as `[TODO: …]`.

#### Scenario: PDF with free-form structure
- **WHEN** a PDF proposal with non-canonical sections is imported
- **THEN** content is mapped to the canonical structure where possible and gaps carry TODO markers

### Requirement: Personal data stripped on import
The skill SHALL remove personal data (matriculation numbers, postal addresses, emails, supervisor names/contacts) and forbidden content (timelines, chapter outlines) from the imported result, and SHALL list what was removed.

#### Scenario: Cover page with matriculation number
- **WHEN** the source PDF carries a matriculation number and supervisor emails
- **THEN** the output contains neither and the removal note names both

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

