## ADDED Requirements

### Requirement: Citation-practice coverage
The fixture corpus SHALL carry two synthetic fixtures for citation practice, each with an `expected.json` oracle calibrated against the mechanical check:
- an idea seed whose references block holds at least ten entries, one of them central enough to a theme that a draft could lean on it for several sentences;
- a proposal draft that already carries the overcitation pattern: the same key on at least three consecutive sentences of one paragraph, an identical multi-key group repeated on adjacent sentences, and a contribution paragraph that summarises one source sentence by sentence.

Neither fixture SHALL contain content from a real proposal. The over-citing draft's oracle SHALL record the repeated-citation warning, and every other proposal fixture's oracle SHALL record its absence. This makes the draft the trip case and the rest of the corpus the pass case for that rule.

The harness SHALL exercise a writing pass that drafts from the seed and a writing pass over the draft, both as dev-runner scenarios and as Inspect tasks. Each run SHALL be judged by an L1 verdict that is a pure function in the shared verdict module, testable without a model call. The verdict SHALL fail when two adjacent sentences carry the same non-empty set of citation keys, comparing within a paragraph and across consecutive items of one list. Sentences whose key sets differ pass. A paragraph break, a heading or a table row resets the comparison. The verdict's sentence and block boundaries SHALL be those of the check's repeated-citation rule, pinned to it by L0 tests. For the pass over the draft, the verdict SHALL additionally fail when a reference the input cites is cited nowhere in the output, so that deleting citations is never a way to pass.

Each Inspect task SHALL carry two model-graded scorers following the rubric-template contract and the `*_l2*` naming the support classifier reads:
- citation scope: every sentence's source is recognisable, no publication is repeated on consecutive sentences while source and topic are unchanged, and no sentence continues a source without a citation or a back-reference cue;
- synthesis: prior work is grouped and compared by theme rather than summarised one source after another.

#### Scenario: Repeated key fails the run
- **WHEN** a produced draft cites the same key on two adjacent sentences of one paragraph
- **THEN** the L1 verdict fails the run, naming the line

#### Scenario: Source switch passes
- **WHEN** adjacent sentences carry different key sets, such as one key and then that key with a second
- **THEN** the L1 verdict does not fail on them

#### Scenario: Deletion is not a repair
- **WHEN** a writing pass over the repetitive draft removes every citation of a reference the input cited
- **THEN** the L1 verdict fails the run, naming the reference

#### Scenario: Verdict logic covered without a model
- **WHEN** the verdict's failure modes are tested
- **THEN** L0 tests call it directly on crafted proposal texts and no model is invoked

#### Scenario: Over-citing draft trips the warning
- **WHEN** the mechanical check runs over the over-citing draft
- **THEN** it reports the repeated-citation warning, as the draft's oracle records, and reports no error

#### Scenario: Uncued deletion fails the scope grade
- **WHEN** a draft keeps one citation per paragraph but leaves the following sentences without a back-reference to the source
- **THEN** the citation-scope scorer grades the sample incorrect
