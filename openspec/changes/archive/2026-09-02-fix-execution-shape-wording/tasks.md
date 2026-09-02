## 1. Sections

- [x] 1.1 `proposal-review`: cap "three agents including you: you are the full review, plus at most one adversarial check … and one optional reading …"; "a helper writes no file: you are the only writer"; "verdict per substance test it examined"; "Its return carries no reasoning prose …"; drop the sibling clause.
- [x] 1.2 `proposal-supervise`: same cap wording; "against the evidence bar below" instead of the number; "a helper writes no file: you are the only writer of `<slug>.md`, its notes file, …"; "it examined"; "Its return carries …"; keep the sibling clause.
- [x] 1.3 `proposal-check`: "the script runs once — a second time only for the digest comparison the read-only mandate requires of a non-interactive run — and the agent pass below …".
- [x] 1.4 `proposal-write`: "One writer per file:"; drop the sibling clause.
- [x] 1.5 `proposal-lit-search`: "the scripts — or, when script networking is denied, your own read-only requests — gather the candidates".
- [x] 1.6 `proposal-reverse`: "the reading, the harvest record and the proposal are all yours in this one context" — no restatement of what is read.

## 2. Pins, docs, instructions

- [x] 2.1 Rewrite the six pins to the new sections.
- [x] 2.2 `proposal-troubleshoot` rung 5: "where it states one"; "budget and effort controls". `README.md`: "The skills whose runs can fan out state the shape …".
- [x] 2.3 `AGENTS.md` "Skill header pattern": one paragraph on the execution-shape convention (which skills, where, pin, test, how coverage extends, origin).

## 3. Verify

- [x] 3.1 `uv run poe test` green (execution-shape equality and position, pinned sentences, header pattern).
- [x] 3.2 `openspec validate --all --strict` passes.
