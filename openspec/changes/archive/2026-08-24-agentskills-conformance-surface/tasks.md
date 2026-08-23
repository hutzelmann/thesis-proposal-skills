# Tasks — agentskills-conformance-surface

## 1. Eval projection

- [x] 1.1 Write `harness/eval_export.py`: `export_evals() -> dict[str, dict]` building the standard's `evals.json` shape per skill from `models.toml` `[tasks.skills]`, task prompts/fixture bindings in `skill_evals.py`/`sources.py`, and assertions derived from L1 verdicts and L2 rubric criteria; `main(argv)` writes `skills/<skill>/evals/evals.json` (GENERATED-marked via a top-level `"generated"` note field)
- [x] 1.2 Generate the projections for all harness-tested skills and commit them
- [x] 1.3 L0 drift test `tests/unit/test_eval_projection.py`: regenerate in-memory, compare to committed files byte-for-byte; failure message points at the harness as the edit site
- [x] 1.4 Confirm `scripts/sync_shared.py` and the pre-commit hook remain stdlib-only and untouched by the projection (drift gate lives in the L0 chain instead); document the regeneration command in `harness/README.md`

## 2. Frontmatter fields

- [x] 2.1 Rework `tests/unit/test_skill_frontmatter.py`: replace set-equality with per-field admission (D2) — `license` required everywhere and matching root `LICENSE.txt`'s identifier, `compatibility` only on `proposal-publish`/`proposal-lit-search` within 1–500 chars, `metadata` only with a `version` key carrying the suite semver (D3, revised: single source is `[project] version` in pyproject.toml); unknown keys still fail; `METADATA_BUDGET` keeps measuring name+description only
- [x] 2.2 Annotate `NAME_LIMIT`, `DESCRIPTION_FORMAT_LIMIT`, `BODY_LINE_LIMIT` (and the new 500-char compatibility limit) with the agentskills.io specification URL as their source
- [x] 2.3 Add `license:` to all eleven `skills/*/SKILL.md`; add `compatibility:` to `proposal-publish` (pandoc/typst toolchain) and `proposal-lit-search` (network access); check the skill-header L0 suite still passes (frontmatter grows, body blocks untouched)
- [x] 2.4 Publish-time stamping: `scripts/stamp_version.py` copies the pyproject semver into every SKILL.md's `metadata.version` (`chore(publish): stamp <version>` commit), refusing to re-stamp a published version; update `harness/README.md` publish pipeline section
- [x] 2.5 `scripts/identify_release.py`: fast path — resolve a report's stamped `version:` line via `git log -S` before falling back to blob-hash comparison; unit-cover stamp parsing (`tests/unit/test_version_stamp.py`)

## 3. Conformance canary

- [x] 3.1 Determine how `skills-ref` is distributed; pinned `skills-ref@0.1.5` (npm) inside `scripts/conform.py` (the CLI validates one directory per call, so the script fans out and aggregates)
- [x] 3.2 Add `poe conform` running the pinned validator over every `skills/*` directory; wire into `poe test` and CI (CI inherits it through the `poe test` gate)
- [x] 3.3 Verify the validator accepts all eleven skills with the new frontmatter — all conform, no divergence-list additions needed

## 4. Documented stance

- [x] 4.1 README: "The Agent Skills standard" section — names agentskills.io, how conformance is validated (`poe conform` + stricter local tests), deliberate-divergence table (workspace-root script paths + dev-runner history, no per-skill lockfile, `templates/` in proposal-publish)
- [x] 4.2 AGENTS.md: agent-facing equivalent with the divergence-not-on-list-is-a-defect rule
- [x] 4.3 Fix `harness/README.md` "all ten skills" → eleven (routing case count 40 → 44 fixed alongside)

## 5. Verify

- [x] 5.1 `uv run poe test` green (includes new drift test, reworked frontmatter test, conform task)
- [x] 5.2 `openspec validate --all --strict` green
