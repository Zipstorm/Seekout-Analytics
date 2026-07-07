---
confluence:
  page_id: "1748861000"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Events Tracker

**Product:** Helix (SeekOut.ai)
**Analytics Platform:** PostHog
**Last Updated:** July 2026

For naming conventions, PostHog setup, and sample code, see [Helix Analytics Events Schema](./event-schema.md).
For dashboards and funnel mappings, see [Helix Analytics Dashboards & Funnels](./dashboards.md).
For login & onboarding event specs, see [event-definitions/login-onboarding/](../event-definitions/login-onboarding/).

---

## Event Catalog

### Login & Onboarding Events

Events for the login and new user onboarding flow. Full specs in [event-definitions/login-onboarding/](../event-definitions/login-onboarding/).


| Event             | Area       | Type        | Trigger                                                        | Source   | Properties                                                                                                                              | Group | Property Updates                                                              | Status |
| ----------------- | ---------- | ----------- | -------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------- | ------ |
| Page Viewed       | Navigation | View   | User lands on a meaningful page                                | Frontend | `current_page_context`, `previous_page_context`, `entry_point` (login page only), `start_source` (interview landing page only)          | --    | `$set_once: entry_point, first_referrer, first_landing_url` (login page only) | Live   |
| Login Started Button Clicked | Account | Interaction | User clicks an auth CTA on signup/signin page | Frontend | `action`, `action_value`, `auth_method`, `current_page_context`, `previous_page_context`, `entry_point`, `entity_type`, `component` | -- | -- | Live |
| Account Create Succeeded | Account | Success | User clicks "Continue as [Persona]" and server confirms role | Backend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entry_point`, `entity_type`, `component`, `current_persona`, `auth_method`, `referred_by` | -- | `$set: current_persona, activated_personas`; `$set_once: first_persona, account_created_at, referred_by` | Live |
| Onboarding Intro Complete Button Clicked | Account | Interaction | User clicks "Let's go" on onboarding intro page | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Live |
| Onboarding Persona Card Clicked | Account | Interaction | User clicks persona card on role selection page | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Dev |
| Onboarding Complete Succeeded | Account | Success | User lands on first post-onboarding page | Frontend | `current_page_context`, `previous_page_context`, `current_persona`, `auth_method`, `onboarding_duration_seconds`, `had_email_verification`, `has_resume`, `has_photo`, `has_handle`, `links_count` | -- | `$set_once: first_persona` | Dev |


### Auth Lifecycle Events (existing — to be replaced)

These events are still firing from `authStore.ts` and will be replaced when the returning user flow is implemented.


| Event                          | Area    | Type | Trigger                                        | Source   | Properties                                     | Group | Property Updates | Status       |
| ------------------------------ | ------- | ---- | ---------------------------------------------- | -------- | ---------------------------------------------- | ----- | ---------------- | ------------ |
| Auth Login Succeeded           | Account | Success   | Backend confirms successful auth               | Frontend | `auth_mode`, `verification_required`           | --    | `$set: email, name, role, org_id, current_persona` (via `identifyUser()`) | Live (legacy) |
| Auth Login Rejected            | Account | Rejected   | Backend returns auth error                     | Frontend | `auth_mode`, `status_code`, `error_detail`     | --    | --               | Live (legacy) |
| Auth Session Restore Succeeded | Account | Success   | Session restored from refresh token            | Frontend | `auth_mode`                                    | --    | `$set: email, name, role, org_id, current_persona` (via `identifyUser()`) | Live (legacy) |
| Auth Session Restore Errored   | Account | Error      | Session restore failed                         | Frontend | `status_code`, `error_detail`                  | --    | --               | Live (legacy) |
| Auth Refresh Errored           | Account | Error      | Token refresh failed                           | Frontend | `source`, `status_code`, `error_detail`        | --    | --               | Live (legacy) |
| Auth Logout Succeeded          | Account | Success   | User logs out                                  | Frontend | `auth_mode`                                    | --    | --               | Live (legacy) |


### Auth Dev Events (dev-only)


| Event                    | Area    | Type | Trigger                  | Source   | Properties               | Group | Property Updates | Status    |
| ------------------------ | ------- | ---- | ------------------------ | -------- | ------------------------ | ----- | ---------------- | --------- |
| Auth Dev Login Started   | Account | Started   | Dev login initiated      | Frontend | `auth_mode`              | --    | --               | Dev only  |
| Auth Dev Login Succeeded | Account | Success   | Dev login succeeded      | Frontend | `auth_mode`              | --    | --               | Dev only  |
| Auth Dev Login Failed    | Account | Rejected   | Dev login failed         | Frontend | `auth_mode`, `status_code`, `error_detail` | --    | --               | Dev only  |


### Email Verification Events


| Event                              | Area    | Type | Trigger                                | Source   | Properties                          | Group | Property Updates | Status |
| ---------------------------------- | ------- | ---- | -------------------------------------- | -------- | ----------------------------------- | ----- | ---------------- | ------ |
| Auth Email Verify Code Send Succeeded | Account | Success | Verification code sent to user's email | Frontend | `cooldown_seconds`                  | --    | --               | Live   |
| Auth Email Verify Code Send Errored  | Account | Error   | Failed to send verification code       | Frontend | `status_code`, `error_detail`       | --    | --               | Live   |
| Auth Email Verify Resend Clicked   | Account | Interaction   | User clicks resend verification link   | Frontend | --                                  | --    | --               | Live   |
| Auth Email Verify Succeeded        | Account | Success   | Email verification succeeds            | Frontend | --                                  | --    | --               | Live   |
| Auth Email Verify Rejected         | Account | Rejected  | Email verification fails               | Frontend | `status_code`, `error_detail`, `attempts_remaining` | --    | --               | Live   |



### Account & Persona Events


| Event             | Area    | Type    | Trigger                                                   | Source   | Properties                                                                                                    | Group | Property Updates                                                            | Status      |
| ----------------- | ------- | ------- | --------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------- | ----------- |
| Account Activated              | Account | Success      | First meaningful action completed                                    | Backend  | `activation_action`, `days_since_signup`                                                           | --    | --                                                                          | Not Started |
| Switch Persona Button Clicked  | Account | Interaction  | User clicks the ⇄ chevron next to current persona in sidebar        | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | -- | --                                                                          | Not Started |
| Persona Updated                | Account | Success | Backend confirms persona switch after user selects a different persona | Backend  | `previous_persona`, `current_persona`, `activated_personas`                 | --    | `$set: current_persona, activated_personas`                                 | Not Started |
| Persona Update Failed          | Account | Rejected | Backend returns error on persona switch attempt                       | Backend  | `previous_persona`, `target_persona`, `error_reason`†, `error_category`     | --    | --                                                                          | Not Started |

† `error_reason` on Persona Update Failed is truncated to 256 chars server-side (`str(e)[:256]`). Other failure events send the full error string.


### Anonymous User Events

Events fired by unauthenticated visitors interacting with shared links before signup.


| Event                | Area      | Type | Trigger                                        | Source   | Properties                                                                             | Group | Property Updates | Status      |
| -------------------- | --------- | ---- | ---------------------------------------------- | -------- | -------------------------------------------------------------------------------------- | ----- | ---------------- | ----------- |
| Job Link Viewed      | Anonymous | View   | Visitor opens a shared job link                | Either   | `referrer_user_id`, `referrer_job_id`, `is_authenticated`                              | --    | --               | Not Started |
| Job Link Engaged     | Anonymous | Interaction   | Visitor takes action on a shared job page      | Frontend | `referrer_user_id`, `referrer_job_id`, `action`                                        | --    | --               | Not Started |
| Profile Link Viewed  | Anonymous | View   | Visitor opens a prospect's shared profile link | Either   | `profile_user_id`, `custom_link_id`, `is_authenticated`                                | --    | --               | Not Started |
| Profile Link Engaged | Anonymous | Interaction   | Visitor takes action on a shared profile page  | Frontend | `profile_user_id`, `custom_link_id`, `action`                                          | --    | --               | Not Started |


### Prospect Persona Events


| Event                           | Area     | Type    | Trigger                                     | Source   | Properties                                                                                             | Group | Property Updates | Status      |
| ------------------------------- | -------- | ------- | ------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------ | ----- | ---------------- | ----------- |
| Candidate Resume Upload Button Clicked | Prospect | Interaction  | User clicks resume upload area              | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `mode`  | --    | --               | Live        |
| Candidate Resume Upload Succeeded | Prospect | Success      | Backend confirms resume stored              | Backend  | `resume_id`, `resume_name`, `resume_file_type`, `resume_size_bytes`, `page_count`, `mode`                      | --    | --               | Live        |
| Candidate Resume Upload Rejected | Prospect | Rejected     | Client-side validation rejects resume       | Frontend | `resume_file_type`, `resume_size_bytes`, `error_reason`, `error_category`, `mode`                              | --    | --               | Live        |
| Candidate Resume Upload Errored | Prospect | Error        | Server extraction fails                     | Backend  | `resume_file_type`, `resume_size_bytes`, `error_reason`, `error_category`, `mode`                              | --    | --               | Live        |
| Candidate Resume Remove Button Clicked | Prospect | Interaction  | User clicks Remove on resume                | Frontend | `action`, `action_value`, `resume_id`, `resume_file_type`, `current_page_context`, `previous_page_context`, `component`, `entity_type`, `mode` | --    | --               | Live        |
| LinkedIn Export Learn How Link Clicked | Prospect | Interaction | User clicks "Learn how" link           | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `mode`  | --    | --               | Live        |
| Add Profile Photo Button Clicked | Prospect | Interaction | User opens photo action menu                | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `mode`  | --    | --               | Live        |
| Profile Photo Add Succeeded     | Prospect | Success      | Photo saved successfully                    | Frontend | `upload_method`, `file_type`, `file_size_bytes`, `current_page_context`, `previous_page_context`, `entity_type`, `mode` | --    | --               | Live        |
| Profile Photo Upload Failed     | Prospect | Rejected     | Photo rejected (size/format)                | Frontend | `upload_method`, `file_size_bytes`, `error_reason`, `error_category`, `current_page_context`, `previous_page_context`, `entity_type`, `mode` | --    | --               | Live        |
| Build Profile Button Clicked    | Prospect | Interaction  | User clicks "Build my AI profile"           | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `mode`  | --    | --               | Live        |
| Candidate Profile Create Succeeded | Prospect | Success   | Backend generates portfolio                 | Backend  | `portfolio_id`, `resume_id`, `input_method`, `has_resume`, `has_photo`, `links_count`, `link_types`, `has_handle`, `resume_page_count`, `mode` | --    | --               | Live        |
| Candidate Profile Create Errored | Prospect | Error       | Backend portfolio generation fails          | Backend  | `resume_id`, `error_reason`, `error_category`, `mode`                                                          | --    | --               | Live        |
| Profile Section Updated         | Prospect | Success      | User edits a profile section                | Frontend | `section`                                                                                              | --    | --               | Not Started |
| Candidate Profile Custom Link Add Succeeded | Prospect | Success      | User creates a named shareable link         | Backend  | `current_persona`, `link_type`, `link_name`, `is_job_specific` (boolean), `target_job_title` (optional), `target_company` (optional), `mode` | --    | --               | Live        |
| Custom Link Shared              | Prospect | Success      | User shares a custom link                   | Frontend | `share_channel`, `is_job_specific`                                                                     | --    | --               | Not Started |
| Express Interest Button Clicked | Prospect | Interaction  | Prospect clicks Express Interest on a job   | Frontend | `job_id`                                                                                               | --    | --               | Not Started |
| Interest Expressed              | Prospect | Success | Server confirms interest recorded           | Backend  | `job_id`, `has_custom_link`, `has_resume`                                                              | --    | --               | Not Started |
| Interest Expression Failed      | Prospect | Rejected | Server returns error on interest submission | Backend  | `job_id`, `error_reason`, `error_category`                                                             | --    | --               | Not Started |
| Interest Withdrawn              | Prospect | Success      | Prospect withdraws interest                 | Backend  | `job_id`, `reason`                                                                                     | --    | --               | Not Started |
| Career Coach Session Started    | Prospect | Started      | User begins AI career coach interaction     | Frontend | `session_type`, `input_mode`                                                                           | --    | --               | Not Started |
| Career Coach Message Sent       | Prospect | Success      | User sends message to career coach          | Frontend | `message_type`, `topic`                                                                                | --    | --               | Not Started |


### Job Seeker Profile & Interview Events


| Event | Area | Type | Trigger | Source | Properties | Group | Property Updates | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Handle Claim Succeeded | Prospect | Success | Handle availability check returns available | Frontend | `handle_length`, `current_page_context`, `source`, `current_persona` | -- | -- | Dev |
| Handle Claim Rejected | Prospect | Rejected | Handle availability check returns unavailable | Frontend | `reason`, `current_page_context`, `source`, `current_persona` | -- | -- | Dev |
| Candidate Previous Resume Select Button Clicked | Prospect | Interaction | User clicks Select on a previous resume | Frontend | `action`, `action_value`, `component`, `resume_id`, `resume_file_type`, `current_page_context`, `previous_page_context`, `entity_type` | -- | -- | Live |
| Candidate Custom Link Delete Button Clicked | Prospect | Interaction | User clicks trash icon on an added link | Frontend | `action`, `action_value`, `component`, `link_type`, `current_page_context`, `previous_page_context`, `entity_type`, `mode` | -- | -- | Live |
| Candidate Custom Link Delete Succeeded | Prospect | Success | Link deletion confirmed | Frontend | `link_type`, `mode` | -- | -- | Live |
| Candidate Custom Link Delete Errored | Prospect | Error | Link deletion fails | Frontend | `link_type`, `error_reason`, `mode` | -- | -- | Live |
| Candidate Profile Overview Load Succeeded | Prospect | Success | Overview tab finishes loading | Frontend | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video`, `profile_completeness_rate`, `current_page_context`, `previous_page_context` | -- | -- | Live |
| Candidate Profile Tab Switched | Prospect | Interaction | User clicks a tab | Frontend | `action`, `action_value`, `portfolio_id`, `tab_name`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Resume Download Succeeded | Prospect | Success | User clicks Download on Resume tab | Frontend | `action`, `action_value`, `portfolio_id`, `resume_id`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Publish Button Clicked | Prospect | Interaction | User clicks Publish in editor header | Frontend | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Publish Succeeded | Prospect | Success | Backend confirms publish | Backend | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video` | -- | -- | Live |
| Candidate Portfolio Publish Errored | Prospect | Error | Backend publish error | Backend | `portfolio_id`, `error_reason`, `error_category` | -- | -- | Live |
| Candidate Portfolio Unpublish Button Clicked | Prospect | Interaction | User clicks Unpublish in editor header | Frontend | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Unpublish Succeeded | Prospect | Success | Backend confirms unpublish | Backend | `portfolio_id`, `is_published` | -- | -- | Live |
| Change Profile Photo Button Clicked | Prospect | Interaction | User clicks change photo when photo exists | Frontend | `action_value`, `portfolio_id` | -- | -- | Live |
| Candidate Profile Photo Remove Button Clicked | Prospect | Interaction | User clicks remove on profile photo | Frontend | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type`, `mode` | -- | -- | Live |
| Candidate Profile Photo Remove Succeeded | Prospect | Success | Photo removal confirmed | Frontend | `portfolio_id`, `mode` | -- | -- | Live |
| Candidate Profile Photo Remove Errored | Prospect | Error | Photo removal fails | Frontend | `portfolio_id`, `error_reason`, `mode` | -- | -- | Live |
| Candidate Portfolio Create Button Clicked | Prospect | Interaction | User clicks + Create on dashboard | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Rename Button Clicked | Prospect | Interaction | User clicks Rename in overflow menu | Frontend | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Rename Succeeded | Prospect | Success | Backend confirms rename (name changed) | Backend | `portfolio_id`, `new_name_length`, `previous_name_length` | -- | -- | Live |
| Candidate Portfolio Delete Button Clicked | Prospect | Interaction | User clicks Delete in overflow menu | Frontend | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- | Live |
| Candidate Portfolio Delete Succeeded | Prospect | Success | Backend confirms delete | Backend | `portfolio_id`, `was_published` | -- | -- | Live |
| Get Started Interview Button Clicked | Prospect | Interaction | User clicks Get Started | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Info Next Button Clicked | Prospect | Interaction | User clicks Next on info form | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `has_first_name`, `has_last_name`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| What To Expect Link Clicked | Prospect | Interaction | User clicks What to expect expander | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Resume Next Button Clicked | Prospect | Interaction | User clicks Next on resume step | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `has_resume`, `agreement_acknowledged`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Resume Upload Succeeded | Prospect | Success | Resume uploaded in interview context | Frontend | `interview_id`, `job_id` | job | -- | Live |
| Candidate Interview Resume Upload Errored | Prospect | Error | Resume upload fails in interview context | Frontend | `interview_id`, `job_id`, `error_reason` | job | -- | Live |
| Open Identity Check Link Clicked | Prospect | Interaction | User clicks Open Identity Check | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Refresh Status Button Clicked | Prospect | Interaction | User clicks Refresh Status | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Identity Verification Succeeded | Prospect | Success | Backend confirms identity verified (decision_category = pass) | Backend | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source`, `time_to_verify_seconds` | job | -- | Live |
| Candidate Interview Identity Verification Errored | Prospect | Error | Backend identity check inconclusive/unavailable | Backend | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source`, `error_reason`, `error_category` | job | -- | Live |
| Candidate Interview Identity Verification Rejected | Prospect | Rejected | Backend identity check fails (decision_category = fail) | Backend | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source` | job | -- | Live |
| Candidate Interview Identity Verification Auto Redirect Succeeded | Prospect | Success | Auto-redirect after fresh verification succeeds | Frontend | `interview_id`, `job_id` | job | -- | Live |
| Candidate Interview Identity Verification Auto Redirect Errored | Prospect | Error | Auto-redirect fails | Frontend | `interview_id`, `job_id` | job | -- | Live |
| Candidate Interview Identity Verification Auto Redirect Rejected | Prospect | Rejected | Auto-redirect blocked (canContinue=false) | Frontend | `interview_id`, `job_id` | job | -- | Live |
| Candidate Interview Identity Verification Continue Button Clicked | Prospect | Interaction | User clicks Continue after verification | Frontend | `action_value`, `interview_id`, `job_id` | job | -- | Live |
| Candidate Interview Privacy Email Link Clicked | Prospect | Interaction | User clicks privacy@seekout.ai link | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Persona Privacy Policy Link Clicked | Prospect | Interaction | User clicks Persona's privacy policy link | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Screening Response Next Button Clicked | Prospect | Interaction | User clicks Next on screening questions (first pass) | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Screening Response Submit Succeeded | Prospect | Success | Screening responses saved after API confirms | Frontend | `interview_id`, `job_id`, `questions_count`, `yes_count`, `no_count`, `optional_context_provided_count`, `required_explanation_count` | job | -- | Live |
| Candidate Interview Screening Response Save And Review Button Clicked | Prospect | Interaction | User clicks Save & Review on screening edit-from-review | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Allow Device Access Button Clicked | Prospect | Interaction | User clicks Allow Access for camera/mic | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Device Access Grant Succeeded | Prospect | Success | Browser grants camera/mic | Frontend | `interview_id`, `job_id`, `camera_granted`, `mic_granted` | job | -- | Live |
| Device Access Rejected | Prospect | Rejected | Browser denies camera/mic | Frontend | `interview_id`, `job_id`, `camera_granted`, `mic_granted`, `error_reason` | job | -- | Live |
| Candidate Interview Start Button Clicked | Prospect | Interaction | User clicks Start Interview | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Started | Prospect | Started | Frontend: first question loads; Backend: posthog.alias() at startInterview() | Frontend + Backend | `interview_id`, `job_id`, `questions_count`, `input_mode`, `has_resume`, `identity_verified`, `is_test_run`, `source` | job | -- | Live |
| Candidate Interview Question Answer Succeeded | Prospect | Success | Question answered (save & continue) | Backend | `interview_id`, `job_id`, `question_number`, `question_status`, `input_mode`, `response_duration_seconds`, `ai_conversation_completed` | job | -- | Live |
| Candidate Interview Question Restart Button Clicked | Prospect | Interaction | User clicks Restart on a question | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `question_number`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Question Restart Succeeded | Prospect | Success | Question restart confirmed | Backend | `interview_id`, `job_id`, `question_number` | job | -- | Live |
| Candidate Interview Question Restart Errored | Prospect | Error | Question restart fails | Backend | `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category` | job | -- | Live |
| Candidate Interview Question Skip Button Clicked | Prospect | Interaction | User clicks Skip on a question | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `question_number`, `current_page_context`, `component`, `entity_type` | job | -- | Live |
| Candidate Interview Question Skip Succeeded | Prospect | Success | Skip confirmed | Backend | `interview_id`, `job_id`, `question_number` | job | -- | Live |
| Candidate Interview Question Skip Errored | Prospect | Error | Skip fails | Backend | `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category` | job | -- | Live |
| Candidate Interview Question Skip Rejected | Prospect | Rejected | User clicks Go back and answer | Frontend | `action_value`, `interview_id`, `job_id`, `question_number` | job | -- | Live |
| Candidate Interview Screening Response Edit Button Clicked | Prospect | Interaction | User clicks Edit on a screening answer | Frontend | `action`, `action_value`, `interview_id`, `job_id`, `entity_type` | job | -- | Live |
| Candidate Interview Review Answer Button Clicked | Prospect | Interaction | User clicks Answer Question for skipped/unanswered question | Frontend | `action_value`, `interview_id`, `job_id`, `question_number`, `entity_type` | job | -- | Live |
| Candidate Interview Retake Question Button Clicked | Prospect | Interaction | User clicks retake on an answered question | Frontend | `action_value`, `interview_id`, `job_id`, `question_number` | job | -- | Live |
| Candidate Interview Review Answer Expand Clicked | Prospect | Interaction | User expands an answer card on review page | Frontend | `interview_id`, `job_id`, `question_number` | job | -- | Live |
| Candidate Interview Answers Submit Succeeded | Prospect | Success | Last question saved, recording phase complete | Frontend | `interview_id`, `job_id`, `questions_count` | job | -- | Live |
| Candidate Interview Answer Retake Succeeded | Prospect | Success | Retake from review completes | Frontend | `interview_id`, `job_id`, `question_number`, `mode`, `outcome`, `previous_state`, `ai_conversation_completed` | job | -- | Live |
| Candidate Interview Screening Response Edit Succeeded | Prospect | Success | Screening edit from review saved | Frontend | `interview_id`, `job_id`, `responses_changed_count`, `context_added_count`, `context_removed_count` | job | -- | Live |
| Candidate Interview Submit Succeeded | Prospect | Success | Backend confirms interview submitted | Backend | `interview_id`, `job_id`, `interview_result_id`, `questions_count`, `screening_questions_count`, `has_resume`, `identity_verified`, `input_mode`, `total_duration_seconds`, `is_test_run`, `source`, `org_id` | job | -- | Live |
| Candidate Interview Submit Rejected | Prospect | Rejected | Backend rejects interview submission | Backend | `interview_id`, `job_id`, `error_reason`, `error_category` | job | -- | Live |


### Hiring Persona Events

All hiring persona events include `job_id`. Backend events include `current_persona` as an explicit event property; frontend events inherit it from the person property (`$set`). See [Schema](./event-schema.md) for standard event properties.


| Event                       | Area   | Type    | Trigger                                                   | Source   | Properties                                                                                                                           | Group | Property Updates                                                                            | Status      |
| --------------------------- | ------ | ------- | --------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------------- | ----------- |
| Create Job Button Clicked   | Hiring | Interaction  | User clicks Create Job button on home page                | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | --    | --                                                                                          | Live |
| Job Posting Draft Created   | Hiring | Success | Server confirms job draft created (step 1 "Next")         | Backend  | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility` | `job` | `group(job): job_title, job_status, hiring_manager_user_id, created_by_user_id, created_at` | Live |
| Job Creation Failed         | Hiring | Rejected | Server returns error on job creation                      | Backend  | `current_persona`, `error_reason`                                                                                        | --    | --                                                                                          | Live |
| Job Post Wizard Started     | Hiring | Started | Wizard page mounts with router state isNewWizard=true     | Frontend | `start_source`, `current_page_context`                                                                                   | --    | --                                                                                          | Live |
| Job Post Wizard Job Details Completed | Hiring | Success | User clicks "Next" on Job Details step                  | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Job Description Evaluated   | Hiring | Success      | AI evaluation of pasted job description completes successfully | Frontend | `company_name`, `current_page_context`, `employment_type`, `entity_type`, `has_benefits`, `has_compensation`, `input_length`, `job_id`, `job_location`, `job_title`, `previous_page_context`, `requirements_count`, `responsibilities_count`, `seniority_level`, `skills_count`, `step_name`, `step_number`, `work_type` | `job` | -- | Live |
| Job Description Evaluation Failed | Hiring | Rejected | AI evaluation fails or returns empty result               | Frontend | `current_page_context`, `entity_type`, `error_reason`, `input_length`, `job_id`, `previous_page_context`, `step_name`, `step_number` | `job` | -- | Live |
| Job Description Details Toggled | Hiring | Interaction   | User clicks "View full details" or "View less" on the evaluation card | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `expanded`, `job_id`, `previous_page_context`, `step_name`, `step_number` | `job` | -- | Live |
| Job Description Field Edited | Hiring | Success     | User edits an AI-extracted field and blurs                | Frontend | `component`, `current_page_context`, `entity_type`, `field_name`, `job_id`, `new_value`, `previous_page_context`, `step_name`, `step_number` | `job` | -- | Live |
| Job Post Wizard Intake Mode Selected | Hiring | Success | User clicks "Next" or "Skip" on Understanding the Role step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `intake_mode` | `job` | --                                                                                 | Live |
| Sam Session Started         | Hiring | Started      | Sam session successfully starts after user selects voice or text | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `session_id` | `job` | --                                                                             | Live |
| Sam Session Setup Failed    | Hiring | Rejected | Voice session setup fails before Sam session starts       | Frontend | `current_page_context`, `entity_type`, `error_category`, `error_reason`, `input_mode`, `job_id`, `mic_enabled`, `previous_page_context`, `session_id` | `job` | -- | Live |
| Sam Session Ended           | Hiring | Success      | User clicks "End Session" or intake auto-completes        | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `duration_seconds`, `ended_by`, `session_id` | `job` | --                                                                                          | Live |
| Job Post Wizard Role Requirements Completed | Hiring | Success | User clicks "Next" on Role Requirements step          | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Requirement Add Button Clicked | Hiring | Interaction   | User clicks "+ Add" on Role Requirements step             | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Role Requirement Deleted    | Hiring | Success      | User deletes a role requirement question                  | Frontend | `action`, `action_value`, `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_source`, `question_text`, `question_type`, `step_name`, `step_number` | `job` | -- | Live |
| Role Requirement Edited     | Hiring | Success      | User edits role requirement question text and saves       | Frontend | `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `new_text`, `original_text`, `previous_page_context`, `question_source`, `question_type`, `step_name`, `step_number` | `job` | -- | Live |
| Role Requirement Added      | Hiring | Success      | User saves a new role requirement question                | Frontend | `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_text`, `question_type`, `step_name`, `step_number` | `job` | -- | Live |
| Job Post Wizard Interview Questions Completed | Hiring | Success | User clicks "Next" on Interview Questions step      | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `identity_verification_mode` | `job` | --                                                                       | Live |
| Question Add Button Clicked | Hiring | Interaction      | User clicks "+ Add" on Interview Questions step           | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Screening Question Deleted  | Hiring | Success      | User deletes a screening question                         | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_number`, `question_source`, `question_text`, `step_name`, `step_number` | `job` | -- | Live |
| Screening Question Edited   | Hiring | Success      | User edits screening question text and saves              | Frontend | `ai_refined`, `component`, `current_page_context`, `entity_type`, `job_id`, `new_text`, `original_text`, `previous_page_context`, `question_number`, `question_source`, `step_name`, `step_number` | `job` | -- | Live |
| Screening Question Added    | Hiring | Success      | User saves a new screening question                       | Frontend | `ai_created`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_text`, `step_name`, `step_number` | `job` | -- | Live |
| Screening Configuration Saved | Hiring | Success    | Backend saves screening config                            | Backend  | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | --                             | Live |
| Job Verification Code Send Button Clicked | Hiring | Interaction | User clicks "Send code" on Verify step              | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Job Post Wizard Verification Completed | Hiring | Success | Email verified successfully on Verify step             | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Job Post Wizard Verification Skipped | Hiring | Success | User clicks "Maybe later" on Verify step                | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Job Post Wizard Back Button Clicked | Hiring | Interaction | User clicks "Back" on any wizard step (2–5)             | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | --                                                                                          | Live |
| Job Posting Verified        | Hiring | Success | Backend verifies 6-digit code successfully                | Backend  | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | --                             | Live |
| Job Posting Published       | Hiring | Success      | Job goes from draft to published                          | Backend  | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): job_status, job_visibility` | Live |
| Success Page Share Button Clicked | Hiring | Interaction | User clicks "Share" on the job creation success page     | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- | Live |
| Job Share Message AI Refined | Hiring | Success     | User refines share message with AI                        | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `refined_message_length` | `job` | -- | Live |
| Job Share Message Copied    | Hiring | Success      | User copies the generated share message                   | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `message_length`, `previous_page_context` | `job` | -- | Live |
| Job Share Channel Clicked   | Hiring | Interaction      | User clicks LinkedIn, X, or email in the share modal      | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `share_channel` | `job` | -- | Live |
| Invite Teammates Button Clicked | Hiring | Interaction   | User clicks "Invite teammates" on the job creation success page | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- | Live |
| Team Member Invite Sent     | Hiring | Interaction      | User sends an invite from the success-page invite modal   | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `invite_count`, `invite_role`, `job_id`, `previous_page_context` | `job` | -- | Live |
| Job Posting Page Link Clicked | Hiring | Interaction    | User clicks "Go to job posting page" on the success page  | Frontend | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- | Live |
| Archive Job Button Clicked  | Hiring | Interaction  | User clicks "Archive" in job card overflow menu           | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `current_persona` | --    | --                                                                                          | Live |
| Share Button Clicked        | Hiring | Interaction  | User clicks Share button on a job                         | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `component`, `context_object_type`, `context_object_id`, `current_persona` | `job` | --                                                                                    | Live |
| Job Shared                  | Hiring | Success | Server confirms job link shared                           | Backend  | `job_id`, `share_channel`, `shared_by_user_id`, `share_source`, `current_persona`                                        | `job` | --                                                                                          | Live |
| Job Share Failed            | Hiring | Rejected | Server returns error on share attempt                     | Backend  | `job_id`, `error_reason`, `error_category`, `share_source`, `current_persona`                                            | `job` | --                                                                                          | Live |
| Job Status Changed          | Hiring | Success      | Job status updated                                        | Backend  | `job_id`, `from_status`, `to_status`, `current_persona`                                                                  | `job` | `group(job): job_status`                                                                    | Live |
| Invite Button Clicked       | Hiring | Interaction  | User clicks Invite button on a job                        | Frontend | `job_id`                                                                                                                 | `job` | --                                                                                          | Not Started |
| Team Member Invited         | Hiring | Interaction | Server confirms invite sent                               | Backend  | `job_id`, `invited_role_label`, `invite_method`, `current_persona`                                                       | `job` | --                                                                                          | Live |
| Team Member Invite Failed   | Hiring | Rejected | Server returns error on invite attempt                    | Backend  | `job_id`, `error_reason`, `error_category`, `current_persona`                                                            | `job` | --                                                                                          | Live |
| Team Member Joined          | Hiring | Success      | Invited user joins a job team                             | Backend  | `job_id`, `role_label`, `signup_context`                                                                                 | `job` | `$set_once: signup_context`                                                                 | Not Started |
| Interest Reviewed           | Hiring | Success      | Team member reviews an expression of interest             | Frontend | `job_id`, `time_to_review_seconds`                                                                                       | `job` | --                                                                                          | Not Started |
| Review Decision Made        | Hiring | Success      | Reviewer makes a decision                                 | Backend  | `job_id`, `decision`                                                                                                     | `job` | --                                                                                          | Not Started |
| Record Video Button Clicked | Hiring | Interaction  | User clicks record intro video CTA                        | Frontend | `job_id`                                                                                                                 | `job` | --                                                                                          | Not Started |
| Intro Video Created         | Hiring | Success | Server confirms video saved                               | Backend  | `job_id`, `duration_seconds`, `takes_count`                                                                              | `job` | `group(job): has_intro_video = true`                                                        | Not Started |
| Intro Video Creation Failed | Hiring | Rejected | Server error on video save                                | Backend  | `job_id`, `error_reason`, `error_category`                                                                               | `job` | --                                                                                          | Not Started |
| Intro Video Deleted         | Hiring | Success      | User deletes intro video                                  | Backend  | `job_id`                                                                                                                 | `job` | `group(job): has_intro_video = false`                                                       | Not Started |
| Intro Script Updated        | Hiring | Success      | User saves script changes from AI editor                  | Backend  | `job_id`, `edit_method`                                                                                                  | `job` | --                                                                                          | Not Started |
| Candidate Viewed            | Hiring | View      | User opens candidate detail page                          | Frontend | `job_id`, `candidate_id`, `ai_recommendation`                                                                            | `job` | --                                                                                          | Not Started |
| Candidate Tab Viewed        | Hiring | View      | User views a tab on candidate detail                      | Frontend | `job_id`, `candidate_id`, `tab_name`                                                                                     | `job` | --                                                                                          | Not Started |
| Candidate Recording Played  | Hiring | Success      | User plays a candidate video recording                    | Frontend | `job_id`, `candidate_id`, `question_number`                                                                              | `job` | --                                                                                          | Not Started |

