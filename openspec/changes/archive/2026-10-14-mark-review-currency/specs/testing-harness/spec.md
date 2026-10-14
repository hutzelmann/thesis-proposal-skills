## ADDED Requirements

### Requirement: Review-currency coverage
The fixture corpus SHALL test the review-currency warning with workspaces that differ only where the behaviour under test differs:

- a **superseded-record workspace**: the narrowed-scope workspace's proposal, notes file and review, each byte for byte, with the review closing on a record of the broader predecessor's research questions — its oracle encodes exactly one `review-questions-changed` warning and the exit code the proposal alone gives;
- the **narrowed-scope workspace** itself, unchanged, whose review carries no record — its oracle continues to encode no review finding, so the pair isolates the record;
- the **current-ready workspace**, whose review gains a record matching its proposal's research questions verbatim — its oracle continues to encode no finding.

Every such fixture SHALL carry an `expected.json` oracle calibrated against the mechanical check. L0 tests without a model call SHALL cover the extraction and comparison:

- line wrapping, list-marker style and numbering, Unicode compatibility forms, invisible format characters, and quote and dash variants, while a change of letter case still counts;
- a nested item kept inside its parent question;
- either record title regardless of the proposal's language;
- notes below the record without a heading of their own, a bulleted list among them, and a thematic break after it, none of which counts as a recorded question;
- a missing or empty record, a review that is not valid UTF-8, and a directory at the review's path;
- a proposal with no ordered-list research question;
- each of changed, added and removed positions, and a message that quotes no question.

An L0 drift test SHALL fail when the review skill's prose stops naming either record title as a `## ` section title the script recognises.

A pure verdict function in the shared verdict module SHALL decide whether a review run wrote the record: the proposal is unchanged, the review file exists, and its record, extracted and normalized exactly as the script does it, equals the proposal's research questions. It SHALL be exercised by L0 tests, among them a record that adds the overarching question a section states in prose, and SHALL be asserted by one dev-runner scenario that reviews the readiness overblocking control on the subscription. Inspect twins and matrix cells for it are a separate, cost-gated decision.

The verdicts that judge a review's own shape SHALL judge the review without its research-questions record, located as the script locates it. These are the check that the findings are enumerated, the check that the review is written in the proposal's language, and the whole-text keyword scans of the hollow-proposal and title-alarm verdicts. A numbered record, or questions copied verbatim in another language, therefore cannot satisfy a gate meant for the findings, and the shipped review verdicts keep their meaning.

#### Scenario: Pair calibrated
- **WHEN** the mechanical check runs over the superseded-record workspace and over the narrowed-scope workspace
- **THEN** the first reports exactly one `review-questions-changed` warning and the second reports no review finding, each as its oracle encodes

#### Scenario: Record dropped
- **WHEN** a dev run's review closes without the record section
- **THEN** the record verdict fails and names the missing section, without model involvement

#### Scenario: Record paraphrased
- **WHEN** a dev run's record rewords the proposal's second research question
- **THEN** the record verdict fails and names RQ2

#### Scenario: Overarching question recorded
- **WHEN** a German proposal states an overarching question in prose before four numbered ones, and the record lists that overarching question as well
- **THEN** the record verdict fails, naming the positions that differ

#### Scenario: Title drift
- **WHEN** the review skill's prose renames the record heading without the script's titles changing with it
- **THEN** the L0 suite fails and names the title it no longer finds

#### Scenario: Numbered record does not make the findings enumerated
- **WHEN** a review lists its findings as bullets and closes with a numbered record
- **THEN** the review-shape verdict fails it as not enumerated

#### Scenario: German record does not make an English review German
- **WHEN** an English review of a German proposal closes with that proposal's research questions copied verbatim
- **THEN** the language verdict fails it as not written in German
