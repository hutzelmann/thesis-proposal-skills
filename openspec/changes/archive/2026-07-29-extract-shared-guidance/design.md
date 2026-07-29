# Design: extract-shared-guidance

## Context

See proposal.md. Sources: legacy `AGENTS.md` (guidance content), guidance-model spec (behavior), skill-packaging spec (sync/self-containment).

## Decisions

- **D-ESG-1 — Canonical German section titles** (fixing the guidance-model requirement):
  - Einführung in das Thema · Beitrag zum Stand der Technik · Forschungsfokus und Forschungsfragen · Forschungsmethodik: \<Methode\>
  - Methodologies: Prototypimplementierung · Theoretische Analyse · Systematische Literaturrecherche · Nutzerstudie
  - Subsections: Vorarbeiten · Anforderungen · Evaluation | Formalisierung · Anforderungen · Beispiel | Suchstrategie und Auswahlkriterien · Extrahierte Informationen · Synthese | Vorbereitung · Durchführung · Analyse
- **D-ESG-2 — `structure.json` is the source directly** (no YAML intermediate): dev-side source format equals the user-side consumed format; sync copies verbatim. One format, zero transformation bugs.
- **D-ESG-3 — Sync destination map** lives in `sync_shared.py` as a plain dict: `guidelines.md` → write/review/customize/ideate `references/`; `structure.json` → check/ideate `references/`; lit-search scripts → ideate `scripts/` (activated once those scripts exist).
- **D-ESG-4 — GENERATED header** as an HTML comment for .md (invisible in rendering) and a top-level `"_generated"` key for .json.
- **D-ESG-5 — Forbidden headings as patterns**: case-insensitive substring/regex list covering en+de variants (timeline/Zeitplan/workplan/Arbeitsplan/milestones/Meilensteine, expected results/erwartete Ergebnisse, thesis structure/Gliederung, supervisor/Betreuer, deliverables).

## Risks / Trade-offs

- Prose and structure.json both list section titles → mitigated by the drift-guard L0 test (title must appear verbatim in prose).
- German title choices are my best academic-German judgment; user review at change review catches disagreements cheaply.
