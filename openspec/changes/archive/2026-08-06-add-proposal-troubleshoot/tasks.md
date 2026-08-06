## 1. Support verdicts as vendorable data

- [x] 1.1 Add a JSON export to `harness/support.py` keyed by model and task, emitting a verdict per cell and marking never-measured cells `untested` distinctly from `fail`
- [x] 1.2 Wire the export into `harness/report.py` so `uv run poe report` writes `shared/model-support.json` alongside the README block and `docs/model-support.md`
- [x] 1.3 Commit an initial `shared/model-support.json` generated from the current logs
- [x] 1.4 Extend `scripts/sync_shared.py` to materialize it into `skills/proposal-troubleshoot/references/model-support.json` with the generated-file marker, and confirm `--check` reports drift when the source changes

## 2. User-side collector

- [x] 2.1 Create `skills/proposal-troubleshoot/scripts/collect.py` — stdlib only, Python ≥ 3.11, cross-platform — with `--level {minimal,structure,full}` defaulting to `minimal` and a `--dry-run` that prints the manifest of what would be written without writing
- [x] 2.2 Implement environment probing: Python version, platform, presence and version of `pandoc` and `typst`, all emitted `[measured]`
- [x] 2.3 Implement install identification: copy workspace `skills-lock.json` verbatim when present, and emit `hashes.txt` with path, git blob sha1 of raw bytes, git blob sha1 of LF-normalized bytes, and sha256 for every file under each installed `proposal-*` skill directory
- [x] 2.4 Implement the three disclosure levels: `minimal` (section names, word counts, TODO and reference counts, proposal sha256, captured script output), `structure` (adds headings verbatim, TODO marker texts, reference DOIs), `full` (adds proposal text with the personal-data strip applied)
- [x] 2.5 Write the bundle to `bug-report/` — `report.md`, `skills-lock.json`, `hashes.txt`, `artifacts/` — creating nothing outside that directory, and exit non-zero without writing when `bug-report/` already exists unless `--force` is given
- [x] 2.6 Collect `artifacts/`: the companion notes file's Log section, `guidelines.md` if present, and any captured script stdout/stderr passed in
- [x] 2.7 Emit the `[measured]` / `[self-reported]` scaffold in `report.md` with the self-reported fields left as labelled placeholders for the agent to fill

## 3. Maintainer-side release identification

- [x] 3.1 Create `scripts/identify_release.py` that reads a submitted `hashes.txt`, resolves each blob hash via `git log --all --find-object`, and reports the revision every file matches
- [x] 3.2 Report files matching no revision as locally modified, and report a hash set spanning multiple revisions as a mixed install naming each
- [x] 3.3 Register it as a poe task and document it in `harness/README.md` or the contributor section, whichever is the closer home

## 4. The skill

- [x] 4.1 Create `skills/proposal-troubleshoot/SKILL.md` with frontmatter `name` and a `description` that routes on "a skill misbehaved", not on proposal quality
- [x] 4.2 Write the four opening blocks: purpose, the workflow line with its own name marked, the verbatim voice block, and the mandate
- [x] 4.3 Pin the mandate at `tests/unit/data/skill_mandates/proposal-troubleshoot.txt`
- [x] 4.4 Write the triage ladder as instructions: stale install first, then model, guidelines override, script failure, violated mandate, dissatisfaction — each naming its rung, its verdict, and its remedy
- [x] 4.5 Write the reporting steps: run `collect.py --dry-run` and show its output before any write, take the user's disclosure choice, then run the collector and fill the `[self-reported]` fields including the replay of the failing exchange
- [x] 4.6 Write the reproduction-seed steps: reduce until the defect stops reproducing and restore one step, keep content synthetic under the fixture rules, write `repro/input.md` and `repro/command.txt`, and record a failed reduction instead of inventing one
- [x] 4.7 Write the delivery section: name the issue template, email and supervisor hand-off as the user's options, and state plainly that the skill transmits nothing
- [x] 4.8 State the degraded behavior when `collect.py` cannot be located, per the user-side script constraints

## 5. Cross-skill uniformity

- [x] 5.1 Update the workflow line in all eight existing `SKILL.md` files to name the ninth skill, keeping the line byte-identical apart from the marked name
- [x] 5.2 Add the pinned offer sentence to each of the nine `SKILL.md` files, once, in the skill's own failure path
- [x] 5.3 Re-run `python3 scripts/sync_shared.py` and confirm `--check` is clean

## 6. Draft-selection safety

- [x] 6.1 Exclude anything under `bug-report/` from draft candidate selection in `harness/l1_checks.py`, alongside the existing notes-file and artifact exclusions
- [x] 6.2 Add the same exclusion to the target-resolution prose in `proposal-check`, `proposal-review`, `proposal-write` and `proposal-publish`, so `repro/input.md` is never auto-picked as the proposal

## 7. Repository-facing surfaces

- [x] 7.1 Add the README "When something goes wrong" section between Quick start and Model support, naming the skill, the update-first step, and that proposal text is excluded by default
- [x] 7.2 Replace the bare "please open an issue first" line with a pointer to that section
- [x] 7.3 Add `.github/ISSUE_TEMPLATE/skill-defect.yml` with fields mirroring `report.md` section for section, stating that proposal text is not required
- [x] 7.4 Add a `config.yml` beside it if needed so the template is offered rather than bypassed

## 8. Tests and evals

- [x] 8.1 Extend `tests/unit/test_skill_header_pattern.py` to nine skills and confirm it fails when the ninth skill's workflow line or mandate drifts
- [x] 8.2 Add an offline test asserting the offer sentence appears verbatim exactly once in each of the nine `SKILL.md` files
- [x] 8.3 Add offline tests for `collect.py`: level boundaries (no proposal prose at `minimal`), git blob hash correctness against `git hash-object` for a known file, refusal to overwrite an existing bundle, and writing nothing outside `bug-report/`
- [x] 8.4 Add offline tests for `identify_release.py`: exact revision match, locally-modified file, mixed install
- [x] 8.5 Add an offline test for the `bug-report/` draft-selection exclusion
- [x] 8.6 Add an offline test that the vendored `model-support.json` marks untested cells distinctly and that a suffix match resolves `claude-opus-5` to `anthropic/claude-opus-5`
- [x] 8.7 Add negative eval coverage in `harness/skill_evals.py`: a diagnostic run against a fixture whose oracle expects findings fails if a report offer appears
- [x] 8.8 Add eval coverage that the troubleshoot skill resolves an unsupported-model case without assembling a report

## 9. Verification

- [x] 9.1 `uv run poe test` green — pytest, ruff, and the generated-copy drift check
- [x] 9.2 `openspec validate --all --strict` clean
- [x] 9.3 Run the skill end to end against a synthetic broken workspace at `minimal` and inspect the produced bundle by hand
- [x] 9.4 Confirm a `proposal-check` run that ends in an accepted offer leaves the examined file's digest unchanged
