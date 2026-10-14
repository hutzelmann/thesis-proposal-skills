## Context

See proposal.md, "Why". The facts the design rests on:

- **The publication record is complete.** GitHub's activity API for `refs/heads/main` lists every push since the first commit. The local remote reflog only goes back to 2026-08-11. Pushes on 2026-07-30 (01:48 CEST) and from 2026-08-11 onward are recorded; nothing was pushed between those dates.
- **Only `skills/proposal-*` ships.** The installer, the plugin (`source: ./skills`) and the skills CLI copy nothing else. A root `CHANGELOG.md` is therefore GitHub-only and never becomes a candidate revision for `poe identify`.
- **Two guards bite on history prose.** `tests/unit/test_model_ids.py` fails on any hyphenated model ID that is not a current roster entry. `test_private_local_paths_stay_unnamed` fails on the private directory's name, but it only runs on the maintainer's machine.
- **Archived history is edit-denied.** The changelog may link `openspec/changes/archive/**` but never edit it.

## Goals / Non-Goals

**Goals:** the decisions below, the mapping from tags to commits, and how the gate is built.

**Non-Goals:**
- `poe release`, the 1.0.0 gate and the model-support lines (change `add-release-command`).
- Showing the version in the installer, the troubleshoot collector and `poe identify` (change `surface-suite-version`).
- Pushing tags or creating GitHub Releases (the maintainer's step).

## Decisions

### D1 — Retroactive versions and tags

| Tag | Commit | Committed (CEST) | Reached users |
|---|---|---|---|
| v0.1.0 | 4a8a3de | 2026-07-30 01:47 | pushed 2026-07-30 01:48 |
| v0.2.0 | 35ff3b3 | 2026-07-31 22:32 | with the 2026-08-11 pushes |
| v0.3.0 | b9a0c6c | 2026-08-06 21:06 | with the 2026-08-11 pushes |
| v0.4.0 | 9c43111 | 2026-08-11 23:09 | pushed 2026-08-11 23:22 |
| v0.5.0 | 6ce232e | 2026-08-31 16:13 | pushed 2026-08-31 16:14 |
| v0.6.0 | f2787ff | 2026-09-02 21:09 | pushed 2026-09-02 21:10 |
| v0.7.0 | bf57878 | 2026-10-06 00:56 | with the 2026-10-13 12:44 push |
| v0.8.0 | 88247bf | 2026-10-13 13:36 | pushed 2026-10-13 13:36 |

- `legacy-latex-template` (2dee235) keeps its name and gets no number: it was a different product, a LaTeX template.
- The table was chosen with the maintainer. Pushed heads anchor most tags. The 2026-07-30 → 2026-08-11 block is split at v0.2.0 and v0.3.0, and the 2026-09-02 → 2026-10-13 block at v0.7.0, because each block reached users in one burst but holds several distinct milestones.
- Every bump is minor, because SemVer's 0.x rule treats a breaking change as a minor increase.
- Rejected: one "History before 1.0.0" narrative with no numbers. The maintainer wanted consistent tags.
- Rejected: tags only on states that were pushed. That would have collapsed eight milestones into five.

**Tag form.** The tags are annotated. Their tagger date is set to the commit date through `GIT_COMMITTER_DATE`, so GitHub orders them correctly. The message reads `Retroactive release vX.Y.Z (tagged 2026-10-14). <one-line theme>. <reached-users line>.`

**Release headings.** A heading's date is the tagged commit's committer date in local time. The "reached users" fact goes in the section's lead, not the heading.

**The next real stamp is 0.9.0.** It covers everything after 88247bf, a38b7b1 included: a38b7b1 was pushed on 2026-10-13 18:25, and the maintainer chose not to give it its own tag.

### D2 — One parser, `scripts/changelog.py`

The gate and the coming `poe release` share one stdlib module. Its interface is `main(argv) -> int` with a `check` subcommand. `parse()` returns dataclasses (`Release(version, date, retroactive, commit, entries, links)`) rather than strings, as the repo's conventions require. The test calls `check` in-process.

Rejected: a regex-only test. `poe release` needs the same model to move Unreleased into a new section.

### D3 — What the gate checks

- **Structure.** The header comes first. `## [Unreleased]` appears exactly once and first. Every release heading after it is `## [X.Y.Z] - YYYY-MM-DD`, with versions strictly descending and dates not increasing. The legacy era closes the file as `## Before the skills: LaTeX template (legacy-latex-template)` and is exempt from the version rules.
- **Categories.** Only `### Added | Changed | Deprecated | Removed | Fixed | Security | For contributors` are allowed, in that order.
- **Retroactive releases.** The marker line reads `_Retroactive release — tagged at <sha7> on 2026-10-14._`. A section is either retroactive or stamped, never both.
- **Stamp agreement.**
  - If any `SKILL.md` carries `metadata.version`, all eleven carry the same value, and it equals `[project] version` and the newest non-retroactive release.
  - If no skill is stamped yet, no non-retroactive release may exist.
- **Links.**
  - Every `openspec/changes/archive/<id>/` link resolves.
  - Every listed version has a reference definition `[X.Y.Z]: …/compare/vPrev...vX.Y.Z`. v0.1.0 uses `…/compare/legacy-latex-template...v0.1.0`.
  - `[Unreleased]` compares the newest tag with `HEAD`.
- **No duplicate entries** within a release. This is the backstop for `merge=union`.
- **Coverage.** Every archive folder whose date prefix is ≥ `2026-10-14` must be linked from the changelog, or its `proposal.md` must have a line matching `^Changelog: internal\s*$`. The cutoff is the day this change archives. The four changes archived earlier that day are linked from Unreleased, internal ones under "For contributors". Earlier history is curated by hand, not gated.
- **Tags.** For each listed version whose tag exists in the local repository, `git rev-list -n1 <tag>` must equal the commit the section names. A missing tag skips the check: CI checkouts fetch no tags.

### D4 — `Changelog:` line in proposals, set through `openspec/config.yaml`

- `rules.proposal` makes every proposal end with `Changelog: <one user-facing sentence>`, or `Changelog: internal` for changes users never notice.
- `operations.archive.guidance` says: before archiving, copy that sentence into `## [Unreleased]` under the fitting category, linking the archive folder's final path, in the same commit as the archive.
- `.claude/` is regenerated by `openspec init`, so the hook lives in the tracked `config.yaml` instead.
- Rejected: towncrier fragments, git-cliff, release-please. The OpenSpec change folder already is the per-change fragment, commit types do not encode what breaks for users, and release automation conflicts with the maintainer-only push.

### D5 — Content rules for the history

- Models appear in prose ("Haiku 5.5"), never as hyphenated IDs.
- The private proposals directory is never named. That guard skips in CI, so the agent greps for it by hand before committing.
- Skill counts follow the dates: 8 skills from 2026-07-29, 9 from 2026-08-06, 10 from 2026-08-10, 11 from 2026-08-23.
- **Breaking:** marks only breaks users could see against a published state: api-keys no longer searched in parent directories, the required Timeline section, nested override keys, the SLR contract, title-as-H1, the supervise feedback file, and the review file shape. Breaks that only touched the harness stay unmarked under "For contributors".
- Credit: merged outside work reads "thanks @handle (#N)". PR #1 is credited for its ideas without a name. Bot PRs are not credited.
- Measured claims carry their caveats or are left out.

### D6 — Where the pointers go

- README: one line under "When something goes wrong", next to update-first. That is outside the install-prompt and model-support regions, and keeps the order the user-onboarding spec requires.
- `docs/install.md` "Updating": one line.
- `AGENTS.md` "History": one sentence. The maintainer explicitly approved this edit on 2026-10-14.

### D7 — Two branches: `main` for releases, `develop` for integration (decided 2026-10-14)

**Branches.**
- `main` stays what every install route fetches. It now moves only by fast-forward to a release's stamp commit.
- Completed changes land on `develop`, and `poe release` runs there.
- Because the cut empties `[Unreleased]` in the stamp commit, `main` never carries unreleased entries.
- The name is git-flow's standard one. Rejected: `dev`, a shortening with no convention behind it, and `next`, which reads as "the next release" rather than "where work integrates".

**Transition.**
1. `develop` is created locally from the current `main`, and both changes land on it.
2. The publish session switches to `develop`, cuts 0.9.0 there and fast-forwards `main`.
3. The maintainer pushes both branches and the tags.

Before this change, local `main` already held 14 commits that had not been pushed. They reach users with 0.9.0, as everything on `develop` will from now on.

**Gradual follow-ups**, recorded in `docs/backlog.md`:
- CI `push` triggers for `develop`;
- the pre-push prompt's "releases to every user", which is only true for `main`;
- the model-currency and openspec-currency bots opening their PRs against `develop`;
- `poe install-check`'s trigger;
- the contributor docs in README and `CONTRIBUTING.md`.

The default branch on GitHub stays `main`, because installers and the plugin read it.

## Risks / Trade-offs

- **Old snapshots become easier to find.** Pushed tags make them installable by name (`npx skills add …#v0.3.0`, a marketplace `#ref`, a zip from the installer's `--source`). Any SHA was already installable this way. → Each GitHub Release body opens with "Historical — install from main".
- **Compare links 404 until the maintainer pushes the tags.** → The hand-off says so, and the push commands come with it.
- **`merge=union` can duplicate or reorder lines.** → The uniqueness check catches duplicates. Order is reviewed at merge time.
- **A retroactive section can misstate history.** → Each section is checked against `git log` and the archive by an independent pass before commit, and the maintainer reviews the draft.
- **Tags exist only locally until they are pushed.** The tag check skips them in CI. → It runs on the maintainer's machine, which is where the tags are made.

## Migration Plan

1. Land the change on main (commit per change).
2. Create the eight local tags.
3. Hand the maintainer the push and `gh release create` commands.
4. Notify the publish session that the next stamp is 0.9.0.

Rollback: delete the local tags (`git tag -d`) and revert the commit. Nothing has shipped until the maintainer pushes.
