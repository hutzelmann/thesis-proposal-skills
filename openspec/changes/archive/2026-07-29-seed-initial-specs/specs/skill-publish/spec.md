# Delta: skill-publish

## Purpose

Optional document build: turns the proposal file into a compact PDF (or fallback formats) with install guidance when tools are missing.

## ADDED Requirements

### Requirement: Publishing is optional
The workspace SHALL be fully usable without any build toolchain; handing in the markdown source file is an accepted outcome. Quick start requires zero build dependencies.

#### Scenario: No build tools installed
- **WHEN** a user works without any converter installed
- **THEN** all other skills function normally and publish offers install guidance only when invoked

### Requirement: Engine resolution order
Publish SHALL resolve the best available pipeline in this order: typst engine, then LaTeX engine, then word-processor format output — and SHALL tell the user what to install for a better tier when only a lower one is available.

#### Scenario: Only LaTeX available
- **WHEN** typst is absent but a LaTeX engine exists
- **THEN** the PDF is built via the LaTeX pipeline and the typst option is mentioned

### Requirement: Compact output and citation style
Generated documents SHALL use a compact layout (successor of the legacy template's look, typst template as fidelity reference) with a citation style limiting each citation bracket to a single reference, honoring the proposal's declared language for localization.

#### Scenario: Two sources in one sentence
- **WHEN** the text cites two works at the same point
- **THEN** the rendered output shows them as separate single-reference citations

### Requirement: Outputs and workspace hygiene
The PDF and intermediate build source SHALL be written next to the proposal. Publish SHALL ensure ignore entries exist for all build artifacts (shared rule: whichever skill first creates an ignorable artifact ensures its ignore entry).

#### Scenario: First build in a workspace
- **WHEN** publish runs for the first time
- **THEN** build outputs appear next to the proposal and the workspace ignore file covers them

### Requirement: Hand-in export
Publish SHALL offer a stripped export for supervisor hand-ins without tooling: references reduced to citation-ready entries with abstracts removed.

#### Scenario: Markdown hand-in
- **WHEN** the user requests the hand-in export
- **THEN** a copy without abstract fields is produced, citations intact
