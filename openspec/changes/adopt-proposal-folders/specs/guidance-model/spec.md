# Spec Delta

## MODIFIED Requirements

### Requirement: Workspace layout and the proposal location
The workspace root SHALL be the working directory the skills and their scripts operate from, which holds the workspace `guidelines.md`. The proposal-location path SHALL be resolved relative to that root and SHALL default to the root itself. Every proposal SHALL live in a folder of its own directly in that location (proposal-file-format: One folder per proposal); no other layout exists.

A configured proposal-location value SHALL be a relative directory inside the workspace: not absolute, not home-anchored, and not escaping the root through parent references.

The proposal's whole family SHALL sit in its folder (proposal-file-format: Proposal family under one handle). Workspace-level files SHALL stay at the root regardless of the configured proposal location: the `guidelines.md` itself, the workspace key file, and the bug-report bundle.

Skills that create or locate proposals SHALL honor only proposal folders in the configured location: a skill SHALL NOT fall back to the workspace root when the configured directory is empty, SHALL NOT treat a file outside a proposal folder as a proposal or a family member, and SHALL NOT write one outside it. A proposal outside its folder is a reportable condition, never a silently accepted alternative.

#### Scenario: Proposals collected in a subdirectory
- **WHEN** the workspace `guidelines.md` sets the proposal-location path to a subdirectory and a skill creates a proposal
- **THEN** the proposal's folder is created in that subdirectory, and `guidelines.md` stays at the workspace root

#### Scenario: Unset key preserves the flat layout
- **WHEN** the workspace sets no proposal-location path
- **THEN** the proposal location stays the workspace root, as before the key existed, and each proposal's folder sits directly in it

#### Scenario: Family follows the proposal
- **WHEN** a skill writes a proposal's review, feedback, notes, harvest record, or built output
- **THEN** the file lands in that proposal's folder, not in the location's root or the workspace root

#### Scenario: No fallback search
- **WHEN** the configured proposal directory holds no proposal folder but the workspace root does
- **THEN** a skill locating a proposal does not silently adopt the root copy; the mismatch surfaces as a reported condition

#### Scenario: Flat proposal not read
- **WHEN** a proposal file and its notes file sit directly in the proposal location, outside any folder
- **THEN** no skill offers the file as a candidate or reads the notes file, and the check reports the proposal as misplaced when it is named explicitly

#### Scenario: Submission handed over as a source
- **WHEN** a professor names a standard-format proposal file saved at the workspace root as the student's submission
- **THEN** the supervising skill reads it as a source document, writes the normalized copy into a new proposal folder, and leaves the original unchanged
