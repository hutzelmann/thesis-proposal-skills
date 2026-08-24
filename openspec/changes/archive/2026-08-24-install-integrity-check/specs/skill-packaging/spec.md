## ADDED Requirements

### Requirement: Installation verified against the tracked tree
An on-demand check SHALL install the repository's tracked tree — exported as the registry would serve it, never the working directory — using the installation command documented in the README, into an isolated environment that cannot touch the operator's own agent configuration. It SHALL assert that exactly the shipped skills install, that installed skill files are byte-identical to the repository's, and that an installed skill's script runs correctly from its installed location. The check SHALL run in CI on the default branch and on a schedule, with the installer deliberately unpinned so a CLI-side regression that would break user installs surfaces here first. It SHALL NOT join the offline test gate.

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
