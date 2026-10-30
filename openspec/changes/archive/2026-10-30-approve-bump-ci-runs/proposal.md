## Why

The weekly currency workflows rest on a premise that stopped holding: "a pull request opened with `GITHUB_TOKEN` triggers no `pull_request` workflow". Since GitHub's change of 2026-06-11, a pull request that `github-actions[bot]` opens or pushes to does create `pull_request` runs, but holds them for approval (`action_required`), and no repository setting turns that off. On PR #5 (OpenSpec 1.15.0) the push of 2026-10-26 left two held CI runs beside the dispatched one, so the pull request read "unstable" although CI was green. The dispatched run's checks, in turn, never reached the pull request: GitHub lists none for it (`statusCheckRollup` is empty). That answers the open question `track-model-currency` left: checks from a `workflow_dispatch` run do not show on the pull request.

## What Changes

- Both weekly workflows (`model-currency.yml`, `openspec-currency.yml`), after pushing the bump branch and opening or updating the pull request, wait for the CI runs GitHub holds for that push and approve them with the built-in token. Their checks then report on the pull request, and nothing is left awaiting approval.
- When no held run appears within the wait, or an approval fails, the workflow dispatches CI on the bump branch as it does today, with a warning in the run log. The dispatch stays as a fallback, in case GitHub changes the behavior again.
- The pull request descriptions drop "close and reopen it" for "approve a run that still waits for approval".
- The comments in `ci.yml` and both workflows, `harness/README.md`, and the L0 pins in `tests/unit/test_currency_workflow.py` describe and enforce the new order: approve first, dispatch as fallback.
- Permissions are unchanged. Approving a run needs `actions: write`, which both workflows already hold for the dispatch.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: "Weekly model-bump pull request" replaces the outdated premise with the approval of held runs and keeps the dispatch as fallback, staying within its 1530-character baseline. To make room, its last sentence drops "read any secret beyond the built-in token", which its first paragraph already rules out ("only the repository's built-in token"). Two new scenarios cover held runs and the fallback. "OpenSpec version kept current" keeps its requirement text. Its "Weekly bump proposed" scenario now says that CI reports on the pull request, approved or dispatched as for the model bump.

## Impact

- `.github/workflows/model-currency.yml`, `.github/workflows/openspec-currency.yml`, `.github/workflows/ci.yml` (comment only).
- `harness/model_currency.py` and `scripts/openspec_currency.py` (PR body line), and their tests.
- `tests/unit/test_currency_workflow.py`, `harness/README.md`.
- No model call and no new secret. The approval path is first exercised by the next weekly run that pushes a bump; until then the dispatch fallback is what is known to work.

Changelog: internal
