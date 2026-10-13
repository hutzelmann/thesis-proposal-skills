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

**Revision, 2026-10-13.** A student's setup report (Windows, OpenCode) exposed three gaps in what this change already shipped to `main`:

- **Python that exists is reported missing.** The prompt tries only `python3`, `python` and `py -3`. On a machine whose only Python came from uv, all three fail ("Python was not found" from the Store shortcut), so the agent tells the student to install a Python they already have. `py -3` also misses Anaconda's.
- **Interpreter hints are scattered and incomplete.** Six script-bearing skills carry their own Windows hint (`py` instead of `python3`, seven sentences); none names a versioned interpreter such as `python3.14`; lit-search and troubleshoot carry none; proposal-check prescribes `winget install Python.Python.3.12`.
- **Manual copies shadow installed ones.** OpenCode loads its own skill folders after the shared `.claude` and `.agents` folders and keeps the last copy of each name, so a copy made by hand into an OpenCode folder silently overrides every update. The installer never looks there.

The student also had nowhere to read what was ready afterwards. The maintainer folded the fixes into this change, which owns the prompt, the installer and the script-constraint requirement.

## What Changes

- **Universal paste-prompt.** One install prompt the student pastes into any local agent. The agent:
  0. stops with a pointer to the chat-only section when it runs in a cloud sandbox, a VM or a chat-only app, where an install would vanish with the conversation;
  1. checks for Python ≥ 3.11: `python3`, `python` and `py -3` first; only when none answers, read-only further probes (`uv python find ">=3.11"` when uv is installed, one lookup for versioned `python3.X` names, and `py -0p` on Windows); stopping with per-OS install guidance only when all of them find nothing;
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

  Added 2026-10-13:
  - **Copies in apps' own skill folders.** A data table, annotated with source and date, names the folders apps read that the installer never writes: OpenCode's `.opencode/skill(s)` in the working folder and `~/.config/opencode/skill(s)`, plus `~/.codex/skills`, `~/.cursor/skills` and `~/.copilot/skills`. Real copies of shipped skills there are listed with the other-scope wording, links into the installed copy are skipped, and removal happens only with `--remove-other`, which the prompt already asks about. `--dry-run` names them. OpenCode's parent-folder lookup up to the git root stays out of reach, a stated gap.
  - **Readiness lines.** The output ends with presence-only lines: the Python version that ran it, whether `python3` is only the Windows Store shortcut, whether `pandoc` and `typst` are found, and whether an `api-keys.env` exists. It runs none of those programs, never opens the key file, and records none of it.
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
  - The collector also restates the installer's table of apps' own skill folders (an offline test keeps the two equal), hashes copies found there, and names the folder, so a bug report shows a shadowing copy (2026-10-13).
- **One interpreter clause in the skills (2026-10-13).** Each of the eight script-bearing `SKILL.md` files gains one sentence, appended to its existing `${CLAUDE_SKILL_DIR}` fallback paragraph: `python3` stands for any Python 3.11 or newer that answers on the machine (`python`, `py -3`, or a versioned name such as `python3.13`), and the agent keeps the one that worked for the rest of the conversation. It replaces the seven per-command Windows parentheticals (check, import ×2, reverse, supervise, write, publish), and proposal-check's `winget install Python.Python.3.12` advice becomes a link to the install guide's "No Python yet?" section. lit-search and troubleshoot gain the clause. A substring test guards it; it is not materialized.
- **Supporting text and tools follow.**
  - The issue template, the harness's troubleshoot eval prompt (and its generated `evals.json` projection), and `harness/README.md` become route-neutral.
  - The claim "the installed skills carry no version" is replaced by the install record.
  - The README's "For supervisors" section gains a brief note on provisioning a cohort through Claude's organization plugin sync, the one app that can load the plugin today. It names ChatGPT Edu and Copilot organizations as not yet able to. This is documentation only, within the portability boundary.
  - `poe install-check` additionally installs the tracked tree through `install.py` from a `git archive` zip.
  - A dev-runner probe pastes the prompt into Claude Code: once unanswered, to check the scope question is asked, and once pre-answered, to check the install lands. An optional third variant (2026-10-13), Linux only, offers no Python on the PATH but a versioned `python3.X`, and passes only when the install lands without the agent sending the student to install Python. It runs only on the maintainer's go-ahead.
  - `docs/install.md` gains one sentence under "Any other agent": an earlier manual copy in OpenCode's own folders can shadow the installed skills, and the installer lists it.
