# Tasks: registry-note-untested-models

## 1. Registry note field

- [x] 1.1 `harness/support.py`: `Model` gains `note: str = ""`; `parse_registry` reads optional `note`; `render_summary` appends a non-empty note to the row's notes after verdict-derived notes ("; "-joined)
- [x] 1.2 `harness/models.toml`: luna entry gains `note = "eval harness cannot drive this model (Azure strict tool schemas reject Inspect's tools) — untested, not a quality signal"`
- [x] 1.3 L0 tests in `tests/unit/test_support_matrix.py`: parse with/without note; render note alone on untested row; render note appended after failing-verdict notes

## 2. Quarantine invalid luna measurements

- [x] 2.1 Identify luna `.eval` files in `logs/evals/` by header model id; move them to `logs/quarantine/` (untracked, local-only)

## 3. Regenerate published tables

- [x] 3.1 `uv run poe report`: README summary (luna → ❔ untested + note), `docs/model-support.md` grid (9-task matrix incl. `review_hollow`), `shared/model-support.json`
- [x] 3.2 `python3 scripts/sync_shared.py`: refresh vendored copy in `proposal-troubleshoot`
- [x] 3.3 Sanity: luna rollup in `shared/model-support.json` reads untested; haiku row reflects logs honestly

## 4. Verify

- [x] 4.1 `uv run poe test` green; `openspec validate --all --strict` green
