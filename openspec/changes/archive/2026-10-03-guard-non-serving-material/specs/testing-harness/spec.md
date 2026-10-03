## MODIFIED Requirements

### Requirement: Substance-verdict coverage
The fixture corpus SHALL contain at least one hollow control: a proposal that passes every mechanical check with zero errors and zero warnings while failing at least the guidance's swap, delta, and executability tests — generic well-sounding text naming no object of study and no delta beyond its citations. Its oracle SHALL encode the check-clean state, so the fixture doubles as proof that "mechanically clean" carries no substance signal. Naming those three tests is a statement about this fixture, not about how many tests exist.

A metered review task over the hollow control SHALL assert: the review file opens with the verdict "no viable thesis core"; at least two failed substance tests are cited by name; the proposal file is byte-identical after the run. The verdict-line assertions SHALL be a pure function in the shared verdict module, exercisable by L0 tests without a model call. A model-graded scorer SHALL additionally judge that the review states what kind of work would change the verdict and that no finding is softened into needs-revision phrasing.

#### Scenario: Hollow control stays check-clean
- **WHEN** the mechanical check runs over the hollow fixture
- **THEN** it reports zero errors and zero warnings, exactly as the fixture's oracle encodes

#### Scenario: Review task fails on a soft verdict
- **WHEN** the review of the hollow fixture opens with "needs revision" or omits the failed-test names
- **THEN** the L1 verdict fails the run without model involvement

#### Scenario: Verdict logic covered without a model
- **WHEN** the verdict-line function's failure modes are tested
- **THEN** L0 tests call it directly on crafted review texts and no model is invoked

## ADDED Requirements

### Requirement: Scoping-vocabulary containment measured against a non-aligned idea
The harness SHALL exercise research-group scoping with at least one scenario whose student idea is plausible for the stated program and touches none of the scoping fixture's research areas, and at least one whose idea overlaps exactly one area of a multi-area fixture. A scenario whose student idea restates one of the fixture's research areas SHALL NOT be the only coverage of the scoping fetch: vocabulary bleed and legitimate adoption are indistinguishable in such a run, so it measures the fetch but not the containment.

The scoping fixture's vocabulary SHALL be carried in two distinct sets, because one term cannot serve both roles: a chat-visibility set whose appearance in the transcript proves the fetch happened, and a containment set whose appearance in any produced file or issued literature query fails the run. Group, university, and program names remain leaks wherever the existing scoping requirements already place them.

Containment SHALL be decided by a pure function in the shared verdict module that takes the dialogue transcript, the produced workspace files, and the queries the run issued, and fails a run for any containment term absent from every student turn but present in a produced file or a query. It SHALL be exercisable by L0 tests without a model call.

#### Scenario: Adjacent idea keeps the profile out
- **WHEN** the scoping scenario's student idea touches none of the fixture's research areas and the run seeds a proposal
- **THEN** the run passes only if no containment term appears in the seed file, the notes file, or any literature query the session issued

#### Scenario: Partial overlap contains the rest
- **WHEN** the student's idea overlaps one research area of the multi-area fixture
- **THEN** the vocabulary of the non-overlapping areas fails the run if it reaches a produced file, while the overlapping area's terms are judged by whether a student turn voiced them

#### Scenario: Student-voiced term is not a leak
- **WHEN** a containment term occurs in a student turn before it appears in a produced file
- **THEN** the containment function does not count it against the run

#### Scenario: Fetch still proven visible
- **WHEN** a scoping scenario completes
- **THEN** the chat-visibility set is still required in the transcript, so a run that made no outbound request fails rather than passing vacuously

### Requirement: Off-topic-reference resolution covered
The fixture corpus SHALL carry a proposal whose `references:` block holds two uncited entries that are each well-formed and academically legitimate, and whose correct resolutions are opposite: one that a claim already in the proposal needs, and one that is topically adjacent but which no research question, delta statement, or method step needs. The mechanical finding SHALL be identical for both, so that only reading the proposal distinguishes them — a fixture carrying just the second would be passed by a run that removes every uncited entry on sight, which is the same failure to judge in the other direction. Its `expected.json` oracle SHALL record that the check reports both entries as uncited and reports nothing about the relevance of either, pinning the formalization boundary: relevance stays agent judgment.

The harness SHALL exercise a writing pass over that fixture and SHALL fail the run when the pass resolves an uncited-reference finding by adding a sentence that cites the entry without a research question, delta statement, or method step depending on it. Citing the needed entry at the claim that needs it SHALL pass; removing the unneeded entry with a recorded reason, and leaving it uncited with a stated reason, SHALL both pass.

#### Scenario: Carrier sentence fails the run
- **WHEN** a writing pass over the fixture produces a new sentence whose only function is to cite the otherwise-uncited entry
- **THEN** the run fails, naming the sentence

#### Scenario: Removal with a reason passes
- **WHEN** a writing pass removes the unneeded entry from `references:` and records it in Excluded Literature with a one-line reason
- **THEN** the run passes

#### Scenario: The needed entry is cited, not removed
- **WHEN** the fixture's other uncited entry supports a claim the proposal already makes
- **THEN** a pass that removes it fails the run, and a pass that cites it at that claim passes

#### Scenario: Check stays silent on relevance
- **WHEN** the mechanical check runs over the fixture
- **THEN** it reports the entry as uncited and reports no finding about whether the entry is relevant, as the oracle records

### Requirement: Substance-test names consistent across guidance, skills, specs and pins
An offline test SHALL assert that the substance tests named in the prose guidance are exactly the set cited wherever the guidance's tests are referred to by name or by count — the skill bodies that judge substance, the verbatim pins that quote a phrase naming them, and the specifications that enumerate them. A site that names a test the guidance does not, omits one the guidance names, or states a count that disagrees with it SHALL fail the offline suite.

Specifications SHALL be checked only while no change is in flight: a specification is rewritten from a change's delta when that change is archived, so between implementation and archive it describes the previous set by design, and failing the suite for that window would make the gate something to route around.

Two constructs SHALL NOT be reported as drift, because neither is a claim about the set: an enumeration explicitly marked as partial, such as a verdict citing only the tests that actually failed; and a number that states an evidence bar — how many tests must fail — rather than how many exist.

This test is a prerequisite for changing the set: it SHALL be in place before a test is added to or removed from the guidance, so that every dependent site fails loudly in the same change rather than drifting silently.

#### Scenario: Test added to the guidance alone
- **WHEN** a substance test is added to the prose guidance and a dependent skill body still enumerates the previous set
- **THEN** the offline suite fails and names the file that disagrees

#### Scenario: Count drifts in a pinned sentence
- **WHEN** a pinned sentence states a number of substance tests that no longer matches the guidance
- **THEN** the offline suite fails

#### Scenario: Evidence bar is not a set size
- **WHEN** a specification states that at least three substance tests must fail decisively
- **THEN** the offline suite does not read that number as a claim about how many tests exist

#### Scenario: Specification stale while its change is in flight
- **WHEN** the guidance names a new set and the change carrying that delta has not been archived
- **THEN** the offline suite skips the specifications and still checks the guidance, the skill bodies, and the pins

#### Scenario: All sites agree
- **WHEN** guidance, skill bodies, specifications, and pins name the same set
- **THEN** the offline suite passes without a model call
