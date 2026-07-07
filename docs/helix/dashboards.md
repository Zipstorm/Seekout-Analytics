---
confluence:
  page_id: "1750433795"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Dashboards & Funnels

**Product:** Helix (SeekOut.ai)  
**Analytics Platform:** PostHog  
**Last Updated:** July 2026

For event definitions and properties, see [Helix Analytics Events Tracker](./event-catalog.md).
For naming conventions and PostHog setup, see [Helix Analytics Events Schema](./event-schema.md).

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
| Signup Complete | c_complete | Account Create Succeeded | Account & Surface |
| Activate | c_activate | Account Activated | Account & Surface |

### Profile Sharing Loop

| Stage | K-factor Term | Event | Defined In |
|-------|--------------|-------|------------|
| Share | i | Custom Link Shared | Prospect Surface |
| View | c_view | Profile Link Viewed | Anonymous User Events |
| Engage | c_click | Profile Link Engaged | Anonymous User Events |
| Signup Form | c_form | Signup Started | Account & Surface |
| Signup Complete | c_complete | Account Create Succeeded | Account & Surface |
| Activate | c_activate | Account Activated | Account & Surface |

---

## Dashboards

| Dashboard | Owner | Status |
|-----------|-------|--------|
| Growth Dashboard | Platform Team | Not Started |
| Prospect Dashboard | Prospect Team | Not Started |
| Hiring Dashboard | HM/Recruiter Team | Not Started |
| Interview Dashboard | Prospect / Hiring Team | Not Started |
| Viral Loop Dashboard | Platform Team | Not Started |
| Platform Health Dashboard | Platform Team | Not Started |

### Growth Dashboard (Platform Team)
- New accounts per day/week, broken down by `signup_context`
- K-factor per viral loop (job sharing, profile sharing)
- Conversion funnel: Job Link Viewed → Job Link Engaged → Signup Started → Account Create Succeeded → Activated
- Activation rate by signup context
- Onboarding-to-job conversion: Account Create Succeeded → Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Posting Draft Created → Job Posting Published
- Retention: WAU, MAU, D7/D30 return rates

### Prospect Dashboard (Prospect Team)
- Profile creation completion rate
- Custom links created per user, job-specific vs. general split (`is_job_specific`)
- Custom link shares by channel (`share_channel`: copy / email / linkedin / other)
- Interest expressions per user; withdrawal rate and `reason` distribution
- Career coach session frequency, `session_type` (first_time vs. returning), `input_mode` (text vs. voice)
- Career coach message volume by `topic` (profile_improvement / job_application / career_advice)
- Onboarding to profile creation funnel: Account Create Succeeded → Onboarding Intro Complete Button Clicked → Page Viewed (filter: `current_page_context` value = `"candidate_create_profile"`) → Build Profile Button Clicked → Candidate Profile Create Succeeded
- Resume upload conversion: Candidate Resume Upload Button Clicked → Candidate Resume Upload Succeeded
- Profile photo adoption: Add Profile Photo Button Clicked → Profile Photo Add Succeeded
- Profile completeness: Candidate Profile Overview Load Succeeded filtered by `profile_completeness_rate`
- Portfolio publish conversion: Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded
- Handle adoption rate: Candidate Profile Create Succeeded filtered by `has_handle` = true

### Hiring Dashboard (HM/Recruiter Team)
- Jobs created and published per user
- Jobs published: public vs. private split (`job_visibility`)
- Job status transitions (`from_status` → `to_status` from Job Status Changed)
- Shares per job by channel (`share_channel` from Job Shared)
- Team members invited per job, by `invited_role_label` and `invite_method`
- Time from Interest Expressed → first Interest Reviewed (`time_to_review_seconds`)
- Review decision distribution (shortlisted / declined / needs_discussion)
- Interests per job (using job group analytics)
- Job post wizard completion funnel — step-by-step drop-off rates (Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Post Wizard Intake Mode Selected → Job Post Wizard Role Requirements Completed → Job Post Wizard Interview Questions Completed → Job Post Wizard Verification Completed → Job Posting Published)
- Job post wizard abandonment — Step 1 drop-off rate (Job Post Wizard Started → Job Post Wizard Job Details Completed)
- Sam session adoption — voice/text session completion rate (Job Post Wizard Intake Mode Selected → Sam Session Started → Sam Session Ended), broken down by `input_mode`
- Sam voice setup failure rate — Sam Session Started where `mic_enabled` = false, `error_category` distribution (timeout / hardware / unknown)
- Voice session stats — completion rate (Sam Session Started → Sam Session Ended), avg `duration_seconds`
- AI content modification rate — % of jobs where requirements/questions were modified (Requirement Modified / Question Modified counts vs Job Posting Published)
- Intro video adoption — % of jobs with intro video (`has_intro_video`), recording completion rate (Record Video Button Clicked → Intro Video Created)
- Candidate review depth — avg tabs viewed per candidate, % of candidates where recording was played. Time-to-decision: median seconds from Candidate Viewed timestamp to Review Decision Made timestamp (computed per-candidate, not a funnel).

