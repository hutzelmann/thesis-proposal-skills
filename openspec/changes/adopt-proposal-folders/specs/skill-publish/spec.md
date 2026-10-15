# Spec Delta

## ADDED Requirements

### Requirement: Figures resolved against the proposal's folder
On every tier, the build SHALL resolve the figures the proposal links against the proposal's own folder, whatever the working directory it was started from, so every linked figure that exists is embedded in the document. On a build that succeeds, publish SHALL pass the converter's warnings through to its output rather than discard them, so a figure that cannot be found never disappears silently.

#### Scenario: Word document built from the workspace root
- **WHEN** a proposal linking two figures in its folder's `img/` is built on the word-processor tier with the workspace root as working directory
- **THEN** the document embeds both figures

#### Scenario: LaTeX PDF built from another directory
- **WHEN** the same proposal is built on the LaTeX tier from a working directory other than its folder
- **THEN** the PDF embeds both figures

#### Scenario: Linked figure missing
- **WHEN** the proposal links `img/overview.png`, no such file exists in its folder, and the build runs on the LaTeX or the word-processor tier and otherwise succeeds
- **THEN** publish reports success and relays the converter's warning naming the missing figure

#### Scenario: Linked figure missing on the typst tier
- **WHEN** the proposal links `img/overview.png`, no such file exists in its folder, and the build runs on the typst tier
- **THEN** the build fails, and publish's failure message names the missing file

#### Scenario: Folder path containing the path-list separator
- **WHEN** the proposal's folder lies under a directory whose name contains the platform's path-list separator, `:` on Linux and macOS or `;` on Windows
- **THEN** the LaTeX PDF and the Word document still embed every linked figure

## MODIFIED Requirements

### Requirement: Outputs and workspace hygiene
The PDF and intermediate build source SHALL be written next to the proposal, in its folder. Publish SHALL ensure ignore entries exist for all build artifacts, in the `.gitignore` in the proposal's folder (shared rule: whichever skill first creates an ignorable artifact ensures its ignore entry).

#### Scenario: First build in a workspace
- **WHEN** publish runs for the first time
- **THEN** build outputs appear in the proposal's folder and that folder's ignore file covers them
