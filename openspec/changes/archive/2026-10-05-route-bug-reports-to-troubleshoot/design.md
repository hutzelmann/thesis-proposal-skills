# Design

## Context

See proposal.md, Why. The current state and the constraints, on `main` at a4e1b68:

- **The routing rig** (`harness/routing.py`, `uv run poe routing`):
  - It installs all eleven skills, without `evals/`, into a temp workspace under an isolated `CLAUDE_CONFIG_DIR`.
  - Only `Skill`, `Read` and `Glob` are reachable.
  - The verdict is the first `proposal-*` Skill invocation, and the run is killed there.
  - A case that makes more than three preparatory calls, or ends without a Skill call, is unrouted. A case still running at its time limit with no route recorded is an error.
- **The rig's child environment is an allowlist** (`routing.isolated_env`, from `isolate-child-environment`). No `ANTHROPIC_*` or `CLAUDE_CODE_USE_*` variable reaches `claude -p`, so the launching shell cannot route a run to per-token billing. `CLAUDE_EFFORT` is not admitted either, so rig children run at the host's default effort.
- **The 6.1 setup matches neither instrument.** It loaded the ambient user configuration: 53 skills, three SessionStart hooks, four plugins. That is not a student's install, and it is not reproducible.
- **Haiku on the rig is a weak router in general.** It scored 5/30 on the write and review cases on 2026-10-05, and `proposal-check` took `review-canonical` 6/6. On the polish case, its description edit moved two instruments differently:
  - the dev runner (one skill installed), 0/3 → 3/3;
  - the rig (full set), 0/3 → 0/3 (`route-polish-to-write/measurement.md`).
- **Account surfaces are closed** (`close-claudeai-surfaces`, a4e1b68). The isolated configuration pins opt-out settings. A case whose stream shows a synced claude.ai skill, connector or plugin is recorded as an error, and synced content found after a sweep voids the whole sweep.
- **The routing report** (`docs/skill-routing.md`) is a sonnet sweep of 46 cases × 3 epochs: 138/138, skills `f410b5b`, recorded in fefeced. It predates the surface closure, so it was measured with the account's synced skills present, among them `docs`, which describes itself as the default for any document. Comparisons against it carry that caveat.
- **Description limits** (`tests/unit/test_skill_frontmatter.py`):
  - 500 characters per description;
  - 4500 for all names plus descriptions together, which stand at 4338 on `main`;
  - owned trigger phrases are lowercase substrings that only their owner may contain.
- **Rule A** (`tests/unit/test_model_ids.py`): `harness/*.toml` files other than the registry carry no model ID at all.
- **The README model-support table is generated.** `harness/report.py` appends a registry `note` to a model's row, so a hand edit is overwritten by the next `poe report`. Haiku's entry already carries the polish-routing note.

## Goals / Non-Goals

**Goals**
- Find out whether the description is what keeps haiku from loading `proposal-troubleshoot` for an "is this a bug I should report?" question on a student's install, and fix it there if it is.
- If it is not, put the limitation where a haiku user reads model guidance.

**Non-Goals**
- No change to the skill body, the ladder, rung 1's matching rule, or `collect.py`. A skill that is never loaded runs none of them.
- No dev-runner scenario, and no re-run of the 6.1 ambient setup (D2).
- Rung 1's behaviour after loading is not checked. The archived change's L0 tests remain the coverage for the matching rule.
- No German troubleshoot case. The dataset has none today, and no description in the suite carries German trigger words. That gap is suite-wide, not this change's.

## Decisions

### D1: The lever is the description

The host selects a skill from the frontmatter alone. Haiku made no Skill call in 6.1, so it read nothing past the frontmatter.

- *Rejected: the D1 read-only lookup mode from the archived change.* It runs inside the skill, so it needs the same load that failed. The archived design's follow-up is superseded, and `measurement.md` records why, because the archive cannot be edited.
- *Rejected: reordering the description trigger-first.* It was measured for `proposal-supervise` and moved haiku from 0/12 to 0/12.
- *Chosen wording.* The edit widens only the trigger clause, with the situations a user names: crashed, ignored the user's instructions, flagged something plainly there, and the bug-report question itself.
  - "a skill misbehaved" stays verbatim, so its row in the owned-trigger table holds.
  - "Not when the proposal needs improving" shortens to "Not for improving the proposal", which keeps the decline at a lower cost.

### D2: The instrument is the routing rig

The rig is the student's install: all eleven skills, nothing ambient, and the description as the only input to selection. The question is whether haiku selects the skill, and that is exactly what the rig measures. The withheld editing tools do not matter, because the request is a question, not an edit.

- *Rejected: the dev runner.* It installs only the skill under test and its declared siblings, so it answers a different question: does haiku load the skill when it is the only one offered? The polish precedent showed the two instruments disagree on haiku, and a student has the full set.
- *Rejected: repeating the 6.1 call.* The ambient configuration measures the operator's machine.

### D3: Decision rule

Each haiku run measures the five troubleshoot cases plus every `review-*` and `write-*` case (the guard), at 3 epochs per case. That is 15 cases and 45 measurements. The control runs on the same day, under the same CLI version and with the same staging, with the description as on `main`.

| Measure | Cases | Per arm | Condition for keeping the edit |
|---|---|---|---|
| Primary | `troubleshoot-report-collision`, `troubleshoot-report-oblique` (haiku) | 6 | edited ≥ 4/6, and edited ≥ control + 3 |
| Secondary | the three existing troubleshoot cases (haiku) | 9 | edited ≥ control − 1 |
| Theft guard, haiku | every `review-*` and `write-*` measurement | 30 | none selects `proposal-troubleshoot` |
| Theft guard, sonnet | every case not expecting `proposal-troubleshoot`, final state, 1 epoch | 43 | none selects `proposal-troubleshoot`; no other regression (below) |

