# skill-ideate Delta

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
- **WHEN** three exchanges in a row yield "I don't know" or equivalent non-contributions
- **THEN** the skill names the impasse, saves the state to the notes file, suggests offline steps, and does not create a proposal file

#### Scenario: Generic contributions do not converge
- **WHEN** the student agrees with every observation and offers only generalities ("something with AI and testing, sounds good, write it down")
- **THEN** the skill voices the swap test Socratically instead of offering to seed, and no seeding offer is made while the aspects hold only generalities

#### Scenario: Persistent genericity routes to the impasse
- **WHEN** the swap test has been voiced and roughly three further exchanges still add no specific contribution
- **THEN** the skill names the impasse, saves the notes file, and ends without seeding — it does not generate the missing specifics itself
