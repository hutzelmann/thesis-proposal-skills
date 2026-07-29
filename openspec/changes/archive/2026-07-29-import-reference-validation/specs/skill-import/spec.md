# Delta: skill-import — reference validation and enrichment

## ADDED Requirements

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
