# skill-packaging Specification

## Purpose
How the skills are packaged, named, kept self-contained, and distributed to user workspaces via the skills.sh ecosystem.
## Requirements
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

### Requirement: Functional self-containment
Each skill SHALL be functional standalone: installed alone, it fulfills its purpose without requiring any sibling skill. Shared guidance, structured data, and cross-skill scripts are provided through one of two declared paths:

1. **Synchronized copy** — the asset is materialized as a committed copy inside the consuming skill from a single dev-side source. Generated copies carry a generated-file marker, and automated verification SHALL fail when copies drift from the source.
2. **Sibling fallback** — the skill uses a sibling skill's files when that sibling is installed, and its SKILL.md SHALL document the degraded behavior used when the sibling is absent. This path is only permitted where the degraded mode still fulfills the skill's purpose; assets required for a skill's core function SHALL be synchronized copies.

#### Scenario: Shared guidance edited
- **WHEN** the shared source changes without re-materializing copies
- **THEN** the sync verification fails

#### Scenario: Sibling absent
- **WHEN** a skill with a declared sibling fallback runs in a workspace where the sibling skill is not installed
- **THEN** the skill performs its documented degraded behavior instead of failing opaquely

#### Scenario: Asset needed for core function
- **WHEN** a shared asset is required for a skill's core purpose rather than for enrichment
- **THEN** the skill ships it as a synchronized copy, not as a sibling fallback

### Requirement: Commit-time sync automation
Materialization of synchronized copies SHALL run automatically at commit time in the development repository, so a commit touching a shared source cannot leave stale copies behind. Continuous integration SHALL keep an independent drift check as backstop for bypassed hooks.

#### Scenario: Shared source edited and committed
- **WHEN** a contributor edits a shared source and commits without manually running the sync script
- **THEN** the commit contains freshly materialized copies

#### Scenario: Hook bypassed
- **WHEN** stale copies reach the repository with commit-time automation bypassed
- **THEN** the continuous-integration drift check fails

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

