## ADDED Requirements

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
