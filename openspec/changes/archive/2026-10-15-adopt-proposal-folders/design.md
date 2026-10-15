## Context

**Status (2026-10-14).** Drafted from the maintainer's grill-me decisions of 2026-10-14 (binding, recorded below as D1–D13) and the research map written before them. Where the map recommended B1 (flat names inside folders) or an opt-in layout key, the decisions supersede it. D14–D25 are decisions this draft derived to make the binding ones implementable; each says which binding decision it serves. A critic review of the first draft was folded in the same day; the "Decision log" at the end records what was applied and what was rejected. "Questions before implementation" lists what the draft could not settle alone; the maintainer answered all seven the same day, each with the recommended option, and the decision log records the answers and where they landed.

**Terms.** A proposal's *slug* names its folder and its proposal file; as the name that travels with the files leaving the folder it is the *handle*. *Location* is the directory `[paths] proposals` names, relative to the workspace root (default `.`). A name is *slug-shaped* when it is lowercase ASCII letters and digits joined by single hyphens, one word or more (check.py's `SLUG_RE`), so `idea` and `idea-2` qualify; the 2–4-word bound applies only to slugs derived from a title. Placeholders: `<slug>`, `<old>`, `<new>`, `<label>`, `<name>`.

State that shapes the approach:

- **One vocabulary, three consumers.** `check.py` holds the family vocabulary (`FAMILY_ROLES`, `COMPANION_SUFFIXES`, `HANDOUT_SUFFIX`, `IDEATION_NOTES`, `FIGURE_FOLDER`, `_shape`, `family_member(s)`), and `harness/l1_checks.py` and `tests/helpers.py` classify through it, so a verdict never disagrees with the warning a writer sees. `l1_checks` binds `FIGURES`, `SHELTERS`, `PROPOSAL`, `KEPT` and `BUILT_EXTENSIONS` at import time, and 57 test modules import `helpers` or `l1_checks`, so a renamed constant fails collection, not one test. `test_workspace_files_block.py` holds the block's role table equal to that vocabulary. About two thirds of the vocabulary exists only to resolve the hyphen ambiguity (`ml-code-review.md` as proposal or review) and slug prefixes on figures; a folder makes both disappear.
- **Location test today.** `paths_findings` compares `proposal.parent` with `<governing guidelines.md's directory>/<value>` and is silent when the key is unset. `resolve_guidelines` tries the proposal's directory, then the working directory.
- **Who calls the check from where.** `claude_runner.run_check` and `run_check_json` start the check without `cwd`, so from the repository root; the Inspect sandbox runs `check.py ws/<proposal>` from the sandbox root; `tests/helpers.run_check` runs in-process from pytest's working directory, with about 84 callers writing flat `tmp_path` proposals; `test_fixture_oracles.py` alone runs with the fixture root as working directory. About 54 lines in tests and harness spell a fixture file's path (`FIXTURES / "<id>" / "<name>.md"`), some read at import time (`helpers.CLEAN_DRAFT`, `skill_evals.W01_SEED`, `W08_SEED`, `F27_DRAFT`). Three corpus walkers glob `tests/fixtures/*/*.md`: `scripts/ci_typst_build.sh`, `test_anonymity_guard.py` and `test_check_rules.py::test_every_emitted_identifier_is_declared`.
- **Stem-keyed scripts.** publish derives every output name from the proposal's stem (`<stem>.pdf`, `<stem>-handout.md`) and writes `.gitignore` into `proposal.parent`; it never reads `guidelines.md` and does not depend on the working directory, except through pandoc, which resolves `img/` against the working directory. collect redacts `{proposal.name, proposal.stem}`, reads `<stem>.notes.md`, `<stem>-review.md`, `<stem>-feedback.md`, and reads `guidelines.md` from the working directory.
- **Pandoc evidence.** Run from a directory other than the proposal's, the LaTeX-PDF and DOCX tiers drop every `img/` figure with only a `[WARNING]` on stderr, which `run()` discards on success. `--resource-path <proposal folder>` fixes both tiers; typst resolves relative to the `.typ` file and is unaffected, and fails outright on a missing image. `tests/unit/test_export_matrix.py` builds f16 from the repository root but asserts only that outputs exist. f16's import-source PDF itself already holds two image objects.
- **Harness staging.** `claude_runner.stage()` copies a fixture's top-level `.md`/`.txt` files and its `img/` only, and `staged_files()` mirrors that; the runners and verdicts list `ws/*.md`, `*-review.md`, `*-feedback.md`, `*.notes.md` without descending; `skill_evals.py` lists `ws/{pattern}` inside the Inspect sandbox; `routing.py` stages named proposal files flat.
- **OpenSpec 1.14.1.** A MODIFIED block may not drop a scenario name the current spec has (validator and archive both refuse), and the gate ratchets requirement length: ADDED ≤ 500 characters, MODIFIED ≤ its baseline entry in `openspec/long-requirements.json`, or 500 when it has none.
- **Open neighbour.** desktop-first-install is implemented and waits only for manual recipe runs. It owns "User-side script constraints", "Installation verified against the tracked tree", "Install identified from workspace evidence" and the README and walkthrough requirements in its user-onboarding delta, and its install probe uses `versioned_python_path`. add-setup-readiness-guide is archived, which frees "Users never work in this repository".

## Goals / Non-Goals

**Goals:**
- One shape for every workspace: a listing shows one folder per proposal, and a folder's content is legible without knowing the slug.
- A rename that is one folder move and one file rename, with no link edits and no partial-family state other than "folder moved, file not", which the check names.
- Every place that names a file follows one table: the shared block and `check.py`'s vocabulary, held equal by an offline test.
- Figures embedded on every tier whatever directory publish runs from.
- $0 subscription evidence, haiku and sonnet, for the six flows the maintainer named.

**Non-Goals:**
- **Reading the flat layout or old names.** No alias, no legacy-name finding, no migration script or skill feature (D1). An old-style `x.notes.md` inside a folder is simply an unclassified file.
- **A layout key.** `[paths] proposals` keeps its meaning (where the folders live); nothing else is added to the override vocabulary.
- **A per-proposal or ancestor build lookup.** Publish's lookup stays "beside the proposal", which is now "in its folder" (D6).
- **Changing what desktop-first-install owns**, in particular the working-directory stake of "User-side script constraints" (D13).
- **Inspect twins, matrix cells or any metered run.** Inspect tasks get their staging and listings fixed and are exercised once offline on `mockllm/model`; no matrix verdict is re-measured here.
- **Renaming spec scenarios without a deliberate baseline entry** (D18, Q6).

## Decisions

### Binding decisions (grill-me, 2026-10-14)

