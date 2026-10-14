## Why

The spec gate (`uv run poe specs`, run by CI) pins OpenSpec 1.7.0, while the maintainer's local CLI is 1.13.1, the generated agent skills under `.claude/skills/` carry `generatedBy: "1.7.0"`, and npm's latest is 1.14.1 (published 2026-10-06). Nothing notices when the pin falls behind. Moving the pin to 1.14.1 is not a one-line bump either: 1.14.1 turned the hint about requirements longer than 500 characters into a WARNING, so `validate --all --strict` fails all 19 items on main (213 long requirements in the specs, 12 more in the open changes' ADDED deltas). The open changes' MODIFIED deltas hold 10 more, which OpenSpec reports only once their changes are archived. Every other check passes under 1.14.1. Shortening 235 requirements in one change would rewrite most of the specs under review pressure, and leaving the gate on 1.7.0 would freeze it.

## What Changes

- **One pin, 1.14.1.** The OpenSpec version lives in one place, `scripts/validate_specs.py`. The `specs` poe task runs that script, and CI runs the task, so CI and developers validate with the same CLI.
- **The gate runs a script.** `scripts/validate_specs.py` runs the pinned CLI's `validate --all --strict --json`. It fails on every error or warning, with one exception: the requirement-length warning goes through a ratchet. A report that validated less than the tree holds (no items, a missing spec or change) stops the gate instead of passing it.
- **The ratchet.** A baseline, `openspec/long-requirements.json`, lists every requirement over 500 characters on today's tree, with its length. Specs are keyed by capability and requirement name, open changes by change, capability and name. Lengths are OpenSpec's own measure, read from the pinned CLI's `show --json` output and counted as JavaScript counts them. A long requirement missing from the baseline fails, and so does one longer than its entry. A requirement that got shorter or disappeared is reported. `--update-baseline` then rewrites the file and only ever tightens it; CI never runs it. MODIFIED text, which OpenSpec measures only after the archive, is measured while its change is open, against its own entry or else the entry of the spec requirement it replaces. When an archive moves an ADDED or MODIFIED requirement from a change into `openspec/specs`, the requirement still matches its change's entry, because the lookup falls back to capability and name.
- **The gate keeps quiet.** Every CLI run gets `OPENSPEC_TELEMETRY=0` and `OPENSPEC_NO_UPDATE_CHECK=1`, so the gate neither phones home nor writes the user's global OpenSpec configuration.
- **A currency check.** `uv run poe openspec-currency` (`scripts/openspec_currency.py`, standard library) compares the pin with npm's latest version (`registry.npmjs.org`). It exits 0 when the pin is current, 1 when it is behind, and 2 when the registry cannot be read. It also reads the local `openspec --version` and the `generatedBy` stamp in `.claude/skills/openspec-*/SKILL.md`. Either one differing from the pin prints a warning that names the action (update the openspec package; regenerate with `openspec update`); neither fails the check. An absent CLI or absent skills, as in CI, are noted, not warned about. A write mode rewrites only the pin. The check is networked, so it stays out of `poe test`; L0 tests stub every source.
- **A weekly bump pull request.** `.github/workflows/openspec-currency.yml` is modelled on `model-currency.yml`. It runs the check in write mode weekly and on dispatch, and keeps one pull request from the fixed branch `openspec-currency/bump` that changes only the pin. It dispatches `ci.yml` on that branch, so the new version's findings, ratchet included, show on the pull request. Its permission model, fail-closed report check and branch protection are those of `model-currency.yml`. It uses no secret beyond `GITHUB_TOKEN` and never merges. L0 tests pin these properties for both workflows.
- **Docs.** AGENTS.md's Commands block and its spec-first paragraph say where the pin lives and name the new task. The pyproject comment keeps "the one place the OpenSpec CLI version is pinned" true by pointing at the script.
- **Unchanged:** every spec's text. No requirement is shortened in this change; the baseline records them as they are. `.claude/skills` is not regenerated here. That is the landing step, and the currency check reports it until it is done.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: one ADDED requirement, "OpenSpec version kept current". The spec gate runs one pinned OpenSpec version and fails on every error or warning except a recorded long requirement that has not grown. A currency check compares the pin with the published version, and a weekly workflow proposes the bump as a pull request that it never merges. The requirement's own text stays under 500 characters, and the details live in its scenarios.

## Impact

- New dev-side scripts: `scripts/validate_specs.py`, `scripts/openspec_currency.py`. New data: `openspec/long-requirements.json`. New workflow: `.github/workflows/openspec-currency.yml`.
- `pyproject.toml`: the `specs` task runs the script; a new `openspec-currency` task.
- Tests: `tests/unit/test_validate_specs.py` and `tests/unit/test_openspec_currency.py`, over recorded 1.14.1 JSON shapes with synthetic content in `tests/unit/data/openspec_cli/`. `tests/unit/test_currency_workflow.py` is generalized to pin both weekly workflows, and checks that no workflow rewrites the baseline. `tests/conftest.py` keeps the new CLI runner and registry fetch offline for the whole suite.
- Docs: `AGENTS.md` (Spec-first workflow, Commands).
- CI: `ci.yml`'s steps are unchanged; its comments and the spec step's name now point at `scripts/validate_specs.py`. The "Spec validation" step still calls `uv run poe specs`, which now needs network for `npx` as before, plus about 20 short CLI runs (about 5 s in parallel).
- No user-side code, shipped skill or `shared/` file changes.
