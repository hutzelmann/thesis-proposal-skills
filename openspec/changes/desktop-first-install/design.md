# Design

## Context

See proposal.md, "Why", for the motivation. The specs this design serves are `installation` (new), and the deltas to `skill-packaging`, `user-onboarding`, `skill-troubleshoot` and `testing-harness`.

The repository's install surface today:

- **Install docs and guards.** `README.md` has the quick start and the update-first step. `docs/getting-started.md` has two terminal walkthroughs.
- **The CI install check.** `scripts/install_check.py` and its CI workflow extract `npx skills add` from the README and install a `git archive` of HEAD.
- **Troubleshoot.** Rung 0 hardcodes the npx command. Rung 3 runs the sibling `check.py` through `.claude/skills/proposal-check/…`; that path is a deliberate divergence, because the audit invariants forbid `../proposal-*/scripts/`. The collector scans five roots and knows only the skills CLI's `skills-lock.json`.
- **Generated copies.** `scripts/sync_shared.py` already vendors `check.py` into import, write, reverse and supervise. It materializes `shared/blocks/` regions into every `SKILL.md`, located by position rather than by marker.

Constraints that shape everything below:

- **User-side code.** Scripts are stdlib only, Python ≥ 3.11, cross-platform, `main(argv)`.
- **No markers in `SKILL.md`.** It is a page skills.sh renders.
- **Byte identity.** Installed skill files must stay byte-identical, so `poe identify` keeps resolving hashes.
- **Audit surface.** A shipped skill must not download code: skills.sh's audits flag remote fetch plus self-modification.
- **Release channel.** `main` is the release channel, so this change stays on a branch until the maintainer has run each recipe.

## Goals / Non-Goals

**Goals:**

- A student installs or updates all eleven skills by pasting one prompt, or by one plugin-button flow, without a terminal.
- The installer is deterministic and L0-testable. The only thing left to the model is following five short steps.
- Every install route is identifiable from a bug report.

**Non-Goals:**

- **Per-skill ZIP uploads for chat-only apps.** Deferred: 11 uploads, no update path, and an unresolved 200-character description limit.
- **Directory or store listings.** These are publishing.
- **The installer auto-detecting which agent runs it.** Agents expose no reliable signal: the skills CLI fails to recognise Claude desktop's `AI_AGENT` value. Writing both shared directories covers 10 of 12 hosts without needing to know.
- **Installing system software.** Python is the student's step, with guidance.

## Decisions

### D1 — The prompt runs our installer; the model does not copy files

Considered alternatives:

- **(a) A prose prompt with a directory table.** The model improvises: wrong directory, hand-rewritten files (which breaks byte identity), npx detours. It is also untestable at L0.
- **(b) npx first, zip fallback** (agenthouse). It needs Node ≥ 22.20 and git. Unattended it misbehaves: no `-g` gives a folder install, no `-a` gives 53 dot-folders, and a false "Failed to install" with exit 0. It also leaves two drifting branches.
- **(c) The host's native installer first.** Codex's `$skill-installer` is the same zip-and-copy into a deprecated directory; the GUI routes still need a human click.
- **(d) The skills.sh "Prompt" text verbatim.** Same prerequisites as (b).

Our own installer moves every decision that can be tested into code. Python ≥ 3.11 is already required by 8 of the 11 skills, so the installer adds no prerequisite, and it surfaces a missing Python at install time instead of mid-proposal.

### D2 — Installer shape

`install.py` lives at the repository root, so the raw URL is short: `https://raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py`. It is never inside `skills/`, so it is never installed.

Interface:

```
python3 install.py --scope all|folder [--remove-other] [--source URL|PATH] [--dry-run]
```

**Interpreter check.** The module parses from Python 3.7 on. It has no syntax newer than 3.7 and no 3.11 name at module level, and it imports `from __future__ import annotations`, which is also why 3.6 and older cannot parse it. `main()` checks `sys.version_info` first, so a 3.9 interpreter (the macOS Command Line Tools ship 3.9.6) gets a sentence naming 3.11, not a traceback. An L0 test parses the file with `feature_version=(3, 7)`.

