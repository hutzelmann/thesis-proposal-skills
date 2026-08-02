# Harden Audit-Flagged Skills

## Why

The skills.sh security audits (2026-07-30) leave four skills below a clean verdict: Snyk fails `proposal-lit-search` (HIGH, 2 issues) and warns on `proposal-check`, `proposal-ideate`, `proposal-import` (MEDIUM, 1 issue each); Gen Agent Trust Hub warns on `proposal-check` (COMMAND_EXECUTION, PROMPT_INJECTION) and `proposal-ideate` (COMMAND_EXECUTION, EXTERNAL_DOWNLOADS, REMOTE_CODE_EXECUTION). The flagged patterns are real static-analysis risk surfaces — instructed shell mutation of user-supplied paths, dynamic module import from CLI input, credential discovery by ancestor-directory traversal, cross-skill script execution with user-derived strings — and each can be removed without weakening the safety property it currently serves.

## What Changes

- **proposal-check**: drop the `chmod a-w` / `attrib +R` enforcement instruction (the ATH-named finding). The read-only mandate stays absolute; mechanical enforcement becomes detection: `check.py` prints a SHA-256 digest of the proposal, and non-interactive runs re-run the script last and compare digests instead of mutating file permissions.
- **proposal-ideate**: replace the embedded `python3 ../proposal-lit-search/scripts/search.py "<user terms>"` command line with delegation to the sibling skill by name (follow its SKILL.md when installed). The documented degraded fallback (agent-side read-only GET against the public scholarly APIs) stays, with an explicit untrusted-data rule.
- **proposal-lit-search scripts**: `search.py`/`snowball.py` stop resolving source modules via `importlib.import_module` on input-derived names; sources come from a static registry and unknown `--sources` names are rejected. `common.py` stops walking ancestor directories for `api-keys.env`; resolution becomes environment → `$THESIS_PROPOSAL_KEYS` file → `api-keys.env` in the working directory → user-global config file. **BREAKING** for users who relied on running scripts from a subdirectory while the key file sits at the workspace root (`$THESIS_PROPOSAL_KEYS` or the global file covers that case).
- **proposal-lit-search SKILL.md**: guided key setup keeps working but gains handling rules (write the key only into the key file, never echo or log it); fetched titles/abstracts are declared untrusted data — never instructions.
- **proposal-import**: inherits the `common.py` fix through the synchronized copy; SKILL.md gains the same untrusted-data rule for PDF content and Crossref records.
- Dev-side: AGENTS.md credential-resolution note, harness sibling staging, and L0 tests updated to match.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-lit-search`: credential resolution loses the ancestor-directory search (working directory, explicit override, and global file only); a new requirement pins source-module resolution to a static registry that rejects unknown names.
- `skill-check`: new requirement makes the read-only property explicit — the check never modifies the checked file, enforcement is digest-based detection, never file-permission mutation.
- `skill-ideate`: literature grounding is specified to go through the sibling skill's documented interface when installed (no embedded cross-skill command lines with user-derived strings), with the direct-API fallback unchanged.

## Impact

- `skills/proposal-check/SKILL.md`, `skills/proposal-check/scripts/check.py` (+ synchronized copies in proposal-import and proposal-write)
- `skills/proposal-ideate/SKILL.md`
- `skills/proposal-lit-search/SKILL.md`, `scripts/common.py`, `scripts/search.py`, `scripts/snowball.py` (+ synchronized `common.py` in proposal-import)
- `skills/proposal-import/SKILL.md`
- `AGENTS.md` (credential-resolution hard rule), `tests/unit/test_lit_common.py`, `tests/unit/test_check.py`, `harness/skill_evals.py` (stage sibling SKILL.md for ideate tasks)
- No new dependencies; user-side scripts stay stdlib-only. Verification of the audit outcome itself requires publish + re-audit on skills.sh (separate, on explicit request).
