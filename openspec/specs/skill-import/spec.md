# skill-import Specification

## Purpose
Imports an existing proposal (usually PDF) into the standard single-file format, stripping personal data and marking gaps.
## Requirements
### Requirement: Import to standard format

Given an existing proposal document, the skill SHALL produce one proposal file in the standard format (body restructured toward the canonical sections, references converted to CSL-YAML), with unmappable or missing information marked as `[TODO: …]`.

The produced file SHALL satisfy the mechanical check apart from findings that follow from what the source did not carry, such as too few references. The skill SHALL show the target shape rather than only describing it, because a source document rarely resembles it.

The skill's instructions SHALL NOT restate rules the mechanical check enforces. Duplicated guidance is a second source of truth that drifts from the check, and the skill runs the check on every import. Instructions SHALL cover only what the check cannot see — among them one person per author entry and a TODO marker placed as a bare line in the metadata block, which leaves the YAML unparseable while the check reports the file clean.

The skill SHALL verify that conformance itself: before reporting completion it SHALL run the mechanical check over the file it wrote and resolve the errors it reports. Errors that reflect what the source did not carry SHALL be reported to the user instead, never resolved by inventing content. Because verification reads the file back, the skill SHALL NOT report a proposal it did not write.

#### Scenario: PDF with free-form structure

- **WHEN** a PDF proposal with non-canonical sections is imported
- **THEN** content is mapped to the canonical structure where possible and gaps carry TODO markers

#### Scenario: Imported file passes the mechanical check

- **WHEN** the mechanical check runs over a freshly imported proposal
- **THEN** it reports no errors other than those caused by information absent from the source

#### Scenario: Rule already enforced by the check

- **WHEN** the mechanical check already reports a structural violation, such as a methodology outside the closed set
- **THEN** the skill's instructions rely on the check for it rather than restating it as a separate rule

#### Scenario: Defect the check cannot see

- **WHEN** a rule cannot be verified mechanically, such as a TODO marker as a bare line in the metadata block
- **THEN** the skill states it explicitly, because nothing downstream will catch it

#### Scenario: Source describes an approach outside the closed methodology set

- **WHEN** the source describes its approach in its own words, such as "implementation and farm validation"
- **THEN** the import maps it onto one methodology from the closed set rather than inventing a methodology name

#### Scenario: A reference cannot be completed from the source

- **WHEN** the import cannot recover a reference field and marks it in the metadata block
- **THEN** the marker is the value of a key rather than a line of its own, so the block still parses and the file still builds

#### Scenario: Source lists references in an unstructured bibliography

- **WHEN** a bibliography is converted
- **THEN** each entry becomes a list item with an `id`, keys follow the documented key shape, and no author name carries "et al."

#### Scenario: Verification finds a fixable defect

- **WHEN** the check reports a structural error such as a research question never referenced from the methodology section
- **THEN** the skill fixes it and re-runs the check before reporting completion

#### Scenario: Verification finds a defect the source caused

- **WHEN** the check reports that the proposal cites fewer references than required, because the source carried only two
- **THEN** the skill reports that to the user and does not invent sources to satisfy it

#### Scenario: The file was never written

- **WHEN** verification cannot read the proposal file back
- **THEN** the skill reports the failure rather than describing the import as complete

### Requirement: Citation form conversion
When converting a source document, the skill SHALL choose the citation syntax by the role the citation plays in its sentence: where the source names the cited authors as the actor of the sentence, the name SHALL be removed from the prose and the citation written in the author-in-text form; where the citation stands as evidence for a claim, it SHALL be written in the bracketed form. The skill SHALL NOT leave an author name typed in the prose immediately before a bracketed citation, because such a name is a copy that stops tracking the reference entry.

#### Scenario: Source names the authors as the actor
- **WHEN** the source reads "Smith et al. [1] propose a drift detector"
- **THEN** the imported text carries the author-in-text citation alone and the typed name "Smith et al." is gone from the prose

#### Scenario: Source cites as evidence
- **WHEN** the source reads "Silent degradation is widely reported [1]."
- **THEN** the imported text carries the bracketed citation and no author name appears in the sentence

#### Scenario: Author-date source
- **WHEN** the source uses an author-date style, naming authors in the running text as "Smith et al. (2020) propose"
- **THEN** the imported text uses the author-in-text form, with neither the typed name nor the year left in the prose

