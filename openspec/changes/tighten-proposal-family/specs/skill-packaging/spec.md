## ADDED Requirements

### Requirement: Workspace-files block in every skill
The workspace rules SHALL be stated once, as a shared block, and materialized into every shipped `SKILL.md` by the automation that materializes the other shared blocks. The block SHALL cover:

- the proposal location: the working directory, unless the workspace `guidelines.md` configures a subdirectory; a proposal's files never go into a host's scratch or temporary folder;
- the proposal family, listed once as a table from each role (proposal, notes, harvest record, review, supervisor feedback, handout, built output, kept file, figure, ideation notes) to its file name, and its slug, including that a rename moves the whole family (proposal-file-format);
- the workspace-level, build, troubleshooting-capture and installer-managed files that may also be present;
- the rule that working material stays out of the workspace, including what to do when no temporary location is writable.

The block SHALL be the whole content of a `## Workspace files` section placed directly before `## Handing over`. No per-skill sentence SHALL be added to that section. Outside the block, a skill's prose SHALL refer to the proposal location without restating its definition, except where a pinned mandate or a script-location fallback paragraph already states it; this requirement changes neither.

The offline suite SHALL fail in any of these cases:

- the section is missing, appears more than once, or stands anywhere but directly before `## Handing over`;
- its content differs from the block;
- it holds anything beyond the block.

The materialization SHALL locate the block's paragraphs without consuming a sentence added after them, so a skill-specific addition fails the suite instead of being silently deleted. The roles of the block's family table SHALL be the roles the mechanical check classifies family files into, and each row's file names SHALL classify as its role. The file names the block lists as allowed and the file names the mechanical check never reports SHALL agree, and the installer-managed folders the block names SHALL agree with the installer's own tables. The offline suite SHALL fail when one side names a role or a file the other does not.

#### Scenario: Block reworded
- **WHEN** the block's source is reworded and the sync runs
- **THEN** every skill's `## Workspace files` section carries the new wording and nothing else in any `SKILL.md` changes

#### Scenario: Skill-specific sentence appended to the section
- **WHEN** a contributor appends a sentence after the block in one skill's `## Workspace files` section
- **THEN** the offline suite fails naming that skill, and running the sync leaves the sentence in place

#### Scenario: Section misplaced
- **WHEN** one skill's `## Workspace files` section stands anywhere but directly before `## Handing over`
- **THEN** the offline suite fails naming that skill, and the sync refuses to write it

#### Scenario: Family table drifts from the check
- **WHEN** the block's family table gains a role the mechanical check does not classify, or the check gains a role the table lacks
- **THEN** the offline suite fails naming the role

#### Scenario: Allowed names drift from the check
- **WHEN** the block gains an allowed workspace file that the mechanical check would still report, or the reverse
- **THEN** the offline suite fails naming the file

#### Scenario: Installer gains a skill folder
- **WHEN** the installer's tables gain a workspace skill folder that the block does not name
- **THEN** the offline suite fails naming the folder

#### Scenario: Body size after the block lands
- **WHEN** the block is materialized into all eleven skills
- **THEN** every body stays within the published line limit and within twice the suite's median body size
