**Approved 2026-10-14.** The maintainer answered the design's Q1–Q8 (every recommendation accepted; Q5 "leave, name, offer rebuild") and decided that the block lists the family once as a role table with today's names (design, decision log, last part). Tasks marked with a question follow that answer. Group 8.3's subscription runs are run one at a time in a later phase. Group 10 carries the maintainer's answers to the approval request (2026-10-14).

**Where to work.**
- Implement on a working copy off `main` after #5 (`widen-lit-live`) and #6 (`utf8-script-output`), both landed. Land as one commit. `utf8_output()` stays the first statement of every user-side `main()`, and a new subprocess capture of script output names `encoding="utf-8"`.
- Never work in a parallel session that shares the checkout: `.githooks/pre-commit` refuses a commit whose staged copies drift.
- After editing `check.py` or `shared/blocks/`, run `python3 scripts/sync_shared.py` and stage what it lists. Never edit the five `check.py` copies or a materialized `SKILL.md` region by hand.
- No model calls outside group 8. No metered run at all.

**Baseline before any edit:** `uv run poe test` green. Record the per-skill body word counts and the median.

## 1. Measurement (no model call, $0)

- [x] 1.1 Record the host caps, then measure the search output (Q1).
  - **Caps.** From pinned sources only, no model call: Claude Code's default Bash output cap (`BASH_MAX_OUTPUT_LENGTH`); Codex's exec-output truncation at the commit `install.py` pins; OpenCode's bash tool limit at the commit `install.py` pins; Copilot's, if its documentation states one. Record each with its unit (characters, bytes, lines) and its source, or "not found".
  - **Runs.** Pick two DOIs from `tests/fixtures/w03-snowball-seed/serverless-energy-scheduling.md`. Run `python3 skills/proposal-lit-search/scripts/snowball.py <doi1> <doi2> --limit-per-seed N` with N = 5, 8, 10, 12 and 20, and `search.py "<w03 topic terms>" --limit 10` and `--limit 6`. Run from a scratch directory, with stdout to the scratchpad and never into the repository. Run keyless, and once more keyed only if an OpenAlex key resolves through the shipped lookup (`$THESIS_PROPOSAL_KEYS` or `~/.config/thesis-proposal/api-keys.env`); never load the repository's `.env`. For each run, record candidates, lines and characters on stdout, the `sources:` and degradation lines, and the per-seed, per-direction counts.
  - **Decide.** Under Q1 (i): the threshold lies below the smallest recorded cap, in characters, plus a line bound if a cap is counted in lines. The default is the largest measured N whose two-seed run stays under the threshold, judged on the keyed run when there is one; if not even 5 fits, the default is 5 and the SKILL.md example snowballs one seed per call. Record whether the example's `--limit 10` stays.
  - Verify:
    - `openspec/changes/tighten-proposal-family/measurement.md` holds the caps table, the runs table, the threshold, the chosen default and the decision on the example;
    - if the threshold or the default differs from the provisional 25,000 characters and 5, the skill-lit-search delta and design D7 are updated through `openspec-update-change` before group 6 starts, and `openspec validate tighten-proposal-family --strict` passes.

## 2. Family vocabulary and the `companion-orphaned` warning (`check.py`, TDD)

- [x] 2.1 Write `tests/unit/test_check_family.py`, red first, using `tmp_path` workspaces. Cover:
  - `family_handles` and `family_member` for every row of design D6, with the kinds named by the block's roles (`FAMILY_ROLES`), including a `-review` file whose base is not in `handles` (returned as `proposal`) and a `-handout.md` with a metadata block (still `handout`);
  - an f00-style `ml-code-review.md` ending in a metadata block is a proposal; an `<old>-review.md` without one is an orphaned review of `<old>`;
  - `None` for `ideation.notes.md`, hidden names, names without a slug-shaped part, `guidelines.md`, `api-keys.env`, `bug-report/…`, `proposal-build`, `proposal-build.sh`, `Makefile`, `justfile`, `check-output.txt`, `version-output.txt`, `skills-lock.json`, `.gitignore`, `.agents/skills/…`, `.claude/skills/…`, `.kiro/skills/…`, `.opencode/skill/…`, `.opencode/skills/…` and `.thesis-proposal-install.json`;
  - orphan findings for a partial-rename workspace: one per leftover file, each naming the old slug;
  - none for a notes-sheltered `<idea>.notes.md` + `<idea>.reading-list.md`, and none for a lone `<thesis>.harvest.md`;
  - none for a w05-style workspace build: `proposal-build.sh`, `faculty.typ`, `proposal.pdf`, `img/logo.png`;
  - none for source documents and project files, each alone under its name: `submission.pdf`, `expose.docx`, `thesis.pdf`, `<name>-expose.pdf`, `vite.config.ts`, `data.tar.gz`, `img/screenshot.png`;
  - an unsheltered slug with two kept files is reported, and so is a built output under a reportable slug, but not under a workspace build;
  - a w07-style workspace (`[paths] proposals = "proposals/"`) with `<slug>.candidates.yaml` at the root: one finding naming the slug;
  - a stale `](img/<old>-x.png)` link, in both variants of the skill-check scenarios: with `<old>` resolvable the message names it, without it the message names only the linked path and the proposal's own slug;
  - exit code unchanged by the warnings, in human and `--json` output;
  - every file byte-identical after the run.

  Verify: the file fails against the current `check.py`.
