## Why

A student working in an OpenCode workspace with `[paths] proposals = "proposals/"` ended up with ten files for one proposal, under two naming prefixes. Only three of them were family members a shipped skill writes: the proposal, its notes file and its review. The other seven were working files: a tool review with a probe folder, a snowball summary, and its candidate list, raw dump and source log. They carried the provisional prefix the idea had before seeding, so the directory listing no longer showed they belonged to the proposal. The causes:

- **The slug is re-derived at seeding, and only the notes file follows.** `proposal-ideate` seeds `<slug>.md` from the working title and renames only the notes file (SKILL.md:106). Anything else under the provisional prefix is left behind. Its wording ("the slug follows" the title, :104) also reads as contradicting `proposal-write` (:69, "the slug is a workspace handle, not the title"). Write's "From scratch" step also creates a fresh `<slug>.md` even when a seed exists, which leaves the seed's family behind in the same way.
- **No rule keeps working files out of the workspace.** The only ban is in `proposal-lit-search`'s browser route ("write no raw response into the workspace"). Nothing covers the scripts' own output, candidate lists, probes or logs. Each skill states the proposal location in its own sentence. There are about ten of them, worded slightly differently, and none says what else may sit there.
- **A default snowball run is larger than a host shows.** Measured 2026-10-13 ($0, no model call): two seeds with default settings (`--limit-per-seed 20`, both directions, OpenAlex keyless) gave 113 candidates, 1,897 lines and 97.9 KB of CSL-YAML on stdout. Claude Code's Bash tool shows about 30,000 characters by default, and other hosts' caps are not recorded yet. An agent that sees a third of the output has to save it somewhere to read it. That the incident's dumps came from this is likely but unverified.
- **Nothing reports a fragmented family.** The check sees the proposal file only. A review, figure or kept file whose slug no longer has a proposal goes unreported.

