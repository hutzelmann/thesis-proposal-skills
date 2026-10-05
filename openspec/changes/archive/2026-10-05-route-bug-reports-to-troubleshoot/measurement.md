# Measurement

Measured 2026-10-05 on `main` at a4e1b68 plus this change's working tree.

The implementation started on fefeced. Before any run, `main` moved to a4e1b68 (`desktop-first-install` merged, `close-claudeai-surfaces`), and the branch was fast-forwarded. Two consequences:

- `troubleshoot_model_rung`'s reinstall sentence now names the install prompt instead of `npx skills add`, so `troubleshoot-report-collision` follows it.
- Every run below is measured with the account's synced claude.ai skills and connectors closed. The 138/138 report was not.

## Setup

- Host: Claude Code CLI 2.1.284.
- Instrument: the routing rig (`uv run poe routing`). All eleven skills are installed without `evals/` under an isolated `CLAUDE_CONFIG_DIR`, with the pinned claude.ai opt-out settings. Only `Skill`, `Read` and `Glob` are reachable.
- Billing and effort: the rig's children start from `routing.isolated_env`. That allowlist admits no `ANTHROPIC_*` variable, no `CLAUDE_CODE_USE_*` switch and no `CLAUDE_EFFORT`, so every run is on the subscription at the host's default effort. No `~/.config/anthropic` profile directory exists and no `CLAUDE_CODE_OAUTH_TOKEN` is exported, so the F8 refusal does not apply and the run uses the linked stored login.
- No OpenRouter, Inspect, matrix or dev-runner call was made.

## Run 1: haiku, description as on `main` (control)

Run log `logs/routing/20261005-234338.json`: 15 cases × 3 epochs = 45 measurements, 0 errors, 19/45 correct. An earlier attempt passed a literal `--` (the old README form), and argparse refused it before any model call.

**Stream checks: pass.** The kept streams cover the last epoch of each case (15 of them):
- `init.apiKeySource` was `none` in all 15, and `init.model` was `claude-haiku-4-5-20251001`.
- All 15 `rate_limit_event`s had status `allowed` and `isUsingOverage: false`.
- The highest seven-day utilisation was 0.19.

| Case | Routes (3 epochs) | Correct |
|---|---|---|
| `troubleshoot-canonical` | none, none, none | 0/3 |
| `troubleshoot-oblique` | none, none, none | 0/3 |
| `troubleshoot-collision` | none, none, none | 0/3 |
| `troubleshoot-report-collision` (new) | none, none, none | 0/3 |
| `troubleshoot-report-oblique` (new) | none, none, none | 0/3 |
| `review-canonical` | check, check, review | 1/3 |
| `review-oblique` | none, none, none | 0/3 |
| `review-collision` | none, none, review | 1/3 |
| `review-canonical-de` | review, review, review | 3/3 |
| `review-ready-collision` | review, review, review | 3/3 |
| `write-canonical` | write, write, write | 3/3 |
| `write-oblique` | none, write, write | 2/3 |
| `write-collision` | write, none, write | 2/3 |
| `write-oblique-de` | none, write, none | 1/3 |
| `write-polish-collision` | write, write, write | 3/3 |

Totals:
- primary (the two new cases): **0/6**;
- secondary (the three existing troubleshoot cases): **0/9**;
- guard: 19/30 correct, and no measurement selected `proposal-troubleshoot`.

**What haiku does on the troubleshoot cases.** On all three it opens with a clarifying reply, the same behaviour 6.1 recorded: no tool call, one turn, and a request for the traceback, the details, or what happened. The kept streams for the two new cases and `troubleshoot-canonical` show this. The host's notional cost was about $0.016 per unrouted measurement, which is not billed.

## Run 2: haiku, edited description

Run log `logs/routing/20261005-234728.json`. Same 15 cases and command as run 1, run against the 425-character description from proposal.md: 45 measurements, 0 errors, 19/45 correct. Streams are kept in `logs/routing/run2-edited/`; run 1's are in `logs/routing/run1-control/`.

**Stream checks: pass.**
- `init.apiKeySource` was `none` in all 15 streams, and `init.model` was `claude-haiku-4-5-20251001`.
- 13 of the 15 streams carry a `rate_limit_event`. All are `allowed` with `isUsingOverage: false`, and the highest seven-day utilisation is 0.19.

