## Context

See proposal.md — Why. The measurement that motivates this change is `docs/skill-routing.md`; the rig that produced it is `harness/routing.py`, archived as `2026-08-10-skill-routing-rig`.

What the baseline actually shows, per skill: `proposal-lit-search` 1/5, `proposal-ideate` 3/6, `proposal-import` 4/5, `proposal-publish` 5/6, everything else clean on sonnet. All nine failures are `none` — the selector chose no skill at all. The one measured *theft* comes from the earlier ambient haiku probe (a review request answered by `proposal-check`), which this change also fixes, on the evidence of the descriptions rather than of a sweep.

Nothing in the repository reads frontmatter today, so both the rewrite and its guard are new surface.

## Goals / Non-Goals

**Goals:**

- Make the trigger clauses describe the user's situation, in the user's words, including German.
- Give every contested term exactly one owner, recorded where a reviewer will see it move.
- Guard the always-loaded metadata cost and body proportion, so this surface cannot rot silently.
- Re-measure, and state the movement.

**Non-Goals:**

- Rewriting bodies, mandates, or the four-block header pattern. `tests/unit/test_skill_header_pattern.py` and the pinned mandates stay untouched; only the `description` line moves.
- Chasing 60/60. Some utterances are genuinely ambiguous, and a description that catches everything catches other packages' work too — the negatives exist to price that.
- Tuning until haiku is satisfied (see Risks).

## Decisions

**Fix narrowness first, greed second, in the same edit.** They are the same twelve lines. The narrowness fix is additive (more situations named); the greed fix is subtractive plus a pointer. Doing them apart would mean two rewrites of one sentence and two sweeps to interpret.

**Named skills in descriptions, not just negated vocabulary.** Alternative considered: drop the contested word and stay silent about the neighbour. Rejected — a student asking about the supervisor moment then gets nothing, which is exactly the failure the baseline is full of. The pointer costs ~45 characters and turns a silent miss into a hand-off.

**Owned-trigger table as data, seeded from the measured collisions.** `tests/unit/data/trigger_terms.json`: `{"owned": {"<term>": "<skill>"}, "shared": ["<term>", …]}`. Alternatives: a similarity threshold between descriptions (rejected — an arbitrary constant that flags boilerplate long before it flags "supervisor"), or no table at all and reliance on the sweep (rejected — the sweep is subscription-gated and local, so a collision introduced in a commit reaches `main` unchallenged). The escape hatch matters: without an explicit `shared` list the first legitimate overlap turns the test into noise a future reader disables.

**Checks live in `tests/unit/test_skill_frontmatter.py`**, parsing frontmatter with the same narrow extraction the repo already uses rather than a YAML parser — user-side constraints do not apply to tests, but a general parser here would invite general frontmatter, and the contract is that frontmatter stays two keys.

**Constants, and where each comes from.** 500-line body cap: Anthropic's skill-authoring guidance, cited. Description budget 500 characters: below the format's 1024, above the worst case after the rewrite. Metadata total 4500 characters: the always-loaded cost, currently 3471 with headroom for the pointers. Proportion guard at 2× the suite median: the only number with no external source, chosen because it is self-adjusting as the suite grows — recorded as judgment in a comment beside the current ratios (median 1330 words, largest `proposal-ideate` at 2348, i.e. 88% of the ceiling).

**Third person by exclusion.** A description may not contain first- or second-person pronouns; "the user", "their", "a student" are the register. Cheap, and it catches the drift the official guidance warns about without trying to parse register.

**Re-measure on sonnet, same flags as the baseline.** Comparing against a differently-configured run would confuse a description improvement with a configuration change. The report states the superseded score.

## Risks / Trade-offs

- **Over-fitting to one model.** A description tuned until sonnet always fires may simply be verbose. Mitigation: the edits are justified by the *user's* vocabulary being absent, not by a model's behaviour; the after-sweep confirms, it does not drive.
- **Broader triggers steal work from other packages.** Mitigation: the four negative cases are exactly this alarm, and they pass today — they must still pass after.
- **Metadata grows toward the budget.** Ten pointers at ~45 characters is ~450, taking 3471 to roughly 3900 against a 4500 ceiling. Mitigation: the budget is a test, so the next addition has to argue for itself.
- **Descriptions are published text.** They render on skills.sh, so a trigger clause written purely for a selector reads badly to a human visitor. Mitigation: the header-pattern rule that the purpose block never restates a rule stays in force, and the descriptions stay sentences rather than keyword lists.
- **The owned-term table drifts from the descriptions it guards.** Mitigation: the check reads both, so the failure surfaces on the next run rather than at review time.
- **Re-measuring costs a subscription sweep (~7 minutes, 60 measurements).** Accepted; it is the only evidence the change worked.

## Migration Plan

Descriptions are read at selection time from the installed copy, so users who already installed a skill keep the old trigger until they update. Rolling release, no migration step. Reverting is a revert of the description lines; the tests and table revert with them.
