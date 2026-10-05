# Tasks

## 1. Facts pinned before code

- [x] 1.1 Pin the facts the design defers. Each answer is recorded in the task notes below with its source.
  - The Antigravity user-skills directory and its detection directory.
  - The Kiro directories.
  - The plugin-cache and registry locations for Claude Code and Codex.
  - The Claude marketplace/plugin manifest layout that ships only `skills/`, if any.
  - Whether VS Code, the Copilot app and Cursor read `.claude-plugin/`.
  - Whether GitHub and `git archive` zips carry the commit id as the archive comment.
  - The macOS python.org certificate behaviour.

## 2. Installer

- [x] 2.1 Write `install.py` at the repository root, per design D2–D5:
  - Python ≥ 3.11 stdlib only, with `main(argv)`, version gate first;
  - `--scope all|folder` mandatory, plus `--remove-other`, `--source` and `--dry-run`;
  - zip, URL and directory sources, with the revision read from the archive comment;
  - staged per-skill swap into the target directories, and home-relative install records;
  - plugin-install refusal (exit 3), and reporting or removing other-scope copies;
  - curl retry on certificate failure, and exit codes 0/1/2/3.

  Verify: `uv run ruff check install.py` is clean.
- [x] 2.2 Add `.` to pytest `pythonpath`, add the installer to coverage `source`, and add the repository root installer to the `SCRIPT_DIRS` scan in `tests/unit/test_repo_conventions.py`. Verify: `uv run pytest tests/unit/test_repo_conventions.py` passes and lists `install.py`.
- [x] 2.3 Write `tests/unit/test_install.py`, run in-process with a tmp HOME (`HOME`/`USERPROFILE` monkeypatched) and tmp cwd. Cover:
  - scope missing → exit 1 naming both choices;
  - fresh `all` install from a synthetic zip carrying a commit comment: both user directories filled byte-identically, and records naming the revision and every directory;
  - `folder` scope;
  - host-specific directory only when its app's config directory exists;
  - re-run replaces, removes files deleted upstream, and prints previous → new revision;
  - unrelated skills untouched;
  - plugin install → exit 3, nothing written;
  - other-scope copies listed and kept, then removed with `--remove-other`;
  - directory source → revision `unknown`;
  - network failure → exit 2, existing install unchanged;
  - an old-interpreter gate message;
  - a real-tree install from a zip of the working tree's `skills/`, after which the installed `check.py` reports findings on f15.

  Verify: `uv run pytest tests/unit/test_install.py` passes, and coverage of `install.py` is ≥ 90%.

## 3. Install prompt and plugin manifests

- [x] 3.1 Write `shared/blocks/install-prompt.md`, the five steps in the spec's order with both prohibitions, at most about 170 words. Extend `scripts/sync_shared.py` so it fills the fenced block after each `<!-- install-prompt -->` comment in `README.md` and `docs/install.md`, and reports drift under `--check`. Verify: new tests in `tests/unit/test_sync.py` check that a drifted prompt copy fails `--check` and a sync restores it.
- [x] 3.2 Add `.claude-plugin/marketplace.json` and the plugin manifest(s) per design D7 and the pinned facts, with no version field. Verify: a new `tests/unit/test_plugin_manifests.py` checks that the manifests resolve to exactly the shipped `proposal-*` skills and carry no version; `claude plugin validate .` passes when the CLI is available, and the result is recorded in the notes.

## 4. Troubleshoot follows the routes

- [x] 4.1 Add `skills/proposal-check/scripts/check.py → skills/proposal-troubleshoot/scripts` to SYNC_MAP and run `python3 scripts/sync_shared.py`. Verify: `.gitattributes` gains the generated entry and `sync_shared.py --check` is clean.
- [x] 4.2 Rewrite troubleshoot Rung 0 (route-neutral, reading the install record) and Rung 3:
  - Rung 3 runs `python3 ${CLAUDE_SKILL_DIR}/scripts/check.py` with the standard fallback prose.
  - Remove the sibling-path sentence and the "carries no version" claim.

  Verify: `test_script_paths.py`, `test_skill_header_pattern.py`, `test_audit_invariants.py` and the body-size checks pass, and the troubleshoot mandate pin is unchanged.
- [x] 4.3 Extend `collect.py`:
  - new roots (Antigravity, Kiro, plugin caches);
  - install-record reading into `[measured]` lines (revision, scope, source kind, time, route), never copying the record verbatim and never printing a home path;
  - the route line "installer | plugin | CLI | unknown".

  Verify: new cases in `tests/unit/test_troubleshoot_collect.py` for the record-present, plugin-cache and neither cases, with no username in the report.
