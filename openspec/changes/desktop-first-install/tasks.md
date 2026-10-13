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

## 8. Maintainer verification (manual, against main)

- [x] 8.0 Merge into `main` before the runs. On 2026-10-05 the maintainer decided against a separate test branch: everything lands on `main` and the runs happen there, with the shipped prompt and the plain marketplace `hutzelmann/thesis-proposal-skills`. This replaces the earlier rule that the change stays off `main` until the runs pass.
  - Until a recipe is run, it stays stamped `*unverified*` on `main`, and the change stays open.
  - The release is the push of `main`, which only the maintainer does.

- [ ] 8.1 ChatGPT desktop app (Codex view, free plan): paste the prompt in a fresh folder, answer the scope question, approve as asked, open a new chat, then ask "help me develop a thesis idea". Record the app version and date in the recipe stamp.
- [ ] 8.2 Claude desktop: run the plugin button (Customize > Plugins > Add marketplace > `hutzelmann/thesis-proposal-skills`) on a paid plan, and the prompt in the Code tab on another machine or a clean profile. Stamp the recipe. This run also settles design D7's open question: does claude.ai honour the marketplace entry's `skills` list, and do all eleven skills appear under Customize > Skills? Also paste the prompt once into the Chat tab and check that the agent stops with the chat-only pointer instead of installing into its sandbox.
- [ ] 8.3 VS Code with GitHub Copilot, or the Copilot app: run the prompt as the recipe says, and check whether the skills show twice. VS Code reads both `~/.agents/skills` and `~/.claude/skills`, and its dedupe is not documented. Stamp it.
- [ ] 8.4 Antigravity: run the prompt and approve the network access. Stamp the recipe.
- [ ] 8.5 Cursor: run the prompt and check whether the skills show twice. Stamp the recipe.
- [ ] 8.7 After section 9 has landed on `main`, on a clean Windows machine, confirm the Python path the guide gives:
  - install "Python install manager" from the Microsoft Store;
  - paste the prompt and watch the first version check download Python, after the agent asks for network access;
  - check that `python`, not `python3`, is what then answers;
  - check the installer's readiness lines: the Python that ran it, and the Store-shortcut line exactly when only the Store's `python3` is present (this confirms the marker pinned in 9.1).

  Then, on a Windows machine (or a clean profile) whose only Python is uv-managed (`uv python install`, no python.org, Store or install-manager Python):
  - paste the prompt and confirm that one of the further probes (`uv python find ">=3.11"`, a versioned name, or `py -0p`) finds that Python, the installer runs with it, and the agent does not tell the student to install Python;
  - in a new chat, ask for a check of a proposal and confirm that the script-bearing skill runs with that interpreter, per the interpreter clause. If it cannot find it, settle design D13's open question: the clause also names the further probes.

  Correct the "No Python yet?" subsection if any of that differs. On a Mac, likewise confirm that the python.org installer followed by Install Certificates.command leaves the literature search working. Record the app, Windows build, Python and uv versions in the notes.
- [ ] 8.6 After section 9 is complete: remove any recipe not run (with the matching edit to `test_install_docs.py::test_the_featured_apps_have_recipes`), re-run `python3 scripts/sync_shared.py`, and archive the change on `main`. Archiving makes `test_install_docs.py` reject any recipe still stamped `unverified`.

## 9. Revision 2026-10-13: finding Python, the interpreter clause, apps' own folders, readiness lines

Design D12–D15. Implemented off `main`; lands there as one complete commit (task 9.11). Python discovery and readiness lines are verified on Windows only by task 8.7; the host runners are Linux-only.

- [x] 9.1 Pin the facts the revision depends on, each recorded in the notes below with its source and date:
  - OpenCode's skill folders and load order. Re-check the 2026-10-13 reading of `anomalyco/opencode` (`dev`, c1615b1): `config/plugin/compatibility.ts`, `config/plugin/skill.ts`, `plugin/internal.ts:265-266`, `state.ts`, `skill.ts`. Record the commit used; the `NATIVE_DIRS` comment cites it.
  - That `uv python find ">=3.11"` only searches and never downloads, and what it prints.
  - What `py -0p` lists under the Python install manager and under the legacy launcher, and whether `py -3` passes over uv (Astral) and Anaconda registrations.
  - The on-disk marker that tells the App Installer's Store `python3` shortcut apart from the Python install manager's `python3` alias, readable without running either.
  - The user-level skill folders of Codex, Cursor and Copilot that design D3 names.

  Verify: every bullet has a source and a date in the notes. A fact that contradicts the design is raised before code is written.
