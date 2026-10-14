## MODIFIED Requirements

### Requirement: Rolling release policy
The default branch `main` SHALL stay the release channel and SHALL hold released versions only: installers receive what it holds, and it moves only by fast-forward to a release commit. Completed work SHALL integrate on the development branch `develop`, where releases are cut at maintainer-chosen milestones as a stamped version, an annotated tag and a dated changelog section. Pushing branches and tags and publishing releases SHALL remain the maintainer's own actions.

#### Scenario: Pre-adoption phase
- **WHEN** changes were pushed to the default branch before the first stamped release
- **THEN** they were live for installers without further release steps, and the changelog records that period as retroactive releases

#### Scenario: Change completed between releases
- **WHEN** a change is completed after the newest release
- **THEN** it lands on the development branch, is listed in the changelog's unreleased section there, and reaches installers only with the next release

#### Scenario: Release cut
- **WHEN** the maintainer cuts a release
- **THEN** the stamp commit on the development branch carries the new version in every skill and a dated changelog section, an annotated tag of that version points at it, and the default branch is fast-forwarded to it
