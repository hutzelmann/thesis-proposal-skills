## 1. Rewrite the rule

- [x] 1.1 Replace the **Git** bullet in `AGENTS.md` (Hard rules) with the invariant form: `main` is the release channel and what lands there is live; unfinished work stays off `main` and its location is unspecified; commit per completed OpenSpec change; re-run `python3 scripts/sync_shared.py` after a merge that touched `shared/`, with CI's `--check` as the backstop; no push and no skills.sh publish without explicit request.
- [x] 1.2 Verify no other tracked file restates the removed mechanism: `grep -rniE "work directly on .?main|no branches|worktree" --include="*.md" .` returns only the archived history and this change folder.

## 2. Verify

- [x] 2.1 `uv run poe test` green (the rule is prose, so this confirms the edit broke no pinned sentence or drift check).
- [x] 2.2 `uv run poe specs` green (`openspec validate --all --strict` accepts the zero-delta change via `skip_specs: true`).
