# Tasks: implement-lit-search

## 1. Foundation

- [x] 1.1 `common.py`: HTTP + politeness + retry, CSL normalization, dedupe, key generation, CSL-YAML emission
- [x] 1.2 Six source clients per D-LS-1 contract, each with a canned real response sample under `tests/unit/data/`

## 2. Orchestration

- [x] 2.1 `search.py` (keyword mode: federate available sources, merge, dedupe, emit CSL-YAML)
- [x] 2.2 `snowball.py` (seed DOIs → references + citations via graph-capable sources, same merge path)

## 3. Skill & packaging

- [x] 3.1 `SKILL.md`: modes, agent relevance judgment, key-upgrade guidance, degradation reporting, merge-into-proposal rules
- [x] 3.2 Extend sync map: vendor scripts into `proposal-ideate/scripts/`; run sync

## 4. Tests

- [x] 4.1 L0 offline tests: parsers on canned samples, dedupe/key-gen, orchestrator merge logic
- [x] 4.2 Live smoke behind `live` marker (deselected by default); run once manually
- [x] 4.3 `uv run pytest` green; sync check green; commit
