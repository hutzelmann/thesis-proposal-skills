## Why

A student ran a whole proposal session — ideation, literature searches, drafting, supervisor-perspective reviews, revisions — and had to orchestrate it themselves. After a review they asked "What do we do now with that feedback? … But else?"; after a revision the assistant reported that no fresh review existed instead of recommending one, and the student had to request it; the session closed on a narrowed draft whose only review judged the previous scope, with no route from there to a supervisor-ready proposal. Some responses did suggest next steps, so the gap is not absence but inconsistency: every skill closes in its own words (ideate "the write skill turns it into a draft", write "point to the review skill", review "fixes are the write skill's job", check a one-line verdict, literature search a report, publish "offer check first"), nothing names a milestone, nothing says when exploration is enough, and no rule says that a review stops covering a text once the text changes in substance. The shared voice block's "with the next step when one exists" is the whole of the contract today.

## What Changes

- **A shared handoff block.** `shared/blocks/handoff.md` is materialized by `scripts/sync_shared.py` as the opening of a new closing section `## Handing over`, placed directly before `## When this run fails` in all eleven skills, with each skill's own exit condition and routes after it. The block carries:
  - **the milestone ladder**: seeded idea → complete draft → ready for supervisor discussion (no mechanical check errors, and a review of the current text with no blockers) → handed in (a built document or hand-in export, which the student sends). Execution readiness is not on the ladder: it is the clarify-early agenda the thesis settles in its first weeks;
  - **the format**: at a stopping point — a stage finished, a verdict given, or the user asking what now — its closing lines, nothing after them: `Where it stands:` (state and what blocks the next milestone), `Next:` (one recommended step, its reason, and a quoted phrase the user can send), and zero to two `Or:` lines. Labels in the chat language; never repeated when nothing changed;
  - **the rules**: the step is named as an action, never as a skill; nothing is done unasked — no finding applied, no choice invented, nothing built or published; a decision only the student can make is anchored in their own text, says what the choice changes, and offers at most three options their material supports plus a way out — never a bare open question; a review that judged an earlier version in substance is superseded and the step is a fresh review, never the report that none exists; on approval, the owning skill's instructions govern the step.
- **Per-skill exits and routes** (hand-written after the block):
  - `proposal-ideate`: after seeding, the next step is the full draft when grounding found the closest prior work, else a literature search first.
  - `proposal-lit-search`: broad search ends when the contribution delta and every research question have an accepted source behind them, or when a round adds no accepted entry; further searches only for a named gap. The reference count never keeps a search going.
  - `proposal-write`: a pass that changed research questions, scope, method, delta or a blocker's passage recommends a fresh review; a wording-only pass recommends the final check. Open `[TODO: …]` markers are sorted into decisions the student must make and execution details that pass the deferral record; the latter move to the notes file's Open Points only on approval.
  - `proposal-check`: owns the cold "where does my proposal stand / what next" — it places the proposal on the ladder from the check result, the review file and the notes file beside it, judging only whether the review still covers the text. It stays read-only. Its verdict line keeps scoping its claim and hands over instead of naming a skill.
  - `proposal-review`: needs revision → the blockers, refinements as an opt-in alternative, then a fresh review; ready → final check and hand-in; no viable thesis core → back to the idea.
  - `proposal-publish`: built → rename and send; supervisor feedback, once it arrives, becomes the next revision.
  - `proposal-import`, `proposal-reverse`: their closing pointer becomes the handoff — the step chosen by the gap left, named as an action.
  - `proposal-supervise`: the handoff goes to the professor in chat, never into the paste-ready feedback.
  - `proposal-customize`, `proposal-troubleshoot`: back to the step the user was on.
- **Description and trigger ownership**: `proposal-check`'s description gains the status moment; `tests/unit/data/trigger_terms.json` assigns it to check.
- **Harness**:
  - the dev runner gains scripted follow-up turns (`claude -p --resume <session>` in the same workspace and configuration);
  - `verdict_handoff()` in `harness/l1_checks.py` checks the format, with L0 tests, and every dev run reports it as an advisory `handoff` field;
  - five scenarios: review then "What do we do now with that feedback?"; a narrowed draft beside a review of the earlier scope; applying a review's blockers; a current ready review; a draft with open decisions and execution details. New fixtures back them;
  - a handoff rubric graded by the dev judge;
  - routing cases for the status moment and the canonical continuation phrases.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: "Cross-skill identical blocks materialized from one source" adds the handoff block; new requirement "Stage handoff at stopping points" (ladder, format, rules, placement before the report offer).
- `skill-check`: "Two-bucket honest reporting" — the verdict line hands over instead of naming the review skill; "Agent pass for non-mechanical issues" — an anticipated outcome phrased as an expectation is the guidance's required form, not a forbidden expected result (the first dev runs turned that false finding into a step before hand-in); new requirement "Proposal status on request".
- `skill-review`: new requirement "Review hands over a bounded revision path".
- `skill-write`: new requirement "Writing pass hands over"; superseded review, open-marker sorting, moves on approval.
- `skill-ideate`: "Seeds the proposal file" — the closing read-back ends in the handoff, with the post-seed route.
- `skill-lit-search`: new requirement "Search converges and hands over".
- `skill-publish`: new requirement "Build hands over to the student".
- `skill-import`: "Import names the continuation path" — the step is named as an action in the handoff, chosen by the gap class.
- `skill-reverse`: "Output bounded by its source, and reported as such" — the closing scenario hands over to a review instead of naming the review skill.
- `skill-supervise`: new requirement "Handoff stays in chat".
- `testing-harness`: new requirement "Handoff coverage" (follow-up turns, the verdict and its advisory probe, scenarios, rubric, routing cases).

## Impact

- **Shared source**: `shared/blocks/handoff.md` (new); `scripts/sync_shared.py` materializes it.
- **Skills**: all eleven `SKILL.md` bodies gain `## Handing over`; route prose in ideate, lit-search, write, check, review, publish, import, reverse, supervise, customize, troubleshoot; `proposal-check` description; existing closing pointers folded into the handoff.
- **Tests**: `tests/unit/test_skill_header_pattern.py` / `test_report_offer.py` (closing-section order), a new handoff-block test, `trigger_terms.json`, pinned sentences where a route is load-bearing, body-size limits re-checked.
- **Harness**: `harness/claude_runner.py` (follow-up turns, five scenarios, advisory probe), `harness/l1_checks.py` (`verdict_handoff` and scenario verdicts), `harness/rubrics/handoff.txt` with its golden prompt, `harness/l2_rubrics.py`, `harness/routing_cases.toml`, `harness/README.md`.
- **Fixtures**: four new synthetic fixtures with `expected.json` oracles; `tests/fixtures/README.md`.
- **Docs**: README "What the skills do", `AGENTS.md` (four materialized blocks).
- **Cost**: verification on the subscription only — dev runs with the dev judge and routing sweeps. No metered run; Inspect twins and matrix cells stay a separate, cost-gated decision.
