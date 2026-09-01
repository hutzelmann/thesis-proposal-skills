# Design: workspace proposal-location override

## Context

See proposal.md — Why. Load-bearing current state (from a full sweep of all ten skills, harness, and tests):

- `check.py` resolves the override file as `explicit or proposal.parent / "guidelines.md"` (`load_overrides`, check.py:257). `collect.py` reads `Path.cwd()/guidelines.md`. Customize prose says "workspace root". The three coincide only while proposals live flat in the root.
- `OVERRIDABLE` (check.py:139) is a closed allowlist of `(table, leaf)` tuples; unknown keys are errors via `override_key_findings`; per-key value validation follows the pattern error-finding-then-default (`min-references-invalid`, `page-limit-invalid`).
- Every artifact except `guidelines.md`, `api-keys.env`, and `bug-report/` is proposal-relative already: notes/harvest/review/feedback/handout by slug naming, publish outputs by suffix-swap on the stem, `img/` by relative links, the managed `.gitignore` and workspace-build discovery via `proposal.parent`.
- The harness grades only top-level workspace markdown (`ls ws/*.md`, `ws.glob("*.md")`); `w02`/`w04` fixtures pin the override TOML shape; `tests/unit/test_check.py:53` pins beside-the-proposal discovery; the pinned sentence `proposal-import--output-location.txt` pins "written into the working directory".

Decisions below were settled with the user in a design interview; do not re-litigate them mid-implementation.

## Goals / Non-Goals

**Goals**
- One new overridable leaf, `[paths] proposals`, default `"."`, byte-identical behavior when unset.
- A guidelines-resolution rule that still finds the workspace configuration after proposals move.
- Loud failure for every misconfiguration: invalid value, unknown paths key, misplaced proposal.

**Non-Goals**
- `paths.derived` (review/feedback always beside the proposal) and `paths.archive` (no consumer exists) — deliberately dropped; each is its own future change if a workspace asks.
- Relocating anything that is not the proposal's family: `bug-report/` stays at the cwd (`--out` already exists), `guidelines.md` and `api-keys.env` stay at the root.
- Any change to `publish.py` output placement or the workspace-build contract ("the proposal's directory is the output directory") — both already follow the proposal.
- Metered eval runs. L0 coverage only.

## Decisions

**D1 — Anchor: workspace root = directory of the governing `guidelines.md` = the cwd skills already pin.** `paths.proposals` resolves against it. Alternatives rejected: guidelines moving with the proposals (circular — you must read the file to learn where the file is); agent-passed `--guidelines` only (a forgotten flag silently drops every override — the silent-fallback failure class this repo designs against).

**D2 — `load_overrides` chain: explicit `--guidelines` > `proposal.parent/guidelines.md` > `Path.cwd()/guidelines.md`.** First file found governs the whole run; no key-level merging across positions; no ancestor search. Same shape as the deliberate credential chain. Flat workspaces are untouched (`proposal.parent == cwd`), so `test_check.py`'s tmp-path discovery test keeps passing — the in-process cwd (repo root) holds no `guidelines.md`. New L0 tests must cover: chain order, whole-file-wins, and cwd-position discovery. Note for tests: any test running check in-process from a directory that *could* hold a `guidelines.md` must chdir or pass `--guidelines` explicitly.

**D3 — Family follows the proposal; `paths.derived` collapsed away.** User decision: harvest, publish outputs, review, feedback all sit beside `<slug>.md` wherever it lives. Consequence: no code change in `publish.py`, `collect.py` sidecar lookup, or lit-search notes lookup — all are proposal-relative already. The managed `.gitignore` lands in the proposals directory; that is correct because everything it covers lands there too.

**D4 — Misplacement is check's finding, not a skill fallback.** New error rule (id `proposal-misplaced`) fires when the governing `guidelines.md` sets a non-`"."` `paths.proposals` and `proposal.parent.resolve() != (governing_dir / value).resolve()`. Message names the expected directory. Only the governing file's own directory anchors the comparison, so the finding is well-defined for every chain position.

**D5 — Value validation per the existing per-key pattern.** New error rule (id `paths-proposals-invalid`): value must be `str`, not absolute (`PurePath.is_absolute()` plus Windows-style drive/backslash guard), not `~`-anchored, and its normalized parts must not contain `..`. On violation: error finding + default applies. `(paths, proposals)` joins `OVERRIDABLE`; anything else under `[paths]` falls out of `override_key_findings` as `override-key-unknown` with no extra code.

**D6 — Skills learn the location from prose, not new scripts.** SKILL.md target-resolution and output wording changes from "the working directory" to "the workspace's proposal location — the working directory unless the workspace `guidelines.md` sets `[paths] proposals`". Affected: check (target resolution + guidelines wording), import (output location — pinned sentence edited in the same change, per convention), write (creation + apply-review), reverse (gains its first explicit location statement, closing the silence gap that class of bug came from), supervise (normalized file + artifacts), review (target + output), ideate (seed + notes + resume), lit-search (notes lookup untouched — proposal-relative), publish (target discovery wording only), troubleshoot (target resolution wording; collector unchanged), customize (documents the namespace). The byte-identical shared blocks are untouched.

**D7 — Fixture `w06-paths-workspace`.** Mirrors `w02`: `guidelines.md` at the fixture root setting `[paths] proposals = "proposals/"`, the proposal inside `proposals/`, `expected.json` beside the proposal per fixture convention. It is the positive control for D2/D4 and the working example customize/README point at. Fixture-discovery helpers (`tests/helpers.py`, `test_fixture_oracles.py`, `test_export_matrix.py` corpus glob `*/*.md`) must learn the one-level-deeper proposal without loosening the "exactly one proposal md per fixture" invariant.

## Risks / Trade-offs

- [cwd chain position makes check cwd-sensitive] → Only as a last resort after the beside-proposal miss, and the credential chain already set the precedent; SKILL.mds already pin "run from the working directory". L0 test pins the order.
- [A guidelines.md inside the proposals directory re-anchors the root and produces a confusing misplacement error] → The error message names the governing file's path and the directory it expects, so the misconfiguration is visible in the finding itself.
- [Harness observes only top-level `ws/*.md`; a future paths eval would grade subdirectory output as "no draft"] → Out of scope here (no metered evals); noted so the harness assumption is a known limit, and L0 fixture tests cover the mechanics instead.
- [Generated-copy drift: check.py is vendored into four skills, structure.json into seven] → All edits at the source + `python3 scripts/sync_shared.py`; CI drift check is the backstop.

## Migration Plan

Pure addition: unset key reproduces current behavior, so no user migration. Workspaces that adopt the key move their proposal families by hand; `proposal-misplaced` guides stragglers. Rollback = revert the change; a workspace `guidelines.md` carrying `[paths]` against an old skill version degrades loudly (`override-key-unknown`), not silently.

## Open Questions

None.
