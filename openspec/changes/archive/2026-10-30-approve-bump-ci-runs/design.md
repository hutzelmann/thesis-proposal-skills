## Context

`track-model-currency` (2026-10-05) and `bump-openspec` (2026-10-14) built two weekly workflows that push a fixed bump branch with `GITHUB_TOKEN`, open or update a pull request against `develop`, and then run `gh workflow run ci.yml --ref "$BRANCH"`. The design's premise was GitHub's documented rule that events caused by `GITHUB_TOKEN` start no new workflow run, `workflow_dispatch` excepted. It also left one question open: do the checks of a dispatched run appear on the pull request?

Measured on PR #5 (OpenSpec 1.15.0), head `3623fe0`, 2026-10-26:

- check suites on the head: one `workflow_dispatch` suite, SUCCESS (`l0`, `l0-windows`, `build-latex`, `build-typst`), and two `pull_request` suites, ACTION_REQUIRED, with no check runs. The workflow made two updates there: the force-push, then `gh pr edit --base develop --title … --body-file …`. Which events caused the two held runs is not visible in the run objects, which carry only `event: pull_request`. On 2026-10-19, when the pull request was opened, there was one.
- `mergeStateStatus: UNSTABLE`, `statusCheckRollup` empty: the dispatched suite does not report on the pull request.
- Repository approval policy `first_time_contributors`, no branch protection. GitHub's change of 2026-06-11 holds `pull_request` runs for pull requests that `github-actions[bot]` authors, even from a branch of the same repository, and offers no setting to turn this off.

## Goals / Non-Goals

**Goals:**
- CI checks report on the bump pull request, and no run is left awaiting approval.
- No new secret and no new permission. The spec's "Workflow bounds" stay exactly as they are.
- When approval does not work, the workflow still runs CI, as today.

**Non-Goals:**
- A personal access token or a GitHub App token, which would make the pushes count as a real user's. Both need a secret beyond the built-in token, which the spec forbids.
- Explaining why one update produced two held runs. The design approves every held run for the pushed commit, so it does not depend on the count.
- Merging or approving the pull request itself. The pull request stays the maintainer's review.

## Decisions

**D1: Approve the held runs with the built-in token.** `POST /repos/{owner}/{repo}/actions/runs/{run_id}/approve` needs `actions: write`, which both workflows already hold for the dispatch. Approved runs are `pull_request` runs, so their checks attach to the pull request. *Alternatives:* (a) leave the held runs: the pull request stays "unstable" and shows no checks; (b) a PAT or App token: rejected by the spec's secret bound; (c) delete the held runs and keep dispatching: the pull request would then show no checks at all.

**D2: Approve every held CI run for the pushed commit, nothing else.** The workflow lists `ci.yml` runs with `--event pull_request --commit "$sha"`, where `$sha` is the commit it just pushed, and approves those with conclusion `action_required`. Filtering by commit keeps it from approving a run that it did not cause. Approving all of them can run CI twice for one push. That costs free Actions minutes on a public repository, once a week at most; leaving one held keeps the pull request "unstable".

**D3: Wait, then settle.** Held runs appear a few seconds after the push or the pull-request update that caused them. The workflow polls every 5 seconds for up to 60 seconds after creating or updating the pull request. Once a held run appears, it waits 10 seconds more and lists again, so a sibling run caused by the second update is approved too.

**D4: Dispatch stays as the fallback.** No held run within the wait, or any failed approval, leads to `gh workflow run ci.yml --ref "$BRANCH"` and a `::warning::` naming the reason. This covers a GitHub reversal (no held runs at all) and an approve endpoint that refuses the built-in token. `ci.yml` keeps `workflow_dispatch:`.

**D5: Inline in both workflows.** The approval block is about 20 lines of shell, repeated in two workflows that already repeat their branch handling inline. The repository extracts at the third repetition. `tests/unit/test_currency_workflow.py` pins both copies through its one property list, as it does for the branch guards.

**D6: Spec text inside the ratchet.** "Weekly model-bump pull request" is baselined at 1530 characters. The premise paragraph is replaced (+28 characters), and the closing sentence drops "read any secret beyond the built-in token", which the first paragraph already rules out (−44). The requirement gets shorter, so the baseline records the new length at archive.

## Risks / Trade-offs

- [The approve endpoint refuses `GITHUB_TOKEN` for bot pull requests] → D4's fallback runs CI as today, and the warning says so. The first weekly run that pushes a bump shows which path ran. Other repositories report that the endpoint accepts it.
- [A held run appears after the wait] → it stays held, as it does today. The pull request description tells the maintainer to approve a run that still waits for approval.
- [Two CI runs per push] → accepted (D2).
- [Approving a run executes code from the bump branch] → the branch is this workflow's own commit on top of `develop`, or a maintainer's (in which case the workflow does not touch the branch, so there is nothing to approve).

## Open Questions

- Does the approve endpoint accept `GITHUB_TOKEN` for these runs? This can only be measured in a real weekly run. Task 4 records it.