#### Scenario: Reference cannot be resolved
- **WHEN** a source citation has no reference entry that can be recovered
- **THEN** the existing TODO marker behavior applies and no author name is invented to accompany it

### Requirement: Personal data stripped on import
The skill SHALL remove personal data (the writer's own name, matriculation numbers, postal addresses, emails, supervisor names/contacts) and forbidden content (work plans, phase breakdowns, milestone tables, chapter outlines) from the imported result, and SHALL list what was removed. The imported file SHALL NOT carry the writer's name in the metadata block or in body text.

A source work plan SHALL NOT be discarded outright: the start and end months it states SHALL be carried over into the canonical timeline section before the phase detail is removed, and the removal note SHALL record that the detail went and the dates stayed. When no timeframe can be recovered, the timeline section SHALL carry a visible TODO marker rather than an invented statement.

#### Scenario: Cover page with matriculation number
- **WHEN** the source PDF carries a matriculation number and supervisor emails
- **THEN** the output contains neither and the removal note names both

#### Scenario: Cover page with the student's name
- **WHEN** the source PDF names its author on the cover page
- **THEN** the imported file carries no `author` metadata key and no name in the body, and the removal note reports the dropped name

#### Scenario: Source carries a phase table
- **WHEN** the source contains a five-phase work plan spanning October to February
- **THEN** the imported timeline section states October and February, the phase rows are gone, and the removal note reports the dropped work plan and the retained dates

#### Scenario: Source states no dates
- **WHEN** the source has no timeline and no dates anywhere
- **THEN** the imported timeline section carries a visible TODO marker and no timeframe is asserted

### Requirement: Imported sections placed in canonical order
The skill SHALL emit the canonical sections in the order the guidance declares, regardless of the order the source used, because that order is now checked.

#### Scenario: Source orders sections differently
- **WHEN** the source presents its methodology before its research questions
- **THEN** the imported file presents the canonical sections in the declared order, and the mechanical check reports no ordering error

### Requirement: Figures marked, not embedded
The skill SHALL NOT silently drop figures: each figure in the source produces a `[TODO: re-add figure from page N as img/<slug>-….png]` marker; when a local image-extraction tool is available it MAY be used to populate `img/` directly.

#### Scenario: Source with two figures, no extraction tool
- **WHEN** a two-figure PDF is imported and no extraction tool exists
- **THEN** the output contains two page-referenced figure TODO markers

### Requirement: Robustness and degradation
Import SHALL handle PDFs from different producers (word processors, LaTeX, LLM-generated) including formatting artifacts such as swallowed headings or missing title blocks. If the executing agent cannot read PDFs, the skill SHALL say so and guide the user to provide the text instead.

#### Scenario: Agent without PDF support
- **WHEN** the agent cannot ingest PDF content
- **THEN** the skill explains the limitation and requests pasted text, then proceeds normally

### Requirement: Imported references are validated and complemented
References found in the imported document SHALL be validated against the academic literature sources and complemented: DOIs verified by lookup, missing metadata (authors, year, venue, DOI, abstract) filled from the sources when the work can be identified with confidence. A reference that cannot be verified SHALL be kept but marked with a `[TODO: verify reference …]` note — never silently trusted and never silently dropped. The import summary SHALL report per reference: verified, enriched, or unverifiable. When the literature sources are unreachable, import SHALL proceed with unvalidated references and say so.

#### Scenario: Typo'd DOI
- **WHEN** an imported reference carries a DOI that resolves to nothing
- **THEN** the entry is kept, marked with a verification TODO, and listed as unverifiable in the import summary

#### Scenario: Incomplete entry completed
- **WHEN** an imported reference has only authors and title but the work is confidently identified at a source
- **THEN** the entry gains year, venue, and DOI (and abstract when available) from the source

#### Scenario: Sources unreachable
- **WHEN** no literature source can be reached during import
- **THEN** the import completes with as-found references and reports that validation was skipped

### Requirement: Notes file seeded at import
The import skill SHALL create `<slug>.notes.md` beside the imported proposal and seed it with the knowledge the import produced but the proposal cannot carry: source content that did not map into the canonical sections (for example dropped work-plan phase detail beyond the kept boundary months), the gap list summarizing what the source did not supply, and an initial Next Focus naming the most important gaps to close first. Submission-blocking gaps continue to appear as `[TODO: …]` markers in the proposal; the notes file summarizes and prioritizes them, it does not replace them. Content copied into the notes file follows the same personal-data stripping rules as the proposal itself.

#### Scenario: Dropped work-plan detail preserved
- **WHEN** the source contains a phase-by-phase work plan whose boundary months go into the Timeline section
- **THEN** the dropped phase detail lands in the notes file instead of being reported only in chat

#### Scenario: Gap list becomes the initial focus
- **WHEN** the import leaves several TODO markers in the proposal
- **THEN** the notes Next Focus section names the gaps to close first, and the markers themselves remain in the proposal

### Requirement: Import names the continuation path
The import summary SHALL close by naming the next step, chosen by the class of gap the import left rather than by a fixed pointer: prose gaps that the source did not fill go to the write skill, a reference shortfall goes to the literature-search skill, and absent research questions or an absent method go to the ideation skill. The summary SHALL state that the `[TODO: …]` markers are the work queue and that the notes file's Next Focus ranks them. Import remains a single pass: naming the next skill SHALL NOT start it, and no gap is filled in the import run.

#### Scenario: Import leaves prose gaps
- **WHEN** the import completes with `[TODO: …]` markers for content the source did not supply
- **THEN** the summary names the write skill as the way to close them, and says the markers are the work queue with the notes file's Next Focus ranking them

#### Scenario: Import leaves a reference shortfall
- **WHEN** the mechanical check reports fewer references than the guidelines require
- **THEN** the summary names the literature-search skill for that gap, rather than pointing the shortfall at the write skill

#### Scenario: Source supplied no research questions
- **WHEN** the source carried no research questions or no method, so those sections hold only markers
- **THEN** the summary says the gap is idea substance and names the ideation skill for it

#### Scenario: Naming the next skill does not start it
- **WHEN** the summary names a continuation skill
- **THEN** the import run ends there and no gap is filled, no further skill runs, and the user decides what happens next

### Requirement: Output lands in the workspace

The imported proposal `<slug>.md` and its companion `<slug>.notes.md` SHALL be written into the workspace's configured proposal location — by default the working directory, or the subdirectory the workspace `guidelines.md` configures as the proposal-location path — beside any proposals already there. The skill's install directory is read-only territory: the skill SHALL NOT write any artifact there, and SHALL NOT change the working directory to the install directory to run its shipped scripts — scripts are invoked from the workspace via their path. When the source document lives outside the workspace, the imported result SHALL still be written into the workspace's configured proposal location, not beside the source.

#### Scenario: Ordinary import

- **WHEN** an import run converts a source document while working in the user's workspace
- **THEN** `<slug>.md` and `<slug>.notes.md` exist in that workspace's configured proposal location when the run reports completion, and no file has been written into the skill's install directory

#### Scenario: Workspace configures a proposal subdirectory

- **WHEN** the workspace `guidelines.md` sets the proposal-location path to a subdirectory
- **THEN** the imported `<slug>.md` and `<slug>.notes.md` are created in that subdirectory, not in the workspace root

#### Scenario: Host leaves the skill-directory variable unexpanded

- **WHEN** the host does not substitute `${CLAUDE_SKILL_DIR}` and the agent falls back to the scripts' real location next to SKILL.md
- **THEN** the agent runs the scripts from the workspace by their full path, and the imported file is created and checked in the workspace, not in the skill directory

#### Scenario: Source document outside the workspace

- **WHEN** the source document is provided by a path outside the workspace (for example a downloads folder)
- **THEN** the imported `<slug>.md` is written into the workspace's configured proposal location, and nothing is written beside the source document

### Requirement: Single-context execution

An import SHALL be performed by one agent in one context: the same agent reads the source once, maps its content onto the canonical sections, converts the references, and writes `<slug>.md` and the notes file. The skill SHALL NOT spawn one helper agent per section, per reference, per citation, or per figure, because reordering into canonical order and the personal-data strip need the whole document in view, every helper would read the source again, and the two output files have one writer. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would map the source through one helper per section or convert the bibliography through one helper per reference
- **THEN** the import is performed in one context, the source is read once, and both output files are written by that one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

