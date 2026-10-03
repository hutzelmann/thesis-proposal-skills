# Measurement

Before/after measurement for `scope-citation-attribution`, following design D7.

## Setup

**Snapshots.** Each state ran from a frozen `git archive` snapshot of its commit, so editing the worktree could not change a run in flight:

| State | Commit | Contents |
|---|---|---|
| before | `25e8082` | instruments only: old rule text, per-sentence hindsight anchor |
| after | `172fa5d` | stage A: attribution-scope rule, cue-anchored hindsight |

**Runner.** Dev runner (`harness/claude_runner.py`) with `--isolated --keep`: a fresh host configuration (settings emptied, credentials linked), real skill discovery, and the workspace kept for reading. Three runs per model × scenario, three running concurrently, on the subscription.

**Scoring.** Every kept workspace was re-scored afterwards with the verdicts at the final commit (a scratch re-score script), because stage A also tightened the verdict module's block splitting (table rows, code masking). Before and after are therefore judged by identical code. `hindsight_old` and `hindsight_new` report whether the before-state and after-state check script warns on the produced draft.

Columns:

| Column | Meaning |
|---|---|
| L1 | the scenario verdict |
| repeats | sentences repeating the previous sentence's key set |
| cited | cited sentences |
| lost | keys the input cited that the output no longer cites (repair only) |
| structure | no check errors beyond the tolerated reference shortfall |

**Host.** Claude Code 2.1.284, models `sonnet` and `haiku` by alias, 2026-10-03/04.

## Results

### Before (`25e8082`) and after stage A (`172fa5d`)

L1 per run. ✓ means pass; ✗ shows the cause.

| Scenario | Model | Before | After A |
|---|---|---|---|
| repair | sonnet | ✓ ✓ ✗(1 repeat) — **2/3** | ✗(1 repeat) ✗(1 repeat) ✓ — **1/3** |
| repair | haiku | ✗(structure, 9 repeats) ✗(structure, 2 repeats) ✗(8 repeats) — **0/3** | ✗(structure, 2) ✗(structure, 5) ✗(structure, 3) — **0/3** |
| rich seed | sonnet | ✗(1 repeat) ✓ ✓ — **2/3** | ✓ ✓ ✓ — **3/3** |
| rich seed | haiku | ✓ ✓ ✗(1 repeat) — **2/3** | ✓ ✓ ✓ — **3/3** |

Totals across all 12 runs:

| | Before | After A |
|---|---|---|
| repeated-citation sentences | 22 | 12 |
| sources dropped by a repair | 0 | 0 |
| host-reported cost (notional, subscription) | $2.40 | $2.31 |

**Reading.**

- **Repetition is not hypothetical.** Before the change, 9 of 12 runs contained a repetition the rule forbids. Every repeat read by hand was genuine: a bracket citation followed by `@key` on the same source, or the same two-key group on the next sentence. No verdict false positive was found.
- **Drafting from a rich seed became solid on both models** (2/3 → 3/3 each). That is the scenario closest to how a draft is born.
- **The hindsight fix is visible in the data.** All three after-state sonnet repairs carry back-reference continuations that the *before* check would have flagged as hindsight leakage (`hindsight_old = true`), and the new check accepts them (`hindsight_new = false`). Before the change, no sonnet repair produced such a continuation (`hindsight_old = false` for all three). The old per-sentence anchor therefore stood exactly where the design said it would: between the writer and the form the guidance asks for.
- **The polishing pass is not solid.**
  - Sonnet repair dropped from 2/3 to 1/3. With three runs per cell this is within noise, and each failing run left exactly one repeat.
  - Haiku repair fails for a reason outside this change: every run damaged the proposal's structure (methodology section or research-question list lost). The probe run before the batch did the same and also "upgraded" the synthetic references to realistic venues. This matches the 2026-08-10 finding that the cheap tier fails the write bars, and neither ladder step addresses it.
- **Ladder.** The bar requires L1 solid on both models. The repair scenario misses it on repetition (sonnet), so step B is triggered.

### After step B (`a2dba32`)

| Scenario | Model | L1 per run | Cell |
|---|---|---|---|
| repair | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| repair | haiku | ✗(structure, 3 repeats) ✗(structure) ✗(7 repeats) | **0/3** |
| rich seed | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| rich seed | haiku | ✓ ✓ ✓ | **3/3 solid** |

**Reading.**

