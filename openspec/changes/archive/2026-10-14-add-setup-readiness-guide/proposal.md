## Why

A student set up an empty proposals folder on Windows with OpenCode and needed hours of trial and error. The installer side of that report — Python discovery beyond `python3`/`python`/`py -3`, the interpreter clause in every script-bearing skill, the listing of shadowing copies, and the installer's presence-only "On this computer:" lines — already landed in `desktop-first-install`'s revision (4a11adb). What remains is documentation the student could not find, plus two defects in the skills themselves:

- Nothing says what each kind of work needs. Writing needs only an agent, while the checks and the literature search need Python, and PDF export needs pandoc and an engine. So a missing `typst` reads like a broken install.
- Nothing tells a student how to confirm that a setup works. "Installed" is not "working", and the installer's lines report presence only.
- When winget fails with a source error (`0x8a15000f`, "required source data missing"), publish's only advice is the package manager. The student's agent improvised a download it was never told how to verify.
- Publish's Windows hint, `winget install --id JohnMacFarlane.Pandoc Typst.Typst`, installs nothing. winget reads the second id as a positional query filtered by `--id JohnMacFarlane.Pandoc`, and no package matches both (winget-cli source, see design).
- `proposal-lit-search` adds `api-keys.env` to `.gitignore` only "if the workspace is a git repo". The spec says to "ensure version-control ignores cover the file" with no condition. A folder that becomes a repository later then commits the secret on its first `git add .`.
- The guide calls the workspace "your proposals folder" in its recipes but "several proposal folders" in its API-keys note. It never says that the proposals folder must not be a clone of this repository, whose `AGENTS.md` is for contributors.

## What Changes

- **`docs/install.md` gains a "What you need" table** directly under its introduction. It covers four kinds of work: writing, ideas and reviews need an agent app with the skills; the checks, the literature search and the other script-backed steps need Python 3.11 or newer, and the search also needs network access; a PDF needs pandoc plus typst or a LaTeX engine (optional); API keys are optional. One sentence says the proposals folder is the student's own empty folder, never a clone of this repository, and that the repository's `AGENTS.md` is for contributors and is never copied into it.
- **`docs/install.md` gains an "Is everything working?" checklist** of four checks, built on output the skills already produce. Each check says what it proves and what it does not:
  1. a new chat lists the eleven skills;
  2. the check script starts with `--help`;
  3. one literature search reports its `sources:` line;
  4. "Build a PDF" on the first draft.
  
  The checklist names the installer's "On this computer:" block as the quick view of what is present, and says that presence is not a working check.
- **`docs/install.md` gains a "PDF export" section**, which replaces the Notes bullet. The package manager comes first, with valid winget commands. When no package manager exists or it reports a source error, the student takes the archive for their platform from the tool's latest GitHub release (typst/typst, jgm/pandoc). They check it against the SHA-256 digest GitHub shows beside the asset, with `certutil -hashfile`, `shasum -a 256` or `sha256sum`, and unpack it into a folder they own that is on PATH. The section never says to repair or reset a package manager, never installs for all users, and pins no version.
- **Workspace wording in `docs/install.md`:**
  - one sentence on when to choose `[paths] proposals`, with flat as the default and without prejudging any later layout option;
  - the API-keys note reworded to "proposals folder", and to say that the student pastes the key and the agent never sees it;
  - README's "their proposal folder" becomes "their proposals folder";
  - README's quick start gains one line pointing to "Is everything working?".
- **`proposal-publish`:**
  - `SKILL.md`'s "When tools are missing" and `publish.py`'s `INSTALL_HINT` give winget one id per command (`winget install --id JohnMacFarlane.Pandoc -e`, `winget install --id Typst.Typst -e`);
  - both link the guide's PDF-export section for machines where no package manager works;
  - neither carries download, digest or extraction steps.
- **`proposal-lit-search`:** the key-setup step adds `api-keys.env` to the workspace-root `.gitignore`, creating the file when there is none, whether or not the workspace is a git repository yet.
- **Tests (L0, no model calls):**
  - tier table rows;
  - checklist structure, and its coupling to `install.py`'s "On this computer:" header and to `search.py`'s `sources:` line;
  - the PDF-export section is version-free, names the digest check and the three hash commands, and links only `releases/latest`;
  - no "proposal folder(s)" wording remains;
  - `INSTALL_HINT`'s winget lines are valid in form, and the hint's link resolves to a section the guide has;
  - publish carries no download steps;
  - the lit-search `.gitignore` sentence is pinned, and its git-only condition is guarded against coming back.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-onboarding`:
  - ADDED "Setup tiers and readiness checks in the install guide": the tier table, the four-check checklist with what each proves and does not prove, the installer's presence lines named as presence only, and an automated check that the quoted output still matches the scripts.
  - ADDED "User-local PDF tools when no package manager works": the version-free, digest-checked fallback, which lives only in the install guide.
  - MODIFIED "Users never work in this repository": the proposals folder is the student's own folder, never a clone, and the contributor `AGENTS.md` is not copied into it. The guide also says when a proposals subfolder is the better choice.
  
  None of these is owned by the open `desktop-first-install`, which modifies "Newcomer-ready README", "Zero-build quick start", "Concrete agent walkthroughs", "README names the path for a problem" and "Issue template mirrors the generated report", and adds three others.
- `skill-publish`: MODIFIED "Engine resolution order". The install guidance gives package-manager commands in a form the package manager accepts as written, and links the guide's PDF-export section for a machine without a working package manager instead of carrying download steps.
- `skill-lit-search`: MODIFIED "Keyless baseline, keys as guided upgrades". The workspace-root ignore file covers the key file whether or not the workspace is under version control yet, and a new scenario covers a workspace that is not a repository.

## Impact

- `docs/install.md`:
  - new sections "What you need", "Is everything working?" and "PDF export";
  - Notes' PDF bullet folded into the new section, and the API-keys bullet reworded;
  - "What you get in the folder" gains the `[paths] proposals` sentence.
  
  The generated install-prompt region is untouched, so `sync_shared.py` regenerates nothing.
- `README.md`: one word in "For supervisors" and one pointer line in the quick start, both outside the generated region.
- `docs/backlog.md`: one entry for the deferred dev-runner scenario that would measure the non-git key-file ignore.
- `skills/proposal-publish/SKILL.md`: one bullet changed and one bullet added in "When tools are missing". `skills/proposal-publish/scripts/publish.py`: `INSTALL_HINT` only, with no change to engine resolution or exit codes.
- `skills/proposal-lit-search/SKILL.md`: one clause of the key-setup bullet.
- Tests:
  - `tests/unit/test_install_docs.py`: tier table, checklist, PDF section, terminology, link coverage for `INSTALL_HINT`;
  - `tests/unit/test_publish.py`: winget form and the hint's link;
  - `tests/unit/test_audit_invariants.py`: no download steps in publish, no git-only condition on the key-file ignore;
  - new pin `tests/unit/data/pinned_sentences/proposal-lit-search--key-file-ignored.txt`.
- Audit posture: no skill gains a URL to a binary, a download command or a hash command, so publish keeps its SAFE/LOW verdicts. `docs/install.md` ships in no skill.
- Manual: the Windows session already scheduled as `desktop-first-install` task 8.7 also runs both winget lines and the archive fallback once, so one Windows run checks both changes.
- Sequencing: this change follows the landed B1 revision. It shares `skills/proposal-lit-search/SKILL.md` with the planned `classify-arxiv-answers` and `tighten-proposal-family`, so they are implemented one after another. It never edits `search.py`'s `sources:` line, which check 3 depends on.
