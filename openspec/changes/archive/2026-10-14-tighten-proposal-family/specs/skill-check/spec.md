## ADDED Requirements

### Requirement: Orphaned companions reported as a warning
The check SHALL list the directory that holds the checked proposal, including its `img/` folder. When the governing `guidelines.md` configures a proposal location, the check SHALL also list the workspace root.

A file is family-shaped when its name has one of the family shapes of proposal-file-format "Proposal family under one handle" under a slug of the form Content-derived slug filenames sets: lowercase ASCII, hyphen-separated. A slug is sheltered when a proposal, a notes file or a harvest record carrying it sits in the proposal location; a harvest record shelters an idea skill-reverse has not yet written, a notes file one that has not been seeded. A `-review` or `-feedback` markdown file whose base slug has no proposal and which ends in a metadata block is itself a proposal, for example `ml-code-review.md`; a file of another family shape carrying the base slug does not count as its proposal. The checked proposal is a proposal whatever its name. A `-handout` file is a companion by its suffix alone.

The check SHALL report a warning, under one stable rule identifier, for each of the following:

- each family-shaped file under an unsheltered slug that carries an unambiguous companion (a review, feedback, handout or figure) or, when the slug has at least two words as Content-derived slug filenames requires, at least two kept files;
- when a proposal location is configured, each family-shaped file at the workspace root, other than a proposal, whose slug is sheltered in the proposal location;
- each figure the checked proposal links under `img/` whose file name does not start with the proposal's own slug followed by `-`.

Built outputs (`.pdf`, `.typ`, `.tex`, `.docx`) SHALL NOT make a slug reportable on their own, SHALL be reported only together with a reportable slug's other files, and SHALL never be reported while a workspace build definition sits beside the proposal. The check SHALL never report any of these:

- `ideation.notes.md`;
- the workspace-level files, the troubleshooting captures and the installer-managed files of proposal-file-format "Working material stays out of the workspace";
- workspace build definitions;
- hidden files or folders, `.gitignore` files included;
- an `img/` file whose name resolves to no reportable slug.

The finding SHALL be a warning and SHALL NOT change the exit code. For this finding, the check SHALL open another file only to tell a proposal from a companion, and SHALL change nothing. The message SHALL name the file and the slug it carries. It SHALL also say that a rename which moved only part of the family is the usual cause, and that a file the user placed there on purpose can be left as it is. For a stale figure link, the message SHALL name the linked path and the proposal's own slug, and SHALL name the old slug only when it resolves against a family-shaped file present.

#### Scenario: Leftovers of a partial rename
- **WHEN** the directory holds `<new>.md` beside a kept file and a review under `<old>`, with no `<old>.md`, no `<old>.notes.md` and no `<old>.harvest.md`
- **THEN** the check reports one orphan warning per leftover file, each naming `<old>`, and the exit code is what the proposal's other findings make it

#### Scenario: Idea not yet seeded
- **WHEN** the directory holds `<idea>.notes.md` and `<idea>.reading-list.md` and no `<idea>.md`
- **THEN** no orphan warning names either file

#### Scenario: Harvest awaiting inspection
- **WHEN** the directory holds `<thesis>.harvest.md` written by a reverse run that stopped for inspection, and no `<thesis>.md`
- **THEN** no orphan warning names it

#### Scenario: Stale figure link with a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png` while its own slug is `<new>`, and a review `<old>-review.md` is present
- **THEN** the check reports an orphan warning for the link that names the linked path, `<new>` and `<old>`

#### Scenario: Stale figure link without a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png` while its own slug is `<new>`, and no other file carries `<old>`
- **THEN** the check reports an orphan warning for the link that names the linked path and `<new>`, and names no other slug

#### Scenario: Workspace, build and installer files ignored
- **WHEN** the directory holds `guidelines.md`, `api-keys.env`, `bug-report/`, `proposal-build.sh`, `faculty.typ`, `proposal.pdf`, `check-output.txt`, `.gitignore`, `.agents/skills/`, `skills-lock.json` and `ideation.notes.md`
- **THEN** none of them is reported

#### Scenario: Source documents and project files ignored
- **WHEN** the directory holds `submission.pdf`, `expose.docx`, `thesis.pdf`, `vite.config.ts`, `data.tar.gz` and `img/screenshot.png`, each the only file under its name
- **THEN** none of them is reported

#### Scenario: Proposal whose name ends like a companion
- **WHEN** `ml-code-review.md` ends in a metadata block and no `ml-code.md` exists beside it
- **THEN** it is treated as a proposal and is not reported

#### Scenario: Companion-shaped proposal beside a file under its base slug
- **WHEN** `ml-code-review.md` ends in a metadata block, no `ml-code.md` exists beside it, and `ml-code.pdf` or `ml-code.candidates.yaml` does
- **THEN** neither file is reported

#### Scenario: Tool files under a one-word name
- **WHEN** the directory holds a LaTeX build's `thesis.tex`, `thesis.pdf`, `thesis.synctex.gz` and `thesis.run.xml`, or a code repository's `tsconfig.app.json` and `tsconfig.spec.json`
- **THEN** none of them is reported

#### Scenario: Dump at the workspace root
- **WHEN** the governing `guidelines.md` sets the proposal location to `proposals/`, the proposal `<slug>.md` sits there, and `<slug>.candidates.yaml` sits at the workspace root
- **THEN** the check reports an orphan warning for the root file naming `<slug>`

#### Scenario: Read-only listing
- **WHEN** the check runs over a directory holding orphaned companions
- **THEN** every file in the directory is byte-identical afterwards and none was moved
