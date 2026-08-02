## Context

See proposal.md — Why. Two facts shape the approach, both established by inspecting skills.sh (July 2026): the package page at `skills.sh/hutzelmann/thesis-proposal-skills` shows only a skill table with install counts, and each skill page renders that skill's `SKILL.md` truncated behind a "Show more". No page on that site renders the repository README, and no page inspected there (`anthropics/frontend-design`, `mattpocock/skills`, our own) contains a single image. GitHub is therefore the README's only reader, and it renders `<details>`/`<summary>` natively.

`openspec` has no command that removes a capability; the documented mechanism is a delta whose `## REMOVED Requirements` covers every requirement in the spec.

## Goals / Non-Goals

**Goals:**
- Demo content survives in a form every markdown renderer shows, at a fraction of the vertical cost.
- Collapsed state carries information — the three summary lines are the workflow, not decoration.
- `docs/demo/` shrinks to what still has a job: the audit trail.

**Non-Goals:**
- Improving how the skills read on skills.sh (separate concern, separate change — the `SKILL.md` files are agent instructions first, and editing them risks L1/L2 eval regressions).
- Rewriting git history to purge the PNG blobs. They leave the working tree; ~500 KB of history is not worth a rewrite.

## Decisions

**Three separate `<details>` blocks, not one.** Each collapsed summary names its beat, so an unexpanded README still shows `1 · A vague anecdote becomes a research question` / `2 · Literature, verified — not invented` / `3 · Drafted, checked, published`. One combined spoiler hides the workflow behind a single click; three visible-but-open blockquotes cost ~20 lines that most visitors will not read. Three collapsed lines is the only arrangement where the unexpanded state is itself informative.

**Prose blockquotes with speaker labels, not a fenced terminal block.** A fenced block reproduces the screenshots' texture faithfully and is nearly free to generate, but it renders as undifferentiated monospace and hides which skill did what. Labelling each answer with the skill that produced it (`proposal-ideate`, `proposal-lit-search`, …) makes the demo double as an illustration of the skill table below it.

**Retire the render pipeline rather than port it.** `transcript.jsonl` + `replay.py` existed because the images were derived artifacts that could drift from their source. Once the README text is the demo, the source and the artifact are the same file, and a generator plus a drift test would guard a block that changes about once a year. `harvest.log` stays: it is the only thing proving the papers and excerpts came from a real session, which the surviving authenticity requirement demands.

**Demo covers `proposal-write`.** The current shot3 jumps from literature search to check, skipping the skill that actually writes the proposal. Text costs nothing per beat, so beat 3 runs write → check → publish.

**Capability removal via a full REMOVED delta.** `demo-recording`'s four requirements are each removed with Reason and Migration. Whether `openspec archive` deletes `openspec/specs/demo-recording/` or leaves an empty shell is unverified — the repository has no prior capability removal to learn from. Handled at archive time (see Risks), not guessed at now.

## Risks / Trade-offs

- **Archive may leave an empty `demo-recording` spec** → After `openspec archive`, run `openspec validate --all --strict` and inspect `openspec/specs/demo-recording/`; if the CLI leaves a husk, resolve it with the CLI's own output rather than hand-deleting spec folders.
- **A visitor who never clicks sees no demo content** → Accepted, and the reason the summary lines carry the workflow narrative. The alternative (a visible teaser above the spoilers) was considered and dropped as reintroducing bulk.
- **Deleting `transcript.jsonl` loses the curated condensation** → The condensed text moves into `README.md`; `harvest.log` retains the raw source it was condensed from, so nothing becomes untraceable.
- **`<details>` is HTML, not markdown** → GitHub renders it; renderers that do not will show the quoted text inline, which degrades to Variant "everything visible" rather than to broken output.