- [x] 9.2 Extend step 1 of `shared/blocks/install-prompt.md` (design D12). Keep the three probes and their order. Add, only for when none reports 3.11 or newer:
  - `uv python find ">=3.11"` when uv is installed;
  - one lookup for versioned `python3.X` names on the PATH;
  - `py -0p` on Windows;
  - "use the first that reports 3.11 or newer".

  The stop-and-guide sentence follows them unchanged. Run `python3 scripts/sync_shared.py` to regenerate `README.md` and `docs/install.md`.

  Verify: new tests in `tests/unit/test_install_docs.py` check that:
  - the prompt names `uv python find` with `>=3.11` and never `uv python install`;
  - it names a versioned-name lookup and `py -0p`;
  - all three come after `py -3 --version` and before the install guidance;
  - the existing link test still passes.

  `sync_shared.py --check` is clean.
- [x] 9.3 Add the interpreter clause (design D13) to the eight script-bearing `SKILL.md` files, appended to each `${CLAUDE_SKILL_DIR}` fallback paragraph: check, import, lit-search, publish, reverse, supervise, troubleshoot, write. Finalize the wording once and use it identically in all eight. Then:
  - remove the seven Windows parentheticals: check (Run line), import (reference validation, check), reverse, supervise, write, and publish's "on Windows use `py` if `python3` is absent";
  - replace proposal-check's `winget install Python.Python.3.12` / `brew install python` advice with a link to `https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#no-python-yet`, keeping its reduced-determinism fallback;
  - leave publish's pandoc/typst `winget` line alone (`add-setup-readiness-guide`).

  Verify:
  - new tests in `tests/unit/test_script_paths.py` check that every script-bearing skill carries the clause's core substring exactly once, inside the paragraph that holds "leaves it unexpanded";
  - no `SKILL.md` contains a `py` instead-of-`python3` parenthetical or `winget install Python`;
  - no `SKILL.md` names `AGENTS.md` or `CLAUDE.md` (none does today), so no skill tells the agent to record the interpreter there;
  - `test_install_docs.py`'s link test is extended to `install.md#…` links in `SKILL.md` files;
  - `test_skill_frontmatter.py` (line and median-proportion caps), `test_skill_header_pattern.py`, `test_audit_invariants.py` and the mandate pins pass unchanged.
- [x] 9.4 Add `NATIVE_DIRS` to `install.py` (design D14): detection on every run in either scope, listing with the other-scope wording, removal under `--remove-other`, the `--dry-run` line, and the `--remove-other` help text. Keep the user-side rules: stdlib only, and the module still parses with `feature_version=(3, 7)`.

  Verify: new cases in `tests/unit/test_install.py`, under both scopes:
  - a hand copy in `./.opencode/skills` and in `~/.config/opencode/skill` is listed and kept, exit 0;
  - copies in `~/.codex/skills`, `~/.cursor/skills` and `~/.copilot/skills` are listed;
  - `--remove-other` removes exactly the listed `proposal-*` entries, while an unrelated skill, a non-shipped `proposal-*` folder and other files in the same folder stay;
  - a folder without a `SKILL.md` is ignored;
  - a symlink into the installed copy is neither listed nor removed. On the Windows CI job, the same holds for a junction;
  - a link to a copy elsewhere is listed, and removed as a link with its target intact;
  - a copy in an app folder that is itself a link to a folder elsewhere is listed, kept under `--remove-other` with the reason stated, and the linked-to tree survives;
  - `--dry-run` names the copies and removes nothing;
  - no folder in the table is ever created;
  - a literal pin of the table, disjoint from `SHARED_DIRS` and `HOST_DIRS`.

  Coverage of `install.py` stays ≥ 90%.
