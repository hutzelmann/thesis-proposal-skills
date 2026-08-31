# proposal-file-format Delta

## MODIFIED Requirements

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

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Language declaration
**Reason**: The `lang` key is retired with the metadata block's reduction to the bibliography database; the language is fully determined by the canonical subtitle and section-title wordings the format already mandates, so declaring it duplicated derivable state.
**Migration**: Tooling infers the language per the added Language inference requirement; a leftover `lang:` key is flagged as retired and otherwise ignored.
