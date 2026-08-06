## Context

See proposal.md — Why. The change is prose in one `## Wrap-up` section plus the gate that holds it there. The design questions are therefore not about architecture but about where the sentence lives and what stops it from drifting away again, since drift is exactly how the gap opened: every sibling skill grew a forward pointer and import did not.

## Goals / Non-Goals

**Goals:**

- The student who arrived through import learns what closes the markers, in the same message that reports them.
- The pointer survives future edits to the skill without a reviewer having to remember it exists.

**Non-Goals:**

- Chaining. Import still ends after its report; naming a skill is not running it.
- Teaching the whole workflow. The workflow line at the top of every SKILL.md already lists the nine skills; the wrap-up answers "which one, for this gap" — not "what else exists".
- Changing what import produces. The file, the notes file, the strip list, and the check loop are untouched.

## Decisions

**Branch on the gap class, not a single pointer.** Import leaves three distinguishable kinds of hole, and they resolve in different skills. Prose the source left thin is the write skill's work. A reference shortfall is the literature-search skill's, and write explicitly refuses it — its own rule is that padding the list with placeholder entries ranks with inventing a publication. Missing research questions or a missing method are idea substance, which write refuses too and hands back to ideation. A single "run the write skill next" would therefore be wrong in two of the three cases, and wrong in the direction that wastes the student's time: they would run write, and write would tell them to go somewhere else.

Alternative considered: name only the write skill, on the grounds that it re-routes correctly anyway. Rejected because the re-route costs a full pass and reads as the tool contradicting itself.

**Pin the sentence rather than assert it in the eval.** `tests/unit/data/pinned_sentences/` already exists for load-bearing prose: a file per sentence, matched verbatim against its SKILL.md by `test_pinned_sentences.py`, which globs the directory and needs no code change to pick up a new pin. Rewording then requires editing the pinned copy in the same change, so the reword arrives as a paired diff. That is the enforcement this change needs, and it is free.

The alternative — extending `verdict_import` — does not work: it takes the produced proposal text and the check output, not the assistant's message, so a chat-only behavior is invisible to it. Reshaping the L1 task to score the transcript would be a harness change out of proportion to a three-sentence edit, and would put a metered model run behind a rule an offline string match already enforces.

**Wrap-up, not mandate.** The mandate is pinned in `tests/unit/data/skill_mandates/proposal-import.txt` and states what the skill does; the continuation pointer is about what happens after it is done. Putting it in the mandate would also drag it above the section that produces the report it belongs to.

## Risks / Trade-offs

- A pinned sentence is a verbatim match, so an unrelated typo fix in that paragraph fails L0 → intended: that failure is the review prompt, and the fix is one file edit.
- Three branches make the wrap-up longer, and a wordy closing message competes with the removal note and the per-reference validation report that already close an import → mitigated by stating the branch as one sentence with three clauses rather than three separate paragraphs, and by making it the last thing said, where a next step belongs.
