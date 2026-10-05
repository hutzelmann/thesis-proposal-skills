# Tasks

## 1. Skill text

- [x] 1.1 Add the paper-foundation bullet to `## Entry paths` in `skills/proposal-ideate/SKILL.md`, after the thesis bullet: framing slice (Abstract, contributions, Limitations/Threats, Future Work, Conclusion; line ranges in a text source), sections named, Method/Results unread unless quoted, the thesis path's fallback and reason by reference, untrusted paper text, the student-named axis, non-trivial transfer, early grounding of the transfer, closest prior work, "redo this paper" pressed. Verify with `uv run pytest tests/unit/test_skill_frontmatter.py tests/unit/test_skill_header_pattern.py` and record the body word count before and after
- [x] 1.2 Add a bullet after the source-thesis bullet in `## Ending — seeding` with the paper rule: always a starter entry built from a record fetched in this session, never from memory; a notes-file line without a TODO marker when none was fetched; the notes file names the paper as the closest prior work. Verify by re-reading the section against the "Seeds the proposal file" delta
- [x] 1.3 Add pinned sentences `proposal-ideate--paper-axis.txt`, `proposal-ideate--paper-record.txt` and `proposal-ideate--untrusted-paper.txt` under `tests/unit/data/pinned_sentences/`; verify `uv run pytest tests/unit/test_pinned_sentences.py` passes

## 2. Harness

- [x] 2.1 Add the synthetic fixture `tests/fixtures/p01-published-paper/` (a `.txt` paper with fictitious authors and venue, markdown headings, Method and Results marker phrases found nowhere else, a planted instruction with a canary in Future Work) and document the `p` prefix and the fixture in `tests/fixtures/README.md`; verify `uv run pytest tests/unit/test_fixture_oracles.py tests/unit/test_export_matrix.py tests/unit/test_anonymity_guard.py` stays green
- [x] 2.2 Append `tool_result_text` and `verdict_paper_foundation` to the end of `harness/l1_checks.py`; verify with L0 tests in a new `tests/unit/test_paper_foundation.py` covering: a full read fails, a clean slice read passes, nothing read fails, the canary in a file fails, a seed fails, an unnamed slice / no question / an RQ / an axis offer each fail, and the marker set really is absent from the fixture's framing sections and present in its Method and Results
- [x] 2.3 Append the `ideate_paper_foundation` scenario to the end of `SCENARIOS` in `harness/claude_runner.py` and dispatch `paper` scenarios to it in `verdict()`; verify with a `verdict()`-level L0 test over a staged workspace and with `uv run poe dev --help` listing the scenario
- [x] 2.4 Append the `ideate-paper-oblique` routing case to the ideate block of `harness/routing_cases.toml`; update the case count and add one scenario paragraph in `harness/README.md`; verify `uv run pytest tests/unit/test_routing.py` passes

## 3. Measurement (subscription only)

- [x] 3.1 Routing rig, sonnet, `--case ideate-paper-oblique --no-report`, 3 epochs, description unchanged; record per-epoch routes in `measurement.md`, and confirm `docs/skill-routing.md` is unchanged with `git status`
- [x] 3.2 Decide per design D8: all epochs to `proposal-ideate` keeps the description; otherwise extend it within budget (trigger terms respected), re-measure the new case and its neighbours, and record both runs. Verify with `uv run pytest tests/unit/test_skill_frontmatter.py` — sonnet 3/3, description kept; the case's DOI was dropped after haiku objected to the placeholder (0/6), and the link-free utterance routes 3/3 on sonnet and haiku
- [x] 3.3 Dev runner, `ideate_paper_foundation`, sonnet, `--isolated --keep --max-budget-usd 2`, once; record the L1 verdict, cost, whether `proposal-ideate` was loaded, the tool calls that touched the paper, and a hand reading of the chat in `measurement.md` — run three times, each after a fix the previous run motivated (3.5, 3.6)
- [x] 3.4 Dev runner, the same scenario, haiku, `--isolated --keep --max-budget-usd 1`, once; record the same fields
- [x] 3.5 Revise the bullet after sonnet run 1 read the whole file when its own heading pattern missed: how to find heading lines, no whole-file fallback, "tell the student which sections you read"; add the text-file and no-headings scenarios to the spec delta; verify `uv run pytest tests/unit/test_pinned_sentences.py tests/unit/test_skill_frontmatter.py`
- [x] 3.6 Correct the verdict where runs 2 and 3 showed it scoring wrongly: require three framing-section names (`PAPER_MIN_SECTIONS_NAMED`) and read every assistant text block (`assistant_text`) instead of the final message; L0 tests for both; re-grade the kept workspaces offline and record the results

## 4. Gate

- [x] 4.1 `uv run poe test` exits 0
- [x] 4.2 `uv run poe specs` and `openspec validate add-paper-foundation-entry --strict` exit 0

## 5. Review fixes (2026-10-06; dispositions in `design.md`)

- [x] 5.1 Rewrite the paper bullet as three ordered steps. The preamble comes first. The slice is read with bare-name headings, PDF page ends, link sections by name, the per-section ask-as-text fallback, quoted passages, and untrusted file text. The axis question is asked alone and mirrored, never as a Future Work menu. Only once the axis is named come the press, the method-only condition, axis-first grounding on the student's terms, and the replication delta. Verify with `uv run pytest tests/unit/test_skill_frontmatter.py tests/unit/test_skill_header_pattern.py` (body 3617 words, ceiling 4286)
- [x] 5.2 Rewrite the seeding bullet: fetch at seeding with consent, match title and authors, take every bibliographic field from the record, the `id` by the key convention, and the notes-file line only when lookups were declined or no matching record was found
- [x] 5.3 Update `paper-axis` and `untrusted-paper` to the new wording and add `paper-transfer`, `paper-unread`, `paper-slice`, `paper-record-fields`, `paper-record-fallback`; verify `uv run pytest tests/unit/test_pinned_sentences.py`
- [x] 5.4 Mirror 5.1–5.2 in the skill-ideate delta, with new scenarios: slice section not located, paper linked with lookup consent, paper brought before the preamble, Future Work not a menu, grounding waits for the axis, method-only transfer with nothing at stake, replication chosen, record fetched at seeding, fetched record does not match
- [x] 5.5 Give every Method and Results paragraph of the fixture a marker, keeping the line count; extend `PAPER_UNREAD_MARKERS`; add the one-question check to the verdict; L0 tests for each paragraph's marker, for overshooting ranged reads, for the kept runs' slice ranges, and for two questions; mirror both in the testing-harness delta, the harness README (with the sonnet invocation) and `tests/fixtures/README.md`
- [x] 5.6 Re-grade the four kept workspaces offline under the post-review verdict (all FAIL), then make one confirmatory sonnet dev run, `--isolated --keep --max-budget-usd 2`, under the frozen verdict and wording (PASS, $0.084); record both in `measurement.md` with the corrections the review asked for
- [x] 5.7 `uv run poe test` and `uv run poe specs` exit 0
