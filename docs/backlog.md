# Backlog

Follow-ups that were deferred by a change or a session and have no change of their own yet. Each line names where the evidence lives. Picking one up means proposing an OpenSpec change for it; an item whose change lands, or that turns out obsolete, is removed here in the same commit.

## Evaluation and measurement

- **Citation support as a review dimension.** The citation-scope bar was not met: L2 attribution scope 6/12, sonnet repair 1/3, haiku repair 0/3 (structurally broken drafts, not citation defects). Evidence: `openspec/changes/archive/2026-10-04-scope-citation-attribution/measurement.md`.
- **`litsearch_bait`.** A lit-search gate test with a pinned candidate set, planned on 2026-09-11 and never built.
- **Degree-level L1 probe** (working name `add-degree-level-review-probe`). A fixture pair with an identical body and a Bachelor vs Master subtitle; review flags missing novelty only for Master. Deferred in `openspec/changes/archive/2026-09-02-add-degree-level-tailoring/`.
- **Matrix cells for the readiness tasks.** `review_ready`, `review_dependency`, `review_converge` and `supervise_ready` have no matrix cells (roster tier `extended`). If promoted, they join `excluded_l1`. Evidence: `openspec/changes/archive/2026-10-13-proportionate-readiness-review/`.
- **Haiku polish routing note.** The shipped note says haiku routes polishing passes to `proposal-write` 0/3, measured with the claude.ai synced skills present; with those surfaces closed the rig measured 6/6. Whether a student's install looks like the first or the second condition is open. Evidence: `openspec/changes/archive/2026-10-05-route-bug-reports-to-troubleshoot/measurement.md`, `openspec/changes/archive/2026-10-05-record-polish-routing-boundary/`.

## Harness

- **Routing report labels.** The routing rig labels its report with the committed skills tree, not the working tree it measured.
- **Silent host stall.** `stream_events` puts no bound on a host that stalls without emitting anything.
- **Harness login, step B.** Observation L1 (the first natural token refresh, task 5.8) and the conditional 5.10 of `openspec/changes/archive/2026-10-06-add-harness-claude-login/` are open; L1 gates removing the `CLAUDE_REAL_CONFIG_DIR` opt-in. Check with `uv run poe host-status` after the next natural refresh; no model call is needed for the check itself.
- **Worktree status view.** One command that lists every worktree with its branch, its open OpenSpec changes and whether it is merged, so open work is visible without an audit.

## Skills

- **Troubleshoot report names the wrong model for an earlier session.** The "Measured facts" requirement still records the troubleshooting agent's own model, so a report about a failure on another model in an earlier session names the wrong one. Listed as a Non-Goal in `openspec/changes/archive/2026-10-05-clarify-troubleshoot-model-subject/design.md`.
- **arXiv and snowball bot checks.** arXiv requests and `snowball.py` do not pass bot checks. A proof-of-work tier at DBLP would block it again; `uv run poe lit-live` exiting 1 shows that.
