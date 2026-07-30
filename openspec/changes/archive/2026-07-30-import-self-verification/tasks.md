## 1. Ship the check with the skill

- [x] 1.1 Add the check script to the sync map, materialized into `skills/proposal-import/scripts/`
- [x] 1.2 Add the structured skeleton to the sync map, materialized into `skills/proposal-import/references/`, since the script resolves it relative to its own location
- [x] 1.3 Run `python3 scripts/sync_shared.py` and confirm the vendored script runs from its new home against a fixture

## 2. Verify before reporting

- [x] 2.1 Replace the wrap-up's "recommend running check" with running it, fixing the reported errors, and re-running until only source-caused findings remain
- [x] 2.2 Name the findings that must not be fixed by inventing content — the reference-count shortfall above all — and require reporting them instead
- [x] 2.3 State plainly that this is import verifying its own fresh output, not the check skill running: that skill is read-only and never edits

## 3. Harness

- [x] 3.1 Point the eval scorer at the skill's own vendored check instead of the staged `tools/` path, and drop that staging

## 4. Verification

- [x] 4.1 `uv run pytest` green
- [x] 4.2 `uv run ruff check .` clean
- [x] 4.3 `python3 scripts/sync_shared.py --check` clean
- [x] 4.4 `openspec validate --all --strict` passes
- [x] 4.5 Measured: **10 PASS / 1 FAIL over 11 runs** on this build, against a 2/4 baseline. Caveat recorded honestly — only 1 of 6 probed runs shows the model actually running the check, so the gain comes from the wrap-up prose (which enumerates the fixable defects) rather than from the verification step firing. The vendored script is present in every workspace; one run wrongly reported it missing. The single failure produced no file; across 11 runs no run was observed both claiming a file and lacking one
