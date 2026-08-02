# Scope

Vehicle-to-everything networks let vehicles share perceived objects without central infrastructure, and message-rate decisions determine whether the channel stays usable under load [@Rossi23Adaptive].
Fixed-rate collective perception ignores fluctuating channel quality, which leads to congested channels and dropped object updates in dense traffic [@Klein24Density].
This Bachelor's thesis develops an adaptive message-rate layer that reacts to observed channel load and compares it against a fixed-rate baseline.
The scope covers simulated traffic of up to 500 vehicles; physical vehicle testbeds are out of scope.

# Requirements

The rate-control layer must recieve channel-load updates from neighbouring vehicles and adjust its rate without global knowledge.
Rate adjustment should complete within one message interval.
Memory usage per on-board unit must stay below the limits of common automotive platforms.
Energy consumption is treated as neglectable for this thesis.

# Research Questions

1. How can a rate-control layer be implemented that reacts to sudden channel-load spikes?
2. How can the neighbour awareness protocol be built so that it scales to 500 vehicles?
3. How can fallback rate selection be designed so that object-update loss stays low during platoon formation?
4. Why does adaptive rate control outperform fixed-rate collective perception in dense traffic?

# Approach

We first implement the adaptive layer inside an open-source vehicular network simulator.
After that, we generate traffic scenarios of increasing density and replay recorded interference traces.
Our evaluation compares object-update delivery ratio, end-to-end latency, and control-message overhead between the adaptive layer and the fixed-rate baseline.
Finally, a seperate stress test examines the behaviour when half of the participating vehicles enter the intersection simultaneously.

# Schedule

- Weeks 1–4: simulator setup and baseline implementation.
- Weeks 5–8: adaptive layer and neighbour awareness.
- Weeks 9–12: experiments and stress test.
- Weeks 13–16: writing and submission.

# Supervisor

The thesis is supervised by Prof. Dr. Max Mustermann (max.mustermann@example.org), Chair of Connected Mobility.

---
title: Adaptive Message Rate Control for V2X Collective Perception
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
  title: Adaptive Rate Control under Channel-Load Fluctuations in Vehicular Networks
  container-title: Proceedings of the Example Conference on Connected Vehicles
  DOI: 10.xxxx/xxxx6
- id: Klein24Density
  type: article-journal
  author:
  - family: Klein
    given: A.
  issued:
    year: 2024
  title: Density Effects on Collective Perception Message Delivery
  container-title: Journal of Example Vehicular Communication
  DOI: 10.xxxx/xxxx7
---
