## MODIFIED Requirements

### Requirement: Compact output and citation style

Generated documents SHALL use a compact, professionally typeset layout (successor of the legacy template's look, typst template as fidelity reference) with a citation style limiting each citation bracket to a single reference, honoring the proposal's declared language for localization. The layout SHALL use the page efficiently: uniform margins tighter than the legacy 1in geometry, a compact title block, and body text that remains at a comfortable reading size rather than gaining density through smaller type. Every page SHALL carry an unobtrusive page number so feedback can reference pages. Both PDF tiers SHALL present the same serif academic look; the word-processor tier is exempt from layout fidelity.

#### Scenario: Two sources in one sentence

- **WHEN** the text cites two works at the same point
- **THEN** the rendered output shows them as separate single-reference citations

#### Scenario: Page numbers present

- **WHEN** a proposal building to more than one page is rendered to PDF
- **THEN** each page shows its page number in the footer

#### Scenario: PDF tiers look alike

- **WHEN** the same proposal is built once through the typst tier and once through the LaTeX tier
- **THEN** both PDFs show the same page geometry, a serif academic typeface of matching character, and the same title block structure

## ADDED Requirements

### Requirement: Bibliography presentation

The reference list SHALL be introduced by an unnumbered headline styled like a section heading, worded in the proposal's declared language ("References" in English, "Literatur" in German). Entries SHALL be set one step below body size, justified, in a two-column arrangement: each entry's numeric label stands flush left in a fixed-width label column, and every text line — first and wrapped alike — aligns on a common left edge, with a small uniform gap separating entries. The reference list SHALL never render as unlabeled body paragraphs. The typst tier is the fidelity reference; the LaTeX tier SHALL approximate the same presentation without packages beyond a standard installation.

#### Scenario: Headline in an English proposal

- **WHEN** an English proposal with references is built to PDF
- **THEN** the reference list appears under the headline "References" without a section number

#### Scenario: Headline in a German proposal

- **WHEN** a German proposal with references is built to PDF
- **THEN** the reference list appears under the headline "Literatur" without a section number

#### Scenario: Long entry wraps

- **WHEN** a reference entry is longer than one typeset line
- **THEN** its continuation lines are indented so the numeric labels remain the leftmost column of the list

#### Scenario: Two-digit labels

- **WHEN** a proposal cites ten or more references
- **THEN** entries with two-digit labels render with the same alignment discipline as single-digit entries

#### Scenario: German quotation marks in reference titles

- **WHEN** a German proposal's reference titles are quoted by the citation style
- **THEN** each title renders with a low opening mark and a high closing mark („Titel“), never with two identical marks
