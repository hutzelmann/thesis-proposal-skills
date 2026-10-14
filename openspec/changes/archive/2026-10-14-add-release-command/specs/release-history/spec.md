## ADDED Requirements

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
