## ADDED Requirements

### Requirement: Construction goals have a home
The guidance SHALL state where an implementation or construction goal belongs, not only that it is not a research question. A goal describes what the work will do; a research question asks what the work will find out. A goal phrased as "how can X be built" SHALL be directed to the contribution section, where the work describes itself, rather than merely rejected.

#### Scenario: Student writes a construction goal as a research question
- **WHEN** the guidance is consulted about "How can a dashboard for X be built?" appearing in the research-question list
- **THEN** it names the section that statement belongs in, rather than only reporting that it is not analytical

### Requirement: Prior work is organised thematically
The guidance SHALL require the contribution section to group prior work into thematic clusters rather than presenting it chronologically or one source at a time, to compare and contrast within a cluster rather than summarise each source in turn, and to close by naming the gap the thesis fills with explicit reference to the research questions.

#### Scenario: Reading-list contribution section
- **WHEN** a contribution section walks through one publication after another without comparing them
- **THEN** the guidance identifies it as a reading list rather than a synthesis, and asks for the shared limitation of each cluster

### Requirement: Standards are legitimate sources
The guidance SHALL state that published standards and regulations are legitimate — and frequently the only correct — sources for normative definitions, required behavior, and terminology, and SHALL require citing the standard by its own designation and year rather than a vendor's or a blog's summary of it. The guidance SHALL also state the limit: a standard establishes what is required, never that an approach works, so empirical claims continue to require peer-reviewed evidence.

#### Scenario: Normative definition needed
- **WHEN** a proposal needs the defined meaning of a term fixed by an ISO, IEEE, ETSI, SAE, UNECE, or EU regulatory document
- **THEN** the guidance treats the standard itself as the correct source and rejects a vendor page restating it

#### Scenario: Standard cited as evidence of effectiveness
- **WHEN** a proposal cites a standard to support a claim that an approach performs well
- **THEN** the guidance requires peer-reviewed evidence for that claim, because the standard cannot supply it

### Requirement: Research involving human participants
The guidance SHALL cover, as advisory prose rather than as a required section or a mechanical check, what a proposal involving human participants is expected to address: the ethics route and the approval required before data collection begins, how informed consent is obtained and recorded, what personal data is collected and how it is pseudonymised, retained, and legally justified, how risk is bounded and how a participant can stop, and whether and how participants are compensated. The guidance SHALL bound its own scope, asking for a few precise sentences inside the existing methodology subsections rather than a compliance appendix.

#### Scenario: User study proposal silent on ethics
- **WHEN** a proposal declares a study with human participants and addresses none of these points
- **THEN** the guidance identifies the omission as the first question a supervisor will ask, while no mechanical check reports an error

#### Scenario: Guidance is not a new section
- **WHEN** a proposal addresses consent and data handling inside its Preparation subsection
- **THEN** that satisfies the guidance, and no separate ethics section is expected

### Requirement: Anticipated outcomes are stated as expectations
The guidance SHALL require that any statement about what the work will yield is phrased as an expectation rather than as a result already obtained, and that the foreseeable limitations — sample size, generalisation, access, time — are named rather than left implicit. This SHALL NOT be read as permitting an expected-results section, which remains forbidden content.

#### Scenario: Proposal asserts its outcome
- **WHEN** a proposal states that the approach improves a metric, as though the work were done
- **THEN** the guidance requires the claim be re-phrased as an expectation

### Requirement: Reference floor is not a reference target
The guidance SHALL distinguish the mechanically checked minimum number of references from the number a submitted proposal is expected to carry. The minimum SHALL be described as a floor that catches an empty or near-empty bibliography; the prose SHALL state the working range separately, so that meeting the floor is never read as meeting the bar.

#### Scenario: Proposal sits at the floor
- **WHEN** a proposal cites exactly the minimum number of references
- **THEN** the mechanical check passes and the guidance still identifies the bibliography as thin
