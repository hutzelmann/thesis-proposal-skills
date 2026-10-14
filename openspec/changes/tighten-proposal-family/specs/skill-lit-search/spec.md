## ADDED Requirements

### Requirement: Search output sized for what a host shows
The keyword-search script and the snowballing script SHALL each print one line on stderr before their stdout output, stating the number of candidates emitted and the size of the stdout output in lines and in characters. When that output exceeds the threshold of 25,000 characters or 1,800 lines, the line SHALL also say that the output is more than some hosts show from one command. The threshold SHALL lie below the smallest known tool-output cap of the hosts the skills support in their default configuration, in characters, and in lines where a cap is counted in lines. In the keyword search, the line SHALL follow the `sources: …` summary line, and that summary line SHALL remain byte-identical. The line is information for the agent, not a degradation note to relay.

The snowballing script's default per-seed limit SHALL be 5, and the skill's snowballing example SHALL pass one seed per call.

When the tool result shows a truncation or omission marker, or fewer candidate entries than the count line states, the skill SHALL instruct the agent to run narrower: fewer seeds per call, one direction, or a lower limit. The skill SHALL NOT write search output into the workspace, unless the user asks to keep it (proposal-file-format: Working material stays out of the workspace).

#### Scenario: Count line beside an unchanged summary
- **WHEN** a keyword search completes with results from three sources
- **THEN** stderr carries the `sources: …` line exactly as before, followed by the count line

#### Scenario: Oversized output flagged
- **WHEN** a run emits more characters or more lines than the threshold
- **THEN** the count line says the output is more than some hosts show from one command

#### Scenario: Default run fits
- **WHEN** the snowballing script runs with its default settings and as many seeds as the skill's example passes, over sources patched to return synthetic records whose number per seed and direction and whose average size match the recorded measurement
- **THEN** stdout stays under the threshold

#### Scenario: Output cut by the host
- **WHEN** the tool result shows fewer candidate entries than the count line states
- **THEN** the agent reruns with fewer seeds, one direction or a lower limit, and adds no file to the workspace

#### Scenario: User keeps the candidate list
- **WHEN** the user asks to keep the candidates of a search
- **THEN** they are written beside the proposal as a kept family member, and nothing else is added
