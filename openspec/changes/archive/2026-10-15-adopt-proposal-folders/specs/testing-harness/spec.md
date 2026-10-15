# Spec Delta

## ADDED Requirements

### Requirement: Figure embedding verified from another working directory
The export verification SHALL build the figure fixture on the LaTeX and word-processor tiers through the shipped build entry point, with the working directory outside the proposal's folder, and SHALL assert that every figure the proposal links is embedded: one media part per figure in the Word document and one image object per figure in the PDF. A build that completes without them SHALL fail the test.

#### Scenario: Converter resolves figures against the working directory
- **WHEN** a change makes the build resolve `img/` links against the working directory again
- **THEN** the verification fails for the LaTeX and word-processor tiers, naming the tier and the number of figures found

#### Scenario: Tier unavailable locally
- **WHEN** a contributor without a LaTeX engine runs the suite
- **THEN** the LaTeX case skips, the word-processor case still runs where pandoc is present, and CI executes both

### Requirement: Folder-layout dev scenarios
The dev runner SHALL carry scenarios for the folder flows that Proposal-family coverage does not run: ideation from scratch to a seed, import of a source with figures, publish of a proposal with figures on the typst, the LaTeX and the word-processor tier, and a literature search whose request asks to keep the candidate list. Each SHALL be judged by pure verdicts covered by L0 tests, and SHALL run on the subscription only, with no Inspect twin.

#### Scenario: Ideation from scratch
- **WHEN** the from-scratch ideation scenario, which stages nothing, runs three turns on one session — the preamble answers without a topic, then a topic phrase, then a working title whose slug differs from the provisional one together with "enough"
- **THEN** its verdict passes only when the run's recorded tool calls show `idea/notes.md` written in the first turn and that folder moved to a provisional slug before the seed was written, the notes file is never written fresh under the final slug, and at the end exactly one proposal folder holds the seed with a notes file carrying the five section headings, no `idea` or provisional folder remains, and no file lies outside a proposal folder

#### Scenario: Import with figures
- **WHEN** the import scenario runs on the figure fixture's source PDF, staged alone at the workspace root under a name that carries no slug, with a request that asks for the figures to be extracted
- **THEN** its verdict passes only when the imported proposal is `<slug>/<slug>.md` with `notes.md` beside it, it carries exactly two figure references, each a link `img/<name>` without a slug prefix that resolves to a file in `<slug>/img/` or a page-referenced figure TODO marker, and at least one of them is such a resolved link

#### Scenario: Import without an extraction tool
- **WHEN** the import scenario is started and the runner finds no image-extraction tool on the run's search path
- **THEN** the run is reported as untested, never as a pass

#### Scenario: Publish on the typst tier
- **WHEN** the publish scenario runs over the figure fixture with nothing hidden
- **THEN** its verdict passes only when the run's tool results carry the build line naming typst, `<slug>.typ` exists, and the PDF in the proposal's folder, added or changed by the run, embeds every figure the proposal links

#### Scenario: Publish on the LaTeX tier
- **WHEN** the publish scenario runs over the figure fixture with typst hidden from the run's search path and a request that says to install nothing
- **THEN** its verdict passes only when the run's tool results carry the build line naming a LaTeX engine, `<slug>.tex` exists and no `<slug>.typ` was added, and the PDF in the proposal's folder, added or changed by the run, embeds every figure the proposal links

#### Scenario: Publish on the word-processor tier
- **WHEN** the publish scenario runs over the figure fixture with typst and every LaTeX engine hidden from the run's search path and a request that says to install nothing
- **THEN** its verdict passes only when the run's tool results carry the build line naming pandoc, no PDF was added, and the Word document in the proposal's folder, added or changed by the run, embeds every figure the proposal links

#### Scenario: Hidden tool still reachable
- **WHEN** before a publish scenario starts, a login shell under the run's environment still finds a tool the scenario hides
- **THEN** the run is reported as untested and names the tool, never judged

#### Scenario: Candidate list kept on request
- **WHEN** the keep scenario's request asks to keep the candidate list of a snowballing run
- **THEN** its verdict passes only when the list lies in the proposal's folder as `<label>.<ext>` under a free label and family-only passes

#### Scenario: Verdicts without a model
- **WHEN** the L0 suite runs
- **THEN** each of these verdicts is exercised on crafted workspaces and documents, and no model is invoked

### Requirement: Check run from the staged workspace's root
Every runner that runs the mechanical check over a staged workspace — the dev runner on each host and the metered path's sandbox — SHALL run it with the workspace's root as working directory and the proposal's path relative to it, as a user's agent does, so placement, orphan and override findings match what the user would see. Workspace listings in verdicts SHALL walk the workspace's folders. L0 tests SHALL hold each runner's check call to that working directory.

