# Spec Delta

## ADDED Requirements

### Requirement: One folder per proposal
Each proposal SHALL live in a folder of its own directly inside the proposal location, named by its slug and holding every file of its family. `bug-report`, `img` and names starting with `.` SHALL never name a proposal folder. A slug-shaped folder SHALL count as a proposal folder only when it holds a proposal named after it, a notes file carrying the notes file's five section headings, or a harvest record. Skills SHALL leave every other folder alone.

#### Scenario: Slug-shaped folder names
- **WHEN** the proposal location holds the folders `idea`, `idea-2`, `flaky-ci-triage`, `Meetings` and `my_notes`
- **THEN** the first three are slug-shaped, because their names are lowercase ASCII letters and digits joined by single hyphens, one word or more, and `Meetings` and `my_notes` are not, so no skill considers them as proposal folders

#### Scenario: Unrelated folder beside the proposals
- **WHEN** the proposal location holds `meetings/notes.md` whose headings are not the notes file's five sections, and `literature/img/scan.png`
- **THEN** no skill treats either folder as a proposal folder, offers a file in it as a candidate, or writes into it

#### Scenario: Idea folder before any proposal
- **WHEN** the proposal location holds `idea/notes.md` carrying the five section headings and no `idea/idea.md`
- **THEN** `idea/` is a proposal folder whose idea has not been seeded

#### Scenario: Slug that names a reserved folder
- **WHEN** the slug derived from a title is `bug-report`
- **THEN** the proposal's folder and file take the numeric suffix, and the `bug-report/` folder is left to the troubleshooting skill

#### Scenario: Proposal without figures
- **WHEN** a proposal uses no figures
- **THEN** no `img/` folder is created in its folder

## MODIFIED Requirements

### Requirement: Content-derived slug filenames
Proposal slugs SHALL be content-derived — lowercase ASCII, hyphen-separated, 2–4 words derived from the title — never a generic name. The slug SHALL name both the proposal's folder and its proposal file. When a folder of that name already exists in the proposal location, or the name is reserved (requirement: One folder per proposal), a numeric suffix SHALL be appended to both.

#### Scenario: Two similar topics
- **WHEN** a second proposal about a similar topic is created and the natural slug's folder already exists
- **THEN** the new proposal's folder and file both receive the slug with a numeric suffix

### Requirement: Proposal targeting
Skills SHALL resolve the target proposal from an explicit user mention; with exactly one candidate in the proposal location it SHALL be auto-picked; with several candidates and no mention, the skill SHALL list candidates and ask. A candidate is a markdown file named after the proposal folder that holds it, `<slug>/<slug>.md`, ending in a pandoc metadata block. No other markdown file SHALL be a candidate.

#### Scenario: Ambiguous workspace
- **WHEN** the proposal location holds three proposal folders, each with its proposal file, and the user names none
- **THEN** the skill lists the three candidates and asks which to use

#### Scenario: Proposal file outside a folder
- **WHEN** the proposal location holds one proposal folder and, directly in the location, a markdown file ending in a metadata block
- **THEN** the folder's proposal is the only candidate and is auto-picked, and the loose file is not offered

### Requirement: Companion notes file
A proposal MAY have a companion working-knowledge file named `notes.md` in its folder. The notes file SHALL use five canonical top-level sections in this order: `## Decisions`, `## Open Points`, `## Next Focus`, `## Excluded Literature`, `## Log`. Section content is free prose or bullets; no mechanical check SHALL validate content beyond the file being markdown — the canonical sections exist so skills know where to read and write, not as a schema.

The notes file is workspace-internal: it SHALL never be built, published, or submitted, and skills that build, check, or review the proposal SHALL ignore it. A notes file SHALL NOT be treated as a proposal candidate by proposal targeting.

#### Scenario: Notes file beside its proposal
- **WHEN** the folder `energy-attack-detection/` holds `energy-attack-detection.md` and `notes.md`
- **THEN** proposal targeting offers only `energy-attack-detection.md` as a candidate and the notes file is ignored by check, review, and publish

#### Scenario: Notes file alone is not a proposal
- **WHEN** a proposal folder holds only `notes.md` and no proposal
- **THEN** skills that need a proposal report none found rather than operating on the notes file

#### Scenario: Headings read only to classify
- **WHEN** a notes file lacks one of the five section headings or carries headings of its own
- **THEN** the mechanical check reports nothing about the notes file; it reads the headings only to decide whether a folder is a proposal folder or a `notes.md` at a root is a stray companion

