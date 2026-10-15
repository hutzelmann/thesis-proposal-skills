# Predicting Build Breakage from Automated Dependency Updates

*Master's Thesis Proposal*

## Introduction to the Topic

Dependency-update bots open a pull request whenever a library a project depends on publishes a new version [@Halloran24Update].
Most projects merge these pull requests without review once the build passes [@Halloran24Update].
The bots reduced the median age of outdated dependencies by 40 % in the projects that adopted them [@Halloran24Update].
At the same time, one update in eight broke the build or the tests of the receiving project [@Halloran24Update].
Semantic versioning is meant to announce such breaking changes, but library maintainers apply it inconsistently [@Vasquez23Semver; @Ito24Breaking].
A minor or patch release regularly removes or changes public interfaces [@Vasquez23Semver; @Ito24Breaking].
Projects therefore cannot rely on the version number to decide which updates are safe to merge [@Vasquez23Semver; @Ito24Breaking].
This thesis evaluates whether the history of a project's past updates predicts which update will break its build before the update is merged.

## Contribution to the State-of-the-Art

A classifier trained on 30,000 dependency updates from the npm ecosystem predicts build breakage from the diff of the updated library [@Morandi25Breakage].
The classifier uses removed exports, changed function signatures, and changed default values as features [@Morandi25Breakage].
It achieved an F1 score of 0.71 on held-out updates from the projects it was trained on [@Morandi25Breakage].
Its F1 score dropped to 0.52 on projects outside the training set [@Morandi25Breakage].
The evaluation did not use the receiving project's own build history [@Morandi25Breakage].

Static compatibility checkers compare two library versions and report breaking interface changes without executing any code [@Ito24Breaking; @Okonjo23Compat].
Most of their warnings concern interfaces the receiving project never calls [@Okonjo23Compat].
Client-side analyses restrict the comparison to the interfaces a project actually calls and cut false warnings by half [@Lambert24Client].

Both lines of work inspect the updated library and ignore how the receiving project reacted to earlier updates.
That record already sits in every project's CI logs, and no approach uses it as a predictor.
The thesis adds that signal: it evaluates a breakage predictor trained on per-project update histories against the diff-based classifier and a client-side static check.
Answering the research questions matters because maintainers decide on every bot pull request whether a green build is enough, and a predictor that ranks risky updates first directs review effort to where breakage is likely.
The deliverable is an evaluation of a history-based predictor against two established baselines, together with the dataset needed to repeat it.

## Research Focus and Research Questions

The focus is build breakage caused by bot-generated dependency updates in open-source projects with public CI logs.

1. To what degree does a predictor trained on a project's own update history detect breaking updates more accurately than a diff-based classifier?
2. How does the prediction quality of the history-based predictor change on projects outside its training set?
3. Under which update types — major, minor, or patch — does a client-side static check detect as many breaking updates as the history-based predictor?

## Methodology for Research: Empirical Model Evaluation

An empirical model evaluation fits because all three questions compare the accuracy of predictors on recorded data, which a controlled measurement on held-out updates answers directly.

### Data and Baselines

The data are bot-generated update pull requests from 200 open-source Java and JavaScript projects, with the CI outcome of each, taken from a published dataset [@Ruiz25Dataset].
Its licence permits research use and redistribution of derived data, and commit author names are removed before analysis because they are personal data.
The baselines are the diff-based classifier [@Morandi25Breakage] and a client-side static check [@Lambert24Client], both re-run on the same updates.

### Experimental Setup

Each project's updates are split by time, so the predictor is always trained on updates older than the ones it is tested on (RQ1).
A second split holds out whole projects to measure transfer to unseen projects (RQ2).
Updates are labelled by semantic-version type before evaluation, so every comparison can be repeated per type (RQ3).

### Analysis

Precision, recall, and F1 are compared between the history-based predictor and the diff-based classifier on the temporal split (RQ1).
The drop in F1 between the temporal and the cross-project split quantifies transfer (RQ2).
Detection rates of the static check and the history-based predictor are compared per update type with McNemar's test (RQ3).
One ecosystem pair and one dataset bound the findings: they describe bot updates in open-source Java and JavaScript projects, not dependency management in general.

## Timeline

The thesis starts in April 2027 and is submitted in September 2027.

## References

---
references:
- id: Halloran24Update
  type: article-journal
  author:
  - family: Halloran
    given: B.
  - family: Mensah
    given: K.
  issued:
    year: 2024
  title: "Update Bots in Open Source: Adoption, Merge Behaviour, and Breakage"
  container-title: Journal of Example Software Engineering Studies
  DOI: 10.xxxx/f27-01
- id: Vasquez23Semver
  type: paper-conference
  author:
  - family: Vasquez
    given: L.
  issued:
    year: 2023
  title: "Semver in Practice: How Library Maintainers Version Breaking Changes"
  container-title: Proceedings of the Example Conference on Software Maintenance
  DOI: 10.xxxx/f27-02
- id: Ito24Breaking
  type: paper-conference
  author:
  - family: Ito
    given: R.
  - family: Schulz
    given: A.
  issued:
    year: 2024
  title: "Breaking Changes in Minor and Patch Releases"
  container-title: Proceedings of the Example Conference on Software Ecosystems
  DOI: 10.xxxx/f27-03
- id: Morandi25Breakage
  type: paper-conference
  author:
  - family: Morandi
    given: G.
  - family: Chen
    given: W.
  issued:
    year: 2025
  title: "Breakage Prediction for Dependency Updates from Library Diffs"
  container-title: Proceedings of the Example Conference on Software Analytics
  DOI: 10.xxxx/f27-04
- id: Okonjo23Compat
  type: article-journal
  author:
  - family: Okonjo
    given: E.
  issued:
    year: 2023
  title: "Compatibility Checkers for Library Upgrades: An Evaluation"
  container-title: Journal of Example Software Practice
  DOI: 10.xxxx/f27-05
- id: Lambert24Client
  type: paper-conference
  author:
  - family: Lambert
    given: F.
  issued:
    year: 2024
  title: "Client-Side Analysis of Breaking Library Changes"
  container-title: Proceedings of the Example Conference on Program Analysis
  DOI: 10.xxxx/f27-06
- id: Ruiz25Dataset
  type: dataset
  author:
  - family: Ruiz
    given: M.
  issued:
    year: 2025
  title: "Dataset of Bot-Generated Dependency Updates with CI Outcomes"
  publisher: Example Research Data Repository
  DOI: 10.xxxx/f27-07
---