#### Scenario: Folder-staged fixture checked through a runner
- **WHEN** a fixture staged in its folder is checked through the dev runner's check helpers or the sandbox check call
- **THEN** no misplacement error is reported, and the fixture's workspace `guidelines.md` governs

#### Scenario: Rename half-state seen through the runner
- **WHEN** a workspace holding `<new>/<old>.md` is checked through the dev runner's structured check helper
- **THEN** the findings carry the folder-name error

#### Scenario: Negative verdict over a folder workspace
- **WHEN** a run that must seed nothing leaves `<slug>/<slug>.md`
- **THEN** the verdict that no proposal was seeded fails, because the workspace listing walks the folders

### Requirement: Corpus walkers cover every proposal fixture
Every walker over the fixture corpus — the shared test walker, the typst CI build script and the guards that read every fixture — SHALL yield exactly the proposal fixtures that carry an oracle, in the folder layout. The CI build script SHALL fail when it built fewer fixtures than that count, so a layout change can never silently empty a tier or a guard. No test or harness module SHALL spell a fixture file's path; they SHALL resolve it through one shared helper.

#### Scenario: Corpus moved into folders
- **WHEN** every fixture's proposal moves into `<fixture>/<slug>/<slug>.md`
- **THEN** each walker still yields every oracle-bearing proposal, and the CI build script reports that count as built

#### Scenario: Walker that finds nothing
- **WHEN** the CI build script's glob matches no proposal, or fewer than the oracle count
- **THEN** the script exits non-zero and names the count it built and the count it expected

#### Scenario: Spelled fixture path
- **WHEN** a test or harness module joins the fixture root with a fixture's name and a proposal file name
- **THEN** an L0 guard fails and names the file and line

## MODIFIED Requirements

### Requirement: Notes files excluded from draft selection
The shared draft-selection function SHALL treat the role-named companions of a proposal folder — `notes.md`, `review.md`, `feedback.md` and `harvest.md` — and a hand-in export `<slug>.handout.md` as non-proposal markdown, alongside the existing non-proposal names, so no verdict ever grades a companion as the produced proposal. The exclusion SHALL be covered by L0 tests without a model call. Fixtures MAY ship notes files; a notes file carries no `expected.json` oracle obligations of its own.

#### Scenario: Notes file never selected as the draft
- **WHEN** a scenario workspace contains `energy-attack/notes.md` and `energy-attack/energy-attack.md`
- **THEN** draft selection returns `energy-attack/energy-attack.md` even when the notes file sorts first

#### Scenario: Kept file never selected as the draft
- **WHEN** a scenario workspace contains `flaky-ci-triage/flaky-ci-triage.md` and a kept `flaky-ci-triage/reading-list.md` without the proposal's title and subtitle, or `idea/notes.md` and a kept `idea/reading-list.md`
- **THEN** draft selection returns `flaky-ci-triage/flaky-ci-triage.md` in the first workspace, although the kept file sorts first, and nothing in the second

#### Scenario: Exclusion tested without a model
- **WHEN** the L0 suite runs
- **THEN** a unit test exercises the companion exclusion through the pure selection function

### Requirement: Proposal-family coverage
The fixture corpus SHALL carry three synthetic workspaces for the proposal family:

- an **orphan workspace**: a proposal in its folder; a slug-shaped folder holding a leftover review and a figure but no proposal, notes file or harvest record; a kept file at the location root named by the proposal's slug; a proposal file directly in the location; and a build definition at the workspace root. Beside them sit workspace-level and installer-managed files that must not be reported. The workspace's `expected.json` oracle encodes the orphan and unused-build-definition warnings;
- a **rename workspace**: a check-clean proposal in its folder with its notes file, its review and a figure it links, with an `expected.json` oracle;
- a **provisional workspace**: a folder under a provisional slug holding a converged notes file, a kept reading list and a sketch figure, with no proposal and therefore no oracle.

Two pure functions in the shared verdict module SHALL judge the workspace a run leaves, each exercised by L0 tests without a model call. Both SHALL classify files with the mechanical check's own family vocabulary, its test for a proposal folder included.

- **family-only** passes when every file the run added is one of these:
  - a file in a proposal folder that classifies as a family member other than a kept file;
  - the counterpart, in a renamed folder, of a staged file the run removed, which is a rename, kept files and figures included;
  - an allowed workspace-level file, troubleshooting capture or build definition, or a hidden file.

  Any other kept file passes only when the scenario's request asked to keep something, and only in a proposal folder. When the scenario names a staged seed and the seed is still present beside a proposal the run added, the verdict SHALL fail and name both. The verdict SHALL name every offending path.