### Requirement: Proposal family under one handle
A proposal's slug (Content-derived slug filenames) SHALL name its folder and its proposal file and is its handle. Every file a skill writes for a proposal SHALL sit in that folder (requirement: One folder per proposal) and belong to one closed family. Files that leave the folder carry the handle; files that stay carry their role's name:

- the proposal `<slug>.md`, the built document and its intermediates `<slug>.pdf`, `<slug>.typ`, `<slug>.tex`, `<slug>.docx`, and the hand-in export `<slug>.handout.md`;
- the notes file `notes.md`, the harvest record `harvest.md`, the review `review.md` and the supervisor feedback `feedback.md`;
- figures `img/<name>.<ext>`;
- files the user asked to keep, `<label>.<ext>`, with a label other than `notes`, `review`, `feedback`, `harvest`, `handout`, `img` and the slug (requirement: Working material stays out of the workspace).

Before a topic phrase exists, an idea's folder SHALL be named `idea`, suffixed when taken, and then by a provisional slug derived from the phrase. The slug SHALL be derived from the title when the proposal file is first written, under the bounds of Content-derived slug filenames. Once the proposal file exists, the slug SHALL NOT follow later title changes, and a full draft of an idea whose proposal file already exists, such as an ideation seed, SHALL be written into that file. Only a rename changes the slug (requirement: A rename moves the whole family).

#### Scenario: Family recognisable from the listing
- **WHEN** a workspace holds a proposal that has been seeded, reviewed, illustrated and built
- **THEN** its folder holds `<slug>.md`, `notes.md`, `review.md`, `img/` and `<slug>.pdf`, and no file of the family lies outside that folder

#### Scenario: Title changed after the proposal exists
- **WHEN** a writing pass adopts a new title for an existing proposal and the user has not asked for a rename
- **THEN** the leading `# ` line carries the new title, and the folder and every family file keep their names

#### Scenario: Draft from a seed keeps the seed's file
- **WHEN** a writing pass drafts a full proposal from an ideation seed `<slug>/<slug>.md`
- **THEN** the draft is written into `<slug>/<slug>.md`, and no second proposal file for the idea exists afterwards

#### Scenario: Ideation without a topic phrase
- **WHEN** an ideation session ends at an impasse before any topic phrase emerged
- **THEN** its state is recorded in `idea/notes.md` and no file or folder carries a slug

#### Scenario: Kept file under a reserved label
- **WHEN** the user asks to keep a review-like summary of a search
- **THEN** it is kept under a label other than `review`, such as `search-summary.md`, so it is never read as the proposal's review

### Requirement: A rename moves the whole family
A slug SHALL change only at the seeding step, when the slug derived from the settled working title differs from the provisional one, or when the user asks for a rename. Either way the rename SHALL move the folder `<old>/` to `<new>/` first, and then rename the proposal file `<old>.md` inside it to `<new>.md` when one exists. Role-named files, figures and kept files keep their names, so no link SHALL be edited. Built outputs and the hand-in export under the old slug SHALL stay in the folder as previous outputs; the skill SHALL name them and offer a rebuild, which writes them under the new slug.

Before moving anything, the skill SHALL check the target folder name:

- at seeding, when a folder named by the derived slug exists, the slug SHALL take the numeric suffix of Content-derived slug filenames;
- on a requested rename, when it exists, nothing SHALL be moved; the skill SHALL name the collision and propose the suffixed slug.

No file SHALL be overwritten. After the move the skill SHALL verify that `<new>/` holds the moved files and that no `<new>/<old>/` exists. When the folder or the proposal file cannot be moved, the skill SHALL stop and SHALL say what moved and what did not. The skill SHALL say in chat what it renamed. A rename SHALL NOT move or rewrite workspace-level files or installer-managed files.

#### Scenario: Requested rename with a linked figure
- **WHEN** the user asks to rename a proposal whose folder holds a notes file, a review and a figure `img/pipeline.png` linked from the proposal
- **THEN** afterwards the folder `<new>/` holds `<new>.md`, `notes.md`, `review.md` and `img/pipeline.png`, the proposal still links `img/pipeline.png`, and no folder `<old>/` remains

#### Scenario: Requested rename onto a taken name
- **WHEN** the user asks for a rename and a folder named by the requested new slug already exists
- **THEN** nothing is moved, the skill names the collision, and it proposes the suffixed slug

#### Scenario: Seeding onto a taken name
- **WHEN** the slug derived from the settled working title already names another proposal's folder
- **THEN** the idea's folder and its seed carry the slug with the numeric suffix, and no file is overwritten

