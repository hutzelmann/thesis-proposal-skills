## Why

The workspace override file grew one flat, hand-named key at a time: `min_references`, `page_limit`, `timeline_detail`, `required_sections`, `forbidden_sections`. None of them matches where the value actually lives in `structure.json` — `page_limit` sits under `length`, `timeline_detail` under `timeline.default_detail` — so every new override needs a naming decision, and the mapping between the two files exists only inside `check.py`.

That was survivable while every knob was a scalar. The next change makes the methodology set configurable, and a methodology is a keyed collection of structured branches. Adding it as one more hand-named flat key is not possible, so the file is about to gain a nested entry whatever happens. Either it gains exactly one nested entry among five flat ones, or the mapping question gets answered once.

Answering it once: **a workspace override key is the same key path as in `structure.json`**. There is no second rule, no hand-named alias, and no legacy form accepted alongside.

## What Changes

- **BREAKING**: every workspace override key moves to its structure path. `min_references` → `[references] min_count`, `page_limit` → `[length] page_limit`, `timeline_detail` → `[timeline] detail`, `required_sections` → `[sections] required`, `forbidden_sections` → `[forbidden] heading_patterns`. The research-question bounds become overridable at `[research_questions] min_count` / `max_count` at the same time, which they were not before.
- **BREAKING**: `structure.json` is normalized so that mirroring produces a file with no flat outliers: `min_references` → `references.min_count`, `forbidden_heading_patterns` / `work_plan_heading_patterns` / `confidentiality_patterns` → the `forbidden` table, `todo_marker` → `todo.marker`, `timeline.default_detail` → `timeline.detail` (the workspace sets the effective value, so "default" was wrong in the name of the thing being overridden).
- No compatibility shim. A workspace file using an old key is **reported as an error naming the new location**, not silently ignored — breaking loudly is the point of breaking at all.
- The merge rule itself is unchanged and now applies uniformly: a user key wins per key, a list value replaces the default list entirely.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the workspace override file's key shape becomes the structure key path, and the research-question bounds join the overridable set.
- `skill-check`: an override key from the pre-migration vocabulary is reported as a configuration error naming its replacement.
- `skill-customize`: the skill writes and explains the nested key shape.

## Impact

- `shared/structure.json` and its five generated copies — key paths only, no values change.
- `skills/proposal-check/scripts/check.py` and its three vendored copies — every structure and override read.
- `shared/guidelines/guidelines.md`, `skills/proposal-customize/SKILL.md` — the documented key names and the example TOML block.
- `tests/fixtures/w02-override-workspace/guidelines.md` — the only fixture carrying an override block.
- Existing user workspaces break by design; the error message carries the migration.
