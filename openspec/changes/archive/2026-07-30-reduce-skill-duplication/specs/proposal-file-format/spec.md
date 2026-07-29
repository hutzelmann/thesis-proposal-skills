# proposal-file-format Delta

## ADDED Requirements

### Requirement: Skill prose must not drift from the format contract
Every skill whose instructions describe the single-file format SHALL state the canonical contract consistently: the metadata block keys (`title`, `author`, `subtitle`, `lang`, `references`), the trailing position of the block, and the blank-line rule. Automated verification SHALL fail when any skill's format prose diverges from the canonical contract.

#### Scenario: Contract element lost in one skill
- **WHEN** the format description in one skill's instructions drops or renames a canonical metadata key
- **THEN** the drift verification fails naming that skill

#### Scenario: All skills consistent
- **WHEN** every format-describing skill states the full canonical contract
- **THEN** the drift verification passes