- [x] 9.5 Add the readiness lines (design D15) to the end of a successful run's and a dry run's output. Use presence only: the Python version and executable file name; on Windows, the Store-shortcut line from the marker pinned in 9.1; `shutil.which` for `pandoc` and `typst`; `is_file` for `api-keys.env` in the working folder and `~/.config/thesis-proposal/`. Nothing is run, opened or recorded.

  Verify: new cases in `tests/unit/test_install.py`:
  - with an empty tool PATH, both PDF tools are reported missing and marked optional, and the exit code is 0;
  - with stub executables on a temporary PATH, both are reported found, and none is executed (`subprocess.run` patched to fail the test);
  - the Store-shortcut line appears for a planted App Installer alias layout under a temporary `LOCALAPPDATA` and not for the install manager's layout, with the Windows check isolated behind a function that tests can call on Linux;
  - an `api-keys.env` holding a sentinel value in the working folder, and another in `~/.config/thesis-proposal/`, are reported present. The sentinel appears in no stdout, stderr or record, and the file is not opened (`Path.read_text`/`open` on it patched to fail);
  - no readiness fact appears in the record;
  - the lines appear in a dry run too.
- [x] 9.6 Paths with spaces and a user name. Use a temporary HOME named `Erika Musterfrau` and a working folder `My Proposals` inside it.

  Verify: a new parametrized case in `tests/unit/test_install.py`, for both scopes, with an OpenCode hand copy and an `api-keys.env` present:
  - the install completes byte-identically;
  - records, the other-scope and apps'-folder listings, and the readiness lines all show `~/…` or `./…` paths;
  - `Erika Musterfrau` appears in no stdout, stderr or record.
- [x] 9.7 Mirror `NATIVE_DIRS` in `skills/proposal-troubleshoot/scripts/collect.py` (design D14): restate the table, add its folders to the hashed roots, and add one `[measured]` line per folder holding a copy, home- or workspace-relative.

  Verify:
  - `tests/unit/test_troubleshoot_collect.py::test_locations_match_the_repository_installer` asserts that the collector's table equals `install.NATIVE_DIRS`;
  - new cases: an OpenCode hand copy beside an installer install is hashed and its folder named, with no home path in the report, and a link from an app's folder into the installed copy is hashed once;
  - the collector running from a hand copy in OpenCode's folder (`collect.HERE` patched there) still names that folder;
  - `test_script_paths.py` and `test_audit_invariants.py` pass.
- [x] 9.8 `docs/install.md`, "Any other agent": add one sentence. An earlier manual copy in OpenCode's own folders (`.opencode/skills`, `~/.config/opencode/skills`) can shadow the installed skills; the installer lists it and removes it only if you agree. Add no OpenCode recipe.

  Verify: `test_install_docs.py` passes, and `git grep -n "opencode" docs/install.md` shows the sentence under that heading only.
- [x] 9.9 Add the optional probe variant `install_prompt_versioned_python` (design D10) to `harness/claude_runner.py`:
  - Linux only, pre-answered;
  - a scratch PATH of links without `python`, `python3`, other `python3.X` or `uv`, plus one `python3.N`;
  - add `verdict_install_prompt_found_python` to `harness/l1_checks.py`;
  - describe it in `harness/README.md`.

  Verify:
  - L0 tests in `tests/unit/test_install_probe.py` cover the verdict on synthetic outcomes: a pass; a final message that sends the student to install Python; an incomplete install;
  - the PATH builder leaves no Python name but the versioned one;
  - `test_repo_conventions.py` finds an L0 test for the new verdict.

  Do not run it live here.
- [x] 9.10 On the maintainer's go-ahead only ($0, subscription): run `uv run poe dev install_prompt` and `install_prompt_answered` with sonnet and haiku on the final prompt, and `install_prompt_versioned_python` with sonnet. Record verdict, cost, turns and helper telemetry in the notes, as in 6.3. Until the go-ahead, this task stays open and the notes say the prompt change is unprobed.
  - *Done 2026-10-13 on the maintainer's go ("Commit + run 9.10/9.11"), on the committed revision 4a11adb, Claude Code 2.1.296, subscription:* all five PASS, no helper agents in any run.
    - `install_prompt`: `claude-sonnet-5-5` 2 turns, `claude-haiku-5-5` 2 turns — "asked the scope question and installed nothing yet".
    - `install_prompt_answered`: `claude-sonnet-5-5` 3 turns, `claude-haiku-5-5` 5 turns — "11 skills byte-identical with a record in 2 directories, no stray copies".
    - `install_prompt_versioned_python`: `claude-sonnet-5-5` 5 turns — "found the versioned Python without sending the student to install one; 11 skills byte-identical with a record in 2 directories, no stray copies".
