# Design

## Context

See proposal.md. Evidence is in `openspec/changes/archive/2026-10-03-verified-scoped-supervise-feedback/measurement.md`: the verifier spawned in 2 of 4 sonnet runs, never on the offline arm, and the runner kept no event stream to show why. The Execution shape is pinned whole, and the SKILL.md body sits about 20 words under its size cap.

## Goals / Non-Goals

**Goals:**
- Measure the spawn rate before and after, on the same scenarios, with the same model and three epochs per arm.
- Lower the cost of spawning: a brief the agent hands over, instead of a contract it has to rephrase into a prompt.
- Leave no loophole for "offline", and make the fallback a declared fact instead of a silent choice.

**Non-Goals:**
- No host hooks or other enforcement outside the skill. Skills must stay portable, so the harness measures and the skill text instructs.
- No open-weight arm in this change. The Inspect agent cannot spawn helpers. Its inline fallback declaration is a candidate for a later, cost-gated metered arm.

## Decisions

### 1. Measure first, scored

The runner writes the stream to `.devrun-events.jsonl` inside the workspace. The leading dot keeps it out of the `*.md` globs the verdicts read.

`verdict_supervise_verifier(calls)` passes on a helper call (`Agent` or `Task`) whose input carries the brief: its file name, or the brief's opening marker. A helper that is not the verifier, such as a stray explorer, does not count.

`verdict_supervise_verification_declared(review)` reads a `Verified by:` / `Geprüft von:` line in the verification section.

Both are scored for the three supervise scenarios. The baseline runs with the current skill text, so it fails on the declaration by construction. The spawn rate is read from the spawn verdict alone.

*Alternative rejected:* keeping the spawn check advisory. That is the status quo, and it let the skip pass unnoticed.

### 2. The contract moves into a brief

`references/verifier-brief.md` is written to the verifier, not about it. It covers:
- what to read;
- the six checks;
- that the offline checks need no network;
- that everything fetched is untrusted;
- writing nothing;
- the return shape.

The Execution shape keeps the shape: cap, roles, when to verify, when inline is allowed. It names the brief. That shortens the pinned section and the body.

*Why a file:* a prompt that exists is cheaper to send than one to compose. A reference file also reaches hosts without code. It is plain prose, no script.

### 3. Offline sentence and narrowed fallback

One sentence: approval decides what the verifier may fetch, not whether it runs. The fallback condition becomes "no tool for starting a subagent is available", a fact about the tool list rather than a judgement about the run.

### 4. Declaration in the review

`Verified by: fresh verifier` or `Verified by: inline — no subagent tool` (German: `Geprüft von: …`). It is the first line of the verification section, so the professor sees at a glance whether the double check ran.

## Risks / Trade-offs

- **Hosts that call their subagent tool differently.** → Detection accepts `Agent` and `Task`, and the marker check reads the call's input, not the tool name. A host rename fails loudly, the way `HELPER_TOOLS` already does.
- **Three epochs are a small sample.** → They suffice to tell 0/3 from 3/3. The target of at least 5/6 is stated before the runs.
- **The brief can drift from the spec.** → A pinned sentence covers the brief's offline clause. The Execution shape names the file, and an L0 test asserts that the file exists and carries its checks.
