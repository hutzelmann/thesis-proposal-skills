# Proposal

## Why

The only documented way to install the skills is a terminal command, `npx skills add hutzelmann/thesis-proposal-skills`. It needs Node.js ≥ 22.20 and git, which most students lack. The getting-started page then walks through two terminal agents. Students who use ChatGPT, or the Claude or ChatGPT desktop apps, find no instructions at all.

Research on 2026-10-03 (23 skill repositories, the agentskills.io standard, Agent Plugins 1.0, skills.sh) shows:

- **No standard covers installation.** Every app leaves it to itself.
- **What popular repositories lead with:** a plugin marketplace in Claude's format, which several apps read, or the skills CLI.
- **The free desktop route for ChatGPT users:** the ChatGPT desktop app's Codex view runs local skills and can install them itself.
- **Problems with the skills CLI under an agent:**
  - it installs into the current folder unless told otherwise;
  - it scatters agent directories across the home folder;
  - it reports false failures while exiting 0.

The maintainer's requirement is to install from the desktop, cover ChatGPT, make it simpler and less error-prone, and let the agent do the work.

## What Changes

- **Universal paste-prompt.** One install prompt the student pastes into any local agent. The agent:
  0. stops with a pointer to the chat-only section when it runs in a cloud sandbox, a VM or a chat-only app, where an install would vanish with the conversation;
  1. checks for Python ≥ 3.11, stopping with per-OS install guidance if it is missing;
  2. asks the student "all your projects (recommended) or only this folder?";
  3. downloads and runs the repository's own `install.py`;
  4. relays what the script printed;
  5. tells the student to reload or open a new chat.

  The agent installs no software and touches no skill file itself. The prompt is single-sourced in `shared/blocks/` and materialized into the README and the install guide.
- **`install.py` at the repository root.** It is user-side: Python ≥ 3.11 standard library only, cross-platform, `main(argv)`. It:
  - fetches the default branch's archive;
  - copies every shipped `proposal-*` folder byte-identically into the scope's directories:
    - `--scope all` → `~/.agents/skills` and `~/.claude/skills`, plus the Antigravity or Kiro directory when that app is present;
    - `--scope folder` → `.agents/skills` and `.claude/skills` in the working directory;
  - writes an install record (`.thesis-proposal-install.json`: commit, date, scope, directories) beside the skills.

  `--scope` is mandatory. The installer refuses to install beside a plugin install of the same skills. It reports copies in the other scope and removes them only with `--remove-other`. It runs no skill script, and uses a skill name as a path only when it matches the shipped `proposal-*` pattern: a record lies in the folder the student opened, so it is untrusted input. Re-running it is the update, and it prints the old and new commit.
- **Plugin button, Claude only for now.** One file, `.claude-plugin/marketplace.json`, defines a `thesis-proposal` marketplace and plugin. It ships only `skills/` and follows the default branch, so Claude desktop on paid plans installs all eleven skills in one step. Codex/ChatGPT, VS Code and the Copilot app would need a root manifest with a pinned version, so they install through the prompt until a later change adds one. The plugin route and a copied install are documented as mutually exclusive.
- **One install guide, `docs/install.md`.**
  - A "which app do you use?" table.
  - Short recipes for:
    - ChatGPT desktop (Codex view, free plan)
    - Claude desktop
    - VS Code / the Copilot app
    - Antigravity
    - Cursor

    Each recipe is stamped "verified <date>, <app version>" once a maintainer has run it. An unrun recipe stays out.
  - A flagged section for chat-only apps (claude.ai or Claude desktop chat, the Gemini app, ChatGPT web). It states what works and what breaks there, and redirects to the plugin button or to a free desktop agent.
  - A "Literature search cannot reach its sources" section naming the API domains, each app's network switch, and the macOS certificate step.
  - A terminal section for `npx skills add`.

  `docs/getting-started.md` folds into it. The README quick start shrinks to: open your app in a folder, paste the prompt or use the plugin button, ask for a thesis idea. One "prefer a terminal?" line keeps the npx command.
