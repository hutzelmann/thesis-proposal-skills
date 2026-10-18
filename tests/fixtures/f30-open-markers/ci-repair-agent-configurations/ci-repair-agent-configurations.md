# Effects of Agent Configuration on Automated Repair of Failing Continuous Integration Builds

*Master's Thesis Proposal*

## Introduction to the Topic

Failing continuous integration builds block merges and cost development teams hours of diagnosis per incident [@Ilic24Builds; @Lindgren24Taxonomy].
Language-model agents that read build output, edit code and re-run the build are now proposed as automated repairers for such failures [@Bauer25Agents].
These agents differ less in their underlying model than in their configuration: how work is split between agents, and which context each agent sees.
Published repair rates mix both factors, so a team choosing a configuration cannot tell which of them produced a reported improvement.
This thesis aims to establish to what degree the configuration of a repair agent, with the model held fixed, changes how many failing builds it repairs and how good the accepted repairs are.

## Contribution to the State-of-the-Art

Prior work on agent-based repair falls into two clusters.
Repair studies report the success of one agent configuration on issue or build benchmarks, each pairing its configuration with a different model [@Bauer25Agents; @Chen26Repair].
Counting passing builds alone overstates their success, because an accepted patch can overfit the failing test [@Haddad25Overfit].
Architecture studies compare single-agent and planner–executor designs on general coding tasks, but not on build failures, whose context is dominated by long build logs [@Moreau25Planner; @Sato26Logs; @Rossi26Context].
Both clusters share a limitation: configuration and model vary together, so none of these studies isolates the effect of the configuration on build repair.
The thesis fills that gap with a controlled comparison in which each configuration runs on the same models, tied to the research questions below.
Answering them matters because practitioners adopt configurations from leaderboards, and an effect that disappears once the model is fixed would mean that effort spent on configuration buys nothing.
What will be new is a within-model estimate of configuration effects on build repair, for teams and tool builders who choose between configurations rather than between models.
The deliverable is an evaluation: a controlled comparison of four agent configurations on a public benchmark of reproducible build failures.

## Research Focus and Research Questions

The focus is the effect of agent configuration — the split of work between agents and the build context they receive — on repair success and repair quality, with the underlying model held fixed.

1. To what degree does the repair rate on reproducible build failures differ between a single-agent and a planner–executor configuration when both run on the same model?
2. Under which failure categories does access to the full build log change the repair rate of either configuration?
3. To what degree do accepted repairs from the two architectures differ in patch size and in their judged maintainability?

## Methodology for Research: Empirical Model Evaluation

All three questions ask what the agent configuration alone changes about repair outcomes, with the model held fixed.
An empirical model evaluation isolates that effect: it runs every configuration on the same benchmark failures with the same model, and measures repair rate, patch size and maintainability the same way for each.

### Data and Baselines

The evaluation uses a public benchmark of about three hundred reproducible build failures from open-source projects, released for research use under a permissive license and labelled with five failure categories [@Ilic24Builds].
Baselines are the benchmark's published non-agent repair tool and the single-agent configuration with the truncated log excerpt, against which each added configuration element is measured.

### Experimental Setup

Both architectures are taken from an open-source agent framework that implements them [@Moreau25Planner], so the thesis configures existing agents rather than building one.
Four configurations cross the two architectures, single-agent and planner–executor, with two context conditions, a truncated log excerpt and the full build log (RQ2).
The models are two current model families, one open-weight and one hosted, chosen at the start of the thesis as the most recent release each family offers [TODO: name the exact model versions and access dates].
Every configuration runs on both models, so architecture effects are compared within one model rather than across models (RQ1).
The open-weight model runs on the research group's GPU server and the hosted model on the group's API budget; the per-run cap on tool calls and tokens is set so that the full design fits that budget, and the failure set is subsampled per category if a pilot shows that it does not.
A repair counts as accepted when the build and the originally failing test pass in a fresh container.
[TODO: choose the log format each run records]
Failures published after a model's training cutoff are reported separately, because earlier failures may have been seen in training [@Novak26Leakage].

### Analysis

Repair rates are compared per model with a paired test over the same failures, because both architectures face identical inputs (RQ1).
The per-category difference between the two context conditions identifies where full logs help or hurt (RQ2).
Patch size is measured in changed lines, and maintainability is judged on a random sample of accepted patches against a published patch-quality rubric [@Chen26Repair] (RQ3).
[TODO: decide who rates maintainability — the student's own audit, or the industry partner's engineers, whose access is still open]
[TODO: fix the audit sample size after a pilot audit of twenty patches]
Each configuration runs three times per failure, and variance across runs is reported alongside the means, because agent runs are not deterministic.
The thesis expects a configuration effect smaller than the model effects that repair studies report [@Bauer25Agents]; a negligible effect would refute the premise that configuration is worth tuning.
Foreseeable limitations are the single benchmark and the two model families, which bound generalization and are stated as such.

## Timeline

[TODO: state start month and submission month]

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
