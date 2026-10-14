## ADDED Requirements

### Requirement: OpenSpec version kept current
The spec gate SHALL validate with one OpenSpec version, pinned in one place, and SHALL fail on every error or warning that version reports, except an overlong requirement that a length baseline records and that has not grown. CI SHALL NOT rewrite the baseline. A currency check SHALL compare the pin with the newest published version, and a weekly workflow SHALL propose a newer version as a pull request that changes only the pin and that it never merges.

#### Scenario: New overlong requirement
- **WHEN** a spec, or an ADDED or MODIFIED requirement in an open change, holds requirement text over OpenSpec's length limit and the baseline lists no entry for it
- **THEN** the gate fails and names the capability and the requirement

#### Scenario: Baselined requirement grew
- **WHEN** a baselined requirement's text is longer than its recorded length
- **THEN** the gate fails, names the requirement with its recorded and its measured length, and says how to shorten it or deliberately accept it

#### Scenario: Modified requirement judged while its change is open
- **WHEN** an open change's MODIFIED requirement is over the limit and the baseline lists no entry for it under that change
- **THEN** the gate judges its text against the entry of the spec requirement it replaces, and fails when that entry is shorter or missing

#### Scenario: Open change does not loosen the spec it modifies
- **WHEN** a spec requirement grows while an open change's baselined MODIFIED requirement of the same name is longer still
- **THEN** the gate judges the spec requirement against its own entry and fails

#### Scenario: Baselined requirement got shorter or went away
- **WHEN** a baselined requirement is shorter than its recorded length, is no longer over the limit, or no longer exists
- **THEN** the gate passes and reports the stale entry, and the update mode records the shorter length or drops the entry

#### Scenario: Update mode only tightens
- **WHEN** the update mode runs while a requirement is new or has grown
- **THEN** the baseline gains no entry for it, no recorded length grows, and the gate still fails

#### Scenario: Archived requirement keeps its entry
- **WHEN** an archive moves a baselined ADDED or MODIFIED requirement, unchanged, from a change into the specs
- **THEN** the gate passes, matching the requirement to its change's entry by capability and requirement name even where the specs recorded a shorter text under that name, and reports the entry as moved

#### Scenario: Length counted as OpenSpec counts it
- **WHEN** a requirement's text holds a character outside the Basic Multilingual Plane
- **THEN** its measured length counts that character as two, as OpenSpec's own count does, and the length comes from the text the pinned version parsed

#### Scenario: Any other finding fails
- **WHEN** the pinned version reports an issue at any level but the informational one, other than the requirement-length warning, or marks an item invalid without naming an error or warning
- **THEN** the gate fails, whatever the baseline holds

#### Scenario: Length warning that cannot be matched
- **WHEN** a length warning names no requirement the pinned version can show, or the shown text is not over the limit
- **THEN** the gate fails and names the warning instead of passing it

#### Scenario: Report that covers less than the tree
- **WHEN** the pinned version's report validates no item, omits a spec or an open change the tree holds, names one the tree does not hold, or carries an exit status its items contradict
- **THEN** the gate stops with its "could not run" status, and the update mode writes nothing

#### Scenario: Show refused
- **WHEN** the pinned version refuses to show a spec or a change the gate measures
- **THEN** the gate stops with its "could not run" status and passes on the pinned version's message, adding for a change that showing it needs a proposal with its Why and What Changes sections

#### Scenario: Pin behind the published version
- **WHEN** the package registry's latest version is newer than the pin
- **THEN** the currency check exits with its "behind" status, and its write mode changes the pin and no other line

#### Scenario: Registry unreachable
- **WHEN** the registry request fails or its answer carries no usable version
- **THEN** the currency check exits with a distinct "unknown" status and writes nothing

#### Scenario: Local tooling differs from the pin
- **WHEN** the local OpenSpec CLI or the stamp in the generated agent skills differs from the pin
- **THEN** the check prints a warning naming the action that brings each in line, and its exit status depends on the pin alone

#### Scenario: Local tooling absent
- **WHEN** no local OpenSpec CLI is installed and no generated agent skills exist, as on a CI runner
- **THEN** the check notes both as absent and warns about neither

#### Scenario: Weekly bump proposed
- **WHEN** the weekly run finds the pin behind
- **THEN** one pull request from a fixed branch carries the pin change and nothing else, and the regular CI workflow runs on that branch

#### Scenario: Maintainer has pushed to the bump branch
- **WHEN** the bump branch carries a commit not made by the workflow
- **THEN** the workflow leaves the branch untouched and comments on the pull request

#### Scenario: Pin already current
- **WHEN** the weekly run finds the pin current
- **THEN** no pull request is opened, and an open one that main has made obsolete is closed

#### Scenario: Workflow bounds
- **WHEN** the weekly workflow runs
- **THEN** it uses the repository's built-in token with write access to contents, pull requests and actions only, reads no other secret, and merges nothing
