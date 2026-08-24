# Tasks — skill-dir-variable-paths

## 1. SKILL.md migration

- [x] 1.1 Replace every `.claude/skills/<skill>/scripts/…` invocation with `${CLAUDE_SKILL_DIR}/scripts/…` in the eight script-bearing SKILL.mds; troubleshoot's cross-skill check invocation becomes `${CLAUDE_SKILL_DIR}/../proposal-check/scripts/check.py`
- [x] 1.2 Retarget the fallback paragraph in each: variable form for substituting hosts, script next to this SKILL.md otherwise; keep the "say what went unverified" sentence verbatim

## 2. Harness

- [x] 2.1 `skill_evals.py::skill_prompt`: substitute `${CLAUDE_SKILL_DIR}` → `skill` when injecting the body
- [x] 2.2 L0 guard test: every documented script invocation in a SKILL.md body uses the variable form; no `.claude/skills/` path survives in any body

## 3. Docs

- [x] 3.1 README divergence table: drop the workspace-root-paths entry; AGENTS.md keeps the dev-runner history beside the new convention
- [x] 3.2 Regenerate eval projections if drift test demands (not expected — bodies are not projected)

## 4. Verify

- [x] 4.1 `uv run poe test` green
- [x] 4.2 `openspec validate --all --strict` green
- [x] 4.3 One live dev-runner scenario (`poe dev check_report --model haiku`) confirms the real host resolves the variable — subscription-billed, cheap