- [x] 2.2 Implement design D6 in `skills/proposal-check/scripts/check.py`:
  - the constants (`FAMILY_ROLES` and `IDEATION_NOTES` included), `family_handles`, `family_member` and `family_findings`, with the signatures D6 pins;
  - `companion-orphaned` in a new `# workspace family` group after `proposal-misplaced` in `RULE_IDS`;
  - the call beside `paths_findings()`, with the governing `guidelines.md` passed for the root scan;
  - the messages naming the file, the slug, the partial-rename cause, and that a file placed on purpose can stay.

  Verify:
  - 2.1 green;
  - `uv run ruff check skills/proposal-check` clean, with complexity ≤ 12 and no new per-file ignore;
  - `python3 scripts/sync_shared.py` lists exactly the five copies, and `--check` passes.
- [x] 2.3 Add a pin test that `check.py`'s build-definition stem equals `publish.py`'s `BUILD_STEM`. Verify: it fails when either constant is edited alone.
- [x] 2.4 Change `tests/helpers.is_fixture_proposal` (design D6): keep `NON_PROPOSAL_MARKDOWN` and `NON_PROPOSAL_SUFFIXES`; for `-review` and `-feedback` files, replace the sibling test with `check.py`'s rule, `family_member` returning `proposal` and the file ending in a metadata block. Verify:
  - `uv run pytest tests/unit/test_fixture_oracles.py tests/unit/test_export_matrix.py` passes, w09–w12 unchanged;
  - new cases in `test_fixture_oracles.py`: an orphaned `<old>-review.md` without a metadata block is not a proposal; a leftover `<old>-handout.md` with one is not a proposal either.

## 3. Fixtures and oracles

- [x] 3.1 Create `tests/fixtures/w13-orphaned-companions/` per design D10. Generate the PNG as a minimal valid image, and calibrate `expected.json` against `check.py`: f28's findings plus the `companion-orphaned` warnings, with rule identifiers. Verify:
  - `test_oracle_holds[w13…]` and `test_oracle_rule_identifiers_hold[w13…]` pass;
  - no warning names `guidelines.md`, `ideation.notes.md` or `.agents/…`;
  - the export matrix builds the proposal.
- [x] 3.2 Create `tests/fixtures/w14-family-rename/` (design D10) with its oracle. Verify: its oracle holds with no `companion-orphaned`, and the export matrix builds it with the figure.
- [x] 3.3 Create `tests/fixtures/w15-provisional-notes/` with no proposal and no oracle. The notes file holds converged state: all five ideation aspects concrete, preamble facts recorded, no real names. Verify: no corpus walker takes any of its files for a proposal (`uv run pytest tests/unit/test_fixture_oracles.py`).
- [x] 3.4 Document w13–w15 in `tests/fixtures/README.md` under "Workflow-state fixtures". Verify: each entry states what the fixture carries deliberately and which scenario or oracle reads it, and no entry claims w16.

## 4. Shared block and materialization

- [x] 4.1 Write `tests/unit/test_workspace_files_block.py`, red first, modelled on `test_handoff_block.py`. Cover:
  - one `## Workspace files` section per skill, directly before `## Handing over`;
  - the section equals the block exactly, so an appended sentence fails;
  - the span covers exactly `WORKSPACE_FILES_PARAGRAPHS` paragraphs and never swallows a heading or an appended sentence;
  - a misplaced or duplicated section is an `AnchorError`;
  - a source with another paragraph count is refused;
  - the block's family table lists every role once: its roles equal `check.py`'s `FAMILY_ROLES` plus the ideation-notes row, both ways, each row's file-name shapes classify as that role, and the test fails naming a role either side lacks;
  - every name in `check.py`'s `WORKSPACE_LEVEL` and the build-definition forms appears in the block, and every backticked file name in the block is one `check.py` classifies or allows;
  - the block's installer folders equal the set read from `install.py`'s tables (the standard targets, the workspace target of each `HOST_DIRS` entry, the working-folder entries of `NATIVE_DIRS`), and the test fails naming a folder when the tables gain one (Q7).

  Verify: red against today's tree.
