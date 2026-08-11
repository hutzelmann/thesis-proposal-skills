## ADDED Requirements

### Requirement: Default methodology branches record their provenance
Every methodology branch in the shipped default set SHALL record where it comes from: its content contract in the prose guidance SHALL close with a one-sentence citation of the branch's primary methodological source, and a maintained sources document SHALL state, per branch, the taxonomy or standard it derives from, the source of its subsection contract, and what the compression deliberately left out. A branch added to the defaults without provenance SHALL be treated as incomplete.

#### Scenario: Supervisor asks why a branch exists
- **WHEN** a supervisor asks why the default set contains a given branch and why it has these subsections
- **THEN** the guidance names a citable source in the branch's contract, and the sources document carries the fuller argument

#### Scenario: New default branch without provenance
- **WHEN** a future change adds a default branch with no citation and no sources-document entry
- **THEN** the change is incomplete against this requirement

#### Scenario: Provenance stays out of structured data
- **WHEN** provenance is recorded for a branch
- **THEN** it lives in prose and documentation, never as fields in the structured guidance data
