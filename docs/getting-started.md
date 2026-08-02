# Getting Started (from zero)

You need three things: an AI agent, a folder for your proposals, and the skills. This page covers two concrete agent setups. They are **examples, not endorsements**; the skills work with 70+ agents (anything supporting the SKILL.md standard).

## Option A: Claude Code

Terminal-based agent by Anthropic. Paid subscription or API billing.

1. Install [Node.js](https://nodejs.org) (LTS).
2. `npm install -g @anthropic-ai/claude-code`
3. Create your proposal folder and start the agent inside it:
   ```sh
   mkdir my-proposals && cd my-proposals
   claude
   ```
   Follow the login prompt on first start.
4. Install the skills (new terminal, same folder):
   ```sh
   npx skills add ignacioalvmar/thesis-proposal-skills
   ```
5. In the agent chat: *"Help me develop a thesis idea."*

## Option B: GitHub Copilot CLI

[Free for verified students](https://github.com/education/students) via the GitHub Student Developer Pack.

1. Get the student pack, then install [Node.js](https://nodejs.org) and:
   ```sh
   npm install -g @github/copilot
   ```
2. Create your folder, start it, log in:
   ```sh
   mkdir my-proposals && cd my-proposals
   copilot
   ```
3. Install the skills: `npx skills add ignacioalvmar/thesis-proposal-skills`
4. Ask: *"Help me develop a thesis idea."*

## What you get in the folder

- `your-topic-name.md` is the exposé: text on top, title-page details and literature at the bottom. This is the only file you edit (or let the agent edit).
- `your-topic-name-review.md` appears when you ask for a review.
- `guidelines.md` appears if you customize the rules for your supervisor.
- `your-topic-name-expose/` appears when you publish: the LaTeX project (`expose.tex`, `literature.bib`, `images/`) you upload to Overleaf.
- `img/` appears only if your proposal uses figures.

Useful prompts: *"Find literature for my proposal"*, *"Check my proposal"*, *"Review it like a supervisor would"*, *"My supervisor wants at least 15 sources, adjust the rules"*, *"Build my exposé"*.

## Notes

- Your proposals stay on your machine; literature search talks to public academic APIs (DBLP, Crossref, arXiv, and others). Optional free API keys improve abstract coverage; the agent offers to walk you through the signup and stores the key in a small `api-keys.env` file in your folder (kept out of version control).
- English is the default; say *"auf Deutsch"* and the whole proposal switches to German conventions.
- Writing and publishing need no extra software. The publish skill writes a LaTeX project folder; you upload it to [Overleaf](https://www.overleaf.com) (New Project → Upload Project) and Overleaf compiles the PDF. If you already have TeX Live or MiKTeX you can compile locally instead with `pdflatex → bibtex → pdflatex → pdflatex`.
- The exposé follows the [THI exposé template](https://github.com/ignacioalvmar/thesis_expose_template). Its title page needs your student ID, degree program, supervisor, and submission date — tell the agent and it stores them in the file's metadata, never in the body text.
