## ADDED Requirements

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
