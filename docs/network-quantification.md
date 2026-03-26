# Helix Network Quantification

**Product:** Helix (SeekOut.ai)
**Phase:** Phase 1
**Last Updated:** March 4, 2026

**Related:** [Network Model](../context/network-model.md) (graph structure) | [Entity-Relationship Model](../context/entity-relationship-model.md) (database schema) | [Viral Loop Metrics](./viral-loop-metrics.md) (per-loop funnels and growth tracking)

---

## Purpose

This document defines how to quantify the Helix network. It answers: given the graph defined in the [network model](../context/network-model.md), how do we measure whether it's big enough and healthy enough?

Two dimensions, each with its own formula:

1. **Helix Size** — how big is the graph?
2. **Network Health** — is it structurally sound? (three independent structural metrics, no composite)

Network growth is driven by viral loops. Per-loop funnels, metrics, and K-factors are defined in [Viral Loop Metrics](./viral-loop-metrics.md).

---

## Variables

| Symbol | Definition | Source |
|--------|-----------|--------|
| U | Total users | User table count |
| J | Total jobs | Job table count |
| EOI | Total expressions of interest | EOI table count |
| CL | Total custom links | CustomLink table count |
| T | Total team edges (collaborates_on) | JobTeamMember table count |
| U_h | Hiring-side users (at least one `collaborates_on` edge) | Distinct user_id from JobTeamMember |
| U_p | Prospect-side users (prospect surface enabled) | Users where `activated_surfaces` includes `prospect` |
| D | Dual-persona users (edges on BOTH sides) | U_h ∩ U_p |

---

## 1. Helix Size

**Formula:**

```
Helix Size = (U_h × T) + (U_p × EOI)
```

Hiring-side size plus prospect-side size. Each side's user count times its respective edges to Jobs.

**What's excluded?** Review edges are activity on top of structure, not structure itself. CustomLinks reach outside the network boundary and are captured in [Viral Loop Metrics](./viral-loop-metrics.md) (Loop 4: Custom Link Virality).

---

## 2. Network Health

Three independent structural metrics. Each measures a different property of the graph. No composite score — monitor and act on each independently.

### Hiring-Side Liquidity

```
EOIs per Job = EOI / J
```

Are jobs getting enough prospect interest? Below some threshold, HMs churn because the platform doesn't deliver candidates. Above it, each job attracts enough prospect interest to justify the hiring team's time. This is a true liquidity metric — the hiring side depends on prospect engagement to get value.

### Prospect Activation

```
CLs per Prospect = CL / U_p
```

Are prospects using the tools that make Helix valuable to them? Prospects don't need hiring-side liquidity — they get value independently by creating custom links and using them in external job applications. A prospect who creates custom links is investing in the platform as part of their job search workflow. This is an activation metric, not a liquidity metric — it measures self-serve tool adoption, and each custom link also seeds Loop 4 (Custom Link Virality).

### Bridging

```
Bridging = D / U
```

Fraction of users participating on BOTH the hiring side and the prospect side. This measures cross-persona conversion — the most valuable long-term loop. Crossing from prospect to HM requires having an open role, which is circumstantial, not a product-design lever.

---

## 3. Network Growth

Network growth is driven by completing viral loops — closed paths through the graph that add new nodes and edges on each completion. The [Network Model](../context/network-model.md) defines these loops as graph paths; the [Viral Loop Metrics](./viral-loop-metrics.md) doc defines the per-loop funnels, metrics, and K-factors.

### Loop Impact on Top-Level Metrics

Each loop completion adds specific nodes and edges to the graph. Because the three health metrics are ratios, adding nodes can **dilute** a metric even as the network grows. The matrix below traces the variable-level changes through to each metric's formula.

| Loop | Graph adds | Helix Size | Liquidity (EOI/J) | Activation (CL/U_p) | Bridging (D/U) |
|------|-----------|------------|-------------------|---------------------|----------------|
| 1. Job Sharing | +U_p, +EOI | UP — U_p↑ and EOI↑ both grow prospect-side term | UP — EOI↑, J unchanged | DOWN — U_p↑ dilutes (new prospect has no CLs yet) | DOWN — U↑, D unchanged |
| 2. Team Invite | +U_h, +T | UP — U_h↑ and T↑ both grow hiring-side term | Neutral — EOI and J unchanged | Neutral | DOWN — U↑, D unchanged |
| 3a. Bridge (P→H) | +U_h, +J, +T, +D | UP — U_h↑ and T↑ grow hiring-side term | DOWN — J↑ dilutes (new job has no EOIs yet) | Neutral | UP — D↑ grows faster than U (U unchanged, D↑) |
| 3b. Bridge (H→P) | +U_p, +EOI/CL, +D | UP — U_p↑ grows prospect-side term | UP if +EOI | UP if +CL | UP — D↑, U unchanged |
| 4. Custom Link | +U_h, (+J, +T) | UP — U_h↑ grows hiring-side term | DOWN if new user creates job (J↑) | Neutral | DOWN — U↑, D unchanged |

### Growth-Health Tension

Every acquisition loop (1, 2, 4) increases Helix Size but dilutes at least one health ratio. This is inherent to ratio metrics: the new user appears in the denominator immediately but hasn't yet performed the numerator action (creating a CL, submitting an EOI, or bridging). Only the Cross-Persona Bridge (Loop 3) can improve Bridging — no acquisition loop can.

This dilution is temporary if new users activate. The question is whether activation happens fast enough to offset acquisition volume. If a loop brings in users who never activate, it grows Size while permanently degrading Health.

### Complementary Activation

Healthy growth requires each loop's output users to perform specific follow-on actions that restore the health ratios they diluted:

- **Loop 1** (brings in prospects): new prospects must create custom links to restore Activation (CL/U_p) and eventually bridge to restore Bridging (D/U)
- **Loop 2** (brings in hiring users): new hiring users must eventually bridge to restore Bridging (D/U)
- **Loop 3a** (P→H bridge): the new job must attract EOIs to restore Liquidity (EOI/J) — this is where Loop 1 feeds back
- **Loop 4** (brings in hiring users): same as Loop 2, plus if the new user creates a job, that job needs EOIs

The [Viral Loop Metrics](./viral-loop-metrics.md) doc tracks per-loop throughput; the activation actions above are the bridge between throughput and sustained health improvement.

---

*This document provides the quantification framework for the network defined in the [Network Model](../context/network-model.md). The formulas use data from the [Entity-Relationship Model](../context/entity-relationship-model.md). Per-loop growth metrics and funnels are defined in [Viral Loop Metrics](./viral-loop-metrics.md).*
