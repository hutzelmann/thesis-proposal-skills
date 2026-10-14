## ADDED Requirements

### Requirement: Proposal family under one handle
A proposal's slug (Content-derived slug filenames) SHALL be its file name without `.md`, and SHALL be the handle that names every file of its family. Every file a skill writes for a proposal SHALL be named by that slug, SHALL sit in the proposal location, and SHALL belong to one closed family:

- the proposal `<slug>.md`;
- the notes file `<slug>.notes.md` and the harvest record `<slug>.harvest.md`;
- the review `<slug>-review.md`, the supervisor feedback `<slug>-feedback.md`, and the hand-in export `<slug>-handout.md`;
- the built document and its intermediates: `<slug>.pdf`, `<slug>.typ`, `<slug>.tex`, `<slug>.docx`;
- figures in the shared `img/` folder beside the proposal, named `img/<slug>-<name>.<ext>`;
- files the user asked to keep, named `<slug>.<label>.<ext>` (requirement: Working material stays out of the workspace).

Before any topic phrase exists, ideation notes SHALL be named `ideation.notes.md`, which carries no slug.

The slug SHALL be derived from the title when the proposal file is first written, under the bounds of Content-derived slug filenames. Before that, a provisional slug derived from the topic phrase SHALL name the notes file. Once the proposal file exists, the slug SHALL NOT follow later title changes, and a full draft of an idea whose proposal file already exists, such as an ideation seed, SHALL be written into that file. Only a rename changes the slug (requirement: A rename moves the whole family).

#### Scenario: Family recognisable from the listing
- **WHEN** a workspace holds a proposal that has been seeded, reviewed, illustrated and built
- **THEN** every file belonging to it either starts with its slug followed by `.`, `-review`, `-feedback` or `-handout`, or sits in the `img/` folder beside it with a name starting `<slug>-`

#### Scenario: Title changed after the proposal exists
- **WHEN** a writing pass adopts a new title for an existing proposal and the user has not asked for a rename
- **THEN** the leading `# ` line carries the new title and every family file keeps its name

#### Scenario: Draft from a seed keeps the seed's file
- **WHEN** a writing pass drafts a full proposal from an ideation seed `<slug>.md`
- **THEN** the draft is written into `<slug>.md`, and no second proposal file for the idea exists afterwards

#### Scenario: Ideation without a topic phrase
- **WHEN** an ideation session ends at an impasse before any topic phrase emerged
- **THEN** its state is recorded in `ideation.notes.md` and no file carries a slug

### Requirement: A rename moves the whole family
A slug SHALL change only at the seeding step, when the slug derived from the settled working title differs from the provisional one, or when the user asks for a rename. Either way the rename SHALL move every family member under the old slug to the new slug: the notes file, harvest record, review, feedback, handout, kept files and `img/<old>-*` figures. Built outputs SHALL stay in place as previous builds; the skill SHALL name them and offer a rebuild, which writes them under the new slug. The rename SHALL update every reference to a moved file inside the proposal and its notes file, and SHALL NOT edit the text of a review or feedback file.

Before moving anything, the skill SHALL check every target name:

- at seeding, when a target name under the derived slug is taken, the slug SHALL take the numeric suffix of Content-derived slug filenames, and the family SHALL move to the suffixed slug;
- on a requested rename, when a target name is taken, nothing SHALL be moved; the skill SHALL name the collision and propose the suffixed slug.

No file SHALL be overwritten. When a member cannot be moved, the skill SHALL stop, SHALL say which files moved and which did not, and SHALL update references only for the files that moved. The skill SHALL say in chat which files it renamed. A rename SHALL NOT move or rewrite workspace-level files or installer-managed files.

#### Scenario: Requested rename with a linked figure
- **WHEN** the user asks to rename a proposal that has a notes file, a review and a figure `img/<old>-pipeline.png` linked from the proposal
- **THEN** afterwards the proposal, notes file, review and figure all carry the new slug, the proposal links `img/<new>-pipeline.png`, and no family member other than a built output remains under the old slug

#### Scenario: Requested rename onto a taken name
- **WHEN** the user asks for a rename and a file named under the requested new slug already exists
- **THEN** no file is moved, the skill names the collision, and it proposes the suffixed slug

#### Scenario: Seeding onto a taken name
- **WHEN** the slug derived from the settled working title is already taken by another proposal's file
- **THEN** the seed and its family carry the slug with the numeric suffix, and no file is overwritten

#### Scenario: Seeding under a diverged provisional slug
- **WHEN** ideation notes, a kept reading list and a sketch under `img/` carry a provisional slug and the settled working title yields a different slug
- **THEN** after seeding, the seed, the notes file, the reading list and the sketch all carry the seed's slug

#### Scenario: Member that cannot be moved
- **WHEN** one family member cannot be moved during a rename, for example because another program holds it open
- **THEN** the skill stops, names what moved and what did not, overwrites nothing, and the references point only at files that moved

#### Scenario: Built output at a rename
- **WHEN** a renamed proposal had a built `<old>.pdf`
- **THEN** `<old>.pdf` stays in place, the chat names it as a previous build, and a rebuild is offered

### Requirement: Working material stays out of the workspace
Skills SHALL write into the workspace only the following:

- proposal families (requirement: Proposal family under one handle), in the proposal location;
- the workspace-level files at the workspace root: `guidelines.md`, `api-keys.env`, the `bug-report/` folder and the root `.gitignore`;
- beside a proposal: a workspace build definition (a file named `proposal-build` with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the `.gitignore` the built-in build adds there, and whatever a workspace build definition reads and writes when the publish step runs it (skill-publish: Workspace-supplied build definition takes precedence);
- the troubleshooting captures `check-output.txt` and `version-output.txt` while a bug report is being assembled.

The installer-managed files are the skill folders `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the install record `.thesis-proposal-install.json`, and `skills-lock.json` in the workspace root. No skill SHALL write, move or delete them.

Working material SHALL stay in the chat: script output, candidate lists, raw responses, probes, logs and scratch drafts. When it is too large to read in one piece, the skill SHALL read it in slices or produce it narrower. A temporary location outside the workspace MAY hold it, but only when one is writable. When none is writable, the skill SHALL read in slices or narrow the run instead, and SHALL NOT fall back to the workspace. A proposal family member SHALL never be written into a host's scratch or temporary folder. Working material SHALL be kept in the workspace only when the user asks. It is then written beside the proposal as a family member named `<slug>.<label>.<ext>`, with a label other than `notes` or `harvest`. Before a slug exists, it is recorded in the notes file instead.

#### Scenario: Search output larger than the host shows
- **WHEN** a literature search emits more output than the host shows from one command
- **THEN** the skill runs narrower and adds no file to the workspace

#### Scenario: Sandbox without a writable temporary folder
- **WHEN** the host refuses writes to the system temporary folder and a script's output is too large to read in one piece
- **THEN** the skill reads it in slices or narrows the run instead of writing the output into the workspace

#### Scenario: User asks to keep a candidate list
- **WHEN** the user asks to keep the candidate list of a search for a proposal
- **THEN** it is written beside the proposal as `<slug>.<label>.<ext>` and nothing else is added

#### Scenario: Workspace build leaves its output
- **WHEN** the publish step runs a workspace build definition that reads `faculty.typ` and writes `proposal.pdf` beside the proposal
- **THEN** both files are allowed, and no skill renames or removes them

#### Scenario: Installer files left alone
- **WHEN** the workspace holds `.agents/skills/` with an install record inside and a `skills-lock.json` in its root
- **THEN** no skill writes, moves or deletes either, a rename included