- **Out of scope:**
  - per-skill ZIP uploads for chat-only apps (a later change, after one real upload settles the 200-character description limit);
  - listings in the Anthropic, OpenAI, Cursor or Antigravity directories (publishing, explicit request only);
  - added 2026-10-13:
    - telling students to record their interpreter in `AGENTS.md` or `CLAUDE.md`: no skill, installer line or document does so;
    - the docs readiness checklist, the publish skill's `winget` syntax fix and the workspace sentences (the later change `add-setup-readiness-guide`);
    - Windows UTF-8 script output (a separate change);
    - an OpenCode recipe, until a maintainer run stamps one.

## Capabilities

### New Capabilities
- `installation`: the install prompt (including where it looks for an existing Python), the `install.py` installer (scope, directories, record, conflicts including copies in apps' own skill folders, update, Python precondition, readiness lines), and the plugin definition — how the skill set reaches a student's machine without a terminal.

### Modified Capabilities
- `skill-packaging`: changes three requirements.
  - "Registry installation from the repository" now names three routes instead of the skills.sh CLI alone: prompt+installer, plugin, and CLI.
  - "Installation verified against the tracked tree" now also covers the repository installer, besides the README's CLI command.
  - "User-side script constraints":
    - a script another skill owns ships as a synchronized copy and is addressed through the skill-directory variable, never by an install path;
    - each script-bearing skill states once what `python3` stands for, instead of per-command platform hints; proposal-check points to the install guide for a missing Python, and no skill names a version-pinned install command (2026-10-13).
- `user-onboarding`: the README quick start carries the install prompt. Concrete agent walkthroughs become a per-app install guide with verified stamps and a flagged chat-only section. The update-first step and the issue template become route-neutral. Supervisors learn about cohort provisioning.
- `skill-troubleshoot`: the stale-install rung reads the install record and names the update route, instead of asserting that installs carry no version. Install identification adds the install record, the plugin and user-level roots, and the apps' own skill folders the installer lists, beside the lock record and hashes.
- `testing-harness`: a dev-runner probe for the install prompt, with an optional versioned-interpreter variant.

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
- **Changed by the 2026-10-13 revision:**
  - `install.py` (the apps' own skill folders table, `--remove-other` and `--dry-run` covering it, readiness lines);
  - `shared/blocks/install-prompt.md`, and its generated copies in `README.md` and `docs/install.md`;
  - the eight script-bearing `SKILL.md` files: check, import, lit-search, publish, reverse, supervise, troubleshoot, write;
  - `skills/proposal-troubleshoot/scripts/collect.py`;
  - `docs/install.md` ("Any other agent");
  - `harness/claude_runner.py`, `harness/l1_checks.py`, `harness/README.md` (the optional probe variant).
- **Removed:** `docs/getting-started.md` (folded into `docs/install.md`).
- **Tests:**
  - new: `tests/unit/test_install.py`, `test_plugin_manifests.py`, `test_install_docs.py`, `test_install_probe.py` (with recorded probe outcomes under `tests/unit/data/install_probe/`);
  - updated: `test_install_check.py`, `test_sync.py`, `test_troubleshoot_collect.py`, `test_repo_conventions.py` (the root installer is scanned), and `test_script_paths.py`, which now forbids every install-path script reference;
  - extended by the 2026-10-13 revision: `test_install.py` (a home and folder with spaces in both scopes, a planted `api-keys.env` sentinel, the apps' own folders, readiness lines), `test_install_docs.py` (the prompt's further probes, links from skills into the guide), `test_script_paths.py` (the interpreter clause), `test_troubleshoot_collect.py` (the mirrored table), `test_install_probe.py` (the optional variant's verdict).
- **Release:** plugin installs follow `main` automatically, so a bad push reaches plugin users without any action on their part. This is consistent with the rolling-release policy, but it is new exposure. Task 8.0 put the change on `main` on 2026-10-05, ahead of the recipe runs; the recipes stay stamped `unverified` until run. The 2026-10-13 revision is implemented off `main` and lands there only complete, with `poe test` green.
