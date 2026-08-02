# Thesis Proposal Skills

Write a convincing Bachelor's or Master's thesis proposal with the help of an AI agent, in English or German.

A real agent session, condensed — a student turns a work anecdote into a proposal:

![A student asks whether their anecdote about a silently degrading churn model could become a thesis; the ideate skill answers with a sharpening Socratic question](docs/demo/shot1.png)
![The literature-search skill builds a base of 15 verified references and rejects noise instead of force-fitting it](docs/demo/shot2.png)
![The check skill verifies the written proposal mechanically, then the publish skill builds the PDF](docs/demo/shot3.png)

This repository contains a set of **agent skills**: instruction packages that teach an AI coding agent (Claude Code, Cursor, Codex, and many others) how to guide you from a vague idea to a polished, literature-grounded proposal. You install the skills once; afterwards you only ever work on your own proposal files, in your own folder. You never need to touch this repository.

**Never used an AI agent before?** Start with [docs/getting-started.md](docs/getting-started.md), which walks you through installing an agent from zero.

## What the skills do

| Skill | What it does for you |
|---|---|
| `proposal-ideate` | Develops your rough idea with you through Socratic questions and early literature checks (is this already solved?), then captures the result in a proposal file. |
| `proposal-lit-search` | Finds real, relevant academic literature (DBLP, Crossref, arXiv, OpenCitations, Semantic Scholar, OpenAlex), by topic or by snowballing from papers you already have. |
| `proposal-write` | Writes or refines the proposal following proven structure and writing rules. It never invents facts or references. |
| `proposal-import` | Converts an existing proposal (usually a PDF) into the workable format and strips personal data. |
| `proposal-check` | Fast mechanical check: required sections, citation consistency, forbidden content, leftover TODOs. |
| `proposal-review` | Supervisor-style content review with numbered, actionable suggestions. |
| `proposal-publish` | Builds the exposé: an Overleaf-ready LaTeX project from the THI template — `expose.tex`, `literature.bib`, `images/` — with your work plan drawn as a Gantt chart. Needs nothing installed. |
| `proposal-customize` | Adapts everything to your supervisor's requirements ("at least 15 sources", "no separate Timeline section", "max 8 pages"). |

Your whole exposé lives in **one file** while you work on it: readable text on top, title-page details and literature entries at the bottom. Many exposés can sit side by side in one folder. When you are ready, `proposal-publish` turns that file into the [THI exposé template](https://github.com/ignacioalvmar/thesis_expose_template) as a folder you upload to Overleaf — you never edit LaTeX by hand.

## Quick start

1. Get an AI agent (see [docs/getting-started.md](docs/getting-started.md) if you don't have one).
2. Create a folder for your proposals and open your agent in it.
3. Install the skills:
   ```sh
   npx skills add ignacioalvmar/thesis-proposal-skills
   ```
4. Tell your agent: *"Help me develop a thesis idea"*, or *"Import my existing proposal from proposal.pdf"*.

The typical flow is ideate, then literature search, then write, check, review, and finally publish. Every skill also works on its own. Publishing needs nothing installed: it writes a LaTeX project you upload to Overleaf, which compiles it for you.

## For supervisors

The skills produce an exposé in the structure of the [THI exposé template](https://github.com/ignacioalvmar/thesis_expose_template): Introduction and Motivation, Problem Statement and Research Questions, Objectives, Related Work, Methodology, Expected Contributions and Results, Work Plan and Schedule. Publishing emits that template as an Overleaf project, so what you receive is the document you already expect.

The guidance is conservative where it matters: one to three analytical research questions (construction goals belong in Objectives), exactly one declared methodology, an explicit gap statement in Related Work, at least ten sources, no fabricated references, and a visible TODO marker for every gap. Personal data stays in the title-page metadata and out of the body. Students can adapt the rules to your requirements with `proposal-customize`.

The methodology set covers Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Simulation Study, Empirical Model Evaluation, and Mixed Methods. Work combining a qualitative and a quantitative strand declares Mixed Methods, whose Integration subsection must say which research questions each strand answers — stacking two methodology sections is still flagged. For studies with human participants the guidance asks for ethics route, informed consent, and GDPR handling in a couple of sentences; this is advisory prose, not an enforced section.

## For contributors (this repository)

This repo is **only** for developing and testing the skills. User proposals never live here.

- Specs are the source of truth: `openspec/specs/`, managed with [OpenSpec](https://github.com/Fission-AI/OpenSpec). Every change runs propose, review, apply, archive. Agent integration files are not committed; run `openspec init --tools <your-agent>` once locally (and `openspec update` after CLI upgrades).
- `shared/` holds the single-source guidance; `scripts/sync_shared.py` materializes it into the skills. Activate the pre-commit hook once per clone with `git config core.hooksPath .githooks` — it re-materializes and stages the copies on every commit; CI's `--check` catches bypassed hooks.
- Tests: `uv run pytest` runs L0 without model calls; `harness/` holds the L1/L2 model evals (see `harness/README.md`).
- Fixtures in `tests/fixtures/` are synthetic: no real proposals, no personal data.

MIT licensed. Issues and PRs welcome; please open an issue first.

## Credits

Originally created by **Thomas Hutzelmann** (Technische Hochschule Ingolstadt) for computer-science thesis supervision. This fork is maintained by the **[Human-Centered Intelligent Systems (HCIS) Lab](https://ignacioalvmar.com)** at THI / AImotion Bavaria, which retargets the guidance and the test corpus to research at the intersection of applied AI, intelligent systems engineering, and human-computer interaction — adding controlled-experiment, simulation-study, empirical-model-evaluation, and mixed-methods branches to the methodology set.
