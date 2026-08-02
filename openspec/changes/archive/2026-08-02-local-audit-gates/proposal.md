# Local Audit Gates

## Why

A local run of Snyk Agent Scan (the engine behind the skills.sh Snyk audits) against the fixed skills confirmed yesterday's remediations but exposed one remaining HIGH finding: W007 insecure credential handling in proposal-lit-search, because the guided key setup has the agent receive and write the secret value into `api-keys.env`. Publishing now would predictably keep lit-search red. Beyond that blocker, the repo has no local audit capability at all — the 2026-08-02 diagnosis had to be reverse-engineered from opaque `Risk: HIGH · 2 issues` counters. The user wants regular local checks ordered before publication, with the skills.sh verdicts as post-publish confirmation.

## What Changes

- **proposal-lit-search key setup (W007 fix)**: the agent still guides the whole flow — one central `api-keys.env` at the workspace root shared by every proposal in that workspace, signup guidance, `.gitignore` coverage — but the secret value never passes through the agent. The agent creates the file with an empty `OPENALEX_API_KEY=` placeholder, the user pastes the key into the file themselves, and the agent verifies by running one search (the script reads the file mechanically). The agent never asks for, reads, echoes, or writes the key value.
- **Pre-publish gate, layer 1**: L0 audit-invariant tests (`tests/unit/test_audit_invariants.py`) freezing the patterns remediated in `harden-audit-flagged-skills`: no dynamic module loading from input, no credential lookup outside the three documented locations, no permission-mutating instructions in SKILL.md files, no cross-skill script execution, no secret-value handling instructions.
- **Pre-publish gate, layer 2**: `scripts/audit_scan.py` — wrapper running `uvx snyk-agent-scan@latest` against the repo's `skills/` staged into an isolated HOME/XDG environment (repo skills only, never the developer's real agent configs), token from `SNYK_TOKEN` or `confidential/credentials.txt`, failing on findings with risk ≥ 0.5 (calibrated 2026-08-02: risk ≤ 0.3 W011 findings exist on skills that skills.sh reports as "No issues").
- **Pre-publish gate, layer 3 (optional)**: `harness/audit_llm_preflight.py` — per-skill LLM audit against the Gen Agent Trust Hub categories via headless `claude -p` on the subscription; advisory, not part of the default gate.
- **Post-publish confirmation**: `scripts/audit_status.py` — polls the public skills.sh audit API for all eight skills, diffs against a committed `audit-baseline.json`, non-zero exit on drift; `--update` rewrites the baseline.
- **Docs**: the publish pipeline order (gates → publish → confirmation) documented in AGENTS.md and `harness/README.md`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-lit-search`: the guided-key-setup requirement changes — setup SHALL keep the secret value out of the agent's hands (placeholder file + user paste + mechanical verification), with one central workspace key file.
- `skill-packaging`: new requirements — a local security gate SHALL pass before publication, published verdicts SHALL be confirmed against a committed baseline after publication, and the remediated audit patterns SHALL be enforced by automated tests.

## Impact

- `skills/proposal-lit-search/SKILL.md` (Keys section rewrite)
- New: `tests/unit/test_audit_invariants.py`, `scripts/audit_scan.py`, `scripts/audit_status.py`, `audit-baseline.json`, `harness/audit_llm_preflight.py`
- `AGENTS.md`, `harness/README.md` (pipeline documentation)
- Dev-side scripts may assume the uv environment and Linux/macOS; user-side content unchanged except the lit-search SKILL.md prose. No new Python dependencies (stdlib + `uvx` invocation).
- Requires `SNYK_TOKEN` (free Snyk account) for layer 2; stored in `confidential/credentials.txt`.
