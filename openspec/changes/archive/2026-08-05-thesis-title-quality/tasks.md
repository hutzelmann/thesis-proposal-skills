## 1. Authority and data

- [x] 1.1 Add the thesis-title rule to `shared/guidelines/guidelines.md`: the positive criterion (contribution + object, tool-independent, standalone on the certificate), the four alarm classes, and the raise-and-justify posture — pointing at the `structure.json` bounds without repeating the numbers
- [x] 1.2 Add the `title` block to `shared/structure.json`: `implementation_openers` (en + de, prefix-matched), `buzzwords` (en + de, substring-matched), `min_words`, `max_words` — values per design.md
- [x] 1.3 Run `python3 scripts/sync_shared.py` and confirm `--check` is clean

## 2. Deterministic checks

- [x] 2.1 Add title tell checks to `skills/proposal-check/scripts/check.py` as warnings: opener at title start, buzzword anywhere, trailing `?`, word count outside bounds — each message naming the matched tell and the certificate consequence
- [x] 2.2 Re-sync the vendored `check.py` copies in `proposal-import` and `proposal-write`
- [x] 2.3 Unit-test each tell (trip and pass) plus the clean-title control in `tests/unit/`
- [x] 2.4 Verify no title finding can set a non-zero exit

## 3. Skill behavior

- [x] 3.1 `proposal-ideate`: raise the alarm on a tool- or implementation-shaped working title, name the certificate consequence, offer 1–3 abstracted alternatives, keep the title labelled working, never block seeding
- [x] 3.2 `proposal-write`: bind the negotiation once the research questions exist, explicitly including a title inherited unchanged from a seed; write the student's chosen title, never a silent replacement
- [x] 3.3 `proposal-check`: judge in the agent pass what the patterns cannot reach (proper noun as instrument, field-naming), reported under the flagged bucket
- [x] 3.4 `proposal-review`: assess the title as its own enumerated dimension, including drift from the research questions
- [x] 3.5 Confirm each edited SKILL.md still satisfies the header pattern and its pinned mandate (`tests/unit/test_skill_header_pattern.py`)

## 4. Fixtures and oracles

- [x] 4.1 Add the bad-title fixture (`Implementing an AI-Powered Kubernetes Dashboard at Musterfirma GmbH`) with an `expected.json` oracle recording the tripped tells
- [x] 4.2 Run the deterministic check across the whole fixture corpus and recalibrate every `expected.json` where a title warning now fires (f08 and f15 expected)
- [x] 4.3 Confirm clean-title controls stay silent

## 5. Eval

- [x] 5.1 Add the metered L2 title-alarm task to `harness/skill_evals.py`, scoring: title raised, certificate consequence named, 1–3 abstracted alternatives offered, no silent rewrite
- [x] 5.2 Document the task in `harness/README.md`

## 6. Verification

- [x] 6.1 `uv run pytest` green
- [x] 6.2 `uv run ruff check .` clean
- [x] 6.3 `python3 scripts/sync_shared.py --check` clean
- [x] 6.4 `openspec validate --all --strict` passes
- [x] 6.5 Adversarial verify pass over the whole diff before committing

**Verify findings (4 review lenses, 24 raw findings, 8 adversarially verified, 5 refuted).** Fixed:
- *(confirmed, major)* Three of five title messages omitted the certificate rationale the skill-check spec requires of every finding, and only one test asserted it. All five now carry it; `test_every_title_warning_names_the_certificate` pins it per tell.
- *(confirmed, major)* The question-form tell had no basis in `guidelines.md`, which named four classes and nothing about form. The prose now states the form and bounds rules, and the guidance-model delta says so too.
- Missing `skill-write` behaviour for two spec scenarios: what happens when the student picks an alternative (slug stays), and that a justified title is not re-raised each self-check pass.
- `proposal-ideate`'s title paragraph sat *after* the instruction that writes the file and slug, and exempted itself from the skill's hard rule in its own voice. Moved above the write step, rewritten without the self-exemption, and given the accepted-alternative branch.
- `towards a` / `towards an` dropped from the openers: it is the standard hedge of a theory title, and the emitted message would have called it building work.
- `min_words` split per language — German compounds made a language-blind bound warn on correct short German titles.
- Unicode: titles are NFC-normalised, so a decomposed umlaut no longer silently escapes the buzzword list.
- A `title:` holding only a YAML block-scalar indicator is no longer judged (it reported "title runs 1 words" on a good long title).
- `verdict_title_alarm` accepted any review containing the word "title"; it now requires the certificate rationale, and both it and `title_line` have L0 coverage, as the testing-harness spec requires of every pure verdict.
- `proposal-check`'s "do not judge semantic quality" line now names the title bullet as its single exception; `tests/fixtures/README.md` no longer claims every other fixture's title is silent, and the f08/f15 rows list their title findings.

Refuted and left alone: opener prefix matching without word boundaries (the proposed fix does not change the headline example); `seamless`/`disruptive` in the buzzword list (a reviewed curation decision design.md records, and warnings are advisory by construction); warning-completeness not enforced corpus-wide by the oracles (reproduction showed both named regressions do turn the suite red); `proposal-import` allegedly instructed to rewrite titles (that passage is error-scoped and title findings are warnings); "no fixture trips the question or max-words tells" (the corpus has never pinned one fixture per message variant).
- [x] 6.6 Run the metered L2 title eval once and record the findings here

**Eval finding (2026-08-05, `title_alarm`, openrouter/anthropic/claude-haiku-4.5, 228k tokens).**
`title_l2_alarm` passed on all five rubric criteria: the review raised the title as its own finding, named the platform-as-instrument and the employer name, said the title reaches the study certificate, offered three abstracted alternatives, and left the choice with the student. `title_l1` failed: the model then rewrote the proposal's `title:` to one of its own suggestions and invented four unrequested workspace files (`REVISION_SUMMARY.md`, a check report, a `PUBLICATION_PACKAGE.md`, a `README.md`). That is the documented Inspect-loop overreach already red for `check_report` and `review_fixture`, not a title-specific defect — the title guidance itself scored clean. Recorded in `harness/README.md` under known limitations.