### Chat WebSocket Events


| Event                        | Area | Type | Trigger                       | Source   | Properties | Group | Property Updates | Status |
| ---------------------------- | ---- | ---- | ----------------------------- | -------- | ---------- | ----- | ---------------- | ------ |
| Chat WebSocket Connected     | Chat | Success   | WebSocket connection opened   | Frontend | --         | --    | --               | Removed — capture call removed in Helix PR #555 |
| Chat WebSocket Error         | Chat | Error   | WebSocket error               | Frontend | --         | --    | --               | Live   |
| Chat WebSocket Abnormal Close| Chat | Error   | WebSocket closed abnormally   | Frontend | --         | --    | --               | Live   |
| Chat WebSocket Parse Error   | Chat | Error   | Failed to parse WS message    | Frontend | --         | --    | --               | Live   |


---

## Removed Events

Events that were previously defined but have been removed or replaced.

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|-------------|
| Signup Started | Login Started Button Clicked | Wrong name (implied new users), hardcoded signup_context | April 2026 |
| Auth Login Started | Login Started Button Clicked | Fired too late (after MSAL popup), redundant | April 2026 |
| Auth Login Cancelled | _(removed)_ | Renamed for consistency; Login Cancelled subsequently removed (dead code) | April 2026 |
| Auth Role Updated | Account Create Succeeded | Role selection during onboarding now fires Account Create Succeeded | April 2026 |
| Auth Role Update Failed | _(removed)_ | Error handling moved to Account Create Succeeded flow | April 2026 |
| Persona Selected | Account Create Succeeded | Combined into single event — role selection IS account creation | April 2026 |
| Account Created (backend) | Account Create Succeeded | Moved from backend 5s heuristic to frontend role selection | April 2026 |
| Persona Activated | Persona Updated | Renamed — "Activated" implied adding a new persona; "Updated" reflects switching between existing personas | May 2026 |
| Job Created | Job Posting Draft Created | Renamed — draft is created on step 1 "Next", not on final publish | May 2026 |
| Job Published | Job Posting Published | Renamed + enriched with full job snapshot properties | May 2026 |
| Job Wizard Started | Job Post Wizard Started | Renamed for clarity | May 2026 |
| Job Wizard Step Completed | Per-step events (Job Post Wizard * Completed) | Umbrella event replaced by distinct per-step events | May 2026 |
| Voice Session Started | Sam Session Started | Now covers both voice AND text sessions via input_mode | May 2026 |
| Voice Session Ended | Sam Session Ended | Now covers both modalities; ended_by changed from user/sam to user/completed | May 2026 |
| Voice Session Setup Failed | Sam Session Setup Failed | Voice setup failure now has a dedicated Sam failure event | May 2026 |
| Requirement Modified | Role Requirement Deleted, Role Requirement Edited, Role Requirement Added | Generic `modification_type` replaced by specific role requirement events with richer properties | June 2026 |
| Question Modified | Screening Question Deleted, Screening Question Edited, Screening Question Added | Generic `modification_type` replaced by specific screening question events with richer properties | June 2026 |
| Profile Created | Candidate Profile Create Succeeded | Enriched with resume, photo, and link state; same trigger point | June 2026 |
| Custom Link Created | Custom Link Added | Renamed for clearer action wording; properties updated from `surface` to `current_persona` | June 2026 |
| Build Profile Snapshot | Candidate Profile Create Succeeded | Metadata folded into backend Candidate Profile Create Succeeded via createPortfolio() API | July 2026 |
| Candidate Interview Question Resolve Succeeded | Candidate Interview Question Answer Succeeded + Skip Succeeded | Split into per-question outcome events | July 2026 |
| Resume Upload Button Clicked | Candidate Resume Upload Button Clicked | Prefix rename | July 2026 |
| Resume Uploaded | Candidate Resume Upload Succeeded | Rename to canonical terminal | July 2026 |
| Resume Upload Failed | Candidate Resume Upload Rejected + Candidate Resume Upload Errored | Split: Rejected = client validation, Errored = server extraction | July 2026 |
| Resume Removed | Candidate Resume Remove Button Clicked | Rename to intent event | July 2026 |
| Custom Link Added | Candidate Profile Custom Link Add Succeeded | Rename to canonical terminal | July 2026 |
| LinkedIn Export Learn How Clicked | LinkedIn Export Learn How Link Clicked | Minor rename (added "Link") | July 2026 |
| Profile Photo Removed | Candidate Profile Photo Remove Button Clicked | Rename to intent event | July 2026 |
| Add Profile Photo Button Clicked (editor) | Change Profile Photo Button Clicked | Create-profile version retained; editor version renamed | July 2026 |
| Account Created | Account Create Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Intro Completed | Onboarding Intro Complete Button Clicked | Reclassified — click event, not async outcome (Success → Interaction) | July 2026 |
| Login Started | Login Started Button Clicked | Reclassified — click event, not state transition (Started → Interaction) | July 2026 |
| Auth Logout Completed | Auth Logout Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Auth Login Failed | Auth Login Rejected | Renamed — user-initiated auth declined by system | July 2026 |
| Auth Email Verify Code Sent | Auth Email Verify Code Send Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Auth Email Verified | Auth Email Verify Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Auth Email Verify Failed | Auth Email Verify Rejected | Renamed — wrong code entered by user | July 2026 |
| Auth Email Verify Code Send Failed | Auth Email Verify Code Send Errored | Renamed — system/network error, not user-caused (Rejected → Error) | July 2026 |
| Auth Session Restore Failed | Auth Session Restore Errored | Renamed — system/network error, not user-caused (Rejected → Error) | July 2026 |
| Auth Refresh Failed | Auth Refresh Errored | Renamed — token refresh is a system process (Rejected → Error) | July 2026 |
| Handle Claimed | Handle Claim Succeeded | Codebase name, never in catalog | July 2026 |
| Handle Claim Failed | Handle Claim Rejected | Codebase name, never in catalog | July 2026 |
| Profile Photo Added | Profile Photo Add Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Candidate Profile Created | Candidate Profile Create Succeeded | Renamed — Success events must end "Succeeded" | July 2026 |
| Candidate Profile Creation Failed | Candidate Profile Create Errored | Renamed — backend failure, not user-caused (Rejected → Error) | July 2026 |
| Login Cancelled | _(removed)_ | Dead code — old MSAL popup, never called since Clerk migration | July 2026 |
| Auth Phone Submitted | _(removed)_ | Dead code — phone collection not wired into app router | July 2026 |
| Auth Phone Submit Failed | _(removed)_ | Dead code — phone collection not wired into app router | July 2026 |
| Auth Phone Skipped | _(removed)_ | Dead code — phone collection not wired into app router | July 2026 |
| Candidate Handle Add Succeeded | _(removed)_ | Never wired — catalog name never matched code | July 2026 |
| Candidate Handle Add Rejected | _(removed)_ | Never wired — catalog name never matched code | July 2026 |