**Source.** The default is `https://codeload.github.com/hutzelmann/thesis-proposal-skills/zip/refs/heads/main` (a GitHub archive). `--source` takes a URL, a zip path or a directory: tests and the install check use it; students never need it.

**Revision.**
- A zip's revision comes from the archive comment. `git archive` and GitHub archives both write the commit id there; this is verified in the facts pass and, for `git archive`, in the L0 tests.
- A directory source has no revision; the record says `unknown`.

**Downloading.**
- Downloads use `urllib.request` with the default SSL context.
- On a certificate-verification failure (the typical python.org macOS build without "Install Certificates"), the installer retries in two steps:
  1. with the base system's bundle `/etc/ssl/cert.pem` as `cafile`;
  2. then through curl, from its fixed system path only: `/usr/bin/curl` or `/bin/curl`, and `%SYSTEMROOT%\System32\curl.exe` on Windows. A PATH search on Windows looks in the current folder first, which is the student's folder. Curl gets `--proto =https`, so a redirect cannot downgrade.

  Either way it then prints a notice: the skills' own literature searches use plain `urllib` and need "Install Certificates" too.
- Any other failure exits 2 with a plain-language cause and changes nothing. That covers a broken-off read (`http.client.HTTPException`), a curl timeout, and a damaged archive member.

**Copying.**
- Per target directory, each shipped skill is extracted into a sibling staging directory `.<name>.new-<pid>` and then swapped in:
  1. the old copy is renamed aside to `.<name>.old-<pid>`;
  2. the new one is moved in;
  3. the old one is deleted, best effort.

  If moving the new one in fails, the old copy is renamed back before the error is reported. A lock on the old copy cannot fail an install that has already succeeded. Leftover `.proposal-*.new-*`/`.old-*` folders from an interrupted run are swept at the start of the next one.
- Files are written with exact bytes. No newline translation: zip members are read as bytes.
- Real copies, never symlinks. Hosts that read both shared directories: Copilot CLI uses the first one found and OpenCode keeps one. VS Code and Cursor are undocumented and are checked in their manual recipe runs (tasks 8.3, 8.5). Symlinks break in sandboxes and on Windows.
- Removal never follows a link. A symlink or Windows directory junction in place of a skill folder (the skills CLI links agent folders with junctions on Windows, and `is_symlink()` misses those before Python 3.12) is removed as a link: `rmdir` on Windows, `unlink` elsewhere, never `rmtree`.

**Safety.**
- A skill name from the archive or from an existing record is used as a path only when it matches `proposal-[a-z0-9][a-z0-9-]*`. A record lies in the folder the student opened, so it is untrusted: a planted `proposal-check/../../..` must never reach `rmtree`. The adversarial review reproduced exactly that before the check existed.
- Only matching `proposal-*` entries and the installer's own staging leftovers are ever replaced or removed. Only the record file is written beside them.
- Messages show home- or folder-relative paths: the more specific base wins, and the home on a tie. A working folder at or above the home folder therefore never prints a user name.

### D3 — Target directories as data

One table in `install.py`, keyed by scope:

| Scope | Always | Only when the app's config directory exists |
|---|---|---|
| `all` | `~/.agents/skills`, `~/.claude/skills` | `~/.gemini/config/skills` (Antigravity 2.0 and its IDE; detected by `~/.gemini/antigravity` or `~/.antigravity`), `~/.gemini/antigravity-cli/skills` (Antigravity CLI), `~/.kiro/skills` (Kiro) |
| `folder` | `./.agents/skills`, `./.claude/skills` | `./.kiro/skills` when `~/.kiro` exists; Antigravity reads `./.agents/skills` in a workspace |

These paths come from the apps' own documentation, read on 2026-10-03:
- **Antigravity.** Its documentation names `~/.gemini/config/skills`. The skills CLI still writes the legacy `~/.gemini/antigravity/skills`, which is tracked as google/agents-cli#26.
- **Kiro.** Documentation as of 2026-10-02.

