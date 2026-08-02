# Tasks — local-audit-gates

## 1. W007 fix: guided key setup without secret hand-through

- [x] 1.1 `skills/proposal-lit-search/SKILL.md` Keys section: central workspace-root file wording; guided setup = create/update file with `OPENALEX_API_KEY=` placeholder + `.gitignore` entry, user pastes value into the file, agent verifies with one search; agent never asks for/reads/echoes/writes the value; key pasted into chat → not repeated, user redirected to the file
- [x] 1.2 L0 check that the SKILL.md keeps the no-secret-through-agent rule (part of invariant tests, task 2.1)

## 2. Layer 1 — audit-invariant tests

- [x] 2.1 `tests/unit/test_audit_invariants.py`: over shipped skill content — no `importlib.import_module`/`exec(`/`eval(`/`subprocess` in user-side scripts; no `Path.cwd().parents`/ancestor-walk credential lookup outside documented candidates; no `chmod`/`attrib`/`icacls` in SKILL.md; no `../proposal-*/scripts/` execution lines in SKILL.md; no instruction for the agent to write a secret value (placeholder-only key file edits)

## 3. Layer 2 — local scanner gate

- [x] 3.1 `scripts/audit_scan.py`: stage skills into temp `.claude/skills`, isolate HOME+XDG_CONFIG_HOME+XDG_DATA_HOME, run `uvx snyk-agent-scan@latest scan --skills --json`, map findings via reference index → skill name, print full table, exit non-zero on risk ≥ 0.5 (named constant, calibration comment), token from `SNYK_TOKEN` else `confidential/credentials.txt`
- [x] 3.2 L0 tests for the wrapper's pure parts (finding extraction, threshold, token resolution order) against a captured sample JSON — no network

## 4. Post-publish confirmation

- [x] 4.1 `scripts/audit_status.py`: fetch all eight skills from the audit API, normalize {skill: {provider: {status, riskLevel}}}, diff vs `audit-baseline.json`, per-skill/provider report, exit non-zero on drift, `--update` rewrites baseline
- [x] 4.2 Commit `audit-baseline.json` seeded from the current published verdicts
- [x] 4.3 L0 tests for normalize/diff logic against captured API sample — no network

## 5. Layer 3 — advisory LLM pre-flight

- [x] 5.1 `harness/audit_llm_preflight.py`: per skill bundle SKILL.md+scripts, one `claude -p` call (subscription; `--model` flag, default haiku), ATH-category JSON verdict, table output, non-zero when any category flags; marked advisory

## 6. Documentation

- [x] 6.1 AGENTS.md: publish pipeline (gate order → publish on request → poller) in Commands section
- [x] 6.2 `harness/README.md`: pre-flight + poller usage, calibration note, advisory status of the LLM layer

## 7. Verification

- [x] 7.1 `uv run pytest`, `uv run ruff check .`, `python3 scripts/sync_shared.py --check`, `openspec validate --all --strict` green
- [x] 7.2 Re-run `scripts/audit_scan.py`: W007 absent, no finding ≥ 0.5 on any skill
- [x] 7.3 Run `scripts/audit_status.py` against the seeded baseline: exits zero pre-publish (verdicts unchanged until a publish happens)
