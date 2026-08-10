## 1. Dataset

- [x] 1.1 Write `harness/routing_cases.toml` with the case schema (utterance, expected skill, kind, language) and a header comment stating what each kind is for
- [x] 1.2 Author 30 cases: each `proposal-*` skill gets one `canonical`, one `oblique`, one `collision` case; collision cases target the measured overlaps (supervisor, feedback, review, idea)
- [x] 1.3 Author 4 `negative` cases whose expected route is none
- [x] 1.4 Author 6 German cases on the highest-traffic skills (check, review, write, ideate, publish, supervise)

## 2. Pure core

- [x] 2.1 `harness/routing.py`: `route_from_events(events)` returning the first `proposal-*` skill invocation, `None` when unrouted, tolerating up to `MAX_PREPARATORY_CALLS` non-skill tool calls
- [x] 2.2 `classify(cases, results)` producing the expected×selected matrix plus per-kind pass counts, treating errors as a category distinct from unrouted
- [x] 2.3 Named constants for the preparatory-call bound and per-case timeout, each with a comment stating they are judgment, not derivation
- [x] 2.4 Dataset loader validating the composition rule (every skill has all three kinds; negatives and German cases present)

## 3. Offline tests

- [x] 3.1 Save the two 2026-08-10 probe captures as fixtures under `tests/unit/data/routing_streams/`
- [x] 3.2 `tests/unit/test_routing.py`: route extraction over the fixtures — routed, unrouted, preparatory-calls-then-route, chained-sibling-ignored, unparseable-input-fails-loudly
- [x] 3.3 Tests for `classify` including the negative-case verdict and the error/unrouted distinction
- [x] 3.4 Test that the shipped dataset satisfies the composition rule and that every expected skill names an installed skill directory

## 4. Runner

- [x] 4.1 Isolated environment setup: temp `CLAUDE_CONFIG_DIR` with empty settings, credentials reached by symlink, refuse to run (with the exact `ln -s` in the message) instead of falling back to the ambient config
- [x] 4.2 Workspace staging: all ten skills installed under `<ws>/.claude/skills/`, one fixture proposal present so utterances can name a real file
- [x] 4.3 Spawn `claude -p` with `--output-format stream-json --verbose --allowed-tools Skill Read Glob`, read events incrementally, terminate on route
- [x] 4.4 Verify once that the isolated config actually blocks a disallowed tool; record the result in a comment whichever way it goes
- [x] 4.5 `main(argv)` with `--model`, `--kind`, `--epochs`, `--jobs` (default 4), `--case`; per-case errors recorded, never retried silently

## 5. Reporting

- [x] 5.1 Persist raw per-case results to `logs/routing/<run>.json` including model, epochs, and the `skills/` git revision
- [x] 5.2 Generate `docs/skill-routing.md` — confusion matrix, per-kind summary, the utterances behind each mis-route, run provenance
- [x] 5.3 Register the `routing` poe task in `pyproject.toml`

## 6. Baseline and documentation

- [x] 6.1 Run the sweep on sonnet (1 epoch, 3 on the collision kind) and commit the resulting `docs/skill-routing.md` as the pre-fix baseline
- [x] 6.2 Document the rig in `harness/README.md`: what it measures, why it is Claude-only, why it is not in CI, how to set up the isolated config
- [x] 6.3 `uv run poe test` green; `openspec validate --all --strict` green
