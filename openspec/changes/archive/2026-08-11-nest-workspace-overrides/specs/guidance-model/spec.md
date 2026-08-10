## MODIFIED Requirements

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block plus freeform prose. Absent file means pure defaults.

Every override key SHALL be the same key path the value occupies in the structured guidance data. There SHALL be exactly one naming rule: no hand-named aliases, and no flat spelling accepted alongside a nested one. The overridable set SHALL cover the reference minimum, the required-section list, the forbidden-heading list, the timeline detail mode, the page limit, and the research-question count bounds.

Merge semantics: a user key wins over the default per key; list values replace defaults entirely; a default-forbidden section may be allowed again by omitting it from the replacement list.

The timeline detail mode SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets the timeline detail mode to `detailed`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` raises the reference minimum to 8
- **THEN** a proposal with 5 references fails the reference-count check

#### Scenario: Research-question bounds overridden
- **WHEN** `guidelines.md` sets the research-question upper bound to 3
- **THEN** a proposal declaring four research questions fails the count check

#### Scenario: Override key mirrors the structure path
- **WHEN** a value is nested in the structured guidance data
- **THEN** the override key for it is nested identically, and no alternative spelling is honoured
