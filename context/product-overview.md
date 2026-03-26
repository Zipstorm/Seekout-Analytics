---
confluence:
  page_id: "1809645592"
  space_id: "1644691474"
  parent_id: "1644691909"
---

# Helix - Product Overview

**Product Name**: Helix (internal name) | SeekOut.ai (user-facing)  
**Status**: Pre-Development / Vision Phase  
**Product Type**: Viral, sharing-driven hiring platform  
**Vision Author**: Aravind Bala (Cofounder & CTO)  
**Date**: January 2026 (updated February 2026)

---

## What is Helix?

Helix (internal name, user-facing as SeekOut.ai) is a recruiting flywheel platform that reimagines hiring as a sharing-driven activity. Instead of fragmented workflows across tools, inboxes, and systems, Helix creates viral loops where hiring managers, recruiters, and prospects naturally share opportunities, talent, signal, and feedback.

**Core Insight**: *"Hiring is inherently sharing-driven."* At its core, hiring is about connections and collaboration, yet today's tools create friction and limit the quality and quantity of those connections.

**Strategic Objective**: Build interconnected viral loops across three personas that naturally grow the platform as users accomplish their goals.

---

## Core Value Proposition

### For Hiring Managers
**Problem**: Scaling prospect reach degrades conversation quality; maintaining quality requires significant manual effort

**Solution**: Share jobs broadly within right networks, conduct high-signal conversations at scale with AI assistance

**Value**: Reach qualified prospects without quality tradeoff

---

### For Recruiters
**Problem**: Initial screens take 30-45 minutes each; manual prospect sharing and HM feedback loops are slow and fragmented. Hiring manager intake is time-consuming and often inaccurate.

**Solution**: 
- AI-assisted screening at scale + efficient prospect packet sharing with structured feedback collection
- **AI-Powered Recruiter Intake**: Interactive voice + dynamic UI interface for hiring manager conversations with real-time constraint identification, trade-off analysis, and synthetic prospect profiles to illustrate bottlenecks (salary/location/skill)
- Four-step intake process: basic questions → difficulty analysis → calibration samples → summary
- **Automated recruitment pipeline**: AI agent autonomously builds queries, sources prospects, and presents shortlists — from intake to prospect presentation

**Value**: Look like a hero to both hiring managers and prospects; scale quality screening. Superior speed and global knowledge application vs. manual intake processes.

---

### For Prospects
**Problem**: Applications disappear into void; no visibility into status, reviews, or next steps. Prospects also lack guidance on how to present themselves effectively and have no way to build a compelling "AI Forward" professional story.

**Solution**:
- **AI Career Coach agent** — available post-onboarding for ongoing profile improvement through agentic conversation (voice + text + A2UI)
- **One mutable portfolio** per prospect — resume converted to Typst (editable intermediate format) during onboarding, then improved over time via natural language editing. See [Prospect structure](./prospect-structure.md).
- **Applications** — immutable snapshots created each time the prospect shares their portfolio. Can be auto-tailored for specific jobs (JD → rubric scorecard → tailored content) or shared as-is. Each application has a unique tracking link with viewer engagement analytics.
- Two tracking models: Expression of Interest (auto-tracked for Helix-posted jobs) and Applications (per share, for external applications — tracks views, clicks, time spent)
- No-login expression of interest and interview flow → account creation after completion for profile and analytics access

**Value**: Transparency and guidance instead of silence; a living portfolio that the system tailors for every opportunity

---

## How Helix Fits Within SeekOut

### Relationship to Existing Products

**SeekOut Recruit** (Enterprise Sales-Led):
- License-based pricing
- Sales-driven GTM
- Feature-rich for enterprise TA teams

**Helix** (Consumer Viral):
- Free-to-paid model
- Viral growth loops
- Individual adoption, optional enterprise integration

**Integration Points**:
- ATS connectivity (shared infrastructure)
- Enterprise SSO and admin
- Spot upsell path (passive sourcing)

### Strategic Positioning

Helix is SeekOut's **first consumer-oriented viral product**:
- Different growth model than traditional enterprise software
- Bottom-up adoption with top-down monetization
- Viral loops create network effects
- Consumer product mechanics in B2B context

---

## Product Architecture

### Three Persona Teams

