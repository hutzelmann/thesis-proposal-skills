# Tasks — harden-audit-flagged-skills

## 1. proposal-check: digest-based read-only enforcement

- [x] 1.1 `check.py`: print a `digest: sha256:<hex>` line for the checked file in the report header
- [x] 1.2 `SKILL.md`: replace the `chmod`/`attrib` instruction with the re-run-and-compare-digest procedure for non-interactive runs; keep the absolute read-only mandate
- [x] 1.3 L0 tests: digest line present, matches file content, changes when the file changes; existing oracles unaffected

## 2. proposal-lit-search: static registry + narrowed credential lookup

- [x] 2.1 `search.py`: static imports + literal source registry; validate `--sources` against it, abort with valid-name list on unknown names
- [x] 2.2 `snowball.py`: same registry pattern, drop `importlib` (including the crossref enrichment import)
- [x] 2.3 `common.py`: `key_file_candidates` = `$THESIS_PROPOSAL_KEYS` file → cwd `api-keys.env` → global file (no ancestor walk); update `KEY_LOCATIONS` text
- [x] 2.4 `SKILL.md`: update Keys section (no parent-directory claim, key-handling rules: write only into the key file, never echo/log); add untrusted-data rule for fetched content
- [x] 2.5 L0 tests: replace subdirectory-walk test with subdirectory-does-not-resolve; add unknown-source rejection test

## 3. proposal-ideate: sibling-interface grounding

- [x] 3.1 `SKILL.md`: replace embedded cross-skill command with delegation to `../proposal-lit-search/SKILL.md` when installed; keep documented API fallback with untrusted-data rule

## 4. proposal-import: synced copy + untrusted-data rule

- [x] 4.1 `SKILL.md`: add untrusted-data rule for PDF content and Crossref records
- [x] 4.2 Run `python3 scripts/sync_shared.py` (propagates fixed `common.py` and digest-bearing `check.py` into import/write)

## 5. Dev-side alignment

- [x] 5.1 `AGENTS.md`: update credential-resolution hard rule to the narrowed order
- [x] 5.2 `harness/skill_evals.py`: stage the sibling's `SKILL.md` in `lit_search_sibling()` so ideate evals exercise the delegation path
- [x] 5.3 Docs mentioning parent-directory key lookup (README / docs/getting-started.md) updated if present

## 6. Verification

- [x] 6.1 `uv run pytest`, `uv run ruff check .`, `python3 scripts/sync_shared.py --check`, `openspec validate --all --strict` all green
- [x] 6.2 Run affected evals once: `check_report` and one ideate task via Inspect/OpenRouter; record outcomes
- [x] 6.3 State plainly in the final report that audit verdicts remain unverified until publish + re-audit (user-triggered)
