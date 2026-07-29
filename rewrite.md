# The Big Rewrite — Plan

Transform this repository from an AI-boosted LaTeX template into **`thesis-proposal-skills`**: an agent-agnostic set of skills (distributed via [skills.sh](https://skills.sh/)) that helps students ideate, research, write, check, review, and publish thesis proposals. Users never touch this repository — they install the skills into their own proposal workspace and work only on their proposals. This repository exists solely to develop and test the skills.

## Locked Decisions

| # | Decision |
|---|----------|
| D1 | Distribution via skills.sh; repo renamed `thesis-proposal-skills`; all skills prefixed `proposal-*`. *(Verified)* skills.sh installs straight from the committed git repo (`npx skills add <owner>/thesis-proposal-skills`, selective via `--skill proposal-write`, updates via `npx skills update`); the installed directory name is the sanitized frontmatter `name:` — so the `proposal-` prefix must be in each SKILL.md's `name:` field, and same-named skills from other repos silently overwrite, making the prefix mandatory. |
| D2 | One proposal = one source file with a content-derived slug name (`ml-code-review.md`), never a generic `proposal.md`. Markdown text on top, **trailing** pandoc YAML metadata block at the bottom (`title`, `author`, `subtitle`, `lang`, `references:` in CSL-YAML). Citations as `[@key]` (or in-text `@key` for author-in-prose, the `\citeauthor` equivalent). Consumed natively by pandoc + citeproc — no custom parsing. *(Verified on pandoc 3.10; minimum pandoc ≥ 3.0, floor set by the typst writer.)* Format guardrails enforced by Check: a blank line must precede the trailing `---` (otherwise pandoc silently treats the YAML as body text); exactly one metadata block per file; citation keys must not be YAML boolean literals (`yes`, `no`, `on`, `off`, `true`, `false`, `y`, `n`). |
| D3 | User workspace is flat: many unrelated proposals side by side. Figures are rare; shared `img/` folder created only when needed, filenames slug-prefixed. Slug grammar: lowercase ASCII, hyphen-separated, 2–4 words derived from the title, numeric suffix on collision. Tests assert the pattern, not an exact name. |
| D4 | Languages: English (default) and German, switched per proposal via `lang: en|de` *(verified: affects babel, typst `text(lang:)`, and the citeproc CSL locale)*. German uses English scientific terms with German capitalization; the **canonical German section titles are fixed in `shared/`** so deterministic checks work for `lang: de`. |
| D5 | Guidance defaults ship inside the skills; a user-owned `guidelines.md` in the workspace overrides/extends them. Its format is two-part: a machine-readable fenced **TOML** block (`required_sections`, `forbidden_sections`, `page_limit`, `min_references`, …) parsed with stdlib `tomllib` and consumed by the deterministic check script, plus freeform prose for agent-level guidance. Merge semantics, specified once in `shared/` and honored by Write, Check, Review, and Ideate alike: user keys win per key; lists replace rather than append; un-forbidding a default-forbidden section is allowed. The Customize skill manages this file. |
| D6 | Dev-side single source of truth in `shared/`; a sync script copies it into each skill's `references/` **and** emits a machine-readable `structure.json` into proposal-check and proposal-ideate. The same mechanism vendors the lit-search scripts into proposal-ideate, keeping every skill self-contained for per-skill installs. Copies are committed (skills.sh installs from the repo) and a test fails when out of sync. **Formalization boundary:** `structure.json` holds *only* what the deterministic check consumes — canonical section titles (en+de), order, the methodology→required-subsections table, forbidden-heading patterns, `min_references`, RQ list conventions. All semantic rules (analytical RQs, high-level introduction, explicit delta to prior work, tone, redundancy) stay prose — the agents' authority; the prose points to `structure.json` for names/lists instead of restating them, and an L0 drift guard asserts every title in `structure.json` appears verbatim in the prose. |
| D7 | Skill scripts are Python 3 **stdlib-only** on the user side (Windows/Mac/Linux, zero pip installs), floor **Python ≥ 3.11** (for `tomllib`). Stdlib has no YAML parser, so scripts never general-parse YAML: the proposal's metadata block is read via narrow, documented extraction (citation `- id:` lines and a few scalars); structured config is JSON (`structure.json`) or TOML (override block). Dev-side tooling may use real dependencies (managed with `uv`). Every script-bearing skill (not just Publish) detects missing tools — including `python3` vs `py` on Windows — and gives install guidance; if the agent's sandbox denies script networking, the SKILL.md instructs the agent to fall back to its own fetch/browse tools against the same API URLs. |
| D8 | Publishing is **optional** — handing in the markdown file is acceptable. Quick start has zero build dependencies. For hand-ins without any tooling, Publish also offers a stripped export (references reduced to citation-ready entries, abstracts removed) so the supervisor-facing file is not half bibliography database. |
| D9 | PDF pipeline is typst-first: pandoc → typst → PDF (two single-binary installs). Fallbacks: LaTeX engine if present, then docx. The typst template gets fidelity priority when porting the `compactarticle.cls` look. A chosen `.csl` style file replicates the compact citation style (max one citation per bracket). |
| D10 | Workflow order: **Ideate ⇄ Literature Search → Write → Check → Review → Publish**. Ideation is literature-grounded: check early whether the idea is already solved or has poor academic literature match. Import is a side entry; Customize is orthogonal. Check is **advisory**: Review and Publish run it first and surface failures, but proceed on user confirmation — it gates nothing hard. |
| D11 | Testing: full pyramid (unit / structural / rubric-judged), hybrid with **inverted roles**. **Authoritative runs go through OpenRouter** (native Inspect providers, native `--model` matrix axis incl. Claude models, full token accounting, judge on the same key): model-matrix comparisons, release gates, and optional CI smoke runs (`OPENROUTER_API_KEY` secret, spend caps). **Subscription `claude -p` (Opus/Sonnet/Haiku) is the cheap everyday dev runner** for interactive skill iteration — free marginal cost, not the source of record. CI always runs unit tests + lint; metered eval runs stay budget-capped and mostly on-demand. |
| D12 | Test framework: pytest as the frame; Inspect AI as the candidate eval engine (spike S1). No `make`; entry points via `uv run pytest`. |
| D13 | No personal data or real proposals in the repo — fixtures are realistic dummies derived from real proposals by extraction + rewriting. Real PDFs stay untracked and gitignored. |
| D14 | Proposal targeting in the flat workspace: skills take the proposal file as an explicit argument/mention; when ambiguous, the agent lists candidate files (markdown files ending in a pandoc metadata block — the shared detection heuristic) and asks. A single candidate is auto-picked. |
| D15 | Workspace hygiene: whichever skill *first creates* an ignorable artifact (build outputs, intermediates, the API-key file) ensures the corresponding `.gitignore` entry at creation time — not only Publish. |
| D16 | Releases: rolling default branch while the tool has no outside users; introduce tagged releases (main = dev) once it does. `npx skills update` tracks the repo, so what is merged is what users get. |
| D17 | Spec sync via **OpenSpec** (`@fission-ai/openspec`, v1.7+, dev-side only — Node ≥ 20.19; user installs it themselves). `openspec/specs/` is the living source of truth once implementation starts; this plan document seeds the initial specs and then becomes historical. Every implementation unit runs the loop `/opsx:propose` (change folder with proposal/design/tasks + spec deltas) → human review → `/opsx:apply` → `openspec archive` (validates + merges ADDED/MODIFIED/REMOVED deltas into `specs/`). Spec-less refactors declare `skip_specs: true`. `openspec validate --all --strict` joins the L0/CI checks. |

## Proposal File Format

```markdown
# Machine Learning for Automated Code Review

Software quality assurance relies on code review [@Smith26Deep].
As @Smith26Deep argue, manual review does not scale.
[TODO: sharpen the motivation with a concrete cost figure]
...

---
title: Machine Learning for Automated Code Review
author: Jane Doe
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Smith26Deep
  type: article-journal
  author: [{family: Smith, given: A.}]
  issued: {year: 2026}
  title: Deep Learning for Code Review
  DOI: 10.1234/example
  abstract: ...
---
```

Conventions:

- Section structure follows the guidance (Introduction to the Topic; Contribution to the State-of-the-Art; Research Focus and Research Questions; Methodology for Research: \<Methodology\>).
- Research questions are an ordered list under the research-questions section; templates style them, the check script counts and validates them.
- Citation rules carried over from the legacy guidance: `[@key]` bracketed, `@key` for author-in-text; no citation of the same work in consecutive sentences (author-in-text first, then stop repeating); no fabricated sources.
- Placeholders use visible `[TODO: 3–10 word hint]` markers — greppable by the check script, visible in any output.
- Reference entries carry abstract, authors, year, DOI when available; URL only when no DOI exists.

## The Eight Skills

1. **proposal-ideate** — Socratic idea development. Never asks directly for missing input; lets the user talk, gives hints and suggestions to refine. Interleaves literature lookups (via its vendored copies of the lit-search scripts, per D6) to ground the idea academically: is it already solved, does relevant literature exist, how does it differ from prior work? Degrades gracefully (states it is working ungrounded) if lookups are unavailable. Ends by seeding `<slug>.md`: working title, problem sketch, candidate RQ directions as notes, open questions as TODOs, YAML block with starter references.
2. **proposal-lit-search** — Academic literature only, multi-source (CS-focused for a start). One stdlib script per source, results merged and deduplicated by DOI/normalized title. Two modes: **keyword search** and **snowballing** (given seed papers from `references:`, expand backward via their reference lists and forward via citing papers + recommendations — the open-graph replacement for the classic Scopus "cited by" workflow). Source tiers *(terms verified 2026-07, re-check in S6)*:
   - **Keyless core** (always works): **Semantic Scholar Graph API** (abstracts where licensed, TLDR, `references`/`citations`/recommendations endpoints; used keyless — shared throttled pool with 429-tolerant backoff suffices at proposal-scale volumes, and its unique contributions are nice-to-haves; no key requested since keys expire and need an extensive application; attribution required, never bundle cached data), **DBLP** (CS-primary: authoritative venues/authors, CC0, no abstracts), **Crossref** (proper CSL author/date fields, DOI validation, open outgoing reference lists, ≤10 req/s via mailto), **OpenCitations** (pure citation graph both directions, CC0, ~180 req/min, no abstracts), **arXiv** (CS preprint abstracts, ~1 req/3 s).
   - **Key-gated upgrades** (free keys, env vars): **OpenAlex** (abstracts via `abstract_inverted_index` + `referenced_works`/`cites:`/`related_works`; key mandatory since 2026-02 — conflicting docs exist, re-verify), **CORE** (OA full text, instant key) later.
   - **Institutional BYO-key adapters** (later, off by default): **Scopus** (needs institutional entitlement + campus network; per-student local calls are the ToS-compatible pattern), **IEEE Xplore** (key approval, ~200 calls/day, institution-bound ToS). **ACM DL has no API** — its metadata, references, and citation counts flow through Crossref/OpenCitations/S2/OpenAlex; its abstracts come from S2/OpenAlex.
   Script-design notes: reconstruct OpenAlex abstracts from the inverted index (often null); prefer Crossref `family`/`given` for CSL authors (OpenAlex/S2 names are unsplit); Crossref `title`/`container-title` are arrays and abstracts are JATS XML needing tag-stripping; S2 recommendations may be empty for a given paper. The agent judges actual relevance (not keyword hits), prefers peer-reviewed venues over preprints, dedupes against existing `references:`, and writes CSL-YAML into the proposal file. Source list extensible per discipline later.
3. **proposal-write** — Writes from scratch or refines, following default guidance + workspace `guidelines.md`. Literature-grounded; never fabricates sources; leaves `[TODO: …]` for missing information.
4. **proposal-import** — Takes an existing proposal (usually PDF), extracts text and references; outputs one file in the standard format with gaps marked as TODOs. **Strips personal data on import** (matriculation numbers, addresses, emails, supervisor names — real proposals carry these routinely) and drops forbidden content (timelines, chapter outlines) with a note listing what was removed. Robust to Word-, LaTeX-, and LLM-produced PDFs (formatting artifacts, swallowed headings, missing title blocks). Relies on the agent's native PDF reading (documented capability requirement); if the agent cannot read PDFs, it guides the user to provide text. Figures are **not** auto-extracted (agents read pages, they don't export embedded images): Import leaves `[TODO: re-add figure from page N as img/<slug>-….png]` markers, and uses `pdfimages`/`mutool` when detected (same detect-and-guide rule as Publish).
5. **proposal-check** — Low-level advisory gate, results in chat only. Deterministic script driven by `structure.json` + workspace TOML overrides: required sections present with canonical titles, exactly one methodology from the closed set with its required subsections, forbidden headings absent, every declared RQ referenced as `(RQn)` in the methodology, `[@key]`/`@key` ↔ `references:` consistency in both directions, duplicate keys, `min_references` met, leftover TODOs, D2 format guardrails (blank line before trailing `---`, single metadata block, no boolean-literal keys). Warning-class regex checks (known false positives, never hard failures): first-person pronouns, three consecutive same-word sentence starts, email/matriculation-number patterns, and confidentiality markers ("confidential", "internal use only", "do not distribute", "NDA", "vertraulich", "nur für den internen Gebrauch", …) — theses get published, so proposals must not carry or promise confidentiality (warning-class because e.g. "confidentiality of user data" as a research topic is legitimate). Output reports honestly in two buckets — "verified mechanically" vs. "flagged for the agent pass" — and never claims semantic rules passed. Agent pass for typos/grammar and content-level forbidden material (e.g. expected results hidden in prose).
6. **proposal-review** — High-level content review: structure of argument, soundness, missing literature/information, sharpness, redundancy, inconsistencies. Explicitly format-agnostic — never complains about section layout or markup. Output: enumerated, actionable issues written to `<slug>-review.md` (overwritten per run), in the proposal's `lang`. If obvious grammar/spelling problems exist, the review ends with a *hint* plus one or two examples — never an exhaustive list (that is Check's job). `ai-feedback.md` seeds the rubric and example tone.
7. **proposal-publish** — pandoc build per D9. Ships templates (`proposal.typ` primary, `proposal.latex`, `reference.docx`, compact `.csl`). Detects missing tools and gives install guidance. Outputs PDF + intermediate source next to the proposal; ensures the workspace `.gitignore` covers all build artifacts; offers the stripped hand-in export (D8).
8. **proposal-customize** — Dialog-driven creation/editing of workspace `guidelines.md` ("my supervisor wants a timeline section", "max 3 pages"). Writes the structured TOML block + prose per D5, validates conflicts against defaults (e.g. lifting a default-forbidden section), and explains consequences.

