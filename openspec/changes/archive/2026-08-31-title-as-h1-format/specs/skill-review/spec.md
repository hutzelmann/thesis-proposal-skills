# skill-review Delta

## MODIFIED Requirements

### Requirement: Format-agnostic
The review SHALL NOT complain about section layout, ordering, headings, or markup conventions — structure compliance belongs to check. The proposal's thesis title is content, not layout, and is therefore in scope for the review despite being carried by the leading `# ` line: the review judges the title's text and stays silent about its markup.

#### Scenario: Non-canonical structure
- **WHEN** the proposal uses a free-form section structure
- **THEN** the review addresses only content and arguments, with no structural complaints

#### Scenario: Title assessed anyway
- **WHEN** the review reaches the leading `# ` title line
- **THEN** it assesses the title as content and stays silent about the line's heading markup

#### Scenario: Metadata title assessed anyway
- **WHEN** an old-format proposal still carries its title in the metadata block
- **THEN** the review assesses that title as content and stays silent about the block's markup
