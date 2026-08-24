# Tasks — eval-definition-isolation

## 1. Fix

- [x] 1.1 `claude_runner.py` stage(): copy skill and siblings with `ignore=shutil.ignore_patterns("evals")`
- [x] 1.2 `routing.py`: extract `install_skills(skill_home)` with the same ignore; rig calls it

## 2. Guard

- [x] 2.1 L0 test: dev-runner `stage()` and routing `install_skills()` produce skill homes with no `evals` directory, `SKILL.md` and `scripts/` present

## 3. Docs

- [x] 3.1 README divergence table: eval input files referenced by name, not copied into `evals/files/` (fixtures live in the repo beside their oracles)

## 4. Verify

- [x] 4.1 `uv run poe test` and `openspec validate --all --strict` green
