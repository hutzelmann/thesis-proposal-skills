# Where the default methodologies come from

The default methodology set was checked against the research-methods literature in a survey on 2026-08-11 (archived OpenSpec changes `2026-08-11-align-section-guidance-with-literature` through `2026-08-11-add-case-study-branch` carry the per-change evidence). This page records, per branch, the taxonomy or standard it derives from, where its subsection contract comes from, and what the compression to three subsections deliberately left out. It exists so that "why these seven?" gets a citation instead of a shrug.

Two constraints shaped the set:

- **Expressiveness, not popularity.** Stol and Fitzgerald's ABC framework (ACM TOSEM 27(3), 2018) spans the space of knowledge-seeking research strategies. A default set that cannot express a strategy students actually need has a hole; the survey used the framework as that test.
- **The default bar.** A branch ships by default only when most students in a computer-science department plausibly need it. Everything else is a workspace declaration — the configurability mechanism answers "someone might want it", so defaults never have to.

## The seven default branches

### Prototype Implementation

- **Derives from:** the solution-seeking (design science) mode of research — Hevner, March, Park and Ram, "Design Science in Information Systems Research", MIS Quarterly 28(1), 2004; Peffers et al., "A Design Science Research Methodology", JMIS 24(3), 2007. In the German-language tradition this is the constructive paradigm that Wilde and Hess (WIRTSCHAFTSINFORMATIK 49(4), 2007) found dominant in computing research.
- **Contract from:** the ACM SIGSOFT Empirical Standards' Engineering Research standard — artifact described, need justified, compared empirically against state-of-the-art alternatives or the absence justified, and the evaluation's empirical form named.
- **Deliberately compressed:** Hevner's design-as-search and two-audience communication guidelines are prose guidance rather than subsections; a full DSR framing (Peffers' six activities) is treated as a vocabulary variant of this branch, not a separate one.

### Theoretical Analysis

- **Derives from:** the formal-theory strategy in Stol and Fitzgerald's framework; result types "analytic model" and "formal model" in Shaw, "Writing Good Software Engineering Research Papers", ICSE 2003.
- **Contract from:** house guidance. No community reporting standard exists for formal work (the SIGSOFT FormalMethods document is an unpublished draft); the branch rests on the General Standard's requirements only.
- **Deliberately compressed:** nothing — the branch predates the survey and the survey found no external contract to hold it against.

### Systematic Literature Review

