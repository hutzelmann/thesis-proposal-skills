## ADDED Requirements

### Requirement: Swap-test anchor coverage
The fixture corpus SHALL carry a minimal pair for the swap test's check of named choices. Both fixtures are synthetic and check-clean, and both are built from the readiness controls' text, so that the anchor is the only judgement that differs between them:

- a **decorative-name fixture**: the title and research questions name one fictitious tool, while the contribution claims a result about the tool's class, so a comparable tool would leave the research questions, the method and the expected contribution unchanged;
- an **anchored-name fixture**: the same text, title and research questions included, except the contribution's close, which makes the named tool's own behaviour the object of the evaluation, for the people who use it.

The pair SHALL differ only in the contribution's close. Each fixture SHALL carry an `expected.json` encoding its check-clean state and a `semantic` list stating what a review must conclude about the name and about readiness.

Four dev-runner scenarios SHALL run over the pair: the review skill and the supervise skill, each over each fixture, with the same request across the pair. Pure verdict functions in the shared verdict module SHALL assert the following, each exercised by L0 tests without a model call:

- the decorative-name review opens with needs revision and carries a proposal blocker whose text cites the swap test as failed and names the tool;
- the anchored-name review carries no enumerated finding, in any class, that cites the swap test as failed — an item saying the name passes the swap test, or that no swap-test finding applies, does not count;
- the decorative-name feedback opens with needs revision, carries a numbered point that names the tool and asks the replacement question — a question, direct ("what would change if …?") or indirect ("ask yourself what would change if …", "überlegen Sie, was sich ändern würde, wenn …"), carrying a contrast with a comparable alternative in the same sentence, so a point that only quotes a research question naming the tool does not count — and contains no mention of the swap test outside the closing note;
- the anchored-name feedback opens with the ready tier and carries no numbered point.

The L1 verdicts match test names, pass and failure cues, contrast cues and the tool name only. Whether a finding treats the named tool as replaceable under another test's name is left to the model-graded criterion. That criterion SHALL grade the two review scenarios against the fixture's `semantic` list. On the decorative-name review it checks that the blocker states what stays unchanged under replacement, offers both repairs, says why it cannot wait, and reports the name once even though the title also carries it. On the anchored-name review it checks that no finding treats the named tool as replaceable or decorative, under any test's name. These grades are dev-runner L2, not comparable to matrix results.

The scenarios SHALL run on the subscription dev runner. Inspect twins and matrix cells for them are a separate, cost-gated decision, and skill routing is not part of this coverage.

When the rule lands, the corpus's existing oracles SHALL be audited. A fixture whose title, purpose statement, research questions or contribution names a tool, system, platform or application domain SHALL have its `semantic` list say how the swap test judges that name where a review of it could otherwise be graded against the earlier rule. Its `check` block is unaffected, because the check is not mechanical.

#### Scenario: Decorative name caught
- **WHEN** the review of the decorative-name fixture opens ready, or none of its blockers cites the swap test and names the tool
- **THEN** the verdict fails without model involvement

#### Scenario: Anchored name blocked
- **WHEN** the review of the anchored-name fixture carries a finding that cites the swap test
- **THEN** the verdict fails without model involvement and quotes the finding

#### Scenario: Verdict that names the passing tests
- **WHEN** the anchored-name review's verdict line lists the swap test among the tests that pass, and no enumerated finding cites it
- **THEN** the anchored verdict passes

#### Scenario: Passing name mentioned in a refinement
- **WHEN** the anchored-name review carries a refinement saying the tool passes the swap test as the object of study
- **THEN** the anchored verdict passes

#### Scenario: Test name reaches the student
- **WHEN** the feedback over the decorative-name fixture says "swap test" outside the closing note, or its point on the tool asks the student nothing
- **THEN** the feedback verdict fails and names which property broke

#### Scenario: Quoted research question is not the replacement question
- **WHEN** the feedback's only point naming the tool quotes a research question that names it and ends in a question mark, about another issue
- **THEN** the feedback verdict fails

#### Scenario: Indirect replacement question
- **WHEN** the feedback's point on the tool asks the student, in imperative form and without a question mark, to consider what in the thesis would change if another framework stood in its place
- **THEN** the feedback verdict counts it as the replacement question, and the same imperative without a contrast cue in its sentence does not count

#### Scenario: Anchored name raised in the feedback
- **WHEN** the feedback over the anchored-name fixture opens with needs revision or carries a numbered point
- **THEN** the feedback verdict fails and quotes the tier phrase or the first point

#### Scenario: Pair stays check-clean and minimal
- **WHEN** the mechanical check runs over both fixtures and the offline suite compares them
- **THEN** each reports exactly what its oracle encodes, and the two proposal files differ only in the contribution's close

#### Scenario: Verdict logic covered without a model
- **WHEN** the new verdict functions' failure modes are tested
- **THEN** L0 tests call them directly on crafted review and feedback texts and no model is invoked

#### Scenario: Existing oracle audited
- **WHEN** the rule lands and a fixture's title names a platform that its research questions never use
- **THEN** that fixture's `semantic` list states that the name fails the swap test and is a blocker, and its `check` block is unchanged
