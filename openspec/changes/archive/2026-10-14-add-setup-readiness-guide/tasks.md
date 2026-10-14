# Tasks

Implement on a working copy off `main` and land as one commit. `desktop-first-install`'s section-9 revision (4a11adb) is already on `main`. Run this change after that revision and before `classify-arxiv-answers` and `tighten-proposal-family`, because they share `skills/proposal-lit-search/SKILL.md`. Never in a parallel session: the pre-commit hook stages every sync destination.

## 1. Offline guards first (TDD; they fail until sections 2–4 land)

- [x] 1.1 Add a winget-form helper to `tests/helpers.py` (design D5; it has three call sites). It finds every `winget install` command in a text and reports one problem string per command that breaks the rule:
  - exactly one id follows `--id`;
  - no further positional token appears;
  - `-e`/`--exact` is present.
  
  Self-test it in `tests/unit/test_publish.py`. `winget install --id JohnMacFarlane.Pandoc Typst.Typst` and `winget install --id Typst.Typst` are each reported, and `winget install --id Typst.Typst -e` is clean. Verify: these self-tests pass now.
- [x] 1.2 `tests/unit/test_publish.py` gains `INSTALL_HINT` tests:
  - the helper reports nothing for `publish.INSTALL_HINT`;
  - the hint names both `JohnMacFarlane.Pandoc` and `Typst.Typst`;
  - the hint carries `https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#pdf-export`;
  - the same helper reports nothing for the publish `SKILL.md`'s "When tools are missing" section.
  
  Verify: they fail on today's text.
- [x] 1.3 `tests/unit/test_install_docs.py` gains the guide tests:
  - (a) "What you need" holds a table whose rows name an agent app, `Python 3.11`, `pandoc` with `typst` and LaTeX, and an API key. The PDF and key rows say "optional".
  - (b) "Is everything working?" holds exactly four numbered items, each carrying `Shows:`, `Does not show:` and `If not`. The items mention, in order: eleven skills, `--help`, `sources:`, and "Build a PDF". The section names `On this computer:`.
  - (c) The checklist's quoted tokens match the code. The test calls `install.report_readiness` with a temporary home and working folder, and its output contains `On this computer:`. It runs `search.federate` in-process with one stub source registered through `monkeypatch.setitem(search.SEARCH_SOURCES, …)`, and stderr contains a line starting `sources: `.
  - (d) "PDF export" holds the following:
    - no version-like token (regex `\bv?\d+\.\d+(?:\.\d+)?\b`);
    - links to `github.com/typst/typst/releases/latest` and `github.com/jgm/pandoc/releases/latest`, and no other `releases/` path;
    - the words `SHA-256`, `certutil -hashfile`, `shasum -a 256` and `sha256sum`;
    - an instruction to delete a mismatching file;
    - no `sudo`, and the words "do not repair or reset" for the package manager;
    - winget lines that pass the 1.1 helper.
  - (e) Neither `docs/install.md` nor `README.md` matches `\bproposal folders?\b` (case-insensitive).
  - (f) The guide states that the proposals folder is not a clone of this repository, and names `AGENTS.md` as not to be copied.
  
  Verify: (a), (b), (d) and (f) fail on today's guide, (c) passes once (b) passes, and (e) fails until README and the Notes are fixed.
- [x] 1.4 Extend `test_every_link_into_the_guide_names_an_existing_section` in `tests/unit/test_install_docs.py`:
  - it also reads `publish.INSTALL_HINT`;
  - it asserts that `proposal-publish` is among the linking skills;
  - it asserts that README links `docs/install.md#is-everything-working`.
  
  Verify: it fails until `#pdf-export` and `#is-everything-working` exist and publish and README link them.
- [x] 1.5 `tests/unit/test_audit_invariants.py` gains two tests:
  - `test_publish_carries_no_download_steps`: none of `releases/latest`, `releases/download`, `curl `, `wget `, `Invoke-WebRequest`, `certutil`, `shasum`, `sha256sum`, `Expand-Archive`, `tar x` appears in `skills/proposal-publish/SKILL.md` or `skills/proposal-publish/scripts/publish.py`;
  - `test_lit_search_ignores_the_key_file_in_every_workspace`: the lit-search `SKILL.md` no longer contains `if the workspace is a git repo`.
  
  Verify: the first passes now and must stay green, and the second fails on today's text.
- [x] 1.6 Add the pin `tests/unit/data/pinned_sentences/proposal-lit-search--key-file-ignored.txt` holding `creating that file if there is none, whether or not the workspace is a git repository yet`. Verify: `test_pinned_sentences` fails until 3.1 lands.

Red run, 2026-10-13, before sections 2–4: `uv run pytest tests/unit/test_publish.py tests/unit/test_install_docs.py tests/unit/test_audit_invariants.py tests/unit/test_pinned_sentences.py` → 13 failed, 205 passed. The failures were 3 publish hint/skill tests, the link test, the 6 new guide tests plus the 2 terminology cases, the lit-search ignore guard and the new pin. The winget self-test and `test_publish_carries_no_download_steps` passed.

## 2. `proposal-publish`

