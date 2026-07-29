# Delta: skill-import

## Purpose

Imports an existing proposal (usually PDF) into the standard single-file format, stripping personal data and marking gaps.

## ADDED Requirements

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
