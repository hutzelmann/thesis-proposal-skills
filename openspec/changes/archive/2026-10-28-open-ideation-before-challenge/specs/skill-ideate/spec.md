## ADDED Requirements

### Requirement: Opening phase before any challenge
Until the problem holds the student's own specifics and the student has picked it, the skill SHALL ask only experiential and curiosity questions: what happened, who was involved, how it showed, why it matters to them. In this phase it SHALL voice no weakness verdict, invoke no imagined adversary, and present no prior work as already covering the idea. A scope remark SHALL wait for the challenge phase unless the idea sits clearly outside the given scope.

#### Scenario: First concrete description of a problem
- **WHEN** the student's second message describes a problem from their workplace for the first time
- **THEN** the skill mirrors it and asks about a concrete occurrence of it, and names no weak spot, no gap and no skeptic

#### Scenario: Literature found during the opening phase
- **WHEN** grounding in the opening phase returns work close to what the student described
- **THEN** the skill names the work as a field others are working in, and asks no question about how the student's idea differs from it

#### Scenario: Idea in doubtful proximity to the scope
- **WHEN** the student's first idea touches the given research group's area only loosely
- **THEN** the skill makes no remark about the fit in the opening phase

#### Scenario: Idea clearly outside the scope
- **WHEN** the student's idea sits clearly outside the scope that was given
- **THEN** the single scope warning may come during the opening phase, as the research-group scoping requirement describes

### Requirement: Announced challenge phase
Once the problem holds the student's own specifics and the student has picked it, the skill SHALL say in one line that it now tests the idea the way a supervisor would and that not knowing an answer yet stays fine. From then on it SHALL frame every test collaboratively — what would convince the student, the part to sharpen next — and SHALL NOT invoke an imagined skeptic or name a weak spot. The push for a gap and for a differentiating angle belongs to this phase.

#### Scenario: Student picks between two directions
- **WHEN** the student has described a problem concretely and then chooses one of two directions the dialogue surfaced
- **THEN** the skill's next message announces the switch in one line before its first test

#### Scenario: Method test in the challenge phase
- **WHEN** the challenge phase is under way and the student's idea has no notion of how a result would be shown
- **THEN** the skill asks what result would convince the student themselves, not how they would convince an imagined skeptic

#### Scenario: Prior work close to the picked problem
- **WHEN** the challenge phase is under way and grounding returns a paper close to the picked problem
- **THEN** the skill shows the paper and asks what remains open for the student beyond it

### Requirement: Not knowing answered with kinds of answer
When the student says they do not know how to answer, the skill SHALL offer the conventional kinds of answer the question admits — how such things are usually shown, asked, observed or measured — as conventions, never as content for the student's problem, and SHALL NOT follow up with a harder or more abstract question. An "I don't know" SHALL count as a non-contribution for the early stop only when the student also leaves the offered kinds unused.

#### Scenario: Student cannot say how a claim would be shown
- **WHEN** the student answers a question about evidence with "I don't know"
- **THEN** the skill names the usual ways such a claim is shown — asking people, observing them, testing the thing — and asks which fits what the student has seen, choosing none for them

#### Scenario: Kinds of answer declined
- **WHEN** the skill offered the kinds of answer and the student again contributes nothing
- **THEN** that exchange counts toward the impasse as a non-contribution

### Requirement: Question rhythm
Between the bookends, the skill SHALL NOT end more than three consecutive turns on a question. At least every fourth turn SHALL be an observation that ends without a question, so the student can take up the point in their own direction.

#### Scenario: Three questions in a row
- **WHEN** the skill's last three turns between the bookends each ended on a question
- **THEN** its next turn ends on an observation without a question

### Requirement: Program requirements asked at seeding
At the closing seeding step the skill SHALL ask once whether the study program requires anything specific of the thesis — a built artifact, a page limit, a required method. On yes it SHALL name recording the requirement in the workspace guidance as the step that makes later skills apply it, and SHALL write nothing to the workspace guidance itself during ideation.

#### Scenario: Program requires a built artifact
- **WHEN** the student answers at seeding that their program requires a software deliverable
- **THEN** the skill names recording that requirement in the workspace guidance as a next step, and the seed and the workspace guidance file are written without it

#### Scenario: No program requirement
- **WHEN** the student answers that the program requires nothing specific
- **THEN** the skill seeds as before and asks no further question about it

## MODIFIED Requirements

### Requirement: Coverage-guided convergence and early stop
The skill SHALL track, internally, which of the idea's load-bearing aspects have taken shape — the problem, why it matters, candidate research-question directions, a plausible method, and feasibility within the stated time budget — and SHALL choose its next Socratic move to close the most consequential open aspect. This model SHALL never surface as a checklist, a form, or a question script. Roughly mid-session, and whenever the dialogue pivots, the skill SHALL give a one-breath stocktake in chat: what stands, what is open.

An aspect counts as taken shape only when it holds concrete, student-contributed specifics — a nameable problem, a nameable object of study, a method the student could start on — not merely plausible-sounding generalities. When the student's contributions stay generic, the skill SHALL voice the guidance's swap test as a Socratic move ("so far this could be any thesis in the area — what is yours specifically about?") rather than converging on generic content. Convergence on generic content is not convergence: a session whose aspects hold only generalities SHALL NOT trigger the seeding offer.

When about three successive exchanges produce no new contribution from the student — including exchanges that add only further generalities after the swap test has been voiced — the skill SHALL name the impasse plainly, record the state in the notes file, suggest concrete offline steps — reading the group's page, talking to the supervisor or fellow students — and end the session without seeding a proposal file. The skill SHALL NOT fill the gap with generated specifics to force convergence.

#### Scenario: Next provocation targets the emptiest slot
- **WHEN** the problem and method have taken shape but nobody has said why the work matters
- **THEN** the skill's next move surfaces the significance gap rather than polishing the method further

#### Scenario: Mid-session stocktake
- **WHEN** the dialogue has covered substantial ground and roughly half the coverage slots are filled
- **THEN** the skill states in one or two lines what stands and what is open, then continues Socratically

#### Scenario: Stalled session ends without a proposal
- **WHEN** three exchanges in a row yield "I don't know" or equivalent non-contributions, each after the skill offered the kinds of answer the question admits
- **THEN** the skill names the impasse, saves the state to the notes file, suggests offline steps, and does not create a proposal file

#### Scenario: Generic contributions do not converge
- **WHEN** the student agrees with every observation and offers only generalities ("something with AI and testing, sounds good, write it down")
- **THEN** the skill voices the swap test Socratically instead of offering to seed, and no seeding offer is made while the aspects hold only generalities

#### Scenario: Persistent genericity routes to the impasse
- **WHEN** the swap test has been voiced and roughly three further exchanges still add no specific contribution
- **THEN** the skill names the impasse, saves the notes file, and ends without seeding — it does not generate the missing specifics itself