- [x] 4.2 Write `shared/blocks/workspace-files.md` from design D1 (three paragraphs and the role table: four blank-line-separated blocks, per the answers to Q5, Q7 and Q8). Extend `scripts/sync_shared.py` per design D3 (the heading constant, `WORKSPACE_FILES_PARAGRAPHS = 4`, `workspace_files_span()`, the replacement map). Extend `tests/unit/test_sync.py` with the new region's round-trip and anchor errors. Verify: 4.1 and `test_sync.py` fail only on the eleven skills that lack the section.
- [x] 4.3 Insert a four-block placeholder `## Workspace files` section directly before `## Handing over` in all eleven `SKILL.md` files. Run `python3 scripts/sync_shared.py`. Verify:
  - 4.1 green;
  - `python3 scripts/sync_shared.py --check` clean;
  - `test_handoff_block.py`, `test_report_offer.py`, `test_execution_shape.py` and `test_skill_header_pattern.py` unchanged and green;
  - body sizes re-measured against the baseline: `test_no_skill_body_outgrows_its_siblings` and the line-limit test green, with the median, ceiling and largest body recorded in `measurement.md` (5.7 measures again after the per-skill prose).
- [x] 4.4 Update `AGENTS.md`, "Skill header pattern": five materialized blocks, and the `## Workspace files` position before `## Handing over`. Verify: `rg -n "Four of those blocks" AGENTS.md` finds nothing, and the section names `shared/blocks/workspace-files.md`.

## 5. Per-skill prose

- [x] 5.1 Apply design D4's table: shorten the location sentences in ideate, write, review, check, supervise, reverse, troubleshoot and customize to pointers. Leave import's mandate, its pin and every `${CLAUDE_SKILL_DIR}` fallback paragraph byte-identical (Q3). Verify:
  - `rg -n "the working directory, unless the workspace" skills/*/SKILL.md` finds only the materialized block, import's mandate and publish's fallback paragraph;
  - `tests/unit/data/skill_mandates/proposal-import.txt` is unchanged;
  - `test_pinned_sentences.py` and `test_skill_header_pattern.py` green.
- [x] 5.2 Import :116: figures are extracted "into the `img/` folder beside the proposal". Verify: `proposal-import--output-location.txt` and the other import pins green.
- [x] 5.3 Ideate per design D5: the slug sentence at :104; the whole-family rename at seeding, with the numeric suffix on a taken target and the renamed files named in the read-back (:106, :116); `ideation.notes.md` renamed once a topic phrase exists (:46/:68, per Q6). Verify:
  - `rg -n "slug follows" skills/proposal-ideate/SKILL.md` finds nothing;
  - `test_pinned_sentences.py` and `test_skill_header_pattern.py` green.
- [x] 5.4 Write per design D5:
  - :48, step 2: when a proposal file for the idea already exists, such as an ideation seed, draft into it; create `<slug>.md` only when none exists, and give a seeded idea a new name only through the whole-family rename;
  - :69 keeps the handle sentence and adds that a requested rename moves the whole family (Workspace files).

  Verify: no sentence in write or ideate says the slug follows a title change, or creates a second proposal beside a seed; test suite green.
- [x] 5.5 Check: one sentence telling the agent how to relay `companion-orphaned`. It names the partial-rename cause and puts the whole-family rename as an anchored choice in the handoff, and the check itself never renames. Verify: `test_pinned_sentences.py` and `test_handoff_block.py` green.
- [x] 5.6 Troubleshoot per design D4 and Q8: rung 3 names the version capture `version-output.txt`; after the collect step, one sentence says the bundle now carries the captures and offers to remove `check-output.txt` and `version-output.txt`. Verify: the troubleshoot pins and `test_handoff_block.py` green; the block's capture names equal the two names in the skill.
- [x] 5.7 Re-measure body sizes. Verify: `test_no_skill_body_outgrows_its_siblings` and the line-limit test green. Record before/after median, ceiling and the largest body in `measurement.md` next to the estimate in design "Risks".

## 6. Lit-search sizing (per the Q1 answer: (a), threshold target (i))

