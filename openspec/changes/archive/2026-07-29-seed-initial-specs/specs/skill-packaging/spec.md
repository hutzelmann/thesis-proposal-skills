# Delta: skill-packaging

## Purpose

How the skills are packaged, named, kept self-contained, and distributed to user workspaces via the skills.sh ecosystem.

## ADDED Requirements

### Requirement: Registry installation from the repository
The skill set SHALL be installable from the public repository via the skills.sh CLI, both all-at-once and per-skill. What is committed on the default branch is what users receive.

#### Scenario: Selective install
- **WHEN** a user installs only the write skill
- **THEN** that skill arrives functional without requiring any sibling skill

### Requirement: Collision-safe naming
Every skill's frontmatter `name` SHALL carry the `proposal-` prefix (the installed directory name derives from the frontmatter name, and same-named skills from other packages silently overwrite each other).

#### Scenario: Installation directory
- **WHEN** any skill of this package is installed
- **THEN** its installed directory name starts with `proposal-`

### Requirement: Self-contained skills via synchronized copies
Each skill SHALL be self-contained: shared guidance, structured data, and cross-skill scripts are materialized as committed copies inside each consuming skill from a single dev-side source. Generated copies carry a generated-file marker, and automated verification SHALL fail when copies drift from the source.

#### Scenario: Shared guidance edited
- **WHEN** the shared source changes without re-materializing copies
- **THEN** the sync verification fails

### Requirement: User-side script constraints
Scripts shipped inside skills SHALL run on stock Python ≥ 3.11 standard library only (no package installs), work on Windows/macOS/Linux, never general-parse YAML (narrow documented extraction only), detect missing interpreters/tools with install guidance, and document an agent-side fallback when script networking is denied.

#### Scenario: Windows machine without python3 alias
- **WHEN** a script-bearing skill runs where only the `py` launcher exists
- **THEN** the skill detects and uses it or guides the user, rather than failing opaquely

### Requirement: Rolling release policy
While the package has no outside users, the default branch SHALL serve as the release channel; tagged releases SHALL begin once outside users exist.

#### Scenario: Pre-adoption phase
- **WHEN** changes merge during the no-outside-users phase
- **THEN** they are immediately live for installers without further release steps
