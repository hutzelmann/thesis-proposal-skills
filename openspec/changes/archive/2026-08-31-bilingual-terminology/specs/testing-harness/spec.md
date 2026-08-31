# testing-harness delta

## ADDED Requirements

### Requirement: Bilingual terminology guard

The L0 suite SHALL verify that the shipped bilingual surfaces use the per-language document term: the supervise getting-started blurb's English section names the document a proposal and never an Exposé; its German section names it an Exposé and contains "proposal" only inside identifiers or URLs; and the shipped German verdict-tier phrases and German subtitle strings use "Exposé". The guard SHALL name the offending file and term on failure.

#### Scenario: Crossed term caught
- **WHEN** "Exposé" enters the blurb's English section, or a bare "proposal" enters its German prose outside an identifier or URL
- **THEN** the L0 suite fails and names the file and the offending term

#### Scenario: Identifiers exempt
- **WHEN** the German section carries the repository URL or a `proposal-*` skill name
- **THEN** the guard does not flag it
