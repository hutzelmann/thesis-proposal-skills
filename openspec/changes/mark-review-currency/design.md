## Context

See proposal.md, "Why". The current state that shapes the approach, read from `1db2ee4`:

- **Where reviews live.** `proposal-review` writes `<slug>-review.md` beside the proposal and overwrites it after carrying the earlier round over (skill-review "Persisted, actionable output", "Review rounds converge"). The file opens with the verdict line, then the optional `## Earlier round`, then three finding sections, and optionally ends with a grammar hint. The review SKILL.md names these titles inline, in backticks inside its Output bullets, not as headings of its own. `proposal-supervise` writes a professor-only review of the same name, plus the student-facing letter `<slug>-feedback.md`. The letter is pasted text: no headings, no backticks, and the fixed closing note as its last paragraph. `[paths] proposals` moves the whole family together (guidance-model), so the review is always in the proposal's directory.
- **What `check.py` reads.** One proposal file, `structure.json`, and the governing `guidelines.md`. It discovers no companion file today. Research questions are counted in `rule_research_questions` with `^\d+[.)]\s+` over `section_text(body, <canonical RQ title>)`, at column 0 only. The text of a question is never extracted. Findings are `Finding(level, rule, message)` from a closed `RULE_IDS` tuple. The report has two levels, error and warning; there is no info level. `research-questions-too-many` is emitted but missing from `RULE_IDS`. No fixture trips it, so `test_every_emitted_identifier_is_declared` never sees it.
- **Research-question sections are not always just a list.** f04 (German) states an overarching question in a prose sentence ("Die übergeordnete Forschungsfrage lautet: …"), then four numbered sub-questions. The count rule sees four.
- **Who judges currency today.** Agents, at stopping points:
  - the check skill's status read ("Proposal status on request": research questions, scope, method, delta and blocker passages, set against the current file);
  - the write skill's handoff route ("It changed research questions … → fresh review");
  - the shared handoff block's sentence that a review whose research questions … no longer match the text is superseded.
- **Who runs `check.py`.** Check, write (self-verification after every pass), import, reverse, supervise (over the normalized submission, before its review is written) and troubleshoot (into `bug-report/check-output.txt`). Troubleshoot's collector redacts every backticked span that is not a canonical title, and replaces the proposal's name with a placeholder.
- **The harness reads reviews loosely.** `harness/l1_checks.py`:
  - `is_enumerated_review` passes any review with a line matching `^\d+[.)]\s`. It gates `verdict_review` and, through it, `verdict_title_alarm`, `verdict_hollow_review` and every readiness verdict (`_review_shape`).
  - `verdict_review_localized` (Inspect task `review_fixture_de`, over f04) counts German function words over the whole file. f04's sub-questions alone contain three of them (" die ", " der ", " und ").
  - `verdict_hollow_review` and `verdict_title_alarm` scan the whole review text for keywords.
  - `review_sections` ends each section at the next `## ` heading, so a closing record ends the refinements section cleanly and is itself ignored.
- **Fixtures.** w09–w12 each stage f28's text beside a `ci-repair-agent-configurations-review.md` written before the record existed. w10 also holds a notes file recording the narrowing. w10's review judged a broader predecessor with four research questions and quotes its RQ4 verbatim; the dev-runner scenario `handoff_superseded` measures the agents' judgement of it. Every oracle encodes no review finding today.

## Goals / Non-Goals

**Goals:**

- A review's subject, as far as it can be compared mechanically, is on disk in the review itself, readable by a student.
- The check states, deterministically, when that subject no longer matches. It stays advisory and read-only, and keeps its existing exit code and digest contracts.
- No existing workspace changes behaviour: reviews written before the record existed stay silent.
- No shipped verdict changes meaning because reviews now end in a numbered list.

**Non-Goals:**

- Mechanical currency for scope, method, contribution delta or blocker passages. Those stay agent judgement: they have no canonical list to compare, and a hash of whole sections would fire on every polishing pass.
- Marking or moving superseded files. The review is overwritten by the next run, as today. Renaming it to an archive is the territory of `add-proposal-folders-layout`.
- Any change to the shared stage-handoff block, to `proposal-write`, to `proposal-supervise`, or to the proposal file format.
- A third report level. Info findings would change the JSON contract and the two-bucket report for one rule.