**Why these thresholds.** They are judgment:
- four of six is a majority of the primary measurements;
- a lead of three over the control cannot come from one epoch flipping;
- a drop of one on the secondary is the coin-flip tolerance the rig's own history shows (`litsearch-oblique`, 2026-08-10).

**Errors are counted against the edit.** An errored measurement, such as a timeout, counts as routed in the control arm and as missed in the edited arm, and it is listed. If more than a third of a run's measurements error, the run is untested.

**Sonnet regressions.** Any other miss on sonnet is re-measured once at 3 epochs. A case that passed in the 138/138 report and misses at least 2 of 3 is a regression.

Outcomes:

1. **Control primary ≥ 4/6.** Haiku already routes the question on a student's install. The description is not the gap, and the 6.1 miss belongs to the ambient configuration. Make no edit and add no note. Record it.
2. **All conditions met.** Keep the edit, and add "a bug they should report" to the owned-trigger table.
3. **Theft on the haiku guard.** Allow one revision that narrows the clause which stole, measured as one more haiku run. If it still steals, or fails the primary, go to 4.
4. **Primary or secondary not met, or the sonnet guard fails.** Revert the description to `main`'s bytes. The new cases stay. Haiku's registry `note` gets the finding, and `poe report` regenerates the README row.

### D4: Run budget and billing checks

At most five rig runs, all on the subscription:

1. haiku control, `--no-report --keep-events`;
2. haiku edited, the same flags;
3. haiku revised, only under outcome 3;
4. sonnet on the final state, `--epochs 1 --no-report --keep-events` (D6). Under outcome 2 it covers the full set, as the theft scan. Under outcomes 1 and 4 the description is `main`'s and there is nothing to scan, so it covers only the five troubleshoot cases, for the new cases' sonnet routes;
5. sonnet re-measurement of non-theft misses only, `--epochs 3 --no-report`.

`isolated_env` already closes the billing routes through the environment. Each run's kept event streams (`logs/routing/events-<case>.jsonl`) still have to pass the dev runner's D5 checks 3 and 4, as a confirmation that costs nothing:

- `init.apiKeySource` is `none`;
- at least one `rate_limit_event` exists across the kept streams, and none carries `isUsingOverage: true`;
- no `rate_limit_event` has a status outside `allowed` and `allowed_warning`.

A run that fails a check is recorded as untested and is not repeated.

### D5: The fallback note goes into the registry

Under outcome 4, the haiku entry in `harness/models.toml` gets the finding in its `note`, joined to the existing polish note with `; `. A TOML comment above it cites `measurement.md`.

The note names its instrument and date, so a reader does not mistake it for a matrix cell. It states a remedy that needs no routing decision from haiku:
- invoke the skill by name, with `/proposal-troubleshoot` in Claude Code;
- or use sonnet or opus.

The draft remedy, "name the skill in the request", was dropped during implementation, because naming the skill in prose still leaves haiku to decide whether to load it (measurement.md, Registry note). The README row is regenerated with `uv run poe report --log-dir <main checkout>/logs/evals`, which reads the logs behind the shipped table. Only the haiku row may change.

### D6: The routing report is not regenerated

`docs/skill-routing.md` holds a 3-epoch sweep over 46 cases, 138/138, recorded today. A 1-epoch run of the full set would replace it with a coarser one. A 3-epoch run (144 measurements) would spend about three times the quota of the scan the decision needs.

Run 4 is therefore a theft scan with `--no-report`. Its per-case routes, including the two new cases on sonnet, go into `measurement.md`. The new cases enter the report at the next 3-epoch sweep, and `harness/README.md`'s case count (48) says the dataset already holds them.

- *Rejected: `--render` from the run-4 log.* The render path writes neither the epoch count nor the superseded score, so it would label a 1-epoch run as 3 epochs.

## Risks / Trade-offs

- [Haiku's general weakness on the rig hides any description effect] → The control runs on the same day, and the primary needs a margin over it. If haiku does not move, that is outcome 4, which is what the fallback exists for.
- [The new description fits the one new sentence, not the situation] → The oblique case names no skill, and the three existing cases have to hold (secondary). The wording names situations, not that sentence's words.
- [The widened clause takes requests meant for other skills] → The haiku guard covers review and write. The sonnet scan covers every skill.
  - "ignored the user's instructions" is the riskiest clause against `write-collision` ("feedback that my methodology section is too vague"), so outcome 3 narrows that clause first.
  - "flagged something plainly there" is the riskiest against `proposal-check`, which the sonnet scan covers.
- [The report lags the dataset by two cases] → `measurement.md` carries their sonnet routes until the next sweep (D6).
- [The metadata budget ends near its ceiling: 4472 of 4500] → 28 characters remain. The next description that grows has to trim something first, and the combined-metadata test enforces that.
- [Weekly plan quota is near its limit: 0.85 seven-day utilisation in 6.1's rate-limit event] → Runs are bounded (D4), each case is killed at its first route, and a non-allowed rate-limit status stops the measurement as untested.

## Open Questions

- Whether haiku with the full set loads `proposal-troubleshoot` outside the rig, with editing tools reachable. `route-polish-to-write` leaves the same question open, and the dev runner has no whole-set scenario.
- Whether `verdict_troubleshoot_model_rung` should also require that the answer names the recorded failure. Carried over unchanged from the archived change.