- **family-renamed**:
  - no folder named by the old slug remains;
  - every file staged in the old folder, other than a built output or the hand-in export, exists in the new folder under the same name, except the proposal file, which carries the new slug;
  - binary members are byte-identical;
  - the proposal's figure links are unchanged.

Three scenarios SHALL run on the subscription dev runner, with family-only part of each one's L1 verdict:

- snowballing from the proposal of the snowball seed fixture, judged by the existing expansion verdict and by family-only;
- a requested rename over the rename workspace, judged by family-renamed and family-only, and by the mechanical check reporting neither an orphan warning nor a folder-name error over the renamed proposal, where a check that did not run fails that judgment;
- seeding over the provisional workspace with a working title that yields a different slug, judged by the existing seed verdict, by family-renamed and by family-only.

On every other dev run, family-only SHALL be reported in the run's summary as an advisory observation, beside the other advisory verdicts. It SHALL NOT change the scenario's pass flag or the exit status, so every runner still reaches the same pass flag for the same produced artifact (requirement: Inverted-hybrid runners). For the draft scenarios, the staged proposal is the seed. A scenario that stages no fixture stages nothing, and every file it leaves counts as added. Inspect twins and matrix cells for the new scenarios, and family verdicts in existing Inspect scorers, are a separate, cost-gated decision.

#### Scenario: Search dump left beside the proposal
- **WHEN** a snowballing run leaves `candidates.yaml` in the proposal's folder, or `<slug>.candidates.yaml` at the location root, and the request asked to keep nothing
- **THEN** family-only fails and names the file

#### Scenario: Review written under a wrong slug
- **WHEN** a run adds `review.md` in a folder `<x>/` that holds no proposal, notes file or harvest record, or at the location root
- **THEN** family-only fails and names the file, as the check's orphan warning would

#### Scenario: Check that did not run
- **WHEN** the mechanical check over the renamed proposal ends without printing its findings
- **THEN** the rename scenario's verdict fails and says the check did not run

#### Scenario: Keeping licensed by the request
- **WHEN** a scenario's request asks to keep the candidate list and the run writes `candidates.yaml` in the proposal's folder
- **THEN** family-only passes

#### Scenario: Staged kept file renamed with its family
- **WHEN** a seeding run renames the folder holding the staged `reading-list.md`, and the request asked to keep nothing
- **THEN** family-only passes

#### Scenario: Ideation that ends before seeding
- **WHEN** an ideation run leaves only `idea/notes.md`, or only `<provisional>/notes.md`
- **THEN** family-only passes

#### Scenario: Figure left behind by a rename
- **WHEN** a rename moves the proposal, its notes file and its review into `<new>/` and leaves `<old>/img/pipeline.png` in place
- **THEN** family-renamed fails and names the file and the folder `<old>/`

#### Scenario: Proposal file left under the old slug
- **WHEN** a rename moves the folder to `<new>/` but leaves `<new>/<old>.md`
- **THEN** family-renamed fails and names the file

#### Scenario: Handout left behind by a rename
- **WHEN** a rename leaves `<old>.handout.md`, which ends in a metadata block, and `<old>.pdf` in the folder `<new>/`
- **THEN** family-renamed passes, because a rename keeps built outputs and the hand-in export as previous outputs

#### Scenario: Draft written beside its seed
- **WHEN** an existing write scenario's run leaves the staged seed in place and adds a fresh proposal file
- **THEN** the run's summary reports the advisory family observation as failed and names both files, and the scenario's pass flag is the one its L1 verdict decides

#### Scenario: Scenario without a fixture
- **WHEN** an import run that staged no fixture leaves the imported proposal's folder with its notes file
- **THEN** the family observation is computed with every file counted as added, and no error is raised

#### Scenario: Orphan oracle holds
- **WHEN** the mechanical check runs over the orphan workspace
- **THEN** it reports exactly the orphan and unused-build-definition warnings its oracle encodes and nothing about the workspace-level or installer-managed files

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions:

- the feedback exists as the role-named feedback file;
- it carries at most five curated points, and carries none only when it opens with the ready tier or its lettered scope options carry its only blocker;
- it opens with one of the student-facing verdict tiers, including the idea-stage rendering in English and German;
- it contains no personal data from the fixture;
- every skill pointer in it names a skill that exists in the set;
- it carries the shared closing note verbatim in the language it was written in;
- any literature it cites is woven rather than listed: every DOI sits inside a numbered point or a prose block rather than a bulleted or bare citation list, is recorded in the companion notes file, and at most three distinct papers are cited; a feedback that cites no literature passes that verdict;
- it carries no format lecture — no sentence that pairs a document-convention subject (name or cover data, Gantt chart or phase list, chapter outline, timeline length, page count, reference link style) with an instruction to remove, shorten or restyle it;
- its markup stays light — no heading line, no blockquote line, no backtick;
- every standard or regulation designation it names that the normalized proposal does not carry has a URL in the paragraph of its first mention.

