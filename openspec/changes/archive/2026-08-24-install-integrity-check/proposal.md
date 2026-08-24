# Install integrity check

## Why

Nothing verifies that the README's install command actually works: that the skills CLI discovers this repository's skills, that exactly the eleven shipped skills install (a local probe found 17 — six untracked `.claude/skills/openspec-*` helpers a naive local install would offer), and that an installed skill's scripts and references run from their installed location. The offline suite cannot see any of this; a broken install would be discovered by a student.

## What Changes

- **`scripts/install_check.py` + `poe install-check`**: exports the tracked tree via `git archive HEAD` (byte-for-byte what GitHub serves — tests the current commit without pushing), installs it with the skills CLI into a temp project under an isolated `HOME`/`XDG`, and asserts: the install command is extracted from the README itself (drift guard), exactly the eleven `proposal-*` skills install and nothing else, every installed `SKILL.md` is byte-identical to the repo's, `scripts/`/`references/`/`evals/` travel, and the installed `proposal-check` script runs against a broken fixture with exit 1 and findings.
- **CI job `install`**: runs the check on push to main and on a weekly schedule (the CLI is deliberately unpinned — users run latest, and an installer regression is exactly the alarm wanted). On the scheduled run only, the README command is additionally run verbatim against GitHub with `--list`, asserting the published repo resolves and offers eleven skills.
- Stays out of `poe test` — the offline gate stays offline.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `skill-packaging`: new requirement — installation is verified against the tracked tree with the documented command, including a functional smoke of an installed script.

## Impact

- `scripts/install_check.py` (new, dev-side), `pyproject.toml` (poe task), `.github/workflows/ci.yml` (job + weekly schedule), `harness/README.md` or README pointer.
- L0: unit test for the pure parts (README command extraction, expected-skill-set derivation) without network.