- **Derives from:** Kitchenham and Charters, "Guidelines for performing Systematic Literature Reviews in Software Engineering", EBSE Technical Report 2007-01.
- **Contract from:** that report's review-protocol components: search strategy, selection criteria, study quality assessment (a mandatory stage there, which is why the second subsection names it), extraction, synthesis with the meta-analysis question answered. PICOC question framing follows Petticrew and Roberts (2006) as adopted by Kitchenham and Charters.
- **Deliberately compressed:** selection procedures for multi-assessor teams (a single student presents the protocol to the supervisor instead — the report's own advice for PhD students); the dissemination and timetable components, which the proposal's other sections carry. Mapping-style reviews (Petersen et al., EASE 2008 and IST 64, 2015) are a declared variant inside the branch rather than a sibling branch, because their skeleton is identical and only the depth and quality-assessment stance differ.

### User Study

- **Derives from:** the questionnaire-survey and interview-study (qualitative survey) guidance in the ACM SIGSOFT Empirical Standards; the survey/case-study/experiment partition in Runeson and Höst (EMSE 14(2), 2009) is why this branch is bounded to observational work.
- **Contract from:** the same standards, compressed to preparation, procedure, and analysis; the human-participants ethics advisory in the guidelines carries the standards' ethics supplements.
- **Deliberately compressed:** instrument validation and sampling detail are prose expectations, not subsections. Hypothesis-testing with manipulated treatments is excluded by the boundary to Controlled Experiment — the survey found "user study" is not a term of art, and the branch is deliberately the observational half of the partition.

### Controlled Experiment

- **Derives from:** Wohlin, Runeson, Höst, Ohlsson, Regnell and Wesslén, *Experimentation in Software Engineering* (Springer, 2012; 2nd ed. 2024); the ACM SIGSOFT Experiments standard.
- **Contract from:** the book's planning phase: hypothesis formulation, variables selection, subjects, design, instrumentation, validity — folded into three subsections that keep the planning order (hypotheses before variables, design before tests).
- **Deliberately compressed:** the externally proposed split into separate Independent Variables and Dependent Variables subsections was rejected against this literature: the book treats variable selection as one planning step whose point is the hypothesis relating manipulated to measured, and the split left hypotheses, design, and validity homeless. The manipulated-versus-measured distinction is enforced by the contract prose inside one subsection instead. GQM-style scoping stays out; the proposal's research-questions section carries that weight.

### Empirical Model Evaluation

- **Derives from:** the ACM SIGSOFT Data Science standard; in ABC terms, a laboratory experiment with programmed subjects, which is also why benchmark studies are homed here (Stol and Fitzgerald note the equivalence to benchmarking).
- **Contract from:** the standard's essentials plus the model-evaluation literature: Raschka, "Model Evaluation, Model Selection, and Algorithm Selection in Machine Learning" (arXiv:1811.12808), and the reproducibility-checklist practice around ML venues — data provenance and licensing, baselines or their justified absence, leakage-aware split protocol, metric justification, variance across runs.
- **Deliberately compressed:** dataflow diagrams and infrastructure detail are expectations inside Experimental Setup rather than subsections; repository-mining studies without a modeling component are near this branch but not identical to it — a workspace can declare Repository Mining separately (see the catalog).

### Case Study

- **Derives from:** Runeson and Höst, "Guidelines for conducting and reporting case study research in software engineering", Empirical Software Engineering 14(2), 2009 (book form: Runeson, Höst, Rainer, Regnell, Wiley 2012); the ACM SIGSOFT Case Study standard; the field-study strategy in ABC terms.
- **Contract from:** the guidelines' plan elements — objective, the case, theory, research questions, methods, selection strategy — with intentional case selection, units of analysis, triangulation, and the single-case limitation carried into the three subsections.
- **Deliberately compressed:** the full case-study protocol as a living document is a thesis-time artifact, not a proposal subsection; the validity scheme (construct/internal/external/reliability) is an expectation inside Analysis. Intervening in the case is excluded by the boundary note: that is action research, a workspace branch.

## Why not more

- **Design Science Research** — a vocabulary for what Prototype Implementation already is (build plus evaluate); two near-identical branches would force a distinction the literature does not sustain. Departments that want the DSR vocabulary can rename via a workspace declaration.
- **Mixed Methods** — deliverability, not legitimacy: Creswell and Plano Clark's sequential designs cannot be fully specified at proposal time because phase two depends on phase-one results, and mixed-methods training is doctoral-level where it exists at all. The catalog carries it with a warning and an integration-plan contract.
- **Grounded Theory** — Stol, Ralph and Fitzgerald (ICSE 2016) found it misapplied even in published research ("method slurring"), and its own application criterion — no up-front research questions — collides with a proposal shape that requires them.
- **Simulation Study** — methodologically distinct (Law's and Sargent's validation obligations have no home in the Prototype contract; the discriminating test is whether the simulation model is the object of study or the measuring instrument), but no prevalence evidence cleared the default bar. The catalog carries a ready-made declaration.
- **Systematic Mapping Study** — a review-type value inside the Systematic Reviews standard, not a method with its own standard; the SLR branch requires declaring the type instead.
- **Replication** — advocated as excellent student work (Fagerholm et al., PeerJ CS 3:e131, 2017) but not prevalent, and its standard is relational: it composes with the replicated method's branch rather than standing alone.

An honest caveat the survey recorded: no peer-reviewed census of methods used in CS Bachelor's and Master's theses exists. The set-level judgements above rest on method taxonomies, standards coverage, and field-level analyses — the best available evidence, named as such.
