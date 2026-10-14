## Why

Since `add-changelog` (D7, 2026-10-14), `main` holds releases only and completed work lands on `develop`, but the automation and the contributor docs still assume the old single-branch flow. CI and the install check run on pushes to `main` only, so work on `develop` is first tested when a release has already moved `main`. The pre-push hook says "This releases to every user" for a push of `develop`, which reaches no installer. The weekly bump bots open their pull requests against `main`, which only fast-forwards to releases. And no contributor document says which branch a pull request targets. `docs/backlog.md` records these five follow-ups under "Release workflow"; this change completes them.

## What Changes

- **CI on `develop`.** `.github/workflows/ci.yml` runs on pushes to `develop` as well as `main`. Its pull-request and dispatch triggers are unchanged.
- **Install check on `develop`.** `.github/workflows/install.yml` also runs on pushes to `develop`, so a broken install is caught before a release moves `main`. The weekly schedule and the scheduled-only verbatim step are unchanged.
- **Pre-push prompt names what a push reaches.** `.githooks/pre-push` keeps "This releases to every user" when the push updates `main` on the remote, in any combination with other refs. A push that updates no remote `main` (`develop`, another branch, a tag) asks with "This reaches no installer" instead. The terminal confirmation, the refusal of a shell without a terminal, and the cancellation are unchanged.
- **Bump pull requests against `develop`.** The weekly model-currency and openspec-currency workflows run their check on `develop` and open their pull requests against it. A bump then reaches users with the next release. Updating an already open bump pull request also moves its base to `develop`, so one the old workflow opened against `main` is not rebuilt from `develop` and left pointing at the release channel. Their fixed branches, the dispatch of `ci.yml`, the fail-closed report check, the branch guards and the permissions are unchanged; the branch guard now counts commits by others relative to `develop`.
- **Contributor docs name `develop`.** README "For contributors" and `CONTRIBUTING.md` say that pull requests target `develop`, and that GitHub's default branch stays `main` because the installers read it. The PR template's checklist carries the same line, since GitHub proposes `main` as the base. `harness/README.md`'s description of the weekly bump PR follows the new base.
- **Backlog.** The five "Release workflow" entries leave `docs/backlog.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: "Weekly model-bump pull request" and "OpenSpec version kept current" say that the bump pull request targets `develop`, and that `develop`, not `main`, decides when an open bump pull request is obsolete. "Weekly model-bump pull request" tightens three phrases (design D4) to stay within its 1530-character baseline (1529), and its "Pull request already open" scenario names the `develop` base; "OpenSpec version kept current" grows from 456 to 472 characters, under the 500 limit.

## Impact

- Workflows: `.github/workflows/ci.yml`, `install.yml`, `model-currency.yml`, `openspec-currency.yml`. Scheduled runs use the workflow files on the default branch, so the bots switch to `develop` once this change has been released to `main`.
- Hook: `.githooks/pre-push`.
- Tests: `tests/unit/test_push_guard.py` reads what the hook writes to its terminal; `tests/unit/test_currency_workflow.py` pins the base branch on create and on update and the branch guard's range; a new `tests/unit/test_release_branches.py` pins the push triggers of `ci.yml` and `install.yml` and the pull-request target in the contributor docs.
- Docs: `README.md` ("For contributors"), `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `harness/README.md`, `docs/backlog.md`.
- No user-side code, shipped skill or `shared/` file changes. GitHub's default branch stays `main`.

Changelog: internal