**1. Hiring Manager & Recruiter Team**
- **AI Recruiter agent** — dedicated agent persona (distinct from career coach) for recruiter and hiring manager workflows
- AI-powered recruiter intake: voice + dynamic UI interface for HM conversations
- Real-time constraint identification and trade-off analysis with synthetic prospect profiles
- Automated pipeline: AI agent builds SeekOut queries autonomously, sources and presents prospects
- Digital twin hiring manager agent for higher-accuracy calibration than human baseline
- Job posting and distribution workflows
- AI-assisted prospect screening
- Prospect packet creation and sharing
- Hiring manager collaboration and feedback

**2. Prospect Team**
- **AI Career Coach agent** — available post-onboarding for ongoing profile improvement through agentic conversation (voice + text + A2UI)
- **Resume conversion pipeline**: PDF upload → vision-based parsing → AI diagnosis → template selection → Typst conversion → mandatory first edit
- **One mutable portfolio** per prospect: resume content (Typst source), extras (photo, video, GitHub, links), template. Edited via natural language (agentic LLM pattern). See [Prospect structure](./prospect-structure.md).
- **Applications** (immutable snapshots): created each time the prospect shares their portfolio. Can be auto-tailored for specific jobs (JD → rubric scorecard → tailored Typst) or shared as-is. Each has a unique tracking link with viewer engagement analytics (views, clicks, time spent).
- Two tracking models:
  - **Expression of Interest**: For jobs posted on Helix — auto-tracked when prospect engages with a shared job link
  - **Applications**: For external job applications — prospect shares portfolio (tailored or as-is); each share creates a tracked application with unique link
- Career development recommendations: new projects, skills, and ways to strengthen profile
- No-login expression of interest and interview flow → account creation after completion for profile and analytics access
- Prospect can switch from portfolio improvement to job application flow at any time
- Traction insights and follow-up guidance

**3. Platform & Analytics Team**
- Shared infrastructure (identity, invites, credits, analytics)
- ATS integration foundation
- Trust, safety, and compliance
- Design system and instrumentation

---

## Agent Strategy

Helix uses **distinct, specialized AI agents** rather than a single generalist — people trust specialized experts more than generalists.

### Agent Personas

| Agent | Audience | Role |
|-------|----------|------|
| **AI Career Coach** | Prospects | Primary prospect interface: profile building, career development, AI-forward project coaching |
| **AI Recruiter** | Recruiters & Hiring Managers | Intake, sourcing, screening, prospect presentation |

Each agent has its own name, personality, and persona. The career coach is introduced after prospect signup; the recruiter agent drives the intake-to-presentation pipeline.

### Prospect Flow

1. **Onboarding**: Resume upload → PDF parsing → AI diagnosis → template selection → Typst conversion → mandatory "try an edit" → portfolio created
2. **Portfolio view**: The prospect's home — edit portfolio via NL, share for jobs, access AI Career Coach
3. **Sharing**: [Share] button → "for a specific job?" → Yes: JD input → auto-tailor → preview → tailored application / No: name → as-is application
4. **Applications**: Every share creates an immutable application with a unique tracking link and activity feed
5. **Returning**: Prospect edits portfolio via NL, creates new applications for new opportunities
6. Prospect can switch to job application flow at any time:
   - Express interest in Helix-posted jobs (auto-tracked)
   - Share portfolio as applications for external jobs (per-application tracking)
7. No-login expression of interest and interview → account creation after completion
8. Ongoing career development via AI Career Coach (post-onboarding)

For detailed step-by-step flows (organic onboarding, joblink, sharing), see [Prospect Flows](./prospect-flows.md).

### Hiring Manager Flow

1. **Onboarding & Job Creation**: Signup → persona selection → welcome → job details (paste URL, auto-extract title/location/company) → voice conversation with Sam (AI hiring partner) → AI-generated role requirements (editable) → AI-generated screening questions (editable, reorderable) → success → share → job dashboard
2. **Sharing & Distribution**: Share modal with pre-drafted LinkedIn/X/email messages, platform-specific copy with interview link
3. **Intro Video**: Dashboard banner CTA → AI-generated script → record → optional AI-assisted script editing (voice/text) → save take → video appears on dashboard
4. **Invite Collaborator**: Overflow menu → invite modal (email, role selector, pre-populated message)
5. **Candidate Review**: Job dashboard with pipeline analytics (Impressions → Clicks → Started → Completed → Advanced), distribution donut, candidate table (Unreviewed/Advancing/Rejected/All) → candidate detail page (AI takeaways, evaluation grid with sentiment scoring, per-question video playback, resume takeaways sidebar) → advance/reject