- [x] 4.4 Make the issue template's update-first checkbox route-neutral and add an install-route field. Make the harness troubleshoot eval prompt route-neutral, then regenerate `evals.json` via `harness/eval_export.py`. Verify: the drift gates are clean and `test_eval_wiring.py` passes.

## 5. Documentation

- [x] 5.1 Write `docs/install.md` per design D11:
  - the app table;
  - the prompt block;
  - recipes for ChatGPT desktop (Codex), Claude desktop, VS Code / Copilot app, Antigravity and Cursor, each with a stamp line (`unverified` until task 8);
  - "Any other agent", the flagged "Chat-only apps", "Literature search says OFFLINE" (six domains plus per-app switch), "Updating", "Removing", "From a terminal", and "What you get in the folder" (moved from getting-started).

  Verify: a new `tests/unit/test_install_docs.py` checks the recipe stamp format, that the prompt block is present in both documents, and that the OFFLINE section names the six domains.
- [x] 5.2 Delete `docs/getting-started.md` and update every link to it. Verify: `git grep getting-started` finds no live references outside archived changes.
- [x] 5.3 Update `README.md`:
  - Quick start: open your app in a folder, then the prompt or the plugin button, then the first request, plus one "prefer a terminal?" `npx skills add` line;
  - the host sentence (desktop apps, ChatGPT);
  - "When something goes wrong": update the way you installed;
  - "For supervisors": cohort provisioning;
  - remove the troubleshoot divergence row.

  Verify: `test_install_check.py` still extracts the command, and the README tests pass.
- [x] 5.4 Update `AGENTS.md` (eleven skills; install routes; `install.py` as user-side code), `harness/README.md` (install check arms; no "no hosted artifact"; the probe), and `scripts/stamp_version.py` docstring wording. Verify: `git grep -n "npx skills add installs\|ten \`proposal-\*\`"` finds no stale claim.

## 6. Install check and dev-runner probe

- [x] 6.1 Add the installer arm to `scripts/install_check.py`: `git archive --format=zip` of HEAD, `install.py --scope all --source <zip>` in an isolated HOME, byte identity in both user directories, record revision equals HEAD, and the installed `check.py` smoke. Update the workflow comment. Verify: new pure-half tests in `test_install_check.py`; `uv run poe install-check` run locally passes both arms.
- [x] 6.2 Add `verdict_install_prompt_asks_scope` and `verdict_install_prompt_installed` to `harness/l1_checks.py`. Verify: L0 tests on synthetic homes and messages, which `test_repo_conventions` requires for every `verdict_*`.
- [x] 6.3 Add the `install_prompt` and `install_prompt_answered` scenarios to `harness/claude_runner.py`: a local server, the rewritten installer source, an isolated HOME, and `prepare_config`. Verify: `uv run poe dev install_prompt` and `uv run poe dev install_prompt_answered` on the subscription; record both outcomes, cost and helper-agent telemetry in the notes below.

## 7. Gate

- [x] 7.1 `uv run poe test` green, `uv run poe cov` holds the floor, and `uv run poe specs` validates strictly.
- [x] 7.2 Run an adversarial multi-lens review workflow of the full diff: correctness, cross-platform behaviour, security/audit surface, student UX of the prompt and docs, and spec ↔ implementation fidelity. Fix the confirmed findings and record them here.

## 8. Maintainer verification (manual, before merge)

- [ ] 8.1 ChatGPT desktop app (Codex view, free plan): paste the prompt in a fresh folder, answer the scope question, approve as asked, open a new chat, then ask "help me develop a thesis idea". Record the app version and date in the recipe stamp.
- [ ] 8.2 Claude desktop: run the plugin button (Customize > Plugins > Add marketplace > `hutzelmann/thesis-proposal-skills`) on a paid plan, and the prompt in the Code tab on another machine or a clean profile. Stamp the recipe. This run also settles design D7's open question: does claude.ai honour the marketplace entry's `skills` list, and do all eleven skills appear under Customize > Skills? Also paste the prompt once into the Chat tab and check that the agent stops with the chat-only pointer instead of installing into its sandbox.
- [ ] 8.3 VS Code with GitHub Copilot, or the Copilot app: run the prompt as the recipe says, and check whether the skills show twice. VS Code reads both `~/.agents/skills` and `~/.claude/skills`, and its dedupe is not documented. Stamp it.
- [ ] 8.4 Antigravity: run the prompt and approve the network access. Stamp the recipe.
- [ ] 8.5 Cursor: run the prompt and check whether the skills show twice. Stamp the recipe.
- [ ] 8.7 On a clean Windows machine, confirm the Python path the guide gives:
  - install "Python install manager" from the Microsoft Store;
  - paste the prompt and watch the first version check download Python, after the agent asks for network access;
  - check that `python`, not `python3`, is what then answers.

  Correct the "No Python yet?" subsection if any of that differs. On a Mac, likewise confirm that the python.org installer followed by Install Certificates.command leaves the literature search working.