The L0 tests pin the table.

Rationale:
- Claude Code reads only `.claude/skills`; requests to add `.agents` were closed "not planned" twice. Codex/ChatGPT desktop, VS Code, the Copilot CLI and app, Cursor, Gemini CLI, OpenCode, Cline, Zed and Devin all read `~/.agents/skills`.
- `~/.codex/skills`, `~/.cursor/skills` and `~/.copilot/skills` are never written: they are deprecated or redundant, and writing them creates duplicates.
- A host-specific directory is written only when its app is present, so no student gains dot-folders for apps they never installed.

### D4 — Install record

`.thesis-proposal-install.json` is written at the root of each filled skills directory, not inside a skill folder, so skill bytes stay identical. Host skill scanners look for directories holding a `SKILL.md`, so a dotfile at the root is inert.

Content:

```json
{"package": "thesis-proposal", "installer": 1, "revision": "<sha>|unknown",
 "installed_at": "<UTC ISO-8601>", "scope": "all|folder",
 "source": "default-branch|url|zip|directory",
 "directories": ["~/.agents/skills", "~/.claude/skills"],
 "skills": ["proposal-check", "…"]}
```

Paths are stored home-relative (`~/…`) where possible. The record may later be read by the troubleshoot collector, which must not carry a user name into a report.

The previous record, if present, provides the "previous revision" line of the output.

### D5 — Existing installs

- **Plugin installs** are detected from each app's own record of its installs:
  - a plugin id `"thesis-proposal@…` in Claude's `~/.claude/plugins/installed_plugins.json` or `~/.claude/settings.json`, or in Codex's `~/.codex/config.toml`;
  - a `thesis-proposal` folder under `~/.claude/plugins/synced/`, which is where a plugin added with Claude's plugin button arrives in Claude Code sessions, with no entry in `installed_plugins.json` (found by the review);
  - Copilot's `~/.copilot/installed-plugins/thesis-proposal/thesis-proposal/`;
  - VS Code's `agentPlugins/github.com/hutzelmann/thesis-proposal-skills` under its user-data folder.

  Cache folders alone are not evidence: Claude keeps an uninstalled plugin's cache, with an `.orphaned_at` marker, for 14 days. One found means exit 3 with the plugin route's update action, and nothing is written.

  A plugin added in the Chat tab never reaches a machine that has not opened a Code session, so detection cannot be complete. The docs therefore tell Claude students never to paste the prompt after using the button.
- **Other-scope copies:**
  - with `--scope all`, the installer checks the working directory's targets;
  - with `--scope folder`, it checks the user-level targets.
  - Copies found are listed and kept, unless `--remove-other` is given; then only their `proposal-*` folders and the record are removed.
- **A skills-CLI lock file** (`skills-lock.json` in the working directory, or the global `~/.agents/.skill-lock.json`) next to other-scope copies is reported as an earlier terminal install, with `npx skills remove` as the tidy-up, and never touched.
- **A folder install in the home folder** fills the all-projects directories, so it is recorded and reported as an all-projects install.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | installed |
| 1 | usage, scope missing |
| 2 | environment (Python, network, permission) |
| 3 | refused because of a conflicting install |

The prompt tells the agent to relay the output and ask before re-running with any option the output names.

### D6 — Install prompt: single source, materialized into documents

- **Source.** `shared/blocks/install-prompt.md`, plain text written for the agent, in English.
- **Placement.** In `README.md` and `docs/install.md` it appears as a fenced `text` block, which GitHub renders with a copy button, directly after an HTML comment `<!-- install-prompt -->`.
- **Materialization.** `scripts/sync_shared.py` replaces the fence content after each such comment and fails `--check` on drift.
- **Why a marker here.** Unlike `SKILL.md` regions, a README is rendered by GitHub, which hides HTML comments, so a marker is invisible to readers. skills.sh renders only `SKILL.md`.

