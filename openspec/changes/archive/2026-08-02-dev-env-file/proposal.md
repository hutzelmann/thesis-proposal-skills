# Dev Env File

## Why

Developer credentials currently live in the untracked `confidential/` directory (`credentials.txt`, a bespoke `Name: value` format that has already caused one accidental value display) and are consumed ad hoc: `scripts/audit_scan.py` parses that file directly, and eval runs require a manually exported `OPENROUTER_API_KEY`. The user wants `confidential/` minimized — especially for keys — replaced by a standard workspace env file with a committed template and documentation, so a new developer has a proper starting point.

## What Changes

- New committed `.env.example`: every dev-side key (`SNYK_TOKEN`, `OPENROUTER_API_KEY`, `OPENALEX_API_KEY`, `CONTACT_EMAIL`) with an empty value and a comment naming what it is for and where to obtain it.
- `.env` (gitignored, standard `KEY=VALUE`) becomes the single local store for dev credentials; existing values migrated out of `confidential/credentials.txt`, which nothing references afterwards.
- `scripts/audit_scan.py` token resolution becomes environment → repo-root `.env` (drops the `credentials.txt` parser); tests updated.
- Metered eval invocations documented as `uv run --env-file .env inspect eval …` (uv-native loading; no new dependency, nothing breaks on a fresh clone without `.env`).
- AGENTS.md credentials rule and `harness/README.md` updated: `.env` for dev keys, `confidential/` for real proposals only.

This is dev-side tooling and documentation only — user-side skills and their `api-keys.env` mechanism are untouched — so the change declares `skip_specs`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — `skip_specs: true`: no spec-level behavior changes)

## Impact

- New: `.env.example`; local-only: `.env`
- `.gitignore` (+`.env`), `scripts/audit_scan.py`, `tests/unit/test_audit_tooling.py`, `AGENTS.md`, `harness/README.md`
- `confidential/credentials.txt` stays on disk but unreferenced; deleting it is the user's call
