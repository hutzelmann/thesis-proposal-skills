## Context

See proposal.md — Why. The evidence is one real run: the professor accepted the end-of-run offer, got a standalone "where this conversation already is" block, and asked twice more until each paper sat inside the point it served — one showing that a research question was already answered in the literature, one showing the worked shape of a falsifiable question, one confirming that the student's own framing is one the field already uses. That final shape is the target; the shipped step cannot reach it because the papers arrive after the points are written. (Nothing here names the submission or its domain; the synthetic test strings use a domain of their own.)

Constraints that shape the approach:

- `proposal-supervise` runs in one context; following the lit-search sibling in that context is explicitly not a helper (execution-shape section, pinned). The search therefore runs in the main agent, and the execution-shape pin stays untouched.
- The feedback is plain text pasted into a channel that renders nothing, so a DOI URL is the only locator that survives; the closing note already carries a URL.
- Fixed wordings in this skill are pinned (`tests/unit/data/pinned_sentences/`) so a reword is a paired diff; verdict functions live in `harness/l1_checks.py` with an L0 test each (`test_repo_conventions.py` enforces it); `evals.json` is a generated projection.
- Headless runs (Inspect task, dev runner) pre-answer every interactive stop in the request; the Inspect sandbox stages no lit-search sibling for supervise, and the dev runner stages one only in the scenario built to observe the network path.

## Goals / Non-Goals

**Goals:**

- One consent question, up front, that a professor can answer once and forget.
- The tier is a property of the submission, not of the network.
- Literature that does work inside a point; nothing appended.
- A hallucinated citation cannot reach a student through this skill without breaking a pinned rule.
- The regression the professor disliked (a standalone list) is caught offline.

**Non-Goals:**

- Student-side `proposal-review` stays offline; the student runs `proposal-lit-search` themselves.
- No standing workspace approval (`guidelines.md` override) — the professor asked for an approval, not a setting; can be a later change.
- No live-network supervise eval task; the network path is observed through a subscription dev run, not a metered matrix cell.
- No change to the lit-search sibling, `shared/`, or the fixture corpus.

## Decisions

**D1 — Approval at run start, not before curation.** Alternative: ask only when a literature finding exists, after the review. Rejected: it adds a second mid-run stop (the borderline deferral is already one), and the professor named the timing ("initial approval"). Cost: the question is asked even when the run ends ready-tier; the wording says the search is conditional on the findings, and an invoking message that asks for literature is treated as the answer, so a professor who always wants it never sees the question.

**D2 — Tier before search; the search never moves the tier.** Alternative: let a found survey count as delta-test evidence. Rejected: reproducibility (same submission, same tier, with or without network or approval) and the asymmetry already in the spec — the harshest tier needs clear evidence, and a hasty lookup claiming "already done" on the wrong paper is exactly the kind of evidence to keep out of the tier. Papers sharpen wording and evidence of points and review findings only. Order in SKILL.md: check → substance tests → tier (+ deferral) → search → review file → feedback.

**D3 — Trigger is the finding.** Alternative: keep idea-stage/borderline only. Rejected: a needs-revision proposal grounded in two blog posts is the common case and the one where "read X before you narrow" helps most. Ready tier has no such finding, so it stays lean without a special rule.

**D4 — Fixed approval wording, pinned.** Alternative: free wording constrained by the spec. Rejected: free wording drifts into "want literature?" and hides the network access; a pin gives L0 something to hold. The sentence names the sibling, read-only network, two or three papers, and that declining means no literature and no repeat.

**D5 — Verification sentence pinned.** "No paper enters the feedback, the review, or the notes file without a record returned in this run by the lit-search scripts or their read-only fallback — a paper you know from memory included; an unverifiable paper stays out." This is the security-weight sentence of the change (a fabricated citation in student-facing text is the worst outcome), so it joins the pinned set like the untrusted-data sentences.