Prompt wording constraints:
- An opening stop line: an agent in a cloud sandbox, a VM or a chat-only app says it cannot install, and links the guide's chat-only section. Pasted into claude.ai's code-execution sandbox, the installer would otherwise "succeed" in a throwaway container (found by the review).
- The five steps in the spec's order.
- A general prohibition: "Do not install any software yourself, and do not copy, edit or run any skill files". Output asking for an install is relayed to the student, not acted on.
- The Windows `python` and `py -3` alternatives, the note that the Store's install manager downloads Python on first run, and the macOS hints: Install Certificates, and cancel the developer-tools dialog (its Python is 3.9).
- A shell command to download, never a web-page reader, which converts the file. The installer runs from the folder the student has open.
- The reload instruction, phrased host-neutrally.

About 250 words. The first draft held 170, but the review showed each added clause closes a failure seen or reproduced. The live probe passes with both sonnet and haiku at this length.

### D7 — Plugin manifest: one Claude marketplace file, skills only

**Layout.** One file: `.claude-plugin/marketplace.json`.
- Marketplace `thesis-proposal`, with one plugin entry `thesis-proposal`.
- `"source": "./skills"`, `"strict": false`, and an explicit `skills` list of the eleven folders.
- No `plugin.json`, and no `version` anywhere.

**Verified with Claude Code 2.1.284** in the facts pass:
- `claude plugin validate --strict` passes;
- all eleven skills load;
- only the 67 skill files land in the plugin cache;
- the installed version is the commit SHA, so a plugin install follows `main`.

**Why a `plugin.json` alternative was rejected.** The other layout, `skills/.claude-plugin/plugin.json` with `"skills": "./"`, warns "No version specified" and fails `--strict`.

**Agent Plugins 1.0 root `plugin.json` rejected for now.** Codex/ChatGPT, VS Code and the Copilot app read `.claude-plugin/marketplace.json`, but they resolve a plugin root to a manifest. A skills-only root has none, so those hosts would need:
- `source: "./"`: ships the whole repository (about 990 files) into every cache;
- a root `plugin.json`: Kiro requires its `version`, and Codex, Copilot and VS Code read it, which pins those hosts to a stamped version instead of `main`.

The featured recipes for those apps use the install prompt, so nothing is lost. A later change can add the root manifest once a version-stamping cadence exists.

**Risk of a stale list.** A listed path that does not exist passes the validator, but the whole plugin then fails with "Path not found". The L0 test therefore pins the list to the `skills/proposal-*` folders that hold a `SKILL.md`.

**Unconfirmed.** Whether claude.ai's "Add marketplace" honours the entry's `skills` list. Anthropic's own Knowledge Work marketplace uses the identical pattern for a third-party skills repository. The maintainer's Claude desktop run (task 8.2) settles it.

**Side effect.** The skills CLI also reads `.claude-plugin/marketplace.json`: it resolves the entry's skill paths and groups them under the plugin name. `poe install-check` confirms the npx arm still installs exactly the eleven folders.

**Cohort provisioning follows.** The README's supervisor note names only Claude's organization plugin sync. ChatGPT Edu's "Import marketplace" and Copilot organization marketplaces would read this file but find no root manifest, so the note says they cannot load the plugin yet. Their students install with the prompt.

### D8 — Troubleshoot

- **T1.** SYNC_MAP gains `skills/proposal-check/scripts/check.py → skills/proposal-troubleshoot/scripts`. The script already resolves `structure.json` relative to itself, and troubleshoot already ships `references/structure.json`.
  - Rung 3's command becomes `python3 ${CLAUDE_SKILL_DIR}/scripts/check.py`, with the standard fallback prose.
  - The sibling-path sentence and README divergence row 187 are removed.
- **Rung 0.** It reads like this:
  - if a `.thesis-proposal-install.json` is in the user's skills directories, update by pasting the install prompt again, answering with the record's `scope`;
  - if the app's plugin page lists "Thesis Proposal", use its update action;
  - if it was installed with the terminal command, `npx skills update`.

  The "carries no version" sentence goes. The prefilled-issue instructions map the report's install-route line onto the template's new `route` options, and an L0 test pins that the mapped options exist in the template.