**D1 — Folders only.** The flat layout is removed. There is no layout key and no backward compatibility: flat workspaces and old file names are not read and get no special rule. `[paths] proposals` stays and says where the proposal folders live (default `.`). The only existing workspace is the maintainer's, migrated by hand (Migration Plan). *Alternative rejected in the grill-me:* an opt-in `paths.layout` with flat as default, which would have made four workspace shapes permanent in every skill's prose and every dev scenario.

**D2 — The folder is the slug.** A proposal lives in `<location>/<slug>/`, under the existing slug rules (lowercase, hyphenated, 2–4 title words, numeric suffix on collision, the collision now tested against folder names). Reserved folder names: `bug-report`, `img` and hidden names. A slug-shaped folder in the location counts as a proposal folder when it holds `<dir>.md`, a `notes.md` with the notes file's five section headings (all five as `## ` lines, order not tested; classification is not validation, and the check never reports on a notes file's headings), or a `harvest.md` (D15). Other folders are invisible: no skill lists them as candidates, writes into them, or reads beyond the classification test.

**D3 — Names inside the folder.** Files that leave the folder keep the handle: `<slug>.md`, `<slug>.pdf`/`.docx`/`.typ`/`.tex`, `<slug>.handout.md` (dot form, replacing `<slug>-handout.md`). Files that stay are role-named: `notes.md`, `review.md`, `feedback.md`, `harvest.md`, `img/<name>.<ext>` (no slug prefix), kept files `<label>.<ext>`. Reserved labels: `notes`, `review`, `feedback`, `harvest`, `handout`, `img`, and the slug itself (D16). The role → name table lives once in `shared/blocks/workspace-files.md` and once in `check.py`'s vocabulary, where `COMPANION_SUFFIXES`, `HANDOUT_SUFFIX` and `IDEATION_NOTES` give way to a `ROLE_NAMES` map (`notes → notes.md`, …) and a handle-shaped set (`.md`, built extensions, `.handout.md`); the about 66 per-skill mentions follow the table. Role files are matched by their exact basename everywhere (check, verdicts, collect), so kept files such as `peer-review.md`, `reading-notes.md` or `supervisor-feedback.md` stay kept files. `review_path()` becomes `proposal.parent / "review.md"`.

**D4 — Ideation starts in a folder.** proposal-ideate creates `idea/notes.md` when a new session starts (`idea-2/`, … when taken); a resumed session reuses its folder. When a topic phrase exists the folder is renamed to `<provisional>/`, and at seeding to `<final>/` if the slug changed; the seed is then written into it. `ideation.notes.md` no longer exists, and kept files before seeding go into the idea's folder rather than into the notes file.

**D5 — Rename is a folder move.** At seeding or on request: check the target folder first (seeding takes the numeric suffix; a request stops and proposes it), move `<old>/` to `<new>/`, then `<old>.md` to `<new>.md`. Role-named files need no change, so no link is edited. Nothing is overwritten; on failure the skill stops and says what moved. Old builds and the old hand-in export stay in the folder as previous outputs, named to the user with a rebuild offered. The only half-state, `<new>/<old>.md`, is what the folder-name error (D8) names. How the move is done safely on each shell is D23.

**D6 — Build definitions stay beside the proposal.** Publish looks only in the proposal's folder, and never-fall-back stays unconditional, so publish keeps not depending on the working directory or on `guidelines.md`. The gap this leaves (a definition at the location root or workspace root, silently unused) is closed by the check's `build-definition-unused` warning. How the check recognizes a definition is D21. A supervisor's faculty build is therefore copied into each proposal folder; README says so.

**D7 — Scripts run from the workspace root.** `api-keys.env`, `guidelines.md` and `bug-report/` stay there, and desktop-first-install's "User-side script constraints" is not touched. The silent risk (an agent `cd`s into a folder, no `guidelines.md` is found, defaults apply) is made visible twice: check's report gains `guidelines: beside the proposal | working directory | explicit | none (defaults)` (JSON: `"guidelines": "beside-proposal" | "working-directory" | "explicit" | "none"`), by position only so a relayed report leaks no path; and the placement test fails such a run (D17). publish keeps writing its `.gitignore` beside the proposal, now inside the folder.

**D8 — Check findings.**

| Rule id | Severity | When |
|---|---|---|
| `proposal-misplaced` (extended) | error | the proposal is not `<location>/<slug>/<slug>.md` relative to the workspace root (D17); message names that path and what may explain it: a working directory named like the proposal is read both ways (its folder: run from the workspace root; the workspace root: move the proposal into its folder), a root set by an explicit override file is named as such, and a folder named after the proposal that sits elsewhere adds that the check may have started outside the workspace root |
| `proposal-folder-mismatch` (new) | error | the proposal sits in a folder directly in the location whose name differs from its stem; names both; `proposal-misplaced` is then not reported |
| `companion-orphaned` (redefined) | warning | role files in a slug-shaped non-proposal folder (D19); family-shaped files and `img/` at the location root. D21 extends the scan |
| `build-definition-unused` (new) | warning | a build definition at the location root or the workspace root |

Plus the guidelines position line. No legacy-name rule. The stale-figure-link half of `companion-orphaned` is dropped, because figure names no longer carry a slug.

**D9 — Troubleshooting.** collect looks companions up by exact role name in `proposal.parent` (`notes.md` for the Log excerpt, `review.md`, `feedback.md`) and inventories them under those names; the build-definition lines are unchanged. Redaction keys on the proposal's stem, plus its folder's name where that differs and the folder is not the working directory (the half-finished rename `<new>/<old>.md`), so `<slug>/<slug>.md` reads `<proposal>/<proposal>.md` and `<slug>/review.md` reads `<proposal>/review.md`. Below `full` the same redaction covers the notes file's Log excerpt, and nothing of the notes file but its Log section is ever stored (decision log, 2026-10-15). `bug-report/` stays at the workspace root, and `bug-report` is a reserved folder name. The reduced reproduction is a workspace of its own: `bug-report/repro/input/input.md`, its command run from `bug-report/repro/` (decision log, 2026-10-15).

**D10 — Fixtures in workspace shape.** Every proposal fixture becomes `tests/fixtures/<fixture>/<slug>/<slug>.md` with role-named companions, its `expected.json` staying at the fixture root (the workspace root, never staged) and recalibrated against `check.py`. w07 becomes `proposals/<slug>/<slug>.md`. w13 is rebuilt as the orphan workspace the testing-harness delta describes (a folder without its proposal, a slug-named dump at the root, a flat proposal at the root, a root build definition); w14 and w15 move into folders; w15's notes file gets the five headings it needs to count as a proposal folder. The import-source PDFs of f03, f09, f11 and f16 stay outside the proposal folder, renamed `submission.pdf` at their fixture's root: inside the folder under `<slug>.pdf` they would read as current builds, and f16's two embedded images would satisfy the publish verdicts with no build at all; a root `submission.pdf` names no slug, so the check ignores it and no oracle changes. Every walker resolves proposals through one shared helper (D25), which reads `*/<dir>/<dir>.md` and `*/proposals/<dir>/<dir>.md`; the "exactly one proposal per fixture" rule stays.