## Repository Layout (target)

```
thesis-proposal-skills/
  skills/
    proposal-ideate/{SKILL.md, references/, scripts/}   # references/ + scripts/ synced from shared/
    proposal-lit-search/{SKILL.md, scripts/}            # source of the lit scripts
    proposal-write/{SKILL.md, references/}
    proposal-import/SKILL.md
    proposal-check/{SKILL.md, scripts/, references/}    # structure.json synced from shared/
    proposal-review/{SKILL.md, references/}
    proposal-publish/{SKILL.md, scripts/, templates/}
    proposal-customize/{SKILL.md, references/}
  openspec/                # D17: living specs (specs/) + change workflow (changes/), managed by OpenSpec
  shared/guidelines/       # single source of truth: structure + writing rules + canonical de titles
  scripts/sync_shared.py   # syncs guidance, structure.json, and vendored scripts into skills
  harness/                 # eval setup: Inspect tasks + OpenRouter providers (authoritative); claude -p dev wrapper
  tests/
    unit/                  # L0: pytest, no model
    structural/            # L1: per skill × per model, deterministic artifact asserts
    rubric/                # L2: model-graded quality (RQ quality, Socratic compliance, review actionability)
    personas/              # simulated students for multi-turn Ideate tests
    fixtures/              # dummy proposals, en + de, various completeness states
  docs/getting-started.md  # concrete agent setup walkthroughs (examples, not endorsements)
  README.md                # for AI newcomers: concept, workflow, npx skills add
  pyproject.toml           # uv-managed dev environment
  LICENSE.txt              # MIT, unchanged
```

