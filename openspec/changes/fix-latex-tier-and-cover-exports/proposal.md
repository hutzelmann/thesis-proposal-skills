# Fix the LaTeX Tier and Cover Every Export Path

## Why

The LaTeX fallback tier does not build. `latex-header.tex` calls `\hypersetup{hidelinks}`, but `--include-in-header` content is emitted before pandoc's template loads hyperref, so pandoc aborts with `Undefined control sequence` and `publish.py` reports "build failed". Every proposal fails on that tier — the tier that exists precisely for users without typst.

The line is redundant: pandoc's own template already emits `hidelinks` after loading hyperref. Deleting it makes all 23 fixtures build.

The defect matters less than the reason it survived. `test_publish.py` exercises `resolve_engine` against a *fake* `which`, plus `strip_abstracts` and `ensure_gitignore` — `build()` has never been executed by a test. The three tests that do invoke pandoc are guarded by `skipif(shutil.which("pandoc") is None)`, and CI installs no pandoc, typst, or TeX, so they skip silently on every run. No test has ever produced a document.

## What Changes

- `\hypersetup{hidelinks}` is removed from the LaTeX header. Verified: all 23 fixtures build on the LaTeX tier afterwards, and link styling is unchanged because pandoc already sets it.
- A build matrix covers every fixture on every output tier, driven through `publish.py`'s own `build()` so the shipped command construction is what gets tested — not a restatement of it. A build is asserted to complete and to produce non-empty declared outputs, PDF tiers additionally checked for a PDF header.
- Targeted content assertions accompany the matrix for what a build-succeeds check cannot see: citations resolved, research-question styling present, TODO annotations numbered.
- CI gains two container jobs so these tests actually run: `pandoc/extra` (pandoc, full TeX Live, Python) covers the LaTeX and word-processor tiers, and `pandoc/typst` (pandoc, typst, no Python) compiles every fixture on the typst tier via a shell script. Image tags are pinned, so a red build always means the change broke something.
- The pandoc command construction in `publish.py` is extracted into a pure function, and an L0 drift test asserts the typst CI script invokes the same template, CSL, and filter chain — the repo's existing guard idiom for a hardcoded copy, and the reason a restatement is acceptable here at all.
- Build tests keep skipping locally when a toolchain is absent; the guarantee comes from CI, where the toolchain is always present.

No user-facing behavior changes beyond the LaTeX tier building at all.

## Capabilities

### New Capabilities

None. This change fixes and verifies existing capabilities.

### Modified Capabilities

- `skill-publish`: gains a requirement that a resolved tier actually produces its declared outputs for a conforming proposal, making the graded-tier promise verifiable rather than nominal.
- `testing-harness`: gains a requirement that automated verification builds real documents on every export path, that such a test drives the shipped build path rather than a reimplementation, and that CI provides the toolchain instead of skipping.

## Impact

- `skills/proposal-publish/templates/latex-header.tex`: one line removed.
- `skills/proposal-publish/scripts/publish.py`: pandoc command construction extracted into a pure function; `build()` calls it. No behavior change, no new dependency (stdlib only, as the hard rules require).
- New `scripts/ci_typst_build.sh` for the typst container job.
- New `tests/unit/test_export_matrix.py` (fixtures × tiers via `build()`) and `tests/unit/test_ci_typst_drift.py` (script vs. constructed command).
- `.github/workflows/ci.yml`: two pinned container jobs added alongside the existing lint/L0 job.
- Unblocks task 5.7 of `highlight-todo-markers`, which cannot pass against a broken tier.
