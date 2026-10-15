# Spec Delta

## MODIFIED Requirements

### Requirement: Figures marked, not embedded
The skill SHALL NOT silently drop figures: each figure in the source produces a `[TODO: re-add figure from page N as img/<name>.png]` marker; when a local image-extraction tool is available it MAY be used to populate the `img/` folder in the proposal's folder directly, linked from the proposal as `img/<name>.<ext>`.

#### Scenario: Source with two figures, no extraction tool
- **WHEN** a two-figure PDF is imported and no extraction tool exists
- **THEN** the output contains two page-referenced figure TODO markers

#### Scenario: Source with two figures, extraction tool present
- **WHEN** a two-figure PDF is imported and a local extraction tool is available
- **THEN** both figures land in the proposal's `img/` folder, and the proposal links each as `img/<name>.<ext>` without a slug prefix

### Requirement: Notes file seeded at import
The import skill SHALL create `notes.md` in the imported proposal's folder and seed it with the knowledge the import produced but the proposal cannot carry: source content that did not map into the canonical sections (for example dropped work-plan phase detail beyond the kept boundary months), the gap list summarizing what the source did not supply, and an initial Next Focus naming the most important gaps to close first. Submission-blocking gaps continue to appear as `[TODO: …]` markers in the proposal; the notes file summarizes and prioritizes them, it does not replace them. Content copied into the notes file follows the same personal-data stripping rules as the proposal itself.

#### Scenario: Dropped work-plan detail preserved
- **WHEN** the source contains a phase-by-phase work plan whose boundary months go into the Timeline section
- **THEN** the dropped phase detail lands in the notes file instead of being reported only in chat

#### Scenario: Gap list becomes the initial focus
- **WHEN** the import leaves several TODO markers in the proposal
- **THEN** the notes Next Focus section names the gaps to close first, and the markers themselves remain in the proposal

### Requirement: Output lands in the workspace

The imported proposal and its notes file SHALL be written as `<slug>/<slug>.md` and `<slug>/notes.md`, a new proposal folder in the workspace's configured proposal location — by default the working directory, or the subdirectory the workspace `guidelines.md` configures as the proposal-location path — beside any proposal folders already there. The skill's install directory is read-only territory: the skill SHALL NOT write any artifact there, and SHALL NOT change the working directory to the install directory to run its shipped scripts — scripts are invoked from the workspace via their path. When the source document lives outside the workspace, the imported result SHALL still be written there, not beside the source.

#### Scenario: Ordinary import

- **WHEN** an import run converts a source document while working in the user's workspace
- **THEN** `<slug>/<slug>.md` and `<slug>/notes.md` exist in that workspace's configured proposal location when the run reports completion, and no file has been written into the skill's install directory

#### Scenario: Workspace configures a proposal subdirectory

- **WHEN** the workspace `guidelines.md` sets the proposal-location path to a subdirectory
- **THEN** the imported proposal's folder is created in that subdirectory, not in the workspace root

#### Scenario: Host leaves the skill-directory variable unexpanded

- **WHEN** the host does not substitute `${CLAUDE_SKILL_DIR}` and the agent falls back to the scripts' real location next to SKILL.md
- **THEN** the agent runs the scripts from the workspace by their full path, and the imported file is created and checked in the workspace, not in the skill directory

#### Scenario: Source document outside the workspace

- **WHEN** the source document is provided by a path outside the workspace (for example a downloads folder)
- **THEN** the imported proposal's folder is written into the workspace's configured proposal location, and nothing is written beside the source document
