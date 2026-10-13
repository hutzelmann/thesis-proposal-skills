# Measurement: served models behind the archived labels

Extracted on 2026-10-13 from evidence on the maintainer's machine. No model was called. The installed host reports `2.1.296 (Claude Code)` (`claude --version`).

The sources are short-lived or untracked, which is why this file copies them:

- `logs/` is gitignored.
- `/tmp/devrun-*` are temporary dev-run workspaces. Each holds the host's event stream as `.devrun-events.jsonl`.

The served model is the `model` field of the stream's `system/init` event, and the CLI version is its `claude_code_version`. In every stream below, the result event's `modelUsage` lists exactly the init model, with no auxiliary model.

## The alias over time

| Alias | 2026-10-05 (CLI 2.1.284) | 2026-10-13 (CLI 2.1.296) |
|---|---|---|
| `haiku` | `claude-haiku-4-5-20251001` | `claude-haiku-5-5` |
| `sonnet` | `claude-sonnet-5-5` | `claude-sonnet-5-5` |

Sources for 2026-10-05:

- `openspec/changes/archive/2026-10-05-add-dev-runner-judge/measurement.md` (8.1 and the smoke rows);
- `2026-10-05-route-bug-reports-to-troubleshoot/measurement.md`, runs 1, 2 and 4;
- the kept routing streams under `logs/routing/from-vigorous-raman-2026-10-05/` and `logs/routing/paper-foundation-entry/`. These are the last 2.1.284 observations, measured 2026-10-05 around 23:52.

Every 2026-10-13 stream below shows 2.1.296. The alias therefore moved between 2026-10-05 23:52 and 2026-10-13 08:00. The evidence narrows it no further, and it does not show whether the CLI version or the service re-pointed the alias.

## Readiness dev runs (`2026-10-13-proportionate-readiness-review`)

Every line of both logs records the requested alias, the served ID and the CLI version, except the re-grade line, which records the served ID only. Each run line is matched to its kept workspace by an identical `duration_ms` in the line and in the workspace's result event; all 19 match. The judge served `claude-sonnet-5-5` on CLI 2.1.296 on every judged line. Sonnet lines are self-graded.

| Log line | Workspace `/tmp/devrun-…` | Scenario | Requested | Served | CLI | L1 | L2 | Outcome |
|---|---|---|---|---|---|---|---|---|
| `readiness.jsonl:1` | `review_dependency-9iat578z` | review_dependency | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:2` | `review_ready-4vihdrxi` | review_ready | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:3` | `review_converge-ak3iataf` | review_converge | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:4` | `review_dependency-_6m5q0s4` | review_dependency | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:5` | `review_converge-ak3iataf` (re-grade) | review_converge | not recorded | `claude-haiku-5-5` | not on the line; kept stream: 2.1.296 | — | passed | PASS |
| `readiness.jsonl:6` | `review_ready-c2g1i9as` | review_ready | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness.jsonl:7` | `review_dependency-xun6ilwt` | review_dependency | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:8` | `review_hollow-jl3ju0hy` | review_hollow | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness.jsonl:9` | `supervise_ready-_ay7rk2r` | supervise_ready | sonnet | `claude-sonnet-5-5` | 2.1.296 | FAIL | — | FAIL |
| `readiness.jsonl:10` | `review_converge-k0a7xyow` | review_converge | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness.jsonl:11` | `review_dependency-vf172ep6` | review_dependency | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | failed | FAIL |
| `readiness.jsonl:12` | `review_ready-iiko2i6n` | review_ready | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:1` | `review_dependency-nx5xybv7` | review_dependency | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:2` | `review_converge-ygluszon` | review_converge | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:3` | `review_ready-go5p_o27` | review_ready | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:4` | `supervise_ready-1hfowevz` | supervise_ready | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | — | PASS |
| `readiness-final.jsonl:5` | `review_dependency-ptg9pnqx` | review_dependency | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:6` | `review_ready-dgvehujz` | review_ready | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:7` | `review_converge-qh6mzumy` | review_converge | haiku | `claude-haiku-5-5` | 2.1.296 | PASS | passed | PASS |
| `readiness-final.jsonl:8` | `review_fixture-rvpb0iel` | review_fixture | sonnet | `claude-sonnet-5-5` | 2.1.296 | PASS | passed | PASS |

Haiku `review_hollow` is `readiness.jsonl:8` only. Its workspace was written at 08:06, before the final-state reruns at 08:19–08:21. Archived task 7.2 lists it under "Final state".

## Handoff dev runs (`2026-10-13-add-stage-handoffs`, `2026-10-13-sharpen-handoff-choices`)

