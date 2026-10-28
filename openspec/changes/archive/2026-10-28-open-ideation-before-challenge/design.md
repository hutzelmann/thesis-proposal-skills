## Context

See proposal.md — Why. The relevant current state:

- `skills/proposal-ideate/SKILL.md` has no notion of phases. "Session arc" aims every move at the emptiest consequential aspect from the first exchange on, "Scoping" asks Master's sessions to "push gently for the gap" with no timing, and "Ground the idea in literature" hands the skill the line "this 2024 paper does almost exactly that — what's your angle beyond it?" as its model move. The hard rule's own example list opens with "how would you convince a skeptic this worked?".
- The spec already requires observation-only turns ("some turns SHALL be observations"), but gives them no frequency, so a transcript in which every turn asks a question does not visibly break it.
- The early stop counts "I don't know" as a non-contribution outright (skill-ideate, Coverage-guided convergence and early stop).
- `harness/rubrics/socratic.txt` is the one template every ideation dialogue task is judged against (`ideate_l2_socratic` in `harness/skill_evals.py`); per-task criteria in `harness/l2_rubrics.py` only narrow it. The dev runner can grade a conversation (`transcript()` in `harness/claude_runner.py`, used by the handoff scenarios), but its `DevCriterion` takes the judge's question from the visible request or a fixture's `semantic` list — not from the transcript.

## Goals / Non-Goals

**Goals:**

- The opening of an ideation session is answerable by a student who has experience but no research vocabulary yet.
- Rigor stays: every test the skill asks today is still asked, later and framed differently.
- Both failure directions — harshness and ghostwriting — are graded by the same rubric, so a fix for one cannot quietly buy the other.

**Non-Goals:**

- Loosening the hard rule. Topics, research questions and the method choice for the student's problem still originate with the student.
- Changing the shared voice block. The opening phase is about what is asked and when, not about warmth; it adds no praise.
- A chat language other than the one the student writes in. The report's student wrote in English as a second language, but nothing showed that a different chat language would have helped; that stays a hypothesis.
- Metered runs. The reactive persona and any re-grade of shipped matrix verdicts are separate, cost-gated decisions.

## Decisions

**D1 — The switch is triggered by progress, not by turn count or permission.** The challenge phase starts once the problem holds the student's own specifics and the student has picked it — the "problem" aspect of the existing five-aspect tracker, plus a choice the student made. A turn count is simpler to test but arbitrary: it coddles a student who arrives with a ready idea and challenges one without it too early. Asking permission ("shall I start testing the idea?") hands the student a decision they cannot yet judge and puts a question first in the phase that is meant to carry fewer. The one-line announcement keeps the switch transparent without asking anything. A student on the prepared-student fast path has picked a problem on arrival, so the switch comes with the first reply.

**D2 — The opening phase defers framing, not information.** Literature is still checked early: knowing early that others work on the problem is useful. What changes is the frame — "a field others are working in" rather than "close to what you describe, so what's your angle". A clearly out-of-scope idea still gets its single warning early, because waiting would waste the student's time; only the in-doubt scope remark waits, which the scoping requirement already says should pass without comment.

**D3 — The ladder offers kinds of answer, which are conventions.** "People usually show this by asking people, watching them, or testing it" names method families, not a method for the student's problem; the skill's existing "conventions yes, content never" line already permits stating such rules once the student's thinking has surfaced the need, and an "I don't know" to an evidence question is that need surfacing. The skill still chooses none of them for the student. An alternative — offering example answers drawn from similar theses — was rejected: that is content, and it would trade away the ownership the report's student valued.

**D4 — The early stop counts "I don't know" after the ladder.** Otherwise the ladder and the impasse rule contradict each other: three honest "I don't know"s would end the session before the ladder ever ran. The stonewalling persona still reaches the impasse, one ladder step later per exchange; its criterion (impasse named after about three contentless exchanges) still holds, since a declined ladder is a contentless exchange.

**D5 — The rhythm is a number: no more than three question-ending turns in a row.** The spec's "some turns" gave the model no way to tell it was failing, and the report's transcript had none in thirteen. Three is generous enough not to stall convergence and small enough for a judge to check.

**D6 — Timing and tone go into `socratic.txt`, not into one task's criterion.** Every ideation dialogue should meet them, and putting them in the shared template means the existing persona tasks start measuring both directions at once — a skill that becomes gentle by supplying content fails the old criteria in the same judgment. The novice scenario adds its own narrowing criterion on top, as the other tasks do.

**D7 — The dev runner grades the novice replay over the transcript.** `DevCriterion` gains a third question source, the transcript itself, filled from the existing `transcript()` function; the rubric's answer slot carries the seed when one was written and "(no file created)" otherwise, as the matrix scorer does. The scenario stages nothing, declines lookups (so it needs no fixture server and is deterministic about grounding), and its follow-ups are fixed: they do not react, which is acceptable because the harshness the report describes sits in the first four or five turns, and those are graded regardless of what the skill says.

