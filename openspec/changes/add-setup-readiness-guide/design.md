# Design

## Context

See proposal.md, "Why". The parts of the student's report that concern the installer and the prompt landed in `desktop-first-install`'s section-9 revision (4a11adb, on `main`):

- the prompt probes `uv python find`, versioned names and `py -0p` before it reports no Python;
- every script-bearing skill carries one interpreter clause;
- `install.py` lists and offers to remove copies in apps' own folders;
- `install.py` ends with presence-only lines under the heading `On this computer:`.

This change carries the documentation half and two small skill defects, and the maintainer settled its scope on 2026-10-13 (P-Q5 default 2, P-Q6, P-Q7). Constraints that shape it:

- `docs/install.md` ships in no skill. The agent follows it only when the student asks. Its install-prompt region is generated from `shared/blocks/install-prompt.md`, and everything else in it is hand-written.
- Publish holds SAFE/LOW verdicts at both auditors (Snyk Agent Scan, Gen Agent Trust Hub). Download-and-run instructions inside a skill are the pattern those audits flag.
- The open `desktop-first-install` owns these requirements:
  - installation: "One install prompt…" and "Existing installs…";
  - skill-packaging: "User-side script constraints";
  - user-onboarding: five MODIFIED and three ADDED requirements.
  
  This change touches none of them. It modifies "Users never work in this repository", which no open change owns, and otherwise only ADDs.
- `search.py` prints `sources: name(n), …` or `sources: none` on stderr (search.py:57). `install.py` prints `On this computer:` (install.py:664). The checklist quotes both strings.

### Upstream facts, verified read-only on 2026-10-13

- **GitHub release digests.** The GitHub changelog of 2025-06-03, "Releases now expose digests for release assets", says GitHub automatically computes and displays SHA256 checksums for all uploaded release assets. They appear "next to each asset" in the Releases UI, and in the REST API, GraphQL and `gh`. Digests are fixed at upload, and the changelog does not say they were backfilled for older releases. The REST API's latest-release endpoint (`gh api repos/<owner>/<repo>/releases/latest`) returns a `digest: "sha256:<hex>"` on every asset of both projects' current latest releases.
- **typst/typst latest release** (`v0.15.1` at the time of reading, published 2026-07-17; recorded here only as evidence, never in the guide):
  - assets are named `typst-<target-triple>` with no version in the name;
  - `typst-x86_64-pc-windows-msvc.zip` and `typst-aarch64-pc-windows-msvc.zip`;
  - `typst-{x86_64,aarch64}-apple-darwin.tar.xz`;
  - `typst-{x86_64,aarch64}-unknown-linux-musl.tar.xz`, plus `armv7` and `riscv64` Linux builds.
  
  The README's Installation section says to download the archive for your platform and place it in a directory that is in your PATH. It names `winget install --id Typst.Typst` and `brew install typst`, and notes that package-manager versions may lag behind the latest release.
- **jgm/pandoc latest release** (`3.12.1` at the time of reading, published 2026-10-08, tag without a `v`):
  - asset names carry the version: `pandoc-<version>-windows-x86_64.zip` / `.msi`, `pandoc-<version>-{arm64,x86_64}-macOS.zip` / `.pkg`, `pandoc-<version>-linux-{amd64,arm64}.tar.gz`, `pandoc-<version>-1-{amd64,arm64}.deb`;
  - there is no Windows ARM build.
  
  `INSTALL.md` (main) has three relevant points:
  - Windows: the zip holds the binaries, to be moved "to a directory of your choice", and the documented winget command is `winget install --source winget --exact --id JohnMacFarlane.Pandoc`;
  - macOS: a zip of the binaries for those who prefer not to use the installer;
  - Linux: the tarball unpacks with `--strip-components 1` into a destination such as `$HOME/.local`, so the binary sits in `bin/`, while the `.deb` needs `sudo dpkg -i`.
