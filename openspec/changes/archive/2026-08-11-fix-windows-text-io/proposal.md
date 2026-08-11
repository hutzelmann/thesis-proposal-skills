## Why

The `l0-windows` CI job — the job that exists precisely to catch "line endings, encoding
defaults, tmp_path semantics" — is red on `main` at 6201496 with seven failures. Both
causes are in test code, both are the platform-default assumptions that job was added to
find, and neither is visible from a Linux clone.

`test_title_tells.py` writes a proposal with `write_text()` and no `encoding`, so a
Windows runner encodes it as cp1252 while `check.py` reads it back as UTF-8 and dies on
`ü`. `test_identify_release.py` computes git blob hashes by feeding `git hash-object
--stdin` through a text-mode pipe, which translates `\n` to `os.linesep`: on Windows every
submitted hash covers CRLF bytes while the runner's `core.autocrlf=true` stored the blobs
LF-normalized, so a clean install resolves to zero matching files.

The shipped skill scripts are not affected — the collector in `proposal-troubleshoot`
already hashes `read_bytes()` and emits `git_blob_lf`. The defect is that the test standing
in for that collector does not.

## What Changes

- `tests/unit/test_title_tells.py` fixes `encoding="utf-8"` on every text read and write.
- `tests/unit/test_identify_release.py` hashes exact bytes (binary pipe, not `text=True`)
  and builds its fixture history from bytes with `core.autocrlf=false`, so the hashes the
  test submits and the blobs git stored are the same bytes on every host.
- A new L0 convention gate in `tests/unit/test_repo_conventions.py` fails on any
  `read_text` / `write_text` / text-mode `open` in the scanned tree that does not fix an
  encoding. Ruff cannot carry this rule: `PLW1514` is preview-only and fires only on a
  literal `Path(...)` receiver, so it flags none of this repository's call sites.
- The 98 existing call sites that violate the new gate — all under `tests/`, 70 of them in
  `test_check.py` — gain `encoding="utf-8"`. `skills/`, `scripts/` and `harness/` already
  comply.

## Capabilities

### New Capabilities

None. Test and tooling change; `skip_specs: true`.

### Modified Capabilities

None. No user-facing behavior changes: the skills, their scripts and their outputs are
untouched.

## Impact

- `tests/unit/test_title_tells.py`, `tests/unit/test_identify_release.py`,
  `tests/unit/test_repo_conventions.py`, plus the ~10 test files carrying the 98
  encoding-less call sites.
- CI: `l0-windows` returns to green; the new gate runs inside `poe test` and `poe
  test-fast` on every host.
- No change to `skills/`, `shared/`, `harness/` or any published artifact.
