# Tasks

## 1. Spec and docs

- [x] 1.1 Delta: MODIFY "Isolated child environment". Scope it to the routing rig's children and the dev runner's model-under-test child, name the judge's governing requirement, and add the scenario "Judge child outside this requirement". All earlier scenarios stay. Verify: `openspec validate scope-isolated-env-requirement --strict`.
- [x] 1.2 `harness/README.md`, "Billing, exit statuses and the smoke": an ambient run keeps effort and session settings; an isolated run gets `routing.isolated_env`; the smoke's protection is the isolated allowlist. Verify: `grep -n "isolated_env" harness/README.md`.

## 2. Verification

- [x] 2.1 `uv run poe test` and `uv run poe specs` are green.
- [x] 2.2 Archive through the CLI with spec sync, and check the synced requirement text.
