# Tasks

## 1. Gate first

- [x] 1.1 Write `scripts/changelog.py`: stdlib only, `main(argv: list[str] | None = None) -> int`, a `check` subcommand, and dataclass parse results. It implements every check in design D3. Verify: `uv run ruff check scripts/changelog.py`, and complexity ≤ 12 without a per-file ignore.
- [x] 1.2 Write `tests/unit/test_changelog.py`. It runs `check` in-process against the real `CHANGELOG.md`, plus one minimal synthetic changelog per failure mode in a tmp dir: malformed heading, versions out of order, duplicate entry, unresolved archive link, missing compare link, retroactive and stamped on the same section, a stamp disagreeing with the newest stamped release, an archived change neither linked nor internal, and a tag pointing at another commit. Verify: each synthetic case fails with a message naming its subject, and the real file passes.

## 2. Changelog content

- [x] 2.1 Draft the header: purpose and audience; SemVer meaning and the declared public API (design D3); main is live; the plugin is deliberately unversioned; how to update; where the detailed records live. Verify: the maintainer reviews the draft.
- [x] 2.2 Draft `## [Unreleased]` with the work since 88247bf, including the four changes archived on 2026-10-14, and the retroactive sections v0.8.0 … v0.1.0 plus the legacy-template closer. Each section is written from `git log` over its commit range and the archive folders in that range. Verify: an independent fact-check pass per section against git and the archive, then the D5 content rules (`uv run pytest tests/unit/test_model_ids.py tests/unit/test_repo_conventions.py`).
- [x] 2.3 Show the maintainer the full draft for review before anything is committed, and apply their corrections. Verify: maintainer approval in the session.

## 3. Hooks and pointers

- [x] 3.1 `openspec/config.yaml`: add `rules.proposal` (the `Changelog:` line) and `operations.archive.guidance` (move the line into Unreleased in the archive commit). Verify: `openspec instructions proposal --change add-changelog --json | jq '.rules'` shows the rule, and `uv run poe specs` passes.
- [x] 3.2 `.gitattributes`: add `CHANGELOG.md merge=union` above `# BEGIN generated`. Verify: `python3 scripts/sync_shared.py --check` passes, and `git check-attr merge CHANGELOG.md` prints `union`.
- [x] 3.3 Add the README line under "When something goes wrong", the `docs/install.md` "Updating" line and the `AGENTS.md` "History" sentence. Verify: `uv run pytest tests/unit -k "readme or install_docs or agents or onboarding"` passes.
- [x] 3.4 End this change's own proposal with its `Changelog:` line, and link its archive folder from Unreleased. Verify: the coverage check passes after archive.
- [x] 3.5 Two-branch model (design D7):
  - the `AGENTS.md` git rule;
  - the changelog header, the Unreleased marker (`_On `develop`, not yet released._`) and its entry;
  - `docs/backlog.md` lists the gradual follow-ups.

  Verify: `uv run pytest tests/unit -k "agents or backlog or changelog"` passes.

## 4. Verify and land

- [x] 4.1 `uv run poe test` and `uv run poe specs` pass; `openspec validate add-changelog --strict` is valid. Grep the new and edited files for the private directory name (read from `.git/info/exclude`): no hit.
- [x] 4.2 Archive the change (`openspec archive add-changelog`), then commit once per change on the `changelog` branch. Create the local `develop` branch from `main` and fast-forward it to `changelog`; `main` itself stays where it is. Verify: `git merge-base --is-ancestor main develop` succeeds and `git rev-parse develop` equals the `changelog` head.
- [x] 4.3 Create the eight annotated tags from design D1 locally, with the tagger date set to each commit's date. Verify: `git for-each-ref refs/tags/v0.* --format='%(refname:short) %(*objectname:short) %(taggerdate:short)'` matches the D1 table, and the tag check passes.

## Workflow follow-up

- `develop` carries both changes. The publish session switches its checkout to `develop`, cuts 0.9.0 there with `poe release`, which fast-forwards `main`, and the maintainer pushes `develop`, `main` and the tags.
- Hand the maintainer the tag-push command and eight `gh release create … --notes-file … --latest=false` commands, oldest first, with only `v0.8.0` as latest. Each body opens "Historical — install from main".
- Tell the publish session that the next stamp is 0.9.0 and how to cut it.