**D11 — Pandoc fix and changelog.** `pandoc_command()` adds `"--resource-path", str(proposal.parent)` to its base list (all pandoc tiers, the typst intermediate included, which is harmless), and `run()` relays the `[WARNING]` lines of a successful run to stderr. pandoc splits `--resource-path` on the platform's path-list separator (`:` on POSIX, `;` on Windows), so when the folder's absolute path contains `os.pathsep`, `pandoc_command()` leaves the flag out and `build()` runs pandoc with the proposal's folder as working directory, where pandoc's default resource path finds `img/`; every other path in the command is absolute. Unit tests cover both branches. On the typst tier a missing figure fails the build, and the failure message already carries typst's stderr naming the file. `scripts/ci_typst_build.sh` and its drift guard follow the base list.

**Changelog:** the proposal carries one `Changelog:` line, because `openspec/config.yaml` asks for exactly one; it is the Breaking line under *Changed*. At archive, a second entry under *Fixed*, linked to the same archive folder as tighten-proposal-family did with three entries, reads exactly:

> proposal-publish embeds figures in LaTeX PDFs and Word documents whatever directory it runs from, and passes pandoc's warnings through on a successful build.

*Why not one combined line:* the fix also repairs existing `[paths] proposals` workspaces independently of the layout, so it is a patch-level fact a reader looks for under *Fixed*; folding it into a Breaking line would hide it.

**D12 — Six flows on the dev runner.** Subscription only, $0, one run at a time, `--model haiku` then `--model sonnet`, after the L0 gates:

| Flow | Scenario | Judged by |
|---|---|---|
| ideate from scratch | `ideate_from_scratch` (new, no fixture; three turns on one session: preamble answers without a topic, then a topic phrase, then a working title whose slug differs plus "enough") | from the recorded tool calls: `idea/notes.md` written in turn 1, moved to a provisional folder before the seed is written, never written fresh under the final slug; end state: seed verdict, one proposal folder with a five-heading `notes.md`, no `idea`/provisional leftover, family-only |
| write rename on request | `write_rename_family` (w14 in folders) | family-renamed, family-only, check over the result |
| review writes `review.md` | `review_converge` (w09 in folders: reads and overwrites `review.md`) | existing review verdicts, review found at `<slug>/review.md` |
| import creates folder with `img/` | `import_figures` (new: f16's `submission.pdf` staged alone through a `sources` key, D24; the request asks for the figures to be extracted) | folder + `notes.md`; exactly two figure references, each a resolved `img/<name>` link without slug prefix or a page-referenced TODO marker, at least one resolved; untested when the runner finds no extraction tool (`pdfimages`) on the run's PATH |
| publish with figures | `publish_figures_typst` (new, Q7: f16 in folders, nothing hidden); `publish_figures_latex`, `publish_figures_docx` (new: f16 in folders; typst — and for docx every LaTeX engine — hidden; the request says to install nothing) | tier evidence (for typst a `built via typst` line and `<slug>.typ` present; a `built via pdflatex/xelatex/lualatex` line, `<slug>.tex` present and no new `<slug>.typ`; for docx `built via pandoc` and no new PDF), and the output in the folder, added or changed by the run, embeds both figures (`word/media/*` count, `/Subtype /Image` count) |
| lit-search kept file | `litsearch_keep` (new: w03, request asks to keep the candidate list) | kept `<label>.<ext>` in the folder, family-only with keeping licensed |

Tool hiding is a new `hide` scenario key backed by its own helper (Linux only, a runner failure elsewhere), built like the install probe's symlinked PATH but leaving `versioned_python_path` and the install-probe scenarios unchanged. The host initializes its shell from the user's profile, and a login shell reads the system profile, which on Arch-like systems appends `/usr/bin` — where typst, the LaTeX engines and pandoc all live on the maintainer's machine. The runner therefore checks before the run, with a login shell under the run's environment, that no hidden tool resolves, and reports the run untested otherwise; the tier evidence in the verdicts is the guard that holds even if a hidden tool is reached another way, and a build through the wrong tier is reported untested rather than as a skill failure. If the pre-check shows the leak on the maintainer's machine, the LaTeX and DOCX runs are recorded untested there with the pre-check's finding (Q7, answered (a)): the L0 figure test builds both tiers for real from another working directory, the manual smoke (6.5) repeats that outside the repository, and `publish_figures_typst` evidences on both models that the agent publishes the folder's proposal from the workspace root. Beyond the six flows, `supervise_ready` stages f28's proposal flat at the workspace root (D22) and runs once, on sonnet only, since README records that haiku does not pick up the supervise skill. Each dev run's outcome is recorded in tasks.md; a failure is triaged as tooling first, then skill prose (memory: verify tooling before blaming models).

**D13 — One change, clear ownership.** One OpenSpec change, `adopt-proposal-folders`, built on a branch off `develop` and released whole. It MODIFIES "Users never work in this repository" now that add-setup-readiness-guide is archived. It does not modify any requirement desktop-first-install owns. Checked for contradictions: "User-side script constraints" says commands run from the agent's working directory "where the user's material lives" — still true of the workspace root, which holds the folders — and that a skill whose script depends on the working directory names that stake beside its script-location fallback; check.py, which ships in six skills (check, import, reverse, supervise, troubleshoot, write), gains such a dependence (D17), so each of the six fallback paragraphs states that the command runs from the workspace root because placement and orphan findings are measured from there, which complies with the owned requirement without modifying it. "Install identified from workspace evidence" reads the lock record and hashes, unaffected. Its README/walkthrough requirements describe installing and starting, not file names. Its install probe's `versioned_python_path` is left unchanged (D12). None contradicts folders, so no question is raised there. README text edits (the notes-file sentence, the folder-layout paragraph) touch prose those requirements do not pin.

### Derived decisions

**D14 — Ideate's folder exists from the first exchange.** "At once" (D4) is read as: when a session starts that resumes no earlier one. A session abandoned after one exchange therefore leaves `idea/notes.md` with the preamble facts, which is the "Nothing to seed" state the spec already accepts. A provisional rename that fails does not end the session: ideate keeps the current folder, says so in one line, and retries at seeding (serves D4/D5; the seeding rename itself still stops on failure as D5 says).

**D15 — A harvest record shelters its folder** (serves D2/D8; see Q1). proposal-reverse writes `harvest.md` and stops for inspection before any proposal or notes file exists. Under the literal decision a harvest-only folder would be invisible yet warned as "role files in a folder without x.md or notes.md", reversing today's "Harvest awaiting inspection" behaviour. The draft adds `harvest.md` to the proposal-folder test.

**D16 — The slug is a reserved label.** A kept file named `<slug>.yaml` would read as a file that leaves the folder; reserving the slug keeps "handle = leaves, role/label = stays" unambiguous.

**D17 — The placement root is the working directory** (serves D7/D8). Today the root is the governing file's directory. With folders, chain position 1 ("beside the proposal") is inside the folder, so that rule would report every proposal with a folder-level `guidelines.md` as misplaced at a nonsensical path. The root is now the directory of an explicitly passed override file, else the working directory — the rule D7 already states. Both the root and the proposal path are resolved before they are compared. A run started inside the proposal's folder fails the placement test with a message saying the check runs from the workspace root. The test applies whether or not `[paths]` is set, and the location-root, workspace-root and build-definition scans are measured from the same root. Consequence for this repository: every caller must run the check the way a user's agent does — `claude_runner.run_check`/`run_check_json` with `cwd=ws`, the Inspect sandbox from the workspace root with the proposal path relative to it (since the review of groups 4–6 the sandbox's root is the workspace root, so the agent's own checks run there too; decision log), `tests/helpers.run_check` under `contextlib.chdir(<workspace root>)` with a `write_proposal(root, slug, text)` helper replacing the flat `tmp_path` writes — which group 1 of the tasks does before any behaviour changes, and the testing-harness delta pins ("Check run from the staged workspace's root").

**D18 — Scenario names survive.** OpenSpec 1.14.1 refuses a MODIFIED block that drops a scenario. Obsolete scenarios therefore keep their names with bodies rewritten to the folder behaviour, and some names now read historically: "Unset key preserves the flat layout", "Flat workspace unchanged", "Stale figure link with/without a resolvable old slug", "Handout left behind by a rename" (which now passes). The bodies are authoritative. Shedding the names is not done without a deliberate baseline entry: the gate's sanctioned route is REMOVED plus an ADDED requirement under a new name, which exceeds 500 characters for each of these requirements and so needs its length recorded by hand under `changes.adopt-proposal-folders` in `openspec/long-requirements.json` (`validate_specs.py`: "record N … by hand"). Whether that is worth it was Q6, answered (a): the names stay, and shedding them is a follow-up.

**D19 — What makes a non-proposal folder reportable** (serves D2/D8; see Q2). Only unambiguous companions: `review.md`, `feedback.md`, `<dir>.handout.md`. `img/`, kept files, built outputs and a `notes.md` without the headings never make a folder reportable, so a user's `website/img/` or `meetings/notes.md` stays invisible as D2 requires.

**D20 — Requirement lengths.** Every MODIFIED requirement stays at or under its baseline, every ADDED one under 500 (measured with `uv run poe specs`). After archive, `python3 scripts/validate_specs.py --update-baseline` records the shorter entries.

**D21 — What the check lists and opens** (serves D6/D8; see Q5). Additions to the binding D8 that the draft made, kept apart so they can be weighed:
- *The workspace root is scanned for companions too*, not only the location root. Forced by the retained skill-check scenario "Dump at the workspace root", which OpenSpec does not let this change drop (D18).
- *A proposal folder moved into another* (`<a>/<b>/` holding `<b>.md`, `notes.md` or `harvest.md`) is a `companion-orphaned` warning. A folder move onto a name that appeared after the target test nests the folder instead of failing (D23); without this finding the nested proposal would vanish from every listing.
- *A second proposal inside a folder* is a warning only when it opens with the proposal frame check.py already parses (a leading `# ` title followed by an emphasized subtitle paragraph) and ends in a metadata block. The metadata block alone would also match a kept reading list such as w15's, which deliberately ends in one.
- *Recognizing a build definition at a root opens recipe files.* A warning on every `Makefile` at a project root would be noise, so the check applies publish's own recognition, target test included; the recipe-name constants stay mirrored from publish.py under the existing pin test.

The check therefore lists the proposal's folder and its subfolders, the location root, the workspace root and the location's slug-shaped folders one level deep; it opens a file only for the frame and metadata-block tests, the notes-headings test and the recipe-target test. It lists none of them while the placement error stands: a proposal folder that does not sit directly in the location means a misplaced proposal or a run started somewhere other than the workspace root, and in the second case the roots it would list are another directory's (a parent's sibling workspaces). The scans follow once placement is fixed.

