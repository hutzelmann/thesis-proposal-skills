## ADDED Requirements

### Requirement: Repeated citations reported as a warning
The skill SHALL report as a warning (never a hard failure, false positives acknowledged) every sentence that cites exactly the same set of references as the sentence before it. Sentences are compared within a paragraph and across consecutive items of one list; a blank line, a heading or a table row ends the comparison. Turning repeated citations into bullet points therefore does not hide them. Sentences are delimited by sentence punctuation outside citation brackets, not by line breaks: a sentence wrapped across lines is one sentence, and a page locator such as `[@key, S. 12]` never splits one. Code spans and fenced blocks SHALL be ignored, as they are for every citation scan. A sentence whose set of cited references differs from its predecessor's SHALL NOT be reported, because a change of source is what the guidance asks to cite. Each finding SHALL carry its line and name the repeated references, and its message SHALL name the fix: cite the publication once, opening with the author-in-text form, and refer back to it in words.

The finding reports the surface pattern only. Whether a sentence without a citation still reads as attributed stays a judgement for the agent and the reader.

#### Scenario: Same reference on adjacent sentences
- **WHEN** two adjacent sentences in one paragraph each cite the same single reference
- **THEN** the check emits a warning for the second sentence, citing its line and naming the reference

#### Scenario: Same group on adjacent sentences
- **WHEN** two adjacent sentences each cite the same two references, in any order
- **THEN** the check emits a warning naming both references

#### Scenario: Source switch
- **WHEN** one sentence cites one reference and the next cites that reference together with another
- **THEN** no warning is emitted

#### Scenario: New paragraph
- **WHEN** the last sentence of one paragraph and the first sentence of the next cite the same reference
- **THEN** no warning is emitted, because the guidance asks to cite again at a new paragraph

#### Scenario: Repetition moved into bullet points
- **WHEN** consecutive items of one list each cite the same reference
- **THEN** the check emits a warning for every item after the first

#### Scenario: Page locators and wrapped lines
- **WHEN** two adjacent sentences cite the same reference with different page locators, or the second sentence wraps onto a following line before its citation
- **THEN** the check still emits the warning

## MODIFIED Requirements

### Requirement: Hindsight leakage reported as a warning
The skill SHALL report as warnings (never hard failures, false positives acknowledged) prose that states the proposal's own work as already done: result verbs in the first person or with the work as subject — showed, found, demonstrated, outperformed, and their German equivalents — and quantitative outcomes stated as findings. A proposal describes work that has not happened, so such a sentence is either a draft written after the work began or a proposal derived from a finished thesis.

The check SHALL fire only on sentences that are not attributed to prior work. Reporting what prior work established is what the Contribution section is for, and a rule that cannot tell "@Rivera23 showed that scheduling reduces water use" from "we showed that scheduling reduces water use" would fire on every correctly written proposal. A sentence is attributed when it carries a citation, or when it continues an attributed run: the preceding sentence in the same paragraph is attributed, and the sentence opens with a back-reference cue — a pronoun, possessive, or noun phrase referring to the cited work or its authors, in English and in German. The cue SHALL stand at the start of the sentence: first, after a single connective set off by a comma, after a preposition introducing a possessive or "the authors", or, in German verb-second order, as the subject directly after the finite verb. A cue in object position does not open a sentence. A reporting clause that names the cited authors as reporters ("…, they report, …", "so die Autoren") SHALL count as a cue wherever it stands, because it attributes the sentence explicitly. "It" counts as a cue unless it opens an expletive construction ("It is shown …", "It was found …"); the possessive "its" always counts. A sentence that speaks in the first person, or that names the work with the words the guidance prescribes for the thesis itself ("the study", "die Studie"), SHALL never count as a continuation. A blank line or a heading ends a run, and so does any sentence that is neither cited nor cued. Sentences are delimited by sentence punctuation outside citation brackets, not by line breaks. The guidance asks for exactly this form of continuation instead of a repeated citation, so the check SHALL NOT reward re-citing a source in the next sentence over referring back to it. An uncited, uncued sentence after a cited one keeps the warning, because its reader cannot tell that it reports prior work either. Each warning SHALL carry its line, quote the text it matched, and name both admissible fixes: attributing the result, by a citation or by a back-reference cue continuing a cited sentence, or writing it as a plan.

The skill SHALL NOT attempt to judge whether a research question is a settled claim in disguise. That reading requires knowing what the work found, which the document does not state; it belongs to the review skill's agent pass and to the reader.

#### Scenario: Result claim without a citation
- **WHEN** the body states that the work demonstrated an effect, in a sentence carrying no citation and continuing no attributed run
- **THEN** the check emits a warning citing the line and quoting the matched text

#### Scenario: Result attributed to prior work
- **WHEN** the same claim is attributed to a cited reference
- **THEN** no warning is emitted

#### Scenario: Result reported in a cued continuation
- **WHEN** a sentence citing a publication is followed, in the same paragraph, by a sentence that opens with a back-reference to that work or its authors and reports its result
- **THEN** no warning is emitted, because the continuation is attributed

#### Scenario: Uncued continuation
- **WHEN** a sentence citing a publication is followed, in the same paragraph, by a sentence that reports a result without a citation and without a back-reference cue
- **THEN** the check emits a warning naming the cue and the citation as fixes

#### Scenario: Run ends at the paragraph
- **WHEN** a sentence opening with a back-reference cue reports a result at the start of a paragraph that follows the cited sentence's paragraph
- **THEN** the check emits a warning, because attribution does not cross a paragraph break

#### Scenario: Run broken by the thesis's own sentence
- **WHEN** an uncited, uncued sentence stands between a cited sentence and a cued sentence reporting a result
- **THEN** the check emits a warning on the cued sentence, because the intervening sentence ended the run

#### Scenario: Attribution carried by a reporting clause or a referential pronoun
- **WHEN** a cited sentence is followed by "Most projects, they report, merge them unreviewed.", then "It uses three features.", then "Its score dropped by 30 %."
- **THEN** no warning is emitted, because every sentence continues the attributed run

#### Scenario: Own result naming the cited work as object
- **WHEN** a sentence after a cited one reports the thesis's own result while mentioning the cited work as an object, such as "We outperformed their baseline by 20 %."
- **THEN** the check emits a warning, because the sentence does not open with a back-reference and speaks in the first person

#### Scenario: The thesis named as the guidance prescribes
- **WHEN** a sentence after a cited one opens with "The study" or "Die Studie" and reports a result
- **THEN** the check emits a warning, because these words name the thesis itself in the prescribed third-person style

#### Scenario: German cued continuation
- **WHEN** a German proposal follows a cited sentence with a sentence opening with a German back-reference such as "Ihre Auswertung" that reports a result
- **THEN** no warning is emitted

#### Scenario: Quantitative outcome stated as a finding
- **WHEN** the body reports a measured improvement as an achieved number, in a sentence carrying no citation and continuing no attributed run
- **THEN** the check emits a warning

#### Scenario: Planned measurement
- **WHEN** the body states what will be measured and against which baseline
- **THEN** no warning is emitted, because the sentence describes a plan rather than an outcome

#### Scenario: Research question that reads like a conclusion
- **WHEN** a research question is phrased so that it presupposes its own answer
- **THEN** the mechanical check stays silent and the judgment is left to the review skill
