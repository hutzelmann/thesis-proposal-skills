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

A skill's instructions SHALL address its own scripts by a path that resolves from the agent's working directory, which is the user's workspace and not the skill's directory. The instruction SHALL also name the skill-relative location, so it stays correct when the skill is installed somewhere other than the workspace's own skill folder.

A skill that cannot locate a script it ships SHALL say so, and SHALL say what consequently went unverified. It SHALL NOT silently substitute its own inspection for a deterministic script: the script exists because the agent's unaided judgement is not equivalent to it.

#### Scenario: Windows machine without python3 alias

- **WHEN** a script-bearing skill runs where only the `py` launcher exists
- **THEN** the skill detects and uses it or guides the user, rather than failing opaquely

#### Scenario: Agent runs a documented script command

- **WHEN** an agent working in the user's workspace runs a script invocation exactly as the skill's instructions give it
- **THEN** the path resolves to the installed script

#### Scenario: Script cannot be found

- **WHEN** a skill's script is absent or cannot be located
- **THEN** the skill reports that the script did not run and names what was therefore not verified, instead of presenting its own inspection as the script's result

### Requirement: Rolling release policy
While the package has no outside users, the default branch SHALL serve as the release channel; tagged releases SHALL begin once outside users exist.

#### Scenario: Pre-adoption phase
- **WHEN** changes merge during the no-outside-users phase
- **THEN** they are immediately live for installers without further release steps

### Requirement: Pre-publish local security gate
Before any publication of the skill set, a local security gate SHALL pass, in this order: the audit-invariant test suite, then a local run of the same skill scanner that audits the published registry entries, executed against the repository's skills staged in isolation from the developer's real agent configuration. The scanner gate SHALL fail on any finding at or above the calibrated risk threshold and SHALL report every finding with its skill, category, and reason. Publication with a failing gate requires an explicit, recorded decision.

#### Scenario: Scanner finds a high-risk pattern
- **WHEN** the local scanner reports a finding at or above the threshold for any skill
- **THEN** the gate exits non-zero, names the skill and the finding, and publication does not proceed by default

#### Scenario: Gate isolation
- **WHEN** the local scanner runs
- **THEN** it scans only the repository's skills, not the developer's installed agent configurations or MCP servers

### Requirement: Post-publish verdict confirmation
After publication, the published audit verdicts for every skill SHALL be fetched from the registry's audit API and compared against a committed baseline. A deviation SHALL be reported as a non-zero result with a per-skill, per-provider diff. The baseline SHALL be updatable only by an explicit command, so silent verdict drift — including provider-side re-scans without a new publication — is always surfaced.

#### Scenario: Provider verdict drifts
- **WHEN** a provider's verdict for any skill differs from the committed baseline
- **THEN** the comparison exits non-zero and names the skill, provider, and both verdicts

#### Scenario: Verdicts match baseline
- **WHEN** all fetched verdicts equal the baseline
- **THEN** the comparison exits zero

### Requirement: Audit-pattern regressions caught by tests
The risk patterns remediated in past audits SHALL be enforced by automated tests over the shipped skill content: no dynamic module loading from input-derived names, no credential lookup outside the documented locations, no instructions to mutate file permissions, no embedded execution of another skill's scripts, and no instructions that pass a secret value through the agent. The tests SHALL run in the default offline test suite.

#### Scenario: Remediated pattern reintroduced
- **WHEN** a change reintroduces one of the remediated patterns into a skill's shipped content
- **THEN** the offline test suite fails naming the file and the pattern

### Requirement: Uniform skill opening structure

Every shipped `SKILL.md` body SHALL open with exactly three blocks, in this order, before its first section heading:

1. **Purpose** — one or two sentences in the vocabulary of a person who has never read the repository, stating what the skill produces and for whom. It SHALL NOT restate, soften, or paraphrase any rule stated below it, because the first statement of a rule fixes that rule's scope.
2. **Workflow line** — a single line naming every skill in the set and the order of the main chain, with the containing skill's own name marked. The line SHALL be identical across all skills except for which name is marked, and SHALL mark exactly one name, which SHALL be the name of the skill whose file it appears in.
3. **Mandate** — the skill's agent-facing opening paragraph. It SHALL remain immediately followed by the paragraph that already followed it, so that a paragraph which elaborates or enforces a mandate is never separated from it.

The workflow line is orientation, not a dependency declaration: a skill SHALL remain functional when the siblings it names are not installed.

#### Scenario: Visitor lands on a single skill page

- **WHEN** a person opens one skill's rendered page without knowing the package
- **THEN** the first two blocks tell them what that skill does for them, that the other skills exist, and where the chain starts

#### Scenario: Purpose block would restate a rule

- **WHEN** a purpose block is written so that it also states a constraint the mandate below it states
- **THEN** the purpose block is rewritten to state the deliverable instead, leaving the constraint stated once, by the mandate

#### Scenario: Mandate has an enforcing paragraph

- **WHEN** a skill's mandate is followed by a paragraph that elaborates or mechanically verifies it
- **THEN** no header block is inserted between the two

#### Scenario: Skill added to the set

- **WHEN** a new skill joins the package
- **THEN** it opens with the same three blocks, and every existing skill's workflow line is updated so the set named on each page stays complete

#### Scenario: Skill installed without its siblings

- **WHEN** a skill is installed alone in a workspace
- **THEN** it performs its purpose, treating the sibling names in its workflow line as orientation rather than as available tools

### Requirement: Opening structure and mandate wording enforced offline

The opening structure SHALL be enforced by the offline test suite rather than by convention. The suite SHALL fail when the workflow line differs between skills, when the marked name does not match the skill it appears in, when the block order or the bounded length of the purpose block is violated, when a mandate is separated from the paragraph beneath it, or when a mandate's wording differs from a committed pinned copy of that mandate.

Changing a mandate SHALL therefore require editing its pinned copy, so the reword appears as an explicit diff under review instead of passing silently.

#### Scenario: Workflow line drifts on one skill

- **WHEN** one skill's workflow line is reworded, reordered, or left stale after the set changes
- **THEN** the offline suite fails naming that skill

#### Scenario: Sibling's line copied without re-marking

- **WHEN** a skill's workflow line marks a name other than its own
- **THEN** the offline suite fails naming that skill

#### Scenario: Mandate silently reworded

- **WHEN** a change alters the wording of a skill's mandate without updating that mandate's pinned copy
- **THEN** the offline suite fails naming the skill and the mandate

#### Scenario: Mandate deliberately revised

- **WHEN** a mandate is intentionally rewritten and its pinned copy is updated in the same change
- **THEN** the offline suite passes and the reword is visible as a diff in review

#### Scenario: Purpose block grows into a marketing section

- **WHEN** the material before the workflow line exceeds a single paragraph
- **THEN** the offline suite fails

