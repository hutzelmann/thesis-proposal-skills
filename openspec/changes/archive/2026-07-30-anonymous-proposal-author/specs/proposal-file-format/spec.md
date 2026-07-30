## MODIFIED Requirements

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
