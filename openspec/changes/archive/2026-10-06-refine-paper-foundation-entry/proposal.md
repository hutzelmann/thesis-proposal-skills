## Why

A final review of `add-paper-foundation-entry` found that the paper path still leaves a menu open, reads more than it needs and less than seeding needs, and turns its per-section fallback into a second question in the turn. The skill may restate the paper's Future Work items before the student points at one, and "tell the student which sections you read" invites a summary of them; together that is the topic menu the no-content rule forbids. A text-file read covers the whole introduction but skips the title and authors that the seeding step matches the fetched record against. A PDF page that also holds Method or Results is thrown away whole. The harness scenario leaves the supervisor item of the preamble unanswered although its requirement says the preamble is pre-answered, and the harness documentation claims the canary check covers any file when the verdict sees only top-level markdown.

## What Changes

- **No Future Work menu, no summary.** The skill names the sections it read and does not summarize their content. It never lays the paper's Future Work items out as options, recommends one, or restates one before the student's answer points at it; only then does it quote the item and judge it with the student.
- **Reading range.** In a text file the skill reads only the front matter (title and authors, which the seeding record match needs), the line ranges beneath the slice's headings, and, for the contributions, the introduction's closing paragraphs. In a PDF it uses nothing from the Method or Results part of a page it opened, rather than discarding the whole page.
- **Per-section fallback as a statement.** For a slice section it cannot locate, the skill says so and says the student may paste it if the paper has one, never reading the whole file or a neighbouring section instead. That is a statement, not a question, so it tells "absent" apart from "not located" and keeps the axis question the turn's only question.
- **Axis wording.** The skill mirrors the student's own words for how the thesis relates to the paper, not only a literal "similar to". It asks the axis question once, and any kinds of change it names go inside that question; this was added after the dev run re-asked the question (design D6). A method-only transfer is spelled out as the paper's method, unchanged, in a new domain.
- **Grounding order.** Grounding whether the transfer was already made waits for the axis and never searches on the paper's own title or its follow-ups. It searches with the student's terms for the new setting.
- **Seeding nit.** The `references:` metadata line names starter entries found during grounding or fetched at seeding.
- **Trim.** The third step states the re-run rule once instead of twice.
- **Harness.** The `ideate_paper_foundation` request also answers the supervisor item ("I don't have a supervisor or research group yet."), so the whole preamble is pre-answered. The harness README and the testing-harness requirement say what the verdict actually sees: a top-level markdown file the run produced. The verdict code does not change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-ideate`: "Entry paths for prepared students" gains the no-summary and no-restating rules, the narrowed text-file range with the front matter, the PDF part rule, the statement-shaped per-section fallback, the mirrored wording, the method-only gloss and the grounding order. "Seeds the proposal file" names records fetched at seeding beside grounding.
- `testing-harness`: "Paper-foundation reading bound covered" scopes the verdict's file checks to top-level markdown files the run produced.

## Impact

- `skills/proposal-ideate/SKILL.md`: the three steps of the paper bullet in `## Entry paths`, and the metadata-block bullet in `## Ending — seeding`.
- `tests/unit/data/pinned_sentences/proposal-ideate--paper-slice.txt`, `--paper-axis.txt` and `--paper-transfer.txt` follow the new wording.
- `harness/claude_runner.py`: the scenario's request text only. `tests/unit/test_paper_foundation.py` pins that the request answers every preamble item and adds the dev run's re-asked question as a failure case.
- `harness/README.md`: one sentence in the scenario paragraph.
- No verdict, fixture, script or description change.
