<!-- What does this PR change, and why? One or two sentences is enough. -->

## Checklist

- [ ] Behavior change → an OpenSpec change folder (proposal, spec deltas, tasks) is included; pure tooling/docs → the change declares `skip_specs: true`
- [ ] `uv run poe test` is green (pytest + ruff + generated-copy drift)
- [ ] Edits touch sync sources (`shared/`, the source skill), not the generated copies `scripts/sync_shared.py` writes
- [ ] New or changed fixtures are synthetic (`Erika Musterfrau`, matriculation `00000000`) and proposal fixtures carry a calibrated `expected.json`
- [ ] Nothing private — no real proposals, real names, or credentials
