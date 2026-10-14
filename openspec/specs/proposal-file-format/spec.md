# proposal-file-format Specification

## Purpose
Defines the single-file storage format for thesis proposals and the conventions of the flat multi-proposal user workspace.

## Requirements

### Requirement: Single-file proposal with trailing metadata block
A proposal SHALL be stored as one markdown file whose body opens with the document itself: the first content line is `# <title>` — the file's only H1 and the sole source of the thesis title — followed by a blank line and the subtitle as one paragraph wrapped entirely in `*…*` emphasis. The five canonical sections follow at H2 with methodology subsections at H3, and the body ends with the closing references section. After the body, separated by a blank line, exactly one YAML metadata block ends the file carrying `references` (CSL-YAML list) and nothing else.

The file MUST be consumable by standard pandoc + citeproc without preprocessing; the canonical invocation maps the body onto document metadata and section levels via pandoc's own heading-shift mechanism, which promotes the leading H1 to the document title only when it is the file's first block — which is why the title line MUST be the first content line.

A proposal SHALL NOT carry the identity of its writer: `author` is not part of the metadata contract, and no skill SHALL create it or a placeholder for it. The keys `title`, `subtitle`, and `lang` are retired from the metadata block: no skill SHALL write them, and tooling SHALL flag each of them when present, in the same way `author` is flagged — a student who sets `author` or `lang` deliberately for an external pipeline receives the finding as expected notice, not as breakage.

#### Scenario: Valid file renders with resolved citations
- **WHEN** a proposal file with body citations and a trailing metadata block is processed by pandoc with citeproc
- **THEN** all citations resolve against the `references` entries and a bibliography is produced

#### Scenario: Blank line must precede the trailing block
- **WHEN** the trailing `---` block is not preceded by a blank line
- **THEN** the file is treated as malformed (metadata silently becomes body text) and tooling SHALL flag it

#### Scenario: Proposal created with the writer's name unknown
- **WHEN** a skill creates or updates a proposal file and no writer name is known
- **THEN** the metadata block contains no `author` key and no `[TODO: add author]` placeholder, because the name is never expected

#### Scenario: Retired key present in the metadata block
- **WHEN** the metadata block carries a `title:`, `subtitle:`, or `lang:` key
- **THEN** tooling flags the key as retired and names the body location that now carries the value

#### Scenario: Content above the title line
- **WHEN** any content block precedes the leading `# <title>` line
- **THEN** tooling flags the misplaced title, because pandoc would silently demote the heading to a paragraph and build a document with no title

#### Scenario: Subtitle paragraph under the title
- **WHEN** a proposal is created for a Master's student writing in German
- **THEN** the line after the title block is `*Exposé zur Masterarbeit*`, and no `subtitle` key appears in the metadata block

### Requirement: Citation syntax and key constraints
Citations SHALL use `[@key]` (bracketed) or `@key` (author-in-text). Citation keys MUST NOT be YAML boolean literals (`y`, `n`, `yes`, `no`, `on`, `off`, `true`, `false` in any case).

The two syntaxes carry different rendered meanings and both SHALL be available within a single proposal. The bracketed form renders as the reference number alone. The author-in-text form renders as an author label derived from the reference entry, followed by the reference number, so the cited authors can serve as the subject of a sentence. An author-in-text citation MAY carry a suffix, including a locator or a further citation, which renders after the author label.

#### Scenario: Boolean-literal key rejected
- **WHEN** a reference uses the id `on`
- **THEN** the check tooling reports it as an invalid key

#### Scenario: Bracketed form stays bare
- **WHEN** the body attaches a bracketed citation to a claim
- **THEN** the rendered output shows the reference number without an author name

#### Scenario: Author-in-text form carries the name
- **WHEN** the body opens a sentence with an author-in-text citation whose reference has three authors
- **THEN** the rendered output shows the first author's surname, "et al.", and the reference number, and the sentence is grammatical

