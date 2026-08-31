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

The hand-in export is the one publish output that is not an ignorable build artifact — it is a deliverable meant to be kept and sent. Publish SHALL therefore NOT silently replace an existing hand-in export whose content differs from what it would write. It SHALL refuse, report the file and the way to proceed anyway, and exit non-zero. An explicit force option SHALL perform the replacement. Writing content identical to the existing file SHALL succeed silently, so an unchanged rebuild stays free. The skill SHALL relay the refusal to the user rather than resolving it on their behalf, because whether hand edits may be discarded is the user's decision.

#### Scenario: Markdown hand-in
- **WHEN** the user requests the hand-in export
- **THEN** a copy without abstract fields is produced, citations intact

#### Scenario: Hand-in export was edited by hand
- **WHEN** the hand-in export already exists with content differing from what would be written
- **THEN** publish refuses, names the file and the force option, and exits non-zero without writing

#### Scenario: Forced replacement
- **WHEN** the user requests the hand-in export with the force option and a differing file exists
- **THEN** the file is replaced

#### Scenario: Unchanged rebuild
- **WHEN** the hand-in export already exists and its content matches what would be written
- **THEN** the run succeeds without a refusal

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

### Requirement: Workspace-supplied build definition takes precedence

A workspace SHALL be able to replace the shipped document pipeline with a build definition of its own, so that a program with a required document layout does not have to fork the skills. Publish SHALL look for such a definition in the proposal's own directory, and SHALL NOT search any other directory, in particular not by walking towards the filesystem root.

Two forms SHALL be recognized:

- an executable build file whose name is `proposal-build`, with or without a suffix, in which case its presence alone is the signal;
- a well-known build-recipe file — a makefile or a justfile under its conventional names — which counts only when it declares a target named `proposal-build`, so that an unrelated build system already present in the workspace is not mistaken for a proposal build.

When a definition is found, publish SHALL NOT build. It SHALL report which definition it found, state that the built-in pipeline was not used, and exit with a status distinct from both success and its build-failure status, so that the run can be told apart from a failure. Executing the definition is the caller's responsibility; the skill's instructions SHALL direct the agent to run it and to relay its output.

#### Scenario: Build file beside the proposal

- **WHEN** a file named `proposal-build` with any suffix sits in the proposal's directory and a build is requested
- **THEN** publish names it, builds nothing, and exits with its handover status

#### Scenario: Recipe file declaring the target

- **WHEN** the proposal's directory holds a makefile or justfile declaring a `proposal-build` target and a build is requested
- **THEN** publish names the file and the target, builds nothing, and exits with its handover status

#### Scenario: Recipe file without the target

- **WHEN** the proposal's directory holds a makefile that declares no `proposal-build` target
- **THEN** it is not a build definition, and the built-in pipeline runs as it would in any other workspace

#### Scenario: Definition in an ancestor directory

- **WHEN** a build definition exists in a directory above the proposal's own
- **THEN** it is not discovered, and the built-in pipeline runs

### Requirement: No fallback to the built-in pipeline

While a workspace build definition exists beside the proposal, publish SHALL NOT produce the built-in document under any circumstance other than an explicit request for it — not on a failed workspace build, not on a missing toolchain, not on an unreadable definition. Producing the default layout when the workspace asked for a different one is a silent wrong answer, because it succeeds visibly and is wrong invisibly.

An explicit option SHALL be provided to run the built-in pipeline anyway, so that a user can establish whether a bad document comes from their template or from their content.

Because the workspace build definition replaces the pipeline, publish SHALL NOT report a missing document toolchain to a delegating workspace, and SHALL NOT resolve an engine for it.

#### Scenario: Workspace build fails

- **WHEN** the workspace build definition runs and fails
- **THEN** no built-in document is produced, and the outcome is reported as the workspace build's failure

#### Scenario: No document toolchain installed

- **WHEN** a delegating workspace has neither of the shipped document engines installed
- **THEN** publish still hands over, and reports no toolchain-install guidance

#### Scenario: Built-in pipeline requested explicitly

- **WHEN** the user explicitly asks for the built-in pipeline in a delegating workspace
- **THEN** the built-in document is produced and the workspace definition is left untouched

### Requirement: Handover is not a defect

The handover status SHALL NOT be treated as a failed run. The skill's bug-report offer, which is made when a shipped script exits non-zero, SHALL NOT be made for it.

#### Scenario: Bug-report offer after handover

- **WHEN** publish hands over to a workspace build definition
- **THEN** no bug report is offered, because nothing failed

### Requirement: Ambiguous build definitions are refused

Where more than one workspace build definition is present beside a proposal, publish SHALL refuse, SHALL name every definition it found, and SHALL neither build nor nominate one of them. Which of two build definitions is the intended one is a question only the user can answer, and guessing it produces the same silent wrong document that the no-fallback rule exists to prevent.

#### Scenario: Two definitions present

- **WHEN** the proposal's directory holds both a `proposal-build` file and a recipe file declaring the `proposal-build` target
- **THEN** publish refuses, names both, and neither builds nor picks one

### Requirement: Contract passed to a workspace build definition

A workspace build definition SHALL receive exactly one piece of information: the absolute path of the proposal file. It SHALL be supplied through an environment variable, so that the same contract serves build files and build recipes alike, and additionally as the first argument where the definition is a build file, which is where the author of a script looks for it. Its directory is the output directory, by the same convention the built-in pipeline follows.

No further input SHALL be added to this contract. The declared language, the output format and the output location are all derivable from the proposal and its directory, and every additional argument is a contract that has to be honoured indefinitely.

#### Scenario: Build file invoked

- **WHEN** a `proposal-build` build file is run for a proposal
- **THEN** it receives the proposal's absolute path both in the environment variable and as its first argument

#### Scenario: Build recipe invoked

- **WHEN** a `proposal-build` recipe target is run for a proposal
- **THEN** it receives the proposal's absolute path in the environment variable

### Requirement: A delegating run writes nothing

On a run that hands over to a workspace build definition, publish SHALL write no file at all — neither a document, nor an intermediate build source, nor an entry in the workspace ignore file. Publish does not know which artifacts a workspace definition produces, so ignore entries for the shipped pipeline's artifacts would be a guess, and the workspace owns its own ignore rules. A workspace build definition is a source file and SHALL NOT be matched by any ignore entry publish manages.

#### Scenario: Ignore file untouched on handover

- **WHEN** publish hands over in a workspace whose ignore file does not yet cover build artifacts
- **THEN** the ignore file is left exactly as it was

#### Scenario: Build definition stays committable

- **WHEN** the ignore entries publish manages are applied to a workspace holding a build definition
- **THEN** none of them matches it

### Requirement: The hand-in export is never delegated

The hand-in export SHALL always be produced by the shipped implementation, including in a workspace that supplies a build definition. It is a transformation of the proposal's own source rather than a rendered document, so a layout template has nothing to say about it, and delegating it would require a second mode in the contract passed to the definition.

#### Scenario: Hand-in export in a delegating workspace

- **WHEN** the user requests the hand-in export in a workspace holding a build definition
- **THEN** the shipped export is written as it would be in any other workspace, and no handover occurs

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

