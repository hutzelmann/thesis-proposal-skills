## ADDED Requirements

### Requirement: Claim-scope swap coverage
The fixture corpus SHALL carry a Bachelor's pair built from the swap-test pair's text: a mixed-scope fixture whose contribution claims the gap for the class beside a close scoped to the named framework, stating no reason why and that the student's team runs the framework, and a twin whose claims are all scoped to the framework. Review and supervise SHALL run over each, and supervise over two earlier-round workspaces on the mixed text, on the subscription dev runner.

#### Scenario: Pair differs inside the contribution only
- **WHEN** the offline suite compares the two Bachelor's fixtures
- **THEN** both carry the Bachelor's subtitle, the same framework placements and the same sentence about the team, and every difference between them lies inside the contribution section

#### Scenario: Mixed scope caught in the review
- **WHEN** the review of the mixed-scope fixture opens ready, or none of its blockers cites the swap test and names the framework
- **THEN** the verdict fails without model involvement

#### Scenario: Setting-scoped twin passes
- **WHEN** the review of the setting-scoped fixture carries an enumerated finding that cites the swap test as failed
- **THEN** the verdict fails without model involvement and quotes the finding

#### Scenario: Mixed scope reaches the student
- **WHEN** the feedback over the mixed-scope fixture carries no numbered point that names the framework and asks the replacement question
- **THEN** the feedback verdict fails

#### Scenario: Setting-scoped feedback stays quiet
- **WHEN** the feedback over the setting-scoped fixture carries a numbered point
- **THEN** the feedback verdict fails

#### Scenario: Earlier remark does not anchor
- **WHEN** a workspace holds the mixed-scope text with an earlier review whose title refinement calls the framework the object of study and an earlier feedback whose What to keep credits the team's access, and the supervise run's review carries no swap-test blocker on the framework labelled as missed in the earlier round
- **THEN** the verdict fails without model involvement

#### Scenario: Earlier point is not dropped
- **WHEN** a workspace holds the mixed-scope text with an earlier feedback that raised the framework as a numbered point, the request asks to redo and replace that feedback, and the supervise run's review lists that point other than open in its earlier-round section, or the new feedback carries no point on the framework
- **THEN** the verdict fails without model involvement

#### Scenario: Pass listed for the professor
- **WHEN** the supervise run over the setting-scoped fixture or the anchored-name fixture carries no line in its review's verification section that names the framework with a quote occurring in the proposal
- **THEN** the verdict fails without model involvement

#### Scenario: Staged earlier files are not graded
- **WHEN** an earlier-round scenario's run leaves the staged earlier review or feedback unchanged, or writes a second proposal folder
- **THEN** the verdict fails without grading the staged files as the run's output

#### Scenario: Reproduction recorded before the rule changes
- **WHEN** the change that adds this coverage is implemented
- **THEN** the mixed-scope scenarios run on the unchanged guidance first, and the record keeps whether the false pass reproduced, with the served model and the run conditions that differ from the reported run, a non-reproduction under different conditions recorded as inconclusive

#### Scenario: Review graded against the fixture's semantic list
- **WHEN** a dev run grades the two Bachelor's review scenarios
- **THEN** the mixed-scope review is graded on quoting a class-scoped and a framework-scoped claim, crediting no dependence the proposal does not state, and naming the repairs that decide the scope; the setting-scoped review is graded on no finding treating the framework as replaceable and no demand for a novelty claim

#### Scenario: Existing oracles audited
- **WHEN** the rule lands
- **THEN** each existing fixture whose title, purpose, research questions or contribution names a tool, platform or setting has its `semantic` list say how the claim-scope rule judges that name, without a change to its `check` block; a fixture behind a shipped matrix cell or a dev-runner L2 criterion keeps its `semantic` list, and its audit is recorded in its corpus README row