- **The warning closes the sonnet gap.** All three sonnet repairs remove every repetition, keep every source, and carry the attribution with back-references that only the new hindsight check accepts (`hindsight_old = true`, `hindsight_new = false` on all three).
- **Haiku ignores the warning.** Its one structurally intact repair still carries seven repeats, so the warning does not reach it. This fits the write skill's contract, where only check errors are binding.
- **Ladder.** Citation mechanics gate both models (interview Q11) and repetition persists on haiku, so step C is triggered: the sequential ladder continues after B. The structural breakage, which haiku shows in two of three repair runs, stays outside every ladder step.

### After step C (`8013803`)

| Scenario | Model | L1 per run | Cell |
|---|---|---|---|
| repair | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| repair | haiku | ✗(structure, 2 repeats) ✗(structure, 7) ✗(structure, 5) | **0/3** |
| rich seed | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| rich seed | haiku | ✓ ✓ ✓ | **3/3 solid** |

**Reading.**

- **Sonnet.** Sonnet holds 3/3 on both scenarios: no repeats, no source dropped, every repair hindsight-clean under the new check. One repair uses back-reference continuations. The other two restructure the paragraphs so that no continuation reports a result at all.
- **Haiku, by its own chat reports.** In the polishing pass haiku does not follow the write skill at all:
  - It renames the canonical sections ("Introduction", "Related Work and Contribution", "Methodology"), which `guidelines.md` forbids and the check reports as errors.
  - It rewrites the analytical research questions as yes/no questions, which the skill names as its most common failure.
  - It strips the subtitle emphasis and reports no check result.
  - It removes some citation repetitions, not all ("consolidated five repetitive citations of the Morandi paper", while others remain).

  Each run is therefore a general skill-adherence failure of the cheap tier on a polish request, not a citation-specific one. No wording in this change can repair it, and the ladder ends here as agreed.

Escalation is exhausted (A → B → C). Per the interview, the pipeline stops escalating and reports the haiku repair cell as it stands.

### Re-score after the review fixes

The review fixes (`142d970`) changed the verdict's splitting: sentences across wrapped lines, locators inside brackets, comparison across consecutive list items, and the shared check-script implementation. Re-scoring all 48 kept workspaces of the four states above with the fixed verdict reproduces every number in this document unchanged. None of the measured drafts hard-wrapped, used locators, or moved a repetition into bullets.

### After the review fixes (`142d970`)

L1 cells:

| Scenario | sonnet | haiku |
|---|---|---|
| repair | 3/3 | 0/3, all structural (2, 6, 0 repeats) |
| rich seed | 3/3 | 3/3 |

One sonnet repair drew a **hindsight warning on correct prose**. A mid-sentence reporting clause ("Most projects, they report, …"), a referential "It uses …", and "According to these studies, …" each broke the run under the positional cues alone. The correctly cued sentence after them then warned. A warning like that pushes a writer back to re-citing, so it is a defect of this change, fixed in `326211b` (design D2).

### Shipped state (`326211b`), the final measurement

| Scenario | Model | L1 per run | Cell |
|---|---|---|---|
| repair | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| repair | haiku | ✗(structure, 5 repeats) ✗(structure, 5) ✗(structure, 9) | **0/3** |
| rich seed | sonnet | ✓ ✓ ✓ | **3/3 solid** |
| rich seed | haiku | ✓ ✓ ✓ | **3/3 solid** |

Each sonnet repair removes every repetition, keeps all seven sources, and carries the attribution with back-references. The old check would have flagged all three as hindsight leakage; the shipped check flags none.

Across all 72 kept drafts the shipped check emits **no** hindsight warning. The before-state check flagged 14 of them, every one a back-reference continuation the guidance asks for.

### Bar (design D7, item 6), evaluated at the shipped state

| Criterion | Result |
|---|---|
| L1 solid on both models, both scenarios | **Not met** for haiku × repair (0/3): structural breakage, general skill non-adherence. Met for the other three cells. |
| L1 solid on the capable tier | **Met**: sonnet 3/3 on both scenarios, in four consecutive states (B, C, review fixes, shipped). |
| L2 citation scope (both models) and synthesis (sonnet) | Pending: stop 1, cost approval. |
| The user's eye on before/after samples | Pending: stop 2. |

### Totals across stages

12 runs per state:

| State | Passing cells (of 4) | L1 passes (of 12) | Repeated-citation sentences | Sources dropped |
|---|---|---|---|---|
| before | 0 | 6 | 22 | 0 |
| after A | 2 | 7 | 12 | 0 |
| after B | 3 | 9 | 10 | 0 |
| after C | 3 | 9 | 14 (all in haiku repair) | 0 |
| review fixes | 3 | 9 | 8 (all in haiku repair) | 0 |
| shipped | 3 | 9 | 19 (all in haiku repair) | 0 |

