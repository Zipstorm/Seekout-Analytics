# Helix Viral Loop Metrics

**Product:** Helix (SeekOut.ai)
**Phase:** Phase 1
**Last Updated:** March 4, 2026

**Related:** [Network Model](../context/network-model.md) (loop definitions, graph paths) | [Network Quantification](./network-quantification.md) (Helix Size and health)

---

## Purpose

This document defines the metrics framework for each viral loop in Helix. The [Network Model](../context/network-model.md) defines the loops as graph paths — what they look like structurally. This doc defines how to measure whether they're working — the funnel stages, volume metrics, rate metrics, and K-factors for each loop.

### Per-Loop Framework

Each loop is characterized by a consistent set of dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Funnel** | Conversion stages from trigger to loop completion |
| **Volume metrics** | Counts at each funnel stage |
| **Rate metrics** | Conversion rates between stages |
| **K-factor (K)** | New users per trigger event: i × c |
| **Trigger frequency (f)** | Trigger events per eligible user per day |
| **Daily throughput** | New users per eligible user per day: **f × K** |
| **Cycle time** | Latency — time from trigger to loop completion |

**Daily throughput (f × K)** is the primary ranking metric. K alone cannot rank loops — a loop with K=0.5 and f=10/day produces 5 new users/user/day; a loop with K=1.0 and f=0.03/day produces 0.03. The high-frequency low-K loop wins 150:1.

Cycle time is secondary: it determines compounding speed (how quickly new users can trigger their own loops), not first-generation throughput. Trigger frequency is mostly determined by the underlying human behavior, not the product — the product can raise or lower it at the margin, but the ceiling is set by how often the real-world activity naturally happens.

---

## Loop 1: Job Sharing

HM or Recruiter shares a job externally, bringing new users into the network as prospects.

### Funnel

```
Job shared externally → Link viewed → Viewer signs up → New user expresses interest
```

### Variables

| Symbol | Definition | Source |
|--------|-----------|--------|
| i_share | Average people reached per job share event | Analytics |
| c_share | Overall conversion: view → signup → EOI | Analytics (view-to-signup × signup-to-EOI) |
| f_share | Share events per hiring-side user per day | Analytics: `Job Shared` count / U_h / days |

### Metrics

| Metric | Type | Definition |
|--------|------|-----------|
| Shares per job | Volume | Total share events / J |
| Reach per share (i_share) | Volume | Unique link views / share events |
| View-to-signup rate | Rate | Signups from job links / unique link views |
| Signup-to-EOI rate | Rate | EOIs created / signups from job links |
| c_share | Rate | View-to-signup × signup-to-EOI |
| **K_sharing** | **K-factor** | **i_share × c_share** |
| Trigger frequency (f_share) | Frequency | `Job Shared` events per hiring-side user per day |
| **Throughput_sharing** | **Throughput** | **f_share × K_sharing** |
| Cycle time | Time | Median time from share event to EOI creation |

**Health impact:** Increases Helix Size (U_p↑, EOI↑) and Liquidity (EOI↑). Dilutes Activation (U_p↑ without CL) and Bridging (U↑ without D). New prospects must create custom links to restore Activation and eventually bridge to restore Bridging.

---

## Loop 2: Team Invite

HM or Recruiter invites colleagues to collaborate on a job, expanding the hiring side.

### Funnel

```
Invite sent → Invite viewed → Invitee signs up → Invitee collaborates on job
```

**Variant B (Recruiter designates HM):**

```
Recruiter creates job → Designates external HM → HM signs up → HM collaborates on job
```

### Variables

| Symbol | Definition | Source |
|--------|-----------|--------|
| i_invite | People reached per invite event (always 1 — each invite targets one person) | Constant |
| c_invite | Overall conversion: invite sent → accepted | Analytics (open × accept) |
| f_invite | Invite events per hiring-side user per day | Analytics: `Team Member Invited` count / U_h / days |

### Metrics

| Metric | Type | Definition |
|--------|------|-----------|
| Invites per user per job | Volume | Invites sent / T |
| Invite open rate | Rate | Invites opened / invites sent |
| Open-to-accept rate | Rate | Invites accepted / invites opened |
| c_invite | Rate | Open rate × accept rate |
| **K_team_invite** | **K-factor** | **i_invite × c_invite = c_invite** (since i=1) |
| Trigger frequency (f_invite) | Frequency | `Team Member Invited` events per hiring-side user per day |
| **Throughput_invite** | **Throughput** | **f_invite × K_team_invite** |
| Cycle time | Time | Median time from invite sent to collaborates_on edge created |

**Variant B sub-funnel:** Track recruiter-created jobs where the designated HM is new to Helix. Measure designation-to-signup rate and time-to-first-review separately — this variant pulls in HMs who wouldn't self-serve.

**Health impact:** Increases Helix Size (U_h↑, T↑). Neutral on Liquidity and Activation. Dilutes Bridging (U↑ without D). A size-only loop — the new hiring-side user must eventually bridge to contribute to health metrics.

---

## Loop 3: Cross-Persona Bridge

A single-surface user activates their second surface, crossing from one side of the network to the other. Not an i × c loop — measured directly as a conversion rate.

### Funnel

```
Single-surface user exists → Activates second surface → Becomes dual-persona user
```

Two directions:
- **Prospect → Hiring** (primary): Prospect creates or joins their first job. Creates a new Job that feeds Loops 1 and 2.
- **Hiring → Prospect**: Hiring-side user expresses interest in a job or creates a custom link. Adds prospect-side edges.

### Variables