- [x] 6.1 In `tests/unit/test_lit_search_cli.py`, red first and in-process through `main(argv)` with patched sources:
  - the `sources: …` line is byte-identical to today's and is followed by `candidates: N (L lines, C characters on stdout)`, printed before the YAML;
  - `L` and `C` equal the line count and `len()` of what was printed;
  - above the threshold, the line carries the "more than some hosts show" clause;
  - `snowball.py` prints the same line;
  - `--limit-per-seed` defaults to the value in the skill-lit-search delta;
  - with sources patched to return synthetic records matching 1.1's per-seed, per-direction counts and average size, a default run with the example's seed count stays under the threshold.

  Verify: red against today's scripts; `tests/unit/test_install_docs.py` untouched and green.
- [x] 6.2 Implement design D7 in `search.py` and `snowball.py`, with no `common.py` change. Verify: 6.1 green; `git diff --stat` shows no `common.py` copy changed (the `check.py` copies under `skills/proposal-import/` and `skills/proposal-reverse/` change through group 2's sync).
- [x] 6.3 Add the paragraph after "Both emit CSL-YAML …" in `skills/proposal-lit-search/SKILL.md`, and the example changes 1.1 called for. Verify:
  - `proposal-lit-search--browser-fallback.txt` and the other lit-search pins green;
  - the paragraph says the count line is not a degradation note to relay, names the observable trigger (a truncation marker, or fewer `- id:` entries than the count line's N), and allows a kept candidate list only when the user asks.

## 7. Verdicts and scenarios (no model call)

- [x] 7.1 Write `tests/unit/test_family_verdicts.py`, red first. It covers both functions in design D8, including:
  - a dump under the correct slug fails family-only unless `keep_licensed`;
  - a staged kept file renamed under the new slug together with its family passes family-only without `keep_licensed`, while a kept file the run added on its own still fails;
  - a notes-only run (`<provisional>.notes.md`) and an `ideation.notes.md`-only run pass family-only;
  - an allowed `api-keys.env`, `.gitignore`, `check-output.txt` and a file under `bug-report/` pass;
  - with `seed` given, a fresh proposal beside the unchanged seed fails and both are named;
  - a remaining `img/<old>-x.png`, a leftover `<old>-handout.md` ending in a metadata block, a changed PNG, a stale `img/<old>-` link in the notes, and a missing harvest record each fail family-renamed and are named; a left-behind `<old>.pdf` does not (Q5).

  Verify: red; `tests/unit/test_repo_conventions.py` finds an L0 test for both verdict names.
- [x] 7.2 Implement `verdict_family_only` and `verdict_family_renamed` in `harness/l1_checks.py` over `CHECK_SCRIPT.family_handles` and `family_member`. Verify: 7.1 green, and `uv run ruff check harness` clean.
- [x] 7.3 In `harness/claude_runner.py` (design D9, Q4):
  - make `workspace_changes()` read `scenario.get("fixture")`, staging nothing when it is absent;
  - add `litsearch_snowball`, `write_rename_family` and `ideate_seed_rename` to `SCENARIOS`, with their dispatch in `verdict()`;
  - add the advisory `family` field to `summary()` for every other run, passing the staged proposal as `seed` for `DRAFT_SCENARIOS`; it never changes `l1` or the exit status.

  Verify: L0 tests in `tests/unit/test_harness_helpers.py` (or a sibling) assert without a model:
  - the three names are in `SCENARIOS`, and their fixtures exist;
  - each scenario's fixture stages into `tmp_path`;
  - `workspace_changes()` over `import_messy` and `ideate_scoped` raises nothing and counts every file as added;
  - `verdict()` reaches the expected pass and fail on synthetic after-states;
  - a summary whose family observation fails keeps the `l1` the verdict decided, for a `write_from_seed` after-state with a fresh proposal beside the seed.
- [x] 7.4 Document the scenarios and the advisory field in `harness/README.md` under "Dev runs", and edit `docs/backlog.md`'s "Dev-runner scenarios for four skills" entry (design D11). Verify: the backlog no longer names `proposal-lit-search` or `litsearch_expand` in that entry; the README names the three scenarios, says they are dev-runner results not comparable to the matrix, and says the `family` field is advisory.

## 8. Gates and subscription runs

- [x] 8.1 Run `uv run poe test` and `uv run poe specs`. Verify: both green; `python3 scripts/sync_shared.py --check` clean.
- [x] 8.2 Run `uv run poe cov`. Verify: at or above the 78 % floor, with `check.py`'s new functions covered in-process.
- [x] 8.3 (Run after group 9.) On the subscription ($0 while extra usage stays off; draws the plan's rolling limits), run once each with `--isolated --model haiku`, then once with `--model sonnet`: `uv run poe dev litsearch_snowball`, `uv run poe dev write_rename_family` and `uv run poe dev ideate_seed_rename`. Verify: record each verdict, the served model, the produced file list and the advisory fields in `measurement.md`. Investigate a FAIL as a possible harness or fixture bug before attributing it to the model, and never re-run in a loop.

## 9. Review findings (design, decision log: review findings)

- [x] 9.1 `check.py`, red first in `tests/unit/test_check_family.py`, then the code and the sync (design D6):
  - `family_members(names, ends_in_block, own="")` applies the skill-check rule ("base slug has no proposal", the checked file a proposal whatever its name), and `family_findings` and `tests/helpers.is_fixture_proposal` use it;
  - kept files make a slug reportable only under a slug of two or more words;
  - a recipe name is looked up case-folded with a leading dot stripped, as in `publish.py`;
  - the listing skips names that are not valid UTF-8.

  Verify: new cases for f00's `ml-code-review.md` beside `ml-code.pdf` and beside `ml-code.candidates.yaml` (no finding), a checked `llm-code-review.md` beside `llm-code.md` (no finding), a LaTeX build and `tsconfig`/`jest` pairs flat and at a `[paths]` root (no finding), a `.justfile` workspace (built outputs quiet; the publish pin covers the lookup), and a non-UTF-8 name (no traceback, on POSIX); `python3 scripts/sync_shared.py --check` clean.
- [x] 9.2 `harness/l1_checks.py` and `harness/claude_runner.py`, red first (design D8, D9):
  - `verdict_family_only` takes `read` and classifies through `family_members`; the runner passes a reader over the workspace that falls back to the staged bytes;
  - `verdict_no_orphans` fails on a `check-failed` finding;
  - the three scenarios sit beside their skills' siblings in `SCENARIOS`.

  Verify: `tests/unit/test_family_verdicts.py` covers a metadata-less `<x>-review.md` under a slug no proposal carries (fails, named) and `[{"rule": "check-failed", ...}]` (fails); `tests/unit/test_family_scenarios.py` green.
- [x] 9.3 Prose: the location pointer at ideate's notes-file creation (:44, :68), each pinned; "a taken name at seeding moves the whole family to the suffixed slug" in `shared/blocks/workspace-files.md` and ideate's seeding sentence, with its pin and a block test; the check's relay sentence offers the rename only for files of the proposal's earlier slug, with its pin. Verify: the sync is clean, the pins and `test_workspace_files_block.py` green, and the body sizes re-measured in `measurement.md`.
- [x] 9.4 Gates after the final edit: `uv run poe test`, `uv run poe specs`, `uv run poe cov`, `python3 scripts/sync_shared.py --check`, `openspec validate tighten-proposal-family --strict`.

## 10. Approval answers (design, decision log: approval answers)

- [x] 10.1 Record the maintainer's answers in design.md's decision log and in `measurement.md`: Codex's fallback cap excluded, so the threshold stays 25,000 characters or 1,800 lines; kept files make a slug reportable only under a slug of two or more words; no wider proposal-vs-review test, with the collision case kept in Risks. Verify: no artifact still calls one of these a question for the maintainer.
- [x] 10.2 Ideate's slug shape, red first: pin `tests/unit/data/pinned_sentences/proposal-ideate--seed-slug-shape.txt`, then give ideate's seeding sentence write's rule, "(lowercase, hyphenated, 2–4 title words; numeric suffix on collision)" (design D5; skill-ideate delta). Verify:
  - the pin fails before the prose edit and passes after;
  - `shared/blocks/workspace-files.md` states nothing that contradicts the shape;
  - ideate's body re-measured in `measurement.md`, and `test_no_skill_body_outgrows_its_siblings` green.
- [x] 10.3 Add two entries to `docs/backlog.md`, each with `openspec/changes/tighten-proposal-family/measurement.md` as evidence: the write skill was not loaded for a rename-only request; the handoff lines were missing after the rename-only requests and haiku's lit-search run. Verify: each follows the file's entry format, in the section that fits it.
- [x] 10.4 Gates after the final edit: `uv run poe test`, `uv run poe specs`, `uv run poe cov`, `python3 scripts/sync_shared.py --check`, `openspec validate tighten-proposal-family --strict`.
- [x] 10.5 One subscription run, approved by the maintainer: `uv run poe host-status` (when logged out, run nothing and report `uv run poe host-login claude` as a user action), then `uv run poe dev ideate_seed_rename --model haiku --isolated --keep`, once. Verify: its verdict, the served model, the slug it produced (2–4 words) and the log path are in `measurement.md`; no re-run.
