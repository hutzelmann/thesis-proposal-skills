## Why

Every CI run currently carries the annotation that `actions/checkout@v4` and
`astral-sh/setup-uv@v5` target Node.js 20 and are being forced onto Node.js 24. The
forcing is a temporary courtesy: when the runners stop supplying it, checkout fails before
any job in this workflow reaches a test, and all four jobs go with it.

Bumping while the shim still works means the bump is verified by a green run rather than
discovered by a red one.

## What Changes

- `actions/checkout@v4` → `@v7` in all four jobs.
- `astral-sh/setup-uv@v5` → `@v9.0.0` in the two jobs that use it. The exact patch version
  is required, not a style choice: setup-uv stopped publishing major and minor tags at v8
  as a supply-chain measure, so `@v9` does not resolve.
- The container images stay pinned where they are. `pandoc/typst` already runs the newest
  `3.10.0.0-ubuntu`, and moving `pandoc/extra` from `3.9.0.2` to `3.10.0.0` would put the
  same pandoc in both, which contradicts the workflow's own comment that the differing
  versions widen coverage.

## Capabilities

### New Capabilities

None. CI configuration only; `skip_specs: true`.

### Modified Capabilities

None. No skill, script, or published artifact changes.

## Impact

- `.github/workflows/ci.yml` only.
- Verified by the CI run on the resulting push; no local command can exercise it.