For detailed step-by-step flows, see [Hiring Manager Flows](./hiring-manager-flows.md).

### Recruiter Flow (AI Recruiter)

1. Voice + dynamic UI intake with hiring manager
2. Real-time difficulty analysis and constraint identification
3. Calibration with synthetic prospect profiles
4. Summary and autonomous query building
5. Prospect sourcing and shortlist presentation

### Automated Pipeline Vision

- Full automation from intake to prospect presentation
- Digital twin hiring manager agent (higher accuracy than human baseline)
- Eliminates need for Quick Eval and manual processes
- Entry point: Helix referral evaluation → upsell to full sourcing
- PLG model: ~$500/role automated sourcing service

### Resume Conversion Pipeline

- Real resumes have complex formatting (multi-column, custom fonts) that LLMs parse at ~80-90% accuracy
- Solution: convert uploaded PDF to **Typst** (an intermediate, LLM-editable format) during onboarding using vision-based parsing + LLM conversion
- Conversion surfaces genuine issues (ATS compatibility, weak bullets, formatting) via a diagnosis card, and auto-fixes structural problems
- Prospect selects a premium template and makes a mandatory first edit via NL — the converted resume becomes *theirs*
- Typst source backs both the portfolio view and PDF downloads; edits via NL update the Typst source in real time

---

## Viral Loop Strategy

### Core Loops

**Recruiter-Led Loops**:
1. Recruiter → Hiring Manager (invite to review prospects)
2. Recruiter → Prospect (distribute job links)
3. Recruiter → Recruiter (word-of-mouth referrals)

**Formula**: K = i · c (viral coefficient = shares × conversion)

**Optimization**: Each loop will be measured and optimized independently on:
- i (shares per user)
- c (conversion rate)
- t (cycle time)
- r (retention rate)

Specific K-factor targets, analytics instrumentation, and north star metrics will be defined as the product matures. The K-factor framework is the foundation for how we'll measure and optimize growth.

See: [Viral Loop Framework](../../../projects/Helix/viral-loop-framework.md) for detailed math

---

## Pricing & Monetization

### Value Ladder

**Tier 1: Free (Frictionless Trial)**
- No payment required to start
- Experience "magic moment" before purchase decision
- All personas can try for free

**Tier 2: Credits (Consumption-Based)**
- AI interviews consume credits
- Text-based interviews free (non-AI fallback)
- Pay as you scale
- Referral credits reduce cost

**Tier 3: Enterprise (Controls & Integration)**
- ATS sync/import/export
- SSO and admin console
- Role-based access, governance
- Enterprise reporting

**Tier 4: Spot Pilot (Agentic Sourcing)**
- Time-boxed pilot (e.g., 3 days)
- Credits for additional volume
- Leverages flywheel signal

**Tier 5: People + Agents (Premium Service)**
- Agentic + human recruiters
- ~90% agentic + human last-mile
- Premium pricing

### Pricing Philosophy

**Jevons Paradox**: Lower friction → More usage → Higher total revenue

Even with low per-unit pricing, users:
- Do more work
- Move faster
- Explore more opportunities
- Total consumption increases

**Goal**: Easy to try, hard to give up, economically aligned with impact

---

## Competitive Moat

### Compounding Preference Learning

**The Defensibility**: Deep understanding of what "good" looks like for each hiring manager

**Learns at Three Levels**:
1. **Individual**: HM preferences (signal, fit, bar, style)
2. **Team**: Calibration, role archetypes, trade-offs
3. **Company**: Culture, leveling, compensation, process

**Result**: Harder to switch than stay; onboarding new tool resets learning

### Agentic Improvement

System continuously improves from:
- Outcome feedback (who succeeds)
- Decision patterns (HM and recruiter choices)
- Engagement signals (prospect behavior)
- Cross-role learning