---

## Property Dictionary

### Enum Properties


| Property                | Type | Scope                     | Allowed Values                                                                      | Used In                                                        |
| ----------------------- | ---- | ------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `entry_point`           | enum | event, person ($set_once) | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct`, `interview` | Page Viewed, Login Started Button Clicked, Account Create Succeeded |
| `first_persona`         | enum | event, person ($set_once) | `hiring_manager`, `recruiter`, `job_seeker`                                         | Account Create Succeeded (person property), Onboarding Complete Succeeded (person property) |
| `signup_context`        | enum | event, person ($set_once) | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct`             | Team Member Joined                                             |
| `current_persona`       | enum | event, person ($set)      | `hiring_manager`, `recruiter`, `job_seeker`, `unknown`                              | All frontend events (super-property), Account Create Succeeded, Persona Updated, Onboarding Complete Succeeded |
| `previous_persona`      | enum | event                     | `hiring_manager`, `recruiter`, `job_seeker`                                         | Persona Updated, Persona Update Failed                         |
| `target_persona`        | enum | event                     | `hiring_manager`, `recruiter`, `job_seeker`                                         | Persona Update Failed                                          |
| `activation_action`     | enum | event                     | `profile_created`, `interest_expressed`, `job_created`                              | Account Activated                                              |
| `input_method`          | enum | event                     | `resume_upload`, `linkedin_import`                                                  | Candidate Profile Create Succeeded                             |
| `section`               | enum | event                     | `summary`, `skills`, `journey`, `experience`, `education`                            | Profile Section Updated                                        |
| `share_channel`         | enum | event                     | `copy`, `email`, `linkedin`, `x`, `other`                                           | Custom Link Shared, Job Shared, Job Share Channel Clicked      |
| `session_type`          | enum | event                     | `first_time`, `returning`                                                           | Career Coach Session Started                                   |
| `input_mode`            | enum | event                     | `text`, `voice`                                                                     | Career Coach Session Started, Sam Session Started, Sam Session Setup Failed, Sam Session Ended, Candidate Interview Started, Candidate Interview Question Answer Succeeded, Candidate Interview Submit Succeeded |
| `message_type`          | enum | event                     | `text`, `voice`                                                                     | Career Coach Message Sent                                      |
| `topic`                 | enum | event                     | `profile_improvement`, `job_application`, `career_advice`                           | Career Coach Message Sent                                      |
| `from_status`           | enum | event                     | `draft`, `open`, `closed`, `archived`                                               | Job Status Changed                                             |
| `to_status`             | enum | event                     | `draft`, `open`, `closed`, `archived`                                               | Job Status Changed                                             |
| `invited_role_label`    | enum | event                     | `recruiter`, `team_member`                                                          | Team Member Invited                                            |
| `invite_method`         | enum | event                     | `email`, `link`                                                                     | Team Member Invited                                            |
| `role_label`            | enum | event                     | `hiring_manager`, `recruiter`, `team_member`                                        | Team Member Joined                                             |
| `decision`              | enum | event                     | `shortlisted`, `declined`, `needs_discussion`                                       | Review Decision Made                                           |
| `action` (job link)     | enum | event                     | `view_details`, `express_interest`                                                  | Job Link Engaged                                               |
| `action` (profile link) | enum | event                     | `view_full_profile`, `download_resume`                                              | Profile Link Engaged                                           |
| `action` (user_action)  | enum | event                     | `click`, `submit`, `toggle`                                                         | Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Description Details Toggled, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Requirement Add Button Clicked, Role Requirement Deleted, Job Post Wizard Interview Questions Completed, Question Add Button Clicked, Screening Question Deleted, Job Verification Code Send Button Clicked, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked, Success Page Share Button Clicked, Job Share Message AI Refined, Job Share Message Copied, Job Share Channel Clicked, Invite Teammates Button Clicked, Team Member Invite Sent, Job Posting Page Link Clicked, Archive Job Button Clicked, Share Button Clicked, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Previous Resume Select Button Clicked, Candidate Custom Link Delete Button Clicked, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Unpublish Button Clicked, Candidate Portfolio Create Button Clicked, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Delete Button Clicked, Get Started Interview Button Clicked, Candidate Interview Info Next Button Clicked, What To Expect Link Clicked, Candidate Interview Resume Next Button Clicked, Open Identity Check Link Clicked, Refresh Status Button Clicked, Candidate Interview Privacy Email Link Clicked, Candidate Interview Persona Privacy Policy Link Clicked, Candidate Interview Screening Response Next Button Clicked, Candidate Interview Screening Response Save And Review Button Clicked, Allow Device Access Button Clicked, Candidate Interview Start Button Clicked, Candidate Interview Question Restart Button Clicked, Candidate Interview Question Skip Button Clicked, Candidate Interview Screening Response Edit Button Clicked |
| `step_name`             | enum | event                     | `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify` | Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited, Job Post Wizard Job Details Completed, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Requirement Add Button Clicked, Role Requirement Deleted, Role Requirement Edited, Role Requirement Added, Job Post Wizard Interview Questions Completed, Question Add Button Clicked, Screening Question Deleted, Screening Question Edited, Screening Question Added, Job Verification Code Send Button Clicked, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked |
| `ended_by`              | enum | event                     | `user`, `completed`                                                                 | Sam Session Ended                                              |
| `share_source`          | enum | event                     | `success_screen`, `dashboard`, `overflow_menu`                                      | Job Shared, Job Share Failed                                   |
| `error_category`        | enum | event                     | `network`, `permission`, `validation`, `server`, `timeout`, `hardware`, `unknown`, `unsupported_format`, `extraction_failed`, `invalid_magic_bytes`, `size_limit`, `ai_generation`, `vendor`, `mismatch` | All failure events (incl. Persona Update Failed), Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Profile Photo Upload Failed, Candidate Profile Create Errored, Candidate Portfolio Publish Errored, Candidate Interview Identity Verification Errored, Candidate Interview Question Restart Errored, Candidate Interview Question Skip Errored, Candidate Interview Submit Rejected |
| `tab_name`              | enum | event                     | `summary`, `role_requirements`, `recordings`, `notes`, `overview`, `resume`, `github`, `portfolio` | Candidate Tab Viewed, Candidate Profile Tab Switched           |
| `edit_method`           | enum | event                     | `text`, `voice`                                                                     | Intro Script Updated                                           |
| `ai_recommendation`     | enum | event                     | `shortlisted`, `declined`                                                           | Candidate Viewed                                               |
| `auth_method`           | enum | event                     | `google`, `microsoft`, `email`, `saml`                                              | Login Started Button Clicked, Account Create Succeeded, Onboarding Complete Succeeded |
| `intake_mode`           | enum | event                     | `ai_copilot`, `hm_solo`, `manual`, `skipped`                                        | Job Post Wizard Intake Mode Selected, Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `identity_verification_mode` | enum | event                | `require`, `off`                                                                    | Job Post Wizard Interview Questions Completed, Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `field_name`            | enum | event                     | `job_title`, `job_location`, `company_name`                                         | Job Description Field Edited                                   |
| `question_type`         | enum | event                     | `yes_no`, `multiple_choice`, `free_text`                                            | Role Requirement Deleted, Role Requirement Edited, Role Requirement Added |
| `question_source`       | enum | event                     | `ai_generated`, `manual`                                                            | Role Requirement Deleted, Role Requirement Edited, Screening Question Deleted, Screening Question Edited |
| `category` (requirement) | enum | event                    | `compensation`, `work_arrangement`, `visa_authorization`, `security_clearance`, `licensing`, `background_check`, `physical_requirements`, `travel`, `other` | Role Requirement Deleted, Role Requirement Edited, Role Requirement Added |
| `invite_role`           | enum | event                     | `recruiter`, `other`                                                                | Team Member Invite Sent                                        |
| `start_source`          | enum | event                     | `create_job_button`, `interview_link`, `email_invite`, `job_board`, `direct`         | Job Post Wizard Started, Page Viewed                           |
| `job_status`            | enum | event, group (job)        | `draft`, `open`, `closed`, `archived`                                               | Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published, All events in job group (group property) |
| `job_visibility`        | enum | event, group (job)        | `public`, `private`                                                                 | Job Posting Draft Created, Job Posting Published, All events in job group (group property) |
| `upload_method`         | enum | event                     | `take_photo`, `upload`                                                              | Profile Photo Add Succeeded, Profile Photo Upload Failed       |
| `resume_file_type`      | enum | event                     | `pdf`, `doc`, `docx`, `txt`                                                         | Candidate Resume Upload Succeeded, Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Candidate Resume Remove Button Clicked, Candidate Previous Resume Select Button Clicked |
| `file_type` (photo)     | enum | event                     | `jpg`, `png`, `gif`, `webp`                                                         | Profile Photo Add Succeeded                                    |
| `link_type`             | enum | event                     | `general`, `job_specific`, `github`, `linkedin`, `portfolio`, `personal`            | Candidate Profile Custom Link Add Succeeded, Candidate Custom Link Delete Button Clicked, Candidate Custom Link Delete Succeeded, Candidate Custom Link Delete Errored |
| `decision_category`     | enum | event                     | `pass`, `fail`, `inconclusive`, `unavailable`                                       | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected |
| `question_status`       | enum | event                     | `answered`, `answered_restarted`, `skipped`                                         | Candidate Interview Question Answer Succeeded                  |
| `mode`                  | enum | event                     | `onboarding`, `editor`, `dashboard`, `retake`                                       | Candidate Interview Answer Retake Succeeded, Candidate Resume Upload Button Clicked, Candidate Resume Upload Succeeded, Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Profile Photo Add Succeeded, Profile Photo Upload Failed, Candidate Profile Photo Remove Button Clicked, Candidate Profile Photo Remove Succeeded, Candidate Profile Photo Remove Errored, Candidate Profile Custom Link Add Succeeded, Candidate Custom Link Delete Button Clicked, Candidate Custom Link Delete Succeeded, Candidate Custom Link Delete Errored, Build Profile Button Clicked, Candidate Profile Create Succeeded, Candidate Profile Create Errored, Onboarding Complete Succeeded |
| `outcome`               | enum | event                     | `answered`, `skipped`                                                               | Candidate Interview Answer Retake Succeeded                    |

