# Retarget the Skills to HCIS Lab Research

## Why

The repository was built for computer-science thesis supervision with a software-engineering and security centre of gravity: the fixture corpus is dominated by cloud compliance, zero-trust, intrusion detection, and microservice topics, and the closed methodology set assumes a thesis is either an artifact, a proof, a review, or a study. Under new ownership the skills serve the Human-Centered Intelligent Systems (HCIS) Lab at THI / AImotion Bavaria, whose students work at the intersection of applied AI, intelligent systems engineering, and human-computer interaction.

Three gaps follow from that shift. There is no methodology branch for a hypothesis-driven experiment with human participants, for a scenario-based simulation campaign, or for a benchmark comparison of models — the three shapes most HCIS theses actually take, currently forced into `Prototype Implementation` or `User Study`. The blanket rule "never combine methodologies" contradicts standard practice in human-computer interaction, where a qualitative and a quantitative strand routinely answer different research questions in one thesis. And the guidance says nothing about ethics approval, informed consent, or personal-data handling, despite `User Study` being one of only four available branches.

Ownership metadata (install command, HTTP user-agent, CSL style id, licence) still points at the original author's repository, which now resolves to the wrong project.

## What Changes

- **Extend the methodology set from four branches to eight**: add `Controlled Experiment` (design and hypotheses / procedure / statistical analysis), `Simulation Study` (scenario design / execution / analysis), `Empirical Model Evaluation` (data and baselines / experimental setup / analysis), and `Mixed Methods` (qualitative strand / quantitative strand / integration), each with canonical English and German titles.
- **Replace the single-methodology prohibition with a one-declared-methodology rule**: combining a qualitative and a quantitative strand is legitimate, but it declares `Mixed Methods` and uses that branch's subsections. Stacking two methodology sections, or smuggling a strand into another branch's subsections, remains a violation. Review judges the Integration subsection hardest, since it is what separates mixed methods from two unrelated small studies.
- **Add advisory human-participant guidance**: ethics route, informed consent, GDPR handling, risk bounding, and compensation, as prose inside the existing subsections. Deliberately *not* a required section and *not* mechanically enforced — the check script gains no new error, so a proposal omitting it still exits clean and only the content review may raise it.
- **Add literature guidance the domain needs**: published standards (ISO, IEEE, ETSI, SAE, UNECE) are legitimate sources for normative definitions but never evidence that an approach works; venue families for relevance judgement across the HCI, machine-learning, and intelligent-systems literatures.
- **Re-domain the fixture corpus and the ideate personas** into automated-driving, automotive-HMI, in-cabin-AI, driver-state, V2X, and AV-safety topics, preserving every fixture's seeded mechanical defects so the `expected.json` oracles still hold. Add compliant fixtures for the four new branches.
- **Re-point ownership**: install command, user-agent, CSL style id, and licence, crediting Thomas Hutzelmann as original author.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the canonical-structure requirement lists eight methodologies instead of four; the "mixed methodologies" scenario is replaced by a two-methodology-sections scenario plus a scenario routing combined strands to the Mixed Methods branch. New requirement — human-participant research guidance, explicitly advisory: it SHALL NOT introduce a required section and the mechanical check SHALL NOT enforce it.
- `skill-review`: the semantic rules the review covers now read "one declared methodology" rather than "single methodology", and add the Integration-subsection substance check for declared Mixed Methods proposals.

Unchanged: `skill-check` already specifies "exactly one methodology from the closed set with its required subsections", which stays literally true — the set grew, the rule did not. `testing-harness` already requires a fixture per methodology branch; the new branches inherit that obligation.

## Impact

- `shared/structure.json`: four new methodology entries with en/de titles and subsections; `scripts/sync_shared.py` materializes them into `skills/proposal-check/references/`.
- `shared/guidelines/guidelines.md`: title table, methodology-content section, branch-selection guidance, human-participant section, literature guidance. Every new title must appear verbatim (enforced by `tests/unit/test_structure_drift.py`).
- `skills/proposal-review/SKILL.md`: single-methodology bullet rewritten; scope-risk split into its own bullet so an added strand is flagged on merit rather than by category.
- `tests/fixtures/`: 23 fixtures re-domained, 3 added (`f20-simulation-study`, `f21-empirical-evaluation`, `f22-mixed-methods`); 8 `expected.json` oracles updated where a pinned reference id or TODO string changed. `f19-drift-alert-validity` is deliberately left alone — it is traceable to the recorded session in `docs/demo/`.
- `tests/unit/test_check.py`: hardcoded fixture filenames and content strings updated.
- `harness/`: persona files re-domained; fixture filenames in `skill_evals.py` and `claude_runner.py` updated.
- `scripts/sync_shared.py`: bug fix — the GENERATED header used `Path.relative_to` directly, emitting backslashes on Windows, so `--check` failed on any Windows clone and a Windows sync would have rewritten the committed headers.
- `LICENSE.txt`, `README.md`, `docs/getting-started.md`, `skills/proposal-lit-search/scripts/common.py`, `skills/proposal-publish/templates/compact-numeric.csl`: ownership.

## Known Follow-ups

- The four fixture PDF renderings (`f03`, `f09`, `f11`, `f16`) still contain pre-re-domaining prose; regenerating them needs pandoc and typst, which are not installed in the environment where this change was implemented. No automated test consumes them.
- `docs/demo/` (storyboard, transcript, screenshots) and the `f19` fixture derived from it remain on the original machine-learning-monitoring topic. Re-domaining them requires recording a new real agent session, which the `demo-recording` spec forbids substituting with invented output.
