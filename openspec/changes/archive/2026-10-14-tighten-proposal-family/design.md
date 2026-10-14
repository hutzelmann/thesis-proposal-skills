## Context

**Status (2026-10-14).** Drafted 2026-10-13 and revised 2026-10-14 after a critic pass; the decision log at the end says what changed and what was not taken over. The maintainer's binding decisions are recorded in proposal.md, "Why". The eight questions under "Questions before implementation" were answered by the maintainer on 2026-10-14: every recommended option was accepted, and Q5 was settled as "leave, name, offer rebuild". The maintainer also decided that the block lists the family once, as a role → file-name table with today's names, and that renaming family files is deferred to a later change (#9). The decision log records the answers and what they changed, then the measurement of task 1.1, the findings of an implementation review, and the maintainer's answers to the approval request, which settled the two points the review had left open (the kept-file word bound and Codex's fallback cap) and fixed ideate's slug length.

**Terms.** A proposal's *slug* is its file name without `.md`. In its role as the name every family file carries, this design also calls it the *handle*. Placeholders are written `<slug>`, `<old>` and `<new>`, as in the existing specs.

The state that shapes the approach (see proposal.md, "Why", for the incident):

- **Materialized blocks.** `scripts/sync_shared.py` writes four shared blocks into each `SKILL.md`.
  - Workflow line and voice block: header positions 2 and 3.
  - Handoff block: the first `HANDOFF_PARAGRAPHS = 3` paragraphs after `## Handing over`.
  - Report offer: the first paragraph after `## When this run fails`.

  The regions are found by fixed positions and headings, never by markers (AGENTS.md, "Skill header pattern"). `## Handing over` must sit directly before `## When this run fails`, and last in `proposal-troubleshoot` (`test_handoff_block.py`). Six skills must open with `## Execution shape` (`test_execution_shape.py`).
- **Location sentences.** The proposal location ("the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory") is restated in ten places:
  - ideate :106, write :48, review :25, check :27, supervise :37, reverse :40, troubleshoot :21;
  - import's pinned mandate (:15);
  - inside publish's `${CLAUDE_SKILL_DIR}` fallback paragraph (:27);
  - customize :68, which lists the family that moves.

  Import also pins its own output rule (:90, `proposal-import--output-location.txt`) and extracts figures "into `img/`" (:116), which under `[paths]` resolves against the working directory, not beside the proposal.
- **Why import's mandate carries the location.** `2026-08-31-fix-import-output-location` put it there on evidence. A real `proposal-supervise` run wrote every deliverable into the host's session scratchpad: where the skill prose was silent, the host's own "use the scratchpad" guidance won. Supervise follows import's `SKILL.md`, and the mandate is the paragraph a delegated run is guaranteed to read; a later section can be skimmed. The dev runner cannot catch a regression there, because its prompt says "work there".
- **Body size.** `test_no_skill_body_outgrows_its_siblings` caps every body at 2 × the median word count. Today the median is 2,697 (troubleshoot) and the ceiling 5,394. The largest bodies are supervise at 4,743 (88 % of the ceiling) and ideate at 4,253.
- **What the check sees.** `check.py` reads the proposal and the governing `guidelines.md`. Its only workspace-shaped finding is `proposal-misplaced`. `paths_findings()` already receives the governing file, whose directory is the workspace root.
  - `tests/helpers.is_fixture_proposal` excludes `NON_PROPOSAL_SUFFIXES` (`-handout.md`, `.harvest.md`, `.notes.md`) and treats `<x>-review.md` as a companion only when `<x>.md` sits beside it. f00's own proposal is `ml-code-review.md`, so the suffix alone cannot decide.
  - `publish.py --handout` keeps the trailing metadata block (`strip_abstracts`), so a `-handout.md` file ends in one.
  - `harness/l1_checks.py` already loads `check.py` from its file (`CHECK_SCRIPT`) so that a verdict and the warning a writer sees never disagree.
- **Search output.** A default two-seed snowball (measured 2026-10-13, no model call, OpenAlex keyless and degraded in every call) emitted 113 candidates: 1,897 lines and 100,264 bytes on stdout, about 17 lines and 890 characters per candidate. `search.py` prints `sources: …` on stderr inside `federate()`; `tests/unit/test_install_docs.py` pins that prefix for the readiness guide.
- **Host output caps.** Claude Code's Bash tool shows about 30,000 characters by default (`BASH_MAX_OUTPUT_LENGTH`). The other hosts' caps are not recorded here. Codex's exec layer has been reported to cut what the model sees to roughly 10 KiB or 256 lines, keeping head and tail, in earlier releases; newer releases budget per model. Both are unverified.
- **Workspace changes in the dev runner.**
  - `stage()` copies only a fixture's top-level `.md` and `.txt` files and its `img/`.
  - `workspace_changes()` returns the changed staged files and the added files. It skips hidden paths, which is where the harness installs skills and saves the stream, and `__pycache__`. It indexes `scenario["fixture"]`, which `import_messy` and `ideate_scoped` do not have.
  - Every summary already carries two advisory verdicts, `single_context` and `handoff`, which never change the exit status.
- **Drafts from a seed.** `select_draft` and the testing-harness scenario "Draft written to a fresh filename" record that models sometimes draft into a fresh `<slug>.md` beside the staged seed. Write's "From scratch" step 2 says "Create `<slug>.md`" whether or not a seed exists.
- **Installer files in a workspace.** `install.py` and the troubleshooting collector know `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, the OpenCode folders `.opencode/skill/` and `.opencode/skills/`, the install record `.thesis-proposal-install.json`, and `skills-lock.json`, which `npx skills add` keeps in the workspace root (install.py:481, collect.py:316).
- **Troubleshooting captures.** Rung 3 writes `check-output.txt` into the working directory, and a version capture without a fixed name, and passes the file to `collect.py --script-output`. The capture cannot go into `bug-report/` first, because the collector refuses an existing `bug-report/`.

## Goals / Non-Goals

**Goals:**
- One statement of where files go, materialized identically into all eleven skills. A later change, such as an opt-in folders layout, then edits one source.
- A family that stays recognisable from a directory listing across seeding, drafting and renames.
- A first snowball run whose output a host shows in full in the measured case, and a signal an agent can observe when a run's output is still larger than what it saw.
- A mechanical report of the fragmentation the incident showed, quiet on the workspaces the skills support, and $0 dev-runner evidence that the skills leave no working files behind.

**Non-Goals:**
- **Per-proposal folders, typed sub-locations, or a discovery script in every skill.** These are the later opt-in `add-proposal-folders-layout`, which follows a grill-me.
- **Migrating existing workspaces.** A fragmented family gets warnings. A rename happens only when the user asks; nothing is moved automatically.
- **A superseded-review marker.** That is `mark-review-currency` (#8).
- **Tightening proposal targeting to dot-free names.** A kept `<slug>.<label>.md` that ends in a metadata block would still be a targeting candidate. That edge case is noted here; the targeting requirement stays as it is.
- **What a workspace build writes.** A workspace build definition, the files it reads and the files it writes stay outside the family contract. The proposal-file-format delta says so explicitly, and the check never reports them (D6).
- **Inspect twins, matrix cells, or any metered run.**
- **Changing the `${CLAUDE_SKILL_DIR}` fallback paragraphs**, interpreter clause and working-directory stake included.
- **Renaming family files.** The block's role table carries today's names, and per-skill mentions such as `<slug>-review.md` stay as they are. New names, if any, are a later change (#9), which then edits the table, `check.py`'s vocabulary and the per-skill mentions together.

## Decisions

**D1 — The block's content.** `shared/blocks/workspace-files.md` has three paragraphs and, inside the first, a role table: four blank-line-separated blocks, about 420 words in total. The wording below is for review and may be tightened during implementation, but every listed name must remain:

1. *Location and family.* "Every file of a proposal goes into the proposal location: the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — then only there, never both, and never into a host's scratch or temporary folder. A proposal's slug, its file name without `.md`, names its whole family:" followed, after a blank line, by the role table, the only place the block lists the family:

   | Role | File name |
   |---|---|
   | proposal | `<slug>.md` |
   | notes | `<slug>.notes.md` |
   | harvest record | `<slug>.harvest.md` |
   | review | `<slug>-review.md` |
   | supervisor feedback | `<slug>-feedback.md` |
   | handout | `<slug>-handout.md` |
   | built output | `<slug>.pdf`, `<slug>.typ`, `<slug>.tex` or `<slug>.docx` |
   | kept file | `<slug>.<label>.<ext>` |
   | figure | `img/<slug>-<name>.<ext>`, in an `img/` folder beside the proposal |
   | ideation notes | `ideation.notes.md`, before a topic phrase exists |

   The names are today's, unchanged (Non-Goals). The roles are the kinds `check.py`'s `family_member` returns (D6), plus the slug-less ideation notes, and an L0 test holds the two equal both ways.
2. *Slug and rename.* "The slug is derived from the working title when the proposal file is first written, and it stays when the title changes later; a draft from an existing seed goes into that file. It changes only by a rename: at seeding, when the settled working title yields a different slug than the provisional one, or when the user asks. A rename moves every family file under the old slug at once, built outputs excepted, and updates every link to a moved file in the proposal and its notes file; it never edits the text of a review or supervisor feedback. Built outputs stay as previous builds: name them and offer a rebuild. Check every target name first. At seeding, when any target name is taken, the slug takes the numeric suffix and the whole family moves to it; on request, move nothing, name the collision and propose the suffixed slug. When a file cannot be moved, stop, overwrite nothing, and say what moved and what did not. Say which files you renamed."
3. *Everything else.* "Besides proposal families, the workspace holds only: `guidelines.md`, `api-keys.env`, `bug-report/` and `.gitignore` at the root; beside a proposal, a workspace build definition (a file named `proposal-build`, with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the files that build reads and writes, and the `.gitignore` the built-in build adds; the troubleshooting captures `check-output.txt` and `version-output.txt` while a report is assembled; and the installers' `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the record `.thesis-proposal-install.json` and `skills-lock.json`, which you never write or tidy. Nothing else goes there. Script output, candidate lists, raw responses, probes and logs stay in the chat. Read output too large for one piece in slices — a page range, the next lines — or produce it narrower. A temporary folder outside the workspace is a fallback only where one is writable, and a refused one is never a reason to write into the workspace. Keep a file only when the user asks: as `<slug>.<label>.<ext>` beside the proposal, never with the label `notes` or `harvest`, or in the notes file before a slug exists."

Paragraph 2 names no family member by role list any more: "every family file under the old slug, built outputs excepted" points at the table, so the family is listed once. Built outputs follow Q5 (leave, name, offer a rebuild), the captures Q8 (a), the installer names Q7 (a).

The Copilot finding decides the order in paragraph 3. A dev run failed on the model's own `tee /tmp/…`, so "use the OS temp folder" cannot be the primary instruction. The chat is the primary place, reading in slices or a narrower run is the answer to size, and a temporary folder is an opportunistic fallback. "The next lines" is shell-neutral on purpose: `head`/`tail` and PowerShell's `Select-Object` windows both satisfy it. Alternatives rejected:
- A temp-first rule fails under that sandbox.
- A rule naming each host's temp folder ages with every host release.
- Writing dumps beside the proposal is exactly the incident.

The block says "the user", not "the student", because it is materialized into `proposal-supervise` too, where the user is the professor. The handoff block's user-control rules already speak of the user.

**D2 — Placement: its own section, directly before `## Handing over`.** The closing order becomes `… → ## Workspace files → ## Handing over → ## When this run fails`. In troubleshoot it is `… → ## Workspace files → ## Handing over`. Reasons:
- **The header is a fixed contract.** It holds four blocks with mandate adjacency, enforced by `test_skill_header_pattern.py` and the "Uniform skill opening structure" requirement. A fifth header block would put operational rules above the mandate, on the part of each page skills.sh shows first.
- **The other first-section slot is taken.** `## Execution shape` must be the first section in six skills (`test_execution_shape.py`). A second fixed early slot would have to be "first or second", depending on the skill.
- **The tail is already the materialized zone.** Handoff and offer are there, so all shared prose sits in two predictable places, header and tail, and the per-skill middle stays hand-written.
- **The anchor that must not be skimmed stays early.** A section at the end can be skimmed, which is why `2026-08-31-fix-import-output-location` put the location into import's mandate. That anchor stays (Q3). Every other file-creating step keeps a short pointer, "in the proposal location (Workspace files below)", the same way the seeding step already says "close with the handoff lines from Handing over below". The block's first sentence names the 2026-08-31 failure mode itself: never a host's scratch or temporary folder.

Rejected: inside `## Handing over`, which would mix two concerns and turn `HANDOFF_PARAGRAPHS` into a migration. Also rejected: a reference file that skills link to, because agents follow links unreliably and skills.sh would not render it.

**D3 — How `sync_shared.py` locates it.**
- A constant `WORKSPACE_FILES_HEADING = "## Workspace files"` and a pinned `WORKSPACE_FILES_PARAGRAPHS = 4`, with the same "changing the count is a migration" guard as `HANDOFF_PARAGRAPHS`. The count is of blank-line-separated blocks, as `section_span()` counts them: the three paragraphs of D1 and the role table, which stands after a blank line so that every Markdown renderer, skills.sh's included, shows it as a table rather than as paragraph text.
- `workspace_files_span(body)` reuses `section_span()`. It raises `AnchorError` when the section is missing, appears twice, or is not immediately followed by `## Handing over`.
- `render_skill_md()` adds the region to its replacement map. `--check`, the pre-commit hook and CI cover the region without further change.

A fixed paragraph count was chosen over "the whole section up to the next heading" deliberately. A sentence a contributor appends survives the sync and fails `test_workspace_files_block.py`, which requires the section to equal the block exactly, instead of being silently overwritten. The first materialization adds content, so the "byte-preserving on adoption" clause does not apply. That clause covers converting an existing hand-maintained block, and this block is new. `AGENTS.md`, "Skill header pattern", changes from four materialized blocks to five and names the section's position.

**D4 — The location sentences.** Each becomes a pointer ("in the proposal location (Workspace files below)") or is shortened to what is specific to the skill:

| Skill | Today | After |
|---|---|---|
| ideate :44 | "create the companion `<slug>.notes.md`", no location | pointer added: the notes file is the first file a session writes, before any proposal exists |
| ideate :68 | "created as `ideation.notes.md`", no location | pointer added |
| ideate :106 | location + "slug from the working title" + notes-only rename | pointer, plus write's 2–4-word shape, since ideate derives the slug at seeding as write does at creation; the rename rules point at Workspace files (D5) |
| write :48 | "Create `<slug>.md`" + slug shape + location | pointer; the 2–4-word shape stays, because it is the derivation write performs; a seed is drafted in place (D5) |
| review :25 | "… proposal location — the working directory, unless …; look only there" | "… the proposal in the proposal location; look only there" |
| check :27 | same pattern | same treatment; :40, the guidelines chain and "run from the workspace root", stays |
| supervise :37 | location sentence | "the file sits in the proposal location" |
| reverse :40 | location sentence + "nothing beside the source" | location clause dropped; "nothing beside the source thesis …" stays |
| troubleshoot :21 | "The search space is the workspace's proposal location: …" | "The search space is the proposal location (Workspace files below)" |
| troubleshoot :61, :110 | an unnamed version capture; nothing after the bundle | the version capture is named `version-output.txt`; one sentence after the collect step: the bundle now carries the captures, so offer to remove them (Q8) |
| customize :68 | family list after "holding each proposal and everything that travels with it" | "holding each proposal and its family (Workspace files below)"; the `[paths]` validation and migration text stays |
| import :15 (mandate) | dash clause defining the location | unchanged, with its pin (Q3) |
| import :90 | pinned output-location sentence | unchanged |
| import :116 | "extract images into `img/`" | "into the `img/` folder beside the proposal" |
| publish :27 | sentence inside the fallback paragraph | unchanged (Q3) |

Review's and supervise's "(beside the proposal, else in the workspace root)" stays, because it is the guidelines chain.

**D5 — Slug and rename semantics in the skills.**
- **Ideate.**
  - :104, "since the slug follows it", becomes "since the slug is derived from it now, once".
  - :106's creation sentence takes write's slug shape: `<slug>.md` "(lowercase, hyphenated, 2–4 title words; numeric suffix on collision)", the wording of write's step 2, pinned as `proposal-ideate--seed-slug-shape.txt`. Without it, both `ideate_seed_rename` dev runs derived an eight-word slug from the full working title (decision log, approval answers).
  - :106 renames the whole provisional family per Workspace files and names the renamed files in the closing read-back. A taken target at seeding gives the slug the numeric suffix, as Content-derived slug filenames already requires, and the whole family moves to the suffixed slug; a seed is never written beside another idea's file.
  - :44 keeps "provisional handle from the phrase".
  - :68, on resume: once a topic phrase exists, `ideation.notes.md` is renamed to `<provisional>.notes.md` (Q6).
- **Write.**
  - :48, "From scratch" step 2: when a proposal file for the idea already exists, such as an ideation seed, the draft goes into that file; `<slug>.md` is created only when none exists. A new name for a seeded idea goes through the whole-family rename. Without this, a fresh `<slug>.md` beside the seed is a rename that leaves the seed, its notes file and any `img/<seed>-*` figures behind, which is the fragmentation the decision forbids.
  - :69 keeps "the slug is a workspace handle, not the title" and adds that a rename the user asks for moves the whole family (Workspace files). With ideate's sentence reworded, the two no longer read as contradicting each other: the slug is derived once, at creation, and is a handle from then on.
- **What a rename covers.**
  - It updates links in the proposal and in the notes file (Q5).
  - It leaves built outputs in place as previous builds, names them, and offers a rebuild (Q5). A rebuild writes them under the new slug; a renamed stale `<old>.pdf` would look like a current build of the new title, and an open PDF or DOCX is the file most likely to refuse a move on Windows or in a synced folder.
  - It never edits the text of a review or feedback file, because those are records of what was judged.
  - It moves nothing outside the family.
  - It checks every target first. At seeding, a taken target gives the slug the numeric suffix and the whole family moves to it; on request, nothing moves, the collision is named and the suffixed slug proposed.
  - When a member cannot be moved, it stops, overwrites nothing, says what moved and what did not, and updates links only for the files that moved.

**D6 — One family vocabulary, owned by `check.py`.** `check.py` gains the following, which the harness reuses through `CHECK_SCRIPT` and #8 reuses for the review path. The function signatures are the contract those callers build on. The kinds are the role names of the block's table (D1), so the block, the check and the verdicts speak one vocabulary.

- **Constants.**
  - `SLUG_RE = r"[a-z0-9]+(?:-[a-z0-9]+)*"`: a family-shaped name needs a slug of this shape (Content-derived slug filenames).
  - `FAMILY_ROLES`: the kinds below, in the table's order; `IDEATION_NOTES = "ideation.notes.md"`, the table's slug-less "ideation notes" row, which `family_member` never classifies.
  - `WORKSPACE_LEVEL`: `guidelines.md`, `api-keys.env`, `bug-report`, `check-output.txt` and `version-output.txt` (Q8), and `skills-lock.json` (Q7).
  - `BUILD_STEM`, mirrored from `publish.py` with a pin test that the two agree, plus the recipe names `Makefile`, `GNUmakefile` and `justfile`. The check recognises a recipe file by its name alone, since it opens no file for this finding; an unrelated `Makefile` therefore only keeps built outputs quiet, which errs on the side of silence. It looks a recipe name up as `publish.py` does, case-folded and with a leading dot stripped, so a hidden `.justfile` that publish runs keeps built outputs quiet too; the pin test covers that lookup, not only the two name sets.
  - Hidden names are never classified, which covers `.gitignore`, `.agents/`, `.claude/`, `.kiro/`, `.opencode/` and `.thesis-proposal-install.json` without a list in the script.
- **`family_handles(names: Iterable[str]) -> frozenset[str]`**, pure: the slug-shaped part before the first `.` of every non-hidden, non-`img/` name that is family-shaped, plus the base slug of every `-handout.md`.
- **`family_member(name: str, handles: frozenset[str]) -> tuple[str, str] | None`**, pure and name-only, returning (slug, kind). `name` is a path relative to the listed directory, such as `img/x.png`; `handles` is what the caller resolved from the listing. Being name-only, it reads a `-review` or `-feedback` name by `handles` alone (the first row below); a caller that classifies a whole listing uses `family_members`, which applies the skill-check rule.

| Kind (role) | Name shape |
|---|---|
| `proposal` | `<slug>.md`; by name alone, also `<slug>-review.md` or `<slug>-feedback.md` whose base slug is not in `handles` |
| `notes` | `<slug>.notes.md` |
| `harvest record` | `<slug>.harvest.md` |
| `review` | `<slug>-review.md`, base slug in `handles` |
| `supervisor feedback` | `<slug>-feedback.md`, base slug in `handles` |
| `handout` | `<slug>-handout.md`, by its suffix alone |
| `built output` | `<slug>.pdf`, `.typ`, `.tex` or `.docx` |
| `kept file` | `<slug>.<label>.<ext>`, or a folder `<slug>.<label>/` |
| `figure` | `img/<file>` starting with a slug in `handles` followed by `-`, longest match |

Hidden names, `ideation.notes.md`, names without a slug-shaped part and the allowed names return `None`. A `-handout.md` file is a companion by its suffix alone, although `publish.py --handout` leaves a metadata block in it.

- **`family_members(names, ends_in_block, own="") -> dict[str, tuple[str, str]]`**, the listing classifier that `family_findings`, the harness verdicts (D8) and `tests/helpers.is_fixture_proposal` share. `names` is a listing as the check lists a directory (top-level names, a folder as `name/`, figures as `img/<file>`); `ends_in_block(name)` answers whether that file's text ends in a metadata block, and is called only for the names the rule needs. It applies the skill-check rule exactly: a `-review` or `-feedback` name whose base slug has **no proposal** in the listing is a proposal when its text ends in a metadata block, and otherwise that base slug's companion; a base slug that only a built output, kept file or notes file carries does not count as a proposal. `-review`/`-feedback` names are decided shortest first, so a base that is itself such a name is settled before it is asked about. `own`, the checked proposal, is a proposal whatever its name, since its text is in hand. Figures are resolved last, against every member's slug, by longest match. A caller that cannot read a file answers `True`, which keeps it a proposal and the warning quiet.
- **`family_findings(proposal_path, overrides, guidelines, text) -> list[Finding]`**, with `paths_findings()`'s first three parameters and the checked proposal's text, which `check_findings()` has already read. It is the only place that opens another file, and only for one purpose: the `ends_in_block` question `family_members` asks. It lists the proposal's directory and its `img/`, and also the workspace root and its `img/` when the governing `guidelines.md` configures a valid proposal location (`overrides`) and the root is another directory. A directory entry whose name is not valid UTF-8 is skipped: no slug-shaped name can contain one, and printing it would end the check with a traceback and lose every finding. It is split into helpers so that no function exceeds the complexity cap.

The rule (Q2, answered (d)):
- A slug is **sheltered** when a proposal, a notes file or a harvest record carries it in the proposal location. A harvest record shelters because skill-reverse writes it before any proposal or notes file exists and invites the user to inspect it.
- An unsheltered slug is **reportable** when it carries an unambiguous companion (a review, feedback, handout or figure) or, under a slug of at least two hyphen-separated words, at least two kept files. Every family-shaped file of a reportable slug is reported. The word bound is the 2–4 words of Content-derived slug filenames, which every skill-derived slug and provisional slug meets; it keeps one-word tool and project names quiet: a LaTeX build's `thesis.synctex.gz` and `thesis.run.xml` (and with them `thesis.tex` and `thesis.pdf`), `tsconfig.app.json` beside `tsconfig.spec.json`, `jest.config.js` beside `jest.setup.js`. The companion arm keeps one-word slugs, so a review left behind by a user-named `expose.md` is still reported. The maintainer confirmed the word bound on 2026-10-14 (decision log, approval answers).
- **Built outputs** (`built output`) never make a slug reportable on their own. They are reported only with a reportable slug, and never when a workspace build definition sits beside the proposal. A faculty template, the build's output, a student's `submission.pdf`, a source `exposé.docx` or a `thesis.pdf` is therefore never an orphan on its own.
- **At the workspace root**, when a proposal location is configured: a non-proposal family-shaped file whose slug is sheltered in the location is reported as lying outside it; others follow the same rule. A redirected dump from a script run at the root is thus seen.
- **Stale figure links**: each `](img/…)` link in the checked proposal whose file name does not start with the proposal's own slug followed by `-`. The message names the linked path and the proposal's own slug, and names the old slug only when it resolves against a family-shaped file present. When only the link and the image carry it, the check cannot tell where the slug ends and the figure name begins.
- An `img/` file that resolves to no reportable slug is never reported. A faculty logo or a README screenshot stays silent.

With this rule, all six incident files under the provisional prefix are still reported: they are kept files, more than two of them, under one unsheltered slug of more than one word.

The rule identifier joins `RULE_IDS` in a new group `# workspace family`, placed after `proposal-misplaced` so that #8's additions land in another hunk. The call sits beside `paths_findings()` in `check_findings()`.

Severity is warning, not error. This is workspace state, not proposal text. The write skill's error list is binding, and must not oblige a writing pass to rename files the user never asked to rename. The warnings bucket is already headed "possible false positives", and the message says that a file the user placed on purpose can stay.

The tests sharing this vocabulary:
- `tests/helpers.is_fixture_proposal` keeps `NON_PROPOSAL_MARKDOWN` and `NON_PROPOSAL_SUFFIXES` and replaces its sibling test for `-review.md` with `check.py`'s rule: `family_members` over the fixture's listing returns `proposal` for the file, with `check.py`'s existing block test as `ends_in_block`. An orphaned review without a block is therefore not taken for a proposal, and f00's `ml-code-review.md` still is.
- An L0 test asserts that the block and the code agree: the roles of the block's family table equal `FAMILY_ROLES` plus the ideation-notes row, both ways, and each row's file-name shapes classify as that role; every name in `WORKSPACE_LEVEL`, the build-definition forms and the installer folders appear verbatim in `shared/blocks/workspace-files.md`; and every backticked file name in the block is one `check.py` classifies or allows. The installer folders are read from `install.py`'s tables (the standard targets, the workspace target of each host in `HOST_DIRS`, and the working-folder entries of `NATIVE_DIRS`), which `test_troubleshoot_collect.py` already pins against the collector, never from a hand-copied list. This is the "names agree" clause in skill-packaging.

**D7 — Lit-search sizing (Q1, answered (a) with threshold target (i)).**
- **The count line.** Both scripts build the YAML string first, then print `candidates: N (L lines, C characters on stdout)` on stderr, then the YAML. The line therefore comes before the output a host may cut. When `C` or `L` exceeds the threshold, the line adds `— more than some hosts show from one command; run narrower`.
  - In `search.py` the line is printed in `main()` after `federate()` returns, so it always follows the untouched `sources:` line.
  - The count line is for the agent, not a degradation note to relay.
  - The threshold's two bounds are constants in each script. These are two copies, short of the third-repetition rule. `common.py` is left alone so the vendored copies do not churn and #6's `common.py` edit is unaffected.
- **The threshold: 25,000 characters or 1,800 lines** (task 1.1, `measurement.md`). The recorded caps of the supported hosts in their default configuration are Claude Code's 30,000 characters (2.1.296), Codex's 10,000 tokens, about 40,000 bytes, for its bundled models (`90f00bd`), and OpenCode's 2,000 lines or 50 KiB (`c1615b1`); Copilot's was not found. Under Q1's threshold sub-question (i), the threshold lies below the smallest of them in characters, and below OpenCode's in lines, the only cap counted in lines. Codex's 10,000-byte fallback for models outside its catalog is recorded and not counted: it would put the threshold below what one seed at the floor emits, and the line would then flag nearly every run on every other host. This exclusion departs from the literal answer to Q1 (i), "below the smallest cap task 1.1 records", so it was put to the maintainer as a direct question in the approval request; the maintainer excluded the fallback on 2026-10-14 ("Exclude it"), and the threshold stays 25,000 characters or 1,800 lines (decision log, approval answers). Each script holds both bounds as constants.
- **The snowball default: 5, one seed per call in the example** (task 1.1). Two of w03's three DOIs are synthetic and resolve nowhere, so the two-seed runs pair w03's resolvable DOI with the resolvable DOI of the `SKILL.md` example. Two seeds at 5 emit 41,392 characters, so not even 5 fits two seeds; under the rule the default is the floor, 5, and the `SKILL.md` example snowballs one seed per call. One seed at 5 emits 17,657 to 23,735 characters, under the threshold; one seed at 8 does not. All runs were keyless, because no key resolves through the shipped lookup on the measuring machine. The search default stays 10, because callers such as ideate pass their own; the example's `--limit 10` stays too, since both measured runs emitted 8,566 characters, with only Crossref answering.
- **No dev `.env`.** The keyed run uses only the shipped resolution (`$THESIS_PROPOSAL_KEYS` or `~/.config/thesis-proposal/api-keys.env`), never the repository's `.env`, as #5 settled (widen-lit-live D3). Loading `.env` into the process would expose unrelated keys to the script.
- **SKILL.md.** One paragraph after "Both emit CSL-YAML …":
  - the count line is for the agent, not a degradation note to relay;
  - when the tool result shows a truncation or omission marker, or fewer `- id:` entries than the count line's N, run narrower: fewer seeds per call, one direction, a lower limit;
  - never redirect search output into the workspace, unless the user asks to keep the candidate list (Workspace files).

  The trigger is something an agent can observe. "More output than the host showed" asks it to compare a count against an output it cannot measure.

Rejected:
- **A `--brief` mode.** Abstracts are what the relevance judgment reads ("not keyword overlap"). A brief-then-full flow doubles requests on keyless, rate-limited sources (Semantic Scholar 429s) and adds a CLI contract.
- **The note alone.** The default is known to exceed the cap, so every first run would be truncated and then repeated.

**D8 — Verdicts.** Three verdicts live in `harness/l1_checks.py`, `verdict_family_only`, `verdict_family_renamed` and `verdict_no_orphans`, beside one public helper, `renamed_proposal`. Each returns `(passed, explanation)` (the helper: the new proposal or `None`, with the reason), and each has L0 tests in `tests/unit/test_family_verdicts.py`. They classify through `CHECK_SCRIPT.family_members`, the listing classifier the check's own warning uses (D6), never a second vocabulary: a `-review` or `-feedback` file is a proposal or a companion by the same metadata-block test, so the verdict and the warning a writer sees never classify a file differently. A path inside a folder other than `img/` counts as that folder, which is a kept `<slug>.<label>/`, an allowed folder such as `bug-report/`, or nothing.

- `verdict_family_only(added, present, staged=(), keep_licensed=False, seed="", read=None)` takes:
  - `added`: the workspace-relative paths the run added;
  - `present`: every path after the run;
  - `staged`: the paths staged before the run;
  - `keep_licensed`: whether the request asked to keep something;
  - `seed`: the staged proposal a draft scenario expects to be drafted in place;
  - `read`: a function from a path to its text, for the metadata-block test; the runner reads the workspace and falls back to the staged bytes for a file the run removed. A path it cannot read, and every path when `read` is `None`, stays a proposal, as in the check.

  An added path passes when it is one of these:
  - a family member other than a `kept file`, of a sheltered slug: a proposal, notes file or harvest record carrying it is present after the run;
  - `ideation.notes.md`;
  - the same-suffix counterpart, under a new slug, of a staged family member the run removed. This is a rename, and it holds for kept files and figures too;
  - an allowed name: a hidden path, a `WORKSPACE_LEVEL` name, a build definition, or anything under `bug-report/`.

  A `kept file` path that is not a rename counterpart passes only with `keep_licensed`. When `seed` is given and still present while the run added another proposal, both are named as a second proposal beside the seed. The verdict names every offender. A dump the run added on its own under a correct slug still fails.
- `renamed_proposal(staged, after, old)` returns the one proposal the run added: a top-level proposal in `after` that was not staged and whose slug is not `old`. None, or more than one, is a failure that names them. "Not staged" keeps an unrelated staged proposal from counting as the rename.
- `verdict_family_renamed(staged, after, old)` takes `{relpath: bytes}` maps and the old slug. It derives the new slug from `renamed_proposal`, and fails when:
  - a path starting `<old>.`, `<old>-` or `img/<old>-` remains, other than a built output (Q5). The check is by prefix, not through the classifier, so a leftover `<old>-handout.md` or an `<old>-review.md` the classifier would take for a proposal is still caught. A new slug that extends the old one (`<old>-v2`) carries the old prefix by construction, so its own files are exempt;
  - a staged member other than a built output is missing under the new slug with its suffix;
  - a staged binary member's bytes changed;
  - the proposal or the notes file still contains `img/<old>-`, other than as the start of `img/<new>-` when the new slug extends the old one.
- `verdict_no_orphans(findings)` reads the check's `--json` findings over the renamed proposal and fails on any `companion-orphaned` finding, naming its message. It also fails when the check did not run: the runner reports a crash or output without JSON as a `check-failed` finding, and an absent finding is then no evidence that nothing was orphaned.

The runner's hidden-path filter stays, which is a known gap: a working file written as a dotfile is not seen. The installer folders are therefore exercised by L0 tests and the check, not by dev runs. `select_draft`'s tolerance for a fresh `<slug>.md` stays: it decides which file is graded, not whether the run kept the family together, and changing it would change the Inspect twins' verdicts.

**D9 — Scenarios and the advisory observation.**

Three new scenarios in `claude_runner.SCENARIOS`, L1 only, with no Inspect twin, so their family verdicts are part of the L1 verdict on every runner that has them:
- **`litsearch_snowball`**
  - Fixture: w03-snowball-seed. Skill: `proposal-lit-search`.
  - Request: snowball from the proposal's references and merge what fits, with "I cannot answer any questions — decide and tell me what you did".
  - Verdicts: `verdict_litsearch_expanded` and `verdict_family_only`.
  - It hits live APIs, so expect variance, as with `supervise_literature`. family-only is deterministic over the workspace.
- **`write_rename_family`**
  - Fixture: w14. Skill: `proposal-write`.
  - Request: a settled new title, "put it in and rename my files to match".
  - Verdicts: `verdict_family_renamed`, `verdict_family_only` with the staged paths, and `verdict_no_orphans` over a check run on the new proposal (`run_check_json`), which fails on any `companion-orphaned` finding and on a check that did not run.
- **`ideate_seed_rename`**
  - Fixture: w15. Skill: `proposal-ideate`.
  - Request: resume from `<provisional>.notes.md`, preamble pre-answered, lookups declined, a stated working title that yields another slug, "treat this as 'enough' and seed now".
  - Verdicts: `verdict_seed`, `verdict_family_renamed` (staged: notes, kept reading list, sketch) and `verdict_family_only` with the staged paths. The renamed reading list passes as a rename counterpart, without `keep_licensed`.

**The advisory observation (Q4, answered (c)).** Every other dev run reports `verdict_family_only` as a `family` field in its summary, beside `single_context` and `handoff`. It never changes the scenario's pass flag or the exit status, so the dev runner and the Inspect twins still reach the same pass flag for the same artifact ("Inverted-hybrid runners", scenario "Verdict reached from both runners"). For the three `DRAFT_SCENARIOS` the runner passes the staged proposal as `seed`, so a draft written to a fresh `<slug>.md` beside the seed is reported. `workspace_changes()` reads `scenario.get("fixture")`: a scenario without a fixture stages nothing and every file counts as added.

The scenarios are host-agnostic. A Copilot run needs the user's go like any other, and is not part of this change's verification.

Each scenario sits beside its own skill's scenarios in `SCENARIOS`, not at the dict's tail: `litsearch_snowball` after `supervise_literature`, `ideate_seed_rename` after `ideate_scoped_partial`, `write_rename_family` after `write_repair_citations`. #8 adds a review-currency scenario beside the `handoff_*` block at the tail, and two insertions at one anchor would conflict on its rebase. The fixtures README is ordered by fixture number, so its w13–w15 entries stay where w16 will follow; that hunk is a trivial rebase resolution, named in the landing step.

**D10 — Fixtures.** All slugs are invented, and none comes from the incident. This change claims w13–w15; #8 takes w16.
- **`w13-orphaned-companions`**
  - The proposal `ci-repair-agent-configurations.md` is f28's text plus one figure link to `img/ci-repair-agents-pipeline.png`.
  - The leftovers are `ci-repair-agents-review.md` (no metadata block), `ci-repair-agents.candidates.yaml` and that figure, a tiny valid PNG so the export matrix still builds the proposal.
  - Must-not-report files: `guidelines.md` (prose only, no TOML), `ideation.notes.md`, and `.agents/skills/.thesis-proposal-install.json` (a synthetic record).
  - The oracle is f28's check result plus the `companion-orphaned` warnings: the three leftovers and the stale link.
  - The rest of the allowlist and the supported setups are covered by `tmp_path` L0 tests rather than committed (task 2.1). A fixture `.gitignore` would also apply to the fixture folder in git, `bug-report/report.md` would enter the corpus walkers, and binary source documents would bloat the corpus.
- **`w14-family-rename`**
  - `ci-repair-agent-configurations.md` (f28 plus a figure link to its own `img/ci-repair-agent-configurations-pipeline.png`), with its notes file (one line mentioning the figure), its review and the PNG.
  - Check-clean apart from what f28 reports, with an oracle.
- **`w15-provisional-notes`**
  - `flaky-ci-triage.notes.md` holds converged ideation state: the five aspects concrete, so a one-shot seed is plausible. Beside it are `flaky-ci-triage.reading-list.md` and `img/flaky-ci-triage-sketch.png`.
  - No proposal and no oracle. The `.reading-list.md` is excluded from the corpus walkers by the helper predicate.
- **Documentation.** `tests/fixtures/README.md` documents all three.

**D11 — Bookkeeping in the implementing commit.**
- `docs/backlog.md`: "Dev-runner scenarios for four skills" becomes "… three skills" and loses `proposal-lit-search` and `litsearch_expand`. On `main` after #5, the entry it used to sit three lines above ("Live check beyond DBLP") is gone, so the hunk is plain.
- `harness/README.md` lists the three scenarios and the advisory `family` field under "Dev runs".

**D12 — Landing.** The order is #5 → #6 → #7 → #8.
- **#5 has landed** (`ccad5a7`, archived in `1999f96`) after this draft's base `1db2ee4`. It touched no spec. This draft is reconciled against `main`'s text; the worktree branch is not moved by planning, and implementation starts from `main` after #6 (tasks).
- **#6 first.** #6 adds a UTF-8 reconfigure at the top of `main()` in `check.py`, `search.py` and `snowball.py`, and an ADDED skill-packaging requirement "Script output encoding". This change edits other hunks of the same functions, so it rebases on #6 and re-runs the sync for the five `check.py` copies.
- **#8 after.** #8 rebases on this change and depends on four things here:
  - the skill-check sentence scoped to this finding ("For this finding, the check SHALL open another file only to tell a proposal from a companion"), so #8's review read is not forbidden;
  - the `family_member(name, handles)` signature and its `review` kind;
  - the requirement name "Proposal family under one handle";
  - `is_fixture_proposal` never taking a review for a proposal.

  #8's draft already takes `w16-superseded-record` and records these dependencies (its task 1.1); nothing needs adding to it. Its other touch points are `RULE_IDS` and `proposal-review`'s Output section and `## Handing over` routes, adjacent to the inserted section, and the tail of `SCENARIOS`, which this change leaves free (D9). The w16 entry in `tests/fixtures/README.md` follows this change's w15 entry, a one-hunk rebase resolution for #8.
- **No shared requirements.** No requirement is MODIFIED here, and #6 and #8 add their own, so archive order cannot drop wording.

## Risks / Trade-offs

- **Every body grows by about 420 words** (≈ +560 tokens per skill load), the role table included; the table replaces the inline family list, so it costs about 50 words over the first draft. Removing or shortening the location sentences saves 15–40 words at eight sites; troubleshoot gains one sentence (Q8). A uniform addition raises the median about as much as every body, so the cap loosens in absolute terms and the largest bodies' share of it drops. Expected after landing:
  - median ≈ 3,090 and ceiling ≈ 6,180;
  - supervise ≈ 5,140 (83 % of the ceiling, down from 88 %);
  - ideate ≈ 4,680 (76 %);
  - every body far under the 500-line limit; the table adds 12 lines.

  Tasks 4.3 and 5.7 re-measure this instead of trusting the estimate.
- **The orphan rule still flags some project files.** Two kept-shaped files under one name of two or more words, such as `docker-compose.override.yml` and `docker-compose.prod.yml` in a code repository used as the workspace, or a LaTeX project named `master-thesis` with its `.synctex.gz` and `.run.xml`, are reported. → It is a warning in the "possible false positives" bucket, the message says a file placed on purpose can stay, and the check's relay offers the rename only for files of the proposal's own earlier slug. One-word names (`thesis`, `tsconfig`, `jest`), single source documents, build outputs and unprefixed images are never reported. A skip list of tool auxiliaries was not added: it ages with every tool.
- **A proposal slugged like another's review.** When `<x>.md` and a proposal `<x>-review.md` sit side by side, the skill-check rule reads `<x>-review.md` as `<x>`'s review, because its base slug has a proposal. A check of `<x>-review.md` itself is quiet (the checked file is a proposal); a check of `<x>.md` reports `<x>-review`'s own review and figures. The two names collide by construction, since `<x>`'s review would carry the same name. → Left as the rule states it, by the maintainer's decision of 2026-10-14: no wider proposal-vs-review test. Promoting every `-review` file that ends in a metadata block would silence the case, but it would change the skill-check delta's rule (decision log, review findings and approval answers).
- **An agent saves a dump under the correct slug without being asked.** → The check cannot tell this from a requested keep. `verdict_family_only` catches it in dev runs, and the block's wording is the guard.
- **A host's cap is lower than the threshold.** → Task 1.1 records the caps it can read at $0; the trigger in the skill is observable on any host (a truncation marker, or fewer entries than the count line's N).
- **A rename fails midway**, for example on a locked file. → The block requires the target check first, a stop on the first failure, and a report of what moved. A later check run reports leftovers.
- **Troubleshooting captures linger** when the user declines removal (Q8). → They are named, allowed and never family-shaped, so the check stays quiet; family-only allows them.
- **New wording reaches the skills.sh audits.** → `poe audit` runs before any publish, as always. The wording adds no network, credential or execution instruction.
- **Live-API variance in `litsearch_snowball`.** → Only the expansion verdict is network-dependent. A degraded run reads as a failed expansion with the stderr notes in the summary, not as a family failure.
- **One restatement of the location remains** in import's mandate, and one in publish's fallback paragraph (Q3). → Both are kept on purpose, and the skill-packaging delta names the exception.

