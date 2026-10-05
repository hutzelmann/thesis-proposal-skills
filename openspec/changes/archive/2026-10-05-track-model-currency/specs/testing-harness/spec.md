## MODIFIED Requirements

### Requirement: Pinned model registry
Matrix runs SHALL take their model roster exclusively from a tracked registry file pinning exact provider-qualified model IDs (the version visible in the ID), each with family, price tier, cached input/output pricing, and an enabled flag. A registry entry MAY carry a free-text note recording a caveat about the model's standing in the matrix — for example that the harness cannot drive it — which SHALL default to empty when absent. The roster SHALL cover at least three model families (Anthropic, OpenAI, open-weight) at cheap and frontier price points. Changing a model version SHALL require editing the registry, never a runtime "latest" resolution, so successive runs stay comparable.

The registry SHALL record the date its prices were copied from the provider's catalog. Prices SHALL be taken from the model vendor's own endpoint at its standard service tier. An entry MAY name the endpoint its prices come from. It SHALL do so when the vendor's provider name differs from its catalog namespace, or when the vendor serves no endpoint of its own.

The registry SHALL also carry a roles table naming every model the harness uses outside the roster:

- the rubric judge of matrix runs;
- the dialogue persona, which SHALL default to the judge when absent;
- the metered smoke model, which SHALL name an enabled roster entry;
- the subscription dev-runner judge, together with its pinned effort level.

Every roster and role ID SHALL be a pinned full ID. A floating alias SHALL make registry parsing fail and name the offending entry. Floating aliases are a bare family name, a `~`-prefixed ID, and an ID ending in `-latest`. The judge's ID SHALL appear only in the roles table; the judge's per-run token budget MAY stay with the task configuration.

Every metered role, that is the judge and the persona, SHALL be priced by the registry: by the roster entry with its ID, or, when no roster entry carries that ID, by a price-only role-price entry under the same price basis and date. A registry whose judge or persona cannot be priced SHALL fail parsing and name the role. A role-price entry that no role names, or that duplicates a roster entry, SHALL fail parsing. All harness price lookups SHALL go through this one resolution.

Harness code SHALL take these IDs from the registry. An environment override MAY replace one role for one invocation, and SHALL NOT carry over to any other role.

#### Scenario: Roster comes from the registry
- **WHEN** a matrix run is started with a tier filter
- **THEN** exactly the enabled registry models of that tier are exercised, under their pinned IDs

#### Scenario: Disabled model skipped
- **WHEN** a registry entry sets enabled to false
- **THEN** matrix runs omit it without failing

#### Scenario: Note is optional
- **WHEN** a registry entry carries no note
- **THEN** the registry parses and the model's rendered notes are unchanged

#### Scenario: Role changed in the registry only
- **WHEN** the judge role is set to a different pinned ID in the registry and no override is present
- **THEN** the rubric scorers and the cost estimate both use the new ID without any code edit

#### Scenario: Floating alias rejected
- **WHEN** a roster entry or a role names `sonnet`, `~anthropic/claude-sonnet-latest`, or any ID ending in `-latest`
- **THEN** registry parsing fails and names the offending entry

#### Scenario: Judge named twice
- **WHEN** the task configuration still carries a judge model ID beside the roles table
- **THEN** registry parsing fails and points to the roles table

#### Scenario: Smoke model outside the roster
- **WHEN** the smoke role names an ID that is not an enabled roster entry
- **THEN** registry parsing fails

#### Scenario: Persona defaults to the judge
- **WHEN** the roles table names a judge and no persona
- **THEN** the persona resolves to the judge's ID

#### Scenario: Judge override does not move the persona
- **WHEN** an invocation overrides the judge from the environment and does not override the persona
- **THEN** the persona keeps the registry's persona role

#### Scenario: Held judge priced after leaving the roster
- **WHEN** the roster entry that carried the judge's ID has been re-pinned and a role-price entry for that ID exists
- **THEN** the registry parses, and the cost estimate prices the judge from the role-price entry

#### Scenario: Unpriced metered role rejected
- **WHEN** the judge or persona names an ID that neither a roster entry nor a role-price entry carries
- **THEN** registry parsing fails and names the role

#### Scenario: Orphaned role price rejected
- **WHEN** a role-price entry names an ID that no role names, or an ID a roster entry also carries
- **THEN** registry parsing fails and names the entry

## ADDED Requirements

### Requirement: Model identifiers live only in the registry
An L0 test SHALL scan the tracked tree for model identifiers. It SHALL recognize the identifier shapes of the vendor families the harness has used, and the version line of every registry entry.

- **Code and configuration:** the harness and repository scripts, the project configuration, and the CI workflows SHALL carry no model identifier.
- **Any other tracked file:** it MAY name a model only by an identifier that resolves to a current roster entry or role. A resolving identifier is in one of these spellings:
  - provider-qualified;
  - without the provider prefix;
  - the subscription CLI's form, which has dashes between version digits and an optional trailing date.

An explicit allowlist SHALL exempt these, each entry with its reason:

- the registry itself;
- change records under the OpenSpec changes directory;
- the main specifications, whose scenarios carry illustrative identifiers, receive them when a change is archived, and change only through a change record;
- generated report outputs, including the generated region of the README;
- generated eval projections;
- model-identifier normalization test data, including an eval scenario whose subject is the model identifier a user reports.

An allowlist entry MAY cover a category of files, a whole file, or a single identifier within one file. An entry that tolerates a violation another change will remove SHALL name that change. Such a parked entry SHALL fail the test once it exempts nothing, and so SHALL an entry for a single identifier, so that a resolved exemption cannot linger. Category entries such as generated outputs and the main specifications stay in place even when their files currently name only current models.

#### Scenario: Hardcoded default rejected
- **WHEN** a harness module introduces a provider-qualified model ID as a default value
- **THEN** the L0 suite fails, naming the file, the line and the identifier

#### Scenario: Stale example rejected
- **WHEN** a documentation file names a model whose version line the registry pins at a different version
- **THEN** the L0 suite fails, naming the identifier and the current pin of that line

#### Scenario: Unregistered model rejected
- **WHEN** a documentation file names a model that no roster entry or role tracks
- **THEN** the L0 suite fails, naming the identifier

#### Scenario: Subscription spelling accepted
- **WHEN** a tracked issue template names `claude-sonnet-5-5` and the registry pins `anthropic/claude-sonnet-5.5`
- **THEN** the guard accepts the identifier

#### Scenario: Exhausted parked entry
- **WHEN** a parked allowlist entry, or an entry for a single identifier, no longer exempts any violation
- **THEN** the L0 suite fails, naming the entry so it can be removed

#### Scenario: Archived scenario names an outgoing model
- **WHEN** an archived change has synced a scenario naming a model into a main specification, and a later bump re-pins that model's line
- **THEN** the guard does not flag the specification

### Requirement: Shipped verdicts list exactly the registry roster
An L0 test SHALL fail when the generated verdict data or the README model-support summary lists a model set different from the registry roster. Outgoing IDs SHALL count as extra and incoming IDs as missing. A roster edit therefore cannot reach the default branch until the report has been regenerated from the run logs.

#### Scenario: Roster bumped without regeneration
- **WHEN** a registry entry's ID is replaced and the report has not been regenerated
- **THEN** the L0 suite fails, naming the outgoing ID as extra and the incoming ID as missing

#### Scenario: Regenerated report
- **WHEN** the report has been regenerated after the bump
- **THEN** the test passes, with the new IDs shown as untested until a matrix run measures them

### Requirement: Model currency check
A checker SHALL compare every roster pin and every role against the provider's public model catalog. It SHALL use no credentials and only the standard library. For each pin it SHALL derive a version line: the identifier with its version number wildcarded and any trailing snapshot-date token ignored. Variants carrying a `:` suffix SHALL be excluded.

An entry MAY override its line with an explicit pattern, or opt out of tracking. An opted-out entry SHALL be reported as untracked, never silently omitted. Subscription-form role IDs SHALL be mapped to catalog IDs: dashes between version digits become dots, a trailing date is dropped, and the vendor namespace is added.

The checker SHALL report each of the following as a structured finding:

- a newer model in the line, newer meaning a higher version, or the same version created later;
- a pin missing from the catalog;
- a non-empty expiration date;
- price drift beyond a fixed relative tolerance against the vendor's own endpoint, for roster entries and role-price entries alike.

It SHALL also report, as informational findings that are never written, the version lines in any vendor namespace the registry uses that no registry entry or role derives and that have a member created after the registry's line-review date. The registry SHALL record that date, and only a maintainer's edit SHALL move it.

Its output SHALL be human-readable by default and JSON on request.

A write mode SHALL apply newer-in-line bumps and refreshed prices to the registry, and update the price date. It SHALL edit lines so that comments and notes are preserved, and running it a second time SHALL change nothing. It SHALL NOT rewrite the matrix judge or the persona role. It SHALL report them as held, because changing either invalidates every rubric-counted cell until a full re-baseline. When it re-pins a roster entry whose outgoing ID a held role still names, it SHALL add a role-price entry for that ID in the same edit, so the held role stays priced. It SHALL NOT change the line-review date. Its logic SHALL be covered by L0 tests over a recorded catalog snapshot, without network access.

#### Scenario: Newer model in the line
- **WHEN** the roster pins `openai/gpt-5.6-sol` and the catalog lists `openai/gpt-6-sol` and `openai/gpt-6.1-sol`
- **THEN** the checker reports `openai/gpt-6.1-sol` as the newest model in the line

#### Scenario: Variants and siblings are not successors
- **WHEN** the catalog lists `:batch` variants, `-pro` or `-prime` siblings, and `~`-prefixed floating aliases next to a pinned model
- **THEN** none of them is reported as a newer model

#### Scenario: Dated snapshot of the same version
- **WHEN** the catalog lists a dated snapshot of the pinned version that was created after the pinned entry
- **THEN** the checker reports the dated snapshot as newer