- **Collector (`collect.py`).**
  - Roots: adds the Antigravity and Kiro user and workspace directories, and the plugin folders: the Claude, Codex and Copilot caches, Claude's synced plugins, and VS Code's agent-plugin clone. Versions marked orphaned are skipped.
  - Records: `install_lines()` reads every install record. The report carries revision, scope, source kind and install time, each repeated only when it has the documented shape and type, otherwise "unreadable". It also carries "route: installer | plugin | CLI | unknown". The CLI route counts the global `~/.agents/.skill-lock.json` too; that lock is reported as present, never copied.
  - Privacy: the record is never copied verbatim. Paths are shown home- or workspace-relative, with the more specific base winning and the home on a tie.
  - Plugin detection: by each app's folder layout rather than by guessing.

### D9 — Install check (CI)

`scripts/install_check.py` keeps the npx arm unchanged and gains an installer arm:

1. `git archive --format=zip --prefix=thesis-proposal-skills-main/ HEAD` into a temp file, so the archive comment is HEAD's commit id;
2. run `install.py --scope all --source <zip>` in-process under an isolated HOME (environment `HOME`/`USERPROFILE` redirected);
3. assert:
   - the eleven skills sit byte-identical in both user-level directories;
   - the records name HEAD's commit;
   - the installed `check.py` smoke passes from `~/.claude/skills`.

The CI workflow comment is updated to name both arms. The README still carries one `npx skills add` line, which the npx arm extracts.

`--ref <tree-ish>` (default `HEAD`) exports a commit or a `git write-tree` tree instead, so the staged state can be checked before it is committed. The README command and the expected skill list are then read from the export, never from the checkout. A tree carries no commit id, so its zip has no comment and the records say `unknown`, as the installer would.

### D10 — Dev-runner probe

Two scenarios, `install_prompt` and `install_prompt_answered`, run as `uv run poe dev <name>`. They live in `run_install_probe`, apart from the skill scenarios, because nothing is staged.

**Setup.** The runner:
- builds a zip of the working tree's `skills/` under a `thesis-proposal-skills-main/` prefix;
- serves it with `install.py` from `127.0.0.1` (the runner already embeds an HTTP server for another scenario). The served `install.py` is the repository file with its default source URL rewritten to the local zip.

**The request** is the shared prompt with the raw GitHub URL replaced by the local one. In the answered variant, the student's answer "install for all my projects" is appended up front.

**Environment.** Claude runs with `HOME` set to a temp directory, and `CLAUDE_CONFIG_DIR` from the routing rig's `prepare_config` so it is logged in without touching the real home.

**Verdicts.** These live in `harness/l1_checks.py` as `verdict_install_prompt_asks_scope` and `verdict_install_prompt_installed`. They have L0 tests on synthetic outcomes, on the recorded final messages of the 2026-10-03 runs (`tests/unit/data/install_probe/`), and on a home the real installer filled, both with and without a hand-copied stray:
- *unanswered*: the final message contains a scope question naming both options, and the temp home has no `proposal-*` directory;
- *answered*: full set byte-identical in both user-level directories, records present, and no other `proposal-*` copies anywhere under the temp home.

### D11 — Documentation layout

`docs/install.md`:

1. "Which app do you use?" table: app, cost, route, link to the recipe.
2. The prompt, with an "If it does not work" note, then a standalone "No Python yet?" subsection that both routes link to. It covers:
   - the Windows install manager, which downloads Python on first run;
   - macOS python.org plus Install Certificates, and cancelling the developer-tools dialog;
   - Linux.
3. Recipes for ChatGPT desktop (Codex), Claude desktop (plugin button, with a Python step for the Code tab), VS Code / Copilot app, Antigravity and Cursor. Each recipe:
   - opens with its stamp line `Verified YYYY-MM-DD with <app> <version>`, or `unverified` while the change is open;
   - covers getting the app, opening a folder, pasting the prompt or using the plugin button, approving the network or file access prompts, and reloading.