## Migration Plan

No user file is moved or rewritten by this change. Existing workspaces with fragmented families see `companion-orphaned` warnings on the next check, and the handoff can offer the whole-family rename as an anchored choice. Rollback is a revert of the implementing commit followed by `python3 scripts/sync_shared.py`.

## Questions before implementation

These change specs or tasks, so they were for the maintainer and were not deferred. All eight were answered on 2026-10-14 (decision log, last part); each ends with its answer.

- **Q1, lit-search sizing.**
  - Options: (a) a lower snowball default set by measurement, plus the count line; (b) the count line only; (c) a `--brief` mode plus the count line.
  - Recommended: (a), for the reasons in D7.
  - Sub-question, what the threshold targets: (i) the smallest cap task 1.1 records for the supported hosts, with the default's floor at 5 and one seed per call in the example when even 5 does not fit; (ii) Claude Code's cap, with the count line naming that host, and smaller-cap hosts relying on the observable trigger. Recommended: (i). The warning is then true on every recorded host, and a smaller default costs one extra call, not a truncated judgment.
  - With (b), the skill-lit-search "Default run fits" scenario and the default sentence go. With (c), the requirement gains a mode. With (ii), the threshold sentence names the host.
  - **Answer: (a), threshold target (i).** The default is set by task 1.1's measurement, floor 5, and both scripts print the count line.
