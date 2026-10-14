## Context

See proposal.md. The command builds on `scripts/changelog.py` from `add-changelog`, which parses the file into `Release` dataclasses, and on `scripts/stamp_version.py`, which reads `[project] version` and refuses to re-stamp. The package version appears in `pyproject.toml` and in `uv.lock`'s `thesis-proposal-skills` entry. If they disagree, the next `uv run` relocks and leaves the tree dirty.

## Decisions

### D1 — One module, a `release` subcommand

`release` lives in `scripts/changelog.py`, beside `check` and `notes`, so all three share one parser. `poe release` maps to `python3 scripts/changelog.py release`. Each step is a pure function (text in, text out), and `main` wires them together:

- `bump_for(entries, current)`;
- `cut(text, version, date, model_line)`;
- `set_project_version(pyproject_text, v)` and `set_lock_version(lock_text, v)`;
- `readiness_problems(root)`;
- `model_support_line(old_roster, new_roster, old_verdicts, new_verdicts)`.

The L0 tests drive these functions, plus one end-to-end run in a temporary git repo.

### D2 — Bump rule

The entries set the minimum bump:

| Unreleased holds | Minimum bump |
|---|---|
| a `**Breaking:**` entry | major from 1.0.0 on, minor before it |
| an `### Added` entry | minor |
| anything else | patch |

`--bump` may raise the bump and may never lower it. 1.0.0 is only reached through an explicit `--version 1.0.0`, because a computed bump never crosses into 1.0.0 by itself; the readiness gate applies to every version ≥ 1.0.0.

### D3 — Readiness gate for 1.0.0

1.0.0 is refused while either holds:

- `openspec/changes/desktop-first-install/` exists (the change is still open);
- the README region between `<!-- model-support:start -->` and `<!-- model-support:end -->` has a table row containing `untested`.

The refusal names each offending row. The README region is what users read, and `poe report` generates it from the newest matrix logs, so it is the agreed criterion ("every enabled row has a verdict").

### D4 — Model-support entry

**Inputs.**
- Previous release reference: the newest listed version's tag, or the commit its retroactive marker names when the tag is absent.
- Roster: `harness/models.toml` read at that reference through `git show` and at the working tree, parsed with `tomllib`, enabled `[[models]]` only.
- Verdicts: the README summary's `(model, verdict)` rows, at the same two points.

**Prose names.** Take the identifier's last path segment and title-case each hyphen-separated word; `gpt` becomes `GPT`. For example, "Claude Haiku 5.5" and "GPT 6 Luna". The model-ID guard (`tests/unit/test_model_ids.py`) only matches lowercase identifier heads, so a capitalised prose name cannot trip it. A unit test pins this against the current registry.

**Output.** One `### Changed` entry, starting `Model support:`, listing models added, retired and re-judged. When nothing differs, there is no entry.

### D5 — Git effects

**Refusals before any write:**
- `git status --porcelain` shows changes to `CHANGELOG.md`, `pyproject.toml`, `uv.lock` or any `skills/*/SKILL.md`;
- the tag already exists;
- `stamp_version.already_stamped(version)` is true.

**Order of work:**
1. Write the four kinds of file.
2. Call `stamp_version.main([])` in-process.
3. Run `check`.
4. `git add` the exact paths (never `-A`).
5. `git commit -m "chore(publish): stamp X.Y.Z"`, with the pre-commit hook left active.
6. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.

If the commit fails, the files stay modified and the command exits non-zero with a hint. It never resets anything.

**Branches** (add-changelog D7).
- The command runs on `develop`. It refuses on any other branch, and when `main` holds commits that `develop` lacks.
- After tagging, it fast-forwards `main` with `git update-ref refs/heads/main HEAD <old>`.
- When `main` is checked out in some worktree, it moves nothing there and prints the `git -C <path> merge --ff-only develop` to run instead.
- Transition: while no `develop` branch exists, a release on `main` itself is allowed. This covers 0.9.0.
- The printed push is `git push origin develop main vX.Y.Z`; during the transition it is `git push origin main vX.Y.Z`.

**Commands it prints for the maintainer:**
- `git push origin main vX.Y.Z`;
- `python3 scripts/changelog.py notes X.Y.Z > <tmp>`;
- `gh release create vX.Y.Z --title vX.Y.Z --notes-file <tmp>`.

## Risks / Trade-offs

- [The command commits while other sessions share the checkout.] → It stages only explicit paths and refuses if those paths already carry edits.
- [README parsing breaks if `poe report` changes its table.] → The gate test reads the live README, so a format change fails L0 at once.
- [A prose model name collides with the guard later.] → A unit test runs every current roster ID through the prose function and the guard's pattern.