None of these runs left a summary log, so the kept streams are the only record of the served model. They record neither the requested alias nor a verdict. Each run is assigned to a round of the archived tasks by when its workspace was last written, which is an inference from timing. The verdicts per round are the archived tasks' own counts. "Turns" counts `init` events: a follow-up turn resumes the same session, and both turns report the same served model.

| Window | Attribution | Workspaces `/tmp/devrun-…` (turns) | Served | CLI |
|---|---|---|---|---|
| 09:05–09:06 | stage-handoffs round 1 | `handoff_after_revision-fjfl2j8j` (1), `handoff_ready-4h7prvt2` (1), `handoff_review_feedback-oz6qfnq8` (2), `handoff_superseded-ngnffiqn` (1), `handoff_todos-bsy4zjic` (1) | `claude-haiku-5-5` | 2.1.296 |
| 09:04–09:06 | stage-handoffs round 1 | `handoff_after_revision-pz6olgjq` (1), `handoff_ready-olb1a7p0` (1), `handoff_review_feedback-1l9xabud` (2), `handoff_superseded-fhhvzt2s` (1), `handoff_todos-4g0ytim_` (1) | `claude-sonnet-5-5` | 2.1.296 |
| 09:30–09:32 | round 2 | `handoff_after_revision-rcvlpigz` (1), `handoff_ready-tqmeyfgp` (1), `handoff_review_feedback-vgavxn82` (2), `handoff_superseded-302vyswj` (1), `handoff_todos-mko994hn` (1) | `claude-haiku-5-5` | 2.1.296 |
| 09:30–09:31 | round 2 | `handoff_after_revision-ifym_ewi` (1), `handoff_ready-jqmuved3` (1), `handoff_review_feedback-06vpj967` (2), `handoff_superseded-fwj4v8o0` (1), `handoff_todos-zlj_w_nq` (1) | `claude-sonnet-5-5` | 2.1.296 |
| 09:37–09:39 | round 3 | `handoff_after_revision-1n4ks1bp` (2), `handoff_ready-8j1ubgww` (1), `handoff_review_feedback-sq2o16wv` (2), `handoff_superseded-jaz1z20k` (1), `handoff_todos-ro3f79u7` (1) | `claude-haiku-5-5` | 2.1.296 |
| 09:36–09:38 | round 3 | `handoff_after_revision-5pbfzz0n` (2), `handoff_ready-gtu62f8k` (1), `handoff_review_feedback-4k0l4523` (2), `handoff_superseded-zamxac_n` (1), `handoff_todos-rrh9c5c2` (1) | `claude-sonnet-5-5` | 2.1.296 |
| 09:42 | round 4 | `handoff_after_revision-cpjfg5a4` (2) | `claude-haiku-5-5` | 2.1.296 |
| 09:41 | round 4 | `handoff_after_revision-my1n20a6` (2) | `claude-sonnet-5-5` | 2.1.296 |
| 09:54–09:56 | stage-handoffs regression guards | `review_ready-9fe12hib` (1), `review_converge-shoevtqe` (1), `write_from_seed-lbhzozso` (1) | `claude-sonnet-5-5` | 2.1.296 |
| 10:01 | sharpen 3.2, `handoff_direct_revision` before the block change | `handoff_direct_revision-0pp3unun` (1), `handoff_direct_revision-mu8i23ge` (1) | `claude-sonnet-5-5` | 2.1.296 |
| 10:04–10:06 | sharpen 3.2, after the block change | `handoff_review_feedback-4pr_62ua` (2), `handoff_review_feedback-2n8_8lye` (2), `handoff_todos-k9ar8jl6` (1) | `claude-sonnet-5-5` | 2.1.296 |

Totals:

- haiku: 16 runs, all `claude-haiku-5-5`.
- sonnet: 16 round runs, 3 guards and 5 sharpen runs, all `claude-sonnet-5-5`.

The fourth regression guard, `check_report`, kept no workspace, so its served model is not recorded.

## Routing sweeps of 2026-10-13 (`2026-10-13-add-stage-handoffs`, task 6.3)

The raw logs record the requested alias, the skills revision, the isolation conditions and the login. They record no served model and no CLI version, and no streams were kept (`--keep-events` not passed).

| Run log `logs/routing/from-stage-handoffs-2026-10-13/…` | Requested | Cases × epochs | Correct | Served |
|---|---|---|---|---|
| `20261013-094341.json` | haiku | 11 × 3 | 27/33 | not recorded |
| `20261013-094559.json` (the report in `docs/skill-routing.md`) | sonnet | 58 × 3 | 171/174 | not recorded |
| `20261013-094758.json` | sonnet | 18 × 3 | 54/54 | not recorded |
| `20261013-094912.json` | haiku | 18 × 3 | 43/54 | not recorded |