### Array Properties


| Property             | Type  | Scope         | Description                                   | Used In                      |
| -------------------- | ----- | ------------- | --------------------------------------------- | ---------------------------- |
| `activated_personas` | array | event, person ($set) | All unique personas the user has ever been in. Seeded with `[persona]` on Account Create Succeeded, accumulates via Persona Updated. Sent as top-level event property on Persona Updated. DB column and PostHog person property stay in sync. | Account Create Succeeded (person property), Persona Updated |
| `link_types`         | array | event                | Platform types of added links (`github`, `linkedin`, `portfolio`, `personal_website`, `other`) | Candidate Profile Create Succeeded |


### Boolean Properties


| Property                  | Type    | Scope       | Used In                                    |
| ------------------------- | ------- | ----------- | ------------------------------------------ |
| `is_job_specific`         | boolean | event       | Candidate Profile Custom Link Add Succeeded, Custom Link Shared |
| `has_custom_link`         | boolean | event       | Interest Expressed                         |
| `has_resume`              | boolean | event       | Interest Expressed, Candidate Profile Create Succeeded, Onboarding Complete Succeeded, Candidate Interview Resume Next Button Clicked, Candidate Interview Started, Candidate Interview Submit Succeeded |
| `is_authenticated`        | boolean | event       | Job Link Viewed, Profile Link Viewed       |
| `job_verified`            | boolean | event       | Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `mic_enabled`             | boolean | event       | Sam Session Setup Failed                   |
| `verification_required`   | boolean | event       | Auth Login Succeeded                       |
| `has_compensation`        | boolean | event       | Job Description Evaluated                  |
| `has_benefits`            | boolean | event       | Job Description Evaluated                  |
| `expanded`                | boolean | event       | Job Description Details Toggled            |
| `ai_refined`              | boolean | event       | Screening Question Edited                  |
| `ai_created`              | boolean | event       | Screening Question Added                   |
| `has_photo`               | boolean | event       | Candidate Profile Create Succeeded, Onboarding Complete Succeeded |
| `has_intro_video`         | boolean | group (job), event | All jobs with intro video (group property), Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `has_handle`              | boolean | event       | Candidate Profile Create Succeeded, Onboarding Complete Succeeded |
| `has_first_name`          | boolean | event       | Candidate Interview Info Next Button Clicked |
| `has_last_name`           | boolean | event       | Candidate Interview Info Next Button Clicked |
| `agreement_acknowledged`  | boolean | event       | Candidate Interview Resume Next Button Clicked |
| `camera_granted`          | boolean | event       | Device Access Grant Succeeded, Device Access Rejected |
| `mic_granted`             | boolean | event       | Device Access Grant Succeeded, Device Access Rejected |
| `is_published`            | boolean | event       | Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded, Candidate Portfolio Unpublish Succeeded |
| `has_description`         | boolean | event       | Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `has_profile_photo`       | boolean | event       | Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `was_published`           | boolean | event       | Candidate Portfolio Delete Succeeded       |
| `identity_verified`       | boolean | event       | Candidate Interview Started, Candidate Interview Submit Succeeded |
| `is_test_run`             | boolean | event       | Candidate Interview Started, Candidate Interview Submit Succeeded |
| `ai_conversation_completed` | boolean | event     | Candidate Interview Question Answer Succeeded, Candidate Interview Answer Retake Succeeded |
| `had_email_verification`  | boolean | event       | Onboarding Complete Succeeded              |


