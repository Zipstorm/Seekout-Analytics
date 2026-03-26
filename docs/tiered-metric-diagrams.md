# Tiered Metric System Diagrams

**Product:** Helix (SeekOut.ai)
**Last Updated:** March 4, 2026

**Related:** [Viral Loop Metrics](./viral-loop-metrics.md) | [Network Quantification](./network-quantification.md)

---

## How to Read These Diagrams

Three-tier hierarchy flows from top-level outcomes down to trackable inputs:

1. **Tier 1 — Top-Level Metrics:** Helix Size, Liquidity, Activation, Bridging
2. **Tier 2 — Viral Loops:** Each loop's throughput = f × i × c (except Loop 3: bridge rate)
3. **Tier 3 — Base Input Metrics:** Raw event counts and entity counts from analytics

Loop 3 (Cross-Persona Bridge) has no i/c/f structure — it's measured as a conversion rate (D_new / U_single).

### Loop-to-Metric Impact Reference

| Loop | Helix Size | Liquidity (EOI/J) | Activation (CL/U_p) | Bridging (D/U) |
|------|-----------|-------------------|---------------------|----------------|
| L1: Job Sharing | UP | UP (+EOI) | DOWN (+U_p) | DOWN (+U) |
| L2: Team Invite | UP | — | — | DOWN (+U) |
| L3: Bridge | UP | mixed | mixed | UP (+D) |
| L4: Custom Link | UP | DOWN (+J) | — | DOWN (+U) |

---

## Idea 1: Per-Metric Decomposition

One diagram per top-level metric showing its full decomposition tree.

---

### Version 1B: Layered Bands

Same metric decomposition as 1A, but using subgraphs to create explicit tier boundaries. Visual emphasis on the three-tier structure.

#### 1B: Helix Size

```mermaid
graph TD
    subgraph tier1 ["Tier 1: Top Metric"]
        HS["Helix Size = (U_h × T) + (U_p × EOI)"]
    end

    subgraph tier2 ["Tier 2: Viral Loops"]
        L1["L1: Job Sharing"]
        L2["L2: Team Invite"]
        L3["L3: Bridge"]
        L4["L4: Custom Link"]
    end

    subgraph tier3 ["Tier 3: Loop Levers"]
        f1["f_share"]
        i1["i_share"]
        c1["c_share"]
        f2["f_invite"]
        c2["c_invite (i=1)"]
        BR["Bridge Rate"]
        f4["f_customlink"]
        i4["i_customlink"]
        c4["c_customlink"]
    end

    subgraph tier4 ["Tier 4: Base Input Metrics"]
        bf1a["Job Shared events"]
        bf1b["U_h"]
        bi1a["Unique link views"]
        bc1a["Signups from job links"]
        bc1c["EOIs from signups"]
        bf2a["Invite events"]
        bc2a["Invites opened"]
        bc2b["Invites sent"]
        bc2c["Invites accepted"]
        bBR1["Surface Activated events"]
        bBR2["Total users U"]
        bBR3["Dual-persona users D"]
        bf4a["CL Shared events"]
        bf4b["U_p"]
        bi4a["Profile Link Viewed"]
        bc4a["Signups from CL views"]
    end

    HS -->|"UP"| L1
    HS -->|"UP"| L2
    HS -->|"UP"| L3
    HS -->|"UP"| L4

    L1 --> f1
    L1 --> i1
    L1 --> c1
    L2 --> f2
    L2 --> c2
    L3 --> BR
    L4 --> f4
    L4 --> i4
    L4 --> c4

    f1 --> bf1a
    f1 --> bf1b
    i1 --> bi1a
    i1 --> bf1a
    c1 --> bc1a
    c1 --> bi1a
    c1 --> bc1c

    f2 --> bf2a
    f2 --> bf1b
    c2 --> bc2a
    c2 --> bc2b
    c2 --> bc2c

    BR --> bBR1
    BR --> bBR2
    BR --> bBR3

    f4 --> bf4a
    f4 --> bf4b
    i4 --> bi4a
    i4 --> bf4a
    c4 --> bc4a
    c4 --> bi4a
```

#### 1B: Liquidity

