# Skill-dir variable paths

## Why

Claude Code now substitutes `${CLAUDE_SKILL_DIR}` (the skill's absolute directory) into skill bodies before the model sees them — a portable answer to the problem that made this repository hardcode workspace-root script paths (`.claude/skills/<skill>/scripts/…`) after the 2026-07-31 dev-runner findings. The variable resolves regardless of install location and working directory; the hardcoded form silently breaks on any non-standard install and is a listed divergence from the Agent Skills standard's path guidance.

## What Changes

- Every documented script invocation in the eight script-bearing `SKILL.md` files switches from `.claude/skills/<skill>/scripts/…` to `${CLAUDE_SKILL_DIR}/scripts/…`. `proposal-troubleshoot`'s cross-skill reference to the check script becomes `${CLAUDE_SKILL_DIR}/../proposal-check/scripts/check.py` (siblings sit next to each other in every install layout).
- The prose fallback stays, retargeted: on hosts that do not substitute the variable, the script lives in `scripts/` next to the SKILL.md — the sentence that already rescues non-Claude hosts keeps doing so.
- The Inspect harness substitutes `${CLAUDE_SKILL_DIR}` → `skill` when injecting a body (`skill_prompt`), so staged sandbox paths keep resolving; the dev runner needs nothing (the real host substitutes).
- README's deliberate-divergence entry for workspace-root paths is replaced: the divergence is resolved, the remaining note documents the fallback for non-substituting hosts.
- `allowed-tools` grants for the script commands are explicitly deferred — a frontmatter widening with audit-scanner implications, its own change if wanted.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `skill-packaging`: the User-side script constraints requirement changes — script paths are addressed through the host's skill-directory substitution variable with a skill-relative prose fallback, instead of a workspace-root path.

## Impact

- 8 `skills/*/SKILL.md` files (check, import, lit-search, publish, reverse, supervise, troubleshoot, write): command lines + fallback paragraph.
- `harness/skill_evals.py::skill_prompt`: one-line substitution.
- Verification: L0 suite (header/mandate pins unaffected — the path paragraphs are not pinned), one dev-runner scenario as a live check.
- README divergence table, AGENTS.md sentence naming the divergence.
