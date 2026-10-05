# Design

## Context

`test_counts_agree_with_the_set` scans the guidance, every `SKILL.md`, the pinned sentences and (when no change is in flight) the main specs with `_COUNT`, then compares any number word it captures to the size of the set parsed from the guidance. `_COUNT` requires `substance` or `named` between the number and `tests`. The source sentence puts the qualifier after the verb ("Five tests define the substance bar"), so the pattern never saw it.

The sites also contain plain mentions of a number of tests that are not claims about the set, the one that matters being the testing-harness spec's "Naming those three tests is a statement about this fixture, not about how many tests exist" — the very sentence written to say it is not a count of the set.

## Goals / Non-Goals

**Goals:** the source's own count sentence is guarded; the existing exclusions (evidence bars after `at least` / `only`, number words that are not counts) keep holding.

**Non-Goals:** recognising digits ("6 tests"), German number words, or count sentences in the README. No site uses those today, and the README is not a guarded site. The README's enumeration names the swap test "anti-generic"; that is a name drift outside a guarded site, not a count, and stays out of this change.

## Decisions

**A second branch keyed on the clause, not a bare `<N> tests`.** The pattern gains an alternative: a number word, then `tests`, then — within the same clause (no `.`, `;` or `:` in between, at most 40 characters) — the word `substance`. That reads "Five tests define the substance bar" as a set claim and leaves "those three tests is a statement about this fixture" alone.

- *Alternative: match every `<number word> tests`.* Rejected — it flags the fixture sentence above and any future "two tests" in a spec about something else, which would turn the guard into something to route around.
- *Alternative: list the verbs (`define`, `make up`, `form`).* Rejected — it guards only the wording that happened to drift, and the next rewording ("Six tests set the substance bar") would slip past it again. Tying the match to the subject of the sentence — the substance bar — survives a change of verb.

**Pattern behaviour is pinned by a table-driven test** over literal phrasings (positive and negative), so a later edit that narrows the pattern fails offline rather than silently re-opening the hole.

**Proof against the real file.** Beyond the table, the widened guard is shown to fail on the guidance with "Five" restored and to pass with "Six" — recorded as evidence in `tasks.md`.

## Risks / Trade-offs

- [A future count sentence names the set without the word "substance" in the same clause] → the existing `substance tests` / `named tests` branch still covers the usual phrasing; the table test makes adding another branch a one-line, reviewable change.