```mermaid
graph TD
    subgraph tier1 ["Tier 1: Top Metric"]
        LIQ["Liquidity = EOI / J"]
    end

    subgraph tier2 ["Tier 2: Viral Loops"]
        L1["L1: Job Sharing (UP)"]
        L3a["L3a: Bridge P-to-H (DOWN)"]
        L4["L4: Custom Link (DOWN)"]
    end

    subgraph tier3 ["Tier 3: Loop Levers"]
        f1["f_share"]
        i1["i_share"]
        c1["c_share"]
        BR["Bridge Rate"]
        f4["f_customlink"]
        i4["i_customlink"]
        c4["c_customlink"]
    end

    subgraph tier4 ["Tier 4: Base Input Metrics"]
        bf1a["Job Shared events"]
        bf1b["U_h"]
        bi1a["Unique link views"]
        bc1a["Signups from job links"]
        bc1c["EOIs from signups"]
        bBR1["Surface Activated events"]
        bBR2["Total users U"]
        bBR3["Dual-persona users D"]
        bf4a["CL Shared events"]
        bf4b["U_p"]
        bi4a["Profile Link Viewed"]
        bc4a["Signups from CL views"]
    end

    LIQ --> L1
    LIQ --> L3a
    LIQ --> L4

    L1 --> f1
    L1 --> i1
    L1 --> c1
    L3a --> BR
    L4 --> f4
    L4 --> i4
    L4 --> c4

    f1 --> bf1a
    f1 --> bf1b
    i1 --> bi1a
    i1 --> bf1a
    c1 --> bc1a
    c1 --> bi1a
    c1 --> bc1c

    BR --> bBR1
    BR --> bBR2
    BR --> bBR3

    f4 --> bf4a
    f4 --> bf4b
    i4 --> bi4a
    i4 --> bf4a
    c4 --> bc4a
    c4 --> bi4a
```

#### 1B: Activation

```mermaid
graph TD
    subgraph tier1 ["Tier 1: Top Metric"]
        ACT["Activation = CL / U_p"]
    end

    subgraph tier2 ["Tier 2: Viral Loops"]
        L1["L1: Job Sharing (DOWN)"]
        L3b["L3b: Bridge H-to-P (UP)"]
    end

    subgraph tier3 ["Tier 3: Loop Levers"]
        f1["f_share"]
        i1["i_share"]
        c1["c_share"]
        BR["Bridge Rate"]
    end

    subgraph tier4 ["Tier 4: Base Input Metrics"]
        bf1a["Job Shared events"]
        bf1b["U_h"]
        bi1a["Unique link views"]
        bc1a["Signups from job links"]
        bc1c["EOIs from signups"]
        bBR1["Surface Activated events"]
        bBR2["Total users U"]
        bBR3["Dual-persona users D"]
    end

    ACT --> L1
    ACT --> L3b

    L1 --> f1
    L1 --> i1
    L1 --> c1
    L3b --> BR

    f1 --> bf1a
    f1 --> bf1b
    i1 --> bi1a
    i1 --> bf1a
    c1 --> bc1a
    c1 --> bi1a
    c1 --> bc1c

    BR --> bBR1
    BR --> bBR2
    BR --> bBR3
```

#### 1B: Bridging

```mermaid
graph TD
    subgraph tier1 ["Tier 1: Top Metric"]
        BRG["Bridging = D / U"]
    end

    subgraph tier2 ["Tier 2: Viral Loops"]
        L3["L3: Bridge (UP)"]
        L1["L1: Job Sharing (DOWN)"]
        L2["L2: Team Invite (DOWN)"]
        L4["L4: Custom Link (DOWN)"]
    end

    subgraph tier3 ["Tier 3: Loop Levers"]
        BR["Bridge Rate"]
    end

    subgraph tier4 ["Tier 4: Base Input Metrics"]
        b1["Surface Activated events"]
        b2["Total users U"]
        b3["Dual-persona users D"]
    end

    BRG -->|"UP"| L3
    BRG -->|"DOWN"| L1
    BRG -->|"DOWN"| L2
    BRG -->|"DOWN"| L4

    L3 --> BR

    BR --> b1
    BR --> b2
    BR --> b3
```

---

## Idea 3: Loop-Centric View

