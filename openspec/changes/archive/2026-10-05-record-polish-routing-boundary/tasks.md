# Tasks

## 1. Trigger boundary

- [x] 1.1 Add "get it ready for a supervisor" → `proposal-write` to `tests/unit/data/trigger_terms.json` beside "polishing pass", plus a `_comment` line recording the split by intent (write changes the text, review answers whether it is ready); verify by grep that write's description contains the phrase and no other description does, and that `uv run pytest tests/unit/test_skill_frontmatter.py` passes
- [x] 1.2 Append "Not a readiness verdict — for whether it is ready, use proposal-review." to `proposal-write`'s description, keeping the earlier wording byte-identical; verify the description is 475 characters (budget 500) and the frontmatter tests pass, including the combined-metadata budget

## 2. Haiku model note

- [x] 2.1 Add a `note` to the haiku entry in `harness/models.toml`, with a comment citing `openspec/changes/archive/2026-10-05-route-polish-to-write/measurement.md`: dev runner 3/3 with only write installed, routing rig 0/3 with the full set, so polishing and editing passes need sonnet or opus; verify `uv run pytest tests/unit/test_support_matrix.py tests/unit/test_model_ids.py` passes
- [x] 2.2 Regenerate the report with `uv run poe report --log-dir <main checkout>/logs/evals` (read-only, the logs behind the shipped table); verify the README diff is the haiku row only, and that `docs/model-support.md` and `shared/model-support.json` are unchanged (`git diff --stat`)

## 3. Gate

- [x] 3.1 `uv run poe test` and `uv run poe specs` exit 0, and `python3 scripts/sync_shared.py --check` reports the generated copies in sync