- **Q2, orphan scope.**
  - Options:
    - (a) all family shapes, including kept and build files. This flags supported setups on every check run: publish's shipped build example (`faculty.typ`, `proposal.pdf`); the source documents of import, supervise and reverse (`submission.pdf`, `exposé.docx`, `thesis.pdf`), which supervise checks on every intake, with a student's name in the message when the source is named after the student; and code-repository workspaces (`vite.config.ts`, `data.tar.gz`, README screenshots under `img/`).
    - (b) only review, feedback, harvest, handout and figures. This misses every working file of the incident.
    - (c) any file in the proposal location that is not allowed. This is noisy wherever the root holds the user's other files.
    - (d) slug-shaped names only; an unsheltered slug is reported when it has an unambiguous companion or at least two kept files; built outputs never alone; nothing under a workspace build; the root scanned too when a location is configured.
  - Recommended: (d). It still reports all six incident files and stays quiet on the setups (a) flags.
  - **Answer: (d)**, slug-shaped names only.
- **Q3, location anchors.**
  - Options:
    - (a) cut import's mandate clause together with its pin, put a pointer at every other file-creating step, and leave publish's fallback paragraph byte-identical;
    - (b) keep import's mandate and its pin as they are (the 2026-08-31 decision), put a pointer at every other file-creating step, leave publish's fallback paragraph byte-identical, and have the block say that family files never go into a host's scratch or temporary folder;
    - (c) put a short anchor that restates the definition at each step ("the working directory unless `[paths] proposals` says otherwise"), about ten words at nine sites, and keep import's mandate.
  - Recommended: (b). It keeps the one anchor that evidence put where a delegated run cannot skim past it, and states the definition once everywhere else, as the decision asks. (c) brings back the restatements the decision removes.
  - **Answer: (b).** Import's mandate and its pin stay, every other file-creating step gets the pointer, publish is unchanged, and the block says proposal files never go into a host's scratch or temporary folder.
