# Tasks: Streamline Key File Lookup

## 1. Resolution logic

- [x] 1.1 Add `key_file_candidates()` to `skills/proposal-lit-search/scripts/common.py`: `$THESIS_PROPOSAL_KEYS`, then `api-keys.env` in cwd and ancestors with the walk bounded at `$HOME`, then `~/.config/thesis-proposal/api-keys.env`
- [x] 1.2 Split file parsing into `_read_key(path, name)` returning `None` for a missing/unreadable file or an undefined key
- [x] 1.3 Rewrite `get_key()` to check the environment, then each candidate in turn, so resolution is per key and files compose
- [x] 1.4 Export `KEY_FILE_ENV` and a `KEY_LOCATIONS` description string for error messages

## 2. Error message

- [x] 2.1 Rewrite the `openalex._api_key()` failure to name the environment variable and every consulted location alongside the signup URL

## 3. Tests

- [x] 3.1 Extend `test_get_key_env_then_file` to clear `$THESIS_PROPOSAL_KEYS` so the ambient environment cannot leak into the assertion
- [x] 3.2 Add `test_get_key_found_from_workspace_subdirectory`: key file at the workspace root, cwd three levels down, key still resolves
- [x] 3.3 Add `test_get_key_explicit_path_overrides_and_resolves_per_key`: override wins for the key it defines, workspace file supplies the key it does not

## 4. Documentation

- [x] 4.1 State the resolution order in `skills/proposal-lit-search/SKILL.md` and keep the guided-setup instruction pointing at the workspace root
- [x] 4.2 Update the credentials line in `AGENTS.md`
- [x] 4.3 Note subfolder inheritance and the global file in `docs/getting-started.md`

## 5. Wrap up

- [x] 5.1 `python3 scripts/sync_shared.py` to regenerate the vendored `proposal-import` copy
- [x] 5.2 `uv run ruff check .` and `uv run pytest tests/unit` green
- [x] 5.3 `openspec validate --all --strict`, then archive and commit
