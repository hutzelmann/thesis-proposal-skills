# Spec Delta

## MODIFIED Requirements

### Requirement: User-side script constraints

Scripts shipped inside skills SHALL run on stock Python ≥ 3.11 standard library only (no package installs), work on Windows/macOS/Linux, never general-parse YAML (narrow documented extraction only), detect missing interpreters/tools with install guidance, and document an agent-side fallback when script networking is denied.

A skill's instructions SHALL address each script it ships as `<skill-dir>/scripts/<name>`, and SHALL define `<skill-dir>` once in prose as the skill's own directory: the folder holding its `SKILL.md`, which the host names when it loads the skill. No skill SHALL rely on a host-specific substitution variable. The definition resolves a script path and nothing else: it SHALL NOT direct the agent to work from, or write into, the skill's install directory. The documented command still runs from the agent's working directory, where the user's material lives. A skill whose script reads from or writes to a working-directory-dependent location SHALL name that stake beside the definition. A script that another skill owns SHALL ship as a synchronized copy inside the skill that runs it, and SHALL be addressed through `<skill-dir>` like the skill's own scripts — never by an install path, which breaks under user-level and plugin installs, and never relative to the skill's own directory, because `../<sibling>/scripts/` is the cross-skill execution shape the audit remediation forbids.

A skill that cannot locate a script it ships SHALL say so, and SHALL say what consequently went unverified. It SHALL NOT silently substitute its own inspection for a deterministic script: the script exists because the agent's unaided judgement is not equivalent to it.

Every script-bearing skill SHALL state once, beside its `<skill-dir>` definition, that `python3` in its commands stands for any Python 3.11 or newer that answers on the machine — `python`, the `py` launcher, or a versioned name such as `python3.13` — and that the agent keeps the interpreter that worked for the rest of the conversation. The skill's instructions SHALL NOT scatter platform-specific interpreter hints across individual commands. Guidance for a missing Python SHALL point to the install guide rather than prescribe a package-manager command pinned to one Python version. No skill SHALL tell the agent to record the interpreter in a host's instruction file.

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
- **THEN** each states what `python3` stands for exactly once, beside its `<skill-dir>` definition, and none carries a per-command platform interpreter hint

#### Scenario: Agent runs a documented script command

- **WHEN** an agent runs a script invocation as the skill's instructions give it, with `<skill-dir>` replaced by the directory the host named when it loaded the skill
- **THEN** the path resolves to the installed script, on any host, wherever the skill is installed and whatever the working directory

#### Scenario: Host does not substitute the variable

- **WHEN** the skill runs on a host that substitutes no variable into skill text — every host, since no skill relies on one
- **THEN** the `<skill-dir>` definition names the script's location next to the SKILL.md, and the agent can still find and run it

#### Scenario: No host-specific variable in any skill

- **WHEN** the offline suite inspects the shipped skills
- **THEN** no `SKILL.md` contains a host substitution variable such as `${CLAUDE_SKILL_DIR}`, every documented script invocation has the `<skill-dir>/scripts/` form, and each script-bearing skill defines `<skill-dir>` exactly once

#### Scenario: Fallback prose does not relocate the work

- **WHEN** an agent resolves `<skill-dir>` for a skill whose script depends on the working directory — one that writes its output there or resolves `api-keys.env` there
- **THEN** the definition names the script's location without instructing the agent to work from it, and the skill's outputs and key lookups still resolve against the agent's working directory

#### Scenario: Script cannot be found

- **WHEN** a skill's script is absent or cannot be located
- **THEN** the skill reports that the script did not run and names what was therefore not verified, instead of presenting its own inspection as the script's result

#### Scenario: A skill needs another skill's script

- **WHEN** a skill's instructions run a script that another skill owns
- **THEN** the script ships as a synchronized copy in that skill and is addressed through `<skill-dir>`, and the offline suite fails on any install-path reference to a skill's scripts