### Numeric Properties


| Property                 | Type   | Scope | Description                                    | Used In                                  |
| ------------------------ | ------ | ----- | ---------------------------------------------- | ---------------------------------------- |
| `time_to_review_seconds` | number | event | Seconds between interest submission and review | Interest Reviewed                        |
| `days_since_signup`      | number | event | Days between account creation and activation   | Account Activated                        |
| `step_number`            | number | event | Wizard step (1–5)                              | Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited, Job Post Wizard Job Details Completed, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Requirement Add Button Clicked, Role Requirement Deleted, Role Requirement Edited, Role Requirement Added, Job Post Wizard Interview Questions Completed, Question Add Button Clicked, Screening Question Deleted, Screening Question Edited, Screening Question Added, Job Verification Code Send Button Clicked, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked |
| `duration_seconds`       | number | event | Duration in seconds                            | Sam Session Ended, Intro Video Created   |
| `takes_count`            | number | event | Number of recording takes before save          | Intro Video Created                      |
| `questions_count`        | number | event | Questions count (screening or interview)       | Screening Configuration Saved, Job Posting Verified, Job Posting Published, Candidate Interview Started, Candidate Interview Answers Submit Succeeded, Candidate Interview Screening Response Submit Succeeded, Candidate Interview Submit Succeeded |
| `ai_generated_questions_count` | number | event | AI-generated screening questions count    | Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `manual_questions_count` | number | event | Manually added screening questions count       | Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `question_number`        | number | event | Question position in order                     | Screening Question Deleted, Screening Question Edited, Candidate Recording Played, Candidate Interview Question Answer Succeeded, Candidate Interview Question Restart Button Clicked, Candidate Interview Question Restart Succeeded, Candidate Interview Question Restart Errored, Candidate Interview Question Skip Button Clicked, Candidate Interview Question Skip Succeeded, Candidate Interview Question Skip Errored, Candidate Interview Question Skip Rejected, Candidate Interview Review Answer Button Clicked, Candidate Interview Retake Question Button Clicked, Candidate Interview Review Answer Expand Clicked, Candidate Interview Answer Retake Succeeded |
| `input_length`           | number | event | Character count of pasted job description text | Job Description Evaluated, Job Description Evaluation Failed |
| `skills_count`           | number | event | Number of skills (AI-extracted or profile)     | Job Description Evaluated, Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `requirements_count`     | number | event | Number of key requirements extracted by AI     | Job Description Evaluated                |
| `responsibilities_count` | number | event | Number of responsibilities extracted by AI     | Job Description Evaluated                |
| `refined_message_length` | number | event | Character count of AI-refined share message    | Job Share Message AI Refined             |
| `message_length`         | number | event | Character count of copied share message        | Job Share Message Copied                 |
| `invite_count`           | number | event | Number of invite recipients submitted          | Team Member Invite Sent                  |
| `status_code`            | number | event | HTTP status code from auth backend             | Auth Login Rejected, Auth Session Restore Errored, Auth Refresh Errored, Auth Dev Login Failed, Auth Email Verify Code Send Errored, Auth Email Verify Rejected |
| `cooldown_seconds`       | number | event | Seconds before resend is allowed               | Auth Email Verify Code Send Succeeded    |
| `attempts_remaining`     | number | event | Remaining verification attempts                | Auth Email Verify Rejected               |
| `resume_size_bytes`      | number | event | Resume file size in bytes                      | Candidate Resume Upload Succeeded, Candidate Resume Upload Rejected, Candidate Resume Upload Errored |
| `file_size_bytes`        | number | event | Image file size (photo events only)            | Profile Photo Add Succeeded, Profile Photo Upload Failed |
| `page_count`             | number | event | Page count (PDF native, DOCX via page breaks, TXT estimated; null for .doc or on error) | Candidate Resume Upload Succeeded        |
| `links_count`            | number | event | Total external links                           | Candidate Profile Create Succeeded, Onboarding Complete Succeeded |
| `resume_page_count`      | number | event | Resume page count                              | Candidate Profile Create Succeeded       |
| `time_to_verify_seconds` | number | event | Seconds from Open Identity Check to verification | Candidate Interview Identity Verification Succeeded |
| `response_duration_seconds` | number | event | Spoken/typed duration on a question          | Candidate Interview Question Answer Succeeded |
| `total_duration_seconds` | number | event | End-to-end interview duration                  | Candidate Interview Submit Succeeded     |
| `yes_count`              | number | event | Yes answers on screening                       | Candidate Interview Screening Response Submit Succeeded |
| `no_count`               | number | event | No answers on screening                        | Candidate Interview Screening Response Submit Succeeded |
| `optional_context_provided_count` | number | event | Yes answers with optional context filled | Candidate Interview Screening Response Submit Succeeded |
| `required_explanation_count` | number | event | No answers (mandatory explanation)           | Candidate Interview Screening Response Submit Succeeded |
| `screening_questions_count` | number | event | Screening question count                      | Candidate Interview Submit Succeeded     |
| `new_name_length`        | number | event | New portfolio name length                      | Candidate Portfolio Rename Succeeded     |
| `previous_name_length`   | number | event | Previous portfolio name length                 | Candidate Portfolio Rename Succeeded     |
| `profile_completeness_rate` | number | event | Percentage of completeness steps filled (0–100) | Candidate Profile Overview Load Succeeded |
| `handle_length`          | number | event | Handle character count                         | Handle Claim Succeeded                   |
| `journey_count`          | number | event | Journey/timeline entries                       | Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `responses_changed_count` | number | event | Number of screening responses changed in edit  | Candidate Interview Screening Response Edit Succeeded |
| `context_added_count`    | number | event | Number of screening contexts added in edit     | Candidate Interview Screening Response Edit Succeeded |
| `context_removed_count`  | number | event | Number of screening contexts removed in edit   | Candidate Interview Screening Response Edit Succeeded |
| `onboarding_duration_seconds` | number | event | Seconds from first auth Page Viewed to Onboarding Complete Succeeded | Onboarding Complete Succeeded |


