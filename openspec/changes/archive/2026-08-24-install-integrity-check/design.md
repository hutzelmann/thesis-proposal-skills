# Design — install-integrity-check

## Context

See proposal.md. Empirics from the probe: the skills CLI (v1.5.23) accepts a local path as the package argument, auto-detects a running agent and goes non-interactive, and found 17 skills in a working checkout (11 tracked + 6 untracked `.claude/skills/openspec-*`). `git ls-files` confirms the tracked tree ships exactly 11 SKILL.md, all under `skills/`.

## Goals / Non-Goals

**Goals:** verify the documented install path end-to-end on the current commit, hermetically enough for CI; make the shipped-skill count an enforced invariant.

**Non-Goals:** testing the GitHub-resolution half on every run (scheduled-only, `--list`); pinning the installer (users run latest — drift is the signal); joining `poe test`.

## Decisions

**D1 — `git archive HEAD` is the unit under test.** The exported tree is byte-for-byte what an install from the hosted repo serves (tracked files only), so the check tests the current commit before any push and is immune to local `.claude/` helpers. Rejected: testing the working directory (17-skill false signal), testing GitHub `main` on PRs (tests yesterday's code).

**D2 — The command comes out of the README.** `install_check.py` regex-extracts the `npx skills add <package>` line, swaps `<package>` for the exported tree's path, and appends only what non-interactivity requires (`-y`, agent/skill selection, `--copy`). The README stays the single source of the command's shape; extraction failure is a test failure. `--copy` because byte-comparing through symlinks would compare a file with itself.

**D3 — Isolation via env, like the audit scanner.** Temp `HOME`/`XDG_*` pointed into the temp dir so the CLI's global state, agent detection, and telemetry config never touch the operator's machine; install is project-scoped into a temp project dir.

**D4 — Smoke = the installed script, the staged fixture.** Copy `tests/fixtures/f15-format-broken/broken-format.md` into the temp project, run `python3 <installed proposal-check>/scripts/check.py broken-format.md`, require exit 1 and a recognizable finding string. This exercises the script, its `references/structure.json` loading, and the vendored-copy integrity in one call.

**D5 — Pure parts unit-tested offline.** Command extraction and expected-skill-set derivation (`git ls-files`-independent: `sorted(skills/proposal-*)`) live as functions with L0 tests; the networked `main()` stays out of the offline gate.

**D6 — CI wiring.** New `install` job on `push` (main) and `schedule` (weekly); ubuntu runner has node and git. Scheduled runs add the verbatim README command with `--list` against GitHub. The job is independent of the `l0` job so an installer regression cannot mask or be masked by an L0 failure.

## Risks / Trade-offs

- [Unpinned CLI changes flags or output format] → the check parses as little as possible (counts directories, compares bytes); a flag break fails loudly, which is the alarm's purpose.
- [npm outage fails the job] → weekly + push cadence keeps noise rare; the job is not a merge gate.
- [CLI installs to an unexpected layout in future] → assertions locate skills by directory name anywhere under the temp project's agent dirs rather than hardcoding one path segment deeper than needed.
