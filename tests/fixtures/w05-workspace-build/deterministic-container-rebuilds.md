# Introduction to the Topic

Container images are rebuilt continuously in modern delivery pipelines, yet two builds of the same source rarely produce the same bytes [@Navarro24Reproduc].
Timestamps, package-mirror state and build-tool nondeterminism all leak into the resulting layers.
Consumers of an image therefore cannot tell an intended change from an incidental one, which weakens the supply-chain guarantees that image signing is meant to provide [@Ibarra25Supply].
This thesis investigates which sources of nondeterminism dominate in practice and how far they can be removed without changing the build inputs.

# Contribution to the State-of-the-Art

Reproducible-build research has concentrated on distribution packages, where the toolchain is under one project's control [@Navarro24Reproduc].
Container images differ: they layer third-party base images, package managers and application builds whose determinism nobody owns end to end.
@Ibarra25Supply argue that signing without reproducibility only proves who built an artifact, never that the artifact follows from its source.
Existing tooling reports whether two images differ, but not which stage introduced the difference [@Tessaro25Layer].
This work contributes a layer-attributed diagnosis of image nondeterminism and measures how much of it a small set of normalizations removes.

# Research Focus and Research Questions

The research focus lies on identifying and attributing the sources of byte-level nondeterminism in repeated container image builds.

1. Which build stages account for the byte-level differences between repeated builds of an unchanged image definition?
2. To what extent do timestamp and file-ordering normalizations reduce those differences across the observed stages?
3. Which forms of nondeterminism persist after normalization, and what causes them to persist?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an existing container build tool and its exposed layer metadata.
Layer comparison follows the differencing approach of @Tessaro25Layer, extended to attribute a difference to the stage that produced it.
A corpus of publicly available image definitions supplies the build inputs.

## Requirements

The tool must attribute every observed byte difference to exactly one build stage, or report it as unattributable rather than guessing.
Normalizations must be individually switchable so their effect can be measured separately.
Rewriting the images' own build definitions is out of scope: the inputs stay as their authors wrote them.

## Evaluation

Repeated builds of each corpus image under a fixed environment establish which stages differ and how often (RQ1).
Enabling each normalization in turn measures the reduction in differing bytes per stage (RQ2).
The residual differences are inspected and classified by cause, with the classification reported per image (RQ3).

# Timeline

The thesis starts in April 2028 and is submitted in September 2028.

---
title: Attributing Byte-Level Nondeterminism in Container Image Builds
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Navarro24Reproduc
  type: article-journal
  author:
  - family: Navarro
    given: L.
  - family: Hendriks
    given: J.
  issued:
    year: 2024
  title: "Reproducible Builds in Practice: A Study of Distribution Packages"
  container-title: Empirical Software Engineering
  DOI: 10.1007/s10664-024-10521-8
- id: Ibarra25Supply
  type: paper-conference
  author:
  - family: Ibarra
    given: R.
  - family: Sundqvist
    given: E.
  issued:
    year: 2025
  title: "What Signing Does Not Prove: Provenance Without Reproducibility"
  container-title: Proceedings of the ACM Conference on Computer and Communications Security
  DOI: 10.1145/3719284.3721103
- id: Tessaro25Layer
  type: article-journal
  author:
  - family: Tessaro
    given: M.
  - family: Ohlsson
    given: K.
  issued:
    year: 2025
  title: Layer-Level Differencing for Container Image Artifacts
  container-title: Journal of Systems and Software
  DOI: 10.1016/j.jss.2025.112287
---
