## ADDED Requirements

### Requirement: Workspace-supplied build definition takes precedence

A workspace SHALL be able to replace the shipped document pipeline with a build definition of its own, so that a program with a required document layout does not have to fork the skills. Publish SHALL look for such a definition in the proposal's own directory, and SHALL NOT search any other directory, in particular not by walking towards the filesystem root.

Two forms SHALL be recognized:

- an executable build file whose name is `proposal-build`, with or without a suffix, in which case its presence alone is the signal;
- a well-known build-recipe file — a makefile or a justfile under its conventional names — which counts only when it declares a target named `proposal-build`, so that an unrelated build system already present in the workspace is not mistaken for a proposal build.

When a definition is found, publish SHALL NOT build. It SHALL report which definition it found, state that the built-in pipeline was not used, and exit with a status distinct from both success and its build-failure status, so that the run can be told apart from a failure. Executing the definition is the caller's responsibility; the skill's instructions SHALL direct the agent to run it and to relay its output.

#### Scenario: Build file beside the proposal

- **WHEN** a file named `proposal-build` with any suffix sits in the proposal's directory and a build is requested
- **THEN** publish names it, builds nothing, and exits with its handover status

#### Scenario: Recipe file declaring the target

- **WHEN** the proposal's directory holds a makefile or justfile declaring a `proposal-build` target and a build is requested
- **THEN** publish names the file and the target, builds nothing, and exits with its handover status

#### Scenario: Recipe file without the target

- **WHEN** the proposal's directory holds a makefile that declares no `proposal-build` target
- **THEN** it is not a build definition, and the built-in pipeline runs as it would in any other workspace

#### Scenario: Definition in an ancestor directory

- **WHEN** a build definition exists in a directory above the proposal's own
- **THEN** it is not discovered, and the built-in pipeline runs

### Requirement: No fallback to the built-in pipeline

While a workspace build definition exists beside the proposal, publish SHALL NOT produce the built-in document under any circumstance other than an explicit request for it — not on a failed workspace build, not on a missing toolchain, not on an unreadable definition. Producing the default layout when the workspace asked for a different one is a silent wrong answer, because it succeeds visibly and is wrong invisibly.

An explicit option SHALL be provided to run the built-in pipeline anyway, so that a user can establish whether a bad document comes from their template or from their content.

Because the workspace build definition replaces the pipeline, publish SHALL NOT report a missing document toolchain to a delegating workspace, and SHALL NOT resolve an engine for it.

#### Scenario: Workspace build fails

- **WHEN** the workspace build definition runs and fails
- **THEN** no built-in document is produced, and the outcome is reported as the workspace build's failure

#### Scenario: No document toolchain installed

- **WHEN** a delegating workspace has neither of the shipped document engines installed
- **THEN** publish still hands over, and reports no toolchain-install guidance

#### Scenario: Built-in pipeline requested explicitly

- **WHEN** the user explicitly asks for the built-in pipeline in a delegating workspace
- **THEN** the built-in document is produced and the workspace definition is left untouched

### Requirement: Handover is not a defect

The handover status SHALL NOT be treated as a failed run. The skill's bug-report offer, which is made when a shipped script exits non-zero, SHALL NOT be made for it.

#### Scenario: Bug-report offer after handover

- **WHEN** publish hands over to a workspace build definition
- **THEN** no bug report is offered, because nothing failed

### Requirement: Ambiguous build definitions are refused

Where more than one workspace build definition is present beside a proposal, publish SHALL refuse, SHALL name every definition it found, and SHALL neither build nor nominate one of them. Which of two build definitions is the intended one is a question only the user can answer, and guessing it produces the same silent wrong document that the no-fallback rule exists to prevent.

#### Scenario: Two definitions present

- **WHEN** the proposal's directory holds both a `proposal-build` file and a recipe file declaring the `proposal-build` target
- **THEN** publish refuses, names both, and neither builds nor picks one

### Requirement: Contract passed to a workspace build definition

A workspace build definition SHALL receive exactly one piece of information: the absolute path of the proposal file. It SHALL be supplied through an environment variable, so that the same contract serves build files and build recipes alike, and additionally as the first argument where the definition is a build file, which is where the author of a script looks for it. Its directory is the output directory, by the same convention the built-in pipeline follows.

No further input SHALL be added to this contract. The declared language, the output format and the output location are all derivable from the proposal and its directory, and every additional argument is a contract that has to be honoured indefinitely.

#### Scenario: Build file invoked

- **WHEN** a `proposal-build` build file is run for a proposal
- **THEN** it receives the proposal's absolute path both in the environment variable and as its first argument

#### Scenario: Build recipe invoked

- **WHEN** a `proposal-build` recipe target is run for a proposal
- **THEN** it receives the proposal's absolute path in the environment variable

### Requirement: A delegating run writes nothing

On a run that hands over to a workspace build definition, publish SHALL write no file at all — neither a document, nor an intermediate build source, nor an entry in the workspace ignore file. Publish does not know which artifacts a workspace definition produces, so ignore entries for the shipped pipeline's artifacts would be a guess, and the workspace owns its own ignore rules. A workspace build definition is a source file and SHALL NOT be matched by any ignore entry publish manages.

#### Scenario: Ignore file untouched on handover

- **WHEN** publish hands over in a workspace whose ignore file does not yet cover build artifacts
- **THEN** the ignore file is left exactly as it was

#### Scenario: Build definition stays committable

- **WHEN** the ignore entries publish manages are applied to a workspace holding a build definition
- **THEN** none of them matches it

### Requirement: The hand-in export is never delegated

The hand-in export SHALL always be produced by the shipped implementation, including in a workspace that supplies a build definition. It is a transformation of the proposal's own source rather than a rendered document, so a layout template has nothing to say about it, and delegating it would require a second mode in the contract passed to the definition.

#### Scenario: Hand-in export in a delegating workspace

- **WHEN** the user requests the hand-in export in a workspace holding a build definition
- **THEN** the shipped export is written as it would be in any other workspace, and no handover occurs