- **Q4, family-only on existing dev scenarios.**
  - Options: (a) add it to the L1 verdict of `ideate_scoped`, `import_messy` and the three `write_*` draft scenarios on the dev runner only; (b) only the three new scenarios; (c) report it on every other dev run as an advisory `family` field that never changes the pass flag or exit status; (d) add it to the Inspect twins as well, which changes shipped verdicts and needs its own cost-gated decision.
  - Recommended: (c). (a) breaks "Verdict reached from both runners", because the Inspect twins of those scenarios keep their scorers. (c) is $0, keeps parity, and shows unrequested files where they would appear, including a draft beside its seed.
  - **Answer: (c)**, the advisory `family` field, which never changes a pass flag.
- **Q5, rename reach.**
  - Links. Options: update links in the proposal and the notes file; or in the proposal only, as the decision states it. Recommended: both files, since the notes file is the other family file that links figures.
  - Built outputs. Options: (i) rename them with the family; (ii) leave them as previous builds, name them, and offer a rebuild. Recommended: (ii). A renamed stale PDF looks like a current build of the new title, and an open PDF or DOCX is the member most likely to refuse a move. Under Q2 (d) a left-behind build is not reported. This reads "the whole family" as everything except regenerable outputs; with (i), the block, the rename requirement and `verdict_family_renamed` drop the exception.
  - **Answer: "leave, name, offer rebuild".** Links are updated in the proposal and its notes file; built outputs stay as previous builds, and the skill names them and offers a rebuild.
