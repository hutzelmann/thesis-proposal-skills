# Tasks: implement-import-ref-validation

## 1. Implementation

- [x] 1.1 validate_refs.py (extraction, DOI verify, title-match identify, report + CSL output)
- [x] 1.2 Sync map: common.py + crossref.py into proposal-import; run sync
- [x] 1.3 SKILL.md validation step + offline degradation

## 2. Verification

- [x] 2.1 Unit tests: typo'd DOI, incomplete-entry completion, offline path
- [x] 2.2 Live smoke on a fixture; pytest green; archive; commit
