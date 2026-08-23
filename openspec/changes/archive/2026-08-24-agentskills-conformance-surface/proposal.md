# Agentskills.io conformance surface

## Why

The skills follow the Agent Skills standard (agentskills.io) in substance but the repo neither states that nor tracks it: eval definitions are invisible to consumers of the published skills, spec-legal frontmatter fields are actively rejected by our own gate, and nothing would alert us if the standard moved. An installed skill today carries no license and no version, which also makes `poe identify` slower than it needs to be.

## What Changes

- **Per-skill `evals/evals.json`, generated.** Each published skill gains an `evals/evals.json` in the standard's format (prompt, expected output, files, assertions), materialized by `scripts/sync_shared.py` from harness truth (task→skill map, task prompts, L1 verdict expectations, L2 rubric criteria). GENERATED-marked, drift-gated by the existing `--check`, never hand-edited. No second source of truth.
- **Frontmatter widened, one field at a time.** The frontmatter gate stops asserting `{name, description}` set equality and instead admits exactly three optional spec fields with per-field rules: `license` (every skill; must agree with the root `LICENSE.txt`), `compatibility` (only `proposal-publish` — pandoc/typst toolchain — and `proposal-lit-search` — network access; forbidden elsewhere), `metadata` (a `version` entry stamped by the publish pipeline, giving `poe identify` a fast path before blob-hash comparison). Narrow extraction stays; still no general YAML parsing.
- **Conformance canary.** A pinned `skills-ref validate` run over all skill directories as a poe task and CI step, beside (not replacing) the stricter local tests. The pin bump is the review trigger when the standard evolves. Spec constants in `tests/unit/test_skill_frontmatter.py` (64/1024/500) get annotated with the agentskills.io spec URL they mirror.
- **Documented stance.** README and AGENTS.md gain a short section naming the standard, how conformance is validated, and the deliberate-divergence list (workspace-root script paths and their dev-runner history, no per-skill lockfile, `templates/` instead of `assets/` in proposal-publish).
- Doc fix rolled in: `harness/README.md` says "all ten skills"; eleven exist.

## Capabilities

### New Capabilities
- `standard-conformance`: the repo's relationship to the Agent Skills standard — generated per-skill eval projections, external validator canary, and the documented deliberate-divergence stance.

### Modified Capabilities
- `skill-packaging`: the Frontmatter contract requirement changes — three optional spec fields (`license`, `compatibility`, `metadata.version`) become admissible under per-field rules, and the publish pipeline stamps `metadata.version`; unknown keys remain rejected.

## Impact

- `scripts/sync_shared.py`: new projection target (`skills/*/evals/evals.json`) sourced from `harness/models.toml` task map + `harness/skill_evals.py` prompts + verdict/rubric expectations.
- `tests/unit/test_skill_frontmatter.py`: per-field admission rules replace set equality; spec-URL annotations on the constants.
- All eleven `skills/*/SKILL.md`: `license:` added; `compatibility:` on two skills; `metadata:` stamped at publish (not committed hand-maintained).
- `pyproject.toml` (`[tool.poe.tasks]`), `.github/workflows/ci.yml`: `conform` task running pinned `skills-ref validate`.
- `scripts/identify_release.py` (or its caller): version fast path.
- `README.md`, `AGENTS.md`, `harness/README.md`: stance section, divergence list, count fix.
- Publish pipeline docs in `harness/README.md` (version stamping step).
