# Design — skill-dir-variable-paths

## Context

See proposal.md. Claude Code docs: `${CLAUDE_SKILL_DIR}` expands to the skill's absolute directory before the body reaches the model; bash cwd never changes to the skill directory. The Inspect harness injects raw SKILL.md text into its prompt and stages skill assets under `skill/` in the sandbox, so a literal `${CLAUDE_SKILL_DIR}` there would reach the model unexpanded.

## Goals / Non-Goals

**Goals:** portable script paths on substituting hosts; unchanged behavior everywhere else; zero new test surface beyond one guard.

**Non-Goals:** `allowed-tools` grants (deferred — audit-scanner implications); touching the routing dataset (descriptions unchanged); rewriting recorded routing streams (they are parser test data, not skill content).

## Decisions

**D1 — Substitute in the harness, not per-task.** `skill_prompt` replaces `${CLAUDE_SKILL_DIR}` with `skill` once, right where the body is injected — the same place that already explains the `skill/` layout to the model. The dev runner and routing rig use the real host, which substitutes natively.

**D2 — Sibling reference keeps the workspace-root form (revised during implementation).** The first cut used `${CLAUDE_SKILL_DIR}/../proposal-check/scripts/check.py`; `tests/unit/test_audit_invariants.py::test_no_cross_skill_script_execution` rejected it — `../<sibling>/scripts/` is exactly the cross-skill execution shape ATH flagged on proposal-ideate and the audit-pattern-regression requirement exists to keep out. So `proposal-troubleshoot`'s one cross-skill invocation stays `.claude/skills/proposal-check/scripts/check.py` with a prose fallback naming the sibling's own `scripts/` directory, and the path guard test (`test_script_paths.py`) forbids the workspace-root form only for a skill's OWN scripts. The exception is documented in the README divergence list.

**D3 — Fallback sentence stays, retargeted.** The existing "the script really lives in `scripts/` next to this SKILL.md" prose already covers non-substituting hosts; only the first half of the sentence (the "standard project install" framing) changes to name the variable. One L0 guard asserts every SKILL.md script invocation uses the variable form and no `.claude/skills/` path remains in any body.

**D4 — Divergence list shrinks.** The README entry documenting workspace-root paths as a deliberate divergence is removed — the divergence no longer exists. Its history note (dev-runner findings 2026-07-31) moves into the fallback-sentence context in AGENTS.md so the lesson survives the entry.

## Risks / Trade-offs

- [A host that neither substitutes nor reads prose carefully runs `${CLAUDE_SKILL_DIR}/…` literally and fails] → same failure class the old form had on non-standard installs, now with the standard's blessing and a prose rescue; the model-support matrix (Inspect path) exercises the substituted form every run.
- [eval projection prompts] → unaffected: projections carry user requests, not skill bodies.
