## 1. Strengthen the verdict

- [x] 1.1 Give `verdict_import()` a check-output parameter and fail on its errors via `disallowed_errors()`, tolerating only the reference-count shortfall
- [x] 1.2 Keep the existing assertions that the check cannot make: leaked personal or confidential data, and an author name typed beside a bracketed citation
- [x] 1.3 Pass the dev runner's existing check run into the verdict
- [x] 1.4 Stage the check script and structure data for the metered `import_messy` task under a scorer-only path, so the model under test is not handed a check tool it would otherwise not have
- [x] 1.5 Extend the L0 verdict tests: a structurally broken file fails on check errors, a reference shortfall alone passes
- [x] 1.6 Fail the verdict on a `[TODO: …]` marker inside the metadata block, which check.py cannot see because it extracts narrowly instead of parsing YAML

## 2. Fix the skill

- [x] 2.1 Show the exact output shape in `skills/proposal-import/SKILL.md` — a worked trailing metadata block, closed, with `references` as a CSL-YAML list of `- id:` entries
- [x] 2.2 Name the closed methodology set and require mapping the source's own wording onto one of them
- [x] 2.3 State that research questions become an ordered list
- [x] 2.4 Give a concrete reference-key example and state that "et al." never belongs in an author name
- [x] 2.5 State that `[TODO: …]` markers are body text only — a marker inside the metadata block breaks the YAML and the file stops building (observed in 4/4 dev-runner artifacts)
- [x] 2.6 State the `(RQn)` cross-reference obligation, which two of four runs violated

## 3. Verification

- [x] 3.1 `uv run pytest` green
- [x] 3.2 `uv run ruff check .` clean
- [x] 3.3 `openspec validate --all --strict` passes
- [x] 3.4 `python3 scripts/sync_shared.py --check` clean
- [x] 3.5 Measured on the real binary (haiku, 4 runs per round). Under the weak verdict the artifacts "passed" while carrying 6 mechanical errors. Under the strengthened verdict: 0/4, all failures on `(RQn)` cross-references plus one phantom write. After making the worked example *show* `(RQn)` in real sentences rather than describe it: **2/4**, with the RQ defect down from three misses to one. The CSL-list, methodology, key-shape, closed-block and YAML-breaking-TODO defects are gone from every artifact