### Interview Dashboard (Prospect / Hiring Team)
- Interview completion funnel: Page Viewed (filter `current_page_context = candidate_interview_landing`) → Get Started Interview Button Clicked → Candidate Interview Info Next Button Clicked → Candidate Interview Resume Next Button Clicked → Candidate Interview Identity Verification Succeeded → Candidate Interview Screening Response Submit Succeeded → Candidate Interview Started → Candidate Interview Submit Succeeded
- Identity verification funnel: Open Identity Check Link Clicked → Candidate Interview Identity Verification Succeeded
- Device → start funnel: Allow Device Access Button Clicked → Device Access Grant Succeeded → Candidate Interview Started
- Per-question completion funnel: Candidate Interview Started → Candidate Interview Question Answer Succeeded → Candidate Interview Submit Succeeded (breakdown by `question_number` and `question_status`)
- Interview → signup funnel: Candidate Interview Submit Succeeded → Account Create Succeeded (filter `entry_point = interview`)
- Publish conversion funnel: Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded
- Screening response edit funnel: Candidate Interview Screening Response Edit Button Clicked → Candidate Interview Screening Response Edit Succeeded
- Question skip rate: Candidate Interview Question Skip Succeeded trend by `question_number`
- Question retake rate: Candidate Interview Question Answer Succeeded (`question_status = answered_restarted`) trend by `question_number`, `job_id`
- Resume attach rate at interview: Candidate Interview Resume Next Button Clicked trend by `has_resume`
- AI conversation completion rate: Candidate Interview Question Answer Succeeded trend by `ai_conversation_completed`, `question_number`
- Test run vs real interview: Candidate Interview Submit Succeeded trend by `is_test_run`

### Viral Loop Dashboard (Platform Team)
- Shares per user (i) — segmented by channel
- View-to-signup conversion (c) — decomposed into c_view, c_click, c_form, c_complete, c_activate
- Cycle time (t) — days from activation to first share
- Effective K per viral loop type

### Platform Health Dashboard (Platform Team)

Tracks rejected-result and technical-error rates across the Interaction / Started → Success / Rejected / Error flows defined in the schema.

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|------|-----------------------------|---------------|----------------|-------------|
| Login / Signup | Login Started Button Clicked | Account Create Succeeded (new) or Auth Login Succeeded (returning) | Auth Login Rejected | -- |
| Sharing a job | Share Button Clicked | Job Shared | Job Share Failed | -- |
| Expressing interest | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed | -- |
| Inviting team member | Invite Button Clicked | Team Member Invited | Team Member Invite Failed | -- |
| Creating a job (wizard start) | Create Job Button Clicked, Job Post Wizard Started | -- | -- | -- |
| Creating a job (draft save) | Job Post Wizard Job Details Completed | Job Posting Draft Created | Job Creation Failed | -- |
| Email verification (job) | Job Verification Code Send Button Clicked | Job Posting Verified | -- | -- |
| Publishing a job (verified) | Job Post Wizard Verification Completed | Job Posting Published | -- | -- |
| Publishing a job (skipped) | Job Post Wizard Verification Skipped | Job Posting Published | -- | -- |
| Email verification | -- | Auth Email Verify Code Send Succeeded | Auth Email Verify Rejected | Auth Email Verify Code Send Errored |
| Session restore | *(implicit — on app load)* | Auth Session Restore Succeeded | -- | Auth Session Restore Errored |
| Recording intro video | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed | -- |
| Persona switch | Switch Persona Button Clicked | Persona Updated | Persona Update Failed | -- |
| Resume upload | Candidate Resume Upload Button Clicked | Candidate Resume Upload Succeeded | Candidate Resume Upload Rejected | Candidate Resume Upload Errored |
| Profile photo upload | Add Profile Photo Button Clicked | Profile Photo Add Succeeded | Profile Photo Upload Failed | -- |
| Profile creation | Build Profile Button Clicked | Candidate Profile Create Succeeded | -- | Candidate Profile Create Errored |
| Persona selection | Onboarding Persona Card Clicked | Account Create Succeeded | -- | -- |
| Intro completion | Onboarding Intro Complete Button Clicked | -- | -- | -- |
| Onboarding completion | -- | Onboarding Complete Succeeded | -- | -- |
| Portfolio publish | Candidate Portfolio Publish Button Clicked | Candidate Portfolio Publish Succeeded | -- | Candidate Portfolio Publish Errored |
| Unpublish portfolio | Candidate Portfolio Unpublish Button Clicked | Candidate Portfolio Unpublish Succeeded | -- | -- |
| Rename portfolio | Candidate Portfolio Rename Button Clicked | Candidate Portfolio Rename Succeeded | -- | -- |
| Delete portfolio | Candidate Portfolio Delete Button Clicked | Candidate Portfolio Delete Succeeded | -- | -- |
| Profile photo remove | Candidate Profile Photo Remove Button Clicked | Candidate Profile Photo Remove Succeeded | -- | Candidate Profile Photo Remove Errored |
| Custom link delete | Candidate Custom Link Delete Button Clicked | Candidate Custom Link Delete Succeeded | -- | Candidate Custom Link Delete Errored |
| Identity verification | Open Identity Check Link Clicked | Candidate Interview Identity Verification Succeeded | Candidate Interview Identity Verification Rejected | Candidate Interview Identity Verification Errored |
| Device access | Allow Device Access Button Clicked | Device Access Grant Succeeded | Device Access Rejected | -- |
| Start interview | Candidate Interview Start Button Clicked | Candidate Interview Started | -- | -- |
| Question restart | Candidate Interview Question Restart Button Clicked | Candidate Interview Question Restart Succeeded | -- | Candidate Interview Question Restart Errored |
| Question skip | Candidate Interview Question Skip Button Clicked | Candidate Interview Question Skip Succeeded | Candidate Interview Question Skip Rejected | Candidate Interview Question Skip Errored |
| Screening response edit | Candidate Interview Screening Response Edit Button Clicked | Candidate Interview Screening Response Edit Succeeded | -- | -- |
| Submit interview | -- | Candidate Interview Submit Succeeded | Candidate Interview Submit Rejected | -- |

- Rejected rate per flow (rejected results / interactions or starts) over time
- Technical error rate where an `Error Event` exists
- `error_category` distribution per flow (with `error_reason` drill-down for debugging)
- Interaction/start-to-success conversion rate per flow