## Decisions

### D1. The record is a visible closing section, not hidden metadata

`## Research questions reviewed` (German `## Begutachtete Forschungsfragen`) is followed by an ordered list of the questions, copied verbatim.

Alternatives considered:

- **HTML comment** (`<!-- reviewed-rqs: … -->`): invisible when rendered, so a student cannot see why the check warns. Some markdown tools drop comments on save. It also reads as machine residue in a file written for people.
- **Front matter or a YAML block**: needs YAML parsing, which user-side scripts may not do. It also collides with the proposal's own trailing `---` metadata convention: the check's target resolution auto-picks "a markdown file ending in a `---` metadata block", and after #7 the fixture walkers use that same test to tell a proposal from a companion. A review must never qualify.
- **A digest of the research-questions section**: not verbatim, so it cannot say which question changed, and a student cannot inspect it. Any whitespace edit breaks it.

A visible section survives a student editing the file because extraction is anchored on a heading, not on a position or a byte offset:

- notes added above or below it do not matter;
- re-wrapping or switching `1.` to `-` does not matter (D3);
- deleting it returns the review to the pre-record state, which is silent (D5).

Both titles are accepted whatever the proposal's language. A student who translates the heading by hand, or a German review of an English proposal, still works.

### D2. Placement at the end, after the grammar hint (Q1, decided)

The review's opening is what the student and the chat summary read first: verdict, then blockers. The record is provenance and closes the file, as a references section does. That makes the grammar hint "close the findings" instead of "end the review": the one MODIFIED requirement, the small skill-review "Grammar hint, never a list".

The alternative was directly after the verdict line. It modifies no requirement in wording, but it sits between the verdict and the earlier-round section. That contradicts a strict reading of "Persisted, actionable output" ("After the verdict it SHALL carry the earlier-round section … then three sections in this order"), the larger requirement. The maintainer chose the end of the file, with only the grammar requirement MODIFIED.

### D3. What is recorded, and the match rule

**What the record holds.** The items of the numbered list in the proposal's research-questions section, verbatim, in order, and nothing else. The skill-review requirement says so in the same terms the script compares, because they are the two halves of one contract. Without that, an agent writing a review of f04 can reasonably record the overarching prose question as RQ1, and the check would then warn on every run against a review that is current.

**Extraction**, one extractor shared by both sides:

- **Proposal side.** Items start at an unindented ordered marker in the canonical research-questions section, exactly where `rule_research_questions` counts them. That function is refactored onto the same extractor, so "what counts as a research question" has one definition and the count rule's behaviour is unchanged.
- **Record side.** Items start at an unindented ordered or bulleted marker in the first list under the last record heading. "Last" because the record closes the file: an earlier review pasted in above it by hand does not win. That list ends at the next heading, at a thematic break, or at the first line after a blank line that is neither a list item nor indented. A loose list (`1. A`, blank line, `2. B`) stays one list. Notes a student adds below the record without a heading of their own, bullets included, are therefore not recorded questions, which is what D1 promises. The thematic break is tested before the list marker, because `* * *` would otherwise start a bulleted item.
- **Item extent.** On both sides an item runs from its marker to the next unindented marker, a blank line, or the section's end. Indented lines, nested list items included, continue it. So a sub-list is part of its parent question on both sides, and the count rule and the comparison agree on what one question is.
- **Normalization.** First every Unicode format character (general category Cf) is removed, then `unicodedata.normalize("NFKC", …)`, then `" ".join(text.split())`, then a fold of typographic variants (maintainer decision Q5, extended by the decisions on the implementation review). The removal covers the soft hyphen (U+00AD), the zero-width space (U+200B), the word joiner (U+2060) and U+FEFF, among others: Word's optional hyphens and zero-width marks reach a proposal invisibly through pandoc or PDF import, and a record copied without them asks the same question. It comes first for two reasons. `str.split` does not count these characters as whitespace, so a zero-width space between two spaces removed after the collapse would leave a double space. And NFKC never produces one (checked over every code point), so removing them before it is complete. NFKC and the whitespace collapse absorb line wrapping, indentation, non-breaking spaces, full-width forms and ligatures. The fold maps:
  - single quotes: `'` (U+0027), `‘` `’` `‚` `‛` (U+2018–U+201B) → `'`;
  - double quotes: `"` (U+0022), `“` `”` `„` `‟` (U+201C–U+201F) → `"`;
  - dashes: hyphen-minus (U+002D), hyphen (U+2010), non-breaking hyphen (U+2011), en dash (U+2013), em dash (U+2014), minus sign (U+2212) → `-`.

  NFKC already turns the non-breaking hyphen into U+2010, so U+2010 is in the dash set for the non-breaking hyphen to fold at all. The low-9 and reversed quotes are the German and typographic forms of the same curly quotes, so a German record copied with straight quotes still matches. Both go one step past the forms the maintainer's Q5 answer names (U+2010 and the low-9 and reversed quotes), and the maintainer confirmed them (decisions on the implementation review, 2026-10-14). The skill-check delta lists every folded form and the removal of format characters, so the spec and the normalizer agree. An agent copying a question through chat or an editor's autocorrect swaps exactly these characters without changing what was asked.
