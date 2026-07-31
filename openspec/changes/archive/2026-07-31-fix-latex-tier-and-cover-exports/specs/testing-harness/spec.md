## ADDED Requirements

### Requirement: Export paths are verified by building real documents

Automated verification SHALL build real documents on every export path the publish skill can resolve, over the full fixture corpus, and SHALL assert that each build completes and produces its declared outputs. A test that only exercises path selection, argument assembly, or offline helpers SHALL NOT be treated as coverage of a build path.

Such a test SHALL drive the shipped build entry point rather than reassembling the converter invocation, so that a defect in how the shipped code constructs that invocation is caught rather than reproduced.

#### Scenario: A broken tier fails the suite

- **WHEN** a change makes one output tier unable to produce a document
- **THEN** the export verification fails for that tier, naming it, without any model involvement

#### Scenario: Selection logic alone is not coverage

- **WHEN** the only test touching a tier verifies which engine would be chosen
- **THEN** that tier counts as unverified, because no document was produced

### Requirement: CI provides the document toolchain

Continuous integration SHALL provide the converter and engines the export verification needs, so those tests execute rather than skip. Toolchain provisioning SHALL use pre-built published images at pinned versions, so a failing run always indicates a change in this repository rather than an upstream update. Where an image cannot host the test runner, the export path it covers MAY be exercised by a script, and that script's invocation SHALL be guarded against divergence from the shipped build path by a test requiring no toolchain.

#### Scenario: Toolchain absent locally

- **WHEN** a contributor without the toolchain runs the suite
- **THEN** the build tests skip and the rest of the suite passes, while CI still executes them

#### Scenario: Script and shipped build diverge

- **WHEN** the shipped build path gains a converter filter that a CI build script does not
- **THEN** the divergence guard fails, independently of whether any toolchain is installed