- [x] 9.11 Gate: `uv run poe test` green, `uv run poe cov` holds the floor, `uv run poe specs` validates strictly, and `uv run poe install-check` passes both arms on the revision's tree (`--ref` before committing). Then land the revision on `main` as one complete commit and run `python3 scripts/sync_shared.py` after the merge.
  - *Done 2026-10-13:* `poe test` 3452 passed, 2 skipped; `poe cov` 92.20% (install.py 96%); `poe specs` 18/18; the revision landed as one commit, 4a11adb; `poe install-check` on 4a11adb passed both arms ("11 skills through the skills CLI and the installer, byte-identical, records name 4a11adb9f894, smoke green"); `sync_shared.py --check` clean (no merge involved).

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

**Merge of main, 2026-10-05 (fefeced).** This merge brings in isolate-child-environment. An isolated `model_env` now returns the allowlisted `routing.isolated_env`, and the probe's `HOME`/`USERPROFILE` override is still applied after it. The admitted `XDG_*` variables keep pointing at the operator's home, but `install.py` derives every target from `Path.home()` and reads only `APPDATA` (Windows), so the probe's scratch home stays the only place it writes. Two conflicts, both resolved by keeping both sides:
- `harness/l1_checks.py`: main's `verdict_cache_reuse` and the install verdicts were both appended at the end of the file.
- `AGENTS.md` line 7: the branch's sentence naming the install routes was kept.

**Revision, 2026-10-13 (section 9).** The maintainer folded these into this change on 2026-10-13, from a student's setup report (Windows, OpenCode):
- all three further Python probes, plus the one interpreter clause in the skills;
- no instruction anywhere to record the interpreter in `AGENTS.md` or `CLAUDE.md`;
- readiness lines in the installer, with the docs checklist left to `add-setup-readiness-guide`;
- apps' own skill folders listed, and removed only on consent;
- folding all of it in now rather than in a new change.

Already read for 9.1, still to be re-checked at implementation: OpenCode `dev` at c1615b1. `internal.ts:265-266` registers `ConfigCompatibilityPlugin` (`.claude`/`.agents` `skills`) before `ConfigSkillPlugin` (`skill`/`skills` under `.opencode` and `~/.config/opencode`). `state.ts` applies transforms in registration order. `skill.ts`'s `add` is `Map.set`, so the last copy wins. Separately, `skill.ts` tells the agent "Base directory for this skill: <dir>", so the existing prose fallback already resolves scripts in OpenCode and needs no OpenCode path note. Until 9.10 runs, the prompt change is unprobed.

**9.1 — facts pinned 2026-10-13.** No fact contradicts the design.

- **OpenCode load order.** Re-read at `anomalyco/opencode` `dev` = `c1615b1db9c2e7a955f2be1024e84bb74c90cc6b` (the branch head on 2026-10-13), raw files under `packages/core/src/`:
  - `config/plugin/compatibility.ts:40` joins `skills` onto the `.claude` and `.agents` roots;
  - `config/plugin/skill.ts:85-88` adds `skill` and `skills` under every config directory entry (`.opencode` up the project, `~/.config/opencode`);
  - `plugin/internal.ts:265-266` registers `ConfigCompatibilityPlugin` before `ConfigSkillPlugin`;
  - `state.ts:19,178-180`: reads rebuild by applying every registered transform in order;
  - `skill.ts:100-101`: the editor's `add` is `editor.skills.set(skill.id, …)`, so the last copy wins.

  Confirms D14. `NATIVE_DIRS` cites the full commit.
