# Spec Delta

## ADDED Requirements

### Requirement: Proposal folder named by its slug
When the checked proposal sits in a folder directly inside the proposal location and the folder's name differs from the proposal's file name without `.md`, the check SHALL report an error under its own stable rule identifier, naming both, and SHALL say that a rename moves the folder and the proposal file together (proposal-file-format: A rename moves the whole family). The misplacement error SHALL NOT be reported for the same proposal.

#### Scenario: Rename that stopped halfway
- **WHEN** the checked proposal is `<new>/<old>.md` in the proposal location
- **THEN** the check reports one folder-name error naming `<new>` and `<old>`, and no misplacement error

#### Scenario: Matching names
- **WHEN** the checked proposal is `<slug>/<slug>.md` in the proposal location
- **THEN** neither the folder-name error nor the misplacement error is reported

### Requirement: Unused build definitions reported
The check SHALL report a warning under its own stable rule identifier for each workspace build definition at the root of the proposal location or at the workspace root, recognized as the publish step recognizes one, and none beside the misplacement error. The message SHALL name the file and SHALL say that the publish step looks for a build definition only in the proposal's folder, so this one is never used. The warning SHALL NOT change the exit code.

#### Scenario: Faculty build at the workspace root
- **WHEN** a `proposal-build.sh` sits at the workspace root and none sits in the checked proposal's folder
- **THEN** the check reports one unused-build-definition warning naming `proposal-build.sh`, and the exit code is the one the proposal's other findings give

#### Scenario: Unrelated recipe file at the root
- **WHEN** a `Makefile` without a `proposal-build` target sits at the workspace root
- **THEN** no unused-build-definition warning is reported

#### Scenario: Definition in the proposal's folder
- **WHEN** the only build definition sits in the checked proposal's folder
- **THEN** no unused-build-definition warning is reported

### Requirement: Governing override file named by position
The check's report SHALL state which override file governed the run by its position in the resolution chain — beside the proposal, the working directory, an explicit path, or none, so that defaults apply — in both output modes and whether or not any override applied. It SHALL NOT print the file's path, so a report relayed into a bug report carries no directory name.

#### Scenario: Run from the workspace root
- **WHEN** the check runs from the workspace root, which holds `guidelines.md`, over `<slug>/<slug>.md`
- **THEN** the report names the working directory as the governing position and prints no path for it

#### Scenario: Run from inside the proposal's folder
- **WHEN** the check runs with the proposal's folder as working directory and no `guidelines.md` lies in it
- **THEN** the report states that no override file governed the run and the defaults applied

#### Scenario: Structured output
- **WHEN** the check runs in its machine-readable output mode
- **THEN** the structured output carries the governing position, and no path

## MODIFIED Requirements

### Requirement: Override file resolution chain
The check SHALL resolve the workspace override file through a fixed chain: an explicitly passed path wins; otherwise a `guidelines.md` beside the proposal, in its folder; otherwise a `guidelines.md` in the working directory, which is the workspace root. The first file found governs the whole run — later chain positions are never consulted to fill in keys the found file lacks. The chain SHALL NOT search ancestor directories or any other location.

#### Scenario: Proposal in a configured subdirectory
- **WHEN** the workspace root holds `guidelines.md`, the proposal's folder lives in the configured proposal subdirectory, and the check runs from the root without an explicit override path
- **THEN** the root `guidelines.md` governs the run and its overrides are honored

#### Scenario: Flat workspace unchanged
- **WHEN** the proposal's folder sits directly in the workspace root, which holds `guidelines.md`, and the check runs from the root
- **THEN** the root `guidelines.md` governs, as it did when proposals sat beside it

#### Scenario: Both chain positions occupied
- **WHEN** a `guidelines.md` exists beside the proposal in its folder and a different one exists in the working directory
- **THEN** the one beside the proposal governs the whole run and the working-directory file is not consulted

#### Scenario: No override file anywhere
- **WHEN** neither position holds a `guidelines.md` and no explicit path is passed
- **THEN** pure defaults apply, and the report says that no override file governed the run

### Requirement: Proposal-location value validated, misplacement reported
The check SHALL validate a configured proposal-location value: it must be a string naming a relative directory inside the workspace — not absolute, not home-anchored, not escaping the root through parent references. An invalid value SHALL be reported as an error finding and the default SHALL apply for the rest of the run. An unknown key under the paths table SHALL be reported through the existing unknown-override-key error, never ignored.

When the checked proposal is not `<location>/<slug>/<slug>.md` relative to the workspace root — the directory of an explicitly passed override file, else the working directory — the check SHALL report an error naming that path, unless the folder-name error applies (requirement: Proposal folder named by its slug).

#### Scenario: Invalid proposal-location value
- **WHEN** the workspace sets the proposal-location path to an absolute path, a parent-escaping path, or a non-string
- **THEN** the check reports an error finding naming the constraint, and the default location applies for the rest of the run

