## MODIFIED Requirements

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block plus freeform prose. Absent file means pure defaults.

Every override key SHALL be the same key path the value occupies in the structured guidance data. There SHALL be exactly one naming rule: no hand-named aliases, and no flat spelling accepted alongside a nested one. The overridable set SHALL cover the reference minimum, the reference-density constant, the required-section list, the forbidden-heading list, the timeline detail mode, the page limit, the research-question count bounds, and the proposal-location path.

Merge semantics: a user key wins over the default per key; list values replace defaults entirely; a default-forbidden section may be allowed again by omitting it from the replacement list.

The timeline detail mode SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets the timeline detail mode to `detailed`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` raises the reference minimum to 8
- **THEN** a proposal with 5 references fails the reference-count check

#### Scenario: Reference density adjusted
- **WHEN** `guidelines.md` sets the reference-density constant to a different value
- **THEN** the density advisory judges the proposal against the workspace value instead of the default

#### Scenario: Research-question bounds overridden
- **WHEN** `guidelines.md` sets the research-question upper bound to 3
- **THEN** a proposal declaring four research questions fails the count check

#### Scenario: Override key mirrors the structure path
- **WHEN** a value is nested in the structured guidance data
- **THEN** the override key for it is nested identically, and no alternative spelling is honoured

#### Scenario: Proposal location overridden at its structure path
- **WHEN** `guidelines.md` sets the proposal-location path at the key path it occupies in the structured guidance data
- **THEN** the workspace's proposal directory is the configured one, and no alternative spelling of the key is honoured

## ADDED Requirements

### Requirement: Workspace layout and the proposal location
The workspace root SHALL be the directory containing the governing `guidelines.md` — the working directory the skills already operate from. The proposal-location path SHALL be resolved relative to that root and SHALL default to the root itself, so an unset key reproduces the flat layout exactly.

A configured proposal-location value SHALL be a relative directory inside the workspace: not absolute, not home-anchored, and not escaping the root through parent references.

The proposal's family SHALL travel with it into the configured directory: the proposal file, its companion notes file, its harvest record, its figure directory, its review and feedback files, and its built outputs all sit beside the proposal wherever it lives. Workspace-level files SHALL stay at the root regardless of the configured proposal location: the `guidelines.md` itself, the workspace key file, and the bug-report bundle.

Skills that create or locate proposals SHALL honor only the configured location: a skill SHALL NOT fall back to searching the default location when the configured directory is empty, and SHALL NOT write a proposal or a family member outside the configured directory. A proposal sitting outside the configured location is a reportable condition, never a silently accepted alternative.

#### Scenario: Proposals collected in a subdirectory
- **WHEN** the workspace `guidelines.md` sets the proposal-location path to a subdirectory and a skill creates a proposal
- **THEN** the proposal and its companion files are created in that subdirectory, and `guidelines.md` stays at the workspace root

#### Scenario: Unset key preserves the flat layout
- **WHEN** the workspace sets no proposal-location path
- **THEN** proposals and their families live directly in the workspace root, byte-identical to the behavior before the key existed

#### Scenario: Family follows the proposal
- **WHEN** the proposal lives in the configured subdirectory and a skill writes its review, feedback, notes, harvest record, or built output
- **THEN** the file lands beside the proposal in that subdirectory, not in the workspace root

#### Scenario: No fallback search
- **WHEN** the configured proposal directory holds no proposals but the workspace root does
- **THEN** a skill locating a proposal does not silently adopt the root copy; the mismatch surfaces as a reported condition