- **winget's `--id A B` form.** Source: microsoft/winget-cli `master`, read 2026-10-13; latest stable `v1.29.380`.
  - `install` takes `[[-q] <query> ...]`.
  - `ExecutionArgs::MoveMultiQueryToSingleQueryIfNeeded` (ExecutionArgs.h) turns a lone positional value into the single `Query`. So `winget install --id JohnMacFarlane.Pandoc Typst.Typst` searches for `Typst.Typst` restricted to the id `JohnMacFarlane.Pandoc`. No package matches both, and nothing is installed.
  - With two or more positionals, `Argument::GetCategoriesAndValidateCommonArguments` (Argument.cpp) rejects every `SinglePackageQuery` argument (`--id`, `--name`, `--moniker`, `--version`, …) with "An argument was provided that can only be used for single package". `-e`/`--exact` is a plain `PackageQuery` argument and stays allowed.
  - Microsoft Learn's `install` page (updated 2026-07-21) documents the multi-package form `winget install A B C` and recommends `winget install --id <Id> -e` to select exactly one package.
  - `0x8A15000F` is `APPINSTALLER_CLI_ERROR_SOURCE_DATA_MISSING` (AppInstallerErrors.h).
- **Hash commands:**
  - `certutil -hashfile <file> SHA256` ships with Windows;
  - `shasum -a 256` ships with macOS;
  - `sha256sum` is GNU coreutils on Linux.
  
  `certutil` prints lowercase hex, PowerShell's `Get-FileHash` prints uppercase, and the GitHub UI prefixes `sha256:`. The guide therefore tells the student to compare the 64 characters and ignore case.

## Goals / Non-Goals

**Goals:**

- A student can tell from one table what their kind of work needs.
- A student can confirm a setup with four checks whose limits are stated.
- A broken or missing package manager has a documented, verifiable, user-local route that will not go stale.
- Publish's Windows hint installs what it names.
- The key file is ignored in every workspace.
- Every new claim the guide makes about script output or upstream structure is guarded offline wherever a guard is possible.

**Non-Goals:**

- No new script, no `install.py --check`, no readiness probe in any skill, and no twelfth "setup" skill (D1).
- No OpenCode recipe. A recipe needs a stamped end-to-end run (onboarding spec, "Concrete agent walkthroughs", owned by `desktop-first-install`).
- No guidance to record the interpreter in `AGENTS.md`/`CLAUDE.md`. `test_no_skill_names_a_host_instruction_file` already forbids it in skills, and the guide does not suggest it either.
- No change to `install.py`, the install prompt, `search.py`'s output, engine resolution or exit codes.
- No per-proposal folder layout. The `[paths] proposals` sentence stays neutral, so that a later `add-proposal-folders-layout` can extend "What you get in the folder" without contradicting it.
- No networked test in CI.

## Decisions

### D1. Documentation over a preflight helper or a setup skill

The report asked for this comparison explicitly.

| Option | What it would cost to maintain | What it would add |
|---|---|---|
| Docs checklist (chosen) | Four entries, plus two coupling tests that fail when quoted output drifts | Builds on output each skill already produces at first use, and has no audit surface |
| Stdlib preflight script in a skill | A new user-side script that must run on three platforms. Its tests cover missing tools, versioned Pythons, spaces in paths and secret-safe output. To prove more than presence it would have to start pandoc and contact the network, which brings a new subprocess and network pattern into an audited skill | Mostly repeats the installer's presence lines and the skills' own first-use reports |
| `install.py --check` | The student downloads the temporary installer again. It grows the open change, whose verification is manual (task 8.7) | Presence again; the lines do not survive into the new chat |
| Twelfth `proposal-setup` skill | The workflow line, header pattern, mandate pin, owned trigger terms, routing cases, eval projection and matrix cells all grow. Routing on small models is already fragile (haiku routing notes) | Another place for the same facts |

### D2. The checklist proves by running, and states its limits

Each check is one prompt the student sends, the output to look for, what that **shows**, what it **does not show**, and where to go **if not**. The four checks span the tiers:

- discovery: the skill list;
- interpreter and path: `check.py --help`, which imports `tomllib` and so fails below Python 3.11;
- network and certificates: the `sources:` line. OpenAlex is key-gated (`openalex.py` raises `SourceError` without a key), so `openalex(n)` in that line also proves the key;
- PDF toolchain: the first build, after which publish names its pipeline.

The installer's `On this computer:` block is named as the quick view of what is present, and the checklist says that present is not working.

