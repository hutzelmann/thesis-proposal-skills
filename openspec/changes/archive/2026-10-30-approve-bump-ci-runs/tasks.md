# Tasks

## 1. Guard first

- [x] 1.1 Extend `tests/unit/test_currency_workflow.py`: each weekly workflow lists `ci.yml` runs with `--event pull_request --commit "$sha"`, selects `action_required`, approves through `actions/runs/$id/approve`, and keeps `gh workflow run ci.yml --ref "$BRANCH"` as the fallback behind a warning. Add mutation cases: the approval removed, and the commit filter removed. Update the module docstring and `test_ci_accepts_the_dispatch`'s docstring (the dispatch is now the fallback). Verify: the new checks fail on both current workflows before task 2.1.
  - 2026-10-30: before 2.1, 6 failed (the security-properties test on both workflows, and the four new mutation cases, which found nothing to mutate), 38 passed.

## 2. Workflows

- [x] 2.1 In `model-currency.yml` and `openspec-currency.yml`, replace the bare dispatch at the end of "Open or update the bump pull request" with the approval block (design D2–D4), and rewrite the header comment's premise paragraph and the `actions: write` comment. Rewrite the `ci.yml` comment on `workflow_dispatch`. Verify: `shellcheck` is clean on the extracted `run:` script of both steps, and task 1.1's tests pass.
  - 2026-10-30: `shellcheck -s bash` is clean on both extracted scripts, `bash -n` passes, and the two approval blocks are identical. 44 of 44 tests in the file pass. The block also ran against a stubbed `gh` under `set -e`, as GitHub's shell runs it. With held runs, the first listing finds run 101 and the settle re-list adds sibling 102; both are approved and nothing is dispatched. With one held run only at the 4th poll, it is approved after 5 listings. With none, 12 listings, then the warning and the dispatch. With an approval refused, both approval calls are made, then the warning and the dispatch.

## 3. Descriptions and docs

- [x] 3.1 Replace the "close and reopen" line in `harness/model_currency.py::render_pr_body` and `scripts/openspec_currency.py::render_pr_body` with the approval line, and update the needles in `tests/unit/test_model_currency.py` and `tests/unit/test_openspec_currency.py`. Update `harness/README.md`'s weekly bump PR paragraph and its step 3. Verify: `grep -rn "close and reopen\|closing and reopening\|triggers no pull_request" .github harness scripts tests` prints nothing outside `openspec/`.
  - 2026-10-30: the grep, widened to README.md, docs/ and AGENTS.md and to "trigger no pull-request", prints nothing.
- [x] 3.2 Run `uv run poe specs` (the modified "Weekly model-bump pull request" must measure at most 1530) and `uv run poe test`. Verify: both green.
  - 2026-10-30: the spec gate passes. The modified requirement measures 1512, against the 1529 the specs record. `poe test`: 6166 passed, 2 skipped; ruff clean, copies in sync, 11 skills conform.

## Follow-up after the push

- The first weekly run that pushes a bump branch answers the design's open question: were the held runs approved (the pull request shows `pull_request` checks and is not "unstable" because of held runs), or did the fallback dispatch CI, with its warning? Tracked as a project todo. If the endpoint refuses the built-in token, the fallback keeps today's behavior, and the approval block is removed in a change of its own.
