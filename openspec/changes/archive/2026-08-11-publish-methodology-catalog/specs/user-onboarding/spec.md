## ADDED Requirements

### Requirement: Supervisors can discover methodology configurability
The supervisor-facing documentation SHALL state that the methodology set is configurable per workspace — a branch can be added, a shipped branch replaced, and a shipped branch disabled — and SHALL point at the skill that produces the workspace file, at a working example of a branch declaration, and at a catalog of ready-to-paste declarations for common non-default methodologies. The catalog SHALL provide, per entry, the declaration in the exact format the workspace file accepts, a statement of when the methodology fits, and the primary source it derives from. The Mixed Methods entry SHALL carry an explicit scope warning and a subsection that forces the integration point to be named at proposal time.

#### Scenario: Supervisor with a missing method
- **WHEN** a supervisor's accepted methodology is not in the shipped defaults
- **THEN** the README tells them the set is a workspace config rather than a fork, and the catalog gives them a declaration to paste and adapt

#### Scenario: Mixed methods requested
- **WHEN** a workspace enables the catalog's Mixed Methods branch
- **THEN** the pasted declaration itself carries the scope warning and an integration-plan subsection, so a proposal that cannot name its point of interface fails the branch's own contract

#### Scenario: Design science requested
- **WHEN** a supervisor looks for Design Science Research in the catalog
- **THEN** the catalog explains it as a rename of the shipped Prototype Implementation branch rather than providing a duplicate declaration
