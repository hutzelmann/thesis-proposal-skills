## MODIFIED Requirements

### Requirement: Dialog-driven override management
The skill SHALL create or edit `guidelines.md` from a conversation about the user's or supervisor's requirements, writing the machine-readable TOML block and prose sections per the guidance model.

The skill SHALL write override keys at the key path the value occupies in the structured guidance data, and SHALL NOT invent shorter or flatter spellings. When it encounters an existing workspace file using a retired key, it SHALL migrate that key rather than leaving it in place, and SHALL say which keys it moved.

#### Scenario: Page limit request
- **WHEN** the user says the supervisor wants at most 3 pages
- **THEN** the skill writes the page limit at its structure key path inside the TOML block

#### Scenario: Existing file uses retired keys
- **WHEN** the workspace `guidelines.md` predates the key migration
- **THEN** the skill rewrites those keys at their current paths and reports what it moved