- **Q6, `ideation.notes.md`.**
  - Options: (a) rename it to the provisional slug's notes file as soon as a topic phrase exists in a resumed session; (b) keep the name until seeding and rename it then.
  - Recommended: (a). The ideate spec already says the notes file exists under a provisional handle as soon as a topic phrase does. Renaming avoids a second notes file for the same idea and frees the shared name for the next idea.
  - **Answer: (a).**
- **Q7, installer files beyond the decision's list.**
  - The decision names `.agents/skills`, `.claude/skills`, `.opencode/skill(s)` and `.thesis-proposal-install.json`. The repository's own installer and collector also know `.kiro/skills/` and `skills-lock.json`, which `npx skills add` keeps in the workspace root. `skills-lock.json` is not hidden, so "nothing else" would have an agent treat it as a stray file.
  - Options: (a) list both as installer-managed, never written or tidied, and derive the names-agree test from `install.py`'s tables; (b) list only the decision's names.
  - Recommended: (a). With (b), the block, the proposal-file-format delta and `WORKSPACE_LEVEL` drop the two names, and the names-agree test uses a fixed list.
  - **Answer: (a).**
- **Q8, troubleshooting captures.**
  - Troubleshoot's rung 3 needs a file for `collect.py --script-output`. The block forbids it in the workspace, the collector refuses an existing `bug-report/`, and the Copilot sandbox denies the temp folder.
  - Options: (a) allow the named captures `check-output.txt` and `version-output.txt` as workspace-level files while a report is assembled, and offer to remove them once the bundle carries them; (b) let the collector accept captures already inside `bug-report/`, a script change; (c) captures in a temp folder or the chat, with the collector reading stdin, also a script change.
  - Recommended: (a). No script change, and it works under every sandbox. With (b) or (c), the block, `WORKSPACE_LEVEL` and the troubleshoot rows of D4 change, and the collector gains a task.
  - **Answer: (a).**

