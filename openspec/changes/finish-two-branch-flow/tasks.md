# Tasks

## 1. CI and the install check on `develop` (D1)

- [x] 1.1 Add `tests/unit/test_release_branches.py` with a narrow `push.branches` extraction and tests that `ci.yml` and `install.yml` run on pushes to both `main` and `develop`, plus a check that a `main`-only list is caught; verify they fail on the current workflows
- [x] 1.2 Add `develop` to `push.branches` in `.github/workflows/ci.yml` and `.github/workflows/install.yml`, keeping every other trigger; verify the tests from 1.1 pass

## 2. Pre-push prompt (D2)

- [x] 2.1 Extend `tests/unit/test_push_guard.py` to read what the hook writes to its terminal, and add tests: a push of `main` (alone, with `develop`, and `develop:main`) asks "This releases to every user"; a push of `develop` or a tag asks "This reaches no installer" and never mentions releasing; a `develop` push without a terminal is still refused; verify the new tests fail on the current hook
- [x] 2.2 Classify the remote refs in `.githooks/pre-push` and choose the prompt's sentence from them, leaving the refusal, the confirmation and the cancellation unchanged; verify `tests/unit/test_push_guard.py` passes

## 3. Weekly bump pull requests against `develop` (D3)

- [x] 3.1 Update `tests/unit/test_currency_workflow.py` first: the guard range is `origin/develop..$expected`, each workflow checks out `ref: develop` and runs exactly one `gh pr create --base develop`, and replacing any of these with its `main` form is caught; verify the tests fail on the current workflows
- [x] 3.2 Update `.github/workflows/model-currency.yml` and `.github/workflows/openspec-currency.yml` (checkout ref, PR base, guard range, step names, comments and messages naming `develop`), keeping branches, dispatch, report checks, permissions and staging; verify `tests/unit/test_currency_workflow.py` passes
- [x] 3.3 Update `harness/README.md`'s weekly bump PR paragraph to say the PR targets `develop` and a merged tip is one carried into `develop`; verify by reading the paragraph against the workflow

## 4. Contributor docs and backlog (D5)

- [x] 4.1 Add tests to `tests/unit/test_release_branches.py` that README "For contributors", `CONTRIBUTING.md` and the PR template name `develop` as the pull-request target; verify they fail first
- [x] 4.2 Add the `develop` target to README "For contributors", a "Branches" section to `CONTRIBUTING.md`, and a checklist line to `.github/PULL_REQUEST_TEMPLATE.md`; verify the tests from 4.1 pass
- [x] 4.3 Remove the five "Release workflow" entries (and the emptied section) from `docs/backlog.md`; verify no entry names a follow-up this change completed

## 5. Review fixes

- [x] 5.1 Extend `tests/unit/test_currency_workflow.py`: each workflow updates its open pull request exactly once, with `gh pr edit "$pr" --base develop`, and an update that keeps the base or names `main` is caught; verify the tests fail on the current workflows
- [x] 5.2 Add `--base develop` to the update of an open bump pull request in `.github/workflows/model-currency.yml` and `.github/workflows/openspec-currency.yml` (D3); verify `tests/unit/test_currency_workflow.py` passes
- [x] 5.3 Add push-guard cases with another ref after `main`'s line (`main` first; the release push `develop main <tag>`); verify they fail against a hook that resets the wording per line and pass on the hook as it is (D2)
- [x] 5.4 Move `CONTRIBUTING.md`'s "Branches" section below the closing privacy paragraph, so that paragraph stays in "How changes work"; verify `tests/unit/test_release_branches.py` passes

## 6. Integration gates

- [x] 6.1 Run `uv run poe test`, `uv run poe specs`, `uv run poe cov`, `python3 scripts/sync_shared.py --check`, `python3 scripts/changelog.py check` and `openspec validate finish-two-branch-flow --strict` from the worktree; verify every one exits 0

## Workflow follow-up

- On archive, the proposal's `Changelog: internal` adds nothing under a user-facing category. Add this line to `CHANGELOG.md` under `## [Unreleased]` → `### For contributors`, ending with the archive link, and commit it with the archive: "Pull requests target `develop`, where CI and the install check now also run on every push; the weekly model and OpenSpec bump pull requests open against `develop`, and the pre-push prompt says whether a push releases to every user or reaches no installer."
- After the next release, confirm the first scheduled bump run opens its pull request against `develop`, or moves an open one there.