**D6 — Weaving as a placement rule, not a template.** No standalone block; ≤3 papers; each inside the point or strengths block where it does one of four jobs (already answered / worked shape / confirms the student's framing / maps thin coverage); a fitting-nowhere paper is dropped to Excluded Literature. First mention full (authors, year, title, venue, DOI URL), later Author Year. The step-4 "Starter literature" block is removed, not kept as fallback — the fallback is the list the professor rejected.

**D7 — Notes file is the professor-side record; the proposal stays the submission.** Merging into `references:` would misrepresent what the student handed in. The notes file exists or is created before any literature is recorded: import seeds it, the inline normalization path now seeds it like import does, and the as-is path (a submission that already arrived in standard format) creates it on first record — the sibling's never-create rule governs the sibling's own runs, and the prose says so. Woven entries go under a `Feedback Literature` section so runs look alike; rejections use the Excluded Literature section the notes file already has by convention. Only DOI-bearing candidates qualify, because the DOI is both the locator a plain-text channel can carry and the token the verdict can check.

**D8 — Verdict design (`verdict_supervise_literature(feedback, notes)`).** Offline, text-only, on the produced feedback plus the notes file:
- Extract DOIs from `https://doi.org/<doi>` URLs in the feedback (case-insensitive, punctuation-trimmed; a balanced parenthesis pair is part of the DOI, as in Elsevier's, while the unbalanced `)` of a markdown link ends it).
- No DOI → pass ("no literature cited") — literature is conditional, so absence is not a failure.
- More than three distinct DOIs → fail (cap).
- Each DOI's block must be prose that carries the citation, not a list. The block is the blank-line-separated paragraph when the DOI's line is the paragraph's only DOI-bearing line; when several DOI-bearing lines share a paragraph — a list written without blank lines — each line is its own block. Fail when the DOI sits on a bulleted line (`-`, `*`, `+`, `•`, `–`), or when the block — numbered-point markers stripped — carries fewer than 40 words, the shape of a bare citation line. A woven point runs well past that; the rejected list's entries sat around 25 words each. (The review found the first version summing a heading and three plain entries past the floor; judging per line when a paragraph holds several DOI lines closes that.)
- Each DOI must appear in the notes file as a DOI token (not a substring — a cited DOI must not pass on a longer recorded one it prefixes) → else fail ("not recorded in the notes file"). This is the offline proxy for the verification bar: a paper that reached the feedback without going through the scripts is one the run never logged. It cannot prove existence; that stays with the pinned sentence and the sibling's scripts.
- Explanation names the offending DOI and the rule.
The verdict does not parse the strengths block by heading (language-dependent); the prose-length rule covers it.

**D9 — Wiring.** New scorer `supervise_l1_literature` (name keeps the `l1` marker the classifier reads) reads `ws/*-feedback.md` and `ws/*.notes.md`; the Inspect task appends it; `EXPECTED_SCORERS` grows by one. The dev runner's aggregate gains the literature verdict: `feedback_files()` also globs `*.notes.md`, and the aggregate scans the notes for personal data as well — the spec forbids student identity in any artifact the skill writes, so the wider scan is the spec's own rule, not a new one, and the existing L0 test that leaks a name through a notes-shaped file keeps passing for the same reason. Both headless requests gain "Do not look up literature." beside the borderline pre-answer — the sandbox has no sibling anyway, the sentence makes the no-search path explicit rather than incidental. The dev runner also gains `supervise_literature`, the network-path twin of `supervise_feedback` (import and lit-search staged as siblings, approval granted in the request); it is the observation point the Non-Goals name — subscription-side, never a metered task — and the Inspect scorer keeps its feedback-only personal-data scope while the dev runner's aggregate also covers the notes it stages.

**D10 — Description and routing unchanged.** The frontmatter description is under the routing measurement; the new behaviour is conditional and internal, so the description keeps its wording and routing stays comparable.

## Risks / Trade-offs

- [Feedback length grows (900 → 1300 words in the real run)] → hard cap of three papers, points stay three to five, first-mention-only full citation; the professor edits a draft.
- [A run fabricates a DOI and also logs it in the notes] → the offline verdict cannot catch it; the pinned verification sentence and the sibling's script-only rule are the defence, and the dev run with the sibling staged is the observation point.
- [The approval question becomes a nag on every run] → single sentence, once, implicit grant from the invoking message, skipped without the sibling.
- [Prose-length heuristic misfires on a legitimately short point carrying a DOI] → 40 words is below any point that also names a direction and a skill pointer; the threshold is a named constant with its reason in the docstring.
- [Search drifts (the real run's first query landed in a neighbouring field)] → retarget-once rule and the per-finding query phrasing; a finding without a fitting paper stays literature-free rather than getting a near-miss.
- [German feedback with English paper titles] → titles are quoted as published; only the framing sentence is German. No rule needed.

## Migration Plan

None for users: the skill installs as a whole from `main`. Archive merges the deltas into `openspec/specs/`.

## Open Questions

None that change specs, approach, or tasks. Whether a standing workspace approval belongs in `proposal-customize` is a separate change if the professor asks for it.
