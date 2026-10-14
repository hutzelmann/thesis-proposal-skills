## ADDED Requirements

### Requirement: Proposal-family coverage
The fixture corpus SHALL carry three synthetic workspaces for the proposal family:

- an **orphan workspace**: a proposal whose slug differs from that of a leftover review, a leftover kept file and a leftover figure. The proposal links that figure. Beside them sit workspace-level and installer-managed files that must not be reported. The workspace's `expected.json` oracle encodes the orphan warnings;
- a **rename workspace**: a check-clean proposal with its notes file, its review and a figure it links, all under one slug, with an `expected.json` oracle;
- a **provisional workspace**: a converged ideation notes file, a kept reading list and a sketch figure under a provisional slug, with no proposal and therefore no oracle.

Two pure functions in the shared verdict module SHALL judge the workspace a run leaves, each exercised by L0 tests without a model call. Both SHALL classify files with the mechanical check's own family vocabulary, including the metadata-block test by which the check tells a proposal from a `-review` or `-feedback` companion.

- **family-only** passes when every file the run added is one of these:
  - a family member other than a kept file, whose slug is carried by a proposal, a notes file or a harvest record present after the run;
  - `ideation.notes.md`;
  - the same-suffix counterpart, under a new slug, of a staged family member the run removed, which is a rename, kept files and figures included;
  - an allowed workspace-level file, troubleshooting capture or build definition, or a hidden file.

  Any other file in the kept-file form passes only when the scenario's request asked to keep something. When the scenario names a staged seed and the seed is still present beside a proposal the run added, the verdict SHALL fail and name both. The verdict SHALL name every offending path.
- **family-renamed**:
  - no file whose path starts with the old slug followed by `.` or `-`, in the proposal location or under `img/`, remains, other than a built output;
  - every family member staged under the old slug, other than a built output, exists under one new slug with the same suffix;
  - binary members are byte-identical;
  - neither the proposal nor its notes file still links `img/<old>-`.

Three scenarios SHALL run on the subscription dev runner, with family-only part of each one's L1 verdict:

- snowballing from the proposal of the snowball seed fixture, judged by the existing expansion verdict and by family-only;
- a requested rename over the rename workspace, judged by family-renamed and family-only, and by the mechanical check reporting no orphan warning over the renamed proposal, where a check that did not run fails that judgment;
- seeding over the provisional workspace with a working title that yields a different slug, judged by the existing seed verdict, by family-renamed and by family-only.

On every other dev run, family-only SHALL be reported in the run's summary as an advisory observation, beside the other advisory verdicts. It SHALL NOT change the scenario's pass flag or the exit status, so every runner still reaches the same pass flag for the same produced artifact (requirement: Inverted-hybrid runners). For the draft scenarios, the staged proposal is the seed. A scenario that stages no fixture stages nothing, and every file it leaves counts as added. Inspect twins and matrix cells for the new scenarios, and family verdicts in existing Inspect scorers, are a separate, cost-gated decision.

#### Scenario: Search dump left beside the proposal
- **WHEN** a snowballing run leaves `<slug>.candidates.yaml` beside the proposal and the request asked to keep nothing
- **THEN** family-only fails and names the file

#### Scenario: Review written under a wrong slug
- **WHEN** a run adds `<x>-review.md` without a metadata block, and no proposal carries `<x>`
- **THEN** family-only fails and names the file, as the check's orphan warning would

#### Scenario: Check that did not run
- **WHEN** the mechanical check over the renamed proposal ends without printing its findings
- **THEN** the rename scenario's verdict fails and says the check did not run

#### Scenario: Keeping licensed by the request
- **WHEN** a scenario's request asks to keep the candidate list and the run writes `<slug>.candidates.yaml`
- **THEN** family-only passes

#### Scenario: Staged kept file renamed with its family
- **WHEN** a seeding run renames the staged `<provisional>.reading-list.md` to `<new>.reading-list.md` together with the rest of the family, and the request asked to keep nothing
- **THEN** family-only passes

#### Scenario: Ideation that ends before seeding
- **WHEN** an ideation run leaves only `<provisional>.notes.md`, or only `ideation.notes.md`
- **THEN** family-only passes

#### Scenario: Figure left behind by a rename
- **WHEN** a rename leaves `img/<old>-pipeline.png` in place
- **THEN** family-renamed fails and names the file

#### Scenario: Handout left behind by a rename
- **WHEN** a rename leaves `<old>-handout.md`, which ends in a metadata block
- **THEN** family-renamed fails and names the file

#### Scenario: Draft written beside its seed
- **WHEN** an existing write scenario's run leaves the staged seed in place and adds a fresh proposal file
- **THEN** the run's summary reports the advisory family observation as failed and names both files, and the scenario's pass flag is the one its L1 verdict decides

#### Scenario: Scenario without a fixture
- **WHEN** an import run that staged no fixture leaves the imported proposal and its notes file
- **THEN** the family observation is computed with every file counted as added, and no error is raised

#### Scenario: Orphan oracle holds
- **WHEN** the mechanical check runs over the orphan workspace
- **THEN** it reports exactly the warnings its oracle encodes and nothing about the workspace-level or installer-managed files