- **`uv python find ">=3.11"`** (uv 0.11.11, run locally): prints one line, the interpreter's path, exit 0; with no match it prints "error: No interpreter found for Python … in virtual environments, managed installations, or search path", exit 2. With downloads left at uv's default (`automatic`) and an empty `UV_PYTHON_INSTALL_DIR`, `uv python find --no-project 3.9` found nothing and the install folder stayed empty: it searches, never downloads. Inside a project it reports the project's `.venv` first, which is still a 3.11+ interpreter.
- **`py -0p`.** CPython `Doc/using/windows.rst` (main, read 2026-10-13), "Listing runtimes": the install manager keeps `--list`, `--list-paths`, `-0` and `-0p` "for compatibility with the old launcher", with legacy output (tag and path per runtime). Its `include_unmanaged` setting (default true) lists runtimes it did not install, i.e. PEP 514 registrations such as uv's (Astral) and Anaconda's. Listing is not a launch command, so it never triggers the "no runtimes installed → install the latest" behaviour of "Basic use". Under the legacy launcher, `-0p` lists every PEP 514 registration with its path, while the short `-3` is the `V:`-less form that `windows.rst` allows only "where the tag refers to an official release" (company `PythonCore`; other distributors need `-V:Company/…`), so `py -3` passes over Astral and ContinuumAnalytics entries. Live output on Windows is task 8.7's.
- **Store-shortcut marker.** The App Installer package (`Microsoft.DesktopAppInstaller_8wekyb3d8bbwe`, the package that also ships winget) owns the `python.exe`/`python3.exe` App Execution Aliases that open the Store (elevenforum.com thread 24886, "What are python.exe and python3.exe, and why do they appear to point to App Installer?"). Aliases live as reparse points in `%LOCALAPPDATA%\Microsoft\WindowsApps`, with a per-package folder beside them; the install manager's own commands sit in `WindowsApps\PythonSoftwareFoundation.PythonManager_qbz5n2kfra8p0` (Store) or `…_3847v3x7pw1km` (python.org) per CPython `windows.rst` ("Advanced installation"), and the old Store Pythons in `PythonSoftwareFoundation.Python.3.X_qbz5n2kfra8p0`. Pinned marker: `WindowsApps\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\python3.exe` exists, no `WindowsApps\PythonSoftwareFoundation.*\python3.exe` exists, and the first PATH folder holding `python3.exe` is `WindowsApps`. Read with `lstat` only; nothing is run. Task 8.7 confirms it live.
- **Codex, Cursor and Copilot user folders.**
  - Codex: `openai/codex` main `90f00bd` (2026-10-13), `codex-rs/ext/skills/src/host_roots.rs:96`: "Deprecated user skills location (`$CODEX_HOME/skills`), kept for backward compatibility"; `~/.agents/skills` is the current one (`AGENTS_DIR_NAME`, line 24).
  - Cursor: cursor.com/docs/context/skills (2026-10-13) names `~/.cursor/skills/` beside `~/.agents/skills`.
  - Copilot: docs.github.com, "About agent skills" (2026-10-13): personal skills in `~/.copilot/skills` or `~/.agents/skills`.