**D8 — The novice is synthetic and differently topical.** Fixtures and scenario text are synthetic by rule; the novice's topic is unrelated to the report's, and none of its sentences come from the transcript. What it keeps is the shape: an experienced practitioner, short imperfect English, a vague complaint from work, one concrete incident when asked, and an honest "I don't know" to an evidence question.

**D9 — Measured before and after on the subscription.** The novice scenario runs against the current skill first (expected: fails the new criterion), then after the skill edit (expected: passes), on sonnet; once on opus after the edit, since the report's student ran opus. The existing ideation dev scenarios rerun after the edit as a regression check. All runs use the dev runner with `--judge`; no metered call.

**D10 — The announcing reply carries no test.** It was added during implementation, after two sonnet runs (see Measurements). With the announcement tied to "before the first test", a model that asked no test announced nothing. Once it was tied to the trigger instead, a model went straight from the announcement into a test, and the run had no observation turn at all. A reply that announces and then ends on an observation does three things. It satisfies the spec's "announces the switch in one line before its first test". It gives the session a guaranteed observation turn at the point where it changes mode. And it lets the student register the switch before the first hard question arrives.

## Risks / Trade-offs

- [The model stretches "the problem holds the student's own specifics" and switches after one concrete sentence] → the trigger also requires the student's pick, and the novice criterion grades that no test precedes the announcement.
- [The opening phase drags for a student with a sharp idea] → the prepared-student fast path picks the problem on arrival; for everyone else the switch comes as soon as their own words carry a concrete problem.
- [Softer framing loses the catches the hard questions produced] → the tests themselves are unchanged and still required; only their position and wording move. The before/after runs read the challenge-phase turns for whether the substantive tests still appear.
- [The rubric change makes shipped ideation matrix verdicts stale] → recorded in the proposal's Impact and in `harness/README.md`; a re-run is a cost-gated decision the maintainer takes separately.
- [A fixed-follow-up replay cannot show whether a student would stay] → accepted for this change; the reactive persona that drops an idea after repeated verdicts is the later, metered measure.

## Measurements

All runs: dev runner, `--isolated --judge`, Claude host on the subscription, harness login; dev-runner L2, not comparable to the matrix. Notional cost is the host's reported figure, not a charge.

**Before (task 2.1), unchanged skill, 2026-10-28.** `uv run poe dev ideate_novice --isolated --judge --keep --model sonnet --summary-log logs/devrun/ideate-novice-before-sonnet.jsonl`. Served `claude-sonnet-5-5`, CLI 2.1.312; judge `claude-sonnet-5-5` at medium effort. L1 PASS (session saved in `driver-knowledge/notes.md`, no seed, family-only). L2 `ideate_novice_l2` FAIL: the judge names the skeptic framing, the missing announcement and the weakness verdicts, each enough on its own, and the turn after "I don't know" asking for research-design knowledge. Six conversation turns, 17 host turns, 68 s, notional $0.238 for the run and $0.027 for the judge. The patterns, read from the kept stream:

- Imagined adversary: reproduced. The turn after "I don't know" states the closed methodology set, then asks the student to imagine a skeptic saying "Prove it" and to name what would make the claim hard to dismiss.
- Harder question after "I don't know": reproduced in the same turn. No kinds of answer were offered.
- Weakness framing in the opening phase: reproduced, mildly. "Right now 'drivers don't follow it' says that it happens, but not what happens", and the swap test ("this could still be about any company with experienced workers") one turn after the student picked a direction.
- No announcement: reproduced. The student's pick ("this part interests me more") was followed by the swap test, not by any switch.
- Unbroken questions: every Socratic turn carried a question; none was an observation alone.
- Prior work framed as covering the idea: not exercised, because the scenario declines lookups.

Instrument note, not a model finding: the transcript the judge read carried every text each turn showed (`shown_turn_texts()`); the judge's stored reason is the summary's tail only. Side observation, outside this change: every dialogue turn closed with the `Where it stands:` / `Next:` / `Or:` lines, although the skill says the dialogue itself has no stopping points.

**Before, re-graded under the final rubric.** The rubric gained two clauses after the before-run: the program-requirements question is part of the closing bookend, and the swap test is a Socratic move, not a weakness verdict. `uv run poe dev ideate_novice --rejudge /tmp/devrun-ideate_novice-7i103m2_` re-graded the kept stream at $0. Still FAIL, for the missing announcement, the skeptic in the opening phase and the harder question after "I don't know". The judge also counted each turn's `Next:` and `Or:` lines against the one-question limit.

**After (task 4.1), first skill edit.**

