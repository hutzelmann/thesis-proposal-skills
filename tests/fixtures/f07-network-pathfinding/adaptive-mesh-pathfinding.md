# Scope

Wireless mesh networks connect embedded nodes without central infrastructure, and routing decisions determine whether the network stays usable under load [@Rossi23Adaptive].
Static shortest-path routing ignores fluctuating link quality, which leads to congested relays and packet loss in dense deployments [@Klein24Mesh].
This Bachelor's thesis develops an adaptive pathfinding layer that reacts to observed link quality and compares it against a static baseline.
The scope covers simulated networks of up to 500 nodes; physical hardware testbeds are out of scope.

# Requirements

The routing layer must recieve link-quality updates from neighbouring nodes and recompute paths without global knowledge.
Path recomputation should complete within one beacon interval.
Memory usage per node must stay below the limits of common embedded platforms.
Energy consumption is treated as neglectable for this thesis.

# Research Questions

1. How can a routing layer be implemented that reacts to sudden link-quality drops?
2. How can the neighbour discovery protocol be built so that it scales to 500 nodes?
3. How can fallback path selection be designed so that packet loss stays low during topology changes?
4. Why does adaptive routing outperform static shortest-path routing in dense deployments?

# Approach

We first implement the adaptive layer inside an open-source network simulator.
After that, we generate topologies of increasing density and replay recorded interference traces.
Our evaluation compares delivery ratio, latency, and control-message overhead between the adaptive layer and the static baseline.
Finally, a seperate stress test examines the behaviour when half of the relay nodes fail simultaneously.

# Schedule

- Weeks 1–4: simulator setup and baseline implementation.
- Weeks 5–8: adaptive layer and neighbour discovery.
- Weeks 9–12: experiments and stress test.
- Weeks 13–16: writing and submission.

# Supervisor

The thesis is supervised by Prof. Dr. Max Mustermann (max.mustermann@example.org), Chair of Distributed Systems.

---
title: Adaptive Pathfinding in Wireless Mesh Networks
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Rossi23Adaptive
  type: paper-conference
  author:
  - family: Rossi
    given: M.
  issued:
    year: 2023
  title: Adaptive Routing under Link-Quality Fluctuations in Mesh Networks
  container-title: Proceedings of the Example Conference on Networked Systems
  DOI: 10.xxxx/xxxx6
- id: Klein24Mesh
  type: article-journal
  author:
  - family: Klein
    given: A.
  issued:
    year: 2024
  title: Mesh Network Performance in Dense Deployments
  container-title: Journal of Example Communication Networks
  DOI: 10.xxxx/xxxx7
---
