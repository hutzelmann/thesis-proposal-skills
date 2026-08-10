## Why

The routing baseline recorded in `docs/skill-routing.md` (sonnet, 60 measurements, 2026-08-10) puts a number on a surface that had never been measured: **51/60**. Every one of the nine failures is a skill that *never fired* — not one that stole another's utterance. `proposal-lit-search` lost four of its five non-canonical measurements; `proposal-ideate` lost its contested phrasing in all three epochs; `proposal-import` and `proposal-publish` each lost one. Asked "Is my idea already published somewhere?", the agent answered from general knowledge. Asked "I want to figure out whether my idea is worth pursuing — talk it through with me", it replied "Sure — what's the idea?" and started an unstructured conversation the skills exist to replace.

The descriptions are therefore too narrow, not too greedy: they name the vocabulary we use for a task rather than the vocabulary a student uses to ask for it.

That said, greed is real too and simply went unmeasured on this model. `proposal-check` and `proposal-review` both claim the supervisor-handoff moment verbatim, and the 2026-08-10 haiku probe routed "is it ready for my supervisor?" to `check`. Four skills claim the word "supervisor" today. A weaker or differently-tuned selector will hit that collision even though sonnet did not.

Both failures are edits to the same twelve lines of always-loaded metadata, and neither has any gate: nothing in the repository reads a skill's frontmatter today.

## What Changes

- Rewrite the `description` of every skill whose trigger surface the baseline found wanting, so each names the situations a user is actually in, in the words they would use — including the German-language cues the intended population types.
- Resolve the measured collisions by pointing rather than tying: the skill that does not own a contested moment says so and names the one that does, and vocabulary it does not own is dropped from its trigger clause.
- Add an owned-trigger table: high-signal terms are assigned to exactly one skill, with an explicit list of terms that are legitimately shared. Editing the boundary means editing the table in the same commit.
- Add a frontmatter contract enforced by L0: name matches its directory, description within budget, third person, states both what the skill does and when to use it, no unknown frontmatter keys.
- Add size guards: the 500-line body cap from Anthropic's skill-authoring guidance, a proportion guard so no skill's body may exceed twice the suite median, and a total metadata budget covering the always-loaded cost of all ten descriptions.
- Re-run the routing sweep and record the after-matrix, so the effect of the rewrite is measured rather than asserted.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `skill-packaging`: adds the frontmatter/trigger contract — descriptions as a cross-skill boundary with exactly one owner per contested term, plus body and metadata size limits.
- `testing-harness`: the routing report gains a recorded baseline it is compared against, so a regression in trigger coverage is visible as a drop rather than as an absolute number.

## Impact

- Modified: the `description` line of the affected `skills/*/SKILL.md` files; `docs/skill-routing.md` (re-measured).
- New: `tests/unit/data/trigger_terms.json`, `tests/unit/test_skill_frontmatter.py`.
- Descriptions are published surface — they render on each skill's skills.sh page — so this changes what a visitor reads, not only what a selector matches.
- No skill body, script, or reference file changes; no behavioural change once a skill has been selected.
