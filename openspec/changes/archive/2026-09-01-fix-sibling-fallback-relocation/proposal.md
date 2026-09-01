# Fix sibling fallback relocation invite

## Why

`2026-08-31-fix-import-output-location` reworded proposal-import's `${CLAUDE_SKILL_DIR}` fallback because "so use that location" invited agents to relocate their work into the skill's install directory — the fallback resolves a script *path*, it never moves the work. The identical hazard phrase survives verbatim in five sibling skills (proposal-write, proposal-check, proposal-lit-search, proposal-publish, proposal-troubleshoot), and two of those scripts are directly working-directory-sensitive: `collect.py` writes its report bundle to `Path.cwd()`, and the lit-search scripts resolve `api-keys.env` against `Path.cwd()` — an agent that "used that location" would misplace a bug report or silently lose the user's API keys. That archived change names this cleanup as its tracked follow-up (design.md, Non-Goals).

## What Changes

- Reword the `${CLAUDE_SKILL_DIR}` fallback paragraph in five SKILL.md files, per-skill by stake:
  - **proposal-write**: adopt the import wording verbatim ("so use that path — but keep running the command from the working directory, where `<slug>.md` stays: the fallback changes where the script is found, never where you work or write") — write edits the same `<slug>.md` in the same working directory that import creates it in.
  - **proposal-troubleshoot**: import shape with the skill's own stake named — `collect.py` writes the report bundle into the working directory. The existing extra sentence about the sibling proposal-check script stays.
  - **proposal-lit-search**: import shape with the skill's own stake named — the scripts look up `api-keys.env` in the working directory, so relocating silently drops the user's keys.
  - **proposal-publish**: import shape with the skill's own stake named — outputs land beside the proposal, and a workspace `proposal-build` definition is discovered beside it and run from the working directory.
  - **proposal-check**: drop the "so use that location" clause entirely, matching the omission shape proposal-supervise and proposal-reverse already use ("…the script really lives in `scripts/` next to this SKILL.md. If you cannot find it…"). Check is read-only by mandate, its script writes nothing, and a relocated relative path fails loudly — a positive relocation instruction has nothing to protect there.
- Strengthen the spec's fallback-prose requirement (`skill-packaging`, "User-side script constraints"): the prose fallback names where the script lives and must not instruct the agent to relocate its work; the documented command still runs from the agent's working directory.
- Add an L0 regression guard in `tests/unit/test_script_paths.py`: the phrase "so use that location" is forbidden in every `SKILL.md` — the known failure mode is the next skill being written by copying the last.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-packaging`: "User-side script constraints" — the prose fallback for non-substituting hosts SHALL name the script's location without directing the agent to work from it; the working directory stays where the user's material lives.

## Impact

- `skills/proposal-write/SKILL.md`, `skills/proposal-check/SKILL.md`, `skills/proposal-lit-search/SKILL.md`, `skills/proposal-publish/SKILL.md`, `skills/proposal-troubleshoot/SKILL.md` — one paragraph each.
- `openspec/specs/skill-packaging/spec.md` — one requirement modified (via delta).
- `tests/unit/test_script_paths.py` — one new assertion.
- No script changes, no mandate changes, no pinned-sentence changes: none of the five mandates or existing pins carries the phrase (verified against `tests/unit/data/skill_mandates/` and `tests/unit/data/pinned_sentences/`). No harness changes.
