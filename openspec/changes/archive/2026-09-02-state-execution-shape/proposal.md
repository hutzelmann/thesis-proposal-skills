# State the execution shape

## Why

A real `proposal-supervise` run on 2026-09-02 under a host mode that orchestrates every task as a multi-agent workflow (Claude Code's ultracode) cost roughly 8.3M tokens against 0.4–0.6M for the same task run in one context, and hit the session limit. The host applied its stock review template — one finder per dimension, one skeptic per finder, one fact-checker — to the nine bullets of review's "What to assess" (the five substance tests plus eight dimensions: 13 finders, 13 skeptics, 1 fact-checker), and every helper re-read the proposal, the whole `guidelines.md` and the source PDF. No shipped script was involved. The skills say nothing about how they expect to be executed, so a per-item list reads as an invitation to fan out, and the host's standing default fills the silence — the same failure class as `2026-08-31-fix-import-output-location` (a location silence filled by the host's scratchpad rule) and `2026-07-31-resolvable-script-paths`.

What the fan-out loses is not per-item context (each finder read the whole proposal) but the joint judgement the skills require: the verdict cites the failing tests together, findings are ordered by severity across all of them, a research question is non-overlapping only relative to the others, and supervise's tier decision needs at least three of five tests failing decisively with a per-test reason. Beyond review and supervise, `proposal-write` is the sibling where a fan-out would mutate rather than merely cost: one helper per section or per review finding means parallel edits to one file, against the surgical-edit rule and the `(RQn)` cross-references.

## What Changes

- `proposal-review`, `proposal-supervise`, `proposal-check`, `proposal-write` each gain an `## Execution shape` section as their first section: the task is single-context, one pass by one agent; helper agents are not part of the skill; if the host insists on a workflow, review and supervise cap it at three agents (one full review, one adversarial check of the review's fail verdicts, one optional reading of the proposal's own references block for citation consistency — no network, which neither skill declares) and never one agent per test, per dimension, or per research question; check is one script run plus one reading by the same agent (including the Python-missing fallback); write is one writer per file. Following a sibling skill's instructions in the same context is explicitly not a helper.
- Review and supervise state a compact contract for any helper the host spawns anyway: the main agent is the only writer and `<slug>-review.md` carries every finding regardless; a helper works from `<slug>.md` (never the submission) with the resolved workspace `guidelines.md` override and only the guideline sections its task needs; it returns a verdict per substance test (decisive fail / uncertain / pass, one quotable finding per failed test — the shape supervise's tier decision consumes), then at most five findings with severity, location, one-sentence problem, one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged; no reasoning prose, no strengths list, no restated guidelines unless the user asks for full reasoning. Title, sentence-level density and exceeded-limit findings keep their fuller required shape and stay with the main agent; supervise's "What to keep" block stays with the main agent.
- Each section's opening (heading plus first sentence naming the shape and, for review and supervise, the three-agent cap) is pinned under `tests/unit/data/pinned_sentences/`, so a rewrite cannot drop it silently. No new test file: `test_pinned_sentences.py` globs the directory.
- `proposal-troubleshoot` rung 5 names the cost case: a run that cost many times the usual and produced correct output is the host's effort or workflow mode fanning the task out, a non-defect with the host's budget controls as the remedy. README "When something goes wrong" carries the same one-line pointer. `harness/README.md` Known limitations records that no harness path can observe a fan-out.

Out of scope, stated so the commit can say it: the host's thinking budget is a harness setting the skills cannot influence, and a standing workflow opt-in may override skill text — this change is a mitigation to be measured on the next real supervise run under that mode, not a guarantee. Tracked follow-ups, not folded in: the same silence in `proposal-reverse`, `proposal-import` and `proposal-lit-search` (per-chapter, per-section, per-candidate shapes; a sibling sweep as its own change, as `2026-09-01-fix-sibling-fallback-relocation` did), and a dev-runner cost probe (the stream-json result event already carries `total_cost_usd` and `num_turns`, and `harness/routing.py` already parses `tool_use` events).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-review`: add a single-context execution requirement — one pass by one agent, helper cap of three with fixed roles, a findings contract and context diet for helpers, the main agent as the only writer.
- `skill-supervise`: add the same requirement in supervise's terms — helpers work from the normalized file, their per-test return feeds the tier decision without making it, strengths and every finding stay with the main agent.
- `skill-check`: add a single-agent execution requirement — one script run, one reading by the same agent, nothing delegated per category.
- `skill-write`: add a one-writer-per-file requirement — sections drafted and review findings applied in sequence by one agent, never parallel helpers editing one file.
- `skill-troubleshoot`: extend the non-defect causes — a cost blowup with correct output under a host fan-out mode lands on the dissatisfaction rung as correct behavior, with the host's budget controls named as the remedy.

## Impact

- `skills/proposal-review/SKILL.md`, `skills/proposal-supervise/SKILL.md`, `skills/proposal-check/SKILL.md`, `skills/proposal-write/SKILL.md` (new first `##` section each; header region untouched, so mandates and successor pins are unchanged)
- `skills/proposal-troubleshoot/SKILL.md` (one sentence in rung 5; mandate untouched)
- `tests/unit/data/pinned_sentences/proposal-{review,supervise,check,write}--execution-shape.txt` (new pins)
- `README.md` ("When something goes wrong"), `harness/README.md` (Known limitations)
- Spec deltas for the five capabilities above. No script, harness, fixture, or `shared/` changes; no frontmatter change, so routing and the `evals.json` projections are unaffected. Body sizes stay far inside the 500-line and 2×-median caps.