### String Properties


| Property              | Type     | Scope              | Description                                                                | Used In                                          |
| --------------------- | -------- | ------------------ | -------------------------------------------------------------------------- | ------------------------------------------------ |
| `action_value`        | string   | event              | Specific UI element interacted with (snake_case)                           | Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Switch Persona Button Clicked, Create Job Button Clicked, Job Post Wizard Job Details Completed, Job Description Details Toggled, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Requirement Add Button Clicked, Role Requirement Deleted, Job Post Wizard Interview Questions Completed, Question Add Button Clicked, Screening Question Deleted, Job Verification Code Send Button Clicked, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked, Success Page Share Button Clicked, Job Share Message AI Refined, Job Share Message Copied, Job Share Channel Clicked, Invite Teammates Button Clicked, Team Member Invite Sent, Job Posting Page Link Clicked, Archive Job Button Clicked, Share Button Clicked, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Previous Resume Select Button Clicked, Candidate Custom Link Delete Button Clicked, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Unpublish Button Clicked, Change Profile Photo Button Clicked, Candidate Portfolio Create Button Clicked, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Delete Button Clicked, Get Started Interview Button Clicked, Candidate Interview Info Next Button Clicked, What To Expect Link Clicked, Candidate Interview Resume Next Button Clicked, Open Identity Check Link Clicked, Refresh Status Button Clicked, Candidate Interview Identity Verification Continue Button Clicked, Candidate Interview Privacy Email Link Clicked, Candidate Interview Persona Privacy Policy Link Clicked, Candidate Interview Screening Response Next Button Clicked, Candidate Interview Screening Response Save And Review Button Clicked, Allow Device Access Button Clicked, Candidate Interview Start Button Clicked, Candidate Interview Question Restart Button Clicked, Candidate Interview Question Skip Button Clicked, Candidate Interview Question Skip Rejected, Candidate Interview Screening Response Edit Button Clicked, Candidate Interview Review Answer Button Clicked, Candidate Interview Retake Question Button Clicked |
| `current_page_context`| string   | event              | Page where event occurred (snake_case, `_` hierarchy)                      | Page Viewed, Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Onboarding Complete Succeeded, Handle Claim Succeeded, Handle Claim Rejected, Switch Persona Button Clicked, Sam Session Started, Sam Session Ended, all Job Post Wizard events, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Profile Photo Add Succeeded, Profile Photo Upload Failed, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Profile Overview Load Succeeded, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Unpublish Button Clicked, Change Profile Photo Button Clicked, Candidate Portfolio Create Button Clicked, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Delete Button Clicked, all Candidate Interview events |
| `previous_page_context`| string  | event              | Previous page before current one                                           | Page Viewed, Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Onboarding Complete Succeeded, Switch Persona Button Clicked, Sam Session Started, Sam Session Ended, all Job Post Wizard events, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Profile Photo Add Succeeded, Profile Photo Upload Failed, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Profile Overview Load Succeeded, Candidate Portfolio Create Button Clicked |
| `component`           | string   | event              | UI container where action occurred                                         | Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Switch Persona Button Clicked, all Job Post Wizard step events, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Previous Resume Select Button Clicked, Candidate Custom Link Delete Button Clicked, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Unpublish Button Clicked, Candidate Portfolio Create Button Clicked, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Delete Button Clicked, Get Started Interview Button Clicked, Candidate Interview Info Next Button Clicked, What To Expect Link Clicked, Candidate Interview Resume Next Button Clicked, Open Identity Check Link Clicked, Refresh Status Button Clicked, Candidate Interview Privacy Email Link Clicked, Candidate Interview Persona Privacy Policy Link Clicked, Candidate Interview Screening Response Next Button Clicked, Candidate Interview Screening Response Save And Review Button Clicked, Allow Device Access Button Clicked, Candidate Interview Start Button Clicked, Candidate Interview Question Restart Button Clicked, Candidate Interview Question Skip Button Clicked |
| `entity_type`         | string   | event              | Business object being acted on (`interview`, `identity_check`, `screening_response`, `interview_question`, `device_check`, `candidate_profile`, `onboarding`, `account`, etc.) | Login Started Button Clicked, Account Create Succeeded, Onboarding Intro Complete Button Clicked, Onboarding Persona Card Clicked, Switch Persona Button Clicked, all Job Post Wizard step events, Candidate Resume Upload Button Clicked, Candidate Resume Remove Button Clicked, LinkedIn Export Learn How Link Clicked, Add Profile Photo Button Clicked, Profile Photo Add Succeeded, Profile Photo Upload Failed, Candidate Profile Photo Remove Button Clicked, Build Profile Button Clicked, Candidate Previous Resume Select Button Clicked, Candidate Custom Link Delete Button Clicked, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Unpublish Button Clicked, Change Profile Photo Button Clicked, Candidate Portfolio Create Button Clicked, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Delete Button Clicked, all Candidate Interview events |
| `link_name`           | string   | event              | User-provided name for the custom link                                     | Candidate Profile Custom Link Add Succeeded      |
| `target_job_title`    | string   | event              | Job title the link targets (optional, only when `is_job_specific` is true) | Candidate Profile Custom Link Add Succeeded      |
| `target_company`      | string   | event              | Company the link targets (optional, only when `is_job_specific` is true)   | Candidate Profile Custom Link Add Succeeded      |
| `resume_id`           | string   | event              | Resume identifier                                                          | Candidate Resume Upload Succeeded, Candidate Resume Remove Button Clicked, Candidate Profile Create Succeeded, Candidate Profile Create Errored, Candidate Resume Download Succeeded, Candidate Previous Resume Select Button Clicked |
| `resume_name`         | string   | event              | Original uploaded filename                                                 | Candidate Resume Upload Succeeded                |
| `portfolio_id`        | string   | event              | Generated portfolio identifier                                             | Candidate Profile Create Succeeded, Candidate Profile Overview Load Succeeded, Candidate Profile Tab Switched, Candidate Resume Download Succeeded, Candidate Portfolio Publish Button Clicked, Candidate Portfolio Publish Succeeded, Candidate Portfolio Publish Errored, Candidate Portfolio Unpublish Button Clicked, Candidate Portfolio Unpublish Succeeded, Change Profile Photo Button Clicked, Candidate Profile Photo Remove Button Clicked, Candidate Profile Photo Remove Succeeded, Candidate Profile Photo Remove Errored, Candidate Portfolio Rename Button Clicked, Candidate Portfolio Rename Succeeded, Candidate Portfolio Delete Button Clicked, Candidate Portfolio Delete Succeeded |
| `reason`              | string   | event              | Reason for withdrawal or rejection                                         | Interest Withdrawn, Handle Claim Rejected        |
| `error_reason`        | string   | event              | System error description                                                   | All failure events, Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Profile Photo Upload Failed, Candidate Profile Create Errored, Candidate Custom Link Delete Errored, Candidate Portfolio Publish Errored, Candidate Profile Photo Remove Errored, Candidate Interview Resume Upload Errored, Candidate Interview Identity Verification Errored, Device Access Rejected, Candidate Interview Question Restart Errored, Candidate Interview Question Skip Errored, Candidate Interview Submit Rejected |
| `auth_mode`           | string   | event              | Auth mode (e.g., `msal`, `posthog`, `dev`)                                 | Auth Login Succeeded, Auth Login Rejected, Auth Session Restore Succeeded, Auth Logout Succeeded, Auth Dev Login Started, Auth Dev Login Succeeded, Auth Dev Login Failed |
| `error_detail`        | string   | event              | Detailed error message                                                     | Auth Login Rejected, Auth Session Restore Errored, Auth Refresh Errored, Auth Dev Login Failed, Auth Email Verify Code Send Errored, Auth Email Verify Rejected |
| `source`              | string   | event              | Source that triggered the refresh; also `webhook` / `poll` for identity verification delivery mechanism, and traffic source for interview events | Auth Refresh Errored, Handle Claim Succeeded, Handle Claim Rejected, Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected, Candidate Interview Started, Candidate Interview Submit Succeeded |
| `first_referrer`      | string   | person ($set_once) | HTTP referrer at first visit                                               | Page Viewed (person property)                    |
| `first_landing_url`   | string   | person ($set_once) | Full landing URL at first visit                                            | Page Viewed (person property)                    |
| `account_created_at`  | ISO date | person ($set_once) | Account creation timestamp                                                 | Account Create Succeeded (person property)       |
| `session_id`          | string   | event              | Backend session identifier for Sam conversations                           | Sam Session Started, Sam Session Setup Failed, Sam Session Ended |
| `job_location`        | string   | event              | Job location extracted from JD                                             | Job Description Evaluated, Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `company_name`        | string   | event              | Company name                                                               | Job Description Evaluated, Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published |
| `seniority_level`     | string   | event              | AI-extracted seniority level                                               | Job Description Evaluated                         |
| `work_type`           | string   | event              | AI-extracted work type                                                     | Job Description Evaluated                         |
| `employment_type`     | string   | event              | AI-extracted employment type                                               | Job Description Evaluated                         |
| `new_value`           | string   | event              | Value after user edit                                                      | Job Description Field Edited                      |
| `question_text`       | string   | event              | Requirement or screening question text                                     | Role Requirement Deleted, Role Requirement Added, Screening Question Deleted, Screening Question Added |
| `original_text`       | string   | event              | Text before edit                                                           | Role Requirement Edited, Screening Question Edited |
| `new_text`            | string   | event              | Text after edit                                                            | Role Requirement Edited, Screening Question Edited |
| `context_object_type` | string   | event              | Object type for contextual actions                                         | Share Button Clicked                             |
| `context_object_id`   | string   | event              | Object ID for contextual actions                                           | Share Button Clicked                             |
| `job_title`           | string   | group (job)        | Job posting title                                                          | All events in job group (group property)         |
| `created_at`          | ISO date | group (job)        | Job creation timestamp                                                     | All events in job group (group property)         |
| `verification_vendor` | string   | event              | Third-party identity vendor                                                | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected |
| `previous_state`      | string   | event              | Previous answer state before retake                                        | Candidate Interview Answer Retake Succeeded      |
| `org_id`              | string   | event              | Organization ID                                                            | Candidate Interview Submit Succeeded             |


