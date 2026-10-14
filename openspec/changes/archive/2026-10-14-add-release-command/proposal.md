## Why

`add-changelog` defines what a release is: a stamped version, a dated changelog section, and an annotated tag on the stamp commit. Cutting one by hand takes six edits that must agree:

1. pick the bump;
2. move the Unreleased entries;
3. update the compare links;
4. change the version in `pyproject.toml` and `uv.lock`;
5. stamp eleven `SKILL.md` files;
6. commit and tag.

The changelog gate only reports a mismatch after the fact. The first real release (0.9.0) is waiting in the publish session.

Two more decisions made with the maintainer on 2026-10-14 need a mechanism:

- 1.0.0 waits until the desktop install is verified and every enabled model has a measured verdict.
- Model-support changes bypass OpenSpec, as with the weekly currency bot, so the archive hook never sees them.

## What Changes

- **`poe release`** (`scripts/changelog.py release`) cuts a release locally.
  - It refuses to run when:
    - Unreleased has no entries or no lead;
    - a requested bump is lower than the entries require: `**Breaking:**` needs major from 1.0.0 on and minor before it, an `Added` entry needs minor, anything else needs patch;
    - the version is already stamped;
    - a file it is about to touch already has uncommitted edits.
  - It computes the version, or takes `--bump`.
  - It adds a "Model support" entry under `Changed` when the enabled roster in `harness/models.toml`, or a verdict in the README summary, differs from the previous release. Model names are written in prose.
  - It moves the Unreleased entries under `## [X.Y.Z] - <date>`, resets Unreleased, and rewrites the compare links.
  - It sets the version in `pyproject.toml` and in `uv.lock`'s project entry, then stamps the skills through `stamp_version.py`.
  - It runs the changelog gate, commits exactly the files it touched as `chore(publish): stamp X.Y.Z`, and creates the annotated tag `vX.Y.Z`.
  - It runs on `develop` only, under the two-branch model from `add-changelog`. After tagging, it fast-forwards `main` to the stamp commit. When `main` is checked out elsewhere, it prints the `merge --ff-only` to run there instead. It refuses when `main` has diverged. While `develop` does not exist yet, it may run on `main`; that transition case is the 0.9.0 release.
  - It prints, but never runs, the tag push and `gh release create … --notes-file` commands.
  - `--dry-run` prints the new section and the bump reasoning, and writes nothing.
- **The 1.0.0 readiness gate.** `poe release` refuses 1.0.0 or higher while either holds:
  - an OpenSpec change named `desktop-first-install` is still open;
  - any row of the README model-support summary reads untested.
- **`changelog.py notes X.Y.Z`** prints the body for a GitHub Release. It already exists from `add-changelog`; the release command points at it.
- **Docs.**
  - `harness/README.md` "Audit pre-flight (publish pipeline)" replaces its manual bump/stamp/commit step with `poe release`.
  - The docstring of `scripts/stamp_version.py` names `poe release` as its caller.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `release-history` (introduced by `add-changelog`) gains three requirements:
  - one release command keeps version, stamp, changelog and tag in agreement;
  - 1.0.0 waits for the readiness gate;
  - model-support changes are summarized at release.

## Impact

- `scripts/changelog.py` (new `release` subcommand), `tests/unit/test_changelog_release.py`, `pyproject.toml` (`release` poe task), `harness/README.md`, `scripts/stamp_version.py` (docstring only).
- Git: the command makes one commit and one local tag per release. It never pushes and never calls GitHub.
- No skill changes. The stamp it writes into `skills/*/SKILL.md` is the existing `metadata.version` contract.

Changelog: internal
