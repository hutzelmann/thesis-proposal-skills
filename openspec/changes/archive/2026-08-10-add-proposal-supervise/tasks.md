# Tasks: add-proposal-supervise

## 1. Skill

- [x] 1.1 Create `skills/proposal-supervise/SKILL.md`: frontmatter, four-block opening (purpose, ten-skill workflow line, voice block, mandate), normalization section (sibling-import delegation + inline fallback per D1), findings + curation section (D2), verdict phrasing map (D5), package assembly (D3), disclosure + getting-started quoting (D4), closing report-offer block.
- [x] 1.2 Create `skills/proposal-supervise/references/getting-started.md` (en + de sections, skills.sh pointer, continue-with-proposal-write instruction).
- [x] 1.3 Add `SYNC_MAP` entries (guidelines.md, structure.json → references; check.py → scripts) and run `python3 scripts/sync_shared.py`.

## 2. Set-wide machinery

- [x] 2.1 Update the workflow line in all nine existing SKILL.md files to name ten skills (own name bolded per file); update supervise's own line consistently.
- [x] 2.2 Update the workflow-line/voice-block constants and rosters in `tests/unit/test_skill_header_pattern.py`; pin the supervise mandate at `tests/unit/data/skill_mandates/proposal-supervise.txt`.
- [x] 2.3 Ensure the report-offer roster (`tests/unit/test_report_offer.py`) covers supervise.

## 3. Testing

- [x] 3.1 Add synthetic raw-submission fixture(s): pasted-email fragment with fake personal data (`Erika Musterfrau`, matriculation `00000000`), following the existing fixture conventions.
- [x] 3.2 Add verdict functions to `harness/l1_checks.py` (letter exists, ≤5 points, verdict tier, personal-data absence, skill pointers resolve) with L0 unit tests for each.
- [x] 3.3 Add the supervise L1 task and adapter scorers to `harness/skill_evals.py`; extend `tests/unit/test_eval_wiring.py` with the new scorer names.

## 4. Docs and verification

- [x] 4.1 Sweep README.md, AGENTS.md, harness/README.md, and any other doc naming the skill count or listing skills — all must list ten including proposal-supervise; matrix/model-support explicitly untested for supervise.
- [x] 4.2 Run `uv run poe test` and `uv run poe specs`; both green.
