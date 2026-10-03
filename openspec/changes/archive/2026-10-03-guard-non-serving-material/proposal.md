## Why

Debugging a derailed Master's proposal — an empirical study of human-AI task allocation in automotive TARA that carried a CAN-bus/fuzzing sentence serving none of its research questions — surfaced two paths by which material that serves no research question reaches a proposal, and one reason neither is currently visible.

The guidance names five substance tests, and all five catch *emptiness*: delta, falsifiability, swap, method-fit, executability. A sentence that is true, specific, well-sourced and about the wrong thing passes every one of them. The swap test in particular catches text that could belong to any thesis; it is silent on text that belongs to a different one.

Two mechanisms exploit that silence:

- **Profile bleed.** `proposal-ideate` fetches a supervisor's group page and publication list to scope the session. The scope is meant to be a filter on the student's idea. Nothing states that it is not also a source: `SCOPING_SIGNALS` in the harness treats the profile's research vocabulary as *proof the fetch happened*, never as a leak, and the only scenario exercising the fetch (`ideate_scoped`) hands the model a student idea identical to the group's first listed research area — so vocabulary bleed and legitimate adoption are indistinguishable by construction.
- **The reference ratchet.** `proposal-lit-search` merges an accepted candidate into `references:`. From then on `check.py` warns `reference-uncited` while the write skill is told that deleting a reference SHALL NOT be used to silence a finding. Post-merge, the only admissible resolution is to write a sentence citing the entry — and that sentence must describe the paper, importing its vocabulary. A reference can enter the proposal but cannot leave it.

The guard that would catch both already exists, in `proposal-supervise`: a paper earns its place by the work it does in one point, and one that fits no point is dropped. It was written for supervisor-side feedback and never generalized.

This change states the rule once, applies it at both entry points, and — the actual ask — builds the tests that measure whether the skills honor it.

## What Changes

- **A sixth named substance test.** *Necessity*: every sentence, citation and technical term serves a research question, the delta, or the method; material that is true, specific and sourced still fails if removing it would not weaken the argument. Named, so the skills that cite tests by name inherit it.
- **Profile fenced as a filter.** Scoping material informs whether an idea fits; its vocabulary does not enter the seed file, the proposal text, or a literature query unless the student voiced it first. The no-idea hint path stays the single, already-specified exception.
- **The ratchet's exit opened.** A merged reference that no claim in the proposal needs may be removed and recorded in Excluded Literature. Removing it is a correct resolution, not the silencing the spec forbids — the existing prohibition narrows to its actual target.
- **Merge requires a named claim.** An entry enters `references:` only when the claim it will support can be named; otherwise it goes straight to Excluded Literature.
- **Harness coverage for all of it**, with negative controls: an adjacent-profile ideation scenario whose student idea is orthogonal to the group's areas, a partial-overlap sibling, an off-topic-reference fixture with its oracle, and a writing scenario that must resolve it by removal rather than by inventing a carrier sentence.
- **A drift guard on the substance-test names, landed first.** "The five substance tests" is written out across the guidance, four SKILL.md bodies, three spec files and two verbatim pins, and nothing checks that they agree. This is the enforcement gate: it lands before the sixth test is added, not after.

No mechanical relevance detector is added. Judging whether material serves a research question stays agent judgment over prose guidance, per the formalization boundary.

## Capabilities

### New Capabilities

None — every rule extends an existing capability.

### Modified Capabilities

- `guidance-model`: the substance tests grow from five to six with the addition of the necessity test.
- `skill-ideate`: research-group scoping gains the filter-not-a-source rule — scoping vocabulary is barred from produced files and from literature queries unless the student introduced it.
- `skill-write`: self-verification gains a correct resolution for `reference-uncited` — remove the entry and record it — narrowing the existing blanket prohibition on deleting a reference to its intended target, findings the skill is silencing rather than resolving.
- `skill-lit-search`: judged relevance becomes a merge precondition — an entry enters `references:` only when the claim it will support can be named.
- `skill-review`: the verdict is judged against six tests rather than five, and a necessity failure alone does not reach the bottom tier — non-serving material is removable in place.
- `skill-supervise`: the same count correction, and the idea-stage evidence bar explicitly excludes necessity failures from the three decisive failures it requires.
- `testing-harness`: new coverage requirements for scoping-vocabulary containment, off-topic-reference resolution, and substance-test-name consistency.

## Impact

- **Guidance**: `shared/guidelines/guidelines.md` (Substance Tests section; the Writing Rules line on irrelevant technical detail becomes the necessity test's cross-reference).
- **Skills**: `proposal-ideate`, `proposal-write`, `proposal-lit-search`, and the test-citing prose in `proposal-review` and `proposal-supervise` SKILL.md bodies. `proposal-supervise` already implements the rule and only gains its name.
- **Pins**: `tests/unit/data/pinned_sentences/proposal-review--execution-shape.txt` and `proposal-supervise--execution-shape.txt` both say "the five substance tests" and must be edited in this change.
- **Harness**: `harness/l1_checks.py` (new verdicts; `SCOPING_SIGNALS` splits into a chat-visibility signal set and a containment leak set), `harness/claude_runner.py` (new dev-runner scenarios), `tests/fixtures/` (new off-topic-reference fixture with `expected.json`).
- **Tests**: `tests/unit/` gains the substance-test-name drift guard and the L0 tests every new `verdict_*` requires.
- **Cost**: the new scenarios run on the subscription dev runner. No metered eval task is added by this change; promoting any of them to a metered L1 task is a separate, cost-gated decision.