The maintainer decided (2026-10-13): the slug is still derived from the working title at seeding, but any rename moves the whole family together, `img/<slug>-*` files and the references to them included. One shared block, materialized into all eleven skills, defines the proposal location and what may sit in the workspace. The check reports orphaned companions. Pure verdicts and subscription dev-runner scenarios cover the rule. On 2026-10-14 the maintainer answered the design's eight open questions, accepting every recommendation, and decided that the block lists the family once as a role table with today's names; renaming family files is a later change (#9). Answering the approval request the same day, the maintainer excluded Codex's fallback cap from the threshold, confirmed the kept-file word bound and the skill-check rule for review files, and had ideate's slug length fixed in this change (design, decision log).

## What Changes

- **One workspace-files block in every skill.** `shared/blocks/workspace-files.md` is materialized by `scripts/sync_shared.py` into a `## Workspace files` section in all eleven `SKILL.md` files. The section sits directly before `## Handing over` and holds the block alone. The block:
  - defines the proposal location once, and says family files never go into a host's scratch or temporary folder;
  - lists the closed proposal family once, as a role → file-name table with today's names (proposal, notes, harvest record, review, supervisor feedback, handout, built output, kept file, figure, ideation notes), and states the slug rules: a draft from a seed goes into the seed, and a rename moves the whole family;
  - lists what else may be there: the workspace-level files, a workspace build definition with what it reads and writes, the troubleshooting captures `check-output.txt` and `version-output.txt` while a report is assembled, and the installer-managed files, `.kiro/skills/` and `skills-lock.json` included beyond the decision's list;
  - keeps everything else in the chat. Output too large for one piece is read in slices or produced narrower. A temporary folder outside the workspace may be used only when one is writable; when none is, which happens in the Copilot sandbox, the agent never falls back to the workspace. A file is kept only when the user asks, as `<slug>.<label>.<ext>`.
- **Location sentences become pointers.** In ideate, write, review, check, supervise, reverse, troubleshoot and customize, the per-skill definition becomes "the proposal location (Workspace files below)". Import's mandate keeps its location clause, which was put there on evidence in `2026-08-31-fix-import-output-location`, and its figure extraction now says "the `img/` folder beside the proposal". The `${CLAUDE_SKILL_DIR}` fallback paragraphs are left as they are, interpreter clause and working-directory stake included, so publish keeps the definition inside its fallback paragraph.
- **Ideate and write agree on the slug.** The slug is derived from the title when the proposal file is first written, in write's shape (lowercase, hyphenated, 2–4 title words), which ideate's seeding sentence now states too, and does not follow later title changes. A full draft of a seeded idea goes into the seed's file. At seeding, a provisional slug that differs is replaced across the whole family: notes, kept files and `img/<slug>-*`, with references to moved files updated. `ideation.notes.md` becomes the provisional slug's notes file once a topic phrase exists. Write's requested rename moves the whole family the same way. Links are updated in the proposal and its notes file. Built outputs stay in place as previous builds; the skill names them and offers a rebuild.
- **Lit-search output sized for the host.** Both search scripts print one stderr line, before their output, with the candidate count and the stdout size in lines and characters. It comes after the `sources: …` line, which stays byte-identical. The default `--limit-per-seed` is lowered to 5, and the skill's example snowballs one seed per call. The flag threshold is 25,000 characters or 1,800 lines, below the smallest recorded caps of the supported hosts in their default configuration; a $0 measurement on 2026-10-14 set both (measurement.md), and the maintainer excluded Codex's smaller fallback for models outside its catalog. The skill tells the agent to run narrower when the tool result shows a truncation marker or fewer entries than the count line states.
- **`companion-orphaned` check warning.** `check.py` lists the proposal's directory, and the workspace root when a proposal location is configured, and changes nothing there. For this finding it opens another file only to tell a proposal from a companion. It warns about the family files of a slug that has no proposal, notes file or harvest record, when that slug carries an unambiguous companion or, under a slug of two or more words, at least two kept files, and about a figure link under another slug. Built outputs never warn on their own and never under a workspace build; source documents, project files, allowed workspace files and installer files are never reported. Only slug-shaped names are classified. The check's family vocabulary uses the block's role names. The warning goes into the five synchronized copies.
- **Coverage.**
  - `verdict_family_only`, `verdict_family_renamed` and `verdict_no_orphans` in `harness/l1_checks.py`, each with L0 tests.
  - Three fixtures: `w13-orphaned-companions` with an `expected.json` oracle, `w14-family-rename` with an oracle, and `w15-provisional-notes`, which has no proposal.
  - Three subscription dev-runner scenarios: `litsearch_snowball`, `write_rename_family` and `ideate_seed_rename`.
  - An advisory `family` field on every other dev run, beside `single_context` and `handoff`, which never changes a pass flag.
  - The backlog item "Dev-runner scenarios for four skills" loses `proposal-lit-search` in the implementing commit.
- **Unchanged:**
  - the `sources: …` line;
  - every existing check finding and exit code;
  - the `[paths] proposals` semantics and flat-layout byte-identity;
  - publish's build lookup and never-fall-back rule;
  - Inspect tasks, their scorers and shipped verdicts (no metered run).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

All deltas are ADDED requirements. No existing requirement is modified or removed, so no later change's MODIFIED block can drop this change's wording, and this change drops none of theirs.

- `proposal-file-format`:
  - ADDED "Proposal family under one handle";
  - ADDED "A rename moves the whole family";
  - ADDED "Working material stays out of the workspace".
- `skill-packaging`: ADDED "Workspace-files block in every skill".
- `skill-ideate`: ADDED "Provisional handle resolved at seeding".
- `skill-lit-search`: ADDED "Search output sized for what a host shows".
- `skill-check`: ADDED "Orphaned companions reported as a warning".
- `testing-harness`: ADDED "Proposal-family coverage".

## Impact

- **Skills.** All eleven `skills/*/SKILL.md`: a materialized section, and location sentences shortened to pointers. Further per-skill edits: ideate (slug sentence, the 2–4-word slug shape at seeding, whole-family rename at seeding, `ideation.notes.md` on resume), write (draft into an existing seed, whole-family rename on request), check (how to relay the warning), lit-search (the sizing paragraph), import (the `img/` folder beside the proposal) and troubleshoot (the named version capture and the removal offer). Import's mandate and its pin stay as they are.
- **Scripts.**
  - `skills/proposal-check/scripts/check.py`, plus its five copies regenerated by the sync: the family vocabulary (`family_handles`, `family_member`, and the listing classifier `family_members` that the harness and the test helpers share), the `companion-orphaned` rule and its rule identifier.
  - `skills/proposal-lit-search/scripts/search.py` and `snowball.py`: the count line, and the snowball default.
  - No `common.py` change, so the vendored copies in import and reverse stay untouched. No change to the troubleshooting collector.
- **Sync.** `shared/blocks/workspace-files.md` (new) and `scripts/sync_shared.py` (a fifth region).
- **Harness.**
  - `harness/l1_checks.py`: three verdicts (`verdict_family_only`, `verdict_family_renamed`, `verdict_no_orphans`) and `renamed_proposal()`, all classifying through `check.py`'s `family_members`.
  - `harness/claude_runner.py`: three scenarios, the advisory `family` field, and `workspace_changes()` for scenarios without a fixture.
  - `harness/README.md`: the scenarios and the field.
- **Tests.**
  - New: `tests/unit/test_workspace_files_block.py`, `tests/unit/test_family_verdicts.py`, `tests/unit/test_check_family.py` and `tests/unit/test_family_scenarios.py` (the runner's scenarios and advisory field, the sibling task 7.3 allows).
  - Extended: `tests/unit/test_sync.py`, `tests/unit/test_lit_search_cli.py`, `tests/unit/test_codex_cli.py` (`litsearch_snowball` needs the network), `tests/unit/test_fixture_oracles.py` and `tests/helpers.py`.
  - Pinned sentences: the check's relay of `companion-orphaned`, write's draft into a seed, ideate's slug shape at seeding, its seeding rename and resumed `ideation.notes.md`, and lit-search's run-narrower trigger.
  - Fixtures: `tests/fixtures/w13-orphaned-companions/`, `w14-family-rename/` and `w15-provisional-notes/`, documented in `tests/fixtures/README.md`.
- **Docs.** `AGENTS.md` ("Skill header pattern": five materialized blocks, and the section's position) and `docs/backlog.md`.
- **Parallel changes.**
  - `widen-lit-live` (#5) has landed on `main`; it touched no spec and removed the backlog entry next to the one this change edits.
  - `utf8-script-output` (#6) lands first and edits the first lines of `main()` in `check.py`, `search.py` and `snowball.py`. This change rebases onto it.
  - `mark-review-currency` (#8) lands after this one, takes fixture w16, and depends on this change's scoped read-only sentence, the `family_member` signature and the requirement name "Proposal family under one handle" (design D12).
