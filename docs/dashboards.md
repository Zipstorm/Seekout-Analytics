---
confluence:
  page_id: "1750433795"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Dashboards & Funnels

**Product:** Helix (SeekOut.ai)  
**Analytics Platform:** PostHog  
**Last Updated:** April 2026

For event definitions and properties, see [Helix Analytics Events Tracker](./event-catalog.md).
For naming conventions and PostHog setup, see [Helix Analytics Events Schema](./event-schema.md).

---

## Login & Onboarding Funnel

**Dashboard:** PostHog — Funnel Insight
**Status:** Live

### New User Signup Funnel

Tracks the full journey from landing page to product entry for new users.

| Step | Event | Filter | Drop-off means |
|------|-------|--------|---------------|
| 1 | `Page Viewed` | `current_page_context = auth/landing` | — |
| 2 | `Login Started` | | User saw page but didn't click CTA (bounce) |
| 3 | `Page Viewed` | `current_page_context = onboarding/role_selection` | User clicked CTA but didn't complete auth |
| 4 | `Account Created` | | User saw persona options but didn't commit |
| 5 | `Page Viewed` | `current_page_context = onboarding/intro` | Should be ~100% (auto-navigates) |
| 6 | `Intro Completed` | | User saw intro but didn't click "Let's go" |
| 7 | `Page Viewed` | `current_page_context` starts with `hiring_manager/` or `recruiter/` or `candidate/` | Should be ~100% (auto-navigates) |

**Recommended breakdowns:**
- `entry_point` (person property) — which acquisition channel converts best
- `first_persona` (person property) — does persona affect completion rate

### Key Metrics from This Funnel

| Metric | Formula |
|--------|---------|
| Landing → CTA rate | Step 2 / Step 1 |
| Auth completion rate | Step 3 / Step 2 |
| Role selection rate | Step 4 / Step 3 |
| Full signup rate | Step 4 / Step 1 |
| Intro engagement rate | Step 6 / Step 5 |

### Events Used

| Event | Type | Source | Implemented? |
|-------|------|--------|-------------|
| `Page Viewed` | page_view | Frontend (JS) | Yes |
| `Login Started` | user_action | Frontend (JS) | Yes |
| `Account Created` | user_action | Frontend (JS) | Yes |
| `Intro Completed` | user_action | Frontend (JS) | Yes |

For full event specs, see [event-definitions/login-onboarding/](../event-definitions/login-onboarding/).

---

## Viral Loop Funnels

Maps events to the K-factor formula: **K = i × c**, where **c = c_view × c_click × c_form × c_complete × c_activate**

`c_signup` from earlier versions is now decomposed into `c_form` (reach signup form) × `c_complete` (finish signup).

### Job Sharing Loop

| Stage | K-factor Term | Event | Defined In |
|-------|--------------|-------|------------|
| Share | i | Job Shared | Hiring Surface |
| View | c_view | Job Link Viewed | Anonymous User Events |
| Engage | c_click | Job Link Engaged | Anonymous User Events |
| Signup Form | c_form | Signup Started | Account & Surface |
| Signup Complete | c_complete | Account Created | Account & Surface |
| Activate | c_activate | Account Activated | Account & Surface |

### Profile Sharing Loop

| Stage | K-factor Term | Event | Defined In |
|-------|--------------|-------|------------|
| Share | i | Custom Link Shared | Prospect Surface |
| View | c_view | Profile Link Viewed | Anonymous User Events |
| Engage | c_click | Profile Link Engaged | Anonymous User Events |
| Signup Form | c_form | Signup Started | Account & Surface |
| Signup Complete | c_complete | Account Created | Account & Surface |
| Activate | c_activate | Account Activated | Account & Surface |

---

## Dashboards

| Dashboard | Owner | Status |
|-----------|-------|--------|
| Growth Dashboard | Platform Team | Not Started |
| Prospect Dashboard | Prospect Team | Not Started |
| Hiring Dashboard | HM/Recruiter Team | Not Started |
| Viral Loop Dashboard | Platform Team | Not Started |
| Platform Health Dashboard | Platform Team | Not Started |

### Growth Dashboard (Platform Team)
- New accounts per day/week, broken down by `entry_point` (person property) and `first_persona`
- Login & Onboarding funnel (see above): Page Viewed (auth/landing) → Login Started → Account Created → Intro Completed → Page Viewed (home)
- K-factor per viral loop (job sharing, profile sharing)
- Viral conversion funnel: Job Link Viewed → Job Link Engaged → Login Started → Account Created → Activated
- Activation rate by entry_point and first_persona
- Onboarding-to-job conversion: Account Created → Job Wizard Started → Job Wizard Step Completed (step 1) → Job Created
- Retention: WAU, MAU, D7/D30 return rates

### Prospect Dashboard (Prospect Team)
- Profile creation completion rate
- Custom links created per user, job-specific vs. general split (`is_job_specific`)
- Custom link shares by channel (`share_channel`: copy / email / linkedin / other)
- Interest expressions per user; withdrawal rate and `reason` distribution
- Career coach session frequency, `session_type` (first_time vs. returning), `input_mode` (text vs. voice)
- Career coach message volume by `topic` (profile_improvement / job_application / career_advice)

### Hiring Dashboard (HM/Recruiter Team)
- Jobs created and published per user
- Jobs published: public vs. private split (`visibility`)
- Job status transitions (`from_status` → `to_status` from Job Status Changed)
- Shares per job by channel (`share_channel` from Job Shared)
- Team members invited per job, by `invited_role_label` and `invite_method`
- Time from Interest Expressed → first Interest Reviewed (`time_to_review_seconds`)
- Review decision distribution (shortlisted / declined / needs_discussion)
- Interests per job (using job group analytics)
- Job wizard completion funnel — step-by-step drop-off rates (Job Wizard Started → Job Wizard Step Completed step 1 → 2 → 3 → 4 → Job Created). Note: Step 4 completion fires both Job Wizard Step Completed (step 4) and the Create Job Button Clicked → Job Created intent/outcome pair.
- Voice session stats — completion rate (Voice Session Started → Voice Session Ended), avg `duration_seconds`
- AI content modification rate — % of jobs where requirements/questions were modified (Requirement Modified / Question Modified counts vs Job Created)
- Intro video adoption — % of jobs with intro video (`has_intro_video`), recording completion rate (Record Video Button Clicked → Intro Video Created)
- Candidate review depth — avg tabs viewed per candidate, % of candidates where recording was played. Time-to-decision: median seconds from Candidate Viewed timestamp to Review Decision Made timestamp (computed per-candidate, not a funnel).

### Viral Loop Dashboard (Platform Team)
- Shares per user (i) — segmented by channel
- View-to-signup conversion (c) — decomposed into c_view, c_click, c_form, c_complete, c_activate
- Cycle time (t) — days from activation to first share
- Effective K per viral loop type

### Platform Health Dashboard (Platform Team)

Tracks failure rates across the five Intent → Success / Failure triplets defined in the event catalog.

| Flow | Intent Event | Success Event | Failure Event |
|------|-------------|---------------|---------------|
| Job creation | Create Job Button Clicked | Job Created | Job Creation Failed |
| Job sharing | Share Button Clicked | Job Shared | Job Share Failed |
| Interest expression | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed |
| Team invite | Invite Button Clicked | Team Member Invited | Team Member Invite Failed |
| Intro video recording | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed |

- Failure rate per flow (failures / intents) over time
- `error_category` distribution per flow (with `error_reason` drill-down for debugging)
- Intent-to-success conversion rate per flow
