## Why

Every script-bearing skill tells the agent to run its script as `python3 scripts/<name>.py`. That path is relative to the skill's own directory, but the agent works from the workspace root, where `scripts/` does not exist. Installed skills live at `.claude/skills/<skill>/scripts/`, so the documented command cannot resolve as written.

The agent sometimes recovers and sometimes does not, and when it does not the result is quiet and bad. Observed on the real binary:

- The check skill: *"Deterministic script missing; running manual checks."* It then eyeballed the file and reported findings that were substantively wrong — it called the trailing metadata block misplaced when the format requires it at the end, and downgraded a YAML boolean-literal reference id to a stylistic warning.
- The import skill: *"Scripts not available in project (`scripts/check.py`, `scripts/validate_refs.py`)"*, skipping both verification and reference validation while reporting the import as done.

Both degrade silently: the user sees a confident answer with no indication that the deterministic part never ran. This is not a harness artifact — the dev runner installs skills exactly as users get them and relies on real discovery, so this is what a real workspace does.

## What Changes

- Each script invocation in a skill's instructions states a path the agent can actually resolve from the workspace root, and names the skill-relative location as the authority so the instruction stays correct wherever the skill is installed.
- A skill that cannot find its own script says so, and says what was therefore not verified. Falling back to manual inspection without saying so is prohibited: the deterministic check is the skill's value, and silently substituting a guess for it misleads the user.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: the user-side script constraints gain the requirement that documented script invocations resolve from the agent's working directory, and that a skill unable to locate its script reports that rather than degrading quietly.

## Impact

- `skills/proposal-check/SKILL.md`, `skills/proposal-import/SKILL.md` (two invocations), `skills/proposal-lit-search/SKILL.md` (two), `skills/proposal-publish/SKILL.md` (two) — seven call sites across four skills.
- No script changes and no packaging changes; the files are already installed in the right place. Only the instructions that address them change.
- Measurable on the dev runner: `check_report` currently scores 1–2 of 5 oracle errors when the script is missed, against a script-accurate run that surfaces all five.