The closing-note verdict SHALL fail on a paraphrase, on the wrong language's snippet, and on a closing note that arrives with markup the shared snippet does not carry. The points verdict SHALL count numbered items only, so lettered scope options and the clarify-early block do not count as points. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed, and at least one over-scoped raw submission carrying a phase-by-phase work plan, a work package whose input size the submission never states, and claims about public regulations. Over that fixture, a dev-runner scenario SHALL assert, in addition to the feedback contract, that the feedback offers at least two lettered cut options with the choice left to the student, and that the review file carries a work-package table with a scope verdict and a verification section. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral and the lookup approval in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, skill-pointer validity, closing-note fidelity, literature placement, format-lecture absence, markup and locators as separate verdicts

#### Scenario: Feedback found in the proposal's folder
- **WHEN** a supervise run normalizes the submission to `<slug>/<slug>.md` and writes `<slug>/feedback.md`
- **THEN** the presence verdict finds the feedback there, and a feedback file anywhere else does not satisfy it

#### Scenario: Submission saved outside any folder
- **WHEN** the dev-runner readiness scenario stages the student's standard-format proposal at the workspace root, where a professor saves it
- **THEN** the verdicts find the feedback and the review in `<slug>/`, and the staged file is byte-identical after the run

#### Scenario: Ready feedback without points passes
- **WHEN** a produced feedback opens with the ready tier and carries no numbered point
- **THEN** the points verdict passes, while the same feedback opening with needs revision fails it

#### Scenario: Negated tier is not the verdict
- **WHEN** a produced feedback or review opens "not yet ready — needs revision"
- **THEN** the tier read is needs revision, so a pointless feedback with that opening fails the points verdict

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the feedback
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Paraphrased closing note caught
- **WHEN** a run rewrites the closing note instead of quoting the shared snippet
- **THEN** the closing-note verdict fails and says the snippet was not carried verbatim

#### Scenario: Standalone literature list caught
- **WHEN** a produced feedback carries its papers as a bulleted list or as bare citation lines rather than inside the points
- **THEN** the literature verdict fails and names the offending DOI

#### Scenario: Unrecorded or excess literature caught
- **WHEN** a produced feedback cites a DOI absent from the notes file, or cites more than three distinct papers
- **THEN** the literature verdict fails and says which rule was broken

#### Scenario: Literature-free feedback passes the literature verdict
- **WHEN** a produced feedback cites no DOI
- **THEN** the literature verdict passes, because literature is conditional on approval and findings

#### Scenario: Format lecture caught
- **WHEN** a produced feedback tells the student that the Gantt chart and the chapter outline do not belong in the proposal
- **THEN** the format verdict fails and quotes the sentence

#### Scenario: Gantt chart cited as scope evidence passes
- **WHEN** a produced feedback says the plan's Gantt chart fits five dependent packages into fourteen weeks
- **THEN** the format verdict passes, because the chart is used as evidence and nothing asks for its removal

#### Scenario: Heavy markup caught
- **WHEN** a produced feedback carries a heading line or a skill name in backticks
- **THEN** the markup verdict fails and names the offending line

#### Scenario: Unlocated regulation caught
- **WHEN** a produced feedback names a regulation the normalized proposal does not carry, with no URL in that paragraph
- **THEN** the locator verdict fails and names the designation

#### Scenario: Later mention needs no second locator
- **WHEN** a produced feedback locates a new regulation at its first mention and names it again in a later point without a URL
- **THEN** the locator verdict passes

#### Scenario: Closing note is not the student's choice
- **WHEN** a produced feedback offers lettered cuts but only its closing note speaks of the student's decisions
- **THEN** the scope-options verdict fails, because the closing note is left out of the choice search

#### Scenario: Scope options asserted on the over-scoped fixture
- **WHEN** the scope scenario runs against the over-scoped raw submission
- **THEN** the verdicts report the lettered options, the student's choice, the review's work-package table with its scope verdict, and the verification section, alongside the feedback contract

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls

#### Scenario: Idea-stage feedback recognized
- **WHEN** the feedback opens with the idea-stage rendering instead of the blunt review vocabulary
- **THEN** the tier verdict passes in both English and German

#### Scenario: Headless run does not stall
- **WHEN** the L1 task or dev runner drives a borderline submission single-turn
- **THEN** the request's pre-answers resolve the deferral and the lookup approval, and the run completes
