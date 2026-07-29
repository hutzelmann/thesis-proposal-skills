# Fixture Corpus

Reference for the synthetic test fixtures in this directory (the "fixture blueprint" the testing-harness spec refers to). The designs were informed by a private corpus of real student proposals (11 documents, mixed quality); nothing here maps to an identifiable original: topics are altered, all names and institutions removed, defect patterns generalized. Each fixture directory holds one proposal file plus an `expected.json` oracle calibrated against the check script.

## Corpus-derived failure taxonomy (aggregate, anonymized)

| Pattern | Frequency | Tested by |
|---|---|---|
| No research questions at all | ~4/11 | Check (RQ section empty), Write/Ideate (must elicit) |
| RQs phrased as implementation goals ("how can X be built") | dominant where RQs exist | L2 rubric, Review |
| Bibliography present but never cited in-text | ~6/11 | Check (defined-but-uncited warning) |
| < 3 scientific references / URL-only bibliographies | ~4/11 | Check (min_references), lit-search |
| Mixed methodologies in one proposal | ~4/11 | Review rubric (single-method rule) |
| Forbidden content: timelines/Gantt, chapter outlines, expected results | very common | Check (forbidden headings) |
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
| `f02-tool-comparison` | de | BSc | mid | Motivation/Objective/Work-steps + Gantt | mech: forbidden timeline heading, 2 URL-only refs (< min), no RQs; sem: evaluative goal never sharpened into questions |
| `f03-compliance-audit` | en | BSc | mid-high | numbered free-form incl. chapter outline + timetable, personal data on cover | mech: forbidden chapter-structure + timetable headings, matriculation/address patterns, work-package pseudo-RQs; sem: RQs are work packages, typos |
| `f04-dsr-vendor-heavy` | de | MSc | mid | TOC/abbreviations, 1 main + 4 sub-RQs, chapter outline | mech: forbidden outline, supervisor + matriculation on title page, duplicate reference entry, "vertraulich" title-page stamp; sem: vendor pages ground definitional claims, RQ sub-questions design-phrased |
| `f05-slr-interviews` | en | MSc | high | canonical 4 sections | mech: clean (control fixture); sem: mixed methodology (SLR + interviews) violating single-method rule, missing interview-ethics note |
| `f06-prototype-testbed` | en | BSc | mid-high | canonical 4 sections | mech: forward-dated reference year; sem: passive-heavy evaluation, 4-campaign scope risk without fallback, no architecture figure despite hardware topic |
| `f07-network-pathfinding` | en | BSc | mid | custom Scope/Requirements/RQ/Approach/Schedule | mech: forbidden schedule, supervisor named, 2 refs; sem: 3 of 4 RQs implementation-goal, one leading RQ, mid-document first-person switch, typos |
| `f08-concept-sketch` | de | BSc | low | Abstract/Intro/Objective/Solution/Work-steps | mech: no RQs, no real bibliography (prose URL list), no in-text markers; sem: severe passive, goals as construction aims, unfalsifiable "concept" outcome |
| `f09-llm-compliance-docs` | en | MSc | high | near-canonical, work-plan table | mech: forbidden work-plan heading, no title/author metadata, refs never cited in-text, swallowed-heading formatting artifact (Import robustness); sem: 3 "which…" RQs lacking degree phrasing, mixed method |
| `f10-risk-scoring` | en | MSc | mid | free-form with supervisor block | mech: supervisor names + emails, undated phase table, refs never cited in-text, "confidential — internal use only" footer marker; sem: 2 of 4 RQs implementation-goal, none operationalized, evaluation leans on internal feedback |
| `f11-migration-architecture` | de | BSc | high | canonical + extra Scope/Summary sections | mech: extra non-canonical sections (warning), vendor-doc references; sem: RQ2 is yes/no, requirements read as spec list — near-target quality, tests that Review stays quiet on structure |

## Beyond-corpus fixtures (invented — no workspace source)

The corpus leaves real coverage holes; these fixtures are designed from the rules alone:

| id | lang | level | purpose |
|---|---|---|---|
| `f00-clean-en` | en | MSc | Fully compliant control, converted from the legacy Jane Doe `proposal.tex` (migration step 3) — the only workspace-sourced entry here, listed for completeness. |
| `f12-clean-de` | de | BSc | Fully compliant **German** control — the corpus contains no compliant German proposal at all. Tests canonical de section titles, de citation locale, Review staying silent. |
| `f13-pure-slr` | en | MSc | Pure Systematic Literature Review with its required subsections (search strategy / extracted information / synthesis) — corpus only has SLR *mixed* with interviews (f05). Exercises that branch of the methodology→subsection table. |
| `f14-user-study` | de | BSc | Pure User Study (preparation / procedure / analysis) — methodology entirely absent from the corpus. |
| `f17-theoretical` | en | BSc | Pure Theoretical Analysis (formalization / requirements / example) — corpus theoretical proposals (f03, f08) are free-form and defect-laden; the compliant branch is untested without this. |
| `f15-format-broken` | en | BSc | Trailing-YAML guardrail fixture: missing blank line before `---`, boolean-literal citation key (`on`), duplicate metadata block, leftover `[TODO: …]`, exactly 2 references (min_references boundary). Tiny file, pure Check-mechanics oracle. |
| `f16-figures-import` | en | MSc | Invented PDF containing two figures — the corpus is nearly figure-free, so Import's `img/`-TODO path has no ground truth without it. |
| `f19-drift-alert-validity` | en | MSc | Session-derived (see `docs/demo/harvest.log`): skills-generated clean-with-TODOs proposal, 15 verified references, citation inside RQ2 — the pattern that broke the publish rq-filter; no other fixture covers either trait. |

Workflow-state fixtures (not proposals, but required test states):

- `w01-ideate-seed` — an Ideate-produced skeleton (idea notes, candidate RQ bullets, empty `references:`) as Write's starting state.
- `w02-override-workspace` — a workspace with `guidelines.md` whose TOML block un-forbids the timeline and sets `min_references = 8`; oracle for override precedence in Write/Check/Customize.
- `w03-snowball-seed` — a proposal with three solid references; oracle for lit-search snowballing expansion.

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
3. Each fixture ships with an `expected.json` (per-fixture ground truth: which mechanical defects Check must report, which semantic defects the rubric expects) — that file is the L1/L2 oracle.