**D22 — A submission outside a folder is a source** (serves D1/D2). A professor saves a student's file wherever they like, usually at the workspace root. supervise's "already standard format, use it as-is" path would then work on a proposal outside a folder, which D1 forbids. Every submission outside a proposal folder, a standard-format `.md` included, is therefore a source document: normalization writes `<slug>/<slug>.md` and leaves the original byte-identical. The original then draws the check's orphan warning ("a file you placed there on purpose can be left as it is"); moving it instead would manage the professor's files, which "Raw submission intake and normalization" rules out ("retention and deletion stay manual"). guidance-model's rule is worded "SHALL NOT treat a file outside a proposal folder as a proposal" so reading a source stays allowed.

**D23 — A folder move that cannot nest** (serves D5). `mv old new` (POSIX, Git Bash) and PowerShell `Move-Item` move `old` *into* `new` when `new` exists, which overwrites nothing and so would pass a naive "nothing overwritten" rule. The shared block therefore prescribes: test that the target is absent; move; then verify that `<new>/` holds the expected file and that no `<new>/<old>/` exists. On PowerShell prefer `Rename-Item`, which refuses an existing target. Never `cd` into a proposal folder (also D7). On Windows and synced folders a move fails while a file inside is open (the PDF just built, a sync in progress): name the open file when the error does and offer a retry. The check backs this up (D21). All group-7 runs are Claude on Linux, so a run on another host and shell is a backlog item (tasks 8.1).

**D24 — Staging keys** (serves D12). `stage()` copies the fixture tree minus `expected.json` and minus `submission.pdf`, and `staged_files()` mirrors it. A new `sources` key maps workspace names to fixture-relative files and stages only those: `import_figures` stages `submission.pdf`, and `supervise_ready` stages f28's `<slug>/<slug>.md` as `ci-repair-agent-configurations.md` at the workspace root, as its request already says the professor saved it.

