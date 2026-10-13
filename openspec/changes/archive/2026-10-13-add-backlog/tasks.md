# Tasks

## 1. Backlog

- [x] 1.1 Write `docs/backlog.md` with the eleven entries from the 2026-10-13 audit (citation support and the citation-scope bar merged), each with its evidence pointer (an archived change where one exists). Verify: every archive path it names exists (`ls`), and it names neither the private proposals directory nor any real proposal.
- [x] 1.2 Leave out the judge-allowlist unification, which `harness/claude_cli.py` already does through `host_login.allowlisted_env`.

## 2. Gate

- [x] 2.1 `uv run poe test` and `uv run poe specs` green; `openspec validate add-backlog --strict` valid.