From "after B" on, every repetition in every state sits in haiku's structurally broken polishing passes. Sonnet's repairs and both models' drafts from the rich seed carry none.

### Kept workspaces

The kept workspaces are local and ephemeral (`/tmp`, gone at reboot). They are listed so that the re-score and the stop-2 samples stay traceable while they exist.

| State | Scenario | Model | Run | L1 | Produced draft |
|---|---|---|---|---|---|
| before | repair | sonnet | 1 | ✓ | `/tmp/devrun-write_repair_citations-bk_v3t8e/dependency-update-breakage.md` |
| before | repair | sonnet | 2 | ✓ | `/tmp/devrun-write_repair_citations-bdj7bvvg/dependency-update-breakage.md` |
| before | repair | sonnet | 3 | ✗ | `/tmp/devrun-write_repair_citations-aqww6sn_/dependency-update-breakage.md` |
| before | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-ku_itehy/dependency-update-breakage.md` |
| before | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-9zv5nxca/dependency-update-breakage.md` |
| before | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-c0w001j0/dependency-update-breakage.md` |
| before | rich_seed | sonnet | 1 | ✗ | `/tmp/devrun-write_rich_seed-nsbrcok1/flaky-test-prediction.md` |
| before | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-ki09fx8n/flaky-test-prediction.md` |
| before | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-fb4kvpui/flaky-test-prediction.md` |
| before | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-sfayxyzs/flaky-test-prediction.md` |
| before | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-itorradu/flaky-test-prediction.md` |
| before | rich_seed | haiku | 3 | ✗ | `/tmp/devrun-write_rich_seed-5v1_07ar/flaky-test-prediction.md` |
| after A | repair | sonnet | 1 | ✗ | `/tmp/devrun-write_repair_citations-nzsxaiv5/dependency-update-breakage.md` |
| after A | repair | sonnet | 2 | ✗ | `/tmp/devrun-write_repair_citations-l2vqmper/dependency-update-breakage.md` |
| after A | repair | sonnet | 3 | ✓ | `/tmp/devrun-write_repair_citations-ahewblca/dependency-update-breakage.md` |
| after A | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-hovxkup3/dependency-update-breakage.md` |
| after A | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-yndh8vam/dependency-update-breakage.md` |
| after A | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-25wz_wcb/dependency-update-breakage.md` |
| after A | rich_seed | sonnet | 1 | ✓ | `/tmp/devrun-write_rich_seed-3xb3h97o/flaky-test-prediction-2.md` |
| after A | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-pumgpwxb/flaky-test-prediction.md` |
| after A | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-xpceh1n7/flaky-test-prediction.md` |
| after A | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-wkbyqf1c/flaky-test-prediction.md` |
| after A | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-53ye10qs/flaky-test-prediction.md` |
| after A | rich_seed | haiku | 3 | ✓ | `/tmp/devrun-write_rich_seed-2qjv1ziq/flaky-test-prediction.md` |
| after B | repair | sonnet | 1 | ✓ | `/tmp/devrun-write_repair_citations-eqqx9u3t/dependency-update-breakage.md` |
| after B | repair | sonnet | 2 | ✓ | `/tmp/devrun-write_repair_citations-qzi3o_bb/dependency-update-breakage.md` |
| after B | repair | sonnet | 3 | ✓ | `/tmp/devrun-write_repair_citations-6u25oy0j/dependency-update-breakage.md` |
| after B | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-5kubqt67/dependency-update-breakage.md` |
| after B | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-gy7oen5t/dependency-update-breakage.md` |
| after B | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-aq8xht9t/dependency-update-breakage.md` |
| after B | rich_seed | sonnet | 1 | ✓ | `/tmp/devrun-write_rich_seed-ovtdxat4/flaky-test-prediction.md` |
| after B | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-wahi4jxs/flaky-test-prediction.md` |
| after B | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-8c1itucx/flaky-test-prediction.md` |
| after B | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-i_t_d1om/flaky-test-prediction.md` |
| after B | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-h84dgll2/flaky-test-prediction.md` |
| after B | rich_seed | haiku | 3 | ✓ | `/tmp/devrun-write_rich_seed-zd6ic0pq/flaky-test-prediction.md` |
| after C | repair | sonnet | 1 | ✓ | `/tmp/devrun-write_repair_citations-u0bkm7hn/dependency-update-breakage.md` |
| after C | repair | sonnet | 2 | ✓ | `/tmp/devrun-write_repair_citations-j_ybcqhy/dependency-update-breakage.md` |
| after C | repair | sonnet | 3 | ✓ | `/tmp/devrun-write_repair_citations-fm1hduf1/dependency-update-breakage.md` |
| after C | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-jp9rbapm/dependency-update-breakage.md` |
| after C | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-eh_cq8bv/dependency-update-breakage.md` |
| after C | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-2o3ia1sv/dependency-update-breakage.md` |
| after C | rich_seed | sonnet | 1 | ✓ | `/tmp/devrun-write_rich_seed-bc8rcenv/flaky-test-prediction-2.md` |
| after C | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-zck98_ge/flaky-test-prediction.md` |
| after C | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-fcrqak9x/flaky-test-prediction-2.md` |
| after C | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-08go6sdy/flaky-test-prediction.md` |
| after C | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-ofxgmm13/flaky-test-prediction.md` |
| after C | rich_seed | haiku | 3 | ✓ | `/tmp/devrun-write_rich_seed-ucaj2p75/flaky-test-prediction.md` |
| review fixes | repair | sonnet | 1 | ✓ | `/tmp/devrun-write_repair_citations-_xiu8rac/dependency-update-breakage.md` |
| review fixes | repair | sonnet | 2 | ✓ | `/tmp/devrun-write_repair_citations-d1onsqho/dependency-update-breakage.md` |
| review fixes | repair | sonnet | 3 | ✓ | `/tmp/devrun-write_repair_citations-bs2ad5pu/dependency-update-breakage.md` |
| review fixes | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-cpqeuz5p/dependency-update-breakage.md` |
| review fixes | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-mmf3_m_z/dependency-update-breakage.md` |
| review fixes | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-o36o5z8y/dependency-update-breakage.md` |
| review fixes | rich_seed | sonnet | 1 | ✓ | `/tmp/devrun-write_rich_seed-u2mj2zq_/flaky-test-prediction-2.md` |
| review fixes | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-8n7nyx97/flaky-test-prediction.md` |
| review fixes | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-ipeml77d/flaky-test-prediction.md` |
| review fixes | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-mo3om8np/flaky-test-prediction.md` |
| review fixes | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-jqi5p53d/flaky-test-prediction.md` |
| review fixes | rich_seed | haiku | 3 | ✓ | `/tmp/devrun-write_rich_seed-0qcl10o3/flaky-test-prediction.md` |
| shipped | repair | sonnet | 1 | ✓ | `/tmp/devrun-write_repair_citations-qmimmsb7/dependency-update-breakage.md` |
| shipped | repair | sonnet | 2 | ✓ | `/tmp/devrun-write_repair_citations-62viwrrf/dependency-update-breakage.md` |
| shipped | repair | sonnet | 3 | ✓ | `/tmp/devrun-write_repair_citations-rf4h1w_u/dependency-update-breakage.md` |
| shipped | repair | haiku | 1 | ✗ | `/tmp/devrun-write_repair_citations-626l98vw/dependency-update-breakage.md` |
| shipped | repair | haiku | 2 | ✗ | `/tmp/devrun-write_repair_citations-aro1te75/dependency-update-breakage.md` |
| shipped | repair | haiku | 3 | ✗ | `/tmp/devrun-write_repair_citations-70q5bsri/dependency-update-breakage.md` |
| shipped | rich_seed | sonnet | 1 | ✓ | `/tmp/devrun-write_rich_seed-zovblhh2/flaky-test-prediction.md` |
| shipped | rich_seed | sonnet | 2 | ✓ | `/tmp/devrun-write_rich_seed-2_cyprja/flaky-test-prediction.md` |
| shipped | rich_seed | sonnet | 3 | ✓ | `/tmp/devrun-write_rich_seed-9sbl102k/flaky-test-prediction.md` |
| shipped | rich_seed | haiku | 1 | ✓ | `/tmp/devrun-write_rich_seed-xvfsblkf/flaky-test-prediction.md` |
| shipped | rich_seed | haiku | 2 | ✓ | `/tmp/devrun-write_rich_seed-0ll2aa07/flaky-test-prediction.md` |
| shipped | rich_seed | haiku | 3 | ✓ | `/tmp/devrun-write_rich_seed-y03gt7uy/flaky-test-prediction.md` |