#### Scenario: Unknown paths key
- **WHEN** the workspace sets a key under the paths table that does not resolve to an overridable leaf
- **THEN** the check reports it through the unknown-override-key error, and it is not applied

#### Scenario: Flat proposal
- **WHEN** the checked proposal `<slug>.md` sits directly in the proposal location, outside any folder
- **THEN** the check reports an error naming `<slug>/<slug>.md` in the location as the path it is expected at

#### Scenario: Misplaced proposal
- **WHEN** the governing `guidelines.md` sets the proposal-location path to `proposals/` and the checked proposal's folder sits at the workspace root
- **THEN** the check reports an error naming `proposals/<slug>/<slug>.md` as the expected path

#### Scenario: Check started inside the proposal's folder
- **WHEN** the check runs with the proposal's folder as working directory and no explicit override path
- **THEN** the check reports the misplacement error, and its message says that the check runs from the workspace root

#### Scenario: Override file passed from the proposal's folder
- **WHEN** the check runs from the workspace root with the explicit override path naming a `guidelines.md` in the proposal's folder
- **THEN** that folder is the workspace root, the misplacement error is reported, and its message names the explicitly passed override file, not the working directory, as what set the root

#### Scenario: Unset key raises no location finding
- **WHEN** the workspace sets no proposal-location path and the checked proposal is `<slug>/<slug>.md` in the workspace root
- **THEN** no location finding is reported

#### Scenario: Paths compared resolved
- **WHEN** the check runs from the workspace root reached through a symbolic link, over the proposal given as a relative path
- **THEN** placement is judged on the resolved paths, and no misplacement error is reported for `<slug>/<slug>.md`

### Requirement: Orphaned companions reported as a warning
The check SHALL list the checked proposal's folder with its subfolders, the root of the proposal location, the workspace root when it differs from that, and the slug-shaped folders of the proposal location one level deep, and no further; while the misplacement error is reported it SHALL list none of them, since the check may have started outside the workspace root. It SHALL report a warning, under one stable rule identifier, for each of the following:

- in the checked proposal's folder:
  - a markdown file named by another slug that opens with a `# ` title followed by an emphasized subtitle paragraph and ends in a metadata block: a second proposal;
  - a subfolder other than `img/` that holds a proposal named after it, a notes file or a harvest record: a proposal folder moved into another;
- at the root of the proposal location or the workspace root:
  - a markdown file named by a slug that ends in a metadata block, other than the checked proposal;
  - a hand-in export `<slug>.handout.md`;
  - a `review.md`, `feedback.md` or `harvest.md`;
  - a `notes.md` carrying the notes file's five section headings;
  - an `img/` folder;
  - any file whose name is the slug of a proposal folder in the location followed by `.`;
- in a slug-shaped folder of the proposal location that is not a proposal folder (proposal-file-format: One folder per proposal), each `review.md`, `feedback.md` or `<folder>.handout.md` it holds.

The check SHALL never report any of these:

- the workspace-level files, the troubleshooting captures and the installer-managed files of proposal-file-format "Working material stays out of the workspace";
- workspace build definitions, which have their own warning (requirement: Unused build definitions reported);
- hidden files or folders, `.gitignore` files included;
- inside a proposal folder, a kept file, and a built output or hand-in export named by an earlier slug, which a rename leaves as a previous output;
- any other folder or its contents.

The finding SHALL be a warning and SHALL NOT change the exit code. For this finding, the check SHALL open a file only to tell whether a markdown file opens with that title and subtitle or ends in a metadata block, or whether a notes file carries the five headings, and SHALL change nothing. The message SHALL name the file, SHALL name the proposal folder it belongs in when its name is a proposal folder's slug, and SHALL say that a file the user placed there on purpose can be left as it is.

#### Scenario: Leftovers of a partial rename
- **WHEN** the location holds `<new>/<new>.md` and a folder `<old>/` with `review.md`, `candidates.yaml` and `img/pipeline.png` but no `<old>.md`, no notes file and no harvest record
- **THEN** the check reports an orphan warning for `<old>/review.md` and none for the kept file or the figure, and the exit code is what the proposal's other findings make it

#### Scenario: Dump at the location root
- **WHEN** the proposal location holds the folder `<slug>/` with its proposal and, at the location's root, `<slug>.candidates.yaml`
- **THEN** the check reports an orphan warning for the root file naming `<slug>/` as the folder it belongs in

#### Scenario: Dump at the workspace root
- **WHEN** the governing `guidelines.md` sets the proposal location to `proposals/`, the proposal is `proposals/<slug>/<slug>.md`, and `<slug>.candidates.yaml` sits at the workspace root
- **THEN** the check reports an orphan warning for the root file naming `proposals/<slug>/` as the folder it belongs in

