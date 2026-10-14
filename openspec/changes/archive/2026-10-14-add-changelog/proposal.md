## Why

The suite has outside users (skills.sh lists 11 skills with about 194 installs, an outside pull request was merged as #2, and issue #3 is open). None of them can tell what changed between two installs. The installer reports a commit SHA. `pyproject.toml` has said 0.1.0 since 2026-07-29. `scripts/stamp_version.py` has existed since 2026-08-24 but has never run, and the only tag is `legacy-latex-template`.

The skill-packaging spec's "Rolling release policy" already says tagged releases begin once outside users exist. The conformance change of 2026-08-24 adopted SemVer in its design D3, but its Non-Goals still read "No semver, tags". The publish session now waiting on main needs a version number. Without a recorded history, it would pick 0.2.

## What Changes

- **`CHANGELOG.md` at the repository root**, written for students, supervisors and workspace maintainers first.
  - Format: Keep a Changelog 1.1.0, plus three things:
    - a `**Breaking:**` prefix, listed first in its group;
    - a link from each entry to its `openspec/changes/archive/<date>-<id>/` folder;
    - a one- or two-sentence lead per release, and a short "For contributors" group at the end of each release.
  - The header states:
    - the SemVer policy and the public API it protects;
    - that `main` is live the moment it is pushed;
    - that the plugin manifest deliberately carries no version.
- **Retroactive history.** Sections v0.8.0 … v0.1.0 cover the suite from its first publication (2026-07-30) to 88247bf (2026-10-13). A closing section covers the LaTeX-template era, which keeps its existing tag `legacy-latex-template`. Each retroactive section names its commit and says it is retroactive. No commit is rewritten.
- **Retroactive tags.** Eight annotated tags `v0.1.0` … `v0.8.0` go on the commits the sections name, with the tagger date set back to the commit date.
  - The agent creates them locally.
  - Pushing the tags and creating one GitHub Release per tag, marked as historical and created oldest first, is the maintainer's step. The agent prints those commands and does not run them.
- **Unreleased.** The section "Unreleased — live on main" lists the work since 88247bf. The first real stamp turns it into 0.9.0.
- **Keeping it current.** `openspec/config.yaml` gains:
  - a proposal rule: every proposal ends with a `Changelog:` line (one user-facing sentence) or `Changelog: internal`;
  - archive guidance: the archive commit moves that line into Unreleased.
- **L0 gate.** `scripts/changelog.py check`, run by `tests/unit/test_changelog.py`, checks:
  - heading shape and order;
  - retroactive markers;
  - the stamp agrees with `pyproject.toml` and with the newest stamped release;
  - archive links resolve, and each release has a compare link;
  - entries within a release are unique;
  - every change archived on or after 2026-10-14 is referenced or declared internal;
  - local tags match the commits their sections name.
- **`.gitattributes`.** A hand-written `CHANGELOG.md merge=union` line keeps parallel worktrees mergeable. The gate's uniqueness check catches duplicated lines.
- **Two-branch release model.**
  - `main` stays the release channel and holds released versions only. It moves by fast-forward to a release's stamp commit.
  - Completed changes land on `develop`, the git-flow name for the integration branch. Releases are cut there, which keeps `[Unreleased]` entries off `main`.
  - The `AGENTS.md` git rule says so. The maintainer requested the model and the edit on 2026-10-14.
  - The rest of the tooling follows gradually and is listed in `docs/backlog.md`: CI triggers, the pre-push wording, the bots' target branch, and the install docs.
- **Pointers.** README gets a "What's new" line in "When something goes wrong", outside every generated region. `docs/install.md` gets an "Updating" link. The "History" section of `AGENTS.md` gets a pointer, which the maintainer approved for this change.

## Capabilities

### New Capabilities

- `release-history`: the user-facing changelog. Covers its audience, format and declared public API, retroactive history, the Unreleased section on a live default branch, and how each archived change is accounted for.

### Modified Capabilities

- `skill-packaging`: "Rolling release policy" changes from "tagged releases begin once outside users exist" to:
  - `main` stays the release channel and holds released versions only, moving by fast-forward;
  - completed work integrates on `develop`, where releases are cut at maintainer-chosen milestones;
  - each release is a stamped, annotated-tagged version with its changelog section;
  - pushing branches and tags and publishing releases stays the maintainer's.

  This supersedes the "No semver, tags" non-goal in `2026-08-24-agentskills-conformance-surface`, which stays unedited in the archive.

## Impact

- New: `CHANGELOG.md`, `scripts/changelog.py`, `tests/unit/test_changelog.py`.
- Edited: `openspec/config.yaml`, `.gitattributes` (hand-written part only), `README.md`, `docs/install.md`, `AGENTS.md` (History pointer and Git rule), `docs/backlog.md`.
- Git: a local `develop` branch created from `main`, where this change lands, and eight local annotated tags. Nothing is pushed.
- Nothing under `skills/` changes, so installs, `poe install-check` and `poe identify` are unaffected. The installers copy `skills/` only.
- Follow-ups: `add-release-command` (`poe release`, the 1.0.0 gate, model-support lines) and `surface-suite-version` (installer, troubleshoot collector and identify show the version; after `desktop-first-install` is archived).

Changelog: Added this changelog, with the suite's history since its first publication as retroactive releases v0.1.0–v0.8.0; installs now receive released versions only, while ongoing work collects on `develop`.
