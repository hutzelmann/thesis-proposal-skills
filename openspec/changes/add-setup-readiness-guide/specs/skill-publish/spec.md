# Spec Delta

## MODIFIED Requirements

### Requirement: Engine resolution order
Publish SHALL resolve the best available pipeline in this order: typst engine, then LaTeX engine, then word-processor format output — and SHALL tell the user what to install for a better tier when only a lower one is available.

The install guidance SHALL give, per platform, package-manager commands that the package manager accepts as written and that each install what they name; where a package manager's form selects one package per command, the guidance SHALL give one command per package. For a machine where no package manager works, the guidance SHALL link the install guide's PDF-export section by its published address. Neither the skill's instructions nor the script's messages SHALL carry download, digest or extraction steps, and neither SHALL tell the user or the agent to repair or reset a package manager.

#### Scenario: Only LaTeX available
- **WHEN** typst is absent but a LaTeX engine exists
- **THEN** the PDF is built via the LaTeX pipeline and the typst option is mentioned

#### Scenario: Windows without pandoc
- **WHEN** pandoc is missing and the user is on Windows
- **THEN** the guidance gives one winget command per tool, each selecting a single package by its exact identifier, so that running each as written installs that tool

#### Scenario: No working package manager
- **WHEN** the user reports that they have no package manager or that it fails with an error about its sources
- **THEN** the skill points them to the install guide's PDF-export section, gives no download steps itself, and does not offer to repair the package manager

#### Scenario: Guide link resolves
- **WHEN** the offline suite reads the link carried by the skill's instructions and by the script's install hint
- **THEN** it names a section the install guide has
