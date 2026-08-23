## MODIFIED Requirements

### Requirement: Frontmatter contract
Every skill's frontmatter `name` SHALL equal its directory name and SHALL be within the length the skill format allows. The `description` SHALL be within both the format's limit and a tighter repository budget, and the combined metadata of all skills SHALL stay within a stated total, because every skill's metadata is loaded into context whether or not that skill is used. Beyond `name` and `description`, frontmatter MAY carry exactly three optional keys defined by the Agent Skills standard, each under a per-field rule; frontmatter SHALL carry no other keys.

- `license` SHALL be present on every skill and SHALL agree with the license the repository ships at its root, so the installed skill folder carries its terms.
- `compatibility` SHALL appear only on skills with genuine environment requirements beyond a standard agent setup — the publish skill (document toolchain) and the literature-search skill (network access) — and SHALL be rejected on any other skill, so the field keeps signal.
- `metadata` SHALL carry only a `version` entry — the suite's semantic version, shared by all skills and copied by the publish pipeline from its single hand-edited source; it SHALL NOT be hand-maintained in the skills, and one version SHALL never name two published snapshots.

#### Scenario: Name diverges from its directory
- **WHEN** a skill's frontmatter name does not match the directory it lives in
- **THEN** the packaging checks fail

#### Scenario: Metadata budget exceeded
- **WHEN** the combined frontmatter of all skills exceeds the stated total
- **THEN** the packaging checks fail

#### Scenario: Unknown frontmatter key
- **WHEN** frontmatter carries a key outside the admitted set
- **THEN** the packaging checks fail

#### Scenario: Optional field on the wrong skill
- **WHEN** `compatibility` appears on a skill without stated environment requirements
- **THEN** the packaging checks fail

#### Scenario: License field drifts from the shipped license
- **WHEN** a skill's `license` value no longer agrees with the repository's root license
- **THEN** the packaging checks fail

#### Scenario: Version stamped at publish
- **WHEN** the publish pipeline runs
- **THEN** every skill's `metadata.version` identifies the published snapshot, and a bug report against that snapshot resolves to it without searching revision history