- [ ] 8.6 Remove any recipe not run, then merge into `main`, re-run `python3 scripts/sync_shared.py`, and archive the change. Archiving makes `test_install_docs.py` reject any recipe still stamped `unverified`.

## Notes

**1.1 — facts pinned 2026-10-03.** Full reports are in the session scratchpad.

- **Antigravity.**
  - User skills directory `~/.gemini/config/skills` (2.0 and the IDE), and `~/.gemini/antigravity-cli/skills` for the CLI.
  - Workspace: `.agents/skills`.
  - Detection: `~/.gemini/antigravity`, `~/.antigravity`, `~/.gemini/antigravity-cli`.
  - Antigravity ignores `~/.agents/skills` at user level (google/agents-cli#26).
  - Source: antigravity.google/docs/skills.
- **Kiro.** `~/.kiro/skills` and `.kiro/skills`, detected by `~/.kiro` (kiro.dev/docs/skills, 2026-10-02).
- **Plugin installs.** Each app's own record of its installs is the evidence, never a cache folder alone (Claude orphans an uninstalled version for 14 days):
  - Claude: `~/.claude/plugins/installed_plugins.json` keyed `thesis-proposal@thesis-proposal`;
  - Codex: `~/.codex/config.toml` `[plugins."thesis-proposal@thesis-proposal"]`;
  - Copilot: `~/.copilot/installed-plugins/<marketplace>/<plugin>/`;
  - VS Code: `<user-data>/Code/agentPlugins/github.com/<org>/<repo>`.
- **Claude manifest.** `.claude-plugin/marketplace.json` with `source: "./skills"`, `strict: false`, an explicit `skills` list, no `plugin.json`, no version.
  - Verified with Claude Code 2.1.284: validate `--strict` passes, 11 skills load, the cache holds only the 67 skill files, and the version is the commit SHA.
  - Codex, VS Code and Copilot read `.claude-plugin/marketplace.json` but need a manifest at the plugin root. That forces whole-repo shipping, plus a root Agent Plugins `plugin.json` whose `version` Kiro requires. Rejected for now (design D7); those apps install through the prompt.
- **Archive comment.** GitHub's branch archive and `git archive --format=zip` of a commit both carry the 40-hex commit id as the zip comment. Verified on octocat/Hello-World and on this repository.
- **macOS certificates.** python.org's macOS builds, 3.12 through 3.15-dev, still need "Install Certificates" for `urllib` HTTPS. The base system's `/etc/ssl/cert.pem` works as `cafile`, and `/usr/bin/curl` is always present. The CLT `python3` is 3.9.6, below the floor.
- **Windows.** The `python3` and `python` App Execution Aliases point at the Store, and with arguments they print "Python was not found". The Store's "Python install manager" provides `python`, `py` and `python3`.

**3.2.** `claude plugin validate --strict .` (Claude Code 2.1.284, empty `CLAUDE_CONFIG_DIR`, no login) reports "Validation passed".

**6.1.** `uv run poe install-check --ref <git write-tree of the staged change>` passed both arms on 2026-10-03:
- the npx arm installed exactly 11 skills with `.claude-plugin/marketplace.json` present;
- the installer arm left byte-identical copies in both user directories;
- the smoke ran green in both.

`--ref` was added so the staged state can be checked before it is committed.

**6.3 — dev-runner probe, 2026-10-03, subscription, isolated config.**

| Scenario | Model | L1 | Cost | Turns | Helpers | Outcome |
|---|---|---|---|---|---|---|
| `install_prompt` | sonnet | PASS | $0.051 | 2 | none | reported Python 3.13 and asked the scope question verbatim; installed nothing |
| `install_prompt_answered` | sonnet | PASS | $0.062 | 3 | none | 11 skills byte-identical with a record in `~/.agents/skills` and `~/.claude/skills`; no stray copies; told the student to start a new chat |
| `install_prompt` | haiku | PASS | $0.030 | 4 | none | asked the scope question; installed nothing |
| `install_prompt_answered` | haiku | PASS | $0.043 | 7 | none | full install, no strays |

These four runs used the first prompt (about 170 words). The review changed it, so the probe was re-run on the final prompt (about 250 words, with the stop line and the general prohibition) on 2026-10-04:

| Scenario | Model | L1 | Cost | Turns |
|---|---|---|---|---|
| `install_prompt` | sonnet | PASS | $0.052 | 2 |
| `install_prompt_answered` | sonnet | PASS | $0.063 | 3 |
| `install_prompt` | haiku | PASS | $0.029 | 2 |
| `install_prompt_answered` | haiku | PASS | $0.042 | 4 |

The stop line itself, an agent in a cloud sandbox declining, cannot be probed locally. Task 8.2's Chat-tab check covers it.

After the review fixes: `uv run poe test` passed 1980 with 2 skipped, and `poe cov` reports 83.5% (installer 95%, collector 94%). `poe specs` is valid. `poe install-check --ref <staged tree>` passed both arms.

**7.2 — adversarial review, 2026-10-04.** 10 agents: five lenses (installer, security, spec fidelity, student UX, repo conventions), each followed by one skeptic who tried to refute every finding and reproduced the confirmed ones in scratch homes. Every confirmed or uncertain finding was fixed.

- **Blockers.** One defect, reported by two lenses. Skill names from an existing install record were used as paths unchecked, so a planted record (`"proposal-check/../../.."`) made the installer `rmtree` the student's project folder (reproduced). Archive folder names had the same gap.
  - Fix: names must match `proposal-[a-z0-9][a-z0-9-]*`.
  - Tests: traversal records under both scopes; archive names with `\`.
- **Majors.**
  - Windows junctions left by the skills CLI aborted every update. Now removed as links, never followed.
  - No rollback when a swap failed, and leftovers were never cleaned. Now the swap rolls back, removal of the old copy is best effort, and leftovers are swept.
  - The prompt let an agent "install" inside claude.ai's cloud sandbox. Now an opening stop line.
  - The prompt forbade installing Python only, not software in general. Now a general prohibition, and installer output asking for installs is relayed, not acted on.
  - The Windows Store install manager ships no runtime (it downloads Python on first run), and python.org's macOS build needs Install Certificates for the skills too. Now covered by the "No Python yet?" subsection, the prompt hints, and the installer's certificate notice.
  - Plugin-button installs were invisible to the installer. Now detected through `~/.claude/plugins/synced/` and Claude's settings, and the guide warns that detection cannot be complete.
  - The supervisor note promised ChatGPT Edu and Copilot org routes that cannot load the plugin. Now Claude-only, and the others are named as not yet possible.
  - The Claude line in the README came after the prompt and missed the "Add" step. Now it comes first and is complete.
  - Curl was resolved through PATH, which on Windows searches the current folder first. Now fixed system paths only, with `--proto =https`.
- **Minors and nits.**
  - Uncaught `IncompleteRead`, curl timeout and damaged archive members. Now exit 2 with a cause.
  - Display paths could show a user name (cwd at or above home). Now home-first on ties.
  - A folder scope run from the home folder. Now treated as all projects.
  - The global CLI lock, synced plugins, VS Code clones and wrong-typed record values in the collector.
  - Removal steps missed the Antigravity/Kiro folders. Now driven by the record's `directories`.
  - The OFFLINE heading used a word the search never prints. Renamed.
  - The `route` field was missing from the prefill instructions.
  - The stamp test accepted `unverified` forever. Now only while this change is open.
  - Literal pins for the directory table, plus an L0 test of the export's commit comment.
  - An old-interpreter parse test.
  - Probe glue tests on a real installer-filled home, plus recorded outcomes.
  - The sibling-path exemption removed from `test_script_paths.py`, and the spec requirement modified to match.
  - The xdist race on tampered documents: the tamper test now works on a copy, and the real-tree readers joined the sync group.
  - The pre-commit hook no longer stages unchanged README or guide.
  - `install-check --ref` reads everything from the export.
  - APPDATA isolation in the installer tests.
  - AGENTS.md counts.
- **Refuted.**
  - Zip-slip on the skill-folder name (subsumed by the name pattern).
  - "Approve every command" advice being unsafe.
  - Missing failure guidance (an "If it does not work" note was added anyway).
  - Gemini CLI named as an example host.

**Merge of main, 2026-10-05 (5437e66).** Main had rewritten the dev runner (subscription judge, `model_env`, `RunnerFailure`, `isolated_config`) and no longer imports `prepare_config`. The probe now enters `isolated_config` like every isolated dev run, so the stored-login write-back covers it, and reports with the dev runner's exit statuses and `--summary-log`. Its `HOME` override is layered on `model_env`'s environment. Not re-run live: the merge changed the probe's plumbing, not its request or verdicts. After the merge, `uv run poe test` passed 2484 with 2 skipped, `poe specs` is valid, and `poe install-check` passed both arms on the merge commit.
