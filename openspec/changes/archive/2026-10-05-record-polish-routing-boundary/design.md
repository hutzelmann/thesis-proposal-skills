# Design

## Context

See proposal.md, Why. The owned-trigger check (`tests/unit/test_skill_frontmatter.py`, `test_owned_trigger_terms_have_exactly_one_claimant`) matches each owned phrase as a lowercase substring of every description. It fails when a skill other than the owner contains the phrase. The README model-support region is written by `harness/report.py`. In it, `support.render_summary` appends a registry `note` after the verdict-derived notes. The note reaches neither `docs/model-support.md` nor `shared/model-support.json`.

## Goals / Non-Goals

**Goals**
- Make the write/review readiness split visible in the table the packaging requirement names, and fail L0 if a later description crosses it.
- Put the haiku polish-routing finding where a haiku user reads model guidance, through the generator's own input.

**Non-goals**
- No routing or dev-runner measurement. The appended sentence stays unmeasured until the next subscription routing run.
- No change to `proposal-review`'s description. It already owns the question and names nothing it declines here.
- No new L0 test. The existing claimant check covers the new entry.

## Decisions

**D1. The owned phrase is "get it ready for a supervisor".** It is the clause the earlier change added to write's description, and it is absent from review's ("ready for their supervisor", "before handing it to a supervisor"). Owning it means no other description may later reuse the request-to-change wording. Review's phrases stay review's.
- Alternative: own "ready for a supervisor". Rejected, because it would also match a future review wording such as "whether it is ready for a supervisor", which is the question review should be free to own.
- Alternative: own "to change the proposal's text". Rejected, because it names the intent without the contested moment, so it would not record the boundary with review.

**D2. Write's description declines the readiness verdict and names review.** The requirement applies: write's description now reaches into a situation review owns, so write has to say which part it does not take. The appended sentence copies `proposal-check`'s existing pattern ("Not content feedback — for whether the argument holds, use proposal-review."), so the suite keeps a single way of declining. It holds no owned phrase of any skill.

**D3. The haiku note goes into `harness/models.toml`, not into README prose.** The model-support region is generated, so a hand edit would be overwritten by the next `poe report`. Outside the region, the note would sit apart from the haiku row it qualifies. The registry note is the mechanism the testing-harness spec provides for a caveat on a model's row. The note names its instrument and date ("0/3 on the routing rig, 2026-10-05"), so a reader does not mistake it for a matrix cell under the table's 2026-08-10 header. The TOML comment above it records both halves of the measurement (dev runner 3/3 with one skill installed, rig 0/3 with the full set) and points to `measurement.md`.

**D4. Regenerate the README by running `poe report`, never by typing the row.** The eval logs are gitignored and exist only in the main checkout, so the report ran from the worktree with `--log-dir` pointed at them, read-only. The run read the same 10 logs (newest 2026-08-10) that produced the shipped table. The only diff was the haiku row. `docs/model-support.md` and `shared/model-support.json` came out byte-identical.

## Risks / Trade-offs

- [The appended sentence could move routing, which no measurement covers] → It sends only the readiness question to review. The collision cases on both sides of the boundary, `write-polish-collision` and `review-ready-collision`, catch a theft in either direction at the next sonnet routing run on the subscription.
- [`harness/models.toml` carries uncommitted roster work in the main checkout] → The hunk is a comment and one `note` line inside the haiku entry. A textual conflict, if one occurs at merge time, is confined to that entry.
- [The note outlives its cause once haiku routes polish passes on the full set] → The note is registry data with a dated measurement. Removing it is a one-line edit followed by `poe report`.
