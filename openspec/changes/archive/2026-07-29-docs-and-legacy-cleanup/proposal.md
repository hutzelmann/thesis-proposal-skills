# Proposal: docs-and-legacy-cleanup

## Why

Last migration steps (6, 7, and the remainder of 2/4): the repository still carries the LaTeX-era files (`proposal.tex`, `compactarticle.cls`, `literature.bib`, `AGENTS.md`, `.vscode/`, `build/`, LaTeX `.gitignore`) and the old template README. The user-onboarding spec requires a newcomer-ready README plus concrete getting-started walkthroughs; the packaging spec requires the repo to present the skills as the product.

## What Changes

- New `README.md` per the user-onboarding spec: what this is, the workflow, zero-build quick start, install via GitHub (skills.sh listing deferred per decision), contributor section pointing at specs/tests.
- `docs/getting-started.md`: copy-paste setup for two example agents.
- Delete legacy: `proposal.tex`, `compactarticle.cls`, `literature.bib`, `AGENTS.md`, `.vscode/`, `build/`, `ai-feedback.md` reference in docs (file itself stays untracked).
- Replace the LaTeX `.gitignore` with a clean one (python/dev + build noise; fixture PDFs stay tracked).
- `skip_specs: true` — implements user-onboarding/packaging requirements.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- Repo presents as `thesis-proposal-skills`; legacy template reachable via tag `legacy-latex-template`.
