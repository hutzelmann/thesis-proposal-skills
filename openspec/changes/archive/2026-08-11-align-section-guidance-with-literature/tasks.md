## 1. Introduction and contribution guidance

- [x] 1.1 In the Proposal Structure list of `shared/guidelines/guidelines.md`, sharpen the introduction item: the section closes with an explicit one-to-two-sentence purpose statement of what the thesis tries to achieve, and the existing "refer to the thesis only at the end" wording becomes that requirement rather than a permission.
- [x] 1.2 Extend the contribution item's closing-gap guidance: the close also states why answering the questions matters once answered (significance, distinct from the delta) and names the kind of deliverable (technique, model, tool or prototype, evaluation of an instance, report of findings), with a clause that typing the deliverable is not an expected-results section.

## 2. Construction goals

- [x] 2.1 In the Research Questions section, extend the goal-versus-question paragraph with the structured goal form: context improved, artifact built, requirements satisfied, stakeholder goal served.
- [x] 2.2 Add the derivation link: where the contribution is an artifact, the research questions interrogate the stated goal (effects against requirements, comparison to alternatives, conditions under which results hold) rather than standing beside it.
- [x] 2.3 Add the reviewer-facing generality nuance: "how can X be done" is legitimate when the answer is a generalizing method; the test is whether the answer generalizes, and a one-off build target fails it. Keep the student-facing rule text unchanged.

## 3. Substance tests and stance

- [x] 3.1 Reword the delta test in the Substance Tests section to the confirms/refutes/extends formulation, keeping the feature-list failure clause.
- [x] 3.2 Add the deliberate-stance sentence to the forbidden-content paragraph: omitting work plans, expected results, and the author's name is a deliberate stance many templates contradict, and a program's contrary requirements are honored through the workspace override.

## 4. Sync and verify

- [x] 4.1 Run `python3 scripts/sync_shared.py` and confirm the generated `guidelines.md` copies update.
- [x] 4.2 `uv run poe test` green (no canonical title changed, so the drift tests must stay green).
- [x] 4.3 `openspec validate --all --strict` green.
