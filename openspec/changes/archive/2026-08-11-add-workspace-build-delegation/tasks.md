## 1. Discovery and handover in publish.py

- [x] 1.1 Add the module-level candidate constants: the `proposal-build` glob for build files, the recipe-file name set, and the `^proposal-build\b[^\n]*:` target pattern
- [x] 1.2 Implement `find_workspace_build(proposal)` returning the discovered definitions — glob `proposal.parent` for build files, filter recipe files on the declared target, deduplicate by resolved path, return in a stable order
- [x] 1.3 Implement the handover report: name the definition (and for a recipe file its target and runner), state that the built-in pipeline was not used, name the `PROPOSAL_PATH` contract, exit 3
- [x] 1.4 Implement the ambiguity refusal: more than one definition names them all, builds nothing, exits 3
- [x] 1.5 Wire discovery into `main()` after the `--handout` branch and before `resolve_engine()`, so the handout path never reaches it and no engine is resolved for a delegating workspace
- [x] 1.6 Add `--builtin` to skip discovery, documented as the only escape from the refusal
- [x] 1.7 Confirm the handover path calls neither `build()` nor `ensure_gitignore()` and writes no file

## 2. Offline tests for publish

- [x] 2.1 Discovery tests: build file present, absent, suffixless, a non-file candidate, a directory named like a candidate
- [x] 2.2 Recipe-file tests: makefile with the target discovered, makefile without it ignored, justfile with a parameterized target discovered, case-variant names deduplicated
- [x] 2.3 Ambiguity test: build file plus recipe file refuses, names both, exits 3
- [x] 2.4 No-fallback tests: no PDF and no intermediate source written on handover, no toolchain guidance emitted, `--builtin` builds normally
- [x] 2.5 Isolation tests: `--handout` in a delegating workspace writes the export and never hands over; the ignore file is untouched on handover; no `GITIGNORE_ENTRIES` glob matches any candidate name
- [x] 2.6 Ancestor test: a definition one directory above the proposal is not discovered

## 3. Audit invariant

- [x] 3.1 Add the annotated invariant test to `tests/unit/test_audit_invariants.py`: `publish.py` never passes a discovered path to `subprocess`, no `shell=True`, and the subprocess argument lists are built from module-level constants only
- [x] 3.2 Confirm `SUBPROCESS_ALLOWED` is unchanged and no other script gains a subprocess use

## 4. Bug-report collector

- [x] 4.1 Record a workspace build definition in `sibling_artifacts()` in `collect.py`: name verbatim, byte size, sha256, `content withheld at every level`
- [x] 4.2 Tests in `tests/unit/test_troubleshoot_collect.py`: recorded when present, absent when not, contents never in the report at the most disclosing level

## 5. Fixture

- [x] 5.1 Create `tests/fixtures/w05-workspace-build/` — a clean short proposal, a `proposal-build.py` that writes a marker file and prints one line
- [x] 5.2 Calibrate `expected.json` against `skills/proposal-check/scripts/check.py` and confirm `tests/unit/test_fixture_oracles.py` passes
- [x] 5.3 End-to-end test over a `tmp_path` copy of the fixture: `main()` exits 3, names the definition, writes no PDF
- [x] 5.4 Add the `w05` entry to `tests/fixtures/README.md`

## 6. Documentation

- [x] 6.1 Add the `## Workspace build script` section to `skills/proposal-publish/SKILL.md`: the two forms, the one-piece contract, no fallback, handout stays built-in, relay the handover line and name the pipeline that produced the document, exit 3 is not a defect
- [x] 6.2 Add the worked example — a short `proposal-build.py` calling pandoc with a faculty template — and the makefile-target variant
- [x] 6.3 Add the "For supervisors" paragraph to `README.md`: rules are a `guidelines.md`, layout is a build definition, neither is a fork
- [x] 6.4 Confirm the skill header blocks, mandate and report-offer section are untouched

## 7. Gates

- [x] 7.1 `uv run poe test` green
- [x] 7.2 `openspec validate --all --strict` green
- [x] 7.3 `uv run poe cov` above the floor
- [x] 7.4 Commit, then archive the change
