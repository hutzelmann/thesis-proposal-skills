# testing-harness delta: model-support-matrix

## ADDED Requirements

### Requirement: Pinned model registry
Matrix runs SHALL take their model roster exclusively from a tracked registry file pinning exact provider-qualified model IDs (the version visible in the ID), each with family, price tier, cached input/output pricing, and an enabled flag. The roster SHALL cover at least three model families (Anthropic, OpenAI, open-weight) at cheap and frontier price points. Changing a model version SHALL require editing the registry, never a runtime "latest" resolution, so successive runs stay comparable.

#### Scenario: Roster comes from the registry
- **WHEN** a matrix run is started with a tier filter
- **THEN** exactly the enabled registry models of that tier are exercised, under their pinned IDs

#### Scenario: Disabled model skipped
- **WHEN** a registry entry sets enabled to false
- **THEN** matrix runs omit it without failing

### Requirement: Cost-gated matrix execution
Before issuing any metered call, a matrix run SHALL print a cost estimate derived from registry pricing and SHALL wait for explicit operator confirmation; an explicit non-interactive flag MAY bypass the prompt. After the run it SHALL report actual spend per model and in total, computed from recorded token usage and registry pricing, and persist it alongside the run logs.

#### Scenario: Estimate shown and declined
- **WHEN** the operator declines the pre-run confirmation
- **THEN** no metered call has been made and the run exits cleanly

#### Scenario: Actual cost reported
- **WHEN** a matrix run completes
- **THEN** per-model and total actual cost are printed and persisted with the run's logs

### Requirement: Epoch-based support classification
Each scorable model×task cell SHALL run a fixed number of epochs (default three) and classify by pass rate: all passes solid, mixed flaky, none fail. Per model, the verdict SHALL be: supported when all scorable cells are solid; flaky with the affected skills named when any cell is flaky; a warning naming the failing skills when any cell fails. Tasks red-by-design on the metered path (environment-fidelity probes) and network-dependent tasks SHALL be excluded from classification; a task MAY contribute only its rubric score where its structural score is excluded. Heavy dialogue tasks MAY run reduced epochs on frontier-tier models for budget reasons, and the report SHALL disclose reduced-epoch cells.

#### Scenario: Flaky cell names the skill
- **WHEN** a model passes a task in some epochs and fails it in others
- **THEN** the model's verdict is flaky and names that task's skill

#### Scenario: Environment-fidelity probe not scored
- **WHEN** a task known to be red-by-design on the metered path fails for every model
- **THEN** no model's verdict is affected by that task's structural score

### Requirement: Generated model-support report
A report generator SHALL derive, from the newest run logs only, (1) a summary table in the repository README between generated-section markers — one row per registry model with its pinned ID, verdict, warnings, and the run timestamp — and (2) a full model×task grid document with per-cell pass rates and per-model run cost. Regeneration SHALL be idempotent and SHALL replace only the marked README region. Models never exercised in the available logs SHALL appear as untested rather than silently omitted.

#### Scenario: README region replaced in place
- **WHEN** the report generator runs twice on the same logs
- **THEN** the README outside the markers is byte-identical and the marked region is identical between runs

#### Scenario: Untested model visible
- **WHEN** a registry model has no cells in the available logs
- **THEN** the summary row shows it as untested instead of dropping it

### Requirement: Matrix logic covered without model calls
Registry parsing, classification banding, verdict derivation, cost estimation arithmetic, and README marker splicing SHALL be pure functions covered by L0 tests that invoke no model.

#### Scenario: Classification tested offline
- **WHEN** the L0 suite runs
- **THEN** unit tests exercise band edges (all-pass, mixed, all-fail, excluded task, reduced epochs) purely in-process
