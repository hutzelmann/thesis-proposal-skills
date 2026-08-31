## ADDED Requirements

### Requirement: Output lands in the workspace

The imported proposal `<slug>.md` and its companion `<slug>.notes.md` SHALL be written into the workspace the run is working in — the working directory — beside any proposals already there. The skill's install directory is read-only territory: the skill SHALL NOT write any artifact there, and SHALL NOT change the working directory to the install directory to run its shipped scripts — scripts are invoked from the workspace via their path. When the source document lives outside the workspace, the imported result SHALL still be written into the workspace, not beside the source.

#### Scenario: Ordinary import

- **WHEN** an import run converts a source document while working in the user's workspace
- **THEN** `<slug>.md` and `<slug>.notes.md` exist in that workspace when the run reports completion, and no file has been written into the skill's install directory

#### Scenario: Host leaves the skill-directory variable unexpanded

- **WHEN** the host does not substitute `${CLAUDE_SKILL_DIR}` and the agent falls back to the scripts' real location next to SKILL.md
- **THEN** the agent runs the scripts from the workspace by their full path, and the imported file is created and checked in the workspace, not in the skill directory

#### Scenario: Source document outside the workspace

- **WHEN** the source document is provided by a path outside the workspace (for example a downloads folder)
- **THEN** the imported `<slug>.md` is written into the workspace, and nothing is written beside the source document
