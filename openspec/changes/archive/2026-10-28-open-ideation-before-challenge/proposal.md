## Why

The first student field report (2026-10-28: a questionnaire plus the full Claude Code transcript of one Master's student who started without a defined topic, on Opus 5.5) names one experience as what almost stopped them: on their first two ideas, `proposal-ideate` asked questions they did not know how to answer and then started calling the idea weak. They only understood how the skill worked by the third idea. The maintainer has seen the same behaviour in their own sessions and judges it the most serious signal in the report: it is harsh at the moment a student is least equipped to answer, and it pushes students away from the skill before any of its value arrives.

The transcript shows where it comes from. Across the thirteen ideation turns before the method choice, every turn ended on a question, although the skill and its spec both say some turns end on an observation. Two turns asked the student to imagine a skeptical expert, a framing the skill's own example plants ("how would you convince a skeptic this worked?"). Three turns named a weak spot or a gap. Four presented literature as already close to the idea, the first in the student's second message. And several questions needed expert knowledge of experimental design that the student did not have yet, while the hard rule forbids offering anything to choose from. The questions the student answered easily and well were the experiential ones: the last time it happened at work, what the tool actually did.

The same transcript also shows the harsh questions working: the session's best catch, an outcome fixed by construction before any run, came from the student's answer to the hardest one, and the student rated the research question as their own (4 of 5). So the content of the questions is not the problem; their timing and framing are. Nothing measures either: `harness/rubrics/socratic.txt` grades only one failure direction (supplying content, uptake, one question per turn, praise), and every ideation persona is a student who holds content back — none is a willing student who lacks the knowledge an expert question assumes.

## What Changes

- **An opening phase before any challenge** (`skills/proposal-ideate/SKILL.md`, "The one hard rule", "Session arc", "Ground the idea in literature", "Scoping"). Until the problem holds the student's own specifics and the student has picked it, the skill asks experiential and curiosity questions only. It voices no weakness verdict and no imagined adversary. Literature found in this phase is presented as a field others work in, not as covering the idea, and a scope remark waits unless the idea sits clearly outside the given scope.
- **A one-line switch into the challenge phase**: once the trigger holds, the skill says that it now tests the idea the way a supervisor would and that "I don't know yet" stays a fine answer. Tests from then on are framed collaboratively — what would convince the student, the part to sharpen next — never as a weak spot or an imagined skeptic. The Master's push for the gap and the "what's your angle beyond this paper" move live here.
- **A ladder for "I don't know"**: the skill answers it with the conventional kinds of answer (how such things are usually shown, asked, observed or measured), never with a harder question and never with content for the student's problem. The hard rule stays unchanged. An "I don't know" counts toward the existing impasse only once the offered kinds also went unused.
- **A question rhythm**: no more than three consecutive turns end on a question; the observation-only turn the spec already requires gets a frequency.
- **One program-requirements question at the seeding bookend**: whether the study program requires anything specific of the thesis — a built artifact, a page limit, a required method — and, on yes, a pointer to recording it in the workspace guidance. The field report's "I have to build something" surfaced only after the PDF was built.
- **The skill's own examples** that model the harsh framing (the skeptic question, the gap push without timing) are rewritten to the collaborative form.
- **Harness**: `socratic.txt` gains timing and tone criteria, so both failure directions are graded in every ideation dialogue task; a new subscription dev-runner scenario replays a synthetic novice — workplace experience, short non-native English, a vague problem, thin answers to expert questions — through scripted follow-ups and is graded by that rubric over the transcript. A reactive novice persona for the metered matrix is recorded as a later, cost-gated step and is not part of this change.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-ideate`: new requirements for the opening phase, the announced challenge phase with collaborative framing, the "I don't know" ladder, the question rhythm, and the program-requirements question at seeding; the early-stop requirement's stalled-session scenario counts an "I don't know" only after the ladder.
- `testing-harness`: a new requirement for the rubric's timing and tone criteria, and one for the synthetic novice dev scenario.

## Impact

- `skills/proposal-ideate/SKILL.md` (hard-rule examples, session arc, literature grounding, scoping, seeding); new pinned sentences under `tests/unit/data/pinned_sentences/proposal-ideate--*.txt`. The mandate and the shared blocks are untouched.
- `harness/rubrics/socratic.txt`, `harness/l2_rubrics.py` (criterion and dev-rubric entry for the new scenario), `harness/claude_runner.py` (the scenario), `harness/README.md`, the generated `skills/proposal-ideate/evals/evals.json` projection, `tests/unit/`.
- The rubric change alters what the metered ideation tasks measure: shipped matrix verdicts for those tasks were graded against the old criteria. Re-running them is a cost-gated decision outside this change.
- No script, frontmatter, guideline, methodology default or workspace key changes. Subscription dev runs only; no metered run.

Changelog: The ideation skill opens with questions about your own experience and holds back critical tests until you have picked a problem, says when it switches to testing the idea, answers "I don't know" with the usual ways such a question is answered, and asks at the end whether your program requires anything specific.