Alternative: a fixture check, such as running `check.py` on a synthetic proposal. Rejected: the student would need a fixture the installed skills do not ship, and check 2 already proves the interpreter and the path.

### D3. Coupling tests instead of trusting prose

The checklist quotes `On this computer:` and `sources:`. `test_install_docs.py` asserts that both strings appear in the checklist. It asserts that `install.report_readiness` prints the first. For the second, it drives `search.federate` in-process with a stub source and checks the stderr prefix, using the same pattern as the `run` fixture in `test_lit_search_cli.py`. Both quoted strings thus stay byte-stable, which matters because `classify-arxiv-answers` and `tighten-proposal-family` both edit `search.py`'s stderr.

### D4. The fallback lives only in `docs/install.md`, without versions

This was decided by the maintainer (P-Q6).

- The guide links `https://github.com/<project>/releases/latest` and describes the asset by platform words (Windows, macOS, Linux, `aarch64`/`arm64`, `x86_64`/`amd64`) rather than by file name. Pandoc's names carry the version, so a file-name example would go stale with every release.
- The digest step is independent of the asset's name.
- It prefers an archive over an installer: `.msi`, `.pkg` and `.deb` may ask for administrator rights or install for all users (pandoc's `.deb` needs `sudo`).
- The destination is a folder the student owns that is already on PATH. Where none exists, the guide says that adding one to the user PATH is the student's decision, and that the agent asks before it changes that setting. This keeps "never change PATH silently" from the report.
- The guide never says to repair, reset or reconfigure a package manager.

Alternatives were rejected:

- **Steps in the publish skill:** the audit pattern, and the skill would go stale with upstream.
- **No fallback:** students stuck on `0x8a15000f` today.
- **Pinning versions with fixed digests in the repo:** stale by design, and it shifts the trust anchor from GitHub's per-asset digest to this repository.

### D5. Valid winget form: one `--id … -e` per package

Both `SKILL.md` and `INSTALL_HINT` give `winget install --id JohnMacFarlane.Pandoc -e` and `winget install --id Typst.Typst -e` as two commands. This form matches the projects' own documented commands. `-e` makes the match exact, as Learn recommends. It works on every winget, including App Installer builds that predate multi-query.

- The documented positional form `winget install -e JohnMacFarlane.Pandoc Typst.Typst` was rejected: it needs a multi-query-capable winget and refuses `--id`.
- `--source winget`, which pandoc's own command adds, was considered and left out. It only disambiguates duplicates across configured sources, neither id is in the msstore source, and it does not help when the winget source itself is broken.

An offline test parses every `winget install` line in `INSTALL_HINT`, the publish `SKILL.md` and the guide's PDF section, and rejects any line that does not meet all of these:

- exactly one id follows `--id`;
- no further positional token appears;
- `-e`/`--exact` is present.

The parser is a helper in `tests/helpers.py`, because it has three call sites.

### D6. Skills link the section and carry nothing else

Publish's `SKILL.md` gains one bullet: with no package manager, or one that fails with a source error, point the user to `…/docs/install.md#pdf-export` instead of repairing the package manager. `INSTALL_HINT` gains the same link under the package-manager lines.

- The address is the published URL on `main`, as `proposal-check` already links `#no-python-yet`, because an installed skill has no repository beside it.
- `test_every_link_into_the_guide_names_an_existing_section` already reads every `SKILL.md`. It is extended to read `publish.INSTALL_HINT`, and it requires `proposal-publish` among the linking skills.
- An audit-invariant test forbids download, hash and extraction tokens in the publish skill and its script: `releases/latest`, `releases/download`, `curl`, `wget`, `Invoke-WebRequest`, `certutil`, `shasum`, `sha256sum`, `Expand-Archive`, `tar x`.

The LaTeX-tier note at publish.py:336 names no command, so it carries no broken form, and it stays as it is.

### D7. The key file is ignored in every workspace

`proposal-lit-search`'s key-setup bullet changes from "ensure `.gitignore` covers `api-keys.env` (add the entry if the workspace is a git repo …)" to an unconditional instruction: add `api-keys.env` to the `.gitignore` at the workspace root, creating that file if there is none, whether or not the workspace is a git repository yet.

- This matches the existing spec clause, which has no condition, and matches `publish.py`'s `ensure_gitignore`, which already writes `.gitignore` regardless of git.
- A workspace nested inside a larger repository is covered too, because git reads `.gitignore` at every level.
- The behaviour is agent prose, so the L0 guard is a pinned sentence plus a negative assertion that the git-only condition does not return.

A dev-runner scenario would measure the behaviour itself. It is not in this change; it goes to the backlog (see "Settled at review").

### D8. Workspace wording

The guide calls the root the "proposals folder" everywhere, as its recipes already do. Two passages change to match:

- the API-keys note: "several proposal folders" becomes "more than one proposals folder";
- README "For supervisors": "their proposal folder" becomes "their proposals folder".

A distinct name stays free for any later per-proposal directory. The clone and `AGENTS.md` warning sits under the tier table, where the student first creates the folder. It lives only in the guide: `test_no_skill_names_a_host_instruction_file` keeps `AGENTS.md` out of every `SKILL.md`, which is why the warning cannot go into a skill.

The `[paths] proposals` sentence says when a subfolder is worth it: the folder holds other files of the student's, or several proposals. It names the phrase to send to the agent, and it says that `guidelines.md` and `api-keys.env` stay at the top.

### D9. Placement in `docs/install.md`

The resulting order of sections:

1. introduction;
2. **What you need** (new);
3. Which app do you use?;
4. The install prompt, with its "No Python yet?" subsection;
5. Recipes, whose intro gains one sentence pointing to the checklist;
6. Chat-only apps;
7. **Is everything working?** (new);
8. Literature search cannot reach its sources;
9. **PDF export** (new);
10. Updating, Removing, From a terminal, What you get in the folder, Notes.

README's quick start also gets one line after its step 4, pointing to the checklist. The tier table is four rows and comes first, because "what do I need" is a newcomer's first question. The checklist sits directly before the two troubleshooting sections it links to. The Notes' PDF bullet moves into the new section, so the same text does not appear twice.

## Draft wording

The tests pin structure and quoted tokens, not every word, so implementation may polish this text.

**What you need** (new section after the introduction):

```markdown
## What you need

| To … | you need |
|---|---|
| develop an idea, write and review a proposal | an agent app with the skills installed — nothing else |
| check a proposal, search literature, import a document | Python 3.11 or newer on your computer; the install prompt checks for it ([No Python yet?](#no-python-yet)). The literature search also needs network access. |
| build a PDF (optional) | `pandoc` plus `typst` or a LaTeX installation ([PDF export](#pdf-export)) |
| better abstracts in the literature search (optional) | a free API key; your agent offers it when it would help ([Notes](#notes)) |

Your proposals folder is an empty folder of your own. Never use a copy (clone) of this repository as your proposals folder, and do not copy its `AGENTS.md` into yours: that file instructs agents that develop the skills, not the agent that helps you write.
```

**Recipes intro**, one added sentence: `After installing, [Is everything working?](#is-everything-working) shows which parts work on your computer.`

**Is everything working?** (new section):

```markdown
## Is everything working?

The installer's last lines, under **On this computer:**, show which Python ran it and whether `pandoc`, `typst` and an `api-keys.env` file are present. Present is not the same as working. These four checks run the real thing, and each one shows one part and leaves the rest open. Ask your agent in a new chat:

1. *"Which proposal skills can you use?"* It should name eleven skills, from `proposal-check` to `proposal-write` (in the Claude desktop app they start with `thesis-proposal:`).
   **Shows:** your app finds the skills. **Does not show:** that their programs run.
   **If not:** start a new chat or reload skills. If some appear twice, see [Removing](#removing).
2. *"Run the proposal-check script with `--help`."* It should print the script's usage.
   **Shows:** a Python 3.11 or newer answers, and the agent finds the skills' programs. **Does not show:** that a check of your proposal passes, or that the network works.
   **If not:** see [No Python yet?](#no-python-yet).
3. *"Run one literature search for a term from my field, add nothing to any proposal, and show me the `sources:` line."* The line lists each service that answered, for example `sources: crossref(10), dblp(4)`.
   **Shows:** the services named there are reachable from your computer and their certificates are trusted; if `openalex` is among them, your API key works. **Does not show:** that the services missing from the line are reachable, or that the results fit your topic.
   **If not** (`sources: none`, or fewer services than you expect): see [Literature search cannot reach its sources](#literature-search-cannot-reach-its-sources).
4. Once you have a first draft: *"Build a PDF."* The agent names the pipeline that built it, typst or LaTeX.
   **Shows:** `pandoc` and an engine work. **Does not show:** anything about the checks or the search. You need this only if you want a PDF.
   **If not** (a `.docx` instead of a PDF, or "pandoc not found"): see [PDF export](#pdf-export).
```

**PDF export** (new section, replacing the Notes bullet):

```markdown
## PDF export

Writing needs no extra software, and a markdown file is a fine hand-in. A PDF needs `pandoc` plus one engine: `typst` (recommended: small and fast) or a LaTeX installation you already have (TeX Live, MiKTeX). The publish skill says what is missing when you first ask for a PDF.

**With a package manager** (try this first):

- Windows: `winget install --id JohnMacFarlane.Pandoc -e`, then `winget install --id Typst.Typst -e`
- macOS: `brew install pandoc typst`
- Linux: your distribution's package manager. Some do not package `typst` yet; then use the release archive below.

**Without a package manager**, or when it fails with an error about its sources (on Windows, for example, `0x8a15000f`), do not repair or reset the package manager. Use the tool's own release archive, installed for you alone:

1. Open the latest release: [typst](https://github.com/typst/typst/releases/latest), [pandoc](https://github.com/jgm/pandoc/releases/latest).
2. Download the archive for your computer: the `.zip` for Windows; on macOS and Linux, the archive that names your system and your processor (`aarch64` or `arm64` for Apple silicon and other ARM machines, `x86_64` or `amd64` for most others). Take the archive, not an installer (`.msi`, `.pkg`, `.deb`): installers may ask for administrator rights.
3. Compare the file with the SHA-256 digest GitHub shows beside the download (`sha256:` followed by 64 characters):
   - Windows: `certutil -hashfile <file> SHA256`
   - macOS: `shasum -a 256 <file>`
   - Linux: `sha256sum <file>`

   The two values must be equal; capital and small letters do not matter. If they differ, delete the file and stop.
4. Unpack the archive and move the program inside it (`typst` or `pandoc`, ending in `.exe` on Windows, sometimes in a `bin` subfolder) into a folder that belongs to you and is already on your PATH, such as `~/.local/bin`. If no such folder is on your PATH, adding one to your user PATH is your decision; your agent should ask before it changes that setting. Never install it for all users.
5. Open a new chat or terminal and check: `typst --version`, `pandoc --version`.

Your agent can do these steps when you ask it to. It should show you each download and the digest comparison before it moves anything. On macOS, if the system refuses to open a downloaded program, use Homebrew instead; do not switch that protection off.
```

**What you get in the folder**, replacing its last paragraph:

```markdown
Everything sits flat in your proposals folder by default, which suits one or two proposals. If the folder also holds other files of yours, or you keep several proposals there, a subfolder keeps them apart: tell your agent *"Keep my proposals in a subfolder"*, and it sets `[paths] proposals` in your `guidelines.md`. The proposal and everything named after it then live in that subfolder, while `guidelines.md` and `api-keys.env` stay at the top.
```

**README quick start**, one line after step 4:

```markdown
Not sure everything works? [Four quick checks](docs/install.md#is-everything-working) show which parts run on your computer.
```

**`docs/backlog.md`**, under "Evaluation and measurement":

```markdown
- **Key-file ignore in a non-git workspace.** `proposal-lit-search`'s key setup adds `api-keys.env` to the root `.gitignore` whether or not the folder is a git repository, which is agent prose guarded only by a pinned sentence. A dev-runner scenario would seed a non-git folder, accept key setup and assert the root `.gitignore`. Evidence: `openspec/changes/archive/<date>-add-setup-readiness-guide/design.md` (D7).
```

**Notes, API keys:**

```markdown
- **API keys.** Optional free keys improve abstract coverage. When one would help, the agent offers to walk you through the signup, creates a small `api-keys.env` file at the top of your proposals folder with an empty line for the key, and adds that file to `.gitignore` so it stays out of version control. You paste the key into the file yourself; the agent never sees it. To use one key in more than one proposals folder, put the file in `~/.config/thesis-proposal/api-keys.env` instead.
```

**`proposal-publish/SKILL.md`, "When tools are missing":**

```markdown
- **pandoc + typst** (recommended, two single binaries): `winget install --id JohnMacFarlane.Pandoc -e` and `winget install --id Typst.Typst -e` / `brew install pandoc typst` / distro packages. Smallest install, fastest builds.
- No package manager, or one that fails with an error about its sources (winget `0x8a15000f`, for example): point the user to the install guide's PDF-export section, https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#pdf-export, rather than repairing the package manager.
```

**`publish.py` `INSTALL_HINT`:**

```text
For PDF output install pandoc + typst (two single binaries):
  Windows: winget install --id JohnMacFarlane.Pandoc -e
           winget install --id Typst.Typst -e
  macOS:   brew install pandoc typst
  Linux:   pandoc + typst via your package manager
No package manager, or it reports an error about its sources? See
  https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#pdf-export
An existing TeX installation also works as fallback (only pandoc needed).
```

**`proposal-lit-search/SKILL.md`, key-setup clause.** The pinned part is "creating that file if there is none, whether or not the workspace is a git repository yet":

```markdown
… with the placeholder line `OPENALEX_API_KEY=` (no value after the `=`), add `api-keys.env` to the `.gitignore` at the workspace root — creating that file if there is none, whether or not the workspace is a git repository yet, because the file holds a secret and a folder can become a repository later — and ask the user to paste their key …
```

## Risks / Trade-offs

- **[Risk]** GitHub stops showing digests in the Releases UI, or a project uploads an asset without one. → The digest is also in the REST API and `gh`. The step says to stop when the values differ, and a missing digest leaves nothing to compare. A weekly networked probe was declined at review.
- **[Risk]** Upstream renames its assets. → The guide describes assets by platform and processor words, never by file name. Only the two `releases/latest` URLs are fixed, and the existing networked `install-check` workflow is the natural place to probe them if that is wanted.
- **[Risk]** macOS Gatekeeper refuses a program downloaded through a browser. → The guide routes macOS to Homebrew in that case and never says to remove the quarantine attribute. The claim is unverified on a Mac and joins the manual run.
- **[Risk]** The agent reads the guide and repairs winget anyway. → Both the guide and the publish skill say not to, and the request boundary ("do not reset package managers") is restated where the agent meets the error.
- **[Risk]** The four-check list is read as complete. → Every check carries its "Does not show" line, and the closing presence paragraph says that presence is not working.
- **[Trade-off]** The `.gitignore` rule is prose, so L0 can guard only the sentence. → A $0 dev-runner scenario can measure it later without changing the spec; its backlog entry lands with this change.
- **[Trade-off]** The winget form is enforced by a token rule derived from winget's source, not by running winget. → The manual Windows session runs both lines once.

## Migration Plan

Documentation and message changes only, so there is no data migration. The change lands on `main` as one commit after `poe test` and `poe specs` are green. It leaves the generated regions alone, so `sync_shared.py --check` stays clean, and a rollback is a revert of that commit. The manual Windows confirmation (task 5.1) runs in the same session as `desktop-first-install` task 8.7 and does not block landing. Its result can only correct wording.

## Settled at review (2026-10-13)

The maintainer approved the change with the recommended defaults for the three questions this draft left open:

- **Dev-runner scenario for the non-git `.gitignore`: deferred.** It becomes one entry in `docs/backlog.md`'s Evaluation section, added in this change's commit. The entry names the setup the scenario would use: a non-git folder, key setup accepted, and the root `.gitignore` asserted. It would sit beside the existing "Dev-runner scenarios for four skills" item.
- **Weekly digest probe: declined.** `poe install-check` stays as it is. The guide's "stop when the values differ" step covers a missing digest.
- **Quick-start pointer: added.** README's quick start gets one line after step 4 that points to `docs/install.md#is-everything-working`. The existing link test checks that it resolves. This adds a link and changes none of the README requirements `desktop-first-install` owns.

The macOS details are unverified: the system refusing a browser-downloaded program, and where pandoc's archive keeps its program. They stay as drafted and are confirmed or corrected in task 5.1, which stays open after landing until that manual run.
