## 1. Baseline before touching any skill

- [x] 1.1 Record the current mandate paragraph of each of the eight skills verbatim, to be used as the pinned fixtures in section 4 — capture before any edit so the pins are provably the pre-change text
- [x] 1.2 Run the L1/L2 eval tasks that assert skill mandates (at minimum the check, review, and ideate scenarios) and save the logs as the before-baseline; note which scenarios are expected-red so the after-run is compared like for like

## 2. Header edits across all eight skills

- [x] 2.1 Write the purpose block for each of the eight skills: one or two sentences, impersonal or third person, stating the deliverable and never restating a rule from below it. For `proposal-write`, `proposal-import`, `proposal-customize`, `proposal-publish`, and `proposal-lit-search`, whose openers are already purpose-shaped, add the user-facing outcome the opener omits rather than re-saying it
- [x] 2.2 Insert the canonical workflow line from design.md into all eight files, bolding only the containing skill's own name; `proposal-import` and `proposal-customize` bold their name inside the `Also:` clause
- [x] 2.3 Verify per file that the mandate paragraph is unchanged byte for byte and still immediately precedes the paragraph that followed it — in particular that `proposal-check`'s digest paragraph still adjoins its read-only mandate
- [x] 2.4 Confirm no file received a per-skill exception — same three blocks, same order, in all eight, with no heading interposed before any mandate

## 3. Frontmatter

- [x] 3.1 Replace `proposal-lit-search`'s frontmatter `description` with the trimmed version: no enumeration of individual scholarly databases, still third person, still stating what the skill does and when to use it
- [x] 3.2 Confirm no other skill's `description` changed, so the discovery surface moves in exactly one place

## 4. Drift guard

- [x] 4.1 Add one pinned mandate fixture per skill under `tests/unit/data/`, seeded from the text captured in 1.1
- [x] 4.2 Add `tests/unit/test_skill_header_pattern.py` asserting, per skill: workflow-line byte-identity across the set after stripping `**`; exactly one bolded name, matching the containing directory; block order with exactly one paragraph between the title and the workflow line; the mandate block equal to its pinned fixture; and nothing inserted between the mandate and the block beneath it
- [x] 4.3 Confirm each assertion actually fails when violated — reword one workflow line, bold a sibling's name, add a second preamble paragraph, and alter one mandate, checking the failure message names the file and the violated rule each time; revert the four probes afterwards
- [x] 4.4 Confirm the test finds all eight skills rather than silently globbing zero files

## 5. Contributor documentation

- [x] 5.1 State the header pattern in `AGENTS.md` — the three blocks, their order, the byte-identical workflow line, and the rule that adding a ninth skill updates every existing skill's workflow line

## 6. Verification

- [x] 6.1 `uv run pytest` green
- [x] 6.2 `uv run ruff check .` clean
- [x] 6.3 `python3 scripts/sync_shared.py --check` clean — expected untouched, since no shared source or generated copy is edited
- [x] 6.4 `openspec validate --all --strict` passing
- [x] 6.5 Read each of the eight rendered openings end to end as a person would, checking that no purpose block reads as a paraphrase of the mandate below it

## 7. After-run and reporting

- [x] 7.1 Re-run the same eval tasks as 1.2 with the same models and compare against the before-baseline
- [x] 7.2 Report the results including any regression, paying specific attention to the review scenario's structural-complaint assertion, which design.md names as the weakest point of the pattern
- [x] 7.3 State plainly what remains outside our control: the site-generated summary line, the absent package-level description slot, and unknown re-indexing timing
