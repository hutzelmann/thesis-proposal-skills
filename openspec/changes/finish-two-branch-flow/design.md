# Design

## Context

`add-changelog` D7 set up the two-branch model: `main` moves only by fast-forward to a release's stamp commit, and completed work lands on `develop`, where `poe release` runs. Its follow-ups were left in `docs/backlog.md` ("Release workflow"). The maintainer approved this change with two choices: the two-branch flow is completed as recorded, and the install check runs on `develop` too.

Constraints that shape the approach:

- GitHub's default branch stays `main`. The install prompt, `install.py` and the plugin marketplace read it.
- Scheduled workflows run the workflow file on the default branch, and `actions/checkout` checks out the default branch on a scheduled run unless told otherwise.
- `.githooks/pre-push` is pinned by `tests/unit/test_push_guard.py`; the weekly workflows by `tests/unit/test_currency_workflow.py`, through narrow text extraction (no YAML parser).
- Two testing-harness requirements describe the weekly workflows. The spec gate's length ratchet holds "Weekly model-bump pull request" at 1530 characters and "OpenSpec version kept current" under 500.

## Goals / Non-Goals

**Goals:**

- Every push to `develop` is tested by CI and by the install check before a release moves `main`.
- The pre-push prompt names what the push reaches, and the guard itself (terminal required, explicit yes) stays as it is.
- Bump pull requests are built from `develop`, target it, and judge staleness and foreign commits against it.

**Non-Goals:**

- Changing GitHub's default branch, branch protection or any repository setting. Those are the maintainer's, outside the tree.
- Changing the install check's spec requirement ("Installation verified against the tracked tree", skill-packaging). It says the check runs "in CI on the default branch and on a schedule"; adding `develop` keeps that true. The open change `desktop-first-install` also modifies that requirement, and a second MODIFIED delta would collide with it at archive time.
- Changing what `poe release` does, or the refusal text of the pre-push hook.

## Decisions

### D1 — CI and the install check run on `[main, develop]`

Both workflows add `develop` to `push.branches` and keep `main`. The `main` run of a release commit is the one that tests exactly what installers fetch, and it is cheap. Rejected: `develop` only, which would leave the release commit itself untested after the fast-forward. The `pull_request`, `workflow_dispatch` and `schedule` triggers are unchanged.

### D2 — The pre-push hook classifies by the remote ref

The hook reads each pushed ref's remote name. If any remote ref is `refs/heads/main`, the prompt keeps "This releases to every user."; otherwise it says "This reaches no installer." Keying on the remote ref, not the local one, means `git push origin develop:main` is recognized as a release. The remote's name is not consulted: the hook cannot know which remote is the public one, so a push to any remote's `main` gets the stronger warning. A tag-only push reaches no installer, since every install route fetches `main`, not a tag.

Everything else stays: refs are listed as before, a push with no refs passes without asking, a shell without a terminal is refused with the same message, and anything but `y`/`Y`/`yes` cancels. A `develop` push still needs the maintainer at a terminal, because AGENTS.md makes every push the maintainer's, not only a release.

The tests read the prompt from the pseudo-terminal's master side after the hook exits, so the wording is asserted where the maintainer sees it. Git sends one line per refspec in command-line order, so the tests put other refs before and after `main`'s line, including the release push that `scripts/changelog.py` prints (`develop main <tag>`): a hook that reset the wording per line would fail them.

### D3 — The weekly bots work on `develop`

In both currency workflows:

- `actions/checkout` gets `ref: develop`, so the check reads develop's registry or pin. On a scheduled run it would otherwise check `main`, propose bumps `develop` already carries, and build the bump branch on the release tree.
- `gh pr create --base develop`.
- `gh pr edit "$pr" --base develop` when an open bump pull request is updated. `gh pr list --head` finds the open pull request whatever its base, so one the old workflow opened against `main` would otherwise keep that base while its branch is rebuilt from `develop`, and would then carry every unreleased `develop` commit to the release channel.
- The foreign-commit guard counts commits in `origin/develop..$expected`. With `origin/main..`, every unreleased commit on `develop` that the bump branch was built on would count as a commit by someone else, and the bot would stop updating its own branch after the maintainer's first commit to `develop`.
- The merged-tip exception, the lease, the report check, the fixed branch, the staged file, the `ci.yml` dispatch and the permissions are unchanged. Messages and comments say "develop is current" and "start over from develop".

Rejected: changing only `--base`. The bump commit would still be built on `main` and could conflict with, or duplicate, a bump already merged into `develop`.

The test pins these as workflow properties: the checkout ref, exactly one `gh pr create` and its base, exactly one update of the open pull request and the base it sets, and the guard's range, each with a check that the old `main` form is caught (for the update, also a form that keeps the base).

### D4 — Spec deltas copy the full text and change only the target

"Weekly model-bump pull request" names `develop` as the pull request's target and as the reference for obsolescence. To stay within its 1530-character baseline it tightens wording elsewhere without changing meaning ("creating or updating it", "once it carries a commit by anyone else", ", so the workflow SHALL start"); it measures 1529. "OpenSpec version kept current" adds "against develop" and grows from 456 to 472, under the 500 limit. The scenarios name `develop` where they named `main` and say that a commit already on `develop` is not someone else's; "Pull request already open" says the updated pull request has `develop` as its base (D3's update). Scenario text does not count toward the ratchet.

### D5 — Contributor docs

README "For contributors" gains one bullet and `CONTRIBUTING.md` a short "Branches" section: pull requests target `develop`; `main` holds releases and is the default branch because installers read it; GitHub therefore proposes `main` as the base, and it has to be switched. The PR template gets one checklist line with the same instruction, because it is what a contributor sees when choosing the base. Pinned by `tests/unit/test_release_branches.py`, which also holds the push-trigger tests of D1.

## Risks / Trade-offs

- [The bots keep targeting `main` until the next release] → Scheduled runs read the workflow file on the default branch, so the change takes effect once a release fast-forwards `main`. Until then a bump pull request may open against `main`. The first run after the release that updates it moves it to `develop` (D3). One that the bot leaves untouched because it carries a maintainer commit keeps `main` as its base, and the maintainer retargets it or closes it before merging anything.
- [Two pushes per release run CI twice on the same commit] → Accepted; the `main` run is the release commit's own record, and CI costs minutes, not money.
- [The pre-push refusal still says "A push releases to every user" for a `develop` push] → Kept by scope: the refusal is for agents' shells, whose pushes are refused whatever the branch. A later change may reword it.
- [Contributors open pull requests against `main` anyway, since GitHub proposes the default branch] → The docs and the PR template say to switch the base; the maintainer retargets a pull request that did not.

## Migration Plan

Lands on `develop` like any change. CI and the install check start on the next push of `develop` after it is pushed; the bots switch after the next release. Rollback is a revert on `develop`.

The proposal says `Changelog: internal`: no student, supervisor or workspace maintainer notices the change (openspec/config.yaml). The archive adds a line under `### For contributors` instead (tasks, Workflow follow-up), as `add-release-command` did.
