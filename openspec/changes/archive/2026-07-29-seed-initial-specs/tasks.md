# Tasks: seed-initial-specs

## 1. Spec authoring (deliverable of this change)

- [x] 1.1 Draft all 13 delta specs under `specs/` from rewrite.md D1–D17 and fixtures-blueprint.md
- [x] 1.2 Cross-check every locked decision D1–D17 maps to at least one requirement (or is deliberately design-level, not spec-level) — D12 (framework choice) and D17 (process) are deliberately design/process-level
- [x] 1.3 Run `openspec validate --change seed-initial-specs --strict` and fix findings

## 2. Review and merge

- [ ] 2.1 User reviews the proposal and delta specs
- [ ] 2.2 Archive the change (`openspec archive seed-initial-specs`), merging deltas into `openspec/specs/`
- [ ] 2.3 Commit the seeded specs on main
