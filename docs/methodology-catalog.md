# Methodology catalog: ready-made workspace branches

The shipped methodology set is a default, not a ceiling. A workspace `guidelines.md` can add a branch, replace a shipped one, or disable one — run `proposal-customize`, or paste one of the declarations below into the TOML block of your workspace `guidelines.md` and adapt the guidance strings to your house style. A working example of a declared branch lives at `tests/fixtures/w04-methodology-branch/guidelines.md` in the repository.

Every entry below was judged legitimate but not default-worthy in the 2026-08-11 literature survey ([why the defaults are what they are](methodology-sources.md)). The declarations are in the exact shape the skills validate: a title in both languages, and per subsection both titles plus a `guidance` string saying what belongs under the heading — a branch without per-subsection guidance is rejected as a configuration error.

## Action Research

For theses that change an organisation's process and study the change while it happens. Distinct from a Case Study, which observes without intervening. Source: the action-research strategy in Oates, *Researching Information Systems and Computing*; ACM SIGSOFT Action Research standard.

```toml
[methodologies.action_research]
[methodologies.action_research.title]
en = "Action Research"
de = "Aktionsforschung"

[[methodologies.action_research.subsections]]
en = "Problem Diagnosis"
de = "Problemdiagnose"
guidance = "The organisation and the problem as its members experience it, the evidence that the problem is real, and the agreed scope of the intervention."

[[methodologies.action_research.subsections]]
en = "Intervention Cycles"
de = "Interventionszyklen"
guidance = "The planned change, how many plan-act-observe cycles fit the timeframe, and what is measured or recorded in each cycle."

[[methodologies.action_research.subsections]]
en = "Reflection and Learning"
de = "Reflexion und Erkenntnisse"
guidance = "How each cycle's observations feed the next, how the researcher's double role is handled, and what the organisation and the research each take away."
```

## Simulation Study

For theses whose object of study is a simulation model — scenario spaces, calibration, validity. If the simulator is merely the instrument that evaluates something you build, use Prototype Implementation instead; that boundary question decides the branch. Source: Law, "How to Build Valid and Credible Simulation Models" (WSC 2009); Sargent's verification-and-validation guidance; ACM SIGSOFT Quantitative Simulation standard.

```toml
[methodologies.simulation]
[methodologies.simulation.title]
en = "Simulation Study"
de = "Simulationsstudie"

[[methodologies.simulation.subsections]]
en = "Model and Scenario Design"
de = "Modell und Szenarienentwurf"
guidance = "The simulation model with its assumptions made explicit, the calibration data and procedure, how the model is validated against the system it stands for, and the scenario or parameter space the study covers."

[[methodologies.simulation.subsections]]
en = "Execution"
de = "Durchführung"
guidance = "The simulation tooling with versions, run lengths and termination conditions, and the number of replications per scenario given the model's stochasticity."

[[methodologies.simulation.subsections]]
en = "Analysis"
de = "Auswertung"
guidance = "How the simulation outputs answer the research questions, and how sensitivity to the model's assumptions is examined."
```

## Systematic Mapping Study

For charting a research field's structure — what exists, where, and how much — rather than weighing evidence on a narrow question. The shipped Systematic Literature Review branch already accepts a mapping-style declaration inside it; use this branch when your program treats mapping as its own method. Source: Petersen et al., "Systematic Mapping Studies in Software Engineering" (EASE 2008) and the 2015 update.

```toml
[methodologies.mapping]
[methodologies.mapping.title]
en = "Systematic Mapping Study"
de = "Systematische Mapping-Studie"

[[methodologies.mapping.subsections]]
en = "Search Strategy and Selection Criteria"
de = "Suchstrategie und Auswahlkriterien"
guidance = "The search process and the inclusion and exclusion criteria; mapping questions are broad classification questions, and the search favors breadth over exhaustiveness."

[[methodologies.mapping.subsections]]
en = "Classification Scheme"
de = "Klassifikationsschema"
guidance = "The facets papers are classified into, how the scheme is derived (typically keywording of abstracts), and why per-study quality assessment is omitted."

[[methodologies.mapping.subsections]]
en = "Mapping and Analysis"
de = "Kartierung und Auswertung"
guidance = "How classification frequencies answer the research questions, and which visualisations (facet counts, bubble plots) present the map."
```

## Repository Mining

For theses that answer questions by analyzing software repositories at scale — commits, issues, build logs — without building a tool or training a model as the contribution. If a predictive model is the point, use Empirical Model Evaluation. Source: ACM SIGSOFT Repository Mining standard.