### UUID Properties


| Property                 | Type | Scope                     | Description                                  | Used In                                                                                                                 |
| ------------------------ | ---- | ------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `job_id`                 | UUID | event                     | Job identifier                               | All job-related events (standard property)                                                                              |
| `shared_by_user_id`      | UUID | event                     | User who shared the link                     | Job Shared                                                                                                              |
| `referrer_user_id`       | UUID | event                     | User who referred the visitor                | Job Link Viewed, Job Link Engaged                                                                                       |
| `referrer_job_id`        | UUID | event                     | Job associated with the referral             | Job Link Viewed, Job Link Engaged                                                                                       |
| `profile_user_id`        | UUID | event                     | Prospect whose profile is being viewed       | Profile Link Viewed, Profile Link Engaged                                                                               |
| `custom_link_id`         | UUID | event                     | Which custom link was used                   | Profile Link Viewed, Profile Link Engaged                                                                               |
| `referred_by`            | UUID | event, person ($set_once) | User who referred this user at signup        | Account Create Succeeded                                                                                                |
| `hiring_manager_user_id` | UUID | group (job)               | Hiring manager for the job                   | All events in job group (group property)                                                                                |
| `created_by_user_id`     | UUID | group (job)               | User who created the job                     | All events in job group (group property)                                                                                |
| `candidate_id`           | UUID | event                     | Candidate being reviewed                     | Candidate Viewed, Candidate Tab Viewed, Candidate Recording Played                                                      |
| `interview_id`           | UUID | event                     | Anonymous AI interview session identifier    | All Candidate Interview events, Get Started Interview Button Clicked, What To Expect Link Clicked, Open Identity Check Link Clicked, Refresh Status Button Clicked, Allow Device Access Button Clicked, Device Access Grant Succeeded, Device Access Rejected |
| `interview_result_id`    | UUID | event                     | Interview result/submission identifier       | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected, Candidate Interview Submit Succeeded |
| `attempt_id`             | string | event                   | Identity verification attempt ID             | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected |
