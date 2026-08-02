# Design — dev-env-file

## Context

See proposal.md — Why. Constraints: no new Python dependency for env loading; a fresh clone without `.env` must keep `uv run pytest` and every other default command working; secret values never printed while migrating.

## Goals / Non-Goals

**Goals**: one standard, documented place for dev keys; zero references to `confidential/credentials.txt` left in code or docs.

**Non-Goals**: touching the user-side `api-keys.env` mechanism (separate product feature, spec-governed); deleting `confidential/` content (user's call); auto-loading `.env` into every command.

## Decisions

### D1: uv-native loading, explicitly per command — no global auto-load
Metered eval runs use `uv run --env-file .env …`. Rejected: `UV_ENV_FILE=.env` in `.claude/settings.json` env — uv fails the run when the named file is missing, which would break every `uv run` on a fresh clone and in CI; a broken default is worse than one extra flag on the two commands that need keys.

### D2: scripts that need a key read `.env` themselves as fallback
`audit_scan.py` resolves `SNYK_TOKEN` from the environment first, then parses repo-root `.env` (`KEY=VALUE`, `#` comments — same narrow parser shape as the user-side key files). Keeps `uv run python scripts/audit_scan.py` working with no flag and no wrapper.

### D3: `.env.example` is the developer onboarding artifact
Committed, all keys present with empty values, each with a one-line comment: purpose + where to obtain (app.snyk.io, openrouter.ai, openalex.org). Setup instruction everywhere: `cp .env.example .env`, fill in.

## Risks / Trade-offs

- [Two env conventions in one repo: dev `.env` vs user-side `api-keys.env`] → deliberate; they serve different audiences and the user-side one is spec-frozen. Docs name the distinction.
- [Secrets in two places during transition] → migration copies values once, docs point only to `.env`; removing `credentials.txt` is left to the user since the file may hold non-key content.

## Migration Plan

Values copied blind (no display) from `confidential/credentials.txt` into `.env` in this change; single commit on main; rollback = revert (local `.env` unaffected by git).
