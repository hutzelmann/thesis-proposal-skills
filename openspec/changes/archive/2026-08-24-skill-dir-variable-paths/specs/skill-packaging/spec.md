## MODIFIED Requirements

### Requirement: User-side script constraints

Scripts shipped inside skills SHALL run on stock Python ≥ 3.11 standard library only (no package installs), work on Windows/macOS/Linux, never general-parse YAML (narrow documented extraction only), detect missing interpreters/tools with install guidance, and document an agent-side fallback when script networking is denied.

A skill's instructions SHALL address its own scripts through the host's skill-directory substitution variable, so the documented command resolves regardless of the agent's working directory and of where the skill is installed. The instruction SHALL also name the skill-relative location in prose, so a host that does not substitute the variable still leads the agent to the script. A sibling skill's script SHALL be addressed by the standard install path with the same prose fallback — never relative to the skill's own directory, because `../<sibling>/scripts/` is the cross-skill execution shape the audit remediation forbids.

A skill that cannot locate a script it ships SHALL say so, and SHALL say what consequently went unverified. It SHALL NOT silently substitute its own inspection for a deterministic script: the script exists because the agent's unaided judgement is not equivalent to it.

#### Scenario: Windows machine without python3 alias

- **WHEN** a script-bearing skill runs where only the `py` launcher exists
- **THEN** the skill detects and uses it or guides the user, rather than failing opaquely

#### Scenario: Agent runs a documented script command

- **WHEN** an agent runs a script invocation exactly as the skill's instructions give it, on a host that substitutes the skill-directory variable
- **THEN** the path resolves to the installed script, wherever the skill is installed and whatever the working directory

#### Scenario: Host does not substitute the variable

- **WHEN** the skill runs on a host that passes the variable through literally
- **THEN** the instructions' prose names the script's location next to the SKILL.md, and the agent can still find and run it

#### Scenario: Script cannot be found

- **WHEN** a skill's script is absent or cannot be located
- **THEN** the skill reports that the script did not run and names what was therefore not verified, instead of presenting its own inspection as the script's result
