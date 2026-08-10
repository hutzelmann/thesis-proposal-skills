# Proposal: registry-note-untested-models

## Why

The published model-support table shows `gpt-5.6-luna` as "❌ not recommended — fails: proposal-write", but the recorded cause is that the eval harness cannot drive the model at all: the account's data policy pins luna to Azure, and Azure's strict tool-schema validation rejects Inspect's `text_editor` tool before the model does any work. That is an invalid measurement, not a measured failure — presenting it as ❌ misleads readers choosing a model, and `proposal-troubleshoot`'s rung 1 (which reads the vendored `model-support.json`) tells luna users their model is the confirmed cause and stops, when the honest answer is "unevaluated". The registry currently has no way to carry such a caveat, so the reason would vanish into archived change notes the moment the cells were blanked.

## What Changes

- `harness/models.toml` gains an optional per-model `note` string; `support.py` parses it (defaulting to empty) and appends it to the Notes column of the rendered README summary row, after any verdict-derived notes.
- `gpt-5.6-luna`'s eval logs are quarantined out of `logs/evals/` (moved to `logs/quarantine/`, local-only — logs are untracked) so its cells classify `untested` instead of `fail`.
- `gpt-5.6-luna`'s registry entry carries a note stating the harness cannot drive it (Azure strict tool schemas) and that untested is not a quality signal.
- README summary, `docs/model-support.md`, and `shared/model-support.json` are regenerated with `poe report`; the vendored copy in `proposal-troubleshoot` is refreshed with `scripts/sync_shared.py`. The regeneration also picks up the current 9-task matrix (adds the `review_hollow` column missing since 2026-08-10).
- L0 tests cover note parsing (present, absent) and note rendering (alone, appended after verdict notes).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: "Pinned model registry" gains the optional per-model note; "Generated model-support report" requires the note to surface in the summary table so an untested-by-incompatibility model is never presented as bare untested or as failing.

## Impact

- `harness/models.toml` — luna entry gains `note`
- `harness/support.py` — `Model` dataclass, `parse_registry`, `render_summary`
- `tests/unit/test_support_matrix.py` — parse/render cases
- `README.md`, `docs/model-support.md`, `shared/model-support.json`, `skills/proposal-troubleshoot/references/model-support.json` — regenerated
- `logs/evals/` → `logs/quarantine/` (untracked, local)
