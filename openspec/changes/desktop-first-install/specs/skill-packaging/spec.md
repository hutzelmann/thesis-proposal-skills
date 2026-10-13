# Spec Delta

## MODIFIED Requirements

### Requirement: User-side script constraints

Scripts shipped inside skills SHALL run on stock Python ≥ 3.11 standard library only (no package installs), work on Windows/macOS/Linux, never general-parse YAML (narrow documented extraction only), detect missing interpreters/tools with install guidance, and document an agent-side fallback when script networking is denied.

A skill's instructions SHALL address its own scripts through the host's skill-directory substitution variable, so the documented command resolves regardless of the agent's working directory and of where the skill is installed. The instruction SHALL also name the skill-relative location in prose, so a host that does not substitute the variable still leads the agent to the script. That prose fallback resolves a script path and nothing else: it SHALL NOT direct the agent to work from, or write into, the skill's install directory — the documented command still runs from the agent's working directory, where the user's material lives. A skill whose script reads from or writes to a working-directory-dependent location SHALL name that stake beside the fallback. A script that another skill owns SHALL ship as a synchronized copy inside the skill that runs it, and SHALL be addressed through the skill-directory variable like the skill's own scripts — never by an install path, which breaks under user-level and plugin installs, and never relative to the skill's own directory, because `../<sibling>/scripts/` is the cross-skill execution shape the audit remediation forbids.

A skill that cannot locate a script it ships SHALL say so, and SHALL say what consequently went unverified. It SHALL NOT silently substitute its own inspection for a deterministic script: the script exists because the agent's unaided judgement is not equivalent to it.

Every script-bearing skill SHALL state once, beside its script-location fallback, that `python3` in its commands stands for any Python 3.11 or newer that answers on the machine — `python`, the `py` launcher, or a versioned name such as `python3.13` — and that the agent keeps the interpreter that worked for the rest of the conversation. The skill's instructions SHALL NOT scatter platform-specific interpreter hints across individual commands. Guidance for a missing Python SHALL point to the install guide rather than prescribe a package-manager command pinned to one Python version. No skill SHALL tell the agent to record the interpreter in a host's instruction file.

#### Scenario: Windows machine without python3 alias

- **WHEN** a script-bearing skill runs on Windows where `python3` is missing or opens only the Microsoft Store, and Python 3.11 or newer answers as `python`, through the `py` launcher, or under a versioned name such as `python3.14`
- **THEN** the agent runs the skill's commands with that interpreter and keeps it for the rest of the conversation, rather than failing opaquely or telling the user that Python is missing

#### Scenario: Only a versioned interpreter

- **WHEN** a script-bearing skill runs on any operating system where neither `python3` nor `python` answers with 3.11 or newer, but a versioned name such as `python3.13` does
- **THEN** the agent runs the skill's commands with that versioned name and keeps it for the rest of the conversation

#### Scenario: No Python at all

- **WHEN** proposal-check runs and no Python 3.11 or newer answers on the machine
- **THEN** it says so, points the user to the install guide's section on installing Python, and performs the script's checks itself with reduced determinism stated; no script-bearing skill names a version-pinned install command

#### Scenario: Interpreter statement present in every script-bearing skill

- **WHEN** the offline suite inspects the skills that ship scripts
- **THEN** each states what `python3` stands for exactly once, beside its script-location fallback, and none carries a per-command platform interpreter hint

#### Scenario: Agent runs a documented script command

- **WHEN** an agent runs a script invocation exactly as the skill's instructions give it, on a host that substitutes the skill-directory variable
- **THEN** the path resolves to the installed script, wherever the skill is installed and whatever the working directory

#### Scenario: Host does not substitute the variable

- **WHEN** the skill runs on a host that passes the variable through literally
- **THEN** the instructions' prose names the script's location next to the SKILL.md, and the agent can still find and run it

#### Scenario: Fallback prose does not relocate the work

- **WHEN** an agent follows the unexpanded-variable fallback of a skill whose script depends on the working directory — one that writes its output there or resolves `api-keys.env` there
- **THEN** the fallback names the script's location without instructing the agent to work from it, and the skill's outputs and key lookups still resolve against the agent's working directory

#### Scenario: Script cannot be found

- **WHEN** a skill's script is absent or cannot be located
- **THEN** the skill reports that the script did not run and names what was therefore not verified, instead of presenting its own inspection as the script's result

#### Scenario: A skill needs another skill's script

- **WHEN** a skill's instructions run a script that another skill owns
- **THEN** the script ships as a synchronized copy in that skill and is addressed through the skill-directory variable, and the offline suite fails on any install-path reference to a skill's scripts

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
