## ADDED Requirements

### Requirement: Proposal-location customization
The skill SHALL treat a request to keep proposals in a subdirectory as a workspace customization, writing the proposal-location path at its structure key path in the TOML block. Before writing, it SHALL validate the value against the layout constraints — a relative directory inside the workspace, never absolute, home-anchored, or parent-escaping — and SHALL refuse an invalid value with the constraint named rather than writing something the check will reject.

When setting the key in a workspace that already holds proposals at the old location, the skill SHALL say that existing proposals and their companion files must move to the configured directory and that checks will report them as misplaced until they do. It SHALL also say what stays at the root: the `guidelines.md` itself, the workspace key file, and the bug-report bundle.

#### Scenario: Proposals subfolder requested
- **WHEN** the user asks for proposals to live in a subfolder
- **THEN** the skill writes the proposal-location path at its structure key path, and explains that existing proposals must move there and that `guidelines.md` stays at the root

#### Scenario: Invalid location refused
- **WHEN** the user asks for an absolute path or a directory outside the workspace
- **THEN** the skill refuses, names the constraint, and writes nothing