- **Comparison.** Item by item, in order. Numbering and marker style never count. Order counts, because the review's findings cite questions by number ("RQ2 cannot fail"), so reordering makes those citations point at other questions.
- **No case folding, no other punctuation folding.** A capitalisation change, a changed word or any other punctuation change is a change to what was judged (D6).

### D4. Severity, identifier and message

The finding is a warning, never an error (maintainer decision), with the identifier `review-questions-changed`. The name says what was detected, not what to conclude, matching the closed set's style (`citation-repeated`, `reference-uncited`). It is reported once per run, after all rule findings: it concerns a companion file, so it comes last in the warnings bucket.

The message names the review file and the differing positions by number, and closes on what replaces the review:

```
`<slug>-review.md` judged research questions that differ from the current ones
(RQ4 removed) — the review may describe an earlier version of the proposal;
a fresh review replaces it, so leave the review file as it is
```

The closing clause follows the style of messages such as `reference-uncited` ("never add a sentence so that it is cited"). The writing skill runs the check after its own pass and fixes findings until only the source material's remain. A pass that changed a question then meets a warning it caused itself, and editing the record or reverting the question are the quick ways to clear it. Both would recreate the staleness this change exists to expose. The clause gives the action without any `proposal-write` prose change (D7).

The positions are computed as structured pairs (position, kind), and the text is formatted only in the finding. The harness verdict (D10) maps the kind without parsing the message, following the repo convention that a consumer never parses a report meant for humans.

A positional diff is enough:

- an insertion in the middle reads as several changed positions plus one added;
- longest-common-subsequence alignment would read better, but it is not worth the code for at most five items.

No question text appears in the message. Troubleshoot's collector redacts backticked spans, but not bare prose. Naming positions keeps proposal wording out of a bug report at every disclosure level without relying on that redaction.

### D5. Silent cases (Q4, decided: silent)

There are three ways to treat a review with no record. The maintainer chose the first.

1. **No finding.** Every review written before this change, every supervise review, and every review whose student deleted the record behaves exactly as today. The agents' content judgement still covers them, which w10 and `handoff_superseded` keep measuring.
2. **A warning that the review predates the record.** It would fire on every existing workspace after release, because `main` is the release channel, and on all four of w09–w12. It says nothing about whether the review is stale.
3. **An info level.** See Non-Goals.

An empty record is likewise silent, and so is a review the script cannot read. "Cannot read" covers both `UnicodeDecodeError` and `OSError`: a OneDrive cloud-only placeholder, a locked file on Windows, or a directory at the review's path raises the latter. `check.py` runs inside six skills, so a crash here would break all of them over a file the check does not own.

### D6. Status read: any mismatch means superseded (Q5, decided: strict, with quote and dash folding)

The shared handoff block already defines supersession: a review whose research questions … no longer match the text. The write skill's route already says that a pass that changed the research questions makes the review superseded. The record only makes the research-question part visible. So the block, which is materialized into all eleven `SKILL.md` files and sits next to the region #7 adds its own block to, stays untouched.

