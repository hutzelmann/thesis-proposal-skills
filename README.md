# Thesis Proposal Skills

Write a convincing Bachelor's or Master's thesis proposal with the help of an AI agent — in English or German.

This repository contains a set of **agent skills**: instruction packages that teach an AI coding agent (Claude Code, Cursor, Codex, and many others) how to guide you from a vague idea to a polished, literature-grounded proposal. You install the skills once; afterwards you only ever work on your own proposal files, in your own folder. You never need to touch this repository.

**Never used an AI agent before?** Start with [docs/getting-started.md](docs/getting-started.md) — it walks you through installing an agent from zero.

## What the skills do

| Skill | What it does for you |
|---|---|
| `proposal-ideate` | Develops your rough idea with you — Socratic questions, early literature checks ("is this already solved?") — and captures the result in a proposal file. |
| `proposal-lit-search` | Finds real, relevant academic literature (DBLP, Crossref, arXiv, OpenCitations, Semantic Scholar, OpenAlex) — by topic or by snowballing from papers you already have. |
| `proposal-write` | Writes or refines the proposal following proven structure and writing rules — never inventing facts or references. |
| `proposal-import` | Converts an existing proposal (usually a PDF) into the workable format, stripping personal data. |
| `proposal-check` | Fast mechanical check: required sections, citation consistency, forbidden content, leftover TODOs. |
| `proposal-review` | Supervisor-style content review with numbered, actionable suggestions. |
| `proposal-publish` | Optional: builds a compact PDF via pandoc + typst. A plain markdown hand-in is fine too. |
| `proposal-customize` | Adapts everything to your supervisor's requirements ("timeline required", "max 3 pages"). |

Your whole proposal lives in **one file**: readable text on top, literature entries at the bottom. Many proposals can sit side by side in one folder.

## Quick start

Nothing to compile, no LaTeX required:

1. Get an AI agent (see [docs/getting-started.md](docs/getting-started.md) if you don't have one).
2. Create a folder for your proposals and open your agent in it.
3. Install the skills:
   ```sh
   npx skills add hutzelmann/thesis-proposal-skills
   ```
4. Tell your agent: *"Help me develop a thesis idea"* — or *"Import my existing proposal from proposal.pdf"*.

Typical flow: **ideate → literature search → write → check → review → publish** — but every skill also works on its own. PDF building is optional; install `pandoc` + `typst` only when you want it (the publish skill tells you how).

## For supervisors

The skills encode conservative academic guidance: analytical research questions (not implementation goals), a single methodology, explicit contribution over the state of the art, no fabricated references, visible TODO markers for every gap. Students can adapt the rules to your requirements with `proposal-customize` — the defaults forbid timelines, personal data, and expected-results sections.

## For contributors (this repository)

This repo is **only** for developing and testing the skills — user proposals never live here.

- Specs are the source of truth: `openspec/specs/` (managed with [OpenSpec](https://github.com/Fission-AI/OpenSpec); every change runs propose → review → apply → archive).
- `shared/` holds the single-source guidance; `scripts/sync_shared.py` materializes it into the skills (CI-checked).
- Tests: `uv run pytest` (L0, no model calls) · `harness/` (L1/L2 model evals, see `harness/README.md`).
- Fixtures in `tests/fixtures/` are synthetic — no real proposals, no personal data.

MIT licensed. Issues and PRs welcome — please open an issue first.