| Case | Run 1 (control) | Run 2 (edited) |
|---|---|---|
| `troubleshoot-canonical` | none ×3 | none ×3 |
| `troubleshoot-oblique` | none ×3 | none ×3 |
| `troubleshoot-collision` | none ×3 | none ×3 |
| `troubleshoot-report-collision` (new) | none ×3 | none ×3 |
| `troubleshoot-report-oblique` (new) | none ×3 | none ×3 |
| `review-canonical` | check, check, review | check ×3 |
| `review-oblique` | none ×3 | review, none, review |
| `review-collision` | none, none, review | none, review, none |
| `review-canonical-de` | review ×3 | review ×3 |
| `review-ready-collision` | review ×3 | review ×3 |
| `write-canonical` | write ×3 | write ×3 |
| `write-oblique` | none, write, write | write, none, none |
| `write-collision` | write, none, write | write ×3 |
| `write-oblique-de` | none, write, none | none ×3 |
| `write-polish-collision` | write ×3 | write ×3 |

Haiku's answers to the two new cases are again clarifying questions, given in one turn without a tool call.

## Decision (design.md D3)

| Measure | Control | Edited | Condition | Met |
|---|---|---|---|---|
| Primary (two new cases) | 0/6 | 0/6 | edited ≥ 4/6 and ≥ control + 3 | no |
| Secondary (three existing troubleshoot cases) | 0/9 | 0/9 | edited ≥ control − 1 | yes |
| Theft guard, haiku (review and write) | 0/30 select troubleshoot | 0/30 select troubleshoot | none | yes |
| Errors | 0 | 0 | — | — |

**Outcome 4: the description lever does not move haiku.**
- Haiku loaded `proposal-troubleshoot` in none of 30 measurements, under either description. That includes `troubleshoot-canonical`, a crashed script with a traceback, the one case the original description already covers word for word.
- There was no theft, so outcome 3's revision does not apply.
- The guard's correct count is 19/30 in both arms. The case-by-case moves cancel out, in the range of the rig's epoch-to-epoch noise.
- On the rig, haiku answers a question about a misbehaving skill without loading a skill. How the description words the situation makes no difference.

The description is therefore reverted to `main`'s bytes, and haiku's registry note records the limitation (tasks 6.2 and 6.3).

## Run 4: sonnet, final state (original description)

Run log `logs/routing/20261005-234820.json`, streams in `logs/routing/run4-sonnet/`. Under outcome 4 the change ships no description edit, so there is nothing to scan for theft. Run 4 therefore covers only the five troubleshoot cases, at 1 epoch: 4/5 correct, 0 errors.

**Stream checks: pass.** `apiKeySource` was `none` in 5 of 5 streams, `init.model` was `claude-sonnet-5-5`, and the one `rate_limit_event` was `allowed` with no overage.

| Case | Route |
|---|---|
| `troubleshoot-canonical` | troubleshoot |
| `troubleshoot-oblique` | troubleshoot |
| `troubleshoot-collision` | troubleshoot |
| `troubleshoot-report-collision` (new) | troubleshoot |
| `troubleshoot-report-oblique` (new, first wording) | none |

**The miss was a dataset defect, not a routing one.** Sonnet answered the oblique case by saying it had no earlier context from the session, so it could not see what had happened. Haiku said the same in runs 1 and 2. The first wording ("This is the second time the tool did the opposite of what I asked. …") points at a past event that a fresh `claude -p` session cannot see, so a clarifying question is the correct answer.

This is the same trap as the 2026-08-10 staging lesson: correct behaviour scored as a routing failure. The case was rewritten to carry its own context: "I asked the proposal assistant to leave my research questions exactly as they are, and it rewrote them anyway — twice now. Is that a bug I should report?"

## Run 5 (sonnet) and the run 3 slot (haiku): the reworded oblique case

Outcome 3's revision did not apply, so its run-3 slot measured haiku on the reworded case. The run count stays at five. Both runs used 3 epochs and the original description.

| Run | Log | Routes | Stream checks |
|---|---|---|---|
| 5, sonnet | `20261005-234918.json` | troubleshoot ×3 | `apiKeySource` none; **no `rate_limit_event`** in the kept stream |
| 3, haiku | `20261005-234927.json` | none ×3 | `apiKeySource` none; `allowed`, no overage |