## Decision log: critic pass (2026-10-14)

Applied:
- **Rename counterparts in family-only** (ideate_seed_rename would fail on correct behaviour): `staged` parameter and the rename-counterpart rule (D8), with L0 cases (task 7.1).
- **Parity with the Inspect twins and the missing fixture key**: Q4 now recommends the advisory observation; `workspace_changes()` handles a scenario without a fixture (D9, task 7.3).
- **Drafting from a seed**: write drafts into an existing seed (D5), with a proposal-file-format scenario and the advisory `seed` check. The check does not fail `write_from_seed`'s L1 verdict, because that would break parity with its Inspect twin.
- **Supported setups flagged by the orphan rule** (publish's build example, source documents, code repositories, student names in supervise): Q2 option (d) is recommended and specified (D6), and the build-output carve-out is in the proposal-file-format delta.
- **Scoped read-only sentence** (two findings): the skill-check sentence applies to this finding only; #8's dependency is recorded (D12).
- **"Without restating" vs the kept restatements**: the skill-packaging delta names the exception for a pinned mandate and a script-location fallback paragraph.
- **Seeding vs requested-rename collisions**, a member that cannot be moved, and stale links naming the old slug only when it resolves: separate rules and scenarios.
- **"Whatever its name"**: reworded to the `-review`/`-feedback` rule; `-handout` is classified by suffix; the helper keeps its suffix exclusions (task 2.4).
- **Sheltering**: a notes file and a harvest record shelter a slug in both the check and family-only; `ideation.notes.md` is accepted.
- **"The user", not "the student"**, in the block and the requirements.
- **Lit-search literals, offline scenario, keyed run without `.env`, host caps, observable trigger, lines in the count line**, and "unless the user asks to keep it" in the lit-search requirement (D7, task 1.1).
- **`<slug>` placeholders** with "handle" defined once.
- **Import's mandate kept** (Q3 now recommends (b)), citing `2026-08-31-fix-import-output-location`; D2 no longer claims hosts read the whole file before acting.
- **Workspace build files** allowed in the block; built outputs never reported under a workspace build.
- **The root scanned under `[paths]`**, and figures in "an `img/` folder beside the proposal", including import's extraction step.
- **Reading in slices** as the general answer to size in the block.
- **The pinned `family_member` signature** (D6).
- **Fixture numbers and #5's backlog entry**: recorded in D10–D12.

Raised as questions instead of decided: `skills-lock.json` and `.kiro/skills/` (Q7), troubleshoot's captures (Q8), built outputs at a rename (Q5).

Not taken over:
- **Moving this worktree's branch onto `main`.** This planning pass is scoped to the change folder and commits nothing; the text is reconciled against `main`, and implementation starts from `main` anyway.
- **Adding a note to #8's draft.** That draft is another session's work, and it already takes w16 and lists its dependencies on this change.

## Decision log: maintainer answers (2026-10-14)

The maintainer answered in the session chat, accepting every recommendation ("Accept, build in parallel"):
- **Q1** (a) with threshold target (i): a measured snowball default, floor 5, and the stderr count line. Task 1.1 still decides the literal threshold and default.
- **Q2** (d): slug-shaped names only (D6).
- **Q3** (b): import's mandate and pin stay, pointers elsewhere, publish unchanged; the block's first sentence carries the scratch-folder ban.
- **Q4** (c): the advisory `family` field (D9).
- **Q5** "leave, name, offer rebuild": links updated in the proposal and its notes file; built outputs stay as previous builds, named, with a rebuild offered.
- **Q6** (a): `ideation.notes.md` becomes `<provisional>.notes.md` as soon as a topic phrase exists.
- **Q7** (a): `.kiro/skills/` and `skills-lock.json` listed as installer-managed; the names-agree test reads `install.py`'s tables.
- **Q8** (a): `check-output.txt` and `version-output.txt` allowed while a report is assembled, removal offered once the bundle carries them.

An earlier decision in the same session ("role table in #7, names in #9") shaped the block's first paragraph: the family is listed once, as a role → file-name table with today's names, and renaming files is deferred to #9 (Non-Goals). What that changed:
- D1 resolves every bracket and carries the table; paragraph 2 refers to "every family file" instead of listing the members again.
- D3 pins four blank-line-separated blocks instead of three, because the table stands after a blank line. A table that interrupts a paragraph renders in GitHub's renderer but not in every CommonMark renderer, and skills.sh's is not known.
- D6's kinds are the table's role names (`harvest record`, `supervisor feedback`, `built output`, `kept file`), exported as `FAMILY_ROLES`, and the names-agree test compares the table with them both ways. `review` keeps its name, which #8 depends on.
- D6's `family_findings` takes `overrides` and the proposal's text, so it can tell a configured location from a governing file elsewhere without reading `guidelines.md` again, and reads the figure links without a second read.
- The skill-packaging delta gains the table and its agreement with the check.
- The body-size estimate grows by about 50 words per skill; tasks 4.3 and 5.7 re-measure it.

## Decision log: measurement (2026-10-14, task 1.1)

`measurement.md` holds the record. What it changed:
- D7's threshold gains a line bound, 1,800 lines below OpenCode's 2,000; the character bound stays 25,000, below Claude Code's 30,000. The skill-lit-search delta carries both.
- The default stays 5, at the floor, because two resolvable seeds at 5 already exceed the threshold; the `SKILL.md` example therefore snowballs one seed per call, and the skill-lit-search delta says so.
- The two-seed runs could not use two of w03's DOIs, because two of the three are synthetic; they pair w03's resolvable DOI with the example's.
- Codex's 10,000-byte fallback for models outside its catalog is recorded and not counted. Because that departs from the literal Q1 (i) answer, it was a direct question in the approval request, not an open point (D7); the maintainer excluded it (approval answers, below).
- After group 4 the bodies measure median 3,169 words, ceiling 6,338, supervise 5,215 (82 %); the role table's pipes count as words in that measure.

## Decision log: review findings (2026-10-14)

A review of the implementation raised thirteen findings, one of them (the `check-failed` pass) twice. What they changed:
- **Proposal or companion, by the delta's rule.** The code had tested whether *any* family-shaped file carried a `-review` file's base slug, so a built output or kept file under `<x>` turned a real `<x>-review.md` proposal into a review of `<x>`, unread, and the checked proposal could be reported as an orphan of itself. `family_members` (D6) now applies the skill-check wording, "base slug has no proposal", treats the checked file as a proposal whatever its name, and is shared by the check, the verdicts and `is_fixture_proposal`. D6's `family_member` row now says it is the name-only reading.
- **Family-only reads what the check reads.** `verdict_family_only` gained `read` (D8), so a metadata-less `<x>-review.md` under a wrong slug fails the verdict as the check reports it; the earlier module comment claimed an agreement the code did not have.
- **A check that did not run fails.** `verdict_no_orphans` fails on a `check-failed` finding (D8), the "empty is not a pass" failure mode.
- **Kept files need a slug of two or more words** to make a slug reportable (D6), with the relay sentence in `proposal-check` made conditional on the files belonging to the proposal's earlier slug. Without it, a LaTeX build (`thesis.synctex.gz`, `thesis.run.xml`, and with them `thesis.tex` and `thesis.pdf`) and code-repository config pairs (`tsconfig.*.json`, `jest.*.js`) were reported on every check run, which contradicts the premise Q2 (d) was accepted on. This reads Q2 (d)'s "slug-shaped names only" with Content-derived slug filenames' 2–4 words; it narrows the kept-file arm only. It was named in the approval request, and the maintainer confirmed it (approval answers, below).
- **`.justfile`** is a build definition for the check as it is for publish (D6).
- **Non-UTF-8 directory entries** are skipped by the listing (D6) instead of ending the check with a traceback.
- **Ideate's notes-file creation** at :44 and :68 gets the location pointer (D4), which Q3 (b) asks for at every file-creating step.
- **A taken name at seeding moves the whole family to the suffixed slug** (D1 paragraph 2, D5), as the proposal-file-format delta already requires; the block had read per file.
- **Planning artifacts** now describe what was built: three verdicts and `renamed_proposal` (proposal, D8), the `renamed_proposal` refinements, folder paths in family-only, and task 6.2's verify line.
- **Scenario placement** beside each skill's siblings (D9, D12), to keep `SCENARIOS`' tail free for #8.
- **Codex's fallback cap**: the exclusion was put to the maintainer as a direct question (D7), and the maintainer excluded it (approval answers, below).

Not taken over: promoting every `-review` or `-feedback` file that ends in a metadata block to a proposal, which one finding offered beside the minimum fix. It would silence the remaining collision case in Risks, but it changes the skill-check delta's rule ("whose base slug has no proposal"), so it was left to the maintainer, who decided against it (approval answers, below).

## Decision log: approval answers (2026-10-14)

The maintainer answered the approval request in the session chat, each time with the recommended option:
- **Codex's fallback cap: excluded** ("Exclude it"). The threshold stays 25,000 characters or 1,800 lines (D7). The 10,000-byte fallback for Codex models outside the bundled catalog stays recorded in `measurement.md` and is not counted; the departure from the literal Q1 (i) answer is a decision now, not an open question.
- **Ideate's slug length: fixed in this change** ("Fix now: 2–4 words"). Both `ideate_seed_rename` dev runs derived an eight-word slug from the full working title: ideate's seeding sentence gave no length, while write's step 2 says "2–4 title words". Ideate's creation sentence now carries write's rule, "(lowercase, hyphenated, 2–4 title words; numeric suffix on collision)", pinned as `proposal-ideate--seed-slug-shape.txt`, red before the prose edit (D5, task 10.2). The skill-ideate delta requires the shape and gains a scenario for a long working title. This brings ideate's prose to proposal-file-format's existing "Content-derived slug filenames", whose main requirement does not change. `shared/blocks/workspace-files.md` states no slug length and nothing that contradicts it, so the block is unchanged. Ideate's body grows by 9 words, to 4,819 (76 % of the 6,344-word ceiling).
- **The review findings' open points: both confirmed** ("Accept all five"; for this change it settles two). Kept files make a slug reportable only under a slug of two or more words (D6), as implemented. No wider proposal-vs-review test: the skill-check delta's rule ("whose base slug has no proposal") stays, and the collision case stays recorded in Risks.
- **Dev-run observations: backlog entries** ("Backlog entries"). `docs/backlog.md` gains two entries, with `measurement.md` as evidence: the write skill was not loaded for a rename-only request, and the handoff lines were missing after the rename-only requests and haiku's lit-search run (the advisory `handoff` field). Neither widens this change.
- **One repeat run.** The maintainer approved repeating the ideate dev run on haiku once after the fix (task 10.5). Its result is in `measurement.md`.