- **Troubleshoot follows the routes.**
  - Rung 0 is route-neutral: it reads the install record and names the update route (re-paste the prompt / the plugin page's "Check for updates" / `npx skills update`).
  - `check.py` is vendored into `proposal-troubleshoot` as a synchronized copy. This retires the hardcoded `.claude/skills/proposal-check/…` path, which breaks under user-level and plugin installs, and the README divergence row that justified it.
  - The collector reads the install record, scans the new install roots and plugin caches, and reports the install route.
- **Supporting text and tools follow.**
  - The issue template, the harness's troubleshoot eval prompt (and its generated `evals.json` projection), and `harness/README.md` become route-neutral.
  - The claim "the installed skills carry no version" is replaced by the install record.
  - The README's "For supervisors" section gains a brief note on provisioning a cohort through Claude's organization plugin sync, the one app that can load the plugin today. It names ChatGPT Edu and Copilot organizations as not yet able to. This is documentation only, within the portability boundary.
  - `poe install-check` additionally installs the tracked tree through `install.py` from a `git archive` zip.
  - A dev-runner probe pastes the prompt into Claude Code: once unanswered, to check the scope question is asked, and once pre-answered, to check the install lands.
- **Out of scope:**
  - per-skill ZIP uploads for chat-only apps (a later change, after one real upload settles the 200-character description limit);
  - listings in the Anthropic, OpenAI, Cursor or Antigravity directories (publishing, explicit request only).

## Capabilities

### New Capabilities
- `installation`: the install prompt, the `install.py` installer (scope, directories, record, conflicts, update, Python precondition), and the plugin definition — how the skill set reaches a student's machine without a terminal.

### Modified Capabilities
- `skill-packaging`: changes three requirements.
  - "Registry installation from the repository" now names three routes instead of the skills.sh CLI alone: prompt+installer, plugin, and CLI.
  - "Installation verified against the tracked tree" now also covers the repository installer, besides the README's CLI command.
  - "User-side script constraints": a script another skill owns ships as a synchronized copy and is addressed through the skill-directory variable, never by an install path.
- `user-onboarding`: the README quick start carries the install prompt. Concrete agent walkthroughs become a per-app install guide with verified stamps and a flagged chat-only section. The update-first step and the issue template become route-neutral. Supervisors learn about cohort provisioning.
- `skill-troubleshoot`: the stale-install rung reads the install record and names the update route, instead of asserting that installs carry no version. Install identification adds the install record and the plugin and user-level roots beside the lock record and hashes.
- `testing-harness`: a dev-runner probe for the install prompt.

## Impact

- **New files:** `install.py`, `shared/blocks/install-prompt.md`, `docs/install.md`, `.claude-plugin/marketplace.json`, and `skills/proposal-troubleshoot/scripts/check.py` (generated).
- **Changed:**
  - `README.md`, `AGENTS.md` (eleven skills; install notes), `CONTRIBUTING.md` if it names the install
  - `skills/proposal-troubleshoot/SKILL.md` and `scripts/collect.py`
  - `scripts/sync_shared.py` (new SYNC_MAP entry; the prompt block materialized into documents)
  - `scripts/install_check.py`, `.github/workflows/install.yml`, `.github/ISSUE_TEMPLATE/skill-defect.yml`
  - `harness/skill_evals.py`, `harness/claude_runner.py`, `harness/README.md`
  - `skills/proposal-troubleshoot/evals/evals.json` (generated)
  - `pyproject.toml` (pythonpath, coverage source)
- **Removed:** `docs/getting-started.md` (folded into `docs/install.md`).
- **Tests:**
  - new: `tests/unit/test_install.py`, `test_plugin_manifests.py`, `test_install_docs.py`, `test_install_probe.py` (with recorded probe outcomes under `tests/unit/data/install_probe/`);
  - updated: `test_install_check.py`, `test_sync.py`, `test_troubleshoot_collect.py`, `test_repo_conventions.py` (the root installer is scanned), and `test_script_paths.py`, which now forbids every install-path script reference.
- **Release:** the change stays off `main` until the maintainer has run each featured recipe once. Once merged, plugin installs follow `main` automatically, so a bad push reaches plugin users without any action on their part. This is consistent with the rolling-release policy, but it is new exposure.
