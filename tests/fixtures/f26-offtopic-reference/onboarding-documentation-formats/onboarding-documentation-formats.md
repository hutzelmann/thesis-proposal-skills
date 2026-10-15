# Onboarding Documentation Formats and First-Contribution Success

*Master's Thesis Proposal*

## Introduction to the Topic

Open-source projects lose most prospective contributors before their first merged change [@Fenwick23Onboarding].
Maintainers respond by rewriting onboarding documentation, usually without evidence about which format helps.
Guided walkthroughs, reference manuals, and annotated example changes coexist in the same ecosystems and are chosen by habit [@Okonkwo25Formats].
This thesis measures which of those formats shortens the path to a first accepted contribution.

## Contribution to the State-of-the-Art

Work on newcomer barriers catalogues obstacles and reports what newcomers say slowed them down [@Fenwick23Onboarding; @Okonkwo25Formats].
Both studies are observational: the documentation a newcomer met was whatever the project already had, so format and project confound each other.
Neither isolates the format itself, and neither reports how long a first contribution took.
This thesis breaks that confound by assigning the format rather than observing it, and adds the delta the cluster lacks: a causal estimate of format effect on time-to-first-contribution, with comprehension measured separately from speed.
The deliverable is a report of findings plus the task materials needed to repeat the experiment.

## Research Focus and Research Questions

The study examines whether the structure of onboarding documentation changes how quickly and how correctly a newcomer completes a first contribution to an unfamiliar codebase.

1. To what degree does documentation format affect the time a newcomer needs to submit a first acceptable change?
2. Under which conditions does a guided walkthrough outperform a reference manual for comprehension of project conventions?
3. How does prior experience with the project's language moderate the format effect?

## Methodology for Research: Controlled Experiment

### Hypotheses and Variables

The independent variable is documentation format, assigned at three levels: guided walkthrough, reference manual, and annotated example changes.
The dependent variables are time to a submitted acceptable change (RQ1) and a scored comprehension questionnaire on project conventions (RQ2).
Prior experience with the project's language is recorded as a moderating variable (RQ3).

### Design and Participants

Participants are recruited from two university programmes and randomly assigned to one format, working on the same prepared task in a seeded repository.
A between-subjects design avoids the learning effect a repeated task would introduce.

### Statistical Analysis

Time-to-submission is compared across the three formats with a one-way analysis of variance and planned contrasts (RQ1).
Comprehension scores are compared the same way, reported separately from the timing outcome (RQ2).
The moderating effect of prior language experience enters as an interaction term (RQ3).

## Timeline

The thesis starts in October 2026 and is submitted in March 2027.

## References

---
references:
- id: Fenwick23Onboarding
  type: article-journal
  author:
  - family: Fenwick
    given: R.
  issued:
    year: 2023
  title: Barriers to the First Contribution in Open Source Projects
  container-title: Journal of Example Software Engineering Studies
  DOI: 10.xxxx/xxxx1
- id: Okonkwo25Formats
  type: paper-conference
  author:
  - family: Okonkwo
    given: A.
  issued:
    year: 2025
  title: Documentation Formats Newcomers Meet in Practice
  container-title: Proceedings of the Example Conference on Collaborative Software
  DOI: 10.xxxx/xxxx2
- id: Serrano24Sampling
  type: article-journal
  author:
  - family: Serrano
    given: M.
  issued:
    year: 2024
  title: Recruiting Student Participants for Software Engineering Experiments
  container-title: Journal of Example Empirical Methods
  DOI: 10.xxxx/xxxx3
- id: Halvorsen24Kernel
  type: article-journal
  author:
  - family: Halvorsen
    given: T.
  issued:
    year: 2024
  title: Scheduling Latency in Preemptible Kernels - A Measurement Study
  container-title: Journal of Example Systems Measurement
  DOI: 10.xxxx/xxxx4
---
