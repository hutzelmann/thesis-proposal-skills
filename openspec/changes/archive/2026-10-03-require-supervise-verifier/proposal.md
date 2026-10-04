# Proposal

## Why

`verified-scoped-supervise-feedback` made one fresh verifier of the finished feedback part of every supervise run where the host can start helpers. The dev runs showed the rule is not followed reliably: the verifier spawned in only 2 of 4 sonnet runs. The offline s01 arm skipped it both times, saying "I did not launch a verifier agent. I ran its checks myself inline", although the headless host offers `Task` and `Workflow`.

Offline is where the skip costs most. The largest error classes of the session that motivated the verifier need no network at all: misreadings of the student's text, contradictions, review jargon, and asks that inflate the workload.

Three likely causes:
- the verifier's remit reads as being mostly about papers and norms;
- the inline fallback reads as an option rather than a last resort;
- spawning a subagent means composing its prompt from a long paragraph.

The runner kept no event stream, so the model's reasoning could not be inspected.

## What Changes

- **Measure first.**
  - The dev runner saves each run's event stream into the workspace.
  - A new scored verdict for the supervise scenarios fails a run that spawns no verifier on a host that can start one; it is no longer advisory for these scenarios.
  - A second verdict checks that the review declares who verified.
  - A three-epoch baseline per arm runs before any skill change.
- **A ready-to-send verifier brief.** `skills/proposal-supervise/references/verifier-brief.md` carries the verifier's inputs, its six checks, the untrusted-data rule and its return shape. The skill tells the agent to start one subagent with that brief. The contract moves out of the pinned Execution shape, which then states only the shape.
- **Offline does not exempt.** Approval decides what the verifier may fetch, not whether it runs.
- **A narrow, declared fallback.** Inline checking only where no tool for starting a subagent exists. The review's verification section states "Verified by: fresh verifier" or "Verified by: inline — no subagent tool" (German: "Geprüft von: …").
- **Re-measure** with three epochs per arm. The target is the verifier spawning in at least 5 of 6 runs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-supervise`: Single-context execution. The verifier runs offline too, works from a shipped brief, and the fallback is narrowed and declared in the review.
- `testing-harness`: Dev-runner cost and helper-agent telemetry. The event stream is saved, and the supervise scenarios score the verifier spawn and the declaration.

## Impact

- **Skill:** `skills/proposal-supervise/SKILL.md` (Execution shape, Verify before hand-over) and the new `references/verifier-brief.md`.
- **Pins:** `tests/unit/data/pinned_sentences/proposal-supervise--execution-shape.txt`, plus a new pin for the offline sentence.
- **Harness:** `harness/l1_checks.py` (two verdicts) and `harness/claude_runner.py` (event capture, scoring), with L0 tests.
- **Cost:** about 12 dev runs on the subscription, no metered spend. The added skill text is about −80 words in net, which eases the body-size cap.
