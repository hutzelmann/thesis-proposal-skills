# Design: supervise-verdict-deferral

## Context

See proposal.md for motivation. The dev runs that surfaced the flapping are recorded in the archived `add-supervise-dev-scenario` change. Constraints that shape the approach: the professor is the interactive user of this skill (chat questions are cheap and natural); eval/dev runs are single-turn and headless (a mid-run question stalls them); the review skill's philosophy — never soften a hollow-core judgement — must survive on the professor-facing side; the mandate and its pinned copy should not change (the no-commitment/draft-only mandate is untouched by this design).

## Goals / Non-Goals

**Goals:**
- The harshest student-facing outcome is either evidence-clear or explicitly professor-chosen — never an automatic coin-flip on a borderline.
- Bottom-tier letters follow the wise-feedback shape: standard + anchored assurance + feed-forward.
- Headless runs stay single-turn.

**Non-Goals:**
- No change to the review skill or its three-tier vocabulary; the reframing is supervise-letter-only.
- No autonomous literature fetching; the starter-literature step is offer-and-approve.
- No new L1 scorers; the existing five adapt (tier pattern only).

## Decisions

**D1 — Evidence bar as instruction, not code.** The ≥3-decisive-failures bar and per-test irreparability statement live in SKILL.md prose; no script computes them (substance tests are semantic). The deterministic harness only checks that *some* tier is stated. Tier *correctness* on borderline material is L2-rubric territory at matrix time, as already noted in the model-support plan.

**D2 — Deferral is a plain chat question.** No tooling: the skill's instructions tell the agent to present the split evidence (failed tests, uncertain tests, one finding excerpt each) and the three options, and to wait. Default on no-answer or explicit decline: needs-revision (in doubt, for the student). This keeps the skill portable across agents with no dependency on any specific question-UI.

**D3 — Student-facing tier rename, professor-side vocabulary unchanged.** Letter tiers: ready / needs revision / idea stage ("not yet at the proposal stage"; de "Ideenphase — noch kein Exposé"). `<slug>-review.md` keeps ready / needs revision / no viable thesis core verbatim. The tier check (`SUPERVISE_TIER_PATTERN`) gains `idea stage` / `not yet a proposal` / `ideenphase` / `noch kein exposé` and keeps the old phrases so pre-rename letters and blunt phrasings still count.

**D4 — Starter literature via sibling, postscript placement.** When outcome is idea-stage/borderline and `../proposal-lit-search/` is installed, offer once in chat; on accept, follow the sibling's verification rules (real lookups only) and add a short "where this conversation already is" list — two or three entries, title + venue + year — to the letter after the strengths block. Declined or sibling missing: no mention in the letter at all.

**D5 — Headless pre-answer.** The Inspect task request and the dev-runner request append: "If the verdict is borderline, do not ask me — take the needs-revision path." This exercises the default rule (D2) rather than bypassing the feature, and matches the ideate_scoped precedent of pre-answering interactive steps in single-turn runs.

## Risks / Trade-offs

- [Letter loses the blunt phrase; students may under-read severity] → the idea-stage letter still says plainly that a proposal cannot be built from the material as-is and that the next step is ideation, not revision; only the framing changes, not the content.
- [Deferral question annoys on frequently-borderline material] → the bar means genuinely clear cases never ask; if practice shows too many questions, the professor can say "stop asking, always pick needs-revision" and the skill respects it for the session.
- [Tier pattern grows permissive; a vague letter could pass on "idea stage" said in passing] → the pattern still only scans the letter's opening five lines, and tier correctness remains L2 territory (D1).
- [Starter-literature offer adds a second question in the same run] → both questions only fire on bottom/borderline outcomes, and the literature offer is one yes/no; acceptable for the case where the professor most wants to help.