- [x] 2.1 In `skills/proposal-publish/scripts/publish.py`, replace `INSTALL_HINT` with design's draft:
  - two `winget install --id … -e` lines;
  - the "No package manager, or it reports an error about its sources? See …#pdf-export" line.
  
  The LaTeX-tier note, engine resolution and exit codes stay unchanged. Verify: 1.1, 1.2 and the engine and handover tests in `test_publish.py` are green.
- [x] 2.2 In `skills/proposal-publish/SKILL.md` "When tools are missing":
  - the pandoc + typst bullet gives the two winget commands;
  - one new bullet points to the guide's PDF-export section by its published URL, instead of repairing the package manager.
  
  No download, hash or extraction step. Verify that these are green:
  - 1.2's `SKILL.md` case, 1.4 and 1.5;
  - `test_skill_frontmatter` (line cap and sibling proportion);
  - `test_skill_header_pattern`;
  - `test_report_offer`;
  - `test_script_paths`.

## 3. `proposal-lit-search`

- [x] 3.1 In `skills/proposal-lit-search/SKILL.md`'s key-setup bullet, replace "ensure `.gitignore` covers `api-keys.env` (add the entry if the workspace is a git repo — the file holds a secret)" with design's draft clause, which carries the pinned phrase. Leave the interpreter-clause paragraph and the secret rule untouched. Verify that these are green:
  - 1.5 and 1.6;
  - `test_lit_search_keeps_no_hand_through_rule`;
  - `test_no_secret_value_through_agent`;
  - the lit-search body under the sibling ceiling.

## 4. `docs/install.md` and README wording

- [x] 4.1 Add `## What you need` directly after the introduction: design's tier table plus the proposals-folder sentence (not a clone, `AGENTS.md` not copied). Verify: 1.3 (a) and (f).
- [x] 4.2 Add one sentence to the Recipes intro that points to `#is-everything-working`, and add `## Is everything working?` after "Chat-only apps", with design's four checks and the `On this computer:` paragraph. Verify: 1.3 (b) and (c), and the link test.
- [x] 4.3 Add `## PDF export` after "Literature search cannot reach its sources", with design's text, and remove the Notes' "PDF export." bullet. Verify:
  - 1.3 (d) and 1.4;
  - `test_offline_advice_names_every_service_the_search_contacts` is still green, because the new section names no API host in backticks.
- [x] 4.4 Two wording changes:
  - in "What you get in the folder", replace the last paragraph with design's `[paths] proposals` paragraph (flat by default, when a subfolder is worth it, and `guidelines.md` and `api-keys.env` stay at the top);
  - reword the Notes' "API keys." bullet as drafted: "proposals folder", the student pastes the key, the agent never sees it, and `.gitignore`.
  
  Verify: 1.3 (e) for `docs/install.md`.
- [x] 4.5 Two README edits, both outside the generated install-prompt region:
  - in "For supervisors", change "their proposal folder" to "their proposals folder";
  - in the quick start, add design's one-line pointer to `docs/install.md#is-everything-working` after step 4.
  
  Verify: 1.3 (e) for README, 1.4's README assertion, and `python3 scripts/sync_shared.py --check` is clean.
- [x] 4.6 In `docs/backlog.md` "Evaluation and measurement", add design's entry for the deferred dev-runner scenario that would measure the non-git key-file ignore. Name this change's archive folder as the evidence, with the date filled in at archive time. Verify: the entry is present, and no other backlog line changes.
  - Done before archiving: the entry cites `openspec/changes/add-setup-readiness-guide/design.md` (D7). The archive step rewrites that to `openspec/changes/archive/<date>-add-setup-readiness-guide/design.md`.

Green run, 2026-10-13, after sections 2–4: the same four test files → 218 passed, and `python3 scripts/sync_shared.py --check` reports "generated copies in sync".

## 5. Verification

- [x] 5.1 Moved on 2026-10-14, at the maintainer's decision, into `desktop-first-install` task 8.7, which runs in the same Windows/Mac session; this change was archived before that run so that `add-proposal-folders` could change "Users never work in this repository" after it. The checks as originally planned, Windows and Mac, in the same session as `desktop-first-install` task 8.7, not as a landing gate:
  1. Run both winget lines from the guide on a machine with a working winget source, and confirm that each installs its tool.
  2. On a machine whose winget source errors (or with winget skipped), follow the archive route for typst once: latest release, `certutil -hashfile` against the page's digest, a user-owned folder on PATH, `typst --version`.
  3. On a Mac, if one is available, confirm whether a browser-downloaded typst archive opens, or whether the Homebrew sentence is needed as written.
  
  Correct the wording only where the run differs, and record the Windows build, winget version and date in this file. Verify: the notes are recorded here.
- [x] 5.2 `uv run poe test` green: pytest with the new tests, ruff including the complexity cap, the drift check and conform. Verify: exit 0, with the counts recorded here.
  - 2026-10-13, main checkout at a38b7b1 plus this change: exit 0, 4474 passed, 2 skipped; ruff clean; "generated copies in sync"; all 11 skills conform.
- [x] 5.3 `uv run poe specs` and `openspec validate add-setup-readiness-guide --strict` green. Verify: exit 0 for both.
  - 2026-10-13: 19 passed, 0 failed; the change is valid.
- [x] 5.4 `uv run poe cov` holds the floor. The only code change is the `INSTALL_HINT` constant. Verify: exit 0.
  - 2026-10-13: total 93.89 % (floor 78 %).
