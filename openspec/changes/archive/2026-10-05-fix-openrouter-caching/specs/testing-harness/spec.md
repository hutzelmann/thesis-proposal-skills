# Spec Delta

## MODIFIED Requirements

### Requirement: Cost-gated matrix execution
Before issuing any metered call, a matrix run SHALL print a cost estimate derived from registry pricing and SHALL wait for explicit operator confirmation; an explicit non-interactive flag MAY bypass the prompt. Besides each model under test, the estimate SHALL cover the role models the run will call: the rubric judge on every cell-epoch and the student persona on every dialogue-task cell-epoch, each at a per-cell-epoch token budget taken from the registry. Role model IDs SHALL be resolved exactly as the evaluation resolves them, environment overrides included, so the model that is priced is the model that runs. Every model SHALL be priced through the registry's one price resolution: by its roster entry when the roster carries its ID, and otherwise by its role-price entry. The estimate and the post-run actual spend SHALL use this same resolution. When a role model resolves to an ID that neither a roster entry nor a role-price entry prices, the run SHALL stop before the confirmation prompt, name the unpriced ID, and make no metered call; the non-interactive flag SHALL NOT bypass this stop. After the run it SHALL report actual spend per model and in total, computed from recorded token usage and registry pricing, and persist it alongside the run logs. Uncached input, output, cache reads and cache writes SHALL each be charged at their own registry price. A roster entry or role-price entry MAY carry a cache-write price; one without it SHALL be charged its input price for cache writes. The report and the persisted summary SHALL also carry, per model under test, the cache-hit rate (cache-read tokens divided by all prompt tokens, that is uncached input plus cache writes plus cache reads), the cache-read and cache-write token counts, and the serving providers recorded in the run's logs. The run SHALL warn when the cache-hit rate of an Anthropic-family model under test whose requests are routed for caching falls below 50%, or when any of its recorded calls was served by a provider outside those its routing pins; a call served by any provider in the pin's list SHALL NOT be warned. A log MAY record the serving provider for only some of its calls; a call without one SHALL be counted as unrecorded and SHALL NOT be warned. After the run it SHALL also print each role model's observed token usage per cell-epoch beside the registry budget, and flag any budget that the observation exceeds.

#### Scenario: Estimate shown and declined
- **WHEN** the operator declines the pre-run confirmation
- **THEN** no metered call has been made and the run exits cleanly

#### Scenario: Actual cost reported
- **WHEN** a matrix run completes
- **THEN** per-model and total actual cost are printed and persisted with the run's logs

#### Scenario: Judge override priced
- **WHEN** the operator overrides the judge with a registry model priced above the default judge
- **THEN** the estimate charges every cell-epoch's judge budget at the override's registry pricing, not the default judge's

#### Scenario: Persona priced on dialogue tasks only
- **WHEN** a selection contains one dialogue task and one single-turn task
- **THEN** the persona budget is added to the dialogue task's cell-epochs and to no others

#### Scenario: Unpriced role model stops the run
- **WHEN** a role model resolves to an ID that has no registry pricing, with or without the non-interactive flag
- **THEN** the run exits non-zero before the confirmation prompt, names the unpriced ID, and has made no metered call

#### Scenario: Held judge priced from its role-price entry
- **WHEN** no roster entry carries the judge's ID, a role-price entry does, and no override is set
- **THEN** the estimate charges the judge budget at the role-price entry's pricing, the run reaches the confirmation prompt without an unpriced-role stop, and the actual spend prices the judge's usage, cache writes included, from the same entry

#### Scenario: Cache writes priced
- **WHEN** a run's recorded usage includes cache-write tokens
- **THEN** the actual cost charges them at the model's cache-write price, or at its input price where its roster entry or role-price entry carries none

#### Scenario: Cache telemetry persisted
- **WHEN** a matrix run that included an Anthropic-family model under test completes
- **THEN** the printed report and the persisted summary carry that model's cache-hit rate, its cache-read and cache-write token counts, and the serving providers recorded for it

