# Backlog

Follow-ups that were deferred by a change or a session and have no change of their own yet. Each line names where the evidence lives. Picking one up means proposing an OpenSpec change for it; an item whose change lands, or that turns out obsolete, is removed here in the same commit.

## Evaluation and measurement

- **Citation support as a review dimension.** The citation-scope bar was not met: L2 attribution scope 6/12, and haiku repair 0/3 (structurally broken drafts, not citation defects); sonnet repair reached 3/3 after the ladder's later steps. Evidence: `openspec/changes/archive/2026-10-04-scope-citation-attribution/measurement.md`.
- **`litsearch_bait`.** A lit-search gate test with a pinned candidate set, planned on 2026-09-11 and never built.
- **Degree-level L1 probe** (working name `add-degree-level-review-probe`). A fixture pair with an identical body and a Bachelor vs Master subtitle; review flags missing novelty only for Master. Deferred in `openspec/changes/archive/2026-09-02-add-degree-level-tailoring/`.
- **Dev-runner scenarios for four skills.** `proposal-publish`, `proposal-reverse`, `proposal-troubleshoot` and `proposal-lit-search` (except as supervise's helper) have no scenario on the subscription dev runner, only metered Inspect tasks (`publish_build`, `reverse_from_harvest`, `troubleshoot_model_rung`, `litsearch_expand`). Scenarios there would catch skill bugs at $0 before a paid matrix run.
- **Key-file ignore in a non-git workspace.** `proposal-lit-search`'s key setup adds `api-keys.env` to the root `.gitignore` whether or not the folder is a git repository, which is agent prose guarded only by a pinned sentence. A dev-runner scenario would seed a non-git folder, accept key setup and assert the root `.gitignore`. Evidence: `openspec/changes/add-setup-readiness-guide/design.md` (D7).
- **Matrix cells for the readiness tasks.** `review_ready`, `review_dependency`, `review_converge` and `supervise_ready` have no matrix cells (roster tier `extended`). If promoted, they join `excluded_l1`. Evidence: `openspec/changes/archive/2026-10-13-proportionate-readiness-review/`.
- **Live check beyond DBLP** (working name `widen-lit-live`). `uv run poe lit-live` runs one DBLP query; arXiv, Crossref and the graph sources are checked only against local fixtures, so a new gate or answer shape there first shows up in a student's run. Evidence: `openspec/changes/classify-arxiv-answers/design.md` (Non-Goals, Risks).
- **Haiku polish routing note.** The shipped note says haiku routes polishing passes to `proposal-write` 0/3, measured with the claude.ai synced skills present; with those surfaces closed the rig measured 6/6. Whether a student's install looks like the first or the second condition is open. Evidence: `openspec/changes/archive/2026-10-05-route-bug-reports-to-troubleshoot/measurement.md`, `openspec/changes/archive/2026-10-05-record-polish-routing-boundary/`.

## Harness

- **Routing report labels.** The routing rig labels its report with the committed skills tree, not the working tree it measured. The routing log's `skills_revision` is the committed `HEAD:skills` even when the working tree changed between sweeps: all four 2026-10-13 sweeps record `36021c9`, although the writing skill's description changed in the working tree between two of them. Evidence: "Also observed" in `openspec/changes/archive/2026-10-13-label-served-models/measurement.md`.
- **Silent host stall.** `stream_events` puts no bound on a host that stalls without emitting anything.
- **Harness login, step B.** Observation L1 (the first natural token refresh, task 5.8) and the conditional 5.10 of `openspec/changes/archive/2026-10-06-add-harness-claude-login/` are open; L1 gates removing the `CLAUDE_REAL_CONFIG_DIR` opt-in. Check with `uv run poe host-status` after the next natural refresh; no model call is needed for the check itself.
- **Worktree status view.** One command that lists every worktree with its branch, its open OpenSpec changes and whether it is merged, so open work is visible without an audit.

## Skills

- **Troubleshoot report names the wrong model for an earlier session.** The "Measured facts" requirement still records the troubleshooting agent's own model, so a report about a failure on another model in an earlier session names the wrong one. Listed as a Non-Goal in `openspec/changes/archive/2026-10-05-clarify-troubleshoot-model-subject/design.md`.
- **Browser fallback for arXiv's Atom feed.** `proposal-lit-search`'s `## If a source asks for browser verification` continues only on DBLP's JSON, so an arXiv verification note would point at a section that does not say what arXiv's valid page, an Atom feed, looks like. arXiv served no verification page on 2026-10-13; deferred by the maintainer. Evidence: `openspec/changes/classify-arxiv-answers/design.md` (Non-Goals).
