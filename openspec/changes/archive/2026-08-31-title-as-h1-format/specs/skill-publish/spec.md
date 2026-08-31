# skill-publish Delta

## MODIFIED Requirements

### Requirement: Compact output and citation style
Generated documents SHALL use a compact, professionally typeset layout (successor of the legacy template's look, typst template as fidelity reference) with a citation style limiting each citation bracket to a single reference, honoring the proposal's inferred language for localization. The layout SHALL use the page efficiently: uniform margins tighter than the legacy 1in geometry, a compact title block, and body text that remains at a comfortable reading size rather than gaining density through smaller type. Every page SHALL carry an unobtrusive page number so feedback can reference pages. Both PDF tiers SHALL present the same serif academic look; the word-processor tier is exempt from layout fidelity.

#### Scenario: Two sources in one sentence
- **WHEN** the text cites two works at the same point
- **THEN** the rendered output shows them as separate single-reference citations

#### Scenario: Page numbers present
- **WHEN** a proposal building to more than one page is rendered to PDF
- **THEN** each page shows its page number in the footer

#### Scenario: PDF tiers look alike
- **WHEN** the same proposal is built once through the typst tier and once through the LaTeX tier
- **THEN** both PDFs show the same page geometry, a serif academic typeface of matching character, and the same title block structure

### Requirement: Continuous TODO numbering

Publish SHALL number TODO markers continuously across the document, starting at one, with no reset and no gaps, so an individual gap can be referred to by number. Markers carried by the leading `# <title>` line and the subtitle paragraph SHALL be numbered ahead of the remaining body markers, matching the order in which a reader encounters them. Markers inside the `references` metadata SHALL NOT be rendered or numbered.

#### Scenario: Body markers numbered in reading order

- **WHEN** a proposal body contains four TODO markers and no title-block marker
- **THEN** they render as numbers one through four in document order

#### Scenario: Subtitle marker precedes body markers

- **WHEN** a proposal carries a TODO marker in its subtitle paragraph and further markers in the body
- **THEN** the subtitle marker renders as number one and the body markers continue from two

#### Scenario: Title marker renders in the title block

- **WHEN** the leading `# ` line carries a TODO marker
- **THEN** the marker renders as an annotation in the title block, numbered ahead of every body marker

#### Scenario: Marker inside a reference entry

- **WHEN** a reference entry in the metadata block contains bracketed text resembling a TODO marker
- **THEN** it is neither rendered as an annotation nor counted in the numbering

### Requirement: Bibliography presentation
The reference list SHALL appear under the proposal's own closing references section heading — "References" in English, "Literatur" in German — rendered like a section heading but without a section number; the build SHALL NOT inject a second bibliography headline. Entries SHALL be set one step below body size, justified, in a two-column arrangement: each entry's numeric label stands flush left in a fixed-width label column, and every text line — first and wrapped alike — aligns on a common left edge, with a small uniform gap separating entries. The reference list SHALL never render as unlabeled body paragraphs. The typst tier is the fidelity reference; the LaTeX tier SHALL approximate the same presentation without packages beyond a standard installation.

#### Scenario: Headline in an English proposal
- **WHEN** an English proposal with references is built to PDF
- **THEN** the reference list appears under the headline "References" without a section number

#### Scenario: Headline in a German proposal
- **WHEN** a German proposal with references is built to PDF
- **THEN** the reference list appears under the headline "Literatur" without a section number

#### Scenario: No duplicate headline
- **WHEN** a proposal carrying the closing references section is built to PDF
- **THEN** exactly one bibliography headline appears, sourced from the body section

#### Scenario: Long entry wraps
- **WHEN** a reference entry is longer than one typeset line
- **THEN** its continuation lines are indented so the numeric labels remain the leftmost column of the list

#### Scenario: Two-digit labels
- **WHEN** a proposal cites ten or more references
- **THEN** entries with two-digit labels render with the same alignment discipline as single-digit entries

#### Scenario: German quotation marks in reference titles
- **WHEN** a German proposal's reference titles are quoted by the citation style
- **THEN** each title renders with a low opening mark and a high closing mark („Titel“), never with two identical marks

## ADDED Requirements

### Requirement: Title block and section levels sourced from the body
The build SHALL source the rendered title block from the body: the leading `# <title>` line becomes the document title and the emphasized subtitle paragraph becomes the subtitle, via pandoc's heading-shift mechanism and the skill's filter chain — never via hand parsing of the markdown. Body sections at H2 SHALL render as top-level sections and H3 as subsections, so the built document is indistinguishable from one built from the retired metadata-key layout. The build SHALL derive the proposal's language by the deterministic inference the file-format contract defines and pass it to the toolchain, so citation locale, hyphenation, and the bibliography headline are localized exactly as under the retired `lang` key. Documentation of workspace build definitions SHALL state the same sourcing, so faculty templates do not render an empty title above a spuriously numbered first section.

#### Scenario: Title and subtitle reach the title block
- **WHEN** a proposal opening with `# <title>` and `*<subtitle>*` is built to PDF
- **THEN** the rendered title block shows both, identical in layout to the retired metadata-key rendering

#### Scenario: Sections render at the top level
- **WHEN** the five canonical sections sit at H2 in the source
- **THEN** they render as numbered top-level sections, with H3 subsections one level below

#### Scenario: German localization without a lang key
- **WHEN** a German proposal with no `lang` key is built
- **THEN** the citation locale, hyphenation, and bibliography headline follow German conventions