### `scripts/sync_shared.py`

Reconciles "devs edit one source" with "skills.sh installs each skill self-contained": one-way, deterministic materialization of `shared/` into the skills — prose guidelines into the `references/` of write, review, customize, and ideate; `structure.json` into check and ideate; the lit-search scripts vendored into ideate. Generated files carry a `GENERATED — edit shared/ instead` header and are **committed** (skills.sh serves the repo as-is; there is no publish pipeline to run builds). No timestamps or other nondeterminism in output. `--check` mode (formatter-style) runs in L0/CI and fails on drift.

## Testing Strategy

- **L0 unit (CI + local):** pytest over all python scripts — check logic, per-source API parsing, narrow metadata extraction, TOML override parsing, `sync_shared.py --check` consistency, and the `structure.json`↔prose drift guard. No model calls.
- **L1 structural (local, per model):** run each skill against fixture workspaces; assert deterministic outcomes — file created matching the slug grammar, YAML parses as CSL, citations resolve, forbidden sections absent, review file written.
- **L2 rubric (local, per model):** model-graded scoring against rubrics distilled from the guidance and `ai-feedback.md`: are RQs analytical rather than implementation goals, is the review actionable, did Ideate stay Socratic (never asked directly), German quality.
- **Ideate** is tested multi-turn with persona files simulating students (hesitant Bachelor student, over-scoped idea, idea already solved in literature). Persona-driver and grader models must be named as part of S1.
- **Runners (inverted hybrid, per D11):** authoritative = Inspect over OpenRouter — Claude and external models (e.g. DeepSeek) on the native `--model` axis; matrix breadth is a budget knob, not an auth constraint. Dev loop = `claude -p --model {opus,sonnet,haiku}` on the Max subscription for fast, free iteration while developing skills. The generic agent loop for non-Claude models comes via Inspect's tooling rather than a hand-rolled harness where possible.
- Fixtures cover English and German, both levels, and all quality tiers per `fixtures-blueprint.md` — 11 synthetic proposals seeding the corpus-derived failure taxonomy (no RQs, implementation-goal RQs, uncited bibliographies, forbidden sections, personal data, mixed methodologies, one clean control), each with an `expected.json` ground-truth oracle for L1/L2.

