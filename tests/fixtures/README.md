# Fixture Corpus

Reference for the synthetic test fixtures in this directory (the "fixture blueprint" the testing-harness spec refers to). The designs were informed by a private corpus of real student proposals (11 documents, mixed quality); nothing here maps to an identifiable original: topics are altered, all names and institutions removed, defect patterns generalized. Each fixture directory holds one proposal file plus an `expected.json` oracle calibrated against the check script.

Fixture topics sit in the HCIS Lab's research area — automated driving, automotive HMI, in-cabin AI, driver state, V2X, and AV safety.

The corpus was restructured a second time when the skills adopted the THI exposé template (<https://github.com/ignacioalvmar/thesis_expose_template>): seven sections instead of four, `min_references = 10`, at most three research questions, and work plans, timelines, and expected results promoted from forbidden content to required sections. Fixtures whose seeded defect *was* a forbidden work-plan heading therefore lost it; each carries a replacement defect (a schedule at month rather than week granularity, which the Gantt renderer cannot draw) recorded in its `semantic` notes. `f19` keeps both its original topic and the old four-section shape, and is now the oracle for detecting a legacy-shape exposé.

## Corpus-derived failure taxonomy (aggregate, anonymized)

| Pattern | Frequency | Tested by |
|---|---|---|
| No research questions at all | ~4/11 | Check (RQ section empty), Write/Ideate (must elicit) |
| RQs phrased as implementation goals ("how can X be built") | dominant where RQs exist | L2 rubric, Review |
| Bibliography present but never cited in-text | ~6/11 | Check (defined-but-uncited warning) |
| < 3 scientific references / URL-only bibliographies | ~4/11 | Check (min_references), lit-search |
| Undeclared mixed methods (a second strand smuggled into another branch's subsections) | ~4/11 | Review rubric (one-declared-methodology rule) |
| More than three research questions | recurring in MSc topics | Check (`max_count`), Review |
| Schedule present but not at week granularity | very common | Publish (Gantt renderer degrades to a plain table and says so) |
| Forbidden content: chapter outlines, supervisor sections, deliverable lists | very common | Check (forbidden headings) |
| Personal data: matriculation numbers, addresses, supervisor names/emails | common | Check (warning regexes), Import (strip on import) |
| Passive voice pervasive (esp. German), first-person narrative slips | near-universal (de) | Check warnings, Review hint |
| Confidentiality markers ("confidential", "vertraulich", NDA remarks) in industry-context proposals | recurring in corporate topics | Check warning (theses get published) |
| Free-form section structures (Goal/Work-steps, Scope/Approach, …) | majority | Check (canonical sections), Import (restructure) |
| Vendor/commercial sources grounding core claims | recurring | Review rubric, lit-search venue preference |
| Human-subjects work with no ethics, consent, or data-handling note | recurring in study-based topics | Review (missing substance) — advisory only, never a Check error |
| Figures | nearly absent (0–1 per proposal) | confirms D3 (img/ optional) |
| PDF production variety: Word, LaTeX, LLM-assisted (formatting artifacts, swallowed headings, missing title blocks) | across corpus | Import robustness |

## Corpus-derived fixtures

Each fixture = one proposal file in the single-file format (plus, for Import tests, a rendered PDF variant). `seeded defects` split into **mechanical** (Check must flag deterministically) and **semantic** (L2 rubric / Review must catch). Topics are synthetic.

| id | lang | level | tier | shape | seeded defects |
|---|---|---|---|---|---|
| `f01-narrative-sketch` | de | BSc | low | free-form "Goal / Work steps" narrative — in-car voice assistant for older drivers | mech: no canonical section present, no in-text citations, 3 refs (< min); sem: first-person storytelling, no gap argument, unfalsifiable outcome |
| `f02-tool-comparison` | de | BSc | mid | Motivation/Objective/Work-steps + Gantt — gaze-tracking toolkit comparison | mech: no canonical sections except a coincidental Zielsetzung, 2 URL-only refs (< min), no RQs; sem: evaluative goal never sharpened into questions, month-granularity Zeitplan the Gantt renderer cannot draw |
| `f03-compliance-audit` | en | BSc | mid-high | numbered free-form incl. chapter outline + timetable, personal data on cover — ODD-compliance auditing of drive logs | mech: forbidden chapter-structure heading, matriculation/address patterns, work-package pseudo-RQs, 3 refs (< min); sem: RQs are work packages, typos, month-granularity timetable |
| `f04-dsr-vendor-heavy` | de | MSc | mid | TOC/abbreviations, 1 main + 4 sub-RQs, chapter outline — driver-monitoring rollout reference model | mech: forbidden outline + Betreuer headings, matriculation, duplicate reference entry, "vertraulich" stamp, 4 RQs over the limit of 3, 5 refs (< min); sem: vendor pages ground definitional claims, RQ sub-questions design-phrased |
| `f05-slr-interviews` | en | MSc | high | canonical 7 sections — trust calibration in partially automated driving | mech: clean (control fixture); sem: undeclared mixed methods (interviews smuggled into the SLR Synthesis instead of declaring Mixed Methods), missing interview-ethics note |
| `f06-prototype-testbed` | en | BSc | mid-high | canonical 7 sections — driver-monitoring latency testbed | mech: forward-dated reference year; sem: passive-heavy evaluation, 4-campaign scope risk without fallback, no architecture figure despite hardware topic |
| `f07-network-pathfinding` | en | BSc | mid | custom Scope/Requirements/RQ/Approach/Schedule — V2X collective-perception rate control | mech: forbidden Supervisor heading, no canonical sections, 2 refs (< min); sem: 3 of 4 RQs implementation-goal, one leading RQ, mid-document first-person switch, typos |
| `f08-concept-sketch` | de | BSc | low | Abstract/Intro/Objective/Solution/Work-steps — shuttle stop information display | mech: no RQs, no canonical sections, no references block at all; sem: severe passive, goals as construction aims, unfalsifiable "concept" outcome |
| `f09-llm-compliance-docs` | en | MSc | high | near-canonical, work-plan table — LLMs for AV safety-case documentation | mech: Objectives / Related Work / Expected Contributions absent, a non-canonical "Work Plan" title, no title/author metadata, refs never cited in-text, 3 refs (< min), swallowed-heading formatting artifact (Import robustness); sem: 3 "which…" RQs lacking degree phrasing, undeclared mixed methods |
| `f10-risk-scoring` | en | MSc | mid | free-form with supervisor block — fleet driver risk scoring | mech: forbidden Supervisors heading with emails, no canonical sections, undated phase table, refs never cited in-text, 3 refs (< min), "confidential — internal use only" marker; sem: 2 of 4 RQs implementation-goal, none operationalized, evaluation leans on internal feedback, telematics personal data with no consent route |
| `f11-migration-architecture` | de | BSc | high | canonical 7 sections + extra Abgrenzung/Zusammenfassung — ECU-to-SDV architecture migration | mech: clean; sem: vendor-doc references, sem: RQ2 is yes/no, requirements read as spec list — near-target quality, tests that Review stays quiet on structure |

## Beyond-corpus fixtures (invented — no workspace source)

The corpus leaves real coverage holes; these fixtures are designed from the rules alone:

| id | lang | level | purpose |
|---|---|---|---|
| `f00-clean-en` | en | MSc | Fully compliant Prototype Implementation control — LLM-based scenario generation for AD validation. Descended from the legacy Jane Doe `proposal.tex` (migration step 3). |
| `f12-clean-de` | de | BSc | Fully compliant **German** control — the corpus contains no compliant German proposal at all. Tests canonical de section titles, de citation locale, Review staying silent. Topic: formal safety-envelope analysis under perception uncertainty. |
| `f13-pure-slr` | en | MSc | Pure Systematic Literature Review with its required subsections (search strategy / extracted information / synthesis) — corpus only has SLR *mixed* with interviews (f05). Topic: XAI for driver state monitoring. |
| `f14-user-study` | de | BSc | Pure User Study (preparation / procedure / analysis) — exploratory think-aloud study of eHMI interpretation by pedestrians. Also carries the advisory ethics/consent/GDPR sentences a clean human-subjects proposal is expected to have. |
| `f17-theoretical` | en | BSc | Pure Theoretical Analysis (formalization / requirements / example) — reference-frame type system for perception code. The compliant branch is untested without this. |
| `f20-simulation-study` | en | MSc | Pure Simulation Study (scenario design / execution / analysis) — occlusion-aware safety envelope. Also the oracle for the "state the validity limit of simulated evidence" rule. |
| `f21-empirical-evaluation` | de | MSc | Pure Empirical Model Evaluation (data and baselines / experimental setup / analysis), in German — gaze estimation under spectacle reflections. Reports baselines, seeds, and an ablation. |
| `f22-mixed-methods` | en | MSc | Pure Mixed Methods (qualitative strand / quantitative strand / integration) — in-vehicle voice-command repair. The compliant counterpart to f05's and f09's undeclared mixing. |
| `f15-format-broken` | en | BSc | Trailing-YAML guardrail fixture: missing blank line before `---`, boolean-literal citation key (`on`), duplicate metadata block, leftover `[TODO: …]`, exactly 2 references (min_references boundary). Tiny file, pure Check-mechanics oracle. |
| `f16-figures-import` | en | MSc | Invented PDF containing two figures — the corpus is nearly figure-free, so Import's `img/`-TODO path has no ground truth without it. Topic: perception-alarm triage. |
| `f18-broken-refs` | en | BSc | Reference-resolution oracle for Import: one real paper with a resolving DOI (VERIFIED), one real paper with no DOI (ENRICHED by title match), one non-resolving DOI and one wholly invented entry (both UNVERIFIABLE). The two real entries are network-verified; keep `Dey19Gaze` at the Crossref short title, since the subtitle breaks the match. |
| `f19-drift-alert-validity` | en | MSc | Session-derived (see `docs/demo/harvest.log`): skills-generated clean-with-TODOs proposal, 15 verified references, citation inside RQ2 — the pattern that broke the publish rq-filter; no other fixture covers either trait. **Deliberately not re-domained**: its value is that every sentence and reference traces to a recorded real session, so changing the topic means recording a new one. |

Workflow-state fixtures (not proposals, but required test states):

- `w01-ideate-seed` — an Ideate-produced skeleton (idea notes, candidate RQ bullets, one starter reference) as Write's starting state. Topic mirrors the `anecdote-master` persona (drowsiness-label reliability).
- `w02-override-workspace` — a workspace with `guidelines.md` whose TOML block un-forbids the timeline and sets `min_references = 8`; oracle for override precedence in Write/Check/Customize. Proposal body is `f00` plus a Timeline section.
- `w03-snowball-seed` — a proposal with three solid references carrying real resolvable DOIs; oracle for lit-search snowballing expansion. Doubles as the compliant **Controlled Experiment** fixture (design and hypotheses / procedure / statistical analysis).

## Coverage checks

- Languages: 8× de, 18× en across the 26 fixture directories; every tier exists in both languages.
- Every deterministic Check rule has ≥1 fixture that trips it and ≥1 that passes it (f05 = clean control).
- Every methodology branch has a compliant fixture: Prototype Implementation (f00), Theoretical Analysis (f17, f12), Systematic Literature Review (f13), User Study (f14), Controlled Experiment (w03), Simulation Study (f20), Empirical Model Evaluation (f21), Mixed Methods (f22). Every branch begins with Use Case Definition.
- Publish coverage: f00 and every compliant fixture render to a LaTeX project whose work-plan table becomes a Gantt chart; f01, f02, f03, and f10 exercise the degrade-to-plain-table path.
- Every Review rubric dimension (RQ quality, one declared methodology, gap argument, vendor grounding, structure-silence) has a dedicated fixture.
- Import robustness: f03 (Word-style, personal data to strip), f09 (LLM artifacts, missing metadata), f11 (LaTeX-clean) get PDF renderings. **These PDFs are stale as of the 2026-08 re-domaining** — they still render the pre-re-domaining prose. Regenerate with `python3 skills/proposal-publish/scripts/publish.py <fixture>.md` once pandoc and typst are installed, then move the output next to the fixture.
- Ideate personas cross-reference: f01/f08 profiles ("no RQs, narrative idea") mirror the hesitant/over-scoped student personas.

## Production rules

1. Write fixtures from this blueprint only — never translate/copy sentences from the corpus; invent all prose fresh around the seeded defects.
2. Personal data in fixtures is obviously fake (e.g. `Erika Musterfrau`, matriculation `00000000`).
3. Reference DOIs are the fake `10.xxxx/…` form, so no fabricated title is ever attached to a real DOI. The two exceptions are deliberate and documented: `f18-broken-refs` and `w03-snowball-seed` carry real, network-verified entries because their tests depend on real resolution behaviour.
4. Compliant fixtures carry at least ten references and cite every one of them. Where a fixture is deliberately under-referenced (`f15`, `f18`, `w01`, `w03`), the resulting `min_references` error is pinned in its oracle and explained in its `semantic` notes.
5. Each fixture ships with an `expected.json` (per-fixture ground truth: which mechanical defects Check must report, which semantic defects the rubric expects) — that file is the L1/L2 oracle.
6. Re-domaining a fixture must preserve its seeded defects exactly; `uv run pytest tests/unit/test_fixture_oracles.py` is the gate. Where a pinned reference id or TODO string changes, update `expected.json` in the same commit.