#### Scenario: Flat proposal beside the folders
- **WHEN** the check runs over `<a>/<a>.md` and the location root holds `<b>.md`, which ends in a metadata block, and `<b>-review.md`
- **THEN** the check reports an orphan warning for `<b>.md` and none for `<b>-review.md`, whose old name it does not classify

#### Scenario: Stale figure link with a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png`, a figure name from before the folder layout, and a folder `<old>/` exists in the location
- **THEN** no orphan warning is reported for the link, because figure names carry no slug and are not judged by one

#### Scenario: Stale figure link without a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png` and nothing else in the workspace carries `<old>`
- **THEN** no orphan warning is reported for the link

#### Scenario: Proposal whose name ends like a companion
- **WHEN** the folder `ml-code-review/` holds `ml-code-review.md`, which ends in a metadata block, and `review.md`
- **THEN** `ml-code-review.md` is the proposal, `review.md` is its review, and neither is reported

#### Scenario: Companion-shaped proposal beside a file under its base slug
- **WHEN** the folder `ml-code-review/` holds its proposal and the location root holds `ml-code.pdf` and `ml-code.candidates.yaml`, while no folder `ml-code/` exists
- **THEN** neither root file is reported, because `ml-code` names no proposal folder

#### Scenario: Tool files under a one-word name
- **WHEN** the workspace root holds a LaTeX build's `thesis.tex`, `thesis.pdf`, `thesis.synctex.gz` and `thesis.run.xml`, or a code repository's `tsconfig.app.json` and `tsconfig.spec.json`
- **THEN** none of them is reported

#### Scenario: Idea not yet seeded
- **WHEN** the location holds `idea/` with a notes file carrying the five headings and `reading-list.md`
- **THEN** no orphan warning names either file

#### Scenario: Harvest awaiting inspection
- **WHEN** the location holds `<thesis>/harvest.md`, written by a reverse run that stopped for inspection, and no `<thesis>/<thesis>.md`
- **THEN** no orphan warning names it

#### Scenario: Previous outputs after a rename
- **WHEN** the checked proposal's folder `<new>/` holds `<old>.pdf` and `<old>.handout.md` from before a rename
- **THEN** no orphan warning names either file

#### Scenario: Second proposal in a folder
- **WHEN** the checked proposal's folder `<a>/` also holds `<b>.md`, which opens with a `# ` title and an emphasized subtitle paragraph and ends in a metadata block
- **THEN** the check reports an orphan warning for `<a>/<b>.md`

#### Scenario: Run started above the workspace root
- **WHEN** the check runs from a directory above the workspace root, over `<ws>/<slug>/<slug>.md`, and that directory also holds another workspace's folders and files
- **THEN** only the misplacement error is reported, naming a start outside the workspace root as a possible cause, and no orphan or unused-build-definition warning names any file there

#### Scenario: Kept list ending in a metadata block
- **WHEN** the checked proposal's folder holds a kept `reading-list.md` that opens with a `# ` title and a plain paragraph and ends in a metadata block
- **THEN** no orphan warning names it, because it does not open with the proposal's title and subtitle

#### Scenario: Folder moved into another proposal's folder
- **WHEN** the checked proposal is `<a>/<a>.md` and `<a>/<b>/` holds `<b>.md`, left by a folder move onto a name that existed
- **THEN** the check reports an orphan warning for `<a>/<b>/` naming the location as the place the folder belongs

#### Scenario: Kept files whose labels end like a role
- **WHEN** the checked proposal's folder holds kept files `peer-review.md`, `reading-notes.md` and `supervisor-feedback.md`
- **THEN** none of them is classified as the review, the notes file or the feedback, because role files are matched by their exact name, and none is reported

#### Scenario: Unrelated folders and notes ignored
- **WHEN** the location holds `meetings/notes.md` without the five headings, `literature/img/scan.png`, and a `notes.md` of the user's own without the five headings at the workspace root
- **THEN** none of them is reported

#### Scenario: Workspace, build and installer files ignored
- **WHEN** the workspace root holds `guidelines.md`, `api-keys.env`, `bug-report/`, `check-output.txt`, `.gitignore`, `.agents/skills/` and `skills-lock.json`, and the checked proposal's folder holds `proposal-build.sh`, `faculty.typ`, `proposal.pdf` and `.gitignore`
- **THEN** no orphan warning names any of them

#### Scenario: Source documents and project files ignored
- **WHEN** the workspace root holds `submission.pdf`, `expose.docx`, `thesis.pdf`, `vite.config.ts` and `data.tar.gz`, and no proposal folder carries any of their names
- **THEN** none of them is reported

#### Scenario: Read-only listing
- **WHEN** the check runs over a workspace holding orphaned companions
- **THEN** every file is byte-identical afterwards and none was moved
