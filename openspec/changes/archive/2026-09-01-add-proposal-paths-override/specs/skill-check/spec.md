## ADDED Requirements

### Requirement: Override file resolution chain
The check SHALL resolve the workspace override file through a fixed chain: an explicitly passed path wins; otherwise a `guidelines.md` beside the proposal; otherwise a `guidelines.md` in the working directory. The first file found governs the whole run — later chain positions are never consulted to fill in keys the found file lacks. The chain SHALL NOT search ancestor directories or any other location, and a workspace with the proposal beside its `guidelines.md` SHALL behave exactly as it did before the chain existed.

#### Scenario: Proposal in a configured subdirectory
- **WHEN** the workspace root holds `guidelines.md`, the proposal lives in the configured proposal subdirectory, and the check runs from the root without an explicit override path
- **THEN** the root `guidelines.md` governs the run and its overrides are honored

#### Scenario: Flat workspace unchanged
- **WHEN** `guidelines.md` sits beside the proposal in the working directory
- **THEN** resolution and results are identical to the behavior before the chain existed

#### Scenario: Both chain positions occupied
- **WHEN** a `guidelines.md` exists beside the proposal and a different one exists in the working directory
- **THEN** the one beside the proposal governs the whole run and the working-directory file is not consulted

#### Scenario: No override file anywhere
- **WHEN** neither position holds a `guidelines.md` and no explicit path is passed
- **THEN** pure defaults apply, silently, as today

### Requirement: Proposal-location value validated, misplacement reported
The check SHALL validate a configured proposal-location value: it must be a string naming a relative directory inside the workspace — not absolute, not home-anchored, not escaping the root through parent references. An invalid value SHALL be reported as an error finding and the default SHALL apply for the rest of the run. An unknown key under the paths table SHALL be reported through the existing unknown-override-key error, never ignored.

When the governing `guidelines.md` configures a proposal location and the checked proposal does not live in that directory relative to the governing file's own directory, the check SHALL report an error naming the expected directory, so a half-migrated workspace fails loudly instead of skills silently disagreeing about where files live.

#### Scenario: Invalid proposal-location value
- **WHEN** the workspace sets the proposal-location path to an absolute path, a parent-escaping path, or a non-string
- **THEN** the check reports an error finding naming the constraint, and the default location applies for the rest of the run

#### Scenario: Unknown paths key
- **WHEN** the workspace sets a key under the paths table that does not resolve to an overridable leaf
- **THEN** the check reports it through the unknown-override-key error, and it is not applied

#### Scenario: Misplaced proposal
- **WHEN** the governing `guidelines.md` sets the proposal-location path to a subdirectory and the checked proposal lives outside that directory
- **THEN** the check reports an error naming the configured directory the proposal is expected in

#### Scenario: Unset key raises no location finding
- **WHEN** the workspace sets no proposal-location path
- **THEN** no misplacement finding is possible, wherever the proposal lives
