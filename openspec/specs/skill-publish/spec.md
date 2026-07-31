# skill-publish Specification

## Purpose
Optional document build: turns the proposal file into a compact PDF (or fallback formats) with install guidance when tools are missing.
## Requirements
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

### Requirement: Author-in-text citation rendering
Publish SHALL render an author-in-text citation as an author label followed by the citation's numeric bracket, and SHALL render a bracketed citation as the numeric bracket alone. Both forms SHALL be usable in the same document without configuration. The author label SHALL be derived from the proposal's own reference entry for the cited key, never from text typed by the author, so that editing a reference updates every in-text mention. The label and its bracket SHALL be joined by a non-breaking space so they cannot be split across a line break.

#### Scenario: Both forms in one paragraph
- **WHEN** a paragraph contains an author-in-text citation of a three-author work and a bracketed citation of another work
- **THEN** the first renders as the first author's surname followed by "et al." and the numeric bracket, and the second renders as the numeric bracket alone

#### Scenario: Reference surname corrected
- **WHEN** an author's surname is corrected in the reference entry and the document is rebuilt
- **THEN** every author-in-text mention of that reference shows the corrected surname

#### Scenario: Citation near a line end
- **WHEN** an author-in-text citation falls at the end of a typeset line
- **THEN** the author label and the numeric bracket stay on the same line

### Requirement: Author label form and localization
The author label SHALL depend on the number of authors of the cited reference: one author yields the surname alone; two authors yield both surnames joined by a conjunction; three or more yield the first surname followed by "et al.". Surname particles that are part of the name SHALL be included. The conjunction SHALL follow the proposal's declared language; the "et al." abbreviation SHALL remain unlocalized.

#### Scenario: Two-author work in an English proposal
- **WHEN** a two-author work is cited author-in-text in a proposal declaring English
- **THEN** the label joins both surnames with "and"

#### Scenario: Two-author work in a German proposal
- **WHEN** the same work is cited author-in-text in a proposal declaring German
- **THEN** the label joins both surnames with "und" and any three-author label still uses "et al."

#### Scenario: Surname with a particle
- **WHEN** a cited author's surname carries a non-dropping particle
- **THEN** the particle appears as part of the in-text surname

### Requirement: Author label fallback for references without authors
When a reference cited author-in-text declares no author, publish SHALL fall back to its editors, marked as editors in the proposal's declared language, and then to the reference title in quotation marks. Publish SHALL NOT fail the build for this reason.

#### Scenario: Editor-only reference
- **WHEN** an author-in-text citation targets a reference that declares editors but no authors
- **THEN** the label uses the editor surnames with a language-appropriate editor marker and the build succeeds

#### Scenario: Reference with neither authors nor editors
- **WHEN** an author-in-text citation targets a reference declaring only a title
- **THEN** the label is the quoted title and the build succeeds

#### Scenario: Institutional author
- **WHEN** a reference declares a single institutional author name rather than a personal name
- **THEN** that name is used verbatim as the label

### Requirement: Locator rendering
Publish SHALL render a citation locator, such as a page or section reference, inside the citation bracket alongside the reference number, in both the bracketed and the author-in-text form. A locator SHALL never be silently discarded.

#### Scenario: Page locator on a bracketed citation
- **WHEN** the body cites a work bracketed with a page locator
- **THEN** the rendered bracket contains the reference number and the abbreviated page locator

#### Scenario: Page locator on an author-in-text citation
- **WHEN** the body cites a work author-in-text with a page locator
- **THEN** the author label precedes a bracket containing the reference number and the locator

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

### Requirement: TODO marker rendering

Publish SHALL render every `[TODO: …]` marker as a visually distinct annotation rather than as body prose, so that a marker cannot be read as a finished sentence. The annotation SHALL carry at least two distinguishing cues, of which at least one SHALL be non-chromatic, so the marker stays identifiable in a grayscale reproduction. The marker's hint text SHALL be preserved verbatim and the bracket delimiters SHALL NOT appear in the output.

#### Scenario: Marker in a justified paragraph

- **WHEN** a proposal paragraph contains a TODO marker and the document is built
- **THEN** the marker renders with a distinguishing field and a label, and the surrounding prose renders unchanged

#### Scenario: Grayscale reproduction

- **WHEN** a built PDF containing a TODO marker is printed or reproduced without color
- **THEN** the marker remains distinguishable from the surrounding prose

#### Scenario: Hint text preserved

- **WHEN** a marker's hint contains punctuation, quotation marks, or a parenthesized fragment
- **THEN** the rendered annotation shows the hint exactly as written, without the surrounding brackets

### Requirement: Continuous TODO numbering

Publish SHALL number TODO markers continuously across the document, starting at one, with no reset and no gaps, so an individual gap can be referred to by number. Markers carried by the `title` and `subtitle` metadata SHALL be numbered ahead of body markers, matching the order in which a reader encounters them. Markers inside the `references` metadata SHALL NOT be rendered or numbered.

#### Scenario: Body markers numbered in reading order

- **WHEN** a proposal body contains four TODO markers and no metadata marker
- **THEN** they render as numbers one through four in document order

#### Scenario: Subtitle marker precedes body markers

- **WHEN** a proposal carries a TODO marker in its `subtitle` and further markers in the body
- **THEN** the subtitle marker renders as number one and the body markers continue from two

#### Scenario: Marker inside a reference entry

- **WHEN** a reference entry in the metadata block contains bracketed text resembling a TODO marker
- **THEN** it is neither rendered as an annotation nor counted in the numbering

### Requirement: Block and inline TODO forms

A TODO marker that occupies a source line on its own SHALL render as a block-level annotation that interrupts the text column. A marker embedded within a sentence SHALL render as an inline annotation that wraps across line breaks without overflowing the text column. Within list items, headings, and table cells, every marker SHALL render in the inline form regardless of its source line position, so that block-level output never appears where the surrounding structure requires inline content.

#### Scenario: Marker alone on its line

- **WHEN** a marker occupies its own source line inside a paragraph of prose
- **THEN** it renders as a block-level annotation and the prose before and after it renders as continuous text

#### Scenario: Long marker inside a sentence

- **WHEN** a marker embedded in a sentence is longer than a typeset line
- **THEN** the annotation wraps onto the following line and stays within the text column

#### Scenario: Marker inside a research-question item

- **WHEN** a research-question list item contains a marker on its own source line
- **THEN** the marker renders inline within the item and the item's research-question styling is preserved

### Requirement: TODO rendering across output tiers

Every output tier SHALL render TODO markers as annotations with the same numbering, degrading only in visual fidelity: the typst tier is the fidelity reference, the LaTeX tier approximates it without requiring packages beyond a standard installation, and the word-processor tier SHALL at minimum render a distinguishing label. No tier SHALL emit a marker as unstyled body text.

#### Scenario: LaTeX fallback tier

- **WHEN** a proposal containing markers is built through the LaTeX pipeline
- **THEN** each marker renders as a distinguishable annotation carrying the same number it would carry in the typst tier

#### Scenario: Word-processor tier

- **WHEN** a proposal containing markers is built to the word-processor format
- **THEN** each marker renders with a distinguishing label and its number

### Requirement: TODO rendering is unconditional

Publish SHALL NOT offer any option, flag, or workspace override that renders TODO markers as ordinary text. A document without marker annotations SHALL be obtainable only by resolving the markers in the proposal file.

#### Scenario: No suppression path

- **WHEN** a user looks for a way to build a marker-free PDF from a proposal that still contains markers
- **THEN** no such option exists and the guidance is to resolve the markers, which the check skill already reports

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