**D25 — Implementation order in green steps** (serves D10/D17). The vocabulary is bound at import time across the suite, and fixture paths are read at import time, so a naive order leaves `uv run poe test` red for four groups. The tasks therefore run: layout-agnostic groundwork first (callers from the workspace root, one fixture-path helper, walkers that read both layouts, guards), green; then the scripts that do not depend on the corpus, green; then the layout switch as one group (check vocabulary, adapters, block table, fixture moves, oracles, staging), red only between its vocabulary task and its fixture task, for a named list of corpus readers; then prose, harness and gates, each green. The change is committed once when complete (8.2).

## Risks / Trade-offs

- **Old installs keep writing flat files** (main is the release channel). → The Breaking changelog entry; troubleshoot's stale-install rung answers first; an updated install reports a flat proposal as `proposal-misplaced` when it is named and as `companion-orphaned` when another proposal is checked.
- **An agent runs a script from inside a folder.** → Placement error with a "run from the workspace root" message, plus the guidelines line saying none governed. The block and the six fallback paragraphs state that scripts run from the workspace root.
- **Callers that are not at the workspace root.** Every test and runner path that runs the check (about 84 in-process callers, two dev-runner helpers, the Inspect sandbox) would gain a `proposal-misplaced` error, lose the fixture's `guidelines.md`, and scan the repository root for orphans, so verdicts would fail or pass vacuously. → Group 1 moves every caller to the workspace root before the check changes, and L0 tests pin each runner's working directory.
- **Collection-time breakage.** Renamed vocabulary constants and moved fixture files fail the import of `helpers`, `l1_checks` and `skill_evals`, which takes most of the suite down at once. → D25's order; the vocabulary, its adapters and the fixture moves land in one group.
- **Corpus walkers that silently match nothing** after the move (the typst CI job, the anonymity guard, the identifier guard). → One walker, a count guard against the oracle count in the CI script, and a test that every walker yields that count.
- **The notes-headings test is strict.** A student who deletes a heading from an unseeded idea's notes makes the folder invisible. → Only unseeded ideas depend on it, and every skill writes the five headings; accepted.
- **Rename half-states.** `<new>/<old>.md` after a failed file rename, `<new>/<old>/` after a move onto a folder that appeared meanwhile. → `proposal-folder-mismatch` names both names; the nested-folder warning (D21); the skill's verification and chat say what moved (D23).
- **Windows and synced folders.** A folder move fails while a file in it is open. → D23's error handling; ideate's provisional rename is non-fatal (D14); a non-Claude, non-Linux run is a backlog item, because decision 12 limits the dev runs to Claude.
- **Tool hiding leaks.** A profile-initialized shell can reach a hidden typst, so a "LaTeX" run could build through typst and pass. → Pre-run login-shell check, tier evidence in both publish verdicts, outputs that must be added or changed by the run, and a request that says to install nothing; where the check finds a leak, the two runs are recorded untested and the L0 figure test plus the typst run carry the flow (Q7 (a)).
- **Large mechanical diff** (about 50 fixture folders, oracles, 11 SKILL.md, 5 vendored copies, about 140 test call sites). → Fixture moves with `git mv`, oracles recalibrated by running `check.py`, never by hand; the drift check and the oracle test gate the rest.
- **Review-currency and family verdicts silently grading the wrong file** after the listing change. → Unit tests on crafted folder workspaces for `select_draft`, the family verdicts, the negative verdicts (paper foundation, early stop) and `review_path` before any listing is changed; exact basename matching for role files.
- **Inspect wiring changed without a run.** → Each touched Inspect task runs once on `mockllm/model` with the local sandbox and `--log-dir logs/scratch` ($0, no model), as `test_cache_probe.py` already does; stub-sandbox unit tests for the listings and the check's working directory.
- **Routing comparability.** `routing.py` stages proposal files; folder staging is a staging change. → The next routing run declares a conditions change ("A conditions change invalidates comparison").
- **Body size.** The block grows every body equally; the 2 × median cap is unaffected. → `test_skill_frontmatter.py` stays in the gate.
- **README demo.** Its curated session lines name `drift-alert-validity.md` and `.pdf`, which remain the files' names; the demo is session-derived and is not edited.
- **Parallel branches.** `add-coverage-campaign` and `add-evidence-beads` are proposed off develop and may touch tests or fixtures. → Whichever lands second rebases; fixture paths are the likely conflict, and the fixture-path helper of group 1 narrows it to one module.
- **Haiku may not follow the folder discipline.** → The six dev flows run on both models; a haiku-only failure is recorded, not papered over, and the README's model notes are updated only on evidence.

## Effort

About 6–8 working sessions:

- groundwork (group 1: about 140 call sites, walkers, guards): 1;
- publish and collect (group 2): 0.5;
- the layout switch (group 3: check, adapters, block, about 50 fixtures, oracles): 2;
- SKILL.md prose, pins and docs (group 4): 1;
- harness verdicts, scenarios and the offline Inspect pass (group 5): 1–1.5;
- gates: 0.25;
- dev runs (ten scenarios on two models plus one supervise run, at most 21 runs and 17 where the LaTeX and DOCX pairs are recorded untested, one at a time, plus triage): 1–1.5.

The caller migration that D17 forces is about one session of that; the folder-name test alone would need most of it too, because flat `tmp_path` proposals fail any folder test.

## Migration Plan

**Users.** No migration feature exists (D1). The maintainer moves their own workspace by hand, per proposal `x`, from the workspace root:

1. `mkdir x` (in `[paths] proposals` when set), then move `x.md`, `x.pdf`, `x.typ`, `x.tex`, `x.docx` into it.
2. Rename into the folder: `x.notes.md → x/notes.md`, `x-review.md → x/review.md`, `x-feedback.md → x/feedback.md`, `x.harvest.md → x/harvest.md`, `x-handout.md → x/x.handout.md`, `x.<label>.<ext> → x/<label>.<ext>`.
3. Move `img/x-<name>.<ext>` to `x/img/<name>.<ext>` and change the links in `x.md` (and `notes.md`) from `img/x-<name>` to `img/<name>`.
4. `ideation.notes.md` → `idea/notes.md`.
5. A build definition sitting beside the proposals → a copy in each folder that uses it.
6. Run `check.py x/x.md` from the workspace root for each proposal; zero `proposal-misplaced`, `proposal-folder-mismatch`, `companion-orphaned` and `build-definition-unused` findings means done.

**Repository.** Implement on a branch off `develop` and merge as one change; `poe release` later fast-forwards `main`. Rollback is the previous release; workspace moves are reversible by hand.

**Archive.** Copy the Breaking line under *Changed* and add the *Fixed* entries exactly as D11 and the decision log of 2026-10-15 draft them, update the `proposal-file-format` Purpose line ("flat multi-proposal user workspace") in the main spec, run `--update-baseline`, and `python3 scripts/changelog.py check`.

## Questions before implementation

All seven were answered by the maintainer on 2026-10-14, each with the recommended option; each question ends with its answer, and the decision log says where it landed.

