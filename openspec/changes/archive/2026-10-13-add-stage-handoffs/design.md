## Context

See proposal.md (Why) for the session that motivated this. The relevant current state:

- Every `SKILL.md` ends with its own closing pointer, and the only shared statement is the voice block's "with the next step when one exists". Three shared regions are materialized today by `scripts/sync_shared.py`: the workflow line and voice block (located by position among the opening blocks) and the report offer (the first paragraph after `## When this run fails`, absent from `proposal-troubleshoot`).
- `proportionate-readiness-review` (archived 2026-10-13) gave the review three finding classes, deferral records, a stopping rule and converging rounds, and routed clarify-early items to the notes file. This change builds on those classes; it does not alter the review file.
- The dev runner (`harness/claude_runner.py`) runs one headless `claude -p` per scenario and judges `final_text(events)`. The host supports `--resume <session-id>` in print mode, and the session id is in the stream's `init` event.
- The routing rig measures, from descriptions alone, which skill a first-turn utterance selects (`harness/routing_cases.toml`).

## Goals / Non-Goals

**Goals:**
- One handoff contract, written once, read by every skill at the moment it closes.
- A handoff a model can be tested on deterministically (format) and by a judge (judgement).
- Continuation without skill names: the user approves or sends a phrase, and the host's own routing finds the skill.

**Non-Goals:**
- No orchestrator skill and no automatic chaining: a handoff recommends, the user decides.
- No change to the review file's shape, the workflow line, or the order of the student path.
- No machine state for "where it stands" (no status file, no digests): the state is read from the proposal, the review file and the notes file each time.
- No Inspect twins or matrix cells in this change; the scenarios run on the subscription dev runner.
- The supervise feedback letter keeps its own wording rules, including its plain-word skill names; the handoff rule binds the chat.

## Decisions

### D1 — A closing block, materialized like the report offer

`shared/blocks/handoff.md` becomes the opening of a `## Handing over` section that every skill carries directly before `## When this run fails` (last in `proposal-troubleshoot`, which has no such section). `sync_shared.py` locates the region as the first *N* paragraphs after the heading, so a multi-paragraph block stays one region and the skill's own route paragraphs follow it untouched. *N* is pinned (`HANDOFF_PARAGRAPHS`), not read from the source: the region in a `SKILL.md` is the block as last materialized, and a source that grew a paragraph would otherwise swallow every skill's first route paragraph — the adversarial review showed a two-paragraph growth consuming ideate's `## When this run fails` heading. A source whose count differs is refused, and so is a span that would cross a heading; changing the count is a migration of the source, the constant and the eleven sections in one commit. The header-pattern tests gain the section's position; a new test pins block identity and position.

*Alternatives:* extending the voice block (header real estate on skills.sh, and AGENTS.md defines voice as conduct without operational rules); a `guidelines.md` section (students read it as proposal guidance, and skills do not read the whole file at their close); per-skill prose only (the status quo, which drifted).

### D2 — The ladder, and why execution readiness is off it

Seeded idea → complete draft → ready for supervisor discussion → handed in. "Ready for supervisor discussion" is the conjunction of the two judgements the skills already make — mechanically valid (no check errors) and a review of the current text with no blockers — so it adds no new criterion. Execution readiness is named explicitly as *not* a milestone, because the session that motivated this change kept growing the proposal toward a protocol; the clarify-early agenda is where those items live.

### D3 — Labelled lines, checkable by L1

`Where it stands:`, `Next:`, up to two `Or:` (German `Stand:`, `Als Nächstes:`, `Oder:`), closing the message. Labels make the contract checkable without a judge: `verdict_handoff()` parses the closing lines and asserts exactly one `Where it stands` and one `Next`, at most two alternatives, none empty, no other text after them, no skill identifier or skill named as one, and a length cap. Alternatives may be `Or:` lines or a list under one empty `Or:` label — sonnet's first runs chose the list, and the contract is about how many alternatives, not how they wrap. Whether the recommendation is *right* stays with the L2 rubric. The scenario verdicts check the step itself in the first sentence of `Next:`, as its object — "a fresh review", not "the review on file still applies" — with no negation just before it, and require a quoted continuation phrase where a sendable step exists; the generic verdict does not, because some steps are the user's own (sending the PDF).

*Alternative:* free prose judged only by L2 — more natural, but every regression would cost a judge call to see.

### D4 — Actions, not skills

The handoff names the step ("a fresh review of the narrowed draft"), never `proposal-review` or "the review skill". The phrase the user can send is worded in the vocabulary of the owning skill's description, and the routing rig measures each canonical phrase. Agent-facing prose keeps naming skills: on approval the owning skill's instructions govern the step, so a "yes" after a review does not get applied under the review skill's rules. The report offer keeps its fixed wording, which names `proposal-troubleshoot` by design. Mid-run pointers elsewhere in the bodies are not rewritten; the requirements that define a closing pointer (check, import, reverse, ideate) are.

### D5 — Cold status belongs to the check

"Where does my proposal stand / what now" in a fresh session routes to `proposal-check`: read-only, cheap, and already the mechanical half of the milestone. The status read adds two files beside the proposal — the review file and the notes file — and one judgement: does the review still cover the text (D6)? It renders no substance verdict and writes nothing. The description gains the moment and `trigger_terms.json` assigns it.

*Alternatives:* review (a status question would trigger a full review and overwrite the review file); a twelfth skill (touches every eleven-skill invariant for a read-only probe).

### D6 — A superseded review is a judgement on fixed anchors

