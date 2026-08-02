# Tasks — dev-env-file

## 1. Env files

- [x] 1.1 `.env.example` committed: SNYK_TOKEN, OPENROUTER_API_KEY, OPENALEX_API_KEY, CONTACT_EMAIL — empty values, per-key comment (purpose + where to obtain)
- [x] 1.2 `.gitignore`: add `.env`
- [x] 1.3 Migrate existing values from `confidential/credentials.txt` into `.env` without displaying them; verify `.env` is ignored by git

## 2. Consumers

- [x] 2.1 `scripts/audit_scan.py`: `snyk_token()` = env → repo-root `.env` (KEY=VALUE parser); no `credentials.txt` reference left
- [x] 2.2 `tests/unit/test_audit_tooling.py`: token tests use `.env` format

## 3. Documentation

- [x] 3.1 AGENTS.md: credentials rule → `.env` (copy from `.env.example`); `confidential/` = real proposals only
- [x] 3.2 `harness/README.md`: `cp .env.example .env` onboarding; eval invocation `uv run --env-file .env inspect eval …`; audit gate reads `.env` itself
- [x] 3.3 Repo grep: zero remaining references to `credentials.txt` in code and docs (memory files excluded)

## 4. Verification

- [x] 4.1 `uv run pytest`, `uv run ruff check .`, `python3 scripts/sync_shared.py --check`, `openspec validate --all --strict` green
- [x] 4.2 `uv run python scripts/audit_scan.py --help`-level smoke: token resolves from `.env` (no SNYK_TOKEN in env)
