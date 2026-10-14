Every file of a proposal goes into the proposal location: the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — then only there, never both, and never into a host's scratch or temporary folder. A proposal's slug, its file name without the extension, names its whole family:

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

The slug is derived from the working title when the proposal file is first written, and it stays when the title changes later; a draft from an existing seed goes into that file. It changes only by a rename: at seeding, when the settled working title yields a different slug than the provisional one, or when the user asks. A rename moves every family file under the old slug at once, built outputs excepted, and updates every link to a moved file in the proposal and its notes file; it never edits the text of a review or supervisor feedback. Built outputs stay as previous builds: name them and offer a rebuild. Check every target name first. At seeding, when any target name is taken, the slug takes the numeric suffix and the whole family moves to it; on request, move nothing, name the collision and propose the suffixed slug. When a file cannot be moved, stop, overwrite nothing, and say what moved and what did not. Say which files you renamed.

Besides proposal families, the workspace holds only: `guidelines.md`, `api-keys.env`, `bug-report/` and `.gitignore` at the root; beside a proposal, a workspace build definition (a file named `proposal-build`, with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the files that build reads and writes, and the `.gitignore` the built-in build adds; the troubleshooting captures `check-output.txt` and `version-output.txt` while a report is assembled; and the installers' `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the record `.thesis-proposal-install.json` and `skills-lock.json`, which you never write or tidy. Nothing else goes there. Script output, candidate lists, raw responses, probes and logs stay in the chat. Read output too large for one piece in slices — a page range, the next lines — or produce it narrower. A temporary folder outside the workspace is a fallback only where one is writable, and a refused one is never a reason to write into the workspace. Keep a file only when the user asks: as `<slug>.<label>.<ext>` beside the proposal, never with the label `notes` or `harvest`, or in the notes file before a slug exists.
