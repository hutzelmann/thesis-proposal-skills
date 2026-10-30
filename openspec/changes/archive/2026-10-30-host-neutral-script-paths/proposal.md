# Proposal

## Why

Every script-bearing skill runs its scripts as `python3 ${CLAUDE_SKILL_DIR}/scripts/…`. Only Claude Code substitutes that variable. On Codex, OpenCode (and OpenChamber on top of it), Copilot and the other hosts the skills are installed into, the shell receives an unset variable. The command becomes `python3 /scripts/check.py` and fails, and the agent has to recover through a fallback paragraph. The skills are meant to be interoperable across hosts, and a syntax that works on one host and is wrong on all others is the wrong default. The hosts do not need it: Claude Code (`Base directory for this skill: …`), OpenCode (`Base directory for this skill: …`, with relative paths resolved against it) and Codex (resolve `scripts/foo.py` against the folder holding the `SKILL.md`) each tell the model where the skill lives, as the Agent Skills client guide asks them to.

## What Changes

- Every documented script invocation in the eight script-bearing `SKILL.md` files changes from `${CLAUDE_SKILL_DIR}/scripts/<name>.py` to `<skill-dir>/scripts/<name>.py`. `<skill-dir>` is a placeholder, like the `<location>` and `<slug>` the commands already carry, for the skill's own directory: the folder holding the `SKILL.md`, which the host names when it loads the skill.
- Each skill's fallback paragraph for an unexpanded variable becomes one sentence defining `<skill-dir>`. The paragraph keeps what it says today about where the command runs (the workspace root), why that matters, what `<location>` stands for, what to say when a script cannot be found, and the interpreter clause.
- No skill names a host-specific substitution variable. The offline suite fails on `${CLAUDE_SKILL_DIR}` in any shipped skill and on any script invocation that does not have the `<skill-dir>/scripts/` form.
- The metered Inspect path stops substituting the variable into skill bodies. Its prompt already names the directory where the skill is installed, as a host does, so the model resolves `<skill-dir>` the way it would on a real host.
- README's divergence table gains a row for `<skill-dir>/scripts/…` instead of the standard's bare `scripts/…`. AGENTS.md, `harness/README.md` and the changelog stop describing the variable as the mechanism.
- The change modifies the same `skill-packaging` requirement as the open change `desktop-first-install`, building on that change's text. It is archived after `desktop-first-install`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-packaging`: the User-side script constraints requirement addresses scripts through the host-neutral `<skill-dir>` placeholder defined in prose, instead of the host's substitution variable with a fallback for hosts that do not substitute it.
- `skill-import`: the Output lands in the workspace requirement's scenario about an unexpanded variable now describes resolving `<skill-dir>`, with the same guarantee that the scripts run from the workspace and write nothing into the skill directory. The scenario keeps its name, as do the two `skill-packaging` scenarios about the variable, because OpenSpec has no way to rename or drop a scenario in a MODIFIED block.

## Impact

- `skills/proposal-{check,import,lit-search,publish,reverse,supervise,troubleshoot,write}/SKILL.md`: command lines and the one fallback paragraph each. None of these regions is materialized by `scripts/sync_shared.py` or pinned under `tests/unit/data/`.
- `tests/unit/test_script_paths.py`: the guards for the variable form and the "leaves it unexpanded" fallback become guards for the placeholder form and its definition.
- `harness/skill_evals.py::skill_prompt`: no substitution; the intro sentence says what `<skill-dir>` stands for. Matrix logs written before and after are not comparable cell by cell for the script-running tasks.
- Docs: README divergence table, AGENTS.md ("The Agent Skills standard"), `harness/README.md` (sandbox layout, Codex and Copilot sections), `openspec/long-requirements.json` (entries for this change's two MODIFIED requirements, no longer than their predecessors).
- Users: the command text in the skills changes. Installed skills keep working until they are updated, and nothing in a workspace changes.

Changelog: Skills now run their scripts the same way on every host — Codex, OpenCode, Copilot and Claude Code alike — instead of using a Claude Code variable that other hosts left unfilled.
