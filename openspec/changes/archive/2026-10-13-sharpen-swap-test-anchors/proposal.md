## Why

The maintainer asked for one more check in supervisor feedback (2026-10-13): "If the proposal names tools or specific domains, there need to be a clear thing being specific to this tool/domain. If the tool is replacable or the specific topic not adding anything, this should be raised to the student as a blocker and require further refinement."

The guidance has no rule for this today:

- **The swap test is about prose.** It catches text that would stay plausible after swapping the topic noun. A proposal whose title and research questions name a framework, platform or application domain reads as specific, so it passes the swap test as written, even when any comparable framework would serve and nothing in the research depends on the name.
- **The title alarm sees only the title, and never blocks.** It raises a tool carried as the instrument, but it is an optional refinement, and it looks only at the title. The same name in a research question or the contribution is checked by nothing.
- **Nothing fails a specific-sounding name.** A judge has no named question to ask of it, so a decorative name is never reported as a substance failure and never blocks.

A specific-sounding name with nothing behind it is generic text that does not look generic, so it belongs under the swap test. It can only be caught by judgement: no proper-noun matcher can tell an object of study from a convenience.

## What Changes

- **The swap test covers named choices** (`shared/guidelines/guidelines.md`, `## Substance Tests`). No seventh test is added. The swap test's bullet gains one clause, and a paragraph below the list makes it checkable:
  - **Scope**: every tool, system, platform or application domain the thesis names in its own claims. These are the title, the purpose statement that closes the introduction, the research focus and research questions, and the contribution section's statements of what the thesis adds (its goals, gap, significance and deliverable). Names of prior work, tools chosen to carry out the method, and domains named only to motivate the topic are not judged by this test.
  - **Pass**: the research depends on the name. It is the object of study, it imposes constraints that shape the method, it supplies data or access no comparable alternative offers, or it is the case the proposal argues suits its research questions (typical, critical or revelatory, as the Case Study contract asks). A comparison of named tools passes by design. A Bachelor's close that evaluates something in a named setting and claims its result for that setting passes.
  - **Fail**: replace the name with a comparable alternative, or drop it, and compare the claims, not the nouns. If the same claim still stands with only the noun changed, the name is decorative and the swap test fails. The repair is to state the dependence or to generalize the claim to the name's class.
- **A decorative name blocks.** A swap-test failure is already a proposal blocker under `## Readiness`. The Readiness section now names this case among the blockers. It also says that a name in the title that fails the swap test blocks as a swap-test failure, not as a title finding. The title alarm itself still never blocks.
- **`proposal-review`**: holds every name in scope to the swap test and says so explicitly. A failure is a blocker that cites the swap test, locates the name, says what stays unchanged under replacement, and gives both repairs. When the name stands in the title, the blocker also carries the title rule's certificate consequence and one to three alternatives, so the same name is not reported twice.
- **`proposal-supervise`**: the review file names the check. A decorative name becomes a numbered blocker point, written as a question to the student: what in the thesis would change if a comparable alternative stood in its place? The point gives both directions. The test's name stays out of the feedback, as all review vocabulary does.
- **`proposal-ideate`**: when the student's idea carries a named tool, system, platform or domain, the skill asks once, Socratically, what about the thesis would change if a comparable one stood in its place. The skill never names the alternative itself. A name the student cannot anchor does not count as a concrete specific. The open question goes to the notes file. Seeding is not blocked.
- **`proposal-write`**: never introduces a name the material gives no dependence for. An author's name without one is kept, and a `[TODO: …]` marker asks for the dependence where the contribution would state it. A student's spoken reason for keeping a named technology in the title is written into the proposal, not left in chat.
- **Evals for both directions**: a minimal pair built from the readiness control's text (f28). Both fixtures name the same fictitious agent framework in the title and the research questions, and both are check-clean.
  - `f31-decorative-tool`: the contribution makes a claim about configurations in general, so the name is decorative and a swap-test blocker is expected.
  - `f32-tool-as-object`: the same text, except that the contribution close makes the framework's own default configuration the object, so no swap-test blocker is expected.
  - Four dev-runner scenarios run review and supervise over each fixture, with pure verdict functions and L0 tests. An L2 criterion grades each review scenario.
  - The existing fixture oracles are audited for names this rule now judges. f21, for one, carries a platform in its title that its research questions never use.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: changed requirements:
  - "Substance tests": the swap test covers named choices (scope, pass anchors, the replacement check, repair) and gains scenarios.
  - "Readiness classification": a decorative name is a blocker, and a title name that fails the swap test blocks as that test's failure.
  - "Title alarm is raised and justified, never silently blocked": the alarm itself stays non-blocking beside the swap test.
- `skill-review`: changed and new requirements:
  - new "Named choices held to the swap test";
  - "Title assessed as its own dimension": a title name that fails the swap test is reported once, as the swap-test blocker.
- `skill-supervise`: new requirement "Decorative names reach the student as a question".
- `skill-ideate`: new requirement "Named choices questioned Socratically".
- `skill-write`: "Substance gate" covers decorative names, and a stated reason for keeping a name is written into the proposal.
- `testing-harness`: new requirement "Swap-test anchor coverage" (minimal pair, four dev-runner scenarios, verdicts, L2 criterion, corpus audit).

## Impact

- **Guidance**: `shared/guidelines/guidelines.md`: the Substance Tests bullet and a new paragraph, a Readiness sentence and blocker list, and a Title sentence. The copies under `skills/*/references/guidelines.md` are regenerated by `scripts/sync_shared.py`. `shared/structure.json` and `check.py` do not change, because the check is semantic and stays out of structured data.
- **Skills**: `skills/proposal-review/SKILL.md`, `skills/proposal-supervise/SKILL.md`, `skills/proposal-ideate/SKILL.md`, `skills/proposal-write/SKILL.md`, with one new pinned sentence each under `tests/unit/data/pinned_sentences/`. Mandates, the purpose, workflow and voice blocks, and the execution-shape pins stay unchanged.
- **Harness**: `harness/l1_checks.py` (new verdicts), `harness/claude_runner.py` (four scenarios), `harness/l2_rubrics.py` (two criteria on `readiness.txt`) and `harness/README.md`. No Inspect task is registered. Inspect twins and matrix cells are a separate, cost-gated decision.
- **Fixtures**: new `tests/fixtures/f31-decorative-tool/` and `f32-tool-as-object/`, each with `expected.json`, and the `tests/fixtures/README.md` entries. Updated `semantic` lines go to the existing oracles the audit finds affected; no `check` block changes.
- **Docs**: one clause in the README's "Substance is judged" paragraph.
- **Routing**: unaffected. No skill description changes.
- **Cost**: the verification runs on the subscription dev runner (sonnet and haiku) with the subscription judge, after implementation, at $0. Nothing is metered.