```toml
[methodologies.mining]
[methodologies.mining.title]
en = "Repository Mining"
de = "Repository-Mining"

[[methodologies.mining.subsections]]
en = "Data Sources and Selection"
de = "Datenquellen und Auswahl"
guidance = "Which repositories or platforms are mined, how the sample is selected from them and why that selection answers the research questions, plus licensing and the handling of personal data such as names in commit metadata."

[[methodologies.mining.subsections]]
en = "Extraction and Metrics"
de = "Extraktion und Metriken"
guidance = "The acquisition procedure, the preprocessing and filtering steps, and the metrics or annotations derived — with a validation plan for any manual annotation."

[[methodologies.mining.subsections]]
en = "Analysis"
de = "Auswertung"
guidance = "How the extracted data answers the research questions, and the external-validity limits the source and selection impose."
```

## Replication Study

For repeating a published study to test whether its findings hold — a legitimate and underused thesis shape whose delta is confirming or refuting under new conditions. The declaration composes with the replicated study's method: the cycles of the original design are described here, not reinvented. Source: ACM SIGSOFT Replication standard; Fagerholm et al., "Guidelines for using empirical studies in software engineering education" (PeerJ CS, 2017).

```toml
[methodologies.replication]
[methodologies.replication.title]
en = "Replication Study"
de = "Replikationsstudie"

[[methodologies.replication.subsections]]
en = "Original Study and Replication Type"
de = "Originalstudie und Replikationstyp"
guidance = "The original study with its research questions, design, and findings; the replication's type (exact, methodological, or conceptual) and whether the original authors are involved."

[[methodologies.replication.subsections]]
en = "Deviations and Setup"
de = "Abweichungen und Aufbau"
guidance = "Every deviation from the original design, each with its justification, and the replication's own setup, data, or participants."

[[methodologies.replication.subsections]]
en = "Comparison and Analysis"
de = "Vergleich und Auswertung"
guidance = "How the replication's results are compared against the original's, and what confirming or refuting the original findings would mean."
```

## Mixed Methods — read the warning first

**Scope warning.** Mixed methods is the single most common way a Bachelor's proposal becomes undeliverable: two instruments, two recruitments, two analyses, and integration work on top, in the same months one study normally takes. The sequential designs cannot even be fully specified at proposal time, because the second phase depends on the first phase's results. Enable this branch only for students and timeframes that can carry it, and expect the convergent design (both strands in parallel, merged at interpretation) to be the only deliverable variant. A proposal that cannot name its point of interface in the Integration Plan is the scope explosion in writing — that subsection exists to make the failure visible before registration, and the branch's contract is deliberately built around it. Source: Creswell and Plano Clark, *Designing and Conducting Mixed Methods Research* (3rd ed., 2018).

```toml
[methodologies.mixed_methods]
[methodologies.mixed_methods.title]
en = "Mixed Methods"
de = "Mixed Methods"

[[methodologies.mixed_methods.subsections]]
en = "Strand Design"
de = "Strang-Design"
guidance = "The quantitative and the qualitative strand, each with its data, procedure, and analysis, and the design type (convergent, explanatory sequential, exploratory sequential) — for a short thesis, convergent with two tightly bounded strands."

[[methodologies.mixed_methods.subsections]]
en = "Integration Plan"
de = "Integrationsplan"
guidance = "The named point of interface where the strands merge, connect, or build on one another, and the joint display or comparison that performs the integration; two studies without this point are not mixed methods."

[[methodologies.mixed_methods.subsections]]
en = "Joint Analysis"
de = "Gemeinsame Auswertung"
guidance = "How meta-inferences are drawn from both strands together to answer the research questions, and what happens if the strands disagree."
```

## Design Science Research

Not an entry — a rename. The shipped Prototype Implementation branch *is* design science research in compressed form: Previous Work carries problem grounding, Requirements carries the solution objectives, Evaluation carries demonstration and evaluation with a named empirical method. A department that wants the DSR vocabulary can declare a branch with id `prototype` and DSR-flavored titles, which replaces the shipped branch while keeping its role; duplicating it under a second id would force students to choose between two names for the same method.

## Not recommended

**Grounded Theory** is deliberately absent. Stol, Ralph and Fitzgerald (ICSE 2016) found it misapplied even in published research, and its defining commitment — no up-front research questions, sampling driven by emerging theory — contradicts a proposal that must state falsifiable questions and a plan. A workspace can still declare it, but this catalog will not hand out the declaration.