| Symbol | Definition | Source |
|--------|-----------|--------|
| D_new | New dual-persona users in the period | `Surface Activated` events (users who activated their second surface) |
| U_single | Single-surface users | U - D (total users minus existing dual-persona users) |

### Metrics

| Metric | Type | Definition |
|--------|------|-----------|
| Bridge rate (D_new / U_single) | Rate | New dual-persona users / single-surface users in the period |
| Time to bridge | Time | Median time from account creation to second surface activation |
| Trigger | -- | Implicit (product prompts, organic discovery, life circumstance) |

This loop has no trigger frequency lever — it depends on life circumstances and product nudges. Not an f × K loop; measured as a period conversion rate. The product lever is reducing friction, not increasing distribution.

**Health impact:** The only loop that improves Bridging (D↑). Direction matters: P→H increases Helix Size and Bridging but dilutes Liquidity (new job has no EOIs yet — needs Loop 1 to fill it). H→P increases Bridging and can improve Liquidity (+EOI) and Activation (+CL) depending on what the new prospect-side user does.

---

## Loop 4: Link Virality (Custom Link)

A prospect has portfolios (P) and adds links (C) to them; they use a link when applying to external jobs. The hiring contact at the external company clicks the link, views the prospect's profile, discovers the platform, and signs up. See [Prospect structure](../context/prospect-structure.md).

### Funnel

```
Prospect creates custom link → Uses in external application → External HM/recruiter views profile → Viewer signs up → Viewer creates job (optional deeper funnel)
```

### Variables

| Symbol | Definition | Source |
|--------|-----------|--------|
| i_customlink | Average views per custom link share event | Analytics: `Profile Link Viewed` count / `Custom Link Shared` count |
| c_customlink | Overall conversion: view → signup | Analytics: signups attributed to custom link views / total views |
| f_customlink | Custom link share events per prospect per day | Analytics: `Custom Link Shared` count / U_p / days |

### Metrics

| Metric | Type | Definition |
|--------|------|-----------|
| Custom links per prospect | Volume | CL / U_p |
| Applications per custom link | Volume | Assumed ~1; external applications are not observable from within Helix |
| Views per share event (i_customlink) | Volume | `Profile Link Viewed` count / `Custom Link Shared` count |
| View-to-signup rate (c_customlink) | Rate | Signups from custom link views / total views |
| Signup-to-job-creation rate | Rate | New users from custom links who create a job / signups (deeper funnel) |
| **K_custom_link** | **K-factor** | **i_customlink × c_customlink** |
| Trigger frequency (f_customlink) | Frequency | `Custom Link Shared` events per prospect per day |
| **Throughput_custom_link** | **Throughput** | **f_customlink × K_custom_link** |
| Cycle time | Time | Median time from custom link view to viewer signup |

Directly fed by Prospect Activation (CLs per Prospect) from the [health metrics](./network-quantification.md#prospect-activation).

**Health impact:** Increases Helix Size (U_h↑). Dilutes Liquidity if the new hiring user creates a job (J↑ without EOIs) and Bridging (U↑ without D). Neutral on Activation. The new hiring-side user must attract EOIs to their job (via Loop 1) and eventually bridge to restore health ratios.

---

## Ranking Loops

### Why throughput, not K

K-factor cannot rank loops. Consider: Loop A has K=0.5 but triggers 10 times/user/day (throughput=5.0). Loop B has K=1.0 but triggers 0.03 times/user/day (throughput=0.03). Loop A produces 150x more growth despite half the K. The dominant variable is **trigger frequency** — how often the underlying human behavior naturally occurs.

Each loop operates independently — Job Sharing does not require Team Invite or Cross-Persona Bridge to function (any hiring-side user can create and share a job), and Cross-Persona Bridge can be triggered by any single-surface user regardless of how they entered the network. Loops can amplify each other: Custom Link Virality brings in hiring-side users who may later trigger Job Sharing or Team Invite, and Cross-Persona Bridge creates new Jobs that feed Loops 1 and 2.

### What to instrument first

1. **Job Sharing** — f_share and c_share: measure reach per share (i_share) and the job link landing experience conversion (c_share). This loop has the broadest distribution surface.
2. **Custom Link** — f_customlink and c_customlink: measure how often prospects use custom links in external applications and the profile landing page conversion for external hiring contacts.
3. **Team Invite** — c_invite: trigger frequency is naturally bounded by team size, so conversion rate is the primary lever.
4. **Cross-Persona Bridge** — bridge rate and time-to-bridge: each bridge creates a new Job that feeds Loops 1 and 2. The product lever is reducing friction, not increasing distribution.

---

**Not yet included — retention and churn:** This framework measures user acquisition per loop but does not yet account for retention. A loop that generates users who churn immediately doesn't grow the network. Effective throughput is `f × K × retention_rate`, and the eligible user base for each loop decays as users' triggering context ends (e.g., a filled job stops generating shares, a placed prospect stops applying externally). Retention modeling needs to be added once we have real usage data.

**Cross-doc alignment needed:** The [dashboards doc](./analytics-dashboards.md) decomposes c into 5 sub-stages (`c_view × c_click × c_form × c_complete × c_activate`). This doc uses a simpler 2-stage model (view-to-signup × signup-to-EOI). These should be reconciled when instrumenting the funnels.

**Assumption: f and c are treated as independent.** In practice, as trigger frequency increases (more shares, more custom links), per-impression conversion may decrease due to recipient fatigue. The framework does not model this interaction. If observed in data, throughput ceilings will need to account for the f-c relationship.

*This document defines per-loop growth metrics for the viral loops defined in the [Network Model](../context/network-model.md). Helix Size and health metrics are in [Network Quantification](./network-quantification.md).*
