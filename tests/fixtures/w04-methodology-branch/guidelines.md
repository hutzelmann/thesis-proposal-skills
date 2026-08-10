# Workspace Guidelines

My supervisor runs industrial case studies and does not accept a purely theoretical thesis.

```toml
[methodologies.case_study]
[methodologies.case_study.title]
en = "Case Study"
de = "Fallstudie"

[[methodologies.case_study.subsections]]
en = "Case and Context"
de = "Fall und Kontext"
guidance = "The organisation, system, or project studied, why it suits the research questions, and what access to it exists."

[[methodologies.case_study.subsections]]
en = "Data Collection"
de = "Datenerhebung"
guidance = "Which sources are drawn on — interviews, documents, repository history — and how each is recorded."

[[methodologies.case_study.subsections]]
en = "Analysis"
de = "Analyse"
guidance = "How the collected material is coded and synthesised into answers, and what threatens the validity of a single-case result."

[methodologies.theoretical]
enabled = false
```

Case studies are the house method here; describe the case before anything else, and never generalise from one case without saying so.
