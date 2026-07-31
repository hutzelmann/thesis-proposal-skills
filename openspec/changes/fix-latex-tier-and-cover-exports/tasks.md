## 1. Fix

- [x] 1.1 Remove `\hypersetup{hidelinks}` from `skills/proposal-publish/templates/latex-header.tex`, with a comment recording that header content precedes the template's own hyperref load and that pandoc already sets `hidelinks`
- [x] 1.2 Confirm by building that link styling is unchanged — pandoc's emitted `\hypersetup{… hidelinks …}` is still present in the generated `.tex`

## 2. Testable build path

- [x] 2.1 In `skills/proposal-publish/scripts/publish.py`, extract the pandoc command construction from `build()` into a pure function taking the proposal path and tier and returning the argument list, leaving behavior identical
- [x] 2.2 Have `build()` call it, keeping the tier-specific template, header, and engine handling where it is
- [x] 2.3 Verify the extraction changed nothing: `tests/unit/test_publish.py` still passes untouched

## 3. Export matrix

- [x] 3.1 Add `tests/unit/test_export_matrix.py`: parametrize over every fixture proposal × every tier, `skipif` per tier on the tool it needs
- [x] 3.2 Copy each fixture directory into `tmp_path` before building, so relatively referenced assets resolve (`f16-figures-import` carries `img/`)
- [x] 3.3 Drive `publish.build()` directly; assert no `SystemExit` escaped and every returned path exists and is non-empty
- [x] 3.4 Assert the PDF tiers' output begins with the PDF magic bytes and the word-processor tier's output is a readable archive
- [x] 3.5 Add targeted content assertions, not per fixture: citations resolved (no bare `@key` in the built source), research-question styling present, TODO annotations numbered
- [x] 3.6 Confirm the matrix fails as intended by restoring the deleted header line locally and observing the LaTeX tier go red

## 4. CI

- [x] 4.1 Add `scripts/ci_typst_build.sh`: build every fixture proposal to `.typ` and compile it, failing on the first error and naming the fixture
- [x] 4.2 Add a `build-typst` job to `.github/workflows/ci.yml` using `container: pandoc/typst` at a pinned `-ubuntu` tag, running that script
- [x] 4.3 Add a `build-latex` job using `container: pandoc/extra` at a pinned `-ubuntu` tag, installing pytest and running the matrix for the LaTeX and word-processor tiers
- [x] 4.4 Leave the existing lint/L0 job on `ubuntu-latest` unchanged, so the suite still passes without any toolchain
- [x] 4.5 Record the pinned versions and why they are pinned in a comment in the workflow

## 5. Drift guard

- [x] 5.1 Add `tests/unit/test_ci_typst_drift.py`: assert `scripts/ci_typst_build.sh` references the same template, CSL, and every filter that the extracted command function produces for the typst tier
- [x] 5.2 Require no toolchain in that test, so it runs in the ordinary CI job
- [x] 5.3 Confirm it fails when a filter is added to `publish.py` but not to the script

## 6. Verification

- [x] 6.1 `uv run pytest` green locally with the full toolchain present, matrix included
- [x] 6.2 `uv run ruff check .` clean
- [x] 6.3 `python3 scripts/sync_shared.py --check` clean
- [x] 6.4 `openspec validate --all --strict` passes
- [x] 6.5 Build every fixture on every tier and confirm 23/23 on each
- [x] 6.6 Run the two container jobs locally via podman with the pinned images, confirming both pass as CI would