**9.2–9.9 — implemented 2026-10-13, off `main`, uncommitted.** Defaults from the maintainer's approval: the interpreter clause is D13's draft wording verbatim (8.7's uv-only run may refine it); no "don't clone this repository" warning here; the key-file line ignores `$THESIS_PROPOSAL_KEYS`; only shipped skill names count as copies in apps' own folders; a link pointing outside the installed copy is listed and removed as a link, never its target.

- **9.2.** Step 1 gains the three read-only probes between `py -3 --version` and the install guidance, under "look further without downloading or installing anything". `README.md` and `docs/install.md` regenerated. `test_install_docs.py::test_the_prompt_looks_further_before_it_reports_no_python` pins names, order and the absence of `uv python install`; the link test passes.
- **9.3.** The clause is appended to the fallback paragraph of check, import, lit-search, publish, reverse, supervise, troubleshoot and write. Seven Windows parentheticals removed; proposal-check now links `…/docs/install.md#no-python-yet` and keeps its reduced-determinism fallback; publish's pandoc/typst `winget` line untouched. New in `test_script_paths.py`: the clause once, inside the "leaves it unexpanded" paragraph; no per-command `py` hint, `winget install Python` or `brew install python`; no `AGENTS.md`/`CLAUDE.md` in any `SKILL.md`. The link test now reads every `SKILL.md`. Frontmatter caps (lines, median proportion), header pattern, audit invariants, pinned sentences, execution shape and mandate pins pass unchanged.
- **9.4.** `install.NATIVE_DIRS` (seven entries, sources and commit in its comment) and `native_copies`: a shipped name in the folder, a real folder or a link holding `SKILL.md`, skipped when it resolves into a directory this run fills (a linked parent folder included). `run` was split into `Plan`, `report_copies`, `report_dry_run` and `install` to stay under the complexity cap. Ten new test functions in `test_install.py` (fourteen cases) cover both scopes, removal of exactly the listed entries, folders without `SKILL.md`, symlinks into the installed copy (junction case on the Windows job), links elsewhere removed as links, `--dry-run`, no folder created, and the literal pin disjoint from `SHARED_DIRS`/`HOST_DIRS`. The 3.7 parse test passes. Review fix: `through_linked_folder` marks a copy whose app folder is reached through a link or junction; it is listed, kept under `--remove-other` with the reason, and named separately in a dry run (`test_a_copy_in_a_folder_linked_elsewhere_is_listed_but_never_removed`).
- **9.5.** `readiness_lines`/`report_readiness` end every successful and dry run with "On this computer:". `store_python3_only(LOCALAPPDATA, PATH)` reads the 9.1 marker with `lexists` only and is called on Windows. Tests: empty PATH → both PDF tools missing and optional, exit 0; stub tools found with `subprocess.run`/`Popen` patched to fail; the Store layout vs the install manager's and vs an earlier real `python3.exe`; a sentinel `api-keys.env` in both places reported present with `open`/`Path.read_text`/`read_bytes`/`open` patched to fail on it, the sentinel in no stream or record; no readiness fact in the record; a dry run carries the lines; a refused install prints none.
- **9.6.** `test_a_home_with_a_user_name_and_spaces_never_shows_the_name[all|folder]`: HOME `Erika Musterfrau`, working folder `My Proposals`, an other-scope install, OpenCode copies in both bases, key files in both places. Byte-identical install; records, listings and readiness lines are `~/…`/`./…`; neither the name nor the sentinel appears in stdout, stderr or records.
- **9.7.** `collect.NATIVE_DIRS` restated, `native_roots` added to the hashed roots, and `native_lines` adds "[measured] skill copies in <~/… or ./…> (<app>'s own skill folder), which may shadow the installed skills: <names>". The equality assert joined `test_locations_match_the_repository_installer`; new cases cover a hand copy hashed and named with no home path, a workspace OpenCode folder, unshipped or incomplete entries, and a link into the installed copy hashed once and not named. Review fix: the collector's own skills folder no longer counts as installed when it is one of the apps' own folders, so a collector loaded from the shadowing copy still names it (`test_a_collector_run_from_the_shadowing_copy_still_names_it`).
- **9.8.** One sentence under "Any other agent"; `git grep -n opencode docs/install.md` shows only that paragraph (line 123).
- **9.9.** Scenario `install_prompt_versioned_python` (`versioned_python: True`), `versioned_python_path`, `probe_search_path` (a runner failure off Linux), and `run_claude(path=…)`. `verdict_install_prompt_found_python` lives in `l1_checks.py`. `harness/README.md` describes it. Tests in `test_install_probe.py`: a pass, four install-advice failures, an incomplete install, the PATH builder (only `python3.14` among Python names, first of each name wins), and the scratch PATH reaching the host. Not run live.

**Gate, 2026-10-13 (without network or push):** `uv run poe test` 3450 passed, 2 skipped, ruff clean, drift check clean, 11 skills conform. `uv run poe cov` 92.17% (floor 78%), with `install.py` 96%, `collect.py` 94% and `claude_runner.py` 93%. `uv run poe specs` 18 passed. `python3 scripts/sync_shared.py --check` clean. `poe install-check` was not run (networked); 9.11 stays open for it, for the commit and for the post-merge sync. Until 9.10 runs, the prompt change is unprobed.
