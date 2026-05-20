---
confluence:
  page_id: "1748861000"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Events Tracker

**Product:** Helix (SeekOut.ai)
**Analytics Platform:** PostHog
**Last Updated:** May 2026

For naming conventions, PostHog setup, and sample code, see [Helix Analytics Events Schema](./event-schema.md).
For dashboards and funnel mappings, see [Helix Analytics Dashboards & Funnels](./dashboards.md).
For login & onboarding event specs, see [event-definitions/login-onboarding/](../event-definitions/login-onboarding/).

---

## Event Catalog

### Login & Onboarding Events

Events for the login and new user onboarding flow. Full specs in [event-definitions/login-onboarding/](../event-definitions/login-onboarding/).


| Event             | Area       | Type        | Trigger                                                        | Source   | Properties                                                                                                                              | Group | Property Updates                                                              | Status |
| ----------------- | ---------- | ----------- | -------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------- | ------ |
| Page Viewed       | Navigation | page_view   | User lands on a meaningful page                                | Frontend | `current_page_context`, `previous_page_context`, `entry_point` (login page only)                                                        | --    | `$set_once: entry_point, first_referrer, first_landing_url` (login page only) | Live   |
| Login Started     | Account    | user_action | User clicks "Continue with Google or Email" on auth landing    | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entry_point`, `entity_type`, `component`                    | --    | --                                                                            | Live   |
| Login Cancelled   | Account    | user_action | User closes MSAL popup without completing auth                 | Frontend | `auth_mode`, `error_code`                                                                                                               | --    | --                                                                            | Live   |
| Account Created   | Account    | user_action | User clicks "Continue as [Persona]" and server confirms role   | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `first_persona`, `auth_method`, `referred_by` | --    | `$set: current_persona, activated_personas`; `$set_once: first_persona, account_created_at, referred_by` | Live   |
| Intro Completed   | Account    | user_action | User clicks "Let's go" on onboarding intro page               | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `auth_method`                    | --    | --                                                                            | Live   |


### Auth Lifecycle Events (existing — to be replaced)

These events are still firing from `authStore.ts` and will be replaced when the returning user flow is implemented.


| Event                          | Area    | Type | Trigger                                        | Source   | Properties                                     | Group | Property Updates | Status       |
| ------------------------------ | ------- | ---- | ---------------------------------------------- | -------- | ---------------------------------------------- | ----- | ---------------- | ------------ |
| Auth Login Succeeded           | Account | --   | Backend confirms successful auth               | Frontend | `auth_mode`, `verification_required`           | --    | `$set: email, name, org_id, org_name, org_domain` (via `identifyUser()`) | Live (legacy) |
| Auth Login Failed              | Account | --   | Backend returns auth error                     | Frontend | `auth_mode`, `status_code`, `error_detail`     | --    | --               | Live (legacy) |
| Auth Session Restore Succeeded | Account | --   | Session restored from refresh token            | Frontend | `auth_mode`                                    | --    | `$set: email, name, org_id, org_name, org_domain` (via `identifyUser()`) | Live (legacy) |
| Auth Session Restore Failed    | Account | --   | Session restore failed                         | Frontend | `status_code`                                  | --    | --               | Live (legacy) |
| Auth Refresh Failed            | Account | --   | Token refresh failed                           | Frontend | `source`, `status_code`                        | --    | --               | Live (legacy) |
| Auth Logout Completed          | Account | --   | User logs out                                  | Frontend | `auth_mode`                                    | --    | --               | Live (legacy) |


### Auth Dev Events (dev-only)


| Event                    | Area    | Type | Trigger                  | Source   | Properties               | Group | Property Updates | Status    |
| ------------------------ | ------- | ---- | ------------------------ | -------- | ------------------------ | ----- | ---------------- | --------- |
| Auth Dev Login Started   | Account | --   | Dev login initiated      | Frontend | `auth_mode`              | --    | --               | Dev only  |
| Auth Dev Login Succeeded | Account | --   | Dev login succeeded      | Frontend | `auth_mode`              | --    | --               | Dev only  |
| Auth Dev Login Failed    | Account | --   | Dev login failed         | Frontend | `auth_mode`, `status_code`, `error_detail` | --    | --               | Dev only  |


### Email Verification Events


| Event                              | Area    | Type | Trigger                                | Source   | Properties                          | Group | Property Updates | Status |
| ---------------------------------- | ------- | ---- | -------------------------------------- | -------- | ----------------------------------- | ----- | ---------------- | ------ |
| Auth Email Verify Code Sent        | Account | --   | Verification code sent to user's email | Frontend | `cooldown_seconds`                  | --    | --               | Live   |
| Auth Email Verify Code Send Failed | Account | --   | Failed to send verification code       | Frontend | `status_code`, `error_detail`       | --    | --               | Live   |
| Auth Email Verify Resend Clicked   | Account | --   | User clicks resend verification link   | Frontend | --                                  | --    | --               | Live   |
| Auth Email Verified                | Account | --   | Email verification succeeds            | Frontend | --                                  | --    | --               | Live   |
| Auth Email Verify Failed           | Account | --   | Email verification fails               | Frontend | `status_code`, `error_detail`, `attempts_remaining` | --    | --               | Live   |


### Phone Collection Events


| Event                     | Area    | Type | Trigger                       | Source   | Properties                    | Group | Property Updates | Status |
| ------------------------- | ------- | ---- | ----------------------------- | -------- | ----------------------------- | ----- | ---------------- | ------ |
| Auth Phone Submitted      | Account | --   | User submits phone number     | Frontend | `phone_length`, `country_code` | --    | --               | Live   |
| Auth Phone Submit Failed  | Account | --   | Phone submission fails        | Frontend | `status_code`, `error_detail`  | --    | --               | Live   |
| Auth Phone Skipped        | Account | --   | User skips phone collection   | Frontend | --                             | --    | --               | Live   |


### Account & Persona Events


| Event             | Area    | Type    | Trigger                                                   | Source   | Properties                                                                                                    | Group | Property Updates                                                            | Status      |
| ----------------- | ------- | ------- | --------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------- | ----------- |
| Account Activated              | Account | --      | First meaningful action completed                                    | Backend  | `activation_action`, `days_since_signup`                                                           | --    | --                                                                          | Not Started |
| Switch Persona Button Clicked  | Account | Intent  | User clicks the ⇄ chevron next to current persona in sidebar        | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | -- | --                                                                          | Not Started |
| Persona Updated                | Account | Success | Backend confirms persona switch after user selects a different persona | Backend  | `previous_persona`, `current_persona`                                       | --    | `$set: current_persona, activated_personas`                                 | Not Started |
| Persona Update Failed          | Account | Failure | Backend returns error on persona switch attempt                       | Backend  | `previous_persona`, `target_persona`, `error_reason`, `error_category`      | --    | --                                                                          | Not Started |


### Anonymous User Events

Events fired by unauthenticated visitors interacting with shared links before signup.


| Event                | Area      | Type | Trigger                                        | Source   | Properties                                                                             | Group | Property Updates | Status      |
| -------------------- | --------- | ---- | ---------------------------------------------- | -------- | -------------------------------------------------------------------------------------- | ----- | ---------------- | ----------- |
| Job Link Viewed      | Anonymous | --   | Visitor opens a shared job link                | Either   | `referrer_user_id`, `referrer_job_id`, `is_authenticated`                              | --    | --               | Not Started |
| Job Link Engaged     | Anonymous | --   | Visitor takes action on a shared job page      | Frontend | `referrer_user_id`, `referrer_job_id`, `action`                                        | --    | --               | Not Started |
| Profile Link Viewed  | Anonymous | --   | Visitor opens a prospect's shared profile link | Either   | `profile_user_id`, `custom_link_id`, `is_authenticated`                                | --    | --               | Not Started |
| Profile Link Engaged | Anonymous | --   | Visitor takes action on a shared profile page  | Frontend | `profile_user_id`, `custom_link_id`, `action`                                          | --    | --               | Not Started |


### Prospect Persona Events


| Event                           | Area     | Type    | Trigger                                     | Source   | Properties                                                                                             | Group | Property Updates | Status      |
| ------------------------------- | -------- | ------- | ------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------ | ----- | ---------------- | ----------- |
| Profile Created                 | Prospect | --      | AI generates initial profile from resume    | Backend  | `input_method`                                                                                         | --    | --               | Not Started |
| Profile Section Updated         | Prospect | --      | User edits a profile section                | Frontend | `section`                                                                                              | --    | --               | Not Started |
| Custom Link Created             | Prospect | --      | User creates a named shareable link         | Backend  | `link_name`, `is_job_specific` (boolean), `target_job_title` (optional), `target_company` (optional)   | --    | --               | Not Started |
| Custom Link Shared              | Prospect | --      | User shares a custom link                   | Frontend | `share_channel`, `is_job_specific`                                                                     | --    | --               | Not Started |
| Express Interest Button Clicked | Prospect | Intent  | Prospect clicks Express Interest on a job   | Frontend | `job_id`                                                                                               | --    | --               | Not Started |
| Interest Expressed              | Prospect | Success | Server confirms interest recorded           | Backend  | `job_id`, `has_custom_link`, `has_resume`                                                              | --    | --               | Not Started |
| Interest Expression Failed      | Prospect | Failure | Server returns error on interest submission | Backend  | `job_id`, `error_reason`, `error_category`                                                             | --    | --               | Not Started |
| Interest Withdrawn              | Prospect | --      | Prospect withdraws interest                 | Backend  | `job_id`, `reason`                                                                                     | --    | --               | Not Started |
| Career Coach Session Started    | Prospect | --      | User begins AI career coach interaction     | Frontend | `session_type`, `input_mode`                                                                           | --    | --               | Not Started |
| Career Coach Message Sent       | Prospect | --      | User sends message to career coach          | Frontend | `message_type`, `topic`                                                                                | --    | --               | Not Started |


### Hiring Persona Events

All hiring persona events include `job_id`. The user's persona context is available via the `current_persona` person property (`$set`) — no need to pass it per-event. See [Schema](./event-schema.md) for standard event properties.


| Event                       | Area   | Type    | Trigger                                                   | Source   | Properties                                                                                                                           | Group | Property Updates                                                                            | Status      |
| --------------------------- | ------ | ------- | --------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------------- | ----------- |
| Create Job Button Clicked   | Hiring | Intent  | User clicks "+ Create job" button on HM job postings page | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`                   | --    | --                                                                                          | Not Started |
| Job Post Wizard Started     | Hiring | Success | Wizard page mounts with router state isNewWizard=true     | Frontend | `start_source`, `current_page_context`                                                                                  | --    | --                                                                                          | Not Started |
| Job Post Wizard Job Details Completed | Hiring | -- | User clicks "Next →" on Job Details step               | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | -- | --                                                                    | Not Started |
| Job Posting Draft Created   | Hiring | Success | Server creates job draft via POST /api/v1/core/job        | Backend  | `job_id`, `job_title`, `company_name`, `location`, `job_status`                                                         | `job` | `group(job): job_title, job_status, created_by_user_id, created_at`                         | Not Started |
| Job Creation Failed         | Hiring | Failure | Server returns error on job creation                      | Backend  | `error_reason`, `error_category`                                                                                        | `job` | --                                                                                          | Not Started |
| Job Post Wizard Role Understanding Completed | Hiring | -- | User clicks "Next →" or "Skip" on Understanding the Role step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `intake_mode` | `job` | -- | Not Started |
| Sam Session Started         | Hiring | --      | Sam session initializes after user selects voice or text  | Frontend | `job_id`, `input_mode`                                                                                                  | `job` | --                                                                                          | Not Started |
| Sam Session Ended           | Hiring | --      | User clicks "End Session" or Sam auto-ends                | Frontend | `job_id`, `input_mode`, `duration_seconds`, `ended_by`                                                                  | `job` | --                                                                                          | Not Started |
| Sam Voice Session Setup Failed | Hiring | Failure | Mic permission denied or device unavailable            | Frontend | `job_id`, `error_reason`, `error_category`                                                                              | `job` | --                                                                                          | Not Started |
| Job Post Wizard Role Requirements Completed | Hiring | -- | User clicks "Next →" or "+ Add question" on Role Requirements step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- | Not Started |
| Job Post Wizard Interview Questions Completed | Hiring | -- | User clicks "Next →", "+ Add question", or "← Back" on Interview Questions step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- | Not Started |
| Screening Configuration Saved | Hiring | --    | Backend saves screening config via POST /api/v1/jobs/flow/{job_id}/screening | Backend | `job_id`, `job_title`, `company_name`, `location`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): questions_count, identity_verification_mode` | Not Started |
| Job Post Wizard Verification Completed | Hiring | -- | User clicks "Send code", "Maybe later", or "← Back" on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- | Not Started |
| Job Posting Verified        | Hiring | Success | Backend verifies 6-digit code successfully                | Backend  | `job_id`, `job_title`, `is_verified`                                                                                    | `job` | `group(job): is_verified`                                                                   | Not Started |
| Job Posting Published       | Hiring | --      | Backend publishes the job via POST /api/v1/jobs/flow/{job_id}/verify | Backend | `job_id`, `job_title`, `company_name`, `location`, `job_status`, `is_verified`, `visibility`, `questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): job_status, is_verified, job_visibility` | Not Started |
| Share Button Clicked        | Hiring | Intent  | User clicks Share button on a job                         | Frontend | `job_id`, `share_source`                                                                                                | `job` | --                                                                                          | Not Started |
| Job Shared                  | Hiring | Success | Server confirms job link shared                           | Backend  | `job_id`, `share_channel`, `shared_by_user_id`, `share_source`                                                          | `job` | --                                                                                          | Not Started |
| Job Share Failed            | Hiring | Failure | Server returns error on share attempt                     | Backend  | `job_id`, `error_reason`, `error_category`, `share_source`                                                              | `job` | --                                                                                          | Not Started |
| Job Status Changed          | Hiring | --      | Job status updated                                        | Backend  | `job_id`, `from_status`, `to_status`                                                                                    | `job` | `group(job): job_status`                                                                    | Not Started |
| Invite Button Clicked       | Hiring | Intent  | User clicks Invite button on a job                        | Frontend | `job_id`                                                                                                                | `job` | --                                                                                          | Not Started |
| Team Member Invited         | Hiring | Success | Server confirms invite sent                               | Backend  | `job_id`, `invited_role_label`, `invite_method`                                                                         | `job` | --                                                                                          | Not Started |
| Team Member Invite Failed   | Hiring | Failure | Server returns error on invite attempt                    | Backend  | `job_id`, `error_reason`, `error_category`                                                                              | `job` | --                                                                                          | Not Started |
| Team Member Joined          | Hiring | --      | Invited user joins a job team                             | Backend  | `job_id`, `role_label`, `signup_context`                                                                                | `job` | `$set_once: signup_context`                                                                 | Not Started |
| Interest Reviewed           | Hiring | --      | Team member reviews an expression of interest             | Frontend | `job_id`, `time_to_review_seconds`                                                                                      | `job` | --                                                                                          | Not Started |
| Review Decision Made        | Hiring | --      | Reviewer makes a decision                                 | Backend  | `job_id`, `decision`                                                                                                    | `job` | --                                                                                          | Not Started |
| Requirement Modified        | Hiring | --      | User adds/edits/deletes an AI-generated requirement       | Frontend | `job_id`, `modification_type`                                                                                           | `job` | --                                                                                          | Not Started |
| Question Modified           | Hiring | --      | User adds/edits/deletes/reorders an AI-generated question | Frontend | `job_id`, `modification_type`                                                                                           | `job` | --                                                                                          | Not Started |
| Record Video Button Clicked | Hiring | Intent  | User clicks record intro video CTA                        | Frontend | `job_id`                                                                                                                | `job` | --                                                                                          | Not Started |
| Intro Video Created         | Hiring | Success | Server confirms video saved                               | Backend  | `job_id`, `duration_seconds`, `takes_count`                                                                             | `job` | `group(job): has_intro_video = true`                                                        | Not Started |
| Intro Video Creation Failed | Hiring | Failure | Server error on video save                                | Backend  | `job_id`, `error_reason`, `error_category`                                                                              | `job` | --                                                                                          | Not Started |
| Intro Video Deleted         | Hiring | --      | User deletes intro video                                  | Backend  | `job_id`                                                                                                                | `job` | `group(job): has_intro_video = false`                                                       | Not Started |
| Intro Script Updated        | Hiring | --      | User saves script changes from AI editor                  | Backend  | `job_id`, `edit_method`                                                                                                 | `job` | --                                                                                          | Not Started |
| Candidate Viewed            | Hiring | --      | User opens candidate detail page                          | Frontend | `job_id`, `candidate_id`, `ai_recommendation`                                                                           | `job` | --                                                                                          | Not Started |
| Candidate Tab Viewed        | Hiring | --      | User views a tab on candidate detail                      | Frontend | `job_id`, `candidate_id`, `tab_name`                                                                                    | `job` | --                                                                                          | Not Started |
| Candidate Recording Played  | Hiring | --      | User plays a candidate video recording                    | Frontend | `job_id`, `candidate_id`, `question_number`                                                                             | `job` | --                                                                                          | Not Started |


### Chat WebSocket Events


| Event                        | Area | Type | Trigger                       | Source   | Properties | Group | Property Updates | Status |
| ---------------------------- | ---- | ---- | ----------------------------- | -------- | ---------- | ----- | ---------------- | ------ |
| Chat WebSocket Connected     | Chat | --   | WebSocket connection opened   | Frontend | --         | --    | --               | Live   |
| Chat WebSocket Error         | Chat | --   | WebSocket error               | Frontend | --         | --    | --               | Live   |
| Chat WebSocket Abnormal Close| Chat | --   | WebSocket closed abnormally   | Frontend | --         | --    | --               | Live   |
| Chat WebSocket Parse Error   | Chat | --   | Failed to parse WS message    | Frontend | --         | --    | --               | Live   |


---

## Removed Events

Events that were previously defined but have been removed or replaced.

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|-------------|
| Signup Started | Login Started | Wrong name (implied new users), hardcoded signup_context | April 2026 |
| Auth Login Started | Login Started | Fired too late (after MSAL popup), redundant | April 2026 |
| Auth Login Cancelled | Login Cancelled | Renamed for consistency | April 2026 |
| Auth Role Updated | Account Created | Role selection during onboarding now fires Account Created | April 2026 |
| Auth Role Update Failed | _(removed)_ | Error handling moved to Account Created flow | April 2026 |
| Persona Selected | Account Created | Combined into single event — role selection IS account creation | April 2026 |
| Account Created (backend) | Account Created (frontend) | Moved from backend 5s heuristic to frontend role selection | April 2026 |
| Persona Activated | Persona Updated | Renamed — "Activated" implied adding a new persona; "Updated" reflects switching between existing personas | May 2026 |
| Job Created | Job Posting Draft Created | Renamed — draft is created on step 1 "Next", not on final publish | May 2026 |
| Job Published | Job Posting Published | Renamed + enriched with full job snapshot properties | May 2026 |
| Job Wizard Started | Job Post Wizard Started | Renamed for clarity — "Job Post Wizard" is more explicit | May 2026 |
| Job Wizard Step Completed | Per-step events (Job Post Wizard * Completed) | Umbrella event replaced by distinct per-step events for easier PostHog filtering | May 2026 |
| Voice Session Started | Sam Session Started | Now covers both voice AND text sessions via `input_mode` property | May 2026 |
| Voice Session Ended | Sam Session Ended | Now covers both modalities; carries over `duration_seconds` and `ended_by` | May 2026 |
| Voice Session Setup Failed | Sam Voice Session Setup Failed | Renamed to Sam namespace; voice-only (text has no hardware setup) | May 2026 |

---

## Property Dictionary

### Enum Properties


| Property                | Type | Scope                     | Allowed Values                                                                      | Used In                                                        |
| ----------------------- | ---- | ------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `entry_point`           | enum | event, person ($set_once) | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct`             | Page Viewed, Login Started                                     |
| `first_persona`         | enum | event, person ($set_once) | `hiring_manager`, `recruiter`, `job_seeker`                                         | Account Created                                                |
| `signup_context`        | enum | event, person ($set_once) | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct`             | Team Member Joined                                             |
| `current_persona`       | enum | event, person ($set)      | `hiring_manager`, `recruiter`, `job_seeker`                                         | Switch Persona Button Clicked, Persona Updated |
| `previous_persona`      | enum | event                     | `hiring_manager`, `recruiter`, `job_seeker`                                         | Persona Updated, Persona Update Failed                         |
| `target_persona`        | enum | event                     | `hiring_manager`, `recruiter`, `job_seeker`                                         | Persona Update Failed                                          |
| `activation_action`     | enum | event                     | `profile_created`, `interest_expressed`, `job_created`                              | Account Activated                                              |
| `input_method`          | enum | event                     | `resume_upload`, `linkedin_import`                                                  | Profile Created                                                |
| `section`               | enum | event                     | `summary`, `experience`, `skills`, `timeline`                                       | Profile Section Updated                                        |
| `share_channel`         | enum | event                     | `copy`, `email`, `linkedin`, `other`                                                | Custom Link Shared, Job Shared                                 |
| `session_type`          | enum | event                     | `first_time`, `returning`                                                           | Career Coach Session Started                                   |
| `input_mode`            | enum | event                     | `text`, `voice`                                                                     | Career Coach Session Started, Sam Session Started, Sam Session Ended |
| `message_type`          | enum | event                     | `text`, `voice`                                                                     | Career Coach Message Sent                                      |
| `topic`                 | enum | event                     | `profile_improvement`, `job_application`, `career_advice`                           | Career Coach Message Sent                                      |
| `visibility`            | enum | event                     | `public`, `private`                                                                 | Job Posting Published                                          |
| `from_status`           | enum | event                     | `draft`, `open`, `closed`, `archived`                                               | Job Status Changed                                             |
| `to_status`             | enum | event                     | `draft`, `open`, `closed`, `archived`                                               | Job Status Changed                                             |
| `invited_role_label`    | enum | event                     | `recruiter`, `team_member`                                                          | Team Member Invited                                            |
| `invite_method`         | enum | event                     | `email`, `link`                                                                     | Team Member Invited                                            |
| `role_label`            | enum | event                     | `hiring_manager`, `recruiter`, `team_member`                                        | Team Member Joined                                             |
| `decision`              | enum | event                     | `shortlisted`, `declined`, `needs_discussion`                                       | Review Decision Made                                           |
| `action` (job link)     | enum | event                     | `view_details`, `express_interest`                                                  | Job Link Engaged                                               |
| `action` (profile link) | enum | event                     | `view_full_profile`, `download_resume`                                              | Profile Link Engaged                                           |
| `action` (user_action)  | enum | event                     | `click`, `submit`, `toggle`                                                         | Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `step_name`             | enum | event                     | `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify` | Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `ended_by`              | enum | event                     | `user`, `sam`                                                                       | Sam Session Ended                                              |
| `intake_mode`           | enum | event                     | `voice`, `text`, `skipped`                                                          | Job Post Wizard Role Understanding Completed, Screening Configuration Saved, Job Posting Published |
| `identity_verification_mode` | enum | event, group (job)   | `require`, `off`                                                                    | Screening Configuration Saved, Job Posting Published, All events in job group (group property) |
| `job_status`            | enum | event, group (job)        | `draft`, `published`, `open`, `closed`, `archived`                                  | Job Posting Draft Created, Job Posting Published, All events in job group (group property) |
| `modification_type`     | enum | event                     | `added`, `edited`, `deleted`, `reordered`                                           | Requirement Modified, Question Modified                        |
| `share_source`          | enum | event                     | `success_screen`, `dashboard`, `overflow_menu`                                      | Share Button Clicked, Job Shared, Job Share Failed             |
| `error_category`        | enum | event                     | `network`, `permission`, `validation`, `server`, `timeout`, `hardware`, `connection` | All failure events (incl. Persona Update Failed, Sam Voice Session Setup Failed) |
| `tab_name`              | enum | event                     | `summary`, `role_requirements`, `recordings`, `notes`                               | Candidate Tab Viewed                                           |
| `edit_method`           | enum | event                     | `text`, `voice`                                                                     | Intro Script Updated                                           |
| `ai_recommendation`     | enum | event                     | `shortlisted`, `declined`                                                           | Candidate Viewed                                               |
| `auth_method`           | enum | event                     | `google`, `email`, `saml`                                                           | Account Created, Intro Completed                               |
| `job_visibility`        | enum | group (job)               | `public`, `private`                                                                 | All events in job group (group property)                       |

> `modification_type` note: `reordered` only applies to Question Modified —
> requirements do not support reordering.


### Array Properties


| Property             | Type  | Scope         | Description                                   | Used In                      |
| -------------------- | ----- | ------------- | --------------------------------------------- | ---------------------------- |
| `activated_personas` | array | person ($set) | All unique personas the user has tried; grows over time | All events (person property) |


### Boolean Properties


| Property                  | Type    | Scope       | Used In                                    |
| ------------------------- | ------- | ----------- | ------------------------------------------ |
| `is_job_specific`         | boolean | event       | Custom Link Created, Custom Link Shared    |
| `has_custom_link`         | boolean | event       | Interest Expressed                         |
| `has_resume`              | boolean | event       | Interest Expressed                         |
| `is_authenticated`        | boolean | event       | Job Link Viewed, Profile Link Viewed       |
| `verification_required`   | boolean | event       | Auth Login Succeeded                       |
| `is_verified`             | boolean | event, group (job) | Job Posting Verified, Job Posting Published, All events in job group (group property) |
| `has_intro_video`         | boolean | group (job) | All jobs with intro video (group property) |


### Numeric Properties


| Property                 | Type   | Scope | Description                                    | Used In                                  |
| ------------------------ | ------ | ----- | ---------------------------------------------- | ---------------------------------------- |
| `time_to_review_seconds` | number | event | Seconds between interest submission and review | Interest Reviewed                        |
| `days_since_signup`      | number | event | Days between account creation and activation   | Account Activated                        |
| `step_number`            | number | event | Wizard step (1–5)                              | Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `duration_seconds`       | number | event | Duration in seconds                            | Sam Session Ended, Intro Video Created   |
| `takes_count`            | number | event | Number of recording takes before save          | Intro Video Created                      |
| `questions_count`        | number | event, group (job) | Total screening questions count           | Screening Configuration Saved, Job Posting Published, All events in job group (group property) |
| `ai_generated_questions_count` | number | event | AI-generated screening questions count   | Screening Configuration Saved            |
| `manual_questions_count` | number | event | Manually added screening questions count       | Screening Configuration Saved            |
| `question_number`        | number | event | Question position in order                     | Candidate Recording Played               |
| `status_code`            | number | event | HTTP status code from auth backend             | Auth Login Failed, Auth Session Restore Failed, Auth Refresh Failed, Auth Dev Login Failed, Auth Email Verify Code Send Failed, Auth Email Verify Failed, Auth Phone Submit Failed |
| `cooldown_seconds`       | number | event | Seconds before resend is allowed               | Auth Email Verify Code Sent              |
| `attempts_remaining`     | number | event | Remaining verification attempts                | Auth Email Verify Failed                 |
| `phone_length`           | number | event | Phone number length (digits)                   | Auth Phone Submitted                     |


### String Properties


| Property              | Type     | Scope              | Description                                                                | Used In                                          |
| --------------------- | -------- | ------------------ | -------------------------------------------------------------------------- | ------------------------------------------------ |
| `action_value`        | string   | event              | Specific UI element interacted with (snake_case)                           | Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `current_page_context`| string   | event              | Page where event occurred (snake_case, `/` hierarchy)                      | Page Viewed, Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `previous_page_context`| string  | event              | Previous page before current one                                           | Page Viewed, Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `component`           | string   | event              | UI container where action occurred                                         | Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `entity_type`         | string   | event              | Business object being acted on                                             | Login Started, Account Created, Intro Completed, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Post Wizard Role Understanding Completed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed |
| `link_name`           | string   | event              | User-provided name for the custom link                                     | Custom Link Created                              |
| `target_job_title`    | string   | event              | Job title the link targets (optional, only when `is_job_specific` is true) | Custom Link Created                              |
| `target_company`      | string   | event              | Company the link targets (optional, only when `is_job_specific` is true)   | Custom Link Created                              |
| `reason`              | string   | event              | User-provided reason for withdrawal                                        | Interest Withdrawn                               |
| `error_reason`        | string   | event              | System error description                                                   | All failure events                               |
| `auth_mode`           | string   | event              | Auth mode (e.g., `msal`, `posthog`, `dev`)                                 | Login Cancelled, Auth Login Succeeded, Auth Login Failed, Auth Session Restore Succeeded, Auth Logout Completed, Auth Dev Login Started, Auth Dev Login Succeeded, Auth Dev Login Failed |
| `error_detail`        | string   | event              | Detailed error message                                                     | Auth Login Failed, Auth Dev Login Failed, Auth Email Verify Code Send Failed, Auth Email Verify Failed, Auth Phone Submit Failed |
| `error_code`          | string   | event              | Error code (e.g., `user_cancelled`)                                        | Login Cancelled                                  |
| `source`              | string   | event              | Source that triggered the refresh                                          | Auth Refresh Failed                              |
| `country_code`        | string   | event              | Phone country code (e.g., `+1`)                                            | Auth Phone Submitted                             |
| `first_referrer`      | string   | person ($set_once) | HTTP referrer at first visit                                               | Page Viewed (person property)                    |
| `first_landing_url`   | string   | person ($set_once) | Full landing URL at first visit                                            | Page Viewed (person property)                    |
| `account_created_at`  | ISO date | person ($set_once) | Account creation timestamp                                                 | Account Created (person property)                |
| `start_source`        | string   | event              | Entry point that initiated the wizard                                      | Job Post Wizard Started                          |
| `company_name`        | string   | event              | Company name extracted from JD (can be null)                               | Job Posting Draft Created, Screening Configuration Saved, Job Posting Published |
| `location`            | string   | event              | Job location extracted from JD (can be null)                               | Job Posting Draft Created, Screening Configuration Saved, Job Posting Published |
| `job_title`           | string   | event, group (job) | Job posting title                                                          | Job Posting Draft Created, Job Posting Verified, Screening Configuration Saved, Job Posting Published, All events in job group (group property) |
| `created_at`          | ISO date | group (job)        | Job creation timestamp                                                     | All events in job group (group property)         |


### UUID Properties


| Property                 | Type | Scope                     | Description                                  | Used In                                                                                                                 |
| ------------------------ | ---- | ------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `job_id`                 | UUID | event                     | Job identifier                               | All job-related events (standard property)                                                                              |
| `shared_by_user_id`      | UUID | event                     | User who shared the link                     | Job Shared                                                                                                              |
| `referrer_user_id`       | UUID | event                     | User who referred the visitor                | Job Link Viewed, Job Link Engaged                                                                                       |
| `referrer_job_id`        | UUID | event                     | Job associated with the referral             | Job Link Viewed, Job Link Engaged                                                                                       |
| `profile_user_id`        | UUID | event                     | Prospect whose profile is being viewed       | Profile Link Viewed, Profile Link Engaged                                                                               |
| `custom_link_id`         | UUID | event                     | Which custom link was used                   | Profile Link Viewed, Profile Link Engaged                                                                               |
| `referred_by`            | UUID | event, person ($set_once) | User who referred this user at signup        | Account Created                                                                                                         |
| `hiring_manager_user_id` | UUID | group (job)               | Hiring manager for the job                   | All events in job group (group property)                                                                                |
| `created_by_user_id`     | UUID | group (job)               | User who created the job                     | All events in job group (group property)                                                                                |
| `candidate_id`           | UUID | event                     | Candidate being reviewed                     | Candidate Viewed, Candidate Tab Viewed, Candidate Recording Played                                                      |