4. "Any other agent": paste the prompt.
5. "Chat-only apps" (flagged): claude.ai uses the plugin button, never the prompt.
6. "Literature search cannot reach its sources" (renamed from "Literature search says OFFLINE"; the search reports "source degraded" or "sources: none", and only reference validation says OFFLINE). It names the six services, each app's network switch, and the macOS certificate step.
7. "Updating" (the record's `scope` tells the student which answer to give), "Removing" (every directory the record lists, plus `npx skills remove`), and "From a terminal" (npx).

`docs/getting-started.md` is deleted after its folder and API-key notes move into `install.md` ("What you get in the folder"). Links to it are updated.

L0 tests (`test_install_docs.py`) pin:
- every recipe heading is followed by a stamp line. `unverified` is accepted only while this change's folder exists, so archiving it forces a stamp or the recipe's removal;
- every `install.md#…` anchor in the guide, the README and the prompt names an existing section;
- the services named equal the hosts the search scripts contact;
- the troubleshoot skill's route mapping matches the issue template.

## Risks / Trade-offs

- **[Agents balk at "download and run a script"]** → The prompt states the source and purpose in the student's own voice, which is a user instruction rather than fetched content. The dev-runner probe measures Claude Code. The maintainer's manual runs cover the other featured apps. A recipe whose agent refuses gets a note, or falls back to the plugin route.
- **[macOS python.org builds lack root certificates]** → The installer retries with the system bundle, then with curl from its fixed system path, and tells the student that the skills need "Install Certificates" too. The guide's macOS Python step and its network section say the same. If every fallback fails, the error names "Install Certificates.command".
- **[A planted install record turns the installer into a deletion tool]** → Names from records and archives are validated against the skill-name pattern before they are used as paths. L0 tests plant traversal names under both scopes.
- **[Windows junctions and locked files]** → Junction-aware removal. The swap rolls back, and leftovers are swept on the next run. The junction test runs only on the Windows CI job.
- **[An agent in a cloud sandbox installs into a container]** → The prompt's opening stop line, and the chat-only section tells claude.ai users to use the plugin button.
- **[Plugin auto-update ships a bad `main` to plugin users without any action on their part]** → Consistent with the rolling-release policy. The CI install check covers both arms on every push. Noted in the proposal as new exposure.
- **[Featured-app UIs move]** → Recipes carry stamps, so a stale recipe is visible as old. The weekly install check guards the code paths, not the GUIs.
- **[Duplicate skills when a student mixes routes]** → The installer refuses beside a plugin install, and the docs state that the two routes are exclusive. Old npx folder copies are reported, not deleted silently.
- **[Hosts reading both shared directories show the skills twice]** → Copilot CLI (first found wins) and OpenCode (later scan overwrites) keep one copy, verified from their sources. VS Code and Cursor read both directories and their duplicate handling is undocumented. The manual recipe runs (tasks 8.3 and 8.5) check it; if they show duplicates, a follow-up writes `~/.claude/skills` as links on macOS and Linux.
- **[`install.py` at the root is a new user-side surface outside `skills/`]** → Same constraints as skill scripts: the conventions test scans it, and ruff and coverage include it. It is not part of any skill, so the skills.sh audits do not see it. The install check exercises it in CI.

## Migration Plan

1. Implement on branch `desktop-first-install`, with `poe test` green throughout.
2. Run the dev-runner probe, both variants, on the subscription.
3. The maintainer runs each featured recipe once from the checklist in tasks.md and reports the app and version. Stamps are filled in; a recipe not run is removed.
4. Merge into `main`, archive the change, and run `python3 scripts/sync_shared.py` after the merge, since the generated copies carry `merge=ours`.
5. Existing npx users need no migration: their installs keep working. Re-installing through the prompt in the same scope replaces the folders; the other scope's copies are reported for removal.

Rollback: revert the merge. Installed copies and records are inert files, and plugin users are rolled back by the next sync.

## Open Questions

- Whether claude.ai's "Add marketplace" honours the plugin entry's `skills` list (see D7). The maintainer's Claude desktop run settles it; a failure there means switching the entry to a `plugin.json`-based layout, which changes data, not the approach.
