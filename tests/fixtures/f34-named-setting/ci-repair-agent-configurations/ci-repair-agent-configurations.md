# Effects of Mendwright Agent Architectures on Automated Repair of Failing Continuous Integration Builds

*Bachelor's Thesis Proposal*

## Introduction to the Topic

Failing continuous integration builds block merges and cost development teams hours of diagnosis per incident [@Ilic24Builds; @Lindgren24Taxonomy].
Language-model agents that read build output, edit code and re-run the build are now proposed as automated repairers for such failures [@Bauer25Agents].
These agents differ less in their underlying model than in their configuration, above all in how work is split between agents.
Published repair rates mix both factors, so a team choosing a configuration cannot tell which of them produced a reported improvement.
The thesis is written in a team whose continuous integration pipeline already runs Mendwright, an open-source agent framework, on its failing builds.
This thesis aims to establish to what degree Mendwright's agent architecture, with the model held fixed, changes how many failing builds it repairs and how large its accepted repairs are.

## Contribution to the State-of-the-Art

Prior work on agent-based repair falls into two clusters.
Repair studies report how often language-model agents fix failing builds and how good their repairs are [@Bauer25Agents; @Chen26Repair].
Design studies compare single-agent and planner–executor architectures [@Moreau25Planner] and measure how agents use long build logs [@Sato26Logs; @Rossi26Context].
None of these studies has measured how Mendwright's own two architectures differ on build repair with the model held fixed.
The thesis closes that gap for Mendwright with a controlled comparison in which both of its architectures run on the same model, tied to the research questions below.
Answering them matters because an architecture difference that disappears once the model is fixed would mean that effort spent on choosing between Mendwright's architectures buys nothing.
What will be new is a within-model estimate of how Mendwright's two architectures differ on build repair.
The deliverable is an evaluation of a specific instance: a controlled comparison of Mendwright's two architectures on a public benchmark of reproducible build failures.

## Research Focus and Research Questions

The focus is the effect of Mendwright's agent architecture — single-agent or planner–executor — on repair success and patch size, with the underlying model held fixed.

1. To what degree does the repair rate on reproducible build failures differ between Mendwright's single-agent and planner–executor configurations when both run on the same model?
2. To what degree do the accepted repairs of either Mendwright configuration differ from those of the other in patch size?

## Methodology for Research: Empirical Model Evaluation

Both questions ask what the agent architecture alone changes about repair outcomes, with the model held fixed.
An empirical model evaluation isolates that effect: it runs both configurations on the same benchmark failures with the same model, and measures repair rate and patch size the same way for each.

### Data and Baselines

The evaluation uses a public benchmark of about three hundred reproducible build failures from open-source projects, released for research use under a permissive license and labelled with five failure categories [@Ilic24Builds].
Within the thesis's months, a stratified subsample of one hundred failures, twenty per category, is evaluated.
Baselines are the benchmark's published non-agent repair tool and the single-agent configuration, against which the planner–executor configuration is measured.

### Experimental Setup

Both architectures are taken from Mendwright, an open-source agent framework that implements them [@Moreau25Planner], so the thesis configures existing agents rather than building one.
Both configurations receive the same truncated build-log excerpt, since agents use only part of a long build log [@Sato26Logs; @Rossi26Context], so the architecture is the only difference between them.
The model is the most recent release of one open-weight model family, chosen at the start of the thesis and documented with its version identifier and access date.
Both configurations run on that model, so the architecture effect is compared within one model (RQ1).
The model runs on the research group's GPU server, and a per-run cap on tool calls and tokens keeps the full design within the group's compute allocation.
Every run executes in Mendwright's sandbox, whose logs record each repair attempt.
A repair counts as accepted when the build, the originally failing test and the project's other tests pass in a fresh container, because a patch can overfit the failing test [@Haddad25Overfit].
Failures published after the model's training cutoff are reported separately, because earlier failures may have been seen in training [@Novak26Leakage].

### Analysis

Repair rates are compared with a paired test over the same failures, because both architectures face identical inputs (RQ1).
Patch size is measured in changed lines and compared between the accepted repairs of the two configurations (RQ2).
Each configuration runs three times per failure, and variance across runs is reported alongside the means, because agent runs are not deterministic.
The thesis expects an architecture effect smaller than the model effects that repair studies report [@Bauer25Agents]; a negligible effect would refute the premise that choosing between Mendwright's architectures is worth the effort.
Foreseeable limitations are the single benchmark, its subsample and the one model family, which bound generalization and are stated as such.

## Timeline

The thesis starts in April 2027 and is submitted in July 2027.

## References

---
references:
- id: Ilic24Builds
  type: paper-conference
  author:
  - family: Ilić
    given: M.
  issued:
    year: 2024
  title: A Benchmark of Reproducible Continuous Integration Build Failures
  container-title: Proceedings of the Example Conference on Mining Software Repositories
  DOI: 10.xxxx/xx41
- id: Lindgren24Taxonomy
  type: article-journal
  author:
  - family: Lindgren
    given: S.
  issued:
    year: 2024
  title: A Taxonomy of Continuous Integration Build Failures
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xx42
- id: Bauer25Agents
  type: paper-conference
  author:
  - family: Bauer
    given: L.
  issued:
    year: 2025
  title: Agents that Fix Builds
  container-title: Proceedings of the Example Conference on Software Engineering
  DOI: 10.xxxx/xx51
- id: Chen26Repair
  type: article-journal
  author:
  - family: Chen
    given: Y.
  issued:
    year: 2026
  title: Repair Quality Beyond Passing Tests
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xx61
- id: Haddad25Overfit
  type: paper-conference
  author:
  - family: Haddad
    given: R.
  issued:
    year: 2025
  title: Overfitting Patches in Automated Program Repair Revisited
  container-title: Proceedings of the Example Conference on Software Testing
  DOI: 10.xxxx/xx53
- id: Moreau25Planner
  type: paper-conference
  author:
  - family: Moreau
    given: J.
  issued:
    year: 2025
  title: Planner and Executor Agents for Code Changes
  container-title: Proceedings of the Example Workshop on Language Models for Code
  DOI: 10.xxxx/xx52
- id: Sato26Logs
  type: paper-conference
  author:
  - family: Sato
    given: K.
  issued:
    year: 2026
  title: Long Build Logs as Context for Code Agents
  container-title: Proceedings of the Example Conference on Software Maintenance
  DOI: 10.xxxx/xx62
- id: Rossi26Context
  type: article-journal
  author:
  - family: Rossi
    given: E.
  issued:
    year: 2026
  title: How Much Context Do Code Agents Use
  container-title: Journal of Example Machine Learning Research
  DOI: 10.xxxx/xx63
- id: Novak26Leakage
  type: paper-conference
  author:
  - family: Novak
    given: P.
  issued:
    year: 2026
  title: Benchmark Contamination in Code Language Models
  container-title: Proceedings of the Example Conference on Machine Learning Evaluation
  DOI: 10.xxxx/xx64
---