**Increasing Returns**: Better data → Better AI → Better results → More trust → More data

### Switching Costs

- Personalized preference models
- Integrated workflow and ATS connectivity
- Shared decision history
- Trust in system's judgment

**Switching breaks continuity and resets personalization**

---

## Development Principles

### FAAFO: Fast, Ambitious, Autonomous, Fun, Optionality

- **Fast**: AI-accelerated development, record execution time
- **Ambitious**: Intentionally aggressive goals
- **Autonomous**: Teams operate independently with clear interfaces
- **Fun**: Innovative, experimental approach
- **Optionality**: Explore multiple paths in parallel

**Speed is a first-class objective**, not a byproduct.

### Multi-Team Execution

- Three autonomous persona teams
- Clear ownership and accountability
- Platform team enables shared infrastructure
- Metrics-driven (4-layer framework)

### Metrics Framework

All teams measured on **4 layers**:
1. **Team Acceptance**: Internal conviction
2. **End-User Acceptance**: External validation
3. **Real User Metrics**: Production behavior
4. **Outcome Metrics**: Business results

**Principle**: Progress at one layer without movement to next = signal to adjust

---

## Current Status

**Phase**: Vision and strategy definition → moving into design and prototyping  
**Project**: Helix project in active development  
**Target Release**: March 8–13, 2026 (aligned with Aravind's Bangalore visit)  
**Next Steps**:
1. Finalize end-to-end screen designs using existing design language
2. Focus on voice interface with avatar and animations for recruiter intake
3. Coordinate recruiter/hiring manager flows with David's team
4. Emphasize clear benefit explanations at each step to prevent user confusion
5. Finalize agent naming (career coach vs recruiter agent)
6. Platform team builds foundation
7. Prototypes and rapid iteration

---

## Key Documents

**Vision & Strategy**:
- [Recruiting Flywheel Vision (Full)](../../../inputs/2026-Q1/meeting-notes/recruiting-flywheel-vision-aravind-jan-2026.md) - Complete Aravind vision document

**Project Management**:
- [Helix Project](../../../projects/Helix/) - Project brief, PM notes, execution tracking

**Frameworks**:
- [Prospect structure](./prospect-structure.md) - Portfolio + Applications model on job-seeker side (1 mutable portfolio, many immutable application snapshots)
- [Prospect Flows](./prospect-flows.md) - Onboarding (organic & joblink) and sharing/tailoring step-by-step flows
- [Screen Diagrams (Prospect)](./screen-diagrams.md) - ASCII wireframes of key prospect screens (portfolio, applications, wizard, share flow)
- [Hiring Manager Flows](./hiring-manager-flows.md) - Onboarding, job creation, sharing, intro video, candidate review step-by-step flows
- [Screen Diagrams (Hiring Manager)](./hiring-manager-screen-diagrams.md) - ASCII wireframes of key HM screens (account creation, job wizard, dashboard, candidate results, video recording)
- [Network Model](./network-model.md) - Graph visualization, node/edge types, viral loop paths, network metrics
- [Network Quantification](./analytics/network-quantification.md) - Formulas and worked examples for network size and health
- [Viral Loop Metrics](./analytics/viral-loop-metrics.md) - Per-loop funnels, metrics, and K-factors for growth tracking
- [Viral Loop Framework](../../../projects/Helix/viral-loop-framework.md) - Mathematical model for growth loops
- [Team Considerations](../../../projects/Helix/team-considerations.md) - Trust, safety, UX considerations per team

---

## Summary

**Helix** is SeekOut's ambitious entry into consumer-oriented viral hiring products. By reimagining hiring as sharing-driven and building mathematical viral loops across hiring managers, recruiters, and prospects, Helix aims to create a new category of recruiting tools that grow organically through network effects.

**Differentiation**:
- Viral growth vs sales-led
- Individual adoption with optional enterprise integration
- Free-to-paid credits model
- Compounding AI preference learning
- Multi-sided network connecting three personas

**Vision**: Own the high-signal sharing and evaluation layer in hiring, then extend into monetization through credits, enterprise features, and premium services.

---

*For complete details, see [Recruiting Flywheel Vision Document](../../../inputs/2026-Q1/meeting-notes/recruiting-flywheel-vision-aravind-jan-2026.md)*