#### Scenario: Floating pin detected
- **WHEN** a pinned ID is absent from the catalog while a dated sibling of the same version is listed
- **THEN** the checker reports the pin as missing and proposes the dated sibling

#### Scenario: Subscription role mapped
- **WHEN** the dev-runner judge role is `claude-sonnet-5-5` and the catalog lists a newer Sonnet
- **THEN** the checker reports the newer model and proposes its subscription-form ID for review

#### Scenario: Judge held
- **WHEN** a newer model exists in the matrix judge's line
- **THEN** the checker reports it as held and the write mode leaves the judge and persona roles unchanged

#### Scenario: Held judge's roster entry re-pinned
- **WHEN** the write mode re-pins the roster entry that carries the judge's ID
- **THEN** the judge role keeps its ID, a role-price entry for that ID is added in the same edit, and the edited registry parses

#### Scenario: New line in a roster vendor namespace
- **WHEN** the catalog lists `anthropic/claude-fable-5.1`, created after the line-review date, and no registry entry or role tracks the Fable line
- **THEN** the checker reports the Fable line as an informational finding naming `anthropic/claude-fable-5.1`, exits as it would without it, and the write mode adds no roster entry

#### Scenario: Reviewed new line
- **WHEN** the maintainer moves the line-review date past the newest member of a reported line
- **THEN** the checker no longer reports that line

#### Scenario: Write is idempotent
- **WHEN** the write mode runs twice against the same catalog snapshot
- **THEN** the second run changes no byte of the registry

#### Scenario: Catalog unreachable
- **WHEN** the catalog request fails
- **THEN** the checker exits with a distinct "currency unknown" status and writes nothing

### Requirement: Weekly model-bump pull request
A CI workflow SHALL run the currency check in write mode weekly and on manual dispatch. When the registry changes, it SHALL keep exactly one open pull request from a fixed branch, creating it or updating it. It SHALL use only the repository's built-in token, with the least permissions this needs.

Pull requests opened with that token trigger no pull-request workflows. The workflow SHALL therefore start the regular CI workflow on the bump branch itself.

It SHALL NOT overwrite the bump branch once the branch carries a commit from anyone else; it SHALL comment on the pull request instead. When main already satisfies every finding, it SHALL close a pull request that is no longer needed.

The pull request description SHALL:

- list every finding, including any role-price entry added for a held role;
- list the new lines in the registry's vendor namespaces as a roster decision for the maintainer;
- instruct the maintainer to regenerate the model-support report locally from the run logs and to re-run the shared-copy sync before merging;
- state that new IDs render as untested until a cost-gated matrix run;
- flag a bump of a subscription role for a check that the CLI resolves the new ID to itself.

Report-only findings, new lines included, SHALL appear in the run summary. A new line alone SHALL NOT open a pull request or fail the run. A pin that is missing or expiring without a writable successor SHALL fail the scheduled run.

The workflow SHALL NOT call any model, read any secret beyond the built-in token, or merge.

#### Scenario: New model published
- **WHEN** the weekly run finds a newer model in a roster line
- **THEN** a pull request from the fixed branch carries the registry edit and a description with the regeneration instructions, and the regular CI workflow runs on that branch

#### Scenario: Pull request already open
- **WHEN** a bump pull request is open and a later run finds further changes
- **THEN** the same pull request is updated and no second one is opened

#### Scenario: Maintainer has pushed to the bump branch
- **WHEN** the bump branch carries a commit not made by the workflow
- **THEN** the workflow leaves the branch untouched and comments the new findings on the pull request

#### Scenario: Nothing to bump
- **WHEN** the check finds no writable change
- **THEN** no pull request is opened, and an open one that main has made obsolete is closed

#### Scenario: Pin about to disappear
- **WHEN** a pinned model carries an expiration date and no newer model exists in its line
- **THEN** the scheduled run fails and its summary names the pin

### Requirement: Currency warning at the cost gate
Before asking for cost confirmation, a matrix run SHALL print stale-model warnings from the same currency check. The warnings SHALL come from a single unauthenticated catalog request with a short timeout. A failed request SHALL print a "model currency unknown" warning. The warning SHALL NOT block the run, alter the estimate, or change the exit status.

The L0 suite SHALL disable the checker's network access for every test by default, so that no test touches the network, including a test that runs a matrix invocation without mentioning the catalog. Tests that assert warnings SHALL substitute a recorded catalog.

#### Scenario: Stale pin warned before confirmation
- **WHEN** a matrix run selects a model whose line has a newer catalog entry
- **THEN** the warning naming the newer model is printed before the confirmation prompt, and the estimate is unchanged

#### Scenario: Offline gate
- **WHEN** the catalog cannot be reached
- **THEN** a "model currency unknown" warning is printed and the run proceeds to the usual confirmation

#### Scenario: L0 test without a catalog substitute
- **WHEN** an L0 test runs a matrix invocation and substitutes nothing for the catalog request
- **THEN** no network request is made, and the gate prints the "model currency unknown" warning