A review covers the text it judged. It is superseded when the research questions, the scope, the method or the contribution delta differ, or when a passage one of its blockers cites was changed. The writing skill states it at the end of its own pass, because it knows what it changed; any other skill compares the anchors when it finds `<slug>-review.md`. The consequence is always the same recommendation — a fresh review, which reads the earlier round and converges — never "there is no review".

*Alternatives:* a digest stamped into the review (every typo fix flips it, so judgement is still needed, and review would gain a script for one line); file modification times (rewritten by checkouts and copies).

### D7 — Bounded revision, conditional recheck

After a needs-revision review the recommended step is the blockers; refinements are one `Or:`. An explicit "apply the review" keeps its meaning from the readiness change (blockers and refinements, clarify-early to the notes). A fresh review is recommended exactly when the pass changed a blocker's passage or substance (D6 anchors); a wording-only pass goes to the final check. A decision only the student can make — RQ2 needs a criterion that can fail — is put as an anchored choice: the student's own text quoted, what the choice changes, at most three options their material supports, and a way out.

### D8 — Sorting open markers by the deferral record

The readiness change's deferral record decides which `[TODO: …]` markers can wait: one whose record can be filled is an execution detail and may move to Open Points as a clarify-early item; one whose record cannot is a decision the student owes the proposal. Moving is an edit, so it happens in a writing pass and only on approval; the check, which owns cold status, only proposes it. Markers are never deleted to quiet the check — the write skill's existing rule.

### D9 — Exploration exits on claims, not counts

Literature search stops broad searching when the contribution delta and every research question have an accepted source behind them, or when a round adds no accepted entry; after that, searches only for a named gap. Ideation's exit is unchanged (five aspects concrete → seed); its handoff picks draft or search by whether grounding found the closest prior work. The reference count stays the check's business, consistent with ideate's existing no-count rule and lit-search's claim-backed merge rule.

### D10 — Follow-up turns via `--resume`

A scenario may list `followups`: after the first run, each is sent with `claude -p <text> --resume <session-id>` in the same workspace, under the same isolated configuration (whose session store persists for the scenario's lifetime) and the same budget cap, which the host applies to the running total. Events are concatenated and saved as today; `turn_texts(events)` returns every result text in order, the verdicts read the last one, and the judge reads the whole transcript (user turns and final texts). Billing and surface checks run per turn, so a follow-up cannot escape them. A turn that reports another session than the one it resumed is a runner failure. In a resumed print-mode turn `total_cost_usd` and `modelUsage` are the session's running totals while `usage`, `num_turns` and `duration_ms` are per turn (recorded 2026-10-13), so the summary takes the last cost and sums the rest, and `--max-budget-usd` caps the session.

*Alternatives:* Inspect persona dialogues (metered, and the scripted lines need no persona); single-turn scenarios with staged state only (cannot reproduce "what now?" right after the skill's own review — the incident's exact shape).

### D11 — The format probe on every dev run is advisory

`verdict_handoff` on the final chat is reported as `handoff` in every dev summary, like `single_context`, and never changes the exit status. It measures every stage for free without moving a shipped verdict: existing scenarios and their Inspect twins keep their meaning. The dedicated handoff scenarios assert it.

### D12 — Rubric over the transcript

`harness/rubrics/handoff.txt` grades the chat transcript against the fixture's `semantic` list, which states what the right step is and why (for a two-turn scenario on f05, the oracle comes from the scenario rather than f05's own `expected.json`, whose list describes the review). Criteria: the stand is accurate; the recommended step is the one that unblocks the next milestone and its reason is stated; a superseded review is recognised and a fresh review recommended; a decision step is anchored with options from the student's material and a way out; nothing was done unasked; no repeated checklist.

### D13 — Fixtures reuse calibrated text

- `w10-narrowed-scope`: a narrowed proposal beside a review of its broader predecessor and a notes file recording the narrowing.
- `w11-blocker-revision`: f29's text beside a needs-revision review whose blocker the request's information resolves.
- `w12-ready-current`: f28's text beside a current ready review.
- `f30-open-markers`: a complete draft with two decision markers and three execution-detail markers.

Each carries an `expected.json` oracle calibrated against `check.py`. Built from f28/f29 where possible, so their check behaviour is already known.

## Risks / Trade-offs

- [Every body grows by the block] → the block is about 300 words — the first runs showed the shorter wording left skill names and missing handoffs unaddressed; the body-size tests (published cap, twice the median) run in `poe test`, and the median grows with every body alike.
- [Fixed labels feel mechanical in long conversations] → only at stopping points, never repeated when nothing changed; one position line, one step, at most two alternatives; the rubric fails a repeated checklist.
- [A follow-up "what now?" may make the agent start the revision unasked] → the scenario verdict fails any change to the proposal; this is exactly the user-control property under test.
- [Routing of continuation phrases differs by model] → canonical phrases measured on sonnet in a full sweep and on haiku for the new cases; a phrase that misroutes is reworded in the skill's route prose, not forced by the description.
- [The status read makes the check judge review staleness, a content question] → bounded to the D6 anchors, stated as information, never a verdict; the check stays read-only and keeps its scoped verdict line.
- [`--resume` behaviour changes across host versions] → the summary records `cli_version`; a missing `session_id` in `init` is a runner failure, never a silent single-turn pass.

## Migration Plan

No data migration. Users receive the block with the next install or plugin update; a workspace with an existing review file is handled by D6 on first contact. Rollback is reverting the change's commit and re-running `scripts/sync_shared.py`.
