## 1. Skill text

- [x] 1.1 Add the future-work entry-path bullet to `## Entry paths` in `skills/proposal-ideate/SKILL.md`, after the supervisor's-topic-list bullet: selective reading of the closing chapters, the reason the rest stays unread, the three path-specific Socratic obligations, and the no-PDF fallback.
- [x] 1.2 Add the source-thesis clause to `## Ending — seeding` in the same file: publicly accessible source thesis becomes a starter `references` entry, otherwise it is named in the notes file only, and no publication metadata is invented for an unpublished thesis.

## 2. Verify

- [x] 2.1 Run `uv run poe test` — the header-pattern, mandate-pin, pinned-sentence and drift checks must stay green (the edit touches neither the opening blocks nor the closing offer).
- [x] 2.2 Run `uv run poe specs` (`openspec validate --all --strict`).