#### Scenario: Seeding under a diverged provisional slug
- **WHEN** the folder `<provisional>/` holds the notes file, a kept reading list and a sketch under `img/`, and the settled working title yields a different slug
- **THEN** after seeding, the folder is `<new>/` and holds the seed `<new>.md` beside the unchanged notes file, reading list and sketch, and no folder `<provisional>/` remains

#### Scenario: Member that cannot be moved
- **WHEN** the folder cannot be moved during a rename, for example because another program holds a file in it open
- **THEN** the skill stops, says that nothing moved, and overwrites nothing

#### Scenario: Proposal file left under the old slug
- **WHEN** the folder was moved to `<new>/` but `<old>.md` inside it cannot be renamed
- **THEN** the skill stops and says that the folder moved and the proposal file did not

#### Scenario: Move that nested the folder
- **WHEN** a folder `<new>/` appeared after the target test, so the move left `<new>/<old>/`
- **THEN** the verification finds `<new>/<old>/`, and the skill stops, says where the folder now is, and moves nothing further

#### Scenario: Built output at a rename
- **WHEN** a renamed proposal had a built `<old>.pdf` and a hand-in export `<old>.handout.md`
- **THEN** both stay in the folder `<new>/` under their names, the chat names them as previous outputs, and a rebuild is offered

### Requirement: Working material stays out of the workspace
Skills SHALL write into the workspace only the following:

- proposal folders and their families (requirement: Proposal family under one handle), in the proposal location;
- the workspace-level files at the workspace root: `guidelines.md`, `api-keys.env`, the `bug-report/` folder and the root `.gitignore`;
- in a proposal's folder: a workspace build definition (a file named `proposal-build` with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the `.gitignore` the built-in build adds there, and whatever a workspace build definition reads and writes when the publish step runs it (skill-publish: Workspace-supplied build definition takes precedence);
- the troubleshooting captures `check-output.txt` and `version-output.txt` while a bug report is being assembled.

The installer-managed files are the skill folders `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the install record `.thesis-proposal-install.json`, and `skills-lock.json` in the workspace root. No skill SHALL write, move or delete them.

Working material SHALL stay in the chat: script output, candidate lists, raw responses, probes, logs and scratch drafts. When it is too large to read in one piece, the skill SHALL read it in slices or produce it narrower. A temporary location outside the workspace MAY hold it, but only when one is writable. When none is writable, the skill SHALL read in slices or narrow the run instead, and SHALL NOT fall back to the workspace. A proposal family member SHALL never be written into a host's scratch or temporary folder. Working material SHALL be kept in the workspace only when the user asks. It is then written into the proposal's folder as a kept file `<label>.<ext>` under a label the family leaves free (requirement: Proposal family under one handle).

#### Scenario: Search output larger than the host shows
- **WHEN** a literature search emits more output than the host shows from one command
- **THEN** the skill runs narrower and adds no file to the workspace

#### Scenario: Sandbox without a writable temporary folder
- **WHEN** the host refuses writes to the system temporary folder and a script's output is too large to read in one piece
- **THEN** the skill reads it in slices or narrows the run instead of writing the output into the workspace

#### Scenario: User asks to keep a candidate list
- **WHEN** the user asks to keep the candidate list of a search for a proposal
- **THEN** it is written into the proposal's folder as `<label>.<ext>`, such as `candidates.yaml`, and nothing else is added

#### Scenario: Idea kept before seeding
- **WHEN** the user asks during ideation to keep a reading list and no slug exists yet
- **THEN** it is written into the idea's folder as `reading-list.md` and moves with the folder at every later rename

#### Scenario: Workspace build leaves its output
- **WHEN** the publish step runs a workspace build definition that reads `faculty.typ` and writes `proposal.pdf` in the proposal's folder
- **THEN** both files are allowed, and no skill renames or removes them

#### Scenario: Installer files left alone
- **WHEN** the workspace holds `.agents/skills/` with an install record inside and a `skills-lock.json` in its root
- **THEN** no skill writes, moves or deletes either, a rename included

## REMOVED Requirements

### Requirement: Flat workspace with shared image folder
**Reason**: Proposals no longer sit side by side at the top level; each lives in a folder of its own, with its figures in that folder's `img/` and no slug prefix (requirement: One folder per proposal).
**Migration**: Move each proposal and its family into `<location>/<slug>/` by hand, renaming companions to their role names and figures to drop the slug prefix (design, Migration). The scenario "Proposal without figures" moves to "One folder per proposal".
