# Fix the LaTeX Tier and Cover Every Export Path — Design

## Context

See proposal.md — Why. Everything below was verified against pandoc 3.10, typst 0.15.1, TeX Live (pdflatex/xelatex/lualatex), and the two container images, on this repo's 23 fixtures.

**The defect.** `--include-in-header` content lands in the preamble *before* pandoc's template loads hyperref. `\hypersetup{hidelinks}` therefore runs against an unloaded package. Pandoc's own template emits `hidelinks` a few lines later, once hyperref is loaded, so the header line was never doing anything except breaking the build. Deleting it builds all 23 fixtures; the alternative of loading hyperref early would work too but changes package load order for no benefit.

**Why no test saw it.** `test_publish.py` covers `resolve_engine` (against a fake `which`), `strip_abstracts`, and `ensure_gitignore`. `build()` is never called. The three pandoc-invoking tests carry `skipif(shutil.which("pandoc") is None)` and CI installs no toolchain, so they skip on every CI run — a skipped test reads as a passing suite.

**Failure mode is loud, not silent.** Pandoc exits 43 with `Error producing PDF`, and `run()` turns that into `sys.exit("build failed: …")`. A plain build-succeeds assertion is therefore sufficient for this bug class; nothing subtler is required to have caught it.

**Container matrix** (verified by running the images):

| Image | pandoc | typst | LaTeX | Python |
|---|---|---|---|---|
| `pandoc/extra` | 3.9.0.2 | no | full — soul, xcolor, titlesec, enumitem, hyperref, geometry | 3.12 + pip |
| `pandoc/typst` | 3.10 | 0.14.2 | no | no |

No official image carries both typst and Python, including the `-ubuntu` and `-debian` flavours. typst 0.14.2 was checked to render the fixture corpus identically to 0.15.1.

## Goals / Non-Goals

**Goals:**

- Every export path produces a document, proven by producing one.
- The proof runs in CI, not only on a maintainer's machine.
- What CI exercises is the shipped build path, not a lookalike.

**Non-Goals:**

- Golden-file or pixel comparison of rendered output. Toolchain versions differ between CI and local, so goldens would encode the environment rather than the behaviour.
- Making the LaTeX tier match the typst tier visually. Graded fidelity is the existing, deliberate contract; this change only makes the tier build.
- Installing a toolchain into CI by package manager. Pre-built images cover it.

## Decisions

### Delete the header line rather than reorder package loading

`\usepackage{hyperref}` ahead of the `\hypersetup` call also fixes the build, but it forces hyperref to load before packages that pandoc's template loads after it, which is a known source of subtle breakage. Deletion is strictly smaller and provably equivalent: pandoc's template already sets `hidelinks` for exactly this document class. Verified on all 23 fixtures with the line removed.

### The matrix drives `publish.build()`

A build test that assembles its own pandoc command tests the test, not the product. `build()` is called directly, with the fixture copied into a temporary directory first — `f16-figures-import` references `img/…` relatively, so a build outside the fixture's own directory fails on a missing asset rather than on anything real.

`run()` raises `SystemExit` on failure, which is the assertion surface: a completed build is one where no `SystemExit` escaped and every returned path exists and is non-empty.

### The typst tier is covered by a script plus a drift guard

`pandoc/extra` can run pytest but has no typst; `pandoc/typst` has typst but no Python, and adding one is the package installation this change is meant to avoid. The seam is real — generating a `.typ` needs no typst, compiling it needs no Python — so the typst job is a shell script that builds every fixture and compiles it.

That script restates the pandoc invocation, which is the same drift risk that hid the original defect. It is therefore guarded the way this repo already guards `rq-filter.lua` against `structure.json` and skill prose against the format contract: `publish.py`'s command construction moves into a pure function, and an L0 test — needing no toolchain, running in the ordinary CI job — asserts the script references the same template, CSL, and filters that function produces.

*Alternative considered:* passing the generated `.typ` between jobs as an artifact. It removes the restatement entirely, but requires `publish.py` to grow a stop-after-source mode that exists only to serve CI. Production code shaped by test plumbing is the worse trade.

### Job `container:`, on the `-ubuntu` image variants

The toolchain is supplied by `container:` on each job — the idiomatic form, with
no container CLI invoked from workflow steps.

The `-ubuntu` tag suffix is load-bearing. Both images default to Alpine, and the
runner mounts its own glibc-built node into a job container so that actions can
execute there; that node cannot run under musl, so `actions/checkout` fails
before any build starts. The Ubuntu 24.04 variants carry the same tools —
verified: `pandoc/extra:3.9.0.2-ubuntu` has pandoc, Python, and every LaTeX
package the header needs, and `pandoc/typst:3.10.0.0-ubuntu` has pandoc 3.10 and
typst 0.14.2 — and avoid the problem entirely.

Ubuntu 24.04 marks its Python environment externally managed, so installing the
test runner needs `--break-system-packages`. The container is discarded after the
job, which is exactly the case where that override is appropriate.

### Pinned image tags

A CI failure must mean "this change broke something". With floating tags, an overnight image rebuild reddens an unrelated pull request, and a suite that cries wolf gets ignored — which is how three skipped tests went unnoticed. Bumps become reviewable commits that can be checked against the fixture corpus.

## Risks / Trade-offs

- **The two images disagree on pandoc version** (3.9.0.2 vs 3.10) → this is coverage, not a defect: users run whatever their package manager ships, and the filters are now exercised on two versions. Recorded so a future failure on one image only is read correctly.
- **CI runs typst 0.14.2 while maintainers run 0.15.1** → verified to render the corpus identically today; the pinned tag makes any future divergence an explicit bump rather than a surprise.
- **The drift guard is a substring check, not a semantic one** → it cannot prove the script is correct, only that it names the same components. That is the same strength as the repo's existing drift tests, and the build itself covers the rest.
- **69 builds add CI time** (~5 s typst, ~50 s LaTeX, ~5 s docx, measured locally) → acceptable for a suite that currently produces no documents at all.
- **`pandoc/extra` needs `pip install pytest`** → a test-runner install in a container job, not a toolchain installation into an image; the toolchain itself is pre-built.