#### Scenario: Author-in-text citation with a citation in its suffix
- **WHEN** the body writes an author-in-text citation whose suffix contains a further citation
- **THEN** the rendered output shows the author label, the first reference's number, and the suffix with the second reference's number

#### Scenario: Several author-in-text citations in one sentence
- **WHEN** a sentence names two works in a row, each in the author-in-text form
- **THEN** each renders with its own author label and reference number

### Requirement: Content-derived slug filenames
Proposal filenames SHALL be content-derived slugs — lowercase ASCII, hyphen-separated, 2–4 words derived from the title — never a generic name. On collision a numeric suffix SHALL be appended.

#### Scenario: Two similar topics
- **WHEN** a second proposal about a similar topic is created and the natural slug is taken
- **THEN** the new file receives the slug with a numeric suffix

### Requirement: Flat workspace with shared image folder
The workspace SHALL hold multiple unrelated proposals side by side at the top level. Images live in a shared `img/` folder created only when needed, with filenames prefixed by the owning proposal's slug.

#### Scenario: Proposal without figures
- **WHEN** a proposal uses no figures
- **THEN** no `img/` folder is created for it

### Requirement: Proposal targeting
Skills SHALL resolve the target proposal from an explicit user mention; with exactly one candidate file in the workspace it SHALL be auto-picked; with several candidates and no mention, the skill SHALL list candidates and ask. A candidate is a markdown file ending in a pandoc metadata block.

#### Scenario: Ambiguous workspace
- **WHEN** the workspace holds three proposal files and the user names none
- **THEN** the skill lists the three candidates and asks which to use

### Requirement: Visible TODO markers
Placeholders for missing information SHALL use the visible form `[TODO: <3–10 word hint>]` in the body text. The leading `# <title>` line and the subtitle paragraph MAY carry a marker in the same form; no other heading SHALL carry one, and a marker inside the `references` block is not a placeholder and carries no meaning. A marker SHALL be rendered by the build as a distinguishable annotation rather than as prose, so that the promise of visibility holds in the compiled document and not only in the source file.

#### Scenario: Missing reference
- **WHEN** a writing step lacks a needed source
- **THEN** it inserts `[TODO: add key reference for X]` instead of fabricating one

#### Scenario: Undecided degree level
- **WHEN** a proposal is created before the degree level is settled
- **THEN** the subtitle paragraph may read `*[TODO: state the degree level]*`, and the built document shows it as an annotation in the title block

#### Scenario: Unsettled title
- **WHEN** a proposal exists before its title is settled
- **THEN** the leading line may read `# [TODO: working title naming the contribution]`, and the built document shows the marker as an annotation in the title block

#### Scenario: Marker survives the build as a marker
- **WHEN** a proposal containing markers is built into a document
- **THEN** each marker is visually distinguishable from the surrounding prose rather than typeset as an ordinary sentence

### Requirement: Skill prose must not drift from the format contract
Every skill whose instructions describe the single-file format SHALL state the canonical contract consistently: the leading `# <title>` line as the file's only H1, the emphasized subtitle paragraph beneath it, the closing references section, the trailing metadata block carrying `references` in its trailing position, and the blank-line rule. No skill's format prose SHALL name `author`, `title`, `subtitle`, or `lang` as a metadata key. Automated verification SHALL fail when any skill's format prose diverges from the canonical contract.

#### Scenario: Contract element lost in one skill
- **WHEN** the format description in one skill's instructions drops the leading-H1 rule or renames the canonical metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: Author key reintroduced
- **WHEN** a skill's format prose reintroduces `author` as a metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: Retired key reintroduced
- **WHEN** a skill's format prose reintroduces `title`, `subtitle`, or `lang` as a metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: All skills consistent
- **WHEN** every format-describing skill states the full canonical contract
- **THEN** the drift verification passes

### Requirement: Companion notes file
A proposal `<slug>.md` MAY have a companion working-knowledge file named `<slug>.notes.md` in the same directory. The notes file SHALL use five canonical top-level sections in this order: `## Decisions`, `## Open Points`, `## Next Focus`, `## Excluded Literature`, `## Log`. Section content is free prose or bullets; no mechanical check SHALL validate content beyond the file being markdown — the canonical sections exist so skills know where to read and write, not as a schema.

