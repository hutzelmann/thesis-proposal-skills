## Why

The import L1 verdict asserts that the produced text contains `"\n---"` and the word `"references"`, and calls that "standard format". A dev-runner artifact that passed it carries six mechanical errors: the metadata block is never closed, `references:` is a YAML mapping instead of a CSL list, the methodology is invented rather than drawn from the closed set, and the research questions are not an ordered list. The eval therefore proves that import strips personal data and converts citations — nothing about whether it produces a usable proposal.

The skill shares the blame. It *states* the format contract in prose but never *shows* it, and it names the methodology section as `Methodology for Research: <Methodology>` without saying that the methodology comes from a closed set of four. Every defect above is a gap the instructions leave open.

Strengthening the verdict alone would leave a red eval with no path to green; fixing the skill alone would leave the defect undetected next time. Both, in one change.

## What Changes

- The import verdict runs the mechanical check over the produced file and fails on its errors, matching how the draft verdict already judges `write_from_seed`. Only the reference-count error is tolerated, because import must never invent sources the document did not carry.
- Both runners supply the check script to that verdict: the dev runner already has it, and the metered task stages it at a path the scorer uses but the model under test is not told about, so the scenario still tests import rather than import-plus-check.
- The import skill shows the exact output shape it must produce — a worked metadata block with a CSL-YAML reference list — rather than only describing it.
- The import skill states the closed methodology set, the ordered-list form of research questions, the concrete reference-key shape, and that "et al." is never part of an author name.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: the shared-verdict requirement gains the rule that a verdict asserting standard format SHALL do so by running the mechanical check rather than by inspecting substrings.
- `skill-import`: the import requirement gains the conformance obligation — output that satisfies the mechanical check apart from information the source did not carry — and the specific structural elements the skill must get right.

## Impact

- `harness/l1_checks.py`: `verdict_import()` takes check output and reuses `disallowed_errors()`.
- `harness/claude_runner.py`: passes its existing check run into the verdict.
- `harness/skill_evals.py`: `import_messy` stages the check script and the structure data under a scorer-only path; `import_l1()` runs it against the produced file.
- `skills/proposal-import/SKILL.md`: worked output example plus the four structural rules.
- `tests/unit/test_harness_helpers.py`: verdict tests extended for the check-driven failure and tolerance.
- The import eval is expected to fail until the skill's output conforms; that is the point of the change, and the dev runner makes iterating on it free.
