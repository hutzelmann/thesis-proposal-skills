## ADDED Requirements

### Requirement: Workspace methodology declarations are validated and merged
The check SHALL merge a workspace methodology declaration over the shipped set before applying any methodology rule, so the accepted set, the required subsections, and the message listing acceptable methodologies all reflect the workspace.

The check SHALL report as a configuration error a declared branch that is missing a title in either language, that declares no subsections, that declares a subsection missing a title in either language, that declares a subsection without guidance, or that carries a key the declaration format does not define. An invalid branch SHALL NOT be applied, and the rest of the file SHALL still be checked — one malformed branch does not invalidate a workspace.

#### Scenario: Proposal uses a workspace branch
- **WHEN** a proposal declares a methodology the workspace added, with that branch's subsections present
- **THEN** the check reports no methodology finding

#### Scenario: Proposal misses a workspace branch's subsection
- **WHEN** a proposal declares a workspace branch and omits one of its declared subsections
- **THEN** the check reports the missing subsection by its declared title

#### Scenario: Unknown methodology lists the workspace set
- **WHEN** a proposal declares a methodology no branch matches
- **THEN** the error lists the accepted methodologies including workspace-declared ones and excluding disabled ones

#### Scenario: Malformed branch declaration
- **WHEN** a workspace declares a branch without per-subsection guidance
- **THEN** the check reports a configuration error naming that branch, and every other rule still runs
