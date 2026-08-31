# skill-troubleshoot Delta

## MODIFIED Requirements

### Requirement: Graded redaction with the most protective default

The user SHALL choose how much of their proposal the report carries, from a graded set whose least-disclosing level carries no proposal prose at all — only structural counts, hashes, script output and environment facts. Intermediate levels add structure without body text; the most disclosing level adds proposal text with the personal-data rules already governing proposals applied to it.

The thesis title is proposal text, not structure, even though the format carries it as the leading `# ` heading: levels below the most disclosing one SHALL mask the title heading rather than print it, and structural counts that classify headings as canonical or custom SHALL exclude the title heading rather than report it as a permanently non-canonical entry.

The default SHALL be the least-disclosing level. Before writing anything, the skill SHALL state what the chosen level includes and what the next level up would add, so the choice is informed rather than inferred. The proposal is an unpublished research idea, so silence about disclosure is not an acceptable default.

#### Scenario: User does not state a level

- **WHEN** a report is assembled without the user naming a disclosure level
- **THEN** the least-disclosing level is used

#### Scenario: Disclosure stated before writing

- **WHEN** the skill is about to write a report
- **THEN** it first states what the chosen level includes and what the next level would add

#### Scenario: Most disclosing level chosen

- **WHEN** the user chooses the level that carries proposal text
- **THEN** the personal-data rules that govern proposals are applied to that text before it enters the report

#### Scenario: Structure level does not disclose the title

- **WHEN** a report is assembled at a level that lists headings
- **THEN** the leading `# ` title heading appears masked, never verbatim, and the canonical-heading tally does not count it
