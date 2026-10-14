# release-history Specification

## Purpose
How the suite tells its users what changed: one changelog at the repository root, organised as versioned releases, that covers the suite's history from its first publication and stays current through the change loop.

## Requirements

### Requirement: User-facing changelog
The repository SHALL keep one changelog, `CHANGELOG.md` at its root, that is written for students, supervisors and workspace maintainers. Releases SHALL be listed newest first. Each release SHALL group its entries under the Keep a Changelog categories, with entries that break the declared public API marked `**Breaking:**` and listed first in their group. Changes that only affect contributors SHALL be kept to one closing group per release.

#### Scenario: Reader checks what changed for them
- **WHEN** a supervisor opens the changelog after updating
- **THEN** each release opens with a short lead, breaking entries come first in their group, and harness or CI changes appear only in that release's contributor group

#### Scenario: Entry traced to its record
- **WHEN** an entry describes a change that has an archived OpenSpec record
- **THEN** the entry links that record's archive folder, and the link resolves in the repository

### Requirement: Declared public API and version meaning
The changelog's header SHALL state which surfaces the suite version protects and what each version part means. A major increase SHALL mark a change after which something a user already has stops working or is read differently. A minor increase SHALL mark new skills, settings or stricter judgement. A patch increase SHALL mark fixes and wording. While the version is below 1.0.0, a breaking change SHALL increase the minor part.

#### Scenario: Stricter check introduced
- **WHEN** a release adds a check error that can flag drafts which passed before
- **THEN** the release is at least a minor increase, and its entry says that earlier drafts may now be flagged

#### Scenario: Harness-only change
- **WHEN** a release contains only harness, CI or other contributor changes
- **THEN** the suite version does not change on their account

### Requirement: Retroactive history
History before the first stamped release SHALL appear as retroactive releases. Each retroactive release SHALL name the commit it describes, say that it is retroactive, and say when its state reached users. Its version SHALL never be stamped into the skills. Annotated tags for retroactive releases SHALL point at the commits their sections name.

#### Scenario: Tag disagrees with its section
- **WHEN** a local tag for a listed release points at a different commit than its section names
- **THEN** the offline checks fail

#### Scenario: Retroactive state never published on its own
- **WHEN** a retroactive release names a commit that was never the head of the published branch
- **THEN** its section says with which later published state it reached users

### Requirement: Unreleased work lives on the development branch
Work that has landed on the development branch but is not yet in a release SHALL be listed in one section at the top of the changelog, which says that it is not yet released. When a release is cut, those entries SHALL move under the new version, so the default branch, which only ever receives release commits, carries that section empty.

#### Scenario: Change archived between releases
- **WHEN** a change is archived on the development branch after the newest release
- **THEN** its entry appears in the top section there until the next release is cut

#### Scenario: Default branch after a release
- **WHEN** the default branch is fast-forwarded to a release
- **THEN** its changelog's top section lists no entries

### Requirement: Every archived change accounted for
Every change archived on or after the changelog's introduction SHALL be accounted for: the changelog either links its archive folder, or the change's proposal declares that it has no user-facing entry. The offline checks SHALL fail on a change that does neither.

#### Scenario: Change archived without an entry
- **WHEN** a change is archived after the introduction, the changelog does not link it, and its proposal declares no internal status
- **THEN** the offline checks fail and name the change

#### Scenario: Internal change
- **WHEN** a proposal ends with `Changelog: internal`
- **THEN** the change needs no changelog entry

### Requirement: Changelog stays consistent under parallel work
The offline checks SHALL fail when the changelog's release headings are malformed, out of order or duplicated, when an entry repeats within a release, or when the newest stamped release disagrees with the version stamped into the skills.

#### Scenario: Merge duplicates a line
- **WHEN** merging two branches duplicates an entry within a release
- **THEN** the offline checks fail and name the repeated entry

#### Scenario: Stamp and changelog disagree
- **WHEN** the skills carry a stamped version that is not the newest stamped release in the changelog
- **THEN** the offline checks fail

### Requirement: One command cuts a release
Cutting a release SHALL be one local command, run on the development branch, that moves the unreleased entries under the new version, sets the suite's version source, stamps every skill, commits exactly the files it changed, tags the commit and fast-forwards the default branch to it. It SHALL never push or publish, and SHALL refuse a version below what the entries require, an empty or lead-less unreleased section, and a default branch that cannot fast-forward.

#### Scenario: Wrong branch
- **WHEN** the command runs on a branch other than the development branch
- **THEN** it refuses before writing anything

#### Scenario: Breaking entry before 1.0.0
- **WHEN** the unreleased section holds a breaking entry and the current version is below 1.0.0
- **THEN** the command requires at least a minor increase and refuses a patch release

#### Scenario: Release cut
- **WHEN** the maintainer runs the command on a clean tree with unreleased entries and a lead
- **THEN** one commit carries the new changelog section, the version source and every skill's stamp, an annotated tag of that version points at it, and the command prints the push and release-publishing commands without running them

#### Scenario: Dry run
- **WHEN** the command runs as a dry run
- **THEN** it shows the version it would cut, why, and the new section, and changes nothing

### Requirement: 1.0.0 waits for verified installs and a measured model roster
The release command SHALL refuse any version of 1.0.0 or higher while the desktop-install change is still open, or while any model in the README's model-support summary is reported as untested.

#### Scenario: Roster not yet measured
- **WHEN** the next version would be 1.0.0 and one summary row reads untested
- **THEN** the command refuses and names that row

### Requirement: Model-support changes summarized at release
When the enabled model roster or a summary verdict differs from the previous release, the release SHALL carry one changelog entry that names the models added, retired or re-judged, in prose names rather than model identifiers.

#### Scenario: Roster bumped between releases
- **WHEN** the weekly currency update replaced a model since the previous release
- **THEN** the new release's entries say which model joined and which left the roster