- *sonnet* (`ideate-novice-after-sonnet.jsonl`): served `claude-sonnet-5-5`, CLI 2.1.312. L1 PASS, L2 FAIL. Six conversation turns, 17 host turns, 53 s, notional $0.178 for the run and $0.022 for the judge. Every opening question was experiential: the last time it happened, one occurrence, how the office found out. No verdict, skeptic or handoff lines appeared mid-dialogue. The turn after the student's pick was an observation alone. The turn after "I don't know" named four kinds of answer (asking, watching, looking at records, trying a change) and asked which was closest to what the student had seen. The judge failed it on one point: no announcement after the pick. The model asked no test at all, and the skill text then read "say so in one line before the first test", which ties the line to a test rather than to the trigger the spec names. That wording was the fault. It was fixed once to "your next reply says so in one line, whether or not it tests anything yet", with what counts as one occurrence and as a pick.
- *opus* (`ideate-novice-after-opus.jsonl`): served `claude-opus-5-5`, CLI 2.1.312. L1 PASS, L2 PASS. Six conversation turns, 22 host turns, 78 s, notional $0.423 for the run and $0.035 for the judge. The questions stayed experiential through the incident. The reply to the pick announced the switch ("From now on I will test the idea the way a supervisor would. When you can't answer a question yet, that's normal."), then ended on an observation. The "I don't know" turn offered three kinds of answer and chose none. Both models still opened two replies with mild approval ("That's a good place to start"), which the voice block already forbids; the judge did not count it.

**After, second skill edit** (`ideate-novice-after2-sonnet.jsonl`): sonnet, served `claude-sonnet-5-5`, CLI 2.1.312. L1 PASS, L2 FAIL. Six conversation turns, 19 host turns, 56 s, notional $0.229 for the run and $0.029 for the judge. The announcement now came in the reply to the pick ("Now you have picked a direction, so from here I'll test the idea the way a supervisor would. Not having an answer yet is fine."), and the "I don't know" turn offered four kinds of answer and chose none. The judge failed it on the rhythm: all five Socratic turns ended on a question, including the announcing reply, which went straight into a test. Turns two and three also stacked two questions each. Sonnet stacked questions in the before-run too, so that part predates this change. A third and last wording edit followed. The announcing reply ends on an observation, with the first test in the turn after. The rhythm rule became a check made before ending any turn on a question.

**After, final skill text** (`ideate-novice-after3-sonnet.jsonl`): sonnet, served `claude-sonnet-5-5`, CLI 2.1.312. L1 PASS, L2 PASS. Six conversation turns, 15 host turns, 46 s, notional $0.163 for the run and $0.027 for the judge. The opening was experiential throughout: the last time it happened, one specific occurrence, which part stays with the student. The reply to the pick announced the switch in one line ("You have chosen your problem, so from now on I will test the idea the way a supervisor would. Not knowing an answer yet is fine.") and ended on an observation mirroring the student's shift. The "I don't know" turn offered four kinds of answer and chose none. At most two turns in a row ended on a question. The substantive tests are not visible here, because the scripted student stops one turn after the switch; the regression runs below cover the rest of the skill. The sonnet tally on the novice criterion across the three edits is 0/1, 0/1 and 1/1: one run per wording, not a pass rate.

*opus, final text* (`ideate-novice-after3-opus.jsonl`): served `claude-opus-5-5`, CLI 2.1.312. L1 PASS, L2 PASS. Notional $0.403 for the run and $0.037 for the judge. The reply to the pick announced the switch and ended on an observation that reframed the student's example. The "I don't know" turn offered three kinds of answer.

**Regression (task 4.2), sonnet, final text up to D10.**

| Scenario | L1 | Explanation | Notional |
|---|---|---|---|
| `ideate_from_scratch` | PASS | seeded after `idea/` → provisional → final slug | $0.163 |
| `ideate_scoped` | PASS | seed complete, scoping honored, no leaks | $0.169 |
| `ideate_scoped_adjacent` | PASS | seed complete, no scoping bleed | $0.222 |
| `ideate_paper_foundation` | FAIL | "chat asks more than one question in its turn" | $0.111 |

The paper path's last recorded sonnet run (2026-10-06) also failed on a second question, and the wording fixed then was never re-run. So the original skill (develop `cec14a5`) was run as a control from a detached worktree: L1 PASS, one question, $0.109. The failing run had asked the axis question and then added "And what about this paper made you want to follow it?", a curiosity question of the new opening phase. That is a regression of this change, not noise the control would share. The fix states that the opening phase's kinds of question come one per turn and never as extra ones: where an entry path fixes a turn's question, as the paper path's axis question, that question stays the turn's only one.

After the fix, the paper path was run three times on each arm, alternating, sonnet, CLI 2.1.312, about $0.10–0.11 notional each. The original skill passed 2 of 3 and the changed skill passed 2 of 3. The one failure on each side had the same shape: the axis question asked, the kinds of change listed, then the question re-asked behind a second question mark ("Which of these is closest to what you have in mind?"). That is the shape the 2026-10-06 change recorded before its wording fix. It is sonnet flakiness this change neither causes nor cures, and it stays recorded as such. The curiosity-question shape the fix addressed did not recur. Three runs per arm can show a large difference, not a small one.

**Final text, confirming run** (`ideate-novice-final-sonnet.jsonl`): `ideate_novice` on sonnet after the one-per-turn fix, served `claude-sonnet-5-5`, CLI 2.1.312. L1 PASS, L2 PASS. Six conversation turns, 17 host turns, 53 s, notional $0.180 for the run and $0.029 for the judge. Opus was not re-run after that last sentence, which only restricts extra questions. Its final-text result is the D10 run above.
