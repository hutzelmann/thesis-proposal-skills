# proposal-file-format Specification

## Purpose
Defines the single-file storage format for thesis proposals and the conventions of the flat multi-proposal user workspace.
## Requirements
### Requirement: Single-file proposal with trailing metadata block
A proposal SHALL be stored as one markdown file: body text on top, followed by exactly one YAML metadata block at the end of the file carrying at least `title`, `subtitle`, `lang`, and `references` (CSL-YAML list). The file MUST be consumable by standard pandoc + citeproc without preprocessing. A proposal SHALL NOT carry the identity of its writer: `author` is not part of the metadata contract, and no skill SHALL create it or a placeholder for it.

#### Scenario: Valid file renders with resolved citations
- **WHEN** a proposal file with body citations and a trailing metadata block is processed by pandoc with citeproc
- **THEN** all citations resolve against the `references` entries and a bibliography is produced

#### Scenario: Blank line must precede the trailing block
- **WHEN** the trailing `---` block is not preceded by a blank line
- **THEN** the file is treated as malformed (metadata silently becomes body text) and tooling SHALL flag it

#### Scenario: Proposal created with the writer's name unknown
- **WHEN** a skill creates or updates a proposal file and no writer name is known
- **THEN** the metadata block contains no `author` key and no `[TODO: add author]` placeholder, because the name is never expected

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

### Requirement: Language declaration
Each proposal SHALL declare its language via `lang: en` or `lang: de` in the metadata block; all skills operating on the proposal SHALL honor it.

#### Scenario: German proposal
- **WHEN** a proposal declares `lang: de`
- **THEN** generated text, section titles, and citation locale follow German conventions

### Requirement: Visible TODO markers
Placeholders for missing information SHALL use the visible form `[TODO: <3–10 word hint>]` in the body text.

#### Scenario: Missing reference
- **WHEN** a writing step lacks a needed source
- **THEN** it inserts `[TODO: add key reference for X]` instead of fabricating one

### Requirement: Skill prose must not drift from the format contract
Every skill whose instructions describe the single-file format SHALL state the canonical contract consistently: the metadata block keys (`title`, `subtitle`, `lang`, `references`), the trailing position of the block, and the blank-line rule. No skill's format prose SHALL name `author` as a metadata key. Automated verification SHALL fail when any skill's format prose diverges from the canonical contract.

#### Scenario: Contract element lost in one skill
- **WHEN** the format description in one skill's instructions drops or renames a canonical metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: Author key reintroduced
- **WHEN** a skill's format prose reintroduces `author` as a metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: All skills consistent
- **WHEN** every format-describing skill states the full canonical contract
- **THEN** the drift verification passes

