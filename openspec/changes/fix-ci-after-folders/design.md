# Design

## Context

See proposal.md (Why) for the three failures. Constraints that shape the fixes:

- The fix ships inside release 0.9.0 by moving its tag, so no file under `skills/` may change; every fix sits in `scripts/`, `tests/` or docs.
- `scripts/install_check.py` runs in its own workflow as plain `python3 scripts/install_check.py`, with no uv and no pytest `pythonpath`, so `harness/` is not importable there by default.
- `l0-windows` runs `poe test-fast`; the Linux lane cannot reproduce a newline translation or a drive-letter path, so the Windows-only behavior needs a test that runs on every OS.

## Goals / Non-Goals

**Goals:**

- The install smoke proves what it claims on the folder layout: the installed check finds the seeded format errors, not a placement error.
- A spelled fixture path in `scripts/` turns L0 red, as one in `tests/` or `harness/` already does.
- The smoke itself is exercised offline at L0, so the next layout change breaks it before CI's networked run does.

**Non-Goals:**

- Changing what the check reports, or any shipped skill file.
- Rewording the testing-harness requirement to name `scripts/`; the guard enforces the existing rule on more files.
- Making `install_check.py` read its fixture from the exported tree instead of the checkout; it read the checkout before and still does.

## Decisions

**D1: The smoke compares error rules with the fixture's oracle.** The smoke runs the installed check with `--json` and requires exit 1 and an error-rule set equal to `expected.json`'s `check.rules.errors`, both resolved through `fixture_paths`. The old test, `"ERROR" in stdout`, is what let a placement-only report count as a pass. Alternatives: keep the human report and reject a placement message by its text (brittle, couples the smoke to prose), or require only "some error other than `proposal-misplaced`" (passes when a reference file fails to travel and one rule silently stops firing). The oracle is already calibrated against `check.py` by L0, so the comparison adds no new source of truth.

**D2: The workspace is the folder shape, run from its root.** The proposal is staged at `<workdir>/<slug>/<slug>.md` and the check runs from `<workdir>` with the relative path, the way a user's agent runs it. In the npx arm `<workdir>` is the project that also holds `.claude/skills/`; the L0 test covers both that shape and the installer's separate home, so a hidden install folder inside the workspace is shown not to produce findings.

**D3: `harness/` becomes importable the way `harness/lit_live.py` makes skill scripts importable.** The script inserts the harness directory into `sys.path` only when it is not already there, so under pytest (where `pythonpath` lists it) nothing changes. Alternatives: a `-m`/`PYTHONPATH` change in the workflow (two places to keep in step, and `poe install-check` would need the same), or a local copy of the fixture lookup (the very duplication `fixture_paths` exists to prevent).

**D4: The fixture-path guard scans `scripts/`.** `offending_lines` walks `tests`, `harness` and `scripts`. Red first: before the fix it names `scripts/install_check.py:42`.

**D5: Bytes, not text, where a test measures bytes.** `sandbox_ws` writes `text.encode("utf-8")` with `write_bytes`, the convention `test_identify_release.py` already uses for the same reason. The same pattern appears in `test_copilot_cli.py`'s `_staged_tree`, whose SKILL.md digest is compared with a byte literal; it is POSIX-only today, so it cannot fail on Windows, but it is aligned so the gate does not depend on that skip.

**D6: The merge hint prints the native path, quoted for the shell, through a formatting function.** `fast_forward_main` hands the path git reports to `checkout_hint(path, flavour=Path)`, which renders `flavour(path)` and quotes it: a Windows path is always double-quoted (`git -C "C:\Users\x" merge …`), a POSIX path goes through `shlex.quote`, which leaves a path of safe characters (every path the Linux test sees) byte-identical and single-quotes anything else. The quoting is what makes the native spelling copyable: unquoted, Git Bash, the usual shell for git on Windows, strips the backslashes (`C:Usersx`), and cmd and PowerShell split a path with a space. Double quotes are the one quoting cmd, PowerShell and Git Bash all honor, and a Windows file name cannot contain `"`. Alternatives: keep git's `C:/Users/x` spelling (copies unquoted into all three shells, but still breaks on a space, and keeps the end-to-end test comparing spellings), or print the native path bare (the first version of this change; a review found it uncopyable in Git Bash). A unit test passes `PureWindowsPath` and `PurePosixPath` explicitly, so the Windows rendering is proven on every OS, not only in the Windows lane; the end-to-end test compares the printed path with the checkout as paths (`samefile`), so it no longer depends on how git or the platform spells it.

## Risks / Trade-offs

- [The oracle and the installed check come from different trees when `--ref` names something other than the checkout's HEAD] → the same was already true of the fixture; under the CI invocation (`HEAD` of a clean checkout) both coincide, and a mismatch names both rule sets.
- [`sys.path.insert(0, …)` could shadow a module of the same name] → `install_check.py` imports only `fixture_paths` from there, and no harness module shares a name with a stdlib module or a script it imports.
- [`Path(path)` normalizes git's path (redundant separators)] → git's porcelain output carries none, and the POSIX case of the unit test pins the unchanged output.
- [A Windows path containing `$` or a backtick would still expand inside double quotes in PowerShell or Git Bash] → no quoting serves cmd, PowerShell and Git Bash alike for those characters; they do not occur in a default profile or temp path, and the unquoted form failed on far commoner paths.
