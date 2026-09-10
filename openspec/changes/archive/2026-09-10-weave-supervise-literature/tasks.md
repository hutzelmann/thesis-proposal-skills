## 1. Skill prose

- [x] 1.1 `skills/proposal-supervise/SKILL.md`: add `## Ask once about literature` after the execution-shape section — sibling check, the fixed approval sentence, the implicit grant, the declined/headless/missing outcomes.
- [x] 1.2 Add `## Ground the points in literature` between "Decide the tier" and "Curate the feedback": trigger findings, tier-first order, per-finding query rule, snowball-first, retarget once, script-run cap, degradation relay, the pinned verification sentence, the four jobs a paper may do, cap of three, first-mention format with DOI URL, notes-file record, proposal untouched.
- [x] 1.3 Rewrite "Curate the feedback": step 4 (starter literature) removed; points and strengths reference the weaving rule; closing note becomes step 4; wrap-up names the woven papers and reports a search that found nothing fitting.
- [x] 1.4 Inline normalization path: seed the notes file as the import skill would, so the literature record has a place on every run.
- [x] 1.5 Pins: `tests/unit/data/pinned_sentences/proposal-supervise--literature-approval.txt` (the approval sentence) and `proposal-supervise--literature-verification.txt` (the verification sentence).

## 2. Harness

- [x] 2.1 `harness/l1_checks.py`: `verdict_supervise_literature(feedback, notes)` per design D8, docstring stating the rule (it is the projected assertion); extend `verdict_supervise_feedback_contract` to run it — the personal-data scan now also covers the notes file the dev runner passes in (design D9, revised).
- [x] 2.2 `harness/skill_evals.py`: `workspace_files()` extracted at the third listing helper; `supervise_notes_text()`, scorer `supervise_l1_literature`, appended to the `supervise_feedback` task; request gains "Do not look up literature."
- [x] 2.3 `harness/claude_runner.py`: `feedback_files()` also globs `*.notes.md`; the supervise request gains the same pre-answer; new dev-runner-only scenario `supervise_literature` (siblings import + lit-search, approval granted in the request).
- [x] 2.4 `harness/eval_export.py`: `supervise_feedback` expected output mentions woven literature and the scorer→verdict map gains the new pair; `skills/proposal-supervise/evals/evals.json` regenerated.
- [x] 2.5 `harness/README.md`: supervise task line names the literature verdict and the pre-answer, plus a paragraph documenting `supervise_literature` (`--model sonnet`, variance from live APIs).

## 3. Tests

- [x] 3.1 `tests/unit/test_supervise_verdicts.py`: literature verdict cases — no DOI passes; woven DOIs recorded in notes pass; case and trailing punctuation normalized; bulleted list fails naming the DOI; bare citation line fails; unrecorded DOI fails; four DOIs fail; missing feedback fails; aggregate reads the notes.
- [x] 3.2 `tests/unit/test_eval_wiring.py`: `supervise_feedback` scorer list grows by `supervise_l1_literature`.

## 4. Docs

- [x] 4.1 `README.md` "For supervisors": one sentence — with your approval at the start, the feedback grounds its points in two or three verified papers where the findings call for it.

## 5. Verify

- [x] 5.1 `uv run poe test` green (1631 passed; ruff, sync check, conform clean). One adjustment on the way: naming the proposal's `references:` key in the new section made supervise a format describer for `test_format_prose_drift`, so the prose says "reference list" instead.
- [x] 5.2 `openspec validate --all --strict` passes (18 items).
- [x] 5.3 Adversarial review workflow over the diff (four lenses: verdict, prose, spec-drift, conventions → 29 findings; top 12 by severity verified, 6 confirmed, 6 refuted). Fixed: (high) a citation list written without blank lines — plain, numbered, or `•`-bulleted — passed the verdict because the paragraph's words summed past the floor → a paragraph holding several DOI lines is now judged line by line and the bullet set is wider; (medium) DOIs with a balanced parenthesis pair were truncated → regex fixed, notes lookup is token-based; (medium) the as-is normalization path had no notes file for the record → prose creates one on first record; (medium) queries were phrased per point before the points were chosen → the points are chosen before the search, in prose and spec; (medium) "typically" hedged the ready-tier rule → unconditional; (low) the `supervise_literature` scenario was missing from the artifacts → added. Also taken from the unverified tail: the fetched-data judgement sentence pinned, the invoking message's grant or decline counts as the answer and the submission's text never does, DOI-less candidates do not qualify, the notes section is named, a dropped paper is recorded as rejected, the wrap-up names the notes file, an aggregate test covers a leak through the notes file, and the test strings and design context use no real submission's domain.
- [x] 5.4 Dev run on the network path — added as the dev-runner-only scenario `supervise_literature` (lit-search staged as a sibling, approval granted in the request) and run once on sonnet (2026-09-10): L1 PASS on every aspect including the literature verdict; 28 turns, no helper agents, ~$1.02 at API rates. Observed: the request's grant was taken as the answer and no question was asked; two keyword queries, retargeted once, then stopped as the rule says; two Crossref-verified sources (a CRC Press chapter titled "SaaS sprawl", a BSI software-asset-management standard) woven into the thin-literature point with DOI URLs, no standalone block, the normalized proposal's references untouched, both entries in the notes as CSL-YAML with a "serves" line, six rejections under Excluded Literature with reasons. Two soft spots, both model judgement rather than skill defects: the chapter was judged on title and publisher because Crossref returned no abstract (the prose asks for abstract and metadata — a book chapter has only the latter), and the notes' "serves" line named the strengths block while the feedback placed the paper in point 3. Neither changes the contract.
