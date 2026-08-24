# Tasks — install-integrity-check

## 1. The check

- [x] 1.1 `scripts/install_check.py`: pure helpers `readme_install_command(text)` and `shipped_skills(repo)`; `main(argv)` — export `git archive HEAD` to a temp dir, install via the README-derived command with non-interactive flags under isolated HOME/XDG, assert exact skill set, byte-identity of every installed skill file, and the f15 smoke (installed check.py, exit 1, findings); `--verbatim` flag additionally runs the README command unchanged with `--list` against GitHub and asserts eleven skills
- [x] 1.2 Empirically pin down the CLI's non-interactive flags and install layout in the isolated environment; encode findings as comments, not assumptions

## 2. Wiring

- [x] 2.1 `poe install-check` task (not part of `poe test`)
- [x] 2.2 CI: `install` job on push + weekly schedule; scheduled run passes `--verbatim`
- [x] 2.3 L0 unit tests for the pure helpers (command extraction incl. failure case, shipped-skill derivation)

## 3. Docs

- [x] 3.1 harness/README.md: short section (what it proves, when it runs, why the CLI is unpinned); AGENTS.md command list gains `poe install-check`

## 4. Verify

- [x] 4.1 `uv run poe install-check` green locally
- [x] 4.2 `uv run poe test` green, `openspec validate --all --strict` green