## Migration Steps

Work happens directly on `main` in this workspace — no feature branches, no worktrees; commit as the refactoring progresses (consistent with D16's rolling-main policy while there are no outside users).

**Step 0 — spec bootstrap (D17):** the user installs OpenSpec (`npm install -g @fission-ai/openspec@latest`) and runs `openspec init --tools claude` in this repo. First change: seed `openspec/specs/` from this plan's decisions and skill specs (proposed via `/opsx:propose`, reviewed, archived). From then on every migration step and spike below runs as an OpenSpec change, keeping specs in sync with the implementation.

**Phase 0 — de-risk (before any conversion):** run remaining spikes S1 and S3. *(S2 and S4 already resolved — see below.)* Split step 8 into harness-spike → L0 → L1 → L2 sub-milestones, with S1 as the harness precondition.

1. Rename repo to `thesis-proposal-skills`; transform in place, keep git history.
2. Extract `AGENTS.md` into `shared/guidelines/` — keep structure rules, RQ criteria, methodology subsections, writing rules, and the citation-usage rules (author-in-text form, no consecutive-sentence repetition); fix the canonical German section titles; drop LaTeX-specific mechanics, replacing them with the markdown/CSL conventions above.
3. Convert `proposal.tex` (Jane Doe dummy) into the first English fixture in the new format; convert `literature.bib` entries to CSL-YAML.
4. Port the `compactarticle.cls` look into `templates/proposal.typ` (primary) and `templates/proposal.latex`; pick/adapt a compact `.csl`; then delete the class file.
5. Turn `ai-feedback.md` into the Review rubric + example output. Build the fixture set from `fixtures-blueprint.md` (11 synthetic fixtures with per-fixture `expected.json` oracles, designed from an analyzed private corpus of real proposals — corpus stays untracked in `confidential/`; blueprint production rules forbid copying any original prose).
6. Replace the LaTeX `.gitignore` with one for the new repo (python, uv, test artifacts, real-proposal PDFs); delete `.vscode/`, `build/`.
7. Rewrite `README.md` for AI newcomers per D8/onboarding; add `docs/getting-started.md`.
8. Build the harness + test pyramid per Phase 0 sub-milestones; seed with the fixtures; wire `uv run pytest` entry points.
9. Publish to skills.sh; verify install + skill discovery end-to-end in a scratch workspace (`npx skills add`, selective `--skill`, `npx skills update`).

## Spikes & Risks

- **S1 — eval harness integration (open, reshaped by D11's inverted hybrid):** Inspect AI confirmed for OpenRouter (native provider) and model-graded scoring with cross-model comparison — that is now the authoritative path, so the nonstandard glue is off the critical path. Spike tasks: (a) wire OpenRouter providers + judge and run one end-to-end L1/L2 eval with spend caps; (b) validate that `inspect-swe`'s `claude_code()` agent bridge works when backed by an OpenRouter-served Claude model (the bridge reroutes all model calls through the configured Inspect provider — verified fact; OpenRouter as that provider is the remaining unknown), giving real-binary tests with full accounting; (c) decide how thin the subscription dev runner needs to be — likely a plain `claude -p` wrapper script outside Inspect entirely, since it is no longer the source of record. Caveat kept on record: the bridge **cannot use Max-subscription auth** (proxy breaks OAuth), which is exactly why subscription runs stay dev-only. Fallback if Inspect underdelivers: DeepEval (pytest-native, swappable judge).
- ~~**S2 — pandoc trailing YAML block**~~ **Resolved:** verified by live test on pandoc 3.10 and the manual — trailing metadata block + CSL-YAML `references:` + `--citeproc` works natively, including the typst writer and `lang: de` locale switching. Minimum pandoc ≥ 3.0. Guardrails moved into D2/Check.
- **S3 — typst template fidelity (open):** reproduce the compact layout (title block, margins, RQ styling) in typst; define the RQ list styling without LaTeX's custom environment.
- ~~**S4 — skills.sh mechanics**~~ **Resolved:** multi-skill repos, selective install, symlink-based multi-agent mapping (70+ agents), `npx skills update`, and install-from-committed-repo all confirmed against the CLI source. Consequence folded into D1 (prefix in frontmatter `name:`; silent overwrite on collisions).
- **S5 — PDF reading across agents (open):** Claude Code reads PDFs natively; verify the degradation path for agents that cannot (Import must fail helpfully). Figure auto-extraction already descoped (see skill 4).
- **S6 — literature API keys (needs careful design):** verified 2026-07 — OpenAlex requires a key since 2026-02-13 (free tier: single lookups free, ~1k searches/day; HTTP 409 when exhausted; mailto/polite-pool deprecated — though some docs still describe keyless access, re-verify at build time); Semantic Scholar works keyless but throttled (shared pool, 429s under load; its free key expires quickly and needs an extensive application — deliberately not used, keyless + backoff is the design); DBLP, arXiv, Crossref, OpenCitations remain keyless. Design rules: (1) the default install works keyless on the core tier — keys only *improve* abstracts/coverage/rate, never gate core functionality; (2) **agent-guided key setup**: skills proactively offer to walk the user through obtaining free keys (S2, OpenAlex, CORE) — explain the concrete benefit, point to the signup URL, tell the user exactly where to put the key (env var or a gitignored workspace key file read by the scripts — decide format in this spike), then validate it with a test call; (3) skills detect missing/exhausted keys (429/409) and degrade to the remaining sources with a clear note. Institutional keys (Scopus, IEEE) follow the same guided pattern but stay opt-in and are never suggested to users without institutional access.
- **Risk — literature API availability/rate limits:** scripts need polite headers, retry, and a clear offline error path; a failing source degrades to the remaining ones, never blocks the search.
- **Risk — German output quality** on non-Claude models: covered by de-fixtures in L2; models that fail stay off the recommended list.