Organized by loop rather than by metric. Answers: "What happens if we improve Loop X?"

---

### Version 3A: One Diagram Per Loop

Each loop gets its own diagram showing which top metrics it impacts, its throughput decomposition, and base input metrics.

#### 3A: Loop 1 — Job Sharing

```mermaid
graph TD
    subgraph impact ["Top Metric Impact"]
        SIZE["Helix Size: UP"]
        LIQ["Liquidity: UP"]
        ACT["Activation: DOWN"]
        BRG["Bridging: DOWN"]
    end

    L1["L1: Job Sharing<br/>Throughput = f_share × K_share"]

    SIZE --- L1
    LIQ --- L1
    ACT --- L1
    BRG --- L1

    L1 --> f1["f_share<br/>Trigger frequency"]
    L1 --> K1["K_share = i × c"]
    K1 --> i1["i_share<br/>Reach per share"]
    K1 --> c1["c_share<br/>Conversion"]

    f1 --> bf1a["Job Shared events"]
    f1 --> bf1b["U_h count"]

    i1 --> bi1a["Unique link views"]
    i1 --> bi1b["Job Shared events"]

    c1 --> bc1a["Signups from job links"]
    c1 --> bc1b["Link views"]
    c1 --> bc1c["EOIs from signups"]
```

#### 3A: Loop 2 — Team Invite

```mermaid
graph TD
    subgraph impact ["Top Metric Impact"]
        SIZE["Helix Size: UP"]
        LIQ["Liquidity: --"]
        ACT["Activation: --"]
        BRG["Bridging: DOWN"]
    end

    L2["L2: Team Invite<br/>Throughput = f_invite × c_invite (i=1)"]

    SIZE --- L2
    BRG --- L2

    L2 --> f2["f_invite<br/>Trigger frequency"]
    L2 --> c2["c_invite<br/>Conversion (i=1)"]

    f2 --> bf2a["Invite events"]
    f2 --> bf2b["U_h count"]

    c2 --> bc2a["Invites opened"]
    c2 --> bc2b["Invites sent"]
    c2 --> bc2c["Invites accepted"]
```

#### 3A: Loop 3 — Cross-Persona Bridge

```mermaid
graph TD
    subgraph impact ["Top Metric Impact"]
        SIZE["Helix Size: UP"]
        LIQ["Liquidity: mixed"]
        ACT["Activation: mixed"]
        BRG["Bridging: UP (only loop)"]
    end

    L3["L3: Cross-Persona Bridge<br/>No i/c/f — conversion rate only"]

    SIZE --- L3
    LIQ --- L3
    ACT --- L3
    BRG --- L3

    L3 --> BR["Bridge Rate = D_new / U_single"]
    L3 --> TtB["Time to Bridge"]

    BR --> b1["Surface Activated events"]
    BR --> b2["Total users U"]
    BR --> b3["Dual-persona users D"]

    TtB --> t1["Account creation timestamp"]
    TtB --> t2["Second surface activation timestamp"]

    L3 --> dir["Two directions"]
    dir --> PtoH["P-to-H: Prospect creates job"]
    dir --> HtoP["H-to-P: Hiring user creates CL or EOI"]
```

#### 3A: Loop 4 — Custom Link Virality

```mermaid
graph TD
    subgraph impact ["Top Metric Impact"]
        SIZE["Helix Size: UP"]
        LIQ["Liquidity: DOWN if +J"]
        ACT["Activation: --"]
        BRG["Bridging: DOWN"]
    end

    L4["L4: Custom Link Virality<br/>Throughput = f_CL × K_CL"]

    SIZE --- L4
    LIQ --- L4
    BRG --- L4

    L4 --> f4["f_customlink<br/>Trigger frequency"]
    L4 --> K4["K_CL = i × c"]
    K4 --> i4["i_customlink<br/>Views per share"]
    K4 --> c4["c_customlink<br/>Conversion"]

    f4 --> bf4a["CL Shared events"]
    f4 --> bf4b["U_p count"]

    i4 --> bi4a["Profile Link Viewed events"]
    i4 --> bi4b["CL Shared events"]

    c4 --> bc4a["Signups from CL views"]
    c4 --> bc4b["Profile Link Viewed events"]
```