Inference: haiku served `claude-haiku-5-5` and sonnet `claude-sonnet-5-5`, both on 2.1.296. The basis is timing. The log stamps are written when a sweep ends, and these sweeps ended between 09:43 and 09:49: alongside or just after the round-3 and round-4 dev runs, and before the guard runs at 09:54. They used the same host binary and the same harness login, and the rig's isolated settings pin no model. Every dev run that day resolved the aliases that way. The rig ran no stream that would confirm it.

## The "no regression" comparison (task 6.3)

The archive compares haiku on the ten `review-*` and `write-*` cases with "its 2026-10-05 baseline on the same ten cases (about 7/30 then, 22/30 now)". The kept logs read:

| Case | 2026-10-05 control `20261005-234338.json` | 2026-10-05 edited `20261005-234728.json` | 2026-10-13 `20261013-094912.json` |
|---|---|---|---|
| `review-canonical` | 1/3 | 0/3 | 3/3 |
| `review-canonical-de` | 3/3 | 3/3 | 2/3 |
| `review-collision` | 1/3 | 1/3 | 0/3 |
| `review-oblique` | 0/3 | 2/3 | 3/3 |
| `review-ready-collision` | 3/3 | 3/3 | 3/3 |
| `write-canonical` | 3/3 | 3/3 | 3/3 |
| `write-collision` | 2/3 | 3/3 | 2/3 |
| `write-oblique` | 2/3 | 1/3 | 3/3 |
| `write-oblique-de` | 1/3 | 0/3 | 1/3 |
| `write-polish-collision` | 3/3 | 3/3 | 2/3 |
| **Total** | **19/30** | **19/30** | **22/30** |
| Served (kept streams, last epoch per case) | `claude-haiku-4-5-20251001`, 2.1.284 | `claude-haiku-4-5-20251001`, 2.1.284 | not recorded (inferred `claude-haiku-5-5`, 2.1.296) |

No kept log matches "about 7/30". The nearest figure is the 5/30 that `route-polish-to-write` measured on these cases with the synced claude.ai skills present (`2026-10-05-route-bug-reports-to-troubleshoot/measurement.md`, side finding). Between the two dates, the description, the served model and the CLI version all changed. The 19/30 → 22/30 movement cannot be attributed to any one of them.

## Routing runs of 2026-10-05 (`2026-10-05-route-bug-reports-to-troubleshoot`)

Kept streams under `logs/routing/from-vigorous-raman-2026-10-05/`, one per case (the last epoch):

| Run | Streams | Served (every stream) | CLI |
|---|---|---|---|
| 1, haiku control | `run1-control/`, 15 | `claude-haiku-4-5-20251001` | 2.1.284 |
| 2, haiku edited | `run2-edited/`, 15 (the top-level copies are the same) | `claude-haiku-4-5-20251001` | 2.1.284 |
| 3, haiku reworded case | `run3-haiku/`, 1 | `claude-haiku-4-5-20251001` | 2.1.284 |
| 4, sonnet final state | `run4-sonnet/`, 5 | `claude-sonnet-5-5` | 2.1.284 |
| 5, sonnet reworded case | `run5-sonnet/`, 1 | `claude-sonnet-5-5` | 2.1.284 |

The archive's own measurement.md names these IDs for runs 1, 2 and 4. Runs 3 and 5 match. The "0/33" belongs to haiku 4.5, and so does the registry note on the haiku-4.5 row. Two-thirds of the epochs left no stream, so their served model is inferred from the same sweep.

## What the evidence cannot establish

- **The served model of any 2026-10-13 routing sweep.** It is inferred, not recorded.
- **The served model of the `check_report` regression guard.** It kept no workspace.
- **Which runs a verdict belongs to.** The handoff workspaces carry no verdict, so per-run verdicts cannot be recovered from them. Re-running today's verdict functions over the streams would grade with code that changed between rounds.
- **When or why the alias moved.** It moved at some point between 2026-10-05 23:52 and 2026-10-13 08:00, and the evidence does not show whether by CLI release or by service mapping.
- **Whether the subscription still serves `claude-haiku-4-5-20251001` when it is requested by full ID.** Answering that takes a model call.

## Also observed

The routing log's `skills_revision` is `git rev-parse HEAD:skills`, the committed tree. All four 2026-10-13 sweeps record `36021c9`, although the writing skill's description changed in the working tree between `-094559` and `-094758`. A sweep over uncommitted descriptions is labelled with a revision it did not measure. That is outside this change's scope and is tracked as the "Routing report labels" entry under "Harness" in `docs/backlog.md`.