**Q1 — Does a harvest record shelter a folder?** The decisions list `<dir>.md` and `notes.md` only.
- (a) Yes, `harvest.md` shelters (drafted, D15). Today's behaviour for a reverse run waiting for inspection survives; no reverse prose change.
- (b) No; proposal-reverse writes `notes.md` together with `harvest.md`. Changes reverse's step order and a reverse spec requirement.
- (c) No, as decided; a harvest-only folder is warned. Reverses an existing scenario.
- *Recommendation:* (a), the smallest change that keeps a shipped behaviour.
- *Answer:* (a) — `harvest.md` alone makes a proposal folder.

**Q2 — Which files make a non-proposal folder reportable?**
- (a) Only `review.md`, `feedback.md`, `<dir>.handout.md` (drafted, D19).
- (b) Any role file, `img/` and a headings-less `notes.md` included, as D8's wording reads literally. Conflicts with D2's "other folders are invisible" for `website/img/` or `meetings/notes.md`.
- *Recommendation:* (a).
- *Answer:* (a) — only `review.md`, `feedback.md` and `<dir>.handout.md` make a non-proposal slug-shaped folder reportable.

**Q3 — A `guidelines.md` inside a proposal folder.** Chain position 1 now means exactly this, and the prose-driven skills read `guidelines.md` from the root, so check and the other skills could judge one proposal by different rules.
- (a) Honour it as chain position 1, made visible only by the guidelines line (drafted).
- (b) Honour it and warn (`guidelines-beside-proposal`), one more ADDED requirement.
- (c) Drop chain position 1: explicit, else working directory.
- *Recommendation:* (a) for this change; (b) as a cheap follow-up if it shows up in a report. (c) contradicts the four positions D7 names.
- *Answer:* (a) — honoured as chain position 1 and visible only through the guidelines line; (b) stays a follow-up.

**Q4 — Rule id for the folder-name error.** Drafted as `proposal-folder-mismatch`; any stable id works, but it lands in fixtures' oracles and in collect's relayed output.
- *Answer:* `proposal-folder-mismatch`.

**Q5 — Does the check report a second proposal inside a folder, and how is it recognized?** Not in decision 8 (D21).
- (a) Report it when the file opens with the proposal frame (`# ` title plus emphasized subtitle) and ends in a metadata block (drafted). A kept reading list that ends in a metadata block, like w15's, is not reported.
- (b) Drop the case; only placement and folder-name errors guard the folder.
- (c) Report any slug-named markdown that ends in a metadata block. Warns on w15's own kept file.
- *Recommendation:* (a): it catches a draft written beside its seed inside the folder, which family-only also judges in the dev runs, at the cost of one frame parse the check already has.
- *Answer:* (a) — reported when the file opens with a `# ` title followed by an emphasized subtitle and ends in a metadata block.

**Q6 — Shed the scenario names that read historically?** D18.
- (a) Keep the names with rewritten bodies (drafted).
- (b) Replace the four affected requirements by REMOVED plus ADDED under new names, recording each new requirement's length by hand under `changes.adopt-proposal-folders` in `openspec/long-requirements.json`.
- *Recommendation:* (a): the bodies are authoritative, and four hand-recorded baseline entries add length budget the ratchet exists to withhold; (b) is a clean follow-up once the layout has settled.
- *Answer:* (a) — the historical scenario names stay with rewritten bodies; (b) is a follow-up.

**Q7 — Publish dev runs when PATH hiding leaks.** Decision 12 asks for the LaTeX and Word tiers on the dev runner, but on a machine whose system profile re-adds `/usr/bin` the hidden tools come back (D12). Task 5.3's pre-check settles whether that happens here, at $0, before any run.
- (a) Record both publish runs as untested on such a machine and rely on the L0 figure test, which builds both tiers from another working directory through the shipped entry point, plus the manual smoke (6.5); run the figure fixture once on the typst tier instead, to evidence that the agent publishes the folder's proposal from the workspace root.
- (b) Hide the tools with a mount namespace (`bwrap` or `unshare`, binding an empty file over each tool), Linux only, as one more harness dependency.
- (c) Run the two scenarios in a container image carrying pandoc and LaTeX but no typst.
- *Recommendation:* (a): the defect and its fix live in `publish.py`, which L0 builds on both tiers for real; what a dev run adds is the agent's behaviour, which does not depend on the tier. (b) if tier-specific agent evidence matters to you.
- *Answer:* (a) — where the pre-check finds a hidden tool reachable, the LaTeX and DOCX dev runs are recorded untested; the L0 figure test builds both tiers for real from another working directory; one typst publish dev run, `publish_figures_typst`, covers the agent's behaviour.

## Decision log

**2026-10-14 — critic review of the first draft.** Applied:
- caller working directory under D17: D17, group 1, testing-harness "Check run from the staged workspace's root";
- the three corpus walkers and the CI count guard: D10, D25, testing-harness "Corpus walkers cover every proposal fixture";
- the import-source PDFs kept out of the folder, and outputs that must be added or changed by the run: D10, D12, D24;
- three-turn from-scratch ideation judged on recorded moves: D12;
- the D8 additions moved into D21, with Q5;
- the import verdict that needs a resolved figure and an extraction tool: D12;
- slug-shaped defined: Terms, proposal-file-format scenario;
- the `.gitignore` in the folder: skill-publish MODIFIED "Outputs and workspace hygiene";
- "workspace `guidelines.md`" in guidance-model;
- D18 reworded, with Q6;
- the *Fixed* sentence drafted: D11;
- `hide` kept apart from `versioned_python_path`: D12, D13;
- the proposal's orphan bullet narrowed;
- the failed provisional rename: D14 and the skill-ideate scenario;
- notes headings read only to classify: D2 and the proposal-file-format scenario;
- green steps instead of a red stretch: D25;
- fixture-path literals behind one helper with a guard: D10, group 1;
- the second proposal recognized by its frame: D21, Q5;
- submissions outside a folder as sources: D22, skill-supervise MODIFIED "Raw submission intake and normalization";
- publish tier evidence and the hidden-tool pre-check: D12;
- recursive listings and an offline Inspect pass: Risks, group 5;
- safe folder moves and nested-folder detection: D23, D21;
- exact basename matching for role files: D3;
- typst's missing-figure failure and the path-list separator: D11, skill-publish scenarios;
- the verifier brief and the six fallback paragraphs: D13, group 4.

