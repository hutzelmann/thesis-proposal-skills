## ADDED Requirements

### Requirement: The methodology set is closed per workspace
The methodology set SHALL remain closed — a proposal declares exactly one methodology from a fixed set, and that constraint is what forces a decision about the kind of evidence the thesis produces. The *contents* of that set SHALL be workspace-configurable, because which methodologies are acceptable is a property of a supervisor's field rather than of thesis writing.

A workspace declaration SHALL be able to add a branch, replace a shipped branch of the same identity, and disable a shipped branch. A workspace that declares no methodologies SHALL get the shipped defaults unchanged.

The guidance SHALL state that the shipped set is a default rather than a claim about which methodologies exist.

#### Scenario: Workspace adds a branch
- **WHEN** a workspace declares a methodology branch the shipped set does not contain
- **THEN** a proposal declaring that methodology is accepted, and its declared subsections are the ones required

#### Scenario: Workspace disables a shipped branch
- **WHEN** a workspace disables one of the shipped branches
- **THEN** a proposal declaring it is reported as an unknown methodology, and the branch is absent from the list of accepted ones

#### Scenario: Workspace declares nothing
- **WHEN** a workspace `guidelines.md` carries no methodology declaration
- **THEN** the shipped set applies unchanged

#### Scenario: Single-methodology rule is unaffected
- **WHEN** a proposal declares two methodology sections in a workspace with a widened set
- **THEN** the single-methodology rule still reports a violation

### Requirement: A workspace methodology branch declares its own content contract
A workspace-declared methodology branch SHALL supply, for every subsection, guidance describing what belongs in it. A branch declaring headings without that guidance SHALL be rejected as a configuration error rather than accepted with empty contracts.

The shipped branches carry their content contract as prose in the guidance document; a workspace branch has no such document, so the declaration is where that contract lives. This SHALL NOT be read as formalizing the shipped guidance: the requirement exists because a workspace cannot ship prose, not because content contracts belong in structured data.

#### Scenario: Branch without guidance
- **WHEN** a workspace declares a branch whose subsections carry no guidance
- **THEN** the declaration is reported as a configuration error naming the branch, and the branch is not applied

#### Scenario: Branch with guidance
- **WHEN** a workspace declares a branch with guidance for each subsection
- **THEN** the branch is applied, and writing tooling has a content contract for every heading it must fill