**Run 5 is untested under D4.**
- The rig keeps only the last epoch's stream per case, and that stream was killed at its route before a rate-limit event arrived.
- `apiKeySource` was `none`, and the isolated environment admits no billing variable, so a billed call is not plausible. Still, the check that D4 fixes in advance is not met.
- Run 5's routes are therefore reported as observed, not as a verdict. They are not repeated.

Haiku's answer to the reworded case, after one turn and with no tool call, starts "Yes, that sounds like it's worth reporting." It agrees it is a bug and still does not load the skill.

**Totals over all five runs:**
- Haiku loaded `proposal-troubleshoot` in **0 of 33** troubleshoot measurements: 15 with the shipped description, 15 with the widened one, and 3 on the reworded case.
- Sonnet routed every self-contained troubleshoot case: 4/4 in run 4 plus 3/3 observed in run 5.

## Registry note (task 6.3)

The haiku entry in `harness/models.toml` now carries a second clause after the polish note:

> questions about a misbehaving skill or a bug to report are answered without loading proposal-troubleshoot (0/33 on the routing rig, 2026-10-05) — invoke it by name (/proposal-troubleshoot in Claude Code) or use sonnet or opus

The README row was regenerated with `uv run poe report --log-dir <main checkout>/logs/evals`, which read 10 logs, the newest from 2026-08-10. The README diff is the haiku row only, and `docs/model-support.md` and `shared/model-support.json` are byte-identical.

The remedy differs from design D5's draft ("name the skill in the request"). Naming it in prose would itself be a routing decision, which haiku is shown here not to make. The slash command invokes the skill without routing, and sonnet is measured to route these questions.

## Cost

Everything ran on the subscription (plan quota). Nothing is billed while extra usage stays off, and the rate-limit events report `overageStatus: rejected`.

- The rig prints no cost, because it kills each case at its first route.
- The kept streams of unrouted haiku cases report about $0.016 to $0.018 notional each.
- For scale: 33 unrouted haiku troubleshoot measurements come to roughly $0.55 notional, and the routed measurements stop sooner.
- Seven-day utilisation stayed at 0.19 throughout.

## Correction to the archived record

`2026-10-05-fix-troubleshoot-model-match/design.md` (Risks, Open Questions) names the D1 read-only lookup mode in `collect.py` as the follow-up if haiku misapplies rung 1. Task 6.1 of that change shows haiku never reached rung 1: it answered without loading the skill. Runs 1 to 3 here show the same on the student's install, under two descriptions.

A lookup mode runs inside the skill, so it cannot help. **That follow-up is superseded.** The fallback is the model note above. The archive is edit-denied by `.claude/settings.json`, so the correction is recorded here.

## Open items

- **The two new cases are not in `docs/skill-routing.md` yet.** They enter it at the next 3-epoch sonnet sweep (design.md D6). That sweep is also the first report measured with the account surfaces closed.
- **Polish note against the closed surfaces.**
  - `write-polish-collision` routed to `proposal-write` 6/6 on haiku here (runs 1 and 2), with the account's synced claude.ai skills closed. The polish note records 0/3, measured with them present.
  - A student logged in with a claude.ai account likely has the same synced skills, so the note is not plainly stale. Which of the two conditions a student's install matches decides whether it is.
  - This change leaves that clause untouched.
- **The D4 rate-limit check versus the rig's kept streams.** The rig keeps one stream per case (the last epoch), and a quickly routed stream can end before any rate-limit event. That makes "at least one `rate_limit_event`" unreliable for short sonnet runs (run 5). Keeping every epoch's stream, or checking the event in the rig itself, would close the gap.
- **Haiku outside the rig.** Whether haiku with the full set loads the skill when editing tools are reachable stays unmeasured, as for `route-polish-to-write`.

**Side finding: closing the account surfaces moved haiku's guard routing.** `route-polish-to-write` measured 5/30 on the write and review cases on the same host, with the synced claude.ai skills present. Here the same cases score 19/30 with those surfaces closed, and `write-polish-collision` goes from 0/3 to 3/3. The synced `docs` skill, which calls itself the default for any document, was one of the competitors present then.
