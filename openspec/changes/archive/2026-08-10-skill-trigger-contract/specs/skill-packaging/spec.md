## ADDED Requirements

### Requirement: Descriptions state what the skill does and when to use it
Every skill's frontmatter `description` SHALL be written in the third person and SHALL carry both what the skill produces and the situations that should trigger it. Trigger clauses SHALL name the situations in the vocabulary a user would use to describe their own position, not only the vocabulary this package uses for the task, and SHALL cover the languages the intended users write in. A description SHALL NOT be the only place a rule is stated, and SHALL NOT promise behaviour the skill does not implement.

#### Scenario: Description written in the second person
- **WHEN** a description addresses the reader as "you" or speaks as "I"
- **THEN** the packaging checks fail

#### Scenario: Trigger clause absent
- **WHEN** a description states only what the skill does, with no triggering situation
- **THEN** the packaging checks fail

### Requirement: One owner per contested trigger term
High-signal trigger terms SHALL be assigned to exactly one skill in a tracked table, and a skill SHALL NOT use a term its description does not own. Terms that are legitimately common across skills SHALL be listed explicitly as shared rather than left implicit. Moving a term between owners SHALL require editing the table, so a boundary change is visible in review rather than emerging from a reworded sentence.

#### Scenario: Second skill claims an owned term
- **WHEN** a skill's description uses a trigger term another skill owns
- **THEN** the packaging checks fail, naming both skills and the term

#### Scenario: Boundary deliberately moved
- **WHEN** the owned-trigger table assigns a term to a different skill and that skill's description uses it
- **THEN** the packaging checks pass

### Requirement: A skill that declines a contested situation names the one that owns it
Where two skills plausibly answer the same user situation, the skill that does not own that situation SHALL say so in its description and SHALL name the skill that does. Disambiguation SHALL be visible at selection time, since no skill body has been loaded when the choice is made.

#### Scenario: Adjacent skill named
- **WHEN** a description declines a neighbouring situation
- **THEN** it names the skill that handles it

### Requirement: Frontmatter contract
Every skill's frontmatter `name` SHALL equal its directory name and SHALL be within the length the skill format allows. The `description` SHALL be within both the format's limit and a tighter repository budget, and the combined metadata of all skills SHALL stay within a stated total, because every skill's metadata is loaded into context whether or not that skill is used. Frontmatter SHALL carry no keys outside the set this package uses.

#### Scenario: Name diverges from its directory
- **WHEN** a skill's frontmatter name does not match the directory it lives in
- **THEN** the packaging checks fail

#### Scenario: Metadata budget exceeded
- **WHEN** the combined frontmatter of all skills exceeds the stated total
- **THEN** the packaging checks fail

#### Scenario: Unknown frontmatter key
- **WHEN** frontmatter carries a key outside the supported set
- **THEN** the packaging checks fail

### Requirement: Body size limits
A skill body SHALL stay within the line limit published in the skill-authoring guidance this package follows, and SHALL NOT exceed twice the median body size of the suite, so that one skill cannot grow disproportionate to its siblings without the growth being noticed. Content beyond those limits SHALL move to reference files rather than raising the limits.

#### Scenario: Body exceeds the published cap
- **WHEN** a SKILL.md body grows past the guidance's line limit
- **THEN** the packaging checks fail

#### Scenario: One skill outgrows its siblings
- **WHEN** a body exceeds twice the median body size across the suite
- **THEN** the packaging checks fail
