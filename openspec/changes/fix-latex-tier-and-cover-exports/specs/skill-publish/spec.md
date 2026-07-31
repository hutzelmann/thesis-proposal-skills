## ADDED Requirements

### Requirement: A resolved tier produces its outputs

When publish resolves a pipeline for a conforming proposal, that pipeline SHALL produce every output it declares — a PDF and its intermediate build source for the PDF tiers, a document file for the word-processor tier — and SHALL NOT abort. A tier that cannot build is a defect in that tier, not an acceptable degradation to the next one: the graded fidelity between tiers concerns appearance only, never whether a document is produced.

#### Scenario: Fallback tier on a conforming proposal

- **WHEN** the preferred engine is absent and publish resolves the fallback PDF pipeline for a proposal that the check tooling accepts
- **THEN** the build completes and the declared PDF and intermediate source both exist and are non-empty

#### Scenario: Every shipped example builds on every tier

- **WHEN** each proposal in the project's fixture corpus is built on each resolvable tier
- **THEN** every build completes and produces its declared outputs

#### Scenario: Header content cannot reference packages the template loads later

- **WHEN** the compact-layout header for the LaTeX tier is assembled
- **THEN** it configures only packages it loads itself, because header content is emitted before the document template's own package loading
