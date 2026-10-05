# Measurement

Measured on 2026-10-05.

**Setup**
- Host: Claude Code CLI 2.1.284. Models served: `claude-haiku-4-5-20251001` and `claude-sonnet-5-5`.
- Billing: every run was on the Claude subscription. No `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_USE_*` or `CLAUDE_CODE_OAUTH_TOKEN` was exported. No OpenRouter, Inspect or matrix call was made.
- Effort: the launching session exported `CLAUDE_EFFORT=xhigh`. The 2026-10-04 investigation session that produced the baseline ran at the same effort.
- Dev runs: `--isolated --keep`, with `--max-budget-usd 1` for haiku and `--max-budget-usd 2` for sonnet.

## Root cause (correcting `2026-10-04-scope-citation-attribution`)

That change's measurement attributed haiku × repair (0/3 on the dev runner) to "structural breakage, general skill non-adherence". **That attribution is wrong.**

Haiku never loaded `proposal-write` for the polishing request. No `Skill` call was made, the guidance was never read and `check.py` never ran. It edited the file from its own judgment, so none of the skill's rules could bind.

This was established on 2026-10-04 from the saved event streams of three repair runs and three seed runs. It is reproduced below with a same-day control. The cause is the description:
- `proposal-write`'s description named drafts, section improvements, prose from bullet points and review findings. It did not name a writing, editing or polishing pass.
- The request's "ready for my supervisor" is `proposal-review`'s trigger phrase.

## Dev runner, `write_repair_citations`

The primary metric is a `Skill` tool_use naming `proposal-write`, read from each kept `.devrun-events.jsonl` with jq.

| Arm | Run | Skill loaded | `check.py` calls | L1 | Cost (host-reported, quota) |
|---|---|---|---|---|---|
| haiku, original description (control) | 1 | no | 0 | FAIL: 9 repeated citations | $0.062 |
| haiku, original description (control) | 2 | no | 0 | FAIL: research-question list broken, 2 repeated citations | $0.068 |
| haiku, original description (control) | 3 | no | 0 | FAIL: four required sections missing (incl. methodology), 2 repeated citations | $0.095 |
| haiku, extended description | 1 | yes | 5 | PASS | $0.230 |
| haiku, extended description | 2 | yes | 6 | PASS | $0.225 |
| haiku, extended description | 3 | yes | 4 | PASS | $0.219 |
| sonnet, extended description (guard) | 1 | yes | 3 | PASS | $0.223 |

**What the runs show**
- **Control, original description.** It reproduces the 2026-10-04 baseline exactly: 0/3 skill loads, 0/3 L1. Each run makes one Read, then 5 to 12 Edits. Without it, a change since 2026-10-04 (host, model or harness) would be an equally good explanation of the result.
- **Extended description.** Skill loads went from 0/3 to 3/3. In every run, haiku reads the proposal, loads the skill, reads `guidelines.md` and iterates `check.py` until the result is clean. L1 went from 0/3 to 3/3.
- **Everything else held constant.** Both arms ran on the same day, under the same CLI version, from the same staging, and differ only in the description line. The control was run after the first edited arm, with the description reverted in place and `skills/` byte-identical to `main`.
- **Sonnet.** It loads the skill and passes, as it did 3/3 before.

## Routing rig

Ten cases: the eight existing write and review cases plus the two new ones. haiku at 3 epochs, sonnet at 1.

| Case | haiku before | haiku after | sonnet after |
|---|---|---|---|
| `write-canonical` | write, write, write | write, write, write | write |
| `write-oblique` | none ×3 | none ×3 | write |
| `write-collision` | none, none, write | none, write, none | write |
| `write-oblique-de` | none, write, none | none ×3 | write |
| `write-polish-collision` (new) | none ×3 | none ×3 | write |
| `review-canonical` | check ×3 | check ×3 | review |
| `review-oblique` | none ×3 | none ×3 | review |
| `review-collision` | none ×3 | none, none, check | review |
| `review-canonical-de` | none ×3 | review, none, none | review |
| `review-ready-collision` (new) | none ×3 | none ×3 | review |
| **total** | **5/30** | **5/30** | **10/10** |

**Haiku on the rig.** The total is unchanged, and the polish case stays 0/3. The guard case never reached `proposal-review` before or after the edit, but `proposal-write` never took it either.

A diagnostic epoch of the polish case with `--keep-events` (after the edit) shows what haiku does instead of loading a skill:
1. It calls Glob, then Read.
2. It plans the edits in text.
3. It calls `Edit` and `Write` (both withheld by the rig, so neither appears in its tool list).
4. It ends by listing its suggested changes.

**The rig and the dev runner disagree on haiku, and the difference is in the setup.**
- The rig installs all eleven skills and withholds the editing tools.
- The dev runner installs only `proposal-write` and offers the full tool set.

A student's install carries all eleven skills. The dev-runner result therefore shows that the description now reaches haiku when the write skill is the only one offered. It does not show that haiku picks it out of the full set. That question stays open (see below).

**Sonnet, full set at 1 epoch: 46/46** (regenerated `docs/skill-routing.md`).
- Both new cases route as intended.
- The previous report scored 119/120 on 40 cases at 3 epochs (2026-08-10, skills `b01246c`). It is marked as measured under different conditions, because the case set and the epoch count both changed. Case by case, every case that passed there passes here, and `ideate-collision`, its one miss (1 of 3 epochs), passes 1/1.
- The rig records the skills revision as `git rev-parse HEAD:skills`, which names the committed tree, not the working tree that was measured. The report's revision line was therefore changed by hand from `f3dfdee`, `main`'s tree, to `0ebcd57`, the tree this change commits. That tree is the content that was measured, with the extended description.

## Decision

The rule (proposal.md) has three conditions:
- **Haiku loads `proposal-write` on the polish request in at least 2 of 3 dev runs: met.** 3/3, against 0/3 for the same-day control.
- **No sonnet routing regression: met.** 46/46, and no case that passed before fails now.
- **The review guard still routes to `proposal-review`: met on sonnet (1/1).** On haiku the guard never routed to review, before or after. What the edit could have broken is a theft by `proposal-write`, and that did not happen (0/6).

**Outcome: the extended description is kept.** "polishing pass" is assigned to `proposal-write` in `tests/unit/data/trigger_terms.json`. No README model note is added: the trigger for that fallback was haiku still not loading the skill, and on the dev runner it now does.

## Cost

Host-reported, all on the subscription (plan quota, no money while extra usage stays off):

| Item | Cost |
|---|---|
| Dev runs: three haiku with the edit | $0.674 |
| Dev runs: three haiku controls | $0.225 |
| Dev runs: one sonnet | $0.223 |
| **Dev runs, total** | **$1.12** |

The routing rig prints no cost, because it kills each case at its first route. The one diagnostic epoch that ran to its end reported $0.062.

## Open

- **Haiku with the full skill set.** Whether haiku picks `proposal-write` for a polishing request when all eleven skills are installed is unmeasured outside the rig, and the rig says no (0/3). Measuring it needs a dev-runner scenario that installs the whole set. The runner does not offer one today.
- **Haiku's routing on the rig is weak in general**: 5/30 on the write and review cases, `review-canonical` stolen by `proposal-check` 6/6. This matches the 2026-10-03 finding (4/12 across six skills). It is a property of the weakest reader, not of this edit.