The check skill owns the status question, so its status paragraph gains one clause: any `review-questions-changed` warning means the review judged other research questions and is superseded, whatever the size of the difference, and counts as superseded in the routes that follow. The clause feeds the existing first-match routes rather than naming the step. An added question without a `(RQn)` reference gives `research-question-unreferenced` and the warning in the same run, and errors still route to a writing pass first. The clause is pinned (`proposal-check--review-currency.txt`), because it carries the routing and no dev-runner scenario stages a recorded review in a status read.

Rejected:

- **A spelling-or-punctuation exception** (the first draft). Write's existing route has no such exception, so after a typo fix in a question, write would recommend a fresh review and a status read straight afterwards would say the review still covers the text. The warning would also keep firing with no skill allowed to clear it. Making both agree needs a MODIFIED "Writing pass hands over", which this change avoids.
- **A wider exception for a rewording the review itself asked for** (critic finding). It rests on reading the check route's "never a reason for another review" as covering question changes. That clause covers the language findings fixed on the way to the hand-in build. A pass that changed a research question already routes to a fresh review under write's route and the shared block, so the exception would contradict both and need a MODIFIED on each.

The cost is accepted: a typo fix in a research question routes to a fresh review until the review is rerun. The maintainer chose the strict script plus the quote and dash fold (D3), and later the removal of invisible format characters: a question re-typeset with straight quotes, a hyphen for a dash, or without a soft hyphen is the same question, and the warning stays silent; a changed letter case or word still fires. Loosening further later is a script-only change with no format migration.

### D7. No write guard in this change (Q3, decided: drop)

The first draft added a guard before a writing pass applies a review: compare the record, name the change, apply nothing until the user confirms. The maintainer dropped it:

- The maintainer's decision is the small shape: the review records, the check warns. A third skill's behaviour, a new requirement in that skill's spec and a new pin go beyond it.
- The analysis deferred the marker because no session had yet shown a stale review being acted on. The same missing incident argues against a guard for it.
- What the guard would protect is already partly covered in prose. Write's self-check shows the warning after any pass, its route already recommends a fresh review after a question change, and its scenario "Blockers applied" already leaves the review file unchanged. The warning's closing clause (D4) names the action without a write prose change.

That coverage is unmeasured so far. The only dev-runner scenarios that run a writing pass over a review are `handoff_after_revision` and `handoff_direct_revision`. Both stage w11, whose review has no record, so no run has yet put the warning in front of a writing pass. Adding a matching record to w11's review would let `verdict_handoff_after_revision`, which already fails any write to the review, observe that pressure. It changes the inputs of two existing scenarios beyond the fixtures decided under Q6, and the maintainer declined it (decisions on the implementation review, 2026-10-14): w11 stays as it is, and this coverage stays unmeasured.

The guard's draft delta was deleted from the change folder by the orchestrator, with the maintainer's explicit OK, since no OpenSpec command removes a delta (tasks 1.2).

### D8. `proposal-supervise` is unchanged (Q2, decided: no record)

- **The letter (`<slug>-feedback.md`) never carries the record, under any option.** It is pasted into a mail or a learning platform's feedback field, it allows no headings, and its fixed closing note must stay its last paragraph.
- **The professor-only review.** Two reasons to leave it without a record in this change:
  - Supervise's own resubmission intake already reads the earlier review by content (title, research questions, method) before overwriting it.
  - No status read runs over it, and a record there would make `check.py` warn inside supervise's own resubmission run, before the overwrite. That would need a sentence telling the agent that the warning concerns the earlier round and stays out of the feedback.

  Without a record, check stays silent there, and supervise needs no edit.

### D9. Fixtures: a minimal pair plus a matching control (Q6, decided)

