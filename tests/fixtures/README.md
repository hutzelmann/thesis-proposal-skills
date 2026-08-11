# Fixture Corpus

Reference for the synthetic test fixtures in this directory (the "fixture blueprint" the testing-harness spec refers to). The designs were informed by a private corpus of real student proposals (11 documents, mixed quality); nothing here maps to an identifiable original: topics are altered, all names and institutions removed, defect patterns generalized. Each proposal-fixture directory holds one proposal file plus an `expected.json` oracle calibrated against the check script; `g`-prefix web fixtures hold served web assets instead and carry no oracle, and `s`-prefix raw submissions (a student's email or export before any normalization — not a proposal, so not check-able) carry none either.

## Corpus-derived failure taxonomy (aggregate, anonymized)

| Pattern | Frequency | Tested by |
|---|---|---|
| No research questions at all | ~4/11 | Check (RQ section empty), Write/Ideate (must elicit) |
| RQs phrased as implementation goals ("how can X be built") | dominant where RQs exist | L2 rubric, Review |
| Bibliography present but never cited in-text | ~6/11 | Check (defined-but-uncited warning) |
| < 3 scientific references / URL-only bibliographies | ~4/11 | Check ([references] min_count), lit-search |
| Mixed methodologies in one proposal | ~4/11 | Review rubric (single-method rule) |
| Forbidden content: work plans/Gantt, chapter outlines, expected results | very common | Check (forbidden headings, timeline size guard) |
| Personal data: matriculation numbers, addresses, supervisor names/emails | common | Check (warning regexes), Import (strip on import) |
| Passive voice pervasive (esp. German), first-person narrative slips | near-universal (de) | Check warnings, Review hint |
| Confidentiality markers ("confidential", "vertraulich", NDA remarks) in industry-context proposals | recurring in corporate topics | Check warning (theses get published) |
| Free-form section structures (Goal/Work-steps, Scope/Approach, …) | majority | Check (canonical sections), Import (restructure) |
| Vendor/commercial sources grounding core claims | recurring | Review rubric, lit-search venue preference |
| Figures | nearly absent (0–1 per proposal) | confirms D3 (img/ optional) |
| PDF production variety: Word, LaTeX, LLM-assisted (formatting artifacts, swallowed headings, missing title blocks) | across corpus | Import robustness |

## Planned fixtures

Each fixture = one proposal file in the new single-file format (plus, for Import tests, a rendered PDF variant). `seeded defects` split into **mechanical** (Check must flag deterministically) and **semantic** (L2 rubric / Review must catch). Topics are synthetic.

| id | lang | level | tier | shape | seeded defects |
|---|---|---|---|---|---|
| `f01-narrative-sketch` | de | BSc | low | free-form "Goal / Work steps" narrative | mech: no RQ section, no in-text citations, forbidden work-plan heading; sem: first-person storytelling, no gap argument, unfalsifiable outcome |
| `f02-tool-comparison` | de | BSc | mid | Motivation/Objective/Work-steps + Gantt | mech: Gantt table under a legitimate `Zeitplan` heading (size guard, not forbidden heading), 2 URL-only refs (< min), no RQs; sem: evaluative goal never sharpened into questions |
| `f03-compliance-audit` | en | BSc | mid-high | numbered free-form incl. chapter outline + timetable, personal data on cover | mech: forbidden chapter-structure + timetable headings, matriculation/address patterns, work-package pseudo-RQs; sem: RQs are work packages, typos |
| `f04-dsr-vendor-heavy` | de | MSc | mid | TOC/abbreviations, 1 main + 4 sub-RQs, chapter outline | mech: forbidden outline, supervisor + matriculation on title page, duplicate reference entry, "vertraulich" title-page stamp; sem: vendor pages ground definitional claims, RQ sub-questions design-phrased |
| `f05-slr-interviews` | en | MSc | high | canonical 4 sections | mech: clean (control fixture); sem: mixed methodology (SLR + interviews) violating single-method rule, missing interview-ethics note |
| `f06-prototype-testbed` | en | BSc | mid-high | canonical 4 sections | mech: forward-dated reference year; sem: passive-heavy evaluation, 4-campaign scope risk without fallback, no architecture figure despite hardware topic |
| `f07-network-pathfinding` | en | BSc | mid | custom Scope/Requirements/RQ/Approach/Schedule | mech: forbidden schedule, supervisor named, 2 refs; sem: 3 of 4 RQs implementation-goal, one leading RQ, mid-document first-person switch, typos |
| `f08-concept-sketch` | de | BSc | low | Abstract/Intro/Objective/Solution/Work-steps | mech: no RQs, no real bibliography (prose URL list), no in-text markers, implementation-opener title (`Konzept für …`); sem: severe passive, goals as construction aims, unfalsifiable "concept" outcome |
| `f09-llm-compliance-docs` | en | MSc | high | near-canonical, work-plan table | mech: forbidden work-plan heading, no title/author metadata, refs never cited in-text, swallowed-heading formatting artifact (Import robustness); sem: 3 "which…" RQs lacking degree phrasing, mixed method |
| `f10-risk-scoring` | en | MSc | mid | free-form with supervisor block | mech: supervisor names + emails, undated phase table, refs never cited in-text, "confidential — internal use only" footer marker; sem: 2 of 4 RQs implementation-goal, none operationalized, evaluation leans on internal feedback |
| `f11-migration-architecture` | de | BSc | high | canonical + extra Scope/Summary sections | mech: extra non-canonical sections (warning), vendor-doc references; sem: RQ2 is yes/no, requirements read as spec list — near-target quality, tests that Review stays quiet on structure |

## Beyond-corpus fixtures (invented — no workspace source)

The corpus leaves real coverage holes; these fixtures are designed from the rules alone:

| id | lang | level | purpose |
|---|---|---|---|
| `f00-clean-en` | en | MSc | Fully compliant control, converted from the legacy Jane Doe `proposal.tex` (migration step 3) — the only workspace-sourced entry here, listed for completeness. |
| `f12-clean-de` | de | BSc | Fully compliant **German** control — the corpus contains no compliant German proposal at all. Tests canonical de section titles, de citation locale, Review staying silent. |
| `f13-pure-slr` | en | MSc | Pure Systematic Literature Review with its required subsections (search strategy / quality assessment and extracted information / synthesis) — corpus only has SLR *mixed* with interviews (f05). Exercises that branch of the methodology→subsection table. |
| `f14-user-study` | de | BSc | Pure User Study (preparation / procedure / analysis) — methodology entirely absent from the corpus. |
| `f17-theoretical` | en | BSc | Pure Theoretical Analysis (formalization / requirements / example) — corpus theoretical proposals (f03, f08) are free-form and defect-laden; the compliant branch is untested without this. |
| `f15-format-broken` | en | BSc | Trailing-YAML guardrail fixture: missing blank line before `---`, boolean-literal citation key (`on`), duplicate metadata block, leftover `[TODO: …]`, exactly 2 references ([references] min_count boundary), a three-word title (below the English `min_words` bound), and the only fixture keeping an `author:` key — it owns the anonymity tripwire. Tiny file, pure Check-mechanics oracle. |
| `f16-figures-import` | en | MSc | Invented PDF containing two figures — the corpus is nearly figure-free, so Import's `img/`-TODO path has no ground truth without it. |
| `f19-drift-alert-validity` | en | MSc | Session-derived (see `docs/demo/harvest.log`): skills-generated clean-with-TODOs proposal, 15 verified references, citation inside RQ2 — the pattern that broke the publish rq-filter; no other fixture covers either trait. |
| `f20-timeline-gantt` | en | MSc | Isolates the timeline size guard: a Gantt table under an otherwise-correct `Timeline` heading, with nothing else wrong. The guard replaced the deleted `timeline`/`zeitplan` forbidden-heading patterns, and f02 only exercises it amid five other defects. |
| `f21-bad-title` | en | BSc | Isolates the thesis-title rule: a mechanically clean body under a title that trips two deterministic tells (implementation opener, buzzword) and carries the two the patterns cannot reach (a platform name as the instrument, an employer name). The only fixture where a title finding stands alone — f08 and f15 each trip one title tell amid their other defects, and every remaining title is silent to the deterministic tells (f22's is deliberately field-vague, an agent-judgement class). The `semantic` block carries the abstracted alternative. |
| `f22-hollow-generic` | en | BSc | Isolates the substance-vs-mechanics split: zero check errors and zero warnings by construction, yet every sentence fails the guidelines' swap test — no object of study, no delta, no falsifiable outcome, and a field-vague title. Exists to prove "mechanically clean" carries no substance signal; the review skill must answer it with the no-viable-core verdict. The `semantic` block lists the failed substance tests by name. |
| `f23-controlled-experiment` | en | MSc | Clean proposal on the Controlled Experiment branch (hypotheses and variables / design and participants / statistical analysis) — the only fixture exercising that methodology→subsection row. Models the contract: hypotheses named before variables, manipulated and measured variables separated, tests derived from a within-subjects design. |
| `f24-model-evaluation` | en | MSc | Clean proposal on the Empirical Model Evaluation branch (data and baselines / experimental setup / analysis) — the only fixture exercising that row. Models the contract: dataset provenance and licensing, published detectors as baselines, leakage-aware temporal splits, metrics tied to the research questions, seed variance reported. |
| `f25-case-study` | en | MSc | Clean proposal on the Case Study branch (case and units of analysis / data collection / analysis) — the only fixture exercising that row. Models the contract: typical-case selection rationale, units of analysis inside one case, three triangulated sources, host-organisation consent, single-case limitation stated. Adapted from the proposal that lived in w04 while Case Study was still a workspace-declared branch. |

Workflow-state fixtures (not proposals, but required test states):

- `w01-ideate-seed` — an Ideate-produced skeleton (idea notes, candidate RQ bullets, empty `references:`) as Write's starting state.
- `w02-override-workspace` — a workspace with `guidelines.md` whose TOML block sets `[timeline] detail = "detailed"` and `[references] min_count = 8`; oracle for override precedence in Write/Check/Customize, with one key relaxing (the phase table passes) and one tightening (3 references still fail) in the same file. It is also the only fixture demonstrating the override key shape, which mirrors `structure.json`'s key paths.
- `w03-snowball-seed` — a proposal with three solid references; oracle for lit-search snowballing expansion.
- `w04-methodology-branch` — a workspace whose `guidelines.md` declares an `Action Research` branch (with per-subsection guidance) and disables the shipped `theoretical` one, plus a clean proposal using that branch. Positive control for workspace-configurable methodologies: no shipped branch has this subsection set, so a pass proves the declaration was merged rather than ignored, and any finding at all means the merge broke. Declared Case Study until that branch was promoted into the shipped defaults, which made the old declaration prove nothing.
- `w05-workspace-build` — a workspace holding a clean proposal and a `proposal-build.py` beside it. Oracle for publish's handover: the presence of a build definition makes the built-in pipeline unreachable, so publish names it and exits 3 without writing a document or an ignore entry. The proposal itself is deliberately uninteresting — it is still built on every tier by the export matrix, which is what proves a build definition beside a proposal does not disturb the shipped pipeline, so any check finding here means the fixture drifted rather than that delegation broke.
- `s01-raw-email` — a raw submission (`s` prefix): a synthetic student email pasted as-is (`submission-email.txt` — deliberately not `.md`, so the corpus-wide "every proposal builds and has an oracle" invariants skip it), with fake personal data (Erika Musterfrau, matriculation 00000000), an implementation-goal idea, blog-post sources, and a work plan. Input for the supervise L1 task, which asserts none of the personal data reaches the send-package. Not a proposal, so no `expected.json`.
- `g01-research-group` — not a workspace state but a synthetic *web* fixture (`g` prefix): a fictional research-group homepage (`group.html`) plus a canned DBLP-shaped `dblp.json`, served over localhost for the ideate scoping preamble. Not a proposal, so no `expected.json`. The page carries a deliberate prompt-injection canary (`CANARY-B715`) that the scoped-ideation verdict asserts never reaches produced files.

## Coverage checks

- Languages: 4× de, 7× en → thin out or duplicate per language as needed; every tier exists in both languages across the set.
- Levels: 7× BSc, 4× MSc. Tiers: 2 low, 4 mid, 3 mid-high/high, 2 high.
- Every deterministic Check rule has ≥1 fixture that trips it and ≥1 that passes it (f05 = clean control).
- Every Review rubric dimension (RQ quality, single method, gap argument, vendor grounding, structure-silence) has a dedicated fixture.
- Import robustness: f03 (Word-style, personal data to strip), f09 (LLM artifacts, missing metadata), f11 (LaTeX-clean) get PDF renderings.
- Ideate personas cross-reference: f01/f08 profiles ("no RQs, narrative idea") mirror the hesitant/over-scoped student personas.

## Production rules

1. Write fixtures from this blueprint only — never translate/copy sentences from the corpus; invent all prose fresh around the seeded defects.
2. Personal data in fixtures is obviously fake (e.g. `Erika Musterfrau`, matriculation `00000000`).
3. Each proposal fixture ships with an `expected.json` (per-fixture ground truth: which mechanical defects Check must report, which semantic defects the rubric expects) — that file is the L1/L2 oracle. `g`-prefix web fixtures carry none.