#### Scenario: Caching regression warned
- **WHEN** an Anthropic-family model under test, routed for caching, has a cache-hit rate below 50% in a completed run
- **THEN** the run prints a warning naming the model and its measured rate

#### Scenario: Serving outside the pin warned
- **WHEN** a routed Anthropic-family model under test pins an ordered list of providers, and its recorded calls were served by the second provider in that list and by one provider outside it
- **THEN** the run warns about the provider outside the list, naming it, and does not warn about the second provider in the list

## ADDED Requirements

### Requirement: Prompt caching on Anthropic matrix rows
Matrix requests for an Anthropic-family model under test SHALL be issued so that prompt caching covers the growing conversation, not only the static system and tool prefix. They SHALL be served by a fixed, ordered list of pinned upstream providers with fallbacks beyond that list disabled, the first listed provider serving whenever it is available, so that successive turns reach the cache they wrote. The pinned providers SHALL be ones the operator account's routing guardrails, such as zero data retention, admit; the harness SHALL NOT require relaxing those guardrails. These routing and caching settings SHALL apply to Anthropic rows only, and requests for every other family SHALL be unchanged. The model ID recorded in a run's log SHALL equal the registry ID, so the logs of a cached run count toward the generated report exactly as before. The rubric judge and the student persona SHALL keep their serving configuration: this requirement neither moves nor re-routes them. No one-shot request, that is a rubric-judge or student-persona prompt that no later call extends, SHALL be given a conversation cache breakpoint, because it would pay the cache-write premium without ever reading the cache back; a request of the model under test heads a conversation whose later turns read it back, even when it consists of a single message. The caching mechanism in use SHALL be one that the cache reuse probe has passed on the Anthropic rows it covers. Until a mechanism has passed, Anthropic-family requests SHALL be issued without the provider pin and the caching settings, exactly as for every other family.

#### Scenario: Other families unchanged
- **WHEN** a matrix run includes an OpenAI-family model and an Anthropic-family model
- **THEN** only the Anthropic model's requests carry the provider pin and the caching settings, and the OpenAI model's requests are built exactly as before

#### Scenario: Logged model ID equals registry ID
- **WHEN** an Anthropic row runs with its routing and caching settings
- **THEN** the run's log records the registry ID as its model, and the report generator counts that log for the row

#### Scenario: One-shot prompt gets no breakpoint
- **WHEN** a judge request consists of a single user message
- **THEN** no conversation cache breakpoint is added to it

#### Scenario: No mechanism passed yet
- **WHEN** a matrix run includes an Anthropic-family model and no caching mechanism has passed the cache reuse probe
- **THEN** that model's requests carry neither the provider pin nor the caching settings

### Requirement: Cache reuse probe
The harness SHALL provide a metered probe that replays a fixed, synthetic multi-turn tool conversation for each selected Anthropic registry model and caching mechanism. The conversation's content SHALL be independent of the model's replies, the probe SHALL build the model the same way the matrix does, and it SHALL record the cache usage of every call. Before its first metered call the probe SHALL print a worst-case cost estimate derived from registry pricing, with every prompt token charged at the cache-write price, and SHALL wait for explicit operator confirmation, as a matrix run does. A mechanism SHALL pass on a model only when cache-read tokens make up at least 80% of all prompt tokens, summed over the calls after the first call that writes the cache. The result SHALL state the measured share, the serving providers recorded, and the actual cost. The pass/fail decision and the worst-case estimate SHALL be pure functions covered by L0 tests that invoke no model.

#### Scenario: Probe declined
- **WHEN** the operator declines the probe's confirmation
- **THEN** no metered call has been made and the probe exits cleanly

#### Scenario: Below threshold fails
- **WHEN** cache reads make up 60% of the prompt tokens on the calls after the first cache write
- **THEN** the mechanism fails on that model and the explanation names the measured 60% and the 80% threshold

#### Scenario: No cache write fails
- **WHEN** no call of the replay writes the cache
- **THEN** the mechanism fails and the explanation says that no call wrote the cache

#### Scenario: Reuse at threshold passes
- **WHEN** cache reads make up at least 80% of the prompt tokens on the calls after the first cache write
- **THEN** the mechanism passes on that model
