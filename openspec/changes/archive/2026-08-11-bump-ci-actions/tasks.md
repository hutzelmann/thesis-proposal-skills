## 1. The bump

- [x] 1.1 `.github/workflows/ci.yml`: `actions/checkout@v4` → `@v7` in all four jobs.
- [x] 1.2 `.github/workflows/ci.yml`: `astral-sh/setup-uv@v5` → `@v9.0.0` in `l0` and
      `l0-windows`, with a comment naming why this one pin is exact — no major or minor
      tags are published from v8 on.

## 2. Verification

- [x] 2.1 `uv run poe test` and `openspec validate --all --strict` still green — the
      workflow is not covered by either, so this only confirms nothing else moved.
- [x] 2.2 Commit, push, and confirm all four jobs pass with no Node.js 20 annotation left
      in the run before archiving.
