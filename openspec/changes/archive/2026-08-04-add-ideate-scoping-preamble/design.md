# Design — add-ideate-scoping-preamble

## Context

See proposal.md — Why. Constraints that shape the approach:

- `proposal-ideate` ships no scripts; the whole skill is SKILL.md prose. The change stays prose-only.
- The skill-header pattern (Purpose block, byte-identical workflow line, pinned mandate) is enforced by `tests/unit/test_skill_header_pattern.py`; the mandate paragraph must stay untouched or its pinned copy moves in the same change.
- The literature-grounding section already documents read-only fetches against public scholarly APIs (Crossref, DBLP, arXiv) with an untrusted-data framing — the pattern to reuse, not reinvent.
- Guidelines forbid supervisor names and the study program inside a proposal, so the seed file can never carry scoping data.
- `check.py::load_overrides` returns `{}` for a `guidelines.md` without a TOML block — a prose-only file is valid, so ideate may create one.
- `claude -p` is one-shot: a runner scenario cannot hold a dialogue, so the scenario request must pre-answer the preamble.
- `tests/unit/test_fixture_oracles.py` only binds fixture dirs that contain `expected.json`; a non-proposal fixture without one breaks nothing.

## Goals / Non-Goals

**Goals:**

- One administrative scoping exchange at session start, bounded so the Socratic hard rule stays absolute in between the bookends.
- Deterministic, low-surface fetch behavior reusing the endpoint families the skill already documents.
- Test coverage that pins the injection framing and the clean-seed rule without metered spend.

**Non-Goals:**

- No inspect L1 task in this change (deferred until the prose stabilizes).
- No stubbing of DBLP in the runner scenario (the endpoint is dblp.org, not redirectable) — the scenario exercises the URL path.
- No changes to proposal-customize; the workspace `guidelines.md` prose section is already its documented surface.
- No scoping enforcement in check.py — fit is a judgment call, deliberately outside the mechanical checker (formalization boundary).

## Decisions

1. **Placement in SKILL.md**: new `## Scoping preamble` section directly after the three opening blocks (Purpose, workflow line, mandate paragraph) and before `## The one hard rule`. The hard-rule section is reworded to scope the rule to idea content between the two administrative bookends; the ending section gains the once-offered scoping note. Mandate stays byte-identical — no pinned-copy churn. Alternative (folding the preamble into the ending section's carve-out text) rejected: the preamble runs at the opposite end of the session and deserves its own section for the fetch and filter rules.

2. **DBLP route**: reuse the already-documented `https://dblp.org/search/publ/api?q=<professor name>&format=json` with a small result count (~10) instead of adding the author-disambiguation API plus per-person page fetch. One endpoint family, no new API shape for the security audit to assess. Trade-off: common names return mixed publications — the skill judges relevance and cross-checks against the fetched group page when one exists.

3. **Fetch mechanics**: the agent's own fetch tools with read-only GETs, exactly like literature grounding. No script, no new dependency. Fetched page and DBLP titles are quoted and judged, never followed as instructions — same sentence pattern the literature section already uses, so the audit sees one consistent posture.

4. **Persistence mechanics**: on acceptance, append a short prose paragraph to the workspace `guidelines.md` (create the file prose-only if absent — tolerated by `load_overrides`, verified). The TOML block is never touched; a broken TOML block found in the file is left alone and mentioned to the user. Alternative (structured TOML key for scoping) rejected: scoping is soft semantic context, and the formalization boundary keeps semantic guidance in prose.

5. **Generous threshold, operationalized**: the SKILL.md instruction is "when in doubt, it fits" — steering plus a single chat-only warning fires only when an idea sits clearly outside both the group's publication profile and the study program. No fit trace in the seed file, ever.

6. **Fixture**: `tests/fixtures/g01-research-group/` — a synthetic group page (`group.html`, fake "Systems Software Group", obviously fake staff names) and a synthetic DBLP response (`dblp.json`) for potential future use; no `expected.json` (not a proposal fixture); `tests/fixtures/README.md` documents the new prefix.

7. **Runner scenario `ideate_scoped`**: `claude_runner.py` starts a stdlib `http.server` on an ephemeral localhost port serving the fixture page and passes the URL inside a single-turn request that pre-answers the preamble (program + group URL + an in-scope idea sketch). Verdict `verdict_ideate_scoped` in `l1_checks.py` — a pure function per the testing-harness spec — asserts: a seed file exists, it contains no supervisor name / group name / study program, and the chat shows the group's topics informed the session. A matching L0 unit test covers the verdict logic without a model.

## Risks / Trade-offs

- [Prompt injection via fetched group page] → untrusted-data framing identical to literature grounding; fetched content only informs scoping, never instructions; covered by the audit gate after implementation.
- [DBLP name ambiguity pollutes scoping] → small result count, relevance judged, cross-checked against the group page; generous threshold means a noisy profile still rarely triggers warnings.
- [Runner scenario flake if the model declines the localhost fetch] → verdict keys on preamble handling and seed cleanliness, with the fetch-influence assertion kept loose (topic words in chat, not fetch logs).
- [Preamble adds session weight] → one question, one fetch round, ~10 titles; the skill's "keep the dialogue light" ethos is written into the new section.
- [Stale or thin group pages misrepresent interests] → DBLP titles carry recency; when both signals are thin the skill says scoping is weak instead of over-filtering.

## Migration Plan

Prose-only change to one skill; no data, no APIs, no rollout order. Rollback = revert the commit. `scripts/audit_scan.py` runs after implementation because the change adds outbound fetch targets; publish stays explicit-request only.
