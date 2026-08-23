## 1. Extract the sources

- [x] 1.1 Create `shared/blocks/voice.md` from the current voice block, verbatim
- [x] 1.2 Create `shared/blocks/report-offer.md` from the current offer paragraph, verbatim
- [x] 1.3 Create `shared/blocks/workflow.md` from the current workflow line with the marked
      name reduced to plain form, so the source states the set once
- [x] 1.4 Confirm each source reproduces its current per-skill rendering exactly (diff the
      rendered result against every skill before wiring anything up)

## 2. Region materialization in sync_shared.py

- [x] 2.1 Add an opening-region locator: split body after frontmatter into blank-line
      separated blocks up to the first `## `, returning their spans
- [x] 2.2 Add a closing-section locator: the first paragraph after `## When this run fails`
- [x] 2.3 Render the workflow line per skill, wrapping the owning skill's own name in `**`
- [x] 2.4 Write the three regions into each destination `SKILL.md`, preserving everything
      outside them byte-for-byte, and excluding `proposal-troubleshoot` from the offer
- [x] 2.5 Fail loudly when an anchor does not resolve (missing section, too few opening
      blocks) instead of inserting at a guessed position
- [x] 2.6 Extend `--check` to report a drifted region through the existing `OUT OF SYNC` path

## 3. Re-point the tests

- [x] 3.1 `test_skill_header_pattern.py`: replace the `VOICE_BLOCK` literal with a read of
      `shared/blocks/voice.md`; keep every positional, length, and uniqueness assertion
- [x] 3.2 `test_skill_header_pattern.py`: assert the workflow line equals the rendered source
      for that skill, keeping the marked-name-is-own-name assertion
- [x] 3.3 `test_report_offer.py`: replace the embedded offer literal with a read of
      `shared/blocks/report-offer.md`; keep both halves (present exactly once in its own
      closing section; the reporter never offers itself)
- [x] 3.4 Confirm no mandate, mandate-successor, or pinned-sentence assertion was touched

## 4. Sync coverage

- [x] 4.1 `test_sync.py`: rendering a source into a skill and re-reading it round-trips
- [x] 4.2 `test_sync.py`: sync is idempotent — a second run changes no bytes
- [x] 4.3 `test_sync.py`: a mutated region is reported by `--check` with a non-zero exit
- [x] 4.4 `test_sync.py`: a skill-specific paragraph following the offer survives a sync
- [x] 4.5 `test_sync.py`: an unresolvable anchor raises rather than writing

## 5. Verify

- [x] 5.1 Run the sync; `git diff --stat` across `skills/*/SKILL.md` MUST be empty
- [x] 5.2 Reword `shared/blocks/voice.md`, sync, confirm exactly ten files change, revert
- [x] 5.3 `uv run poe test` green
- [x] 5.4 `uv run poe specs` green
- [x] 5.5 Update `AGENTS.md` — the skill header pattern section names where the shared blocks
      live and that they are materialized, not retyped
