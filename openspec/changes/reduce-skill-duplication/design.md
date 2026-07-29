# Design — reduce-skill-duplication

## Context

See proposal.md — Why. Current mechanics that constrain the design:

- `scripts/sync_shared.py` holds the SYNC_MAP (source → destination dirs), materializes copies with generated-file markers, and CI runs `--check` (`.github/workflows/ci.yml`).
- The import skill already uses a sibling reference with fallback (`../proposal-write/references/guidelines.md`, degradation prose in its SKILL.md) — the pattern being generalized.
- Ideate's SKILL.md invokes only `scripts/search.py`; its fallback paragraph points at "the lit-search skill's fallback URLs" — a cross-reference that itself breaks when the sibling is absent.
- Both eval harnesses stage exactly one skill into the sandbox: `harness/claude_runner.py` `stage()` copies `SKILLS / scenario["skill"]` into `ws/.claude/skills/`; `harness/skill_evals.py` `stage_files()` maps the one skill's `references/scripts/templates` under `skill/` (with an `extra_skill_files` escape hatch). After the change, ideate evals would silently run in sibling-absent mode.

## Goals / Non-Goals

**Goals**
- Ideate ships zero vendored scripts; grounded ideation works via sibling lit-search when installed, agent-fetch otherwise.
- No manual sync step in the dev workflow; CI stays the independent backstop.
- Format-contract prose across SKILL.mds is drift-checked like structure-vs-prose and rq-filter already are.

**Non-Goals**
- No change to what guidelines.md/structure.json consumers vendor (core-function assets stay copies).
- No change to import's vendored `common.py`/`crossref.py` (`validate_refs.py` imports them as Python modules; a missing sibling would crash, not degrade).
- No skills.sh/packaging-registry changes; no user-facing install flow changes.

## Decisions

**D1 — Ideate sibling reference + inlined fallback URLs.**
Ideate's grounding section references `../proposal-lit-search/scripts/search.py` (relative to the skill's base directory, same convention as import's sibling reference). When absent, the SKILL.md instructs agent-side fetch against the same APIs — with the three fallback URL templates (Crossref, DBLP, arXiv) inlined into ideate's SKILL.md rather than cross-referenced, because the current "see the lit-search skill's fallback URLs" pointer is unavailable exactly when it is needed. The URL list is three lines and stable; duplication is acceptable and NOT added to the sync map. If literature is entirely unreachable, the existing ungrounded-notice behavior stands (skill-ideate spec, unchanged).
*Alternative rejected:* vendoring only `search.py` + its source modules — still 7+ copies, keeps the bulk of the problem.

**D2 — SYNC_MAP shrinks; vendored ideate scripts deleted.**
Remove the nine `skills/proposal-lit-search/scripts/*.py → proposal-ideate` entries from SYNC_MAP (the `common`/`crossref` → import entries stay). Delete `skills/proposal-ideate/scripts/` entirely. `references/guidelines.md` remains a synced copy (core-function asset per the modified packaging requirement). Ideate's `references/structure.json` copy is dropped too: no script reads it, its lone SKILL.md mention adds nothing over guidelines.md (which the guidance-model drift check forces to contain every canonical title verbatim), so the copy fails the core-function test that justifies vendoring.

**D3 — Hook via committed `.githooks/` + `core.hooksPath`.**
A committed `.githooks/pre-commit` shell script runs `python3 scripts/sync_shared.py` and `git add`s the SYNC_MAP destination paths it regenerated. Auto-staging is safe: destinations are generated files, never hand-edited (marker headers say so). Activation is a one-time `git config core.hooksPath .githooks` per clone, documented in the README dev section. CI `--check` is unchanged and catches bypassed/unactivated hooks (packaging spec scenario).
*Alternatives rejected:* pre-commit/prek framework — an extra tool plus config file to run one deterministic stdlib script (boilerplate without benefit); CI auto-commit — mutating CI on a direct-on-main repo is worse than a local hook.

**D4 — Format-prose drift test with key-count discovery.**
New L0 pytest in `tests/unit/`. Discovery rule: any `skills/*/SKILL.md` naming **two or more** of the five canonical metadata keys (`title`, `author`, `subtitle`, `lang`, `references`) counts as describing the format and must then (a) name all five keys, (b) state the blank-line rule (match on "blank line"), (c) state the trailing/end position of the block. The canonical key list lives in the test itself — the test is the executable statement of the contract, same as the existing rq-filter drift test. Expected members today: write, import, ideate. Skills touching a single key in passing (lit-search's `references:`, check's "ending in a `---` metadata block") stay out by construction.
*Alternative rejected:* explicit file list in the test — silently misses a future skill that starts describing the format.

**D5 — Eval harnesses stage the sibling for ideate.**
- `claude_runner.py`: scenario dict gains an optional `siblings: [...]` list; `stage()` copies each sibling skill directory into `ws/.claude/skills/` alongside the primary skill. Ideate scenarios declare `proposal-lit-search`. Real skill-discovery layout makes `../proposal-lit-search/…` resolve naturally.
- `skill_evals.py`: ideate tasks stage the lit-search scripts via the existing `extra_skill_files` mechanism under sandbox path `proposal-lit-search/scripts/…`, which is exactly where `skill/../proposal-lit-search/scripts/…` resolves.
- The sibling-absent path (agent-fetch fallback) is intentionally NOT the default eval mode; it may get a dedicated scenario later (out of scope here — the ungrounded-notice scenario already exists in the ideate spec).

## Risks / Trade-offs

- [Ideate grounding quality drops in agent-fetch fallback (no retry/backoff/dedup logic)] → sibling install is the default bundle path (skills.sh all-at-once); fallback is documented degradation, and evals keep the grounded path staged (D5).
- [Fresh clone without hook activation commits stale copies] → CI `--check` fails the push; README documents the one-time activation.
- [Key-count discovery misses a SKILL.md describing the format with one key only] → such prose is already too vague to be a format description; threshold and rationale documented in the test.
- [Inlined fallback URLs in ideate drift from lit-search's] → three stable API base URLs; if they churn, promoting them into SYNC_MAP is trivial.

## Migration Plan

Direct-on-main, one commit series: spec-side edits land with code (specs updated on archive). Rollback = revert the commits; re-running `sync_shared.py` with the old SYNC_MAP restores vendored copies bit-identically.

## Open Questions

None.