The notes file is workspace-internal: it SHALL never be built, published, or submitted, and skills that build, check, or review the proposal SHALL ignore it. A notes file SHALL NOT be treated as a proposal candidate by proposal targeting.

#### Scenario: Notes file beside its proposal
- **WHEN** a workspace holds `energy-attack-detection.md` and `energy-attack-detection.notes.md`
- **THEN** proposal targeting offers only `energy-attack-detection.md` as a candidate and the notes file is ignored by check, review, and publish

#### Scenario: Notes file alone is not a proposal
- **WHEN** a workspace holds only a `*.notes.md` file and no proposal
- **THEN** skills that need a proposal report none found rather than operating on the notes file

### Requirement: Blocking-TODO split between proposal and notes
`[TODO: …]` markers in the proposal file SHALL be reserved for submission-blocking content gaps — information the finished document cannot ship without. Working knowledge that does not block submission — decisions and their rationale, rejected alternatives, non-blocking open points, next steps — SHALL live in the companion notes file, not as proposal TODOs. When a proposal TODO is resolved, the resolving skill SHALL move it to the notes file's Log section as a done entry (original marker text plus what resolved it) instead of deleting it silently.

#### Scenario: Non-blocking knowledge kept out of the proposal
- **WHEN** a session decides between two candidate methodologies and records why the loser was rejected
- **THEN** the rationale lands in the notes Decisions section and the proposal carries no TODO about it

#### Scenario: Resolved TODO leaves a trace
- **WHEN** a skill fills the gap behind `[TODO: state the delta to prior work]`
- **THEN** the marker disappears from the proposal and the notes Log gains a done entry naming that marker and its resolution

### Requirement: Closing references section
The body SHALL end with a references section: a heading titled "References" (English) or "Literatur" (German) as the last section of the document, with an empty body — the rendered bibliography is produced beneath it by the build, and the raw file gains a visible marker that what follows the `---` is the bibliography database. Tooling SHALL flag a proposal whose references section is missing, not last, or non-empty.

#### Scenario: References section present and last
- **WHEN** a proposal ends its body with the references heading directly above the trailing metadata block
- **THEN** no finding is emitted and the built document renders the bibliography under that heading

#### Scenario: References section carries prose
- **WHEN** the references section contains body text or hand-written entries
- **THEN** tooling flags it, because entries live in the metadata block and the section exists as a heading only

#### Scenario: References section missing
- **WHEN** the body ends with the timeline section and no references heading
- **THEN** tooling flags the missing section

### Requirement: Language inference
A proposal SHALL NOT declare its language. All tooling operating on the proposal SHALL infer it deterministically, without model judgement, from the workspace-resolved canonical wordings: an exact match of the subtitle paragraph against the canonical subtitle wordings decides first; otherwise the majority of canonical section-title matches decides; when neither decides, tooling SHALL report the language as undeterminable and fall back to English for its own messages. Skills SHALL honor the inferred language exactly as they honored the declared one, and the build SHALL pass the inferred language to the toolchain so localization (citation locale, hyphenation, bibliography headline) is unchanged.

#### Scenario: German proposal inferred from the subtitle
- **WHEN** a proposal's subtitle paragraph is `*Exposé zur Bachelorarbeit*`
- **THEN** all tooling treats the proposal as German — generated text, section titles, and citation locale follow German conventions

#### Scenario: Subtitle is a TODO marker
- **WHEN** the subtitle paragraph carries a `[TODO: …]` marker and the five section headings match the German canonical titles
- **THEN** the proposal is treated as German by section-title majority

#### Scenario: Language undeterminable
- **WHEN** neither the subtitle nor a majority of section titles matches either language's canonical wordings
- **THEN** tooling reports the language as undeterminable as a finding and emits its own messages in English

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