- **`w16-superseded-record`** (new; #7 owns w13–w15, so this change creates w16 only). w10's three files byte for byte: the proposal (f28's text), the notes file, and the review. The review gains one addition: a closing record that lists the broader predecessor's four questions, RQ1–RQ3 as f28 states them plus RQ4 as w10's review quotes it. Oracle: exit 0, no errors, `warnings_contain: ["RQ4 removed"]`, `rules.warnings: ["review-questions-changed"]`. The `semantic` list is w10's, plus the warning. Because the notes file is copied too, the record is the only difference in the pair.
- **`w10-narrowed-scope`** stays as it is. It is the unmarked control whose superseded state only judgement can see, so `handoff_superseded` keeps measuring that judgement.
- **`w12-ready-current`**'s review gains a record of f28's three questions, verbatim. Its oracle is unchanged (no findings), and it becomes the rule's passing fixture, as "Fixture corpus with oracles" asks: one fixture trips each rule and one passes it. `handoff_ready` is a dev-runner-only scenario, so no shipped verdict moves.

The fixture walkers do not take a review for a proposal: today `helpers.is_fixture_proposal` excludes `<slug>-review.md` beside its proposal, and after #7 it uses `check.py`'s proposal test (a markdown file ending in a metadata block), which a review closing on a list never passes. #7's `companion-orphaned` rule stays silent on w16, since the review and notes file share the proposal's handle.

### D10. Tests and verification

**L0 tests** (`tests/unit/test_check_rules.py`, or a new `tests/unit/test_review_currency.py` if that file grows past readability) call the new functions in-process. They cover every case in the skill-check delta's scenarios, plus:

- an indented continuation line, and an unindented lazy continuation;
- a nested sub-list on both sides;
- the last-heading rule;
- notes below the record with bullets, and a thematic break (`---`, `* * *`) after it, both silent;
- a proposal whose file name is not a kebab-case slug (`My Proposal.md` beside `My Proposal-review.md`), which must still warn, so the rebase onto #7 cannot narrow the review path to slug-shaped names;
- the no-proposal-items skip;
- `UnicodeDecodeError`, and a directory at the review's path (portable stand-in for `OSError`);
- `--json` and human output agreeing on the exit code.

`research-questions-too-many` gets its unit test and an entry in `COVERED_BY_UNIT_TESTS`, since `test_every_declared_identifier_is_reachable` counts only fixture oracles and that set. `review-questions-changed` is reached by w16's oracle.

**Drift test.** Every title in `check.py`'s record-title constant appears as `` `## <title>` `` inside the record bullet of the review SKILL.md's Output section, which names section titles inline in backticks; a failure names the missing title. The sentence carrying the verbatim instruction is also pinned (`proposal-review--rq-record.txt`), so a reword from "copied verbatim" to "summarize" fails offline.

**Review-shape verdicts.** A helper in `harness/l1_checks.py`, `without_rq_record(review)`, cuts every record section, located through `CHECK_SCRIPT`'s record-title constant and section finder. It is applied before `is_enumerated_review` in `verdict_review` and `verdict_title_alarm`, before the German-signal count in `verdict_review_localized`, and before the whole-text keyword scans in `verdict_hollow_review` and `verdict_title_alarm`. `review_tier` and `review_sections` need nothing: the first reads the opening lines, and the second ignores the record heading and ends the refinements section at it. L0 tests in `tests/unit/test_harness_helpers.py`:

- bulleted findings plus a numbered record → "review not enumerated";
- an English review plus f04's German record → not German.

Correction to the first draft, which said the shipped verdicts were untouched: no Inspect task is added or rewired, but without the helper the record would loosen the L1 gates of `review_fixture`, `review_fixture_de`, `title_alarm`, `review_hollow` and every readiness task. With it they judge what they judged before. If a verdict docstring changes, the `evals/evals.json` projection is regenerated (`harness/eval_export.py`). No matrix cell is re-run: the gates keep their meaning, and a re-run is metered.

**L1.** `verdict_review_records_questions(original, current, review, review_name)` in `harness/l1_checks.py`. It reuses `CHECK_SCRIPT`'s extractor and normalizer, so the verdict and the warning cannot disagree. Its L0 tests go in `tests/unit/test_readiness_verdicts.py`, including f04 with the overarching question recorded as an extra item, which must fail. It is wired to a new dev-runner scenario `review_record`: f28 and `READINESS_REVIEW_REQUEST`, as in `review_ready`, but judged on the record alone. No Inspect task and no `test_eval_wiring.py` entry.

**Verification.** `uv run poe test` and `uv run poe specs` green, then one `uv run poe dev review_record --model sonnet --isolated` on the subscription, at the maintainer's go. Plan quota only, never metered.

### D11. Adjacent fix: declare `research-questions-too-many` (Q7, decided: here)

This change rewrites `rule_research_questions` onto the shared extractor. A one-line `RULE_IDS` entry, one unit test and one `COVERED_BY_UNIT_TESTS` entry close a gap in a requirement that already exists ("Findings carry stable identifiers"). No spec delta: the spec already demands it.

### D12. The review's path is referenced, not restated

The skill-check delta names the review as "the review file the review skill writes for this proposal" and points at skill-review "Persisted, actionable output" and #7's proposal-file-format "Proposal family under one handle", instead of restating `-review` before `.md`. `add-proposal-folders-layout` is expected to move reviews; with the derivation in one place, that change modifies the family requirement and the warning follows.

In code, the path sits behind exactly one function in `check.py`. Because this change is built in parallel with #7 on a `main` that does not yet have #7's family vocabulary, that function holds a temporary `-review.md` literal, the only one in `check.py`. At the rebase onto #7 (landing-time task 7.1), the function is swapped to #7's family vocabulary: it builds the name from the `review` entry of #7's role table (`COMPANION_SUFFIXES` in #7's draft), as `proposal.with_name(proposal.stem + suffix + ".md")`. It never classifies through `family_member` or its shape test. Those return nothing unless the stem is a kebab-case slug, and today's warning also covers stems such as `My Proposal` or `Exposé`, whose review #7's own definition of the slug (the file name without the extension) still names `<stem>-review.md`. An L0 test with a stem that is not kebab-case pins this (D10). The rebase verifies that no `-review.md` literal remains in `check.py`. Every caller goes through the function, so the swap touches one body.

## Coordination with parallel changes

Landing order is #5 `widen-lit-live` → #6 `utf8-script-output` → #7 `tighten-proposal-family` → #8 this change. #5 and #6 are on `main` (`2f1fa0d`).

**Built in parallel with #7 (maintainer decision, 2026-10-14).** This change is implemented now, on top of `main` at `2f1fa0d`, in its own worktree, while #7 is implemented in another. The landing order stays: #7 lands first, then this change is rebased onto it (landing-time task 7.1). To keep that rebase small:

- the review's path sits behind one function in `check.py`, with a temporary `-review.md` literal; the rebase swaps it to #7's family vocabulary (the `review` entry of its role table, never a classification through `family_member`) and checks that no `-review.md` literal remains in `check.py` (D12);
- new `check.py` helpers sit next to `rule_research_questions`, not after `paths_findings`, where #7's `family_findings` goes;
- new `SCENARIOS` entries in `harness/claude_runner.py` sit next to the same skill's scenarios, not at the end of the table, where #7 appends;
- new verdicts in `harness/l1_checks.py` sit beside the related review verdicts;
- the only new fixture is w16; #7 owns w13–w15.

**Requirements touched here.** ADDED: skill-review "Research questions recorded in the review", skill-check "Review currency warning", testing-harness "Review-currency coverage". MODIFIED: skill-review "Grammar hint, never a list". #6 only ADDed to skill-packaging, and #7's draft only ADDs (proposal-file-format, skill-check, skill-ideate, skill-lit-search, skill-packaging, testing-harness), so no MODIFIED collision exists today. Task 7.1 re-checks this against #7's archived text.

**#7's read-only sentence (Q8, closed).** #7's ADDED skill-check requirement "Orphaned companions reported as a warning" scopes its read-only sentence to its own finding: "For this finding, the check SHALL open another file only to tell a proposal from a companion, and SHALL change nothing." It therefore leaves this change's review read allowed, and this change carries no MODIFIED block for #7's requirement. Task 7.1 confirms the archived wording still scopes the sentence before landing.

**Files shared with #7:**

- `check.py`: `RULE_IDS` (#7 adds a `# workspace family` group after `proposal-misplaced`, so this change's entries go in another hunk), `check_findings` (#7's `family_findings()` call sits beside `paths_findings()`), and the family vocabulary (`family_member`), which the review-path function adopts at the rebase.
- `harness/l1_checks.py`: #7 adds `verdict_family_only` and `verdict_family_renamed`.
- `harness/claude_runner.py`: #7 adds three scenarios to `SCENARIOS` and the dispatch.
- `harness/README.md`: #7 documents its scenarios under "Dev runs".
- `tests/helpers.py`: #7 switches `is_fixture_proposal` to `check.py`'s proposal test.
- `proposal-review`, `proposal-check` SKILL.md: #7 replaces location sentences and adds a materialized block near `## Handing over`.
- `tests/fixtures/README.md` (and the fixture numbers: #7 takes w13–w15), `tests/unit/test_check_rules.py`. In the README, w16's entry sits directly below w10's, the fixture it pairs with, and w12's line stays untouched: #7 inserts w13–w15 after w12, and a trial three-way merge against #7's in-progress tree conflicted only on an edited w12 line followed by w16.

Re-run `python3 scripts/sync_shared.py` after rebasing. The vendored `check.py` copies carry `merge=ours`.

**#6 on `main`.** `utf8_output()` stays the first statement of `check.py`'s `main()` (`tests/unit/test_utf8_output.py` pins it), and any new subprocess capture of script output in the tests names `encoding="utf-8"`. Nothing here prints new non-ASCII text beyond the em dash the existing messages already use.

**Body size.** Review and check each gain one or two sentences. Re-check the median cap after #7's block lands.

## Risks / Trade-offs

- [The agent paraphrases or translates the record, or adds the overarching question] → `check.py` then warns on a review that is in fact current, and under D6 the status read routes to a fresh review. Mitigations: the record definition in the same terms as the extractor (D3), the pinned verbatim sentence, and the `review_record` dev-runner verdict, whose L0 tests include the f04 shape.
- [A typo fix in a question routes to a fresh review] → Accepted (D6). It matches the write skill's existing route, and the alternative needs MODIFIED write and handoff wording.
- [A student edits the record to silence the warning] → Accepted. The record is visible and theirs. The warning concerns what the review judged, not a gate, and the check is advisory.
- [A warning on every check run until the next review] → Intended: that is the "visible on disk" the maintainer asked for. Write's self-check shows it too, which agrees with its fresh-review route.
- [The record loosens harness gates] → The record-stripping helper (D10), with L0 tests for the two gates the record would otherwise satisfy.
- [Normalization too strict] (a case change fires) → Accepted with D6. Quote and dash variants are folded and invisible format characters removed (D3); loosening further later is a script-only change with no format migration.
- [Positional diff reads awkwardly after an insertion] → Accepted for at most five questions. The message's job is "something changed, here is roughly where".
- [Supervise warns in a professor's run] → Not possible under D8: supervise reviews carry no record.
- [#7's read-only sentence lands in a wider wording than its draft] → Q8 is closed on #7's draft; task 7.1 re-reads the archived text at the rebase and stops the landing if the sentence no longer scopes to #7's own finding.
- [The parallel build drifts from #7] → The placement rules in "Coordination" keep the hunks apart, and the review path's one function is the only seam that changes at the rebase (task 7.1).

## Migration Plan

None needed. Existing reviews carry no record and stay silent (D5). Each review written after release closes with the record and is compared from then on. Rollback is reverting the commit: a review that carries a record is still valid markdown, and older scripts ignore the section.

## Critic findings, 2026-10-13

Applied:

- #7's read-only sentence contradicts the review read → Coordination and Q8; #7's draft now scopes it, and task 7.1 re-reads the archived text.
- Fixture number collides with #7's w13 → `w16-superseded-record`; #7 owns w13–w15.
- Write guard exceeds the decided shape → Q3 now recommends dropping it; D7.
- The pair also differed in the notes file → the notes file is copied (D9).
- Item extent contradicted D3 → one rule for both sides, unindented markers only, with a nested-item scenario (D3).
- The spelling exception disagreed with write's route → any mismatch is superseded (D6, Q5).
- "Later round" was untestable → it asserts exactly one record, the last section.
- The drift test expected a heading line in SKILL.md → it looks for the backticked title in the Output bullet (D10).
- Reachability needs `COVERED_BY_UNIT_TESTS`; the 6.2 command used a relative script path → both fixed in tasks.
- The status-read clause had no offline guard → pinned (D6).
- The record would loosen shipped L1 gates → record-stripping helper and two L0 tests (D10).
- The record definition did not match what the script compares → numbered items only, with the f04 scenario (D3).
- Unreadable review raised `OSError` → silent case widened (D5).
- The review path was restated → referenced instead (D12).

Rejected:

- Widen the exception to rewordings the review asked for → the "never a reason for another review" clause covers language findings, not question changes; the exception would contradict write's route and the shared block (D6).

## Maintainer decisions, 2026-10-14

Answered in the session chat ("Accept, build in parallel"):

- **Q1 Placement**: end of file (D2). Only "Grammar hint, never a list" is MODIFIED.
- **Q2 Supervise**: no record in the professor-side review (D8). The letter never carries it.
- **Q3 Write guard**: dropped (D7). The orchestrator deleted the guard's draft delta with the maintainer's explicit OK.
- **Q4 Records written before this change**: silent (D5).
- **Q5 Strictness**: strict, plus a fold of quote and dash variants (D3, D6). NFKC, whitespace collapse, curly and straight single and double quotes to one form each, and hyphen-minus, en dash, em dash, minus sign and non-breaking hyphen to one form; case and wording stay significant.
- **Q6 Fixtures**: new w16 plus a matching record in w12 (D9).
- **Q7 Adjacent fix**: `research-questions-too-many` is declared here (D11).
- **Q8 #7's read-only sentence**: closed; #7's draft scopes it to its own finding (Coordination).
- **Build order**: in parallel with #7, on `main` `2f1fa0d`; the rebase onto #7 and the swap of the review-path function are a landing-time task (7.1).

## Implementation review, 2026-10-14

Applied:

- The status-read clause named the step ("so the step is a fresh review") and contradicted the first-match routes when errors co-occur → the clause feeds the routes (D6), with a scenario for errors beside a superseded review.
- The delta's fold list omitted the hyphen (U+2010) and the low-9 and reversed quotes the fold covers → listed in the delta (D3); an extension of Q5, confirmed by the maintainer (below).
- The record verdict parsed the warning's text → `question_changes` returns (position, kind) pairs (D4).
- The record pin left the overarching-question and nested-item clause unpinned → the pin covers the whole clause through "exactly one when you overwrite an earlier review".
- Three test helpers each appended a record, and f04's questions were extracted twice → one `review_with_record` and one `f04_numbered_questions` in `tests/helpers.py`.
- Notes below the record, with bullets or a thematic break, counted as recorded questions → the record ends where its first list ends (D3).
- The warning named no action, which a writing pass could clear by editing the record → the message closes on the replacement (D4).
- A swap through `family_member` would drop the warning for stems that are not kebab-case → task 7.1 and D12 name the role table, and an L0 test pins such a stem.
- The fixtures README conflicted with #7's w13–w15 → w16 below w10, w12's line untouched (Coordination).

Left to the maintainer, because they went beyond the decisions of 2026-10-14, and decided below:

- The fold's extension to the hyphen (U+2010) and the low-9 and reversed quotes (D3).
- A matching record in w11's review, so the two write-over-review dev scenarios observe the warning (D7). It changes the inputs of `handoff_after_revision` and `handoff_direct_revision`, beyond the fixtures decided under Q6.
- Removing Unicode format characters (soft hyphen U+00AD, zero-width space U+200B, word joiner U+2060, U+FEFF) before the fold. Word's optional hyphens reach a proposal through pandoc or PDF import, and a record that drops one would warn on a current review. It extends the Q5 normalization.

### Maintainer decisions on the implementation review, 2026-10-14

Answered in the session chat ("Accept all five (Recommended)"):

- **Fold extension**: confirmed. The fold keeps the hyphen (U+2010) and the low-9 and reversed quotes (U+201A, U+201B, U+201E, U+201F) (D3).
- **Format characters**: accepted. `normalize_question` removes every character of general category Cf before NFKC and the fold, test-first (task 2.11; D3, skill-check delta). The record verdict reuses the same normalizer, so it stays consistent with the warning.
- **Record in w11's review**: declined. No record is added to w11, and D7's note that the write-over-review coverage is unmeasured stays.