Rejected or narrowed:
- *Making placement independent of the working directory* (the folder-name test always, the location test only when `[paths]` is set), offered as an alternative to migrating the callers. Rejected: D7 already fixes the workspace root as the working directory, and a path-derived rule cannot tell a flat proposal at the root from a half-finished rename, so its message could not name the right target. The flat `tmp_path` writers would need migrating under either rule.
- *A local commit after each step.* Narrowed: each step ends green and is a safe stopping point, but the change is committed once when complete (AGENTS.md: commit per completed OpenSpec change).
- *A scratch HOME for the publish scenarios.* Not adopted: it skips the user's profile but not the system profile a login shell reads, which is what puts `/usr/bin` back on PATH. The login-shell pre-check and the tier evidence cover the leak whatever its source; what to do if it shows up is Q7.

**2026-10-14 — maintainer answers to Q1–Q7** (session chat; "Accept all" for Q1–Q6, "Untested + L0" for Q7, both the recommended options; the release stays held, which changes no plan). Every answer is the recommended option:
- Q1 (a), `harvest.md` alone makes a proposal folder: as drafted in D2, D15, the proposal-file-format and skill-check deltas, and task 3.1.
- Q2 (a), only `review.md`, `feedback.md` and `<dir>.handout.md` make a non-proposal slug-shaped folder reportable: as drafted in D19 and the skill-check delta.
- Q3 (a), a `guidelines.md` inside a proposal folder is honoured as chain position 1 and visible only through the guidelines line: as drafted in D7 and the skill-check delta; (b) goes to the backlog (8.1).
- Q4, the rule id is `proposal-folder-mismatch`: as drafted in D8 and the skill-check delta.
- Q5 (a), a second proposal in a folder is reported when it opens with a `# ` title followed by an emphasized subtitle and ends in a metadata block: as drafted in D21 and the skill-check delta.
- Q6 (a), the historical scenario names stay with rewritten bodies: as drafted in D18; (b) goes to the backlog (8.1).
- Q7 (a): the one answer that changes the plan. A third figure scenario, `publish_figures_typst`, hides nothing and evidences on both models that the agent publishes the folder's proposal from the workspace root (D12; testing-harness "Folder-layout dev scenarios" gains the typst tier and the scenario "Publish on the typst tier"; tasks 5.1, 5.3, 7.5). The LaTeX and DOCX scenarios keep their hiding and pre-check, and where the pre-check finds a hidden tool reachable they are recorded untested; the L0 figure test of 2.1 and the smoke of 6.5 carry those tiers. Proposal and Effort follow the scenario count.

**2026-10-14 — review of groups 0–3.** Applied, each test-first:
- D9's redaction sentence corrected to what collect.py and task 2.3 do: the stem, plus the folder's name where it differs.
- The misplacement message (D8): a working directory named like the proposal is read both ways, since a flat workspace from before the layout looks exactly like a run from inside the folder, and sending it one level up would make it pass as a proposal folder; a root set by an explicit override file is named as such; a folder named after the proposal that sits elsewhere names a start outside the workspace root as a possible cause.
- The scans of D21 skipped while the placement error stands: started above the workspace root, the check listed the parent directory and warned about sibling workspaces. skill-check: "Orphaned companions reported as a warning" and "Unused build definitions reported" say so, with the scenario "Run started above the workspace root".
- A folder name that is not valid UTF-8 printed with its undecodable bytes replaced: the folder-name error and the nested-folder warning print it, and no listing filters it.
- publish's hand-in hint: rename for sending but keep the `.handout.md` ending, because a slug-shaped `<name>.md` in the folder carries the proposal frame and reads as a second proposal (Q5).
- Draft selection (testing-harness: Notes files excluded from draft selection): a candidate is `<dir>/<dir>.md`, a file at the workspace root, or another file in a folder whose text carries the proposal frame, so a kept `reading-list.md` never wins over the proposal it sorts before, and a seed written under the wrong name is still seen by the negative verdicts.
- `scripts/ci_typst_build.sh` pinned to LF: a test runs it under sh on the Windows lane.
- w13's test again pins exactly its four leftovers.
- Task 5.4 opens with a red test that every workspace path an Inspect prompt or scorer names is staged.

**2026-10-14 — harness, group 5.** Decided while implementing D12, D22 and D24, each test-first:
- The pre-check runs alone through `--preflight-only`, which on Claude now checks a scenario's hidden and required tools under the environment the run would get and starts no host (exit 0 ready, 3 not ready). Copilot's option of that name is unchanged; on Claude a scenario without such tools is a usage error. Task 5.3 asked for the pre-check alone without naming an entry point, and an option the operator can rerun before 7.5 beats a one-off script.
- The login shell of the check runs interactive as well (`$SHELL -l -i`), so it also reads the rc files a host's shell snapshot reads; D12's "login shell" alone would miss a PATH an rc file sets. On this machine the plain login shell already leaks: `/etc/profile` appends `/usr/bin` (`append_path '/usr/bin'`), so `publish_figures_latex` and `publish_figures_docx` read not ready and 7.5 records them untested (Q7 (a)).
- A required tool (`requires`) is checked with the hidden ones: `import_figures` needs `pdfimages` or `mutool` (D12), and each publish tier needs its own tools, so a machine without typst cannot record a typst run as a skill failure.
- `verdict_no_orphans` fails on `proposal-folder-mismatch` too: "Proposal-family coverage" judges the rename by the check reporting neither an orphan warning nor a folder-name error.
- Role files in both runners count only in a proposal folder, classified by `check.family_members` over the recursive listing, so a feedback outside one does not satisfy the presence verdict ("Feedback found in the proposal's folder").
- The Inspect path constants are derived from the fixtures through the fixture-path helper rather than restated, and `supervise_ready` stages its proposal at the root there too. The staged-path test was red on 17 tasks, not 15: `customize_override` read its proposal by a flat literal, and `reverse_from_harvest` named `W06_HARVEST`. The persona dialogues' `rm -f ws/*.md` setup no longer emptied a folder-staged w03, so it became `find ws -mindepth 1 -delete`.
- The routing rig stages a named proposal with its folder, whether the sentence names the file or `<slug>/<slug>.md`, and `write-polish-collision` names the folder path, word for word with `write_repair_citations`; both are a conditions change the next routing run declares.

