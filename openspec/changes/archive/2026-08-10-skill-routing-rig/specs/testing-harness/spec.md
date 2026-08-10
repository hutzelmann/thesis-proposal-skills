## ADDED Requirements

### Requirement: Skill selection measured through the real host selector
The harness SHALL measure which skill a host agent selects for a user utterance, using the production skill-discovery path — the installed skill set and the frontmatter metadata a host reads before any skill body is loaded — rather than a reconstruction of that path inside an eval prompt. A routing measurement SHALL install the whole `proposal-*` set, so every case is decided against the same competition set a user's install presents.

#### Scenario: Selection decided by metadata alone
- **WHEN** a routing case is measured
- **THEN** the skill's body has not been supplied to the agent before it chooses, and the choice is attributable to the installed metadata

#### Scenario: Whole set competes
- **WHEN** a routing case for one skill is measured
- **THEN** all `proposal-*` skills are installed and available to be chosen

### Requirement: Isolated measurement environment
A routing run SHALL execute against an isolated host configuration containing only the skills under measurement — no operator-specific skills, hooks, plugins, or agents — so that results reproduce on any machine and describe a user's install rather than the developer's. A run that cannot establish that isolation SHALL fail with a message naming what is missing, and SHALL NOT fall back to the ambient configuration.

#### Scenario: Ambient configuration excluded
- **WHEN** the operator's own configuration defines additional skills or session hooks
- **THEN** the routing run is unaffected by them

#### Scenario: Isolation cannot be established
- **WHEN** the isolated configuration cannot authenticate or cannot be created
- **THEN** the run exits with a diagnostic and produces no routing verdicts

### Requirement: Route determined by the first skill invocation
A case's route SHALL be the first invocation of a `proposal-*` skill observed in the run, and the run SHALL be terminated as soon as that route is recorded. Preparatory non-skill tool calls SHALL be tolerated up to a bounded number, and a case that exceeds that bound or its time limit SHALL be recorded as unrouted rather than retried. Skill invocations after the first SHALL NOT change the recorded route.

#### Scenario: Route recorded and run stopped
- **WHEN** the agent invokes a `proposal-*` skill
- **THEN** that skill is the case's route and no further work is performed for that case

#### Scenario: Agent inspects before choosing
- **WHEN** the agent makes a small number of non-skill tool calls and then invokes a `proposal-*` skill
- **THEN** the invoked skill is still recorded as the route

#### Scenario: No skill chosen
- **WHEN** the bound on preparatory tool calls or the time limit is reached with no `proposal-*` skill invoked
- **THEN** the case is recorded as unrouted

#### Scenario: Skill chains into a sibling
- **WHEN** the selected skill invokes another `proposal-*` skill
- **THEN** the recorded route remains the first invocation

### Requirement: Routing dataset covers canonical, oblique, and contested phrasings
The routing dataset SHALL be a tracked data file in which each case carries its utterance, its expected skill, and its kind. Every `proposal-*` skill SHALL have at least one case in each of three kinds: the phrasing its description literally promises, an oblique phrasing a user would plausibly type, and a phrasing that lands in a zone contested by another skill. The dataset SHALL further include negative cases whose expected outcome is that no `proposal-*` skill is selected, and cases in German, the language of the intended user population.

#### Scenario: Skill added without cases
- **WHEN** a `proposal-*` skill has no case of one of the three kinds
- **THEN** the dataset is rejected as incomplete

#### Scenario: Negative case satisfied
- **WHEN** a negative case produces no `proposal-*` route
- **THEN** that case passes

### Requirement: Routing verdicts computed by pure functions over recorded events
Route extraction and matrix classification SHALL be pure functions over event data, separable from process execution, and SHALL be covered by tests that exercise them against recorded host output without issuing any model call. A change in the host's output format SHALL therefore surface as a failure of those tests rather than as an unexplained routing result.

#### Scenario: Parser covered offline
- **WHEN** the L0 suite runs
- **THEN** route extraction and classification are exercised against recorded events with no model call

#### Scenario: Output format changes
- **WHEN** recorded events no longer contain a parseable skill invocation
- **THEN** the parser test fails and names the unparseable input

### Requirement: Routing reported as a confusion matrix
A routing run SHALL persist its raw per-case results and SHALL generate a tracked report presenting expected skill against selected skill, so that a failure names the skill that wrongly claimed the utterance. A single aggregate pass rate SHALL NOT be the only reported figure. The report SHALL record the model and case count the run used.

#### Scenario: Mis-route is attributable
- **WHEN** cases expected to select one skill are routed to another
- **THEN** the report shows that pairing and the utterances involved

#### Scenario: Run provenance recorded
- **WHEN** a report is generated
- **THEN** it names the model used and the number of cases measured

### Requirement: Routing runs are on-demand, not a CI gate
The routing rig SHALL be invocable through a registered task and SHALL NOT be part of the default local test chain or of CI, since it depends on an interactive host installation and subscription credentials. The dataset's structural integrity and the rig's pure functions SHALL be part of the default test chain.

#### Scenario: Default chain stays offline
- **WHEN** the L0 chain runs
- **THEN** no routing measurement is issued and the chain passes without host credentials

#### Scenario: Dataset guarded by the default chain
- **WHEN** the dataset is edited to drop a required case kind
- **THEN** the L0 chain fails
