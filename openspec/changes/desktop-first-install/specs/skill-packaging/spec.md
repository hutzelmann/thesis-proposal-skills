# Spec Delta

## MODIFIED Requirements

### Requirement: Registry installation from the repository
The skill set SHALL be installable from the public repository through three routes, each delivering what is committed on the default branch: the install prompt carried out with the repository's installer, the plugin definition, and the skills.sh CLI. The installer and the plugin definition install the whole set; the CLI SHALL additionally support installing a single skill. What is committed on the default branch is what users receive on every route.

#### Scenario: Selective install
- **WHEN** a user installs only the write skill
- **THEN** that skill arrives functional without requiring any sibling skill

#### Scenario: Routes deliver the same skills
- **WHEN** the same revision is installed once through the installer, once through the plugin definition, and once through the CLI
- **THEN** each route delivers the same shipped skills with the same file contents

### Requirement: Installation verified against the tracked tree
An on-demand check SHALL install the repository's tracked tree — exported as the registry and the default-branch archive would serve it, never the working directory — into an isolated environment that cannot touch the operator's own agent configuration, once through the installation command documented in the README and once through the repository's installer given the exported archive. For each route it SHALL assert that exactly the shipped skills install, that installed skill files are byte-identical to the repository's, and that an installed skill's script runs correctly from its installed location; for the installer it SHALL also assert the install record names the exported revision. The check SHALL run in CI on the default branch and on a schedule, with the CLI installer deliberately unpinned so a CLI-side regression that would break user installs surfaces here first. It SHALL NOT join the offline test gate.

#### Scenario: Untracked skill-shaped directory in a checkout
- **WHEN** a local checkout carries untracked skill directories (agent integration helpers)
- **THEN** the check, operating on the tracked tree, still counts exactly the shipped skills — and an accidentally committed extra skill directory fails the count

#### Scenario: README command drifts
- **WHEN** the README's documented install command is removed or reworded beyond recognition
- **THEN** the check fails at command extraction rather than silently testing a command nobody documents

#### Scenario: Installed script smoke
- **WHEN** the check runs the installed check script against a known-broken fixture
- **THEN** the script exits with findings, proving scripts and references travel and resolve from the installed location

#### Scenario: Installer regression upstream
- **WHEN** a new skills-CLI release breaks installation of this repository
- **THEN** the scheduled run fails without any commit here, naming the installer as the moving part

#### Scenario: Repository installer from the exported archive
- **WHEN** the check runs the repository's installer against the exported archive in an isolated home
- **THEN** exactly the shipped skills land byte-identical in every user-level target directory, and the install record names the exported revision