**2026-10-14 — gates, group 6.**
- A proposal file name that is not valid UTF-8 is printed through `_shown()`, like its folder's name since the review of groups 0–3: the report header `# Check: <name>`, the JSON `file` field and every message naming the checked proposal (the folder-name error, the misplacement error, the nested-folder and second-proposal warnings). Before, such a name ended the run in a `UnicodeEncodeError` traceback, on develop as well. The maintainer chose to fix it in this change ("Fix it here"); task 6.6, test-first. No spec delta: the check's requirements say what it reports, and a crash was never part of that.
- Incidental flat names in tests (a review verdict's label, verifier prompts, recorded host streams, a symbolic link's name) moved to folder names, so the retired-name grep of 6.4 finds only tests that assert an old name is not classified. The slug `ml-code-review` and the kept labels `peer-review.md`, `reading-notes.md` and `supervisor-feedback.md` match the grep's pattern without being retired names.
- Found by the smoke of 6.5 and left open for the maintainer (still open after the review of groups 4–6): collect stores the notes file's Log section verbatim at every disclosure level (and the whole notes file when it has no Log heading), so a Log line naming the proposal carries its slug into a `minimal` bundle. This predates the change, and "Proposal handle redacted in every path" covers the report and the stored script outputs, not this artifact. The fix that would close it (the handle replaced in the Log excerpt below `full`, nothing but the Log section stored) changes skill-troubleshoot behaviour this change does not touch; the choice is to fix it here or to put it on the backlog (8.1).

**2026-10-15 — review of groups 4–6.** Thirteen findings, each verified and applied test-first (task 6.7); none rejected:
- The shared block states the collision rule for every new proposal: a proposal folder is never named `bug-report` or `img` (the reserved names are a proposal folder's, not every folder's, since the block itself names `img/`, the root's `bug-report/` and `.agents/skills/`), a new proposal's slug takes the numeric suffix when its folder exists or the name is reserved, and a new proposal never goes into another proposal's folder. Import, reverse and supervise said nothing of it, so two submissions on one topic would have shared a folder (proposal-file-format: Content-derived slug filenames).
- The provisional rename is suffixed when taken (skill-ideate: Provisional handle resolved at seeding), stated in the block.
- The rename's order follows proposal-file-format: move the folder, verify it (no `<new>/<old>/`, stop if there is one), then rename `<old>.md` when the folder holds one. An idea's folder holds none, so the old order made ideate's automatic renames fail on a file that cannot exist.
- The block says never to `cd` into a proposal folder, as D23 prescribes, not only never to run a script from one.
- ideate's impasse and resume sentences cover `idea-2/` and on; check's placement relay puts the rerun into the handoff, so its pinned single run stands; supervise normalizes a revision into its earlier folder under that folder's name (skill-supervise: Resubmission intake, "under the same slug").
- collect redacts each name also in the form the check prints since 6.6: the check's replacement character had let the slug's readable part through at `minimal`, a leak 6.6 itself opened.
- Harness: `bug-report/` excluded from draft selection only as a first path component; from-scratch ideation accepts a provisional slug equal to the final one when the move came in an earlier turn, and says no seeding rename was exercised (the agent picks both slugs, so the scenario's premise is not guaranteed); the figure count comes from the staged proposal; the tier scenarios are refused on Codex and Copilot, whose tool output `tool_result_text` does not read; the routing report records its staging as it records its isolation, which implements the existing scenario "Staging changed between runs" without an operator's flag.
- The Inspect sandbox's root is the workspace. D17 moved the scorer's check to the workspace root, but the agent still worked one level above `ws/`, where every check it ran as the skill documents reported a misplaced proposal and found no workspace `guidelines.md`; Inspect's `bash` tool takes no working directory, so the fixture tree now lands at the root and the skill under `.claude/skills/<skill>/`, a hidden folder no listing reads, as a project-level install puts it. The dialogue tasks stage nothing rather than emptying w03, which also ends a projection regression of 5.4 (all five listed w03's proposal); the cache probe follows the agent's new system message. This changes the metered matrix's conditions: the next run is not comparable cell by cell with earlier logs, and it needs the maintainer's cost approval (8.1).

**2026-10-15 — maintainer answers after the review of groups 4–6** (session chat; each the recommended option where one was offered). Applied test-first:
- *AGENTS.md fixture rule* ("Apply this wording"): the "Fixtures are synthetic" rule states the workspace shape, the oracle at the fixture root and fixture files resolved through `harness/fixture_paths.py`, in the wording task 4.3 proposed. Applied by the orchestrator and verified here; 4.3 is closed.
- *Troubleshoot notes-log leak* ("Fix here"), left open by the gates of group 6. Below `full`, collect replaces the proposal's handle in the stored Log excerpt with the names `handle_names()` gives the stored script outputs (the stem, the folder's name where it differs, each also in the form the check prints when it is not valid UTF-8), and at every level it stores the notes file's Log section and nothing else. A notes file without a Log heading contributes nothing, and the report says so in one measured line. *Why nothing rather than a placeholder file:* what such a file holds is the idea itself (topic, decisions), which no level promises, `full` included, whose promise is the proposal text; a placeholder would be a file that carries no evidence, while the report line keeps the absence legible as a fact. The troubleshoot level table tells the user that every level stores the Log section. skill-troubleshoot MODIFIED "Graded redaction with the most protective default" (1064 characters against its 1067: the title paragraph shortened to fit, its detail kept in the scenario "Structure level does not disclose the title"), with the scenarios "Notes log stored without the handle" and "Notes file without a Log section"; tasks 6.5 and 6.8. The leak predates the layout, as D11's figure fix does, so at archive it gets its own *Fixed* entry, drafted as: "proposal-troubleshoot's bug report no longer carries the proposal's name in the notes file's Log excerpt below the full level, and stores nothing of a notes file that has no Log section."
- *`verdict_publish`* (backlog candidate, fixed here). The verdict took one listing text, the folder's PDFs and its `.gitignore` together, so the `.gitignore` line `*.pdf` alone passed for a build. It now takes the non-empty files of the proposal's folder and the `.gitignore` text apart (AGENTS.md: the data shape is the contract), `publish_listing()` reads them through the shared workspace listing instead of a shell glob, and a `.gitignore` entry counts only as a whole line. No requirement names the Inspect verdict, so no delta; the projection is regenerated. Task 6.9.
- *Troubleshoot reproduction* (backlog candidate, fixed here). The reduced reproduction was `bug-report/repro/input.md`, which under D17 the check reports as `proposal-misplaced` from any working directory, so a seed for a wrong check finding reproduced the placement error instead; and "Reproduction seed only where reduction is possible" binds the seed to the fixture rules, which are now folder-shaped. The reproduction is a workspace of its own: the reduced file at `bug-report/repro/input/input.md`, `command.txt` beside `input/`, the command run from `bug-report/repro/`, and a copy of `guidelines.md` there only when the defect depends on it, since from that root the check no longer finds the user's. `input` is a fixed stand-in for the slug, so no slug derived from the real topic reaches the bundle. No requirement names the path, so no delta; the report's reproduction line, the issue template's Reproduction field and the harness's bug-report test paths follow, and the new pin `proposal-troubleshoot--repro-location` holds the sentence. Task 6.10.
- *Writing from scratch beside an unseeded `idea/`* (backlog candidate, not chosen): recorded under Skills in `docs/backlog.md`, citing this design (8.1).
