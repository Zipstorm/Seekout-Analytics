# Tracking Plan: Job Seeker Interview v2

**Product:** Helix (SeekOut.ai)
**Feature:** Job seeker v2 — handle on create-profile, profile editor/overview, dashboard portfolio management, and the anonymous AI screening interview flow
**Date:** 2026-06-12
**Related PRD:** —
**Repo:** Zipstorm/helix
**Branch:** job-seeker-interview-v2
**PR:** https://github.com/Zipstorm/helix/pull/739

- [x] Draft created — 2026-06-12
- [x] Validated — 2026-06-12, 13/13 rules pass
- [x] Codebase implemented — helix#739
- [x] Absorbed from codebase — 2026-07-02, 65 events
- [x] Re-validated — 2026-07-02, 13/13 rules pass
- [x] PR raised — seekout-analytics#30
- [ ] PR approved
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/helix/event-schema.md`, and `docs/helix/event-catalog.md`.

This plan builds on **Job Seeker Profile Setup v1** (`tracking-plan/job-seeker-v1` branch). It picks up the editor (B) and dashboard (C) events that v1 explicitly deferred to v2, adds the handle field (A) to the v1 create-profile flow, and instruments the brand-new anonymous AI interview flow (D).

It is organized into four parts:

| Part | Area | Surface |
|---|---|---|
| **A** | Profile handle | `/candidate/create-profile` (modifies v1 events) |
| **B** | Profile editor / overview | `/candidate/editor/:portfolioId` |
| **C** | Dashboard — portfolio management | `/candidate/dashboard` |
| **D** | Anonymous AI screening interview | `/interview/:interviewId` |

---

## Distinct ID & anonymous handling (Part D)

The interview candidate **does not need to be a Helix user**. PostHog's native anonymous ID is used with header-based backend bridging:

1. **Frontend anonymous ID.** PostHog assigns an auto-generated anonymous browser ID. All frontend interview events fire under this ID.
2. **Backend bridging via `X-PostHog-Anon-Id` header.** The frontend passes its anonymous ID to the backend on every authenticated request. At `startInterview()`, the backend calls `posthog.alias(candidate_id, anon_id)` to merge the backend person with the frontend anonymous person. Submit events use the anonymous ID as `distinct_id`.
3. **Email alias.** At the info step (D2), `posthog.alias(email)` links the anonymous browser ID to the candidate's email.
4. **Interview ID alias.** On mount, `posthog.alias(interviewId)` links the anonymous browser ID to the interview ID used by `Interview Link Open Succeeded`.
5. **Signup stitching.** If the candidate creates an account, `posthog.identify(userId)` merges the anonymous person into the authenticated user. `Account Created` fires from the backend with `entry_point = interview`.
6. **Identity verification events.** Webhook/poll events fire with `candidate_id` as `distinct_id` (no HTTP context). They rely on the email alias from step 3 to join the funnel.

---

## New Events Summary

Overview of all events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Candidate Handle Add Succeeded | Prospect | Success | Frontend | Handle blur or submit, availability = available | Job seeker, /candidate/create-profile, handle field availability check passes | `handle_length`, `current_page_context` | -- | -- | Dev |
| Candidate Handle Add Rejected | Prospect | Rejected | Frontend | Handle blur or submit, availability = unavailable | Job seeker, /candidate/create-profile, handle field availability check fails (taken) | `handle_length`, `current_page_context` | -- | -- | Dev |
| Candidate Previous Resume Select Button Clicked | Prospect | Interaction | Frontend | User clicks Select on a previous resume | Job seeker, /candidate/portfolio/new, selects previously uploaded resume instead of new upload | `action`, `action_value`, `component`, `resume_id`, `resume_file_type` | -- | -- | Dev |
| Candidate Custom Link Delete Button Clicked | Prospect | Interaction | Frontend | User clicks trash icon on an added link | Job seeker, /candidate/portfolio/new, removes a link from Add links section | `action`, `action_value`, `component`, `link_type` | -- | -- | Dev |
| Candidate Custom Link Delete Succeeded | Prospect | Success | Frontend | Link deletion confirmed | Job seeker, /candidate/portfolio/new, link successfully removed | `link_type` | -- | -- | Dev |
| Candidate Custom Link Delete Errored | Prospect | Error | Frontend | Link deletion fails | Job seeker, /candidate/portfolio/new, link removal failed | `link_type`, `error_reason` | -- | -- | Dev |
| Candidate Profile Overview Load Succeeded | Prospect | Success | Frontend | Overview tab finishes loading | Job seeker, /candidate/editor/:portfolioId, overview tab loads with completeness snapshot | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video`, `profile_completeness_rate` | -- | -- | Dev |
| Candidate Profile Tab Switched | Prospect | Interaction | Frontend | User clicks a tab | Job seeker, /candidate/editor/:portfolioId, switches between Overview/Resume/Github/Portfolio tabs | `action_value`, `portfolio_id`, `tab_name`, `component` | -- | -- | Dev |
| Candidate Resume Download Succeeded | Prospect | Success | Frontend | User clicks Download on Resume tab | Job seeker, /candidate/editor/:portfolioId Resume tab, downloads resume | `portfolio_id`, `resume_id` | -- | -- | Dev |
| Candidate Portfolio Publish Button Clicked | Prospect | Interaction | Frontend | User clicks Publish in editor header | Job seeker, /candidate/editor/:portfolioId, initiates portfolio publish | `action_value`, `portfolio_id`, `component` | -- | -- | Dev |
| Candidate Portfolio Publish Succeeded | Prospect | Success | Backend | Backend confirms publish | System confirms portfolio published with completeness snapshot | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video` | -- | -- | Dev |
| Candidate Portfolio Publish Errored | Prospect | Error | Backend | Backend publish error | System fails to publish portfolio | `portfolio_id`, `error_reason`, `error_category` | -- | -- | Dev |
| Candidate Portfolio Unpublish Button Clicked | Prospect | Interaction | Frontend | User clicks Unpublish in editor header | Job seeker, /candidate/editor/:portfolioId, initiates portfolio unpublish | `action_value`, `portfolio_id`, `component` | -- | -- | Dev |
| Candidate Portfolio Unpublish Succeeded | Prospect | Success | Backend | Backend confirms unpublish | System confirms portfolio unpublished | `portfolio_id`, `is_published` | -- | -- | Dev |
| Change Profile Photo Button Clicked | Prospect | Interaction | Frontend | User clicks change photo when photo exists | Job seeker, /candidate/editor/:portfolioId, changes existing profile photo | `action_value`, `portfolio_id` | -- | -- | Dev |
| Candidate Profile Photo Remove Button Clicked | Prospect | Interaction | Frontend | User clicks remove on profile photo | Job seeker, /candidate/editor/:portfolioId, initiates photo removal | `action_value`, `portfolio_id` | -- | -- | Dev |
| Candidate Profile Photo Remove Succeeded | Prospect | Success | Frontend | Photo removal confirmed | Profile photo successfully removed | `portfolio_id` | -- | -- | Dev |
| Candidate Profile Photo Remove Errored | Prospect | Error | Frontend | Photo removal fails | Profile photo removal failed | `portfolio_id`, `error_reason` | -- | -- | Dev |
| Candidate Portfolio Create Button Clicked | Prospect | Interaction | Frontend | User clicks + Create on dashboard | Job seeker, /candidate/dashboard, starts creating new portfolio | `action_value`, `component` | -- | -- | Dev |
| Candidate Portfolio Rename Button Clicked | Prospect | Interaction | Frontend | User clicks Rename in overflow menu | Job seeker, /candidate/dashboard, opens rename modal for a portfolio | `action_value`, `portfolio_id`, `component` | -- | -- | Dev |
| Candidate Portfolio Rename Succeeded | Prospect | Success | Backend | Backend confirms rename (name changed) | System confirms portfolio name changed (only fires if name actually changed) | `portfolio_id`, `new_name_length`, `previous_name_length` | -- | -- | Dev |
| Candidate Portfolio Delete Button Clicked | Prospect | Interaction | Frontend | User clicks Delete in overflow menu | Job seeker, /candidate/dashboard, deletes portfolio (no confirmation dialog) | `action_value`, `portfolio_id`, `component` | -- | -- | Dev |
| Candidate Portfolio Delete Succeeded | Prospect | Success | Backend | Backend confirms delete | System confirms portfolio deleted | `portfolio_id`, `was_published` | -- | -- | Dev |
| Get Started Interview Button Clicked | Prospect | Interaction | Frontend | User clicks Get Started | Interview candidate (anonymous), /interview/:interviewId landing, begins interview flow | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Info Next Button Clicked | Prospect | Interaction | Frontend | User clicks Next on info form | Interview candidate, /interview/:interviewId info step, submits email + optional name; triggers posthog.alias(email) | `action_value`, `interview_id`, `job_id`, `has_first_name`, `has_last_name`, `component` | job | -- | Dev |
| What To Expect Link Clicked | Prospect | Interaction | Frontend | User clicks What to expect expander | Interview candidate, /interview/:interviewId resume step, expands info section (nervousness signal) | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Resume Next Button Clicked | Prospect | Interaction | Frontend | User clicks Next on resume step | Interview candidate, /interview/:interviewId resume step, proceeds with or without resume | `action_value`, `interview_id`, `job_id`, `has_resume`, `agreement_acknowledged`, `component` | job | -- | Dev |
| Candidate Interview Resume Upload Succeeded | Prospect | Success | Frontend | Resume uploaded in interview context | Interview candidate, /interview/:interviewId, resume upload succeeds | `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Resume Upload Errored | Prospect | Error | Frontend | Resume upload fails in interview context | Interview candidate, /interview/:interviewId, resume upload fails | `interview_id`, `job_id`, `error_reason` | job | -- | Dev |
| Open Identity Check Link Clicked | Prospect | Interaction | Frontend | User clicks Open Identity Check | Interview candidate, /interview/:interviewId verify identity step, opens third-party verification | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Refresh Status Button Clicked | Prospect | Interaction | Frontend | User clicks Refresh Status | Interview candidate, /interview/:interviewId verify identity step, manually checks verification status | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Identity Verification Succeeded | Prospect | Success | Backend | Backend confirms identity verified (decision_category = pass) | System confirms third-party identity check passed | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source`, `time_to_verify_seconds` | job | -- | Dev |
| Candidate Interview Identity Verification Errored | Prospect | Error | Backend | Backend identity check inconclusive/unavailable | System reports ambiguous identity check outcome | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source`, `error_reason`, `error_category` | job | -- | Dev |
| Candidate Interview Identity Verification Rejected | Prospect | Rejected | Backend | Backend identity check fails (decision_category = fail) | System reports definitive identity check failure | `interview_id`, `job_id`, `interview_result_id`, `verification_vendor`, `attempt_id`, `decision_category`, `source` | job | -- | Dev |
| Candidate Interview Identity Verification Auto Redirect Succeeded | Prospect | Success | Frontend | Auto-redirect after fresh verification succeeds | Interview candidate, verification timer auto-navigates after fresh check passes | `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Identity Verification Auto Redirect Errored | Prospect | Error | Frontend | Auto-redirect fails | Interview candidate, auto-redirect after verification fails | `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Identity Verification Auto Redirect Rejected | Prospect | Rejected | Frontend | Auto-redirect blocked (canContinue=false) | Interview candidate, auto-redirect blocked because verification did not pass | `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Identity Verification Continue Button Clicked | Prospect | Interaction | Frontend | User clicks Continue after verification | Interview candidate, /interview/:interviewId, manually continues after identity check | `action_value`, `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Privacy Email Link Clicked | Prospect | Interaction | Frontend | User clicks privacy@seekout.ai link | Interview candidate, identity check card, clicks privacy email link | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Persona Privacy Policy Link Clicked | Prospect | Interaction | Frontend | User clicks Persona's privacy policy link | Interview candidate, identity check what-to-expect section, clicks privacy policy link | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Screening Response Next Button Clicked | Prospect | Interaction | Frontend | User clicks Next on screening questions (first pass) | Interview candidate, /interview/:interviewId screening step, submits screening answers (first time through) | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Screening Response Submit Succeeded | Prospect | Success | Frontend | Screening responses saved after API confirms | Interview candidate, screening answers saved successfully with aggregate composition | `interview_id`, `job_id`, `questions_count`, `yes_count`, `no_count`, `optional_context_provided_count`, `required_explanation_count` | job | -- | Dev |
| Candidate Interview Screening Response Save And Review Button Clicked | Prospect | Interaction | Frontend | User clicks Save & Review on screening edit-from-review | Interview candidate, /interview/:interviewId screening step (edit mode from review page), saves edited answers | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Allow Device Access Button Clicked | Prospect | Interaction | Frontend | User clicks Allow Access for camera/mic | Interview candidate, /interview/:interviewId device check, requests browser permissions | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Device Access Grant Succeeded | Prospect | Success | Frontend | Browser grants camera/mic | System confirms browser granted camera and microphone permissions | `interview_id`, `job_id`, `camera_granted`, `mic_granted` | job | -- | Dev |
| Device Access Rejected | Prospect | Rejected | Frontend | Browser denies camera/mic | Browser denied camera/microphone permissions | `interview_id`, `job_id`, `camera_granted`, `mic_granted`, `error_reason` | job | -- | Dev |
| Candidate Interview Start Button Clicked | Prospect | Interaction | Frontend | User clicks Start Interview | Interview candidate, /interview/:interviewId device check, starts interview (enabled after device access) | `action_value`, `interview_id`, `job_id`, `component` | job | -- | Dev |
| Candidate Interview Started | Prospect | Started | Frontend + Backend | Frontend: first question loads; Backend: posthog.alias() at startInterview() | Interview session initialized; frontend capture on first question, backend alias for identity stitching | `interview_id`, `job_id`, `questions_count`, `input_mode`, `has_resume`, `identity_verified`, `is_test_run`, `source` | job | -- | Dev |
| Candidate Interview Question Answer Succeeded | Prospect | Success | Backend | Question answered (save & continue) | Backend confirms answer saved for a question; primary per-question signal | `interview_id`, `job_id`, `question_number`, `question_status`, `input_mode`, `response_duration_seconds`, `ai_conversation_completed` | job | -- | Dev |
| Candidate Interview Question Restart Button Clicked | Prospect | Interaction | Frontend | User clicks Restart on a question | Interview candidate, recording screen, opens restart confirmation modal | `action_value`, `interview_id`, `job_id`, `question_number`, `component` | job | -- | Dev |
| Candidate Interview Question Restart Succeeded | Prospect | Success | Backend | Question restart confirmed | Backend confirms question restarted, recording re-initialized | `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Question Restart Errored | Prospect | Error | Backend | Question restart fails | Backend could not re-initialize question recording | `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category` | job | -- | Dev |
| Candidate Interview Question Skip Button Clicked | Prospect | Interaction | Frontend | User clicks Skip on a question | Interview candidate, recording screen, opens skip confirmation modal | `action_value`, `interview_id`, `job_id`, `question_number`, `component` | job | -- | Dev |
| Candidate Interview Question Skip Succeeded | Prospect | Success | Backend | Skip confirmed | Backend confirms question skipped | `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Question Skip Errored | Prospect | Error | Backend | Skip fails | Backend could not process question skip | `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category` | job | -- | Dev |
| Candidate Interview Question Skip Rejected | Prospect | Rejected | Frontend | User clicks Go back and answer | Interview candidate, skip confirmation modal, cancels skip and returns to recording | `action_value`, `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Screening Response Edit Button Clicked | Prospect | Interaction | Frontend | User clicks Edit on a screening answer | Interview candidate, /interview/:interviewId review page, edits a screening response | `action_value`, `interview_id`, `job_id` | job | -- | Dev |
| Candidate Interview Review Answer Button Clicked | Prospect | Interaction | Frontend | User clicks Answer Question for skipped/unanswered question | Interview candidate, review page, navigates to answer a previously skipped question | `action_value`, `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Retake Question Button Clicked | Prospect | Interaction | Frontend | User clicks retake on an answered question | Interview candidate, review page, navigates to re-record an already answered question | `action_value`, `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Review Answer Expand Clicked | Prospect | Interaction | Frontend | User expands an answer card on review page | Interview candidate, review page, expands answer to see details (fires only on expand) | `interview_id`, `job_id`, `question_number` | job | -- | Dev |
| Candidate Interview Answers Submit Succeeded | Prospect | Success | Frontend | Last question saved, recording phase complete | Interview candidate, recording screen, saves final question marking end of recording phase | `interview_id`, `job_id`, `questions_count` | job | -- | Dev |
| Candidate Interview Answer Retake Succeeded | Prospect | Success | Frontend | Retake from review completes | Interview candidate, returns from retake recording to review page with outcome | `interview_id`, `job_id`, `question_number`, `mode`, `outcome`, `previous_state`, `ai_conversation_completed` | job | -- | Dev |
| Candidate Interview Screening Response Edit Succeeded | Prospect | Success | Frontend | Screening edit from review saved | Interview candidate, returns from screening edit to review with diff properties | `interview_id`, `job_id`, `responses_changed_count`, `context_added_count`, `context_removed_count` | job | -- | Dev |
| Candidate Interview Submit Succeeded | Prospect | Success | Backend | Backend confirms interview submitted | System confirms complete interview submission; headline conversion event | `interview_id`, `job_id`, `interview_result_id`, `questions_count`, `screening_questions_count`, `has_resume`, `identity_verified`, `input_mode`, `total_duration_seconds`, `is_test_run`, `source`, `org_id` | job | -- | Dev |
| Candidate Interview Submit Rejected | Prospect | Rejected | Backend | Backend rejects interview submission | System rejects interview submission due to validation or server error | `interview_id`, `job_id`, `error_reason`, `error_category` | job | -- | Dev |

---

## Property Details

Detailed property definitions for new events. Properties shared across multiple events are listed once.

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | UUID | | Portfolio/profile identifier — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish/Unpublish/Rename/Delete events |
| `has_profile_photo` | boolean | `true` / `false` | Profile photo present — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `resume_id` | UUID or null | | Resume identifier — Candidate Resume Download Succeeded, Candidate Previous Resume Select Button Clicked *(reuses existing v1 property)* |
| `identity_verified` | boolean | `true` / `false` | Whether identity was verified before start — Candidate Interview Started, Candidate Interview Submit Succeeded |
| `interview_id` | UUID | | Anonymous AI interview session identifier (from URL) |
| `interview_result_id` | UUID | | Interview result/submission identifier — Candidate Interview Identity Verification Succeeded/Errored/Rejected, Candidate Interview Submit Succeeded |
| `attempt_id` | string | | Identity verification attempt ID — Candidate Interview Identity Verification Succeeded/Errored/Rejected |
| `decision_category` | enum | `pass`, `fail`, `inconclusive`, `unavailable` | Identity verification outcome category — Candidate Interview Identity Verification Succeeded/Errored/Rejected |
| `is_published` | boolean | `true` / `false` | Profile published state — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded / Unpublish Succeeded |
| `skills_count` | number | | Skills on the profile — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `journey_count` | number | | Journey/timeline entries — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `has_description` | boolean | `true` / `false` | Summary present — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `profile_completeness_rate` | number | `0`–`100` | Percentage of completeness steps filled — Candidate Profile Overview Load Succeeded |
| `has_handle` | boolean | `true` / `false` | Handle claimed — Candidate Profile Created |
| `handle_length` | number or null | | Handle character count — Candidate Handle Add Succeeded, Candidate Handle Add Rejected |
| `tab_name` | enum | `overview`, `resume`, `github`, `portfolio` | Editor tab — Candidate Profile Tab Switched |
| `new_name_length` | number | | New portfolio name length — Candidate Portfolio Rename Succeeded |
| `previous_name_length` | number | | Previous portfolio name length — Candidate Portfolio Rename Succeeded |
| `was_published` | boolean | `true` / `false` | Whether a deleted portfolio was published — Candidate Portfolio Delete Succeeded |
| `start_source` | enum | `interview_link`, `email_invite`, `job_board`, `direct` (+ existing `create_job_button`) | How a candidate reached the interview — Page Viewed (interview_landing) |
| `has_first_name` | boolean | `true` / `false` | Optional name field filled — Candidate Interview Info Next Button Clicked |
| `has_last_name` | boolean | `true` / `false` | Optional name field filled — Candidate Interview Info Next Button Clicked |
| `agreement_acknowledged` | boolean | `true` | Recording/data agreement accepted — Candidate Interview Resume Next Button Clicked. Always true (gated) — kept for auditability |
| `verification_vendor` | string | `persona` | Identity vendor — Candidate Interview Identity Verification Succeeded / Errored / Rejected |
| `time_to_verify_seconds` | number or null | | Seconds from Open Identity Check to verification — Candidate Interview Identity Verification Succeeded |
| `camera_granted` | boolean | `true` / `false` | Camera permission — Device Access Grant Succeeded / Rejected |
| `mic_granted` | boolean | `true` / `false` | Mic permission — Device Access Grant Succeeded / Rejected |
| `input_mode` | enum | `voice`, `text` | *(reuses existing enum)* Interview modality — Candidate Interview Started, Candidate Interview Question Answer Succeeded, Candidate Interview Submit Succeeded |
| `input_method` | string | | How the profile was built (replaces Build Profile Snapshot) — Candidate Profile Created |
| `question_status` | enum | `answered`, `answered_restarted`, `skipped` | Terminal status of a question — Candidate Interview Question Answer Succeeded |
| `question_number` | number | `1`–`N` | *(reuses existing property)* Question position — interview question events |
| `questions_count` | number | | *(reuses existing property)* Total interview questions — Candidate Interview Started, Candidate Interview Answers Submit Succeeded, Candidate Interview Submit Succeeded |
| `response_duration_seconds` | number or null | | Spoken duration on a question — Candidate Interview Question Answer Succeeded |
| `ai_conversation_completed` | boolean | `true` / `false` | Whether the AI conversation completed for this question — Candidate Interview Question Answer Succeeded, Candidate Interview Answer Retake Succeeded |
| `yes_count` | number | | Yes answers on screening — Candidate Interview Screening Response Submit Succeeded |
| `no_count` | number | | No answers on screening — Candidate Interview Screening Response Submit Succeeded |
| `optional_context_provided_count` | number | | Yes answers with optional context filled — Candidate Interview Screening Response Submit Succeeded |
| `required_explanation_count` | number | | No answers (mandatory explanation) — Candidate Interview Screening Response Submit Succeeded |
| `screening_questions_count` | number | | Screening question count — Candidate Interview Submit Succeeded |
| `total_duration_seconds` | number or null | | Full interview duration — Candidate Interview Submit Succeeded |
| `is_test_run` | boolean | `true` / `false` | Whether the interview is a test run — Candidate Interview Started, Candidate Interview Submit Succeeded |
| `mode` | enum | `retake` | Edit-mode indicator for retake flows from review page — Candidate Interview Answer Retake Succeeded |
| `outcome` | enum | `answered`, `skipped` | Retake outcome — what happened to the question — Candidate Interview Answer Retake Succeeded |
| `previous_state` | string | | Previous answer state before retake (e.g. `answered`, `skipped`) — Candidate Interview Answer Retake Succeeded |
| `responses_changed_count` | number | | Number of screening responses changed in edit — Candidate Interview Screening Response Edit Succeeded |
| `context_added_count` | number | | Number of screening contexts added in edit — Candidate Interview Screening Response Edit Succeeded |
| `context_removed_count` | number | | Number of screening contexts removed in edit — Candidate Interview Screening Response Edit Succeeded |
| `resume_page_count` | number | | Pages in the uploaded resume — Candidate Profile Created |
| `org_id` | string | | Organization ID — Candidate Interview Submit Succeeded |
| `source` | string | `webhook`, `poll` (identity verification context); traffic source enum (interview context) | Used in two contexts: (1) identity verification backend events to indicate whether the result came via webhook or polling; (2) Candidate Interview Started / Submit Succeeded to carry traffic source |
| `link_type` | string | `github`, `linkedin`, `portfolio`, `personal`, etc. | Type/platform of the link — Candidate Custom Link Delete Button Clicked, Candidate Custom Link Delete Succeeded, Candidate Custom Link Delete Errored |
| `resume_file_type` | string | `docx`, `pdf`, `doc`, `txt` | File type of the selected resume — Candidate Previous Resume Select Button Clicked |

**Property Dictionary updates needed on merge:**

- `error_category` — append values: `vendor`, `mismatch` (identity), and confirm `validation`, `server`, `network`, `timeout` already exist.
- `start_source` — extend allowed values with `interview_link`, `email_invite`, `job_board`, `direct`.
- `entry_point` — extend allowed values with `interview`.
- `entity_type` — add values: `interview`, `identity_check`, `screening_response`, `interview_question`, `device_check`, `candidate_profile`.
- `source` — document dual usage: traffic source (interview context) and backend delivery mechanism (`webhook` / `poll` in identity verification context).

---

## Event Specifications

Detailed per-event specs organized by Part. All property tables include only the properties specific to that event; standard context properties (`current_page_context`, `previous_page_context`, `entity_type`, `helix_session_id`) follow the global schema.

---

# Part A — Profile handle (`/candidate/create-profile`)

The create-profile page has a "Your handle (optional)" field with a live availability check. Handle events fire on blur (if value changed) or on submit click (if handle is dirty and not yet blur-fired). The specific event depends on the most recent availability API response.

### Candidate Handle Add Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Handle Add Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Handle input blur (if value changed) or "Build my AI profile" click (if handle is dirty and not yet blur-fired), AND the most recent availability check returned available |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `handle_length` | number | e.g. `8` | Character count of the handle. Never capture the handle string itself. |
| `current_page_context` | string | `candidate_create_profile` | Page |

---

### Candidate Handle Add Rejected

| Field | Value |
|---|---|
| **Event** | `Candidate Handle Add Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Handle input blur (if value changed) or "Build my AI profile" click (if handle is dirty and not yet blur-fired), AND the most recent availability check returned unavailable (taken) |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `handle_length` | number | e.g. `8` | Character count of the attempted handle |
| `current_page_context` | string | `candidate_create_profile` | Page |

---

### Candidate Previous Resume Select Button Clicked

User clicks "Select" on a previously uploaded resume in the "Or use a previous resume" list on the Build your profile page (`/candidate/portfolio/new`). Distinct from the new-upload flow — this reuses an already-uploaded file.

| Field | Value |
|---|---|
| **Event** | `Candidate Previous Resume Select Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks "Select" on a previously uploaded resume in the "Or use a previous resume" list |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `select` | Exact button label |
| `component` | string | `create_profile_resume_section` | Resume section on Build your profile page |
| `current_page_context` | string | `candidate_create_portfolio` | |
| `entity_type` | string | `candidate_profile` | |
| `resume_id` | string (UUID) | | ID of the selected resume |
| `resume_file_type` | string | `docx`, `pdf`, `doc`, `txt` | File type of the selected resume |

---

### Candidate Custom Link Delete Button Clicked

User clicks the trash icon on an added link in the "Add links" section on the Build your profile page (`/candidate/portfolio/new`).

| Field | Value |
|---|---|
| **Event** | `Candidate Custom Link Delete Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks the trash icon on an added link in the "Add links" section |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `delete` | Trash icon action |
| `component` | string | `create_profile_add_links_section` | "Add links" section on Build your profile page |
| `current_page_context` | string | `candidate_create_portfolio` | |
| `entity_type` | string | `candidate_profile` | |
| `link_type` | string | `github`, `linkedin`, `portfolio`, `personal`, etc. | Type/platform of the link being deleted |

---

### Candidate Custom Link Delete Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Custom Link Delete Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Link deletion confirmed |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `link_type` | string | `github`, `linkedin`, `portfolio`, `personal`, etc. | Type/platform of the link removed |

---

### Candidate Custom Link Delete Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Custom Link Delete Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Link deletion fails |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `link_type` | string | `github`, `linkedin`, `portfolio`, `personal`, etc. | Type/platform of the link that failed to remove |
| `error_reason` | string | | Truncated to 256 chars |

---

# Part B — Profile editor / overview (`/candidate/editor/:portfolioId`)

The editor has an Overview / Resume / Github / Portfolio tab bar, a Download action on the Resume tab, a Publish / Unpublish toggle in the header, and profile photo management. v1 deferred all editor events to v2.

### Candidate Profile Overview Load Succeeded

A content-aware load event for the overview tab — separate from the generic `Page Viewed`, because it carries the profile's completeness state at load time.

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Overview Load Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Overview tab finishes loading on the editor page |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | Which profile/portfolio is open |
| `is_published` | boolean | `true` / `false` | Is the profile currently published? |
| `skills_count` | number | e.g. `10` | Number of skills shown |
| `journey_count` | number | e.g. `3` | Number of journey/timeline entries |
| `has_profile_photo` | boolean | `true` / `false` | Profile photo present? |
| `has_description` | boolean | `true` / `false` | Summary/description present? |
| `has_intro_video` | boolean | `true` / `false` | Intro video recorded? (the "Record an introduction video" card) |
| `profile_completeness_rate` | number | `0`–`100` | Percentage of completeness steps filled (e.g. 3/5 = 60). Steps: skills > 0, journey > 0, profile photo, description, intro video. |
| `current_page_context` | string | `candidate_editor_overview` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### Candidate Profile Tab Switched

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Tab Switched` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Overview / Resume / Github / Portfolio tab |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `overview_tab`, `resume_tab`, `github_tab`, `portfolio_tab` | Exact tab clicked |
| `portfolio_id` | string (UUID) | | |
| `tab_name` | enum | `overview`, `resume`, `github`, `portfolio` | Destination tab |
| `current_page_context` | string | `candidate_editor` | Page |
| `component` | string | `editor_tab_bar` | UI location |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Resume Download Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Resume Download Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | User clicks "Download" on the Resume tab |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `resume_id` | string (UUID) or null | | Resume being downloaded |
| `current_page_context` | string | `candidate_editor_resume` | Page |
| `component` | string | `editor_resume_tab` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Publish Button Clicked

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Publish Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Publish in the editor header |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `publish_button` | |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor` | |
| `component` | string | `editor_header_actions` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Publish Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Publish Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms publish |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `is_published` | boolean | `true` | Confirmed published state |
| `skills_count` | number | | Snapshot of completeness at publish time |
| `journey_count` | number | | |
| `has_profile_photo` | boolean | | |
| `has_description` | boolean | | |
| `has_intro_video` | boolean | | |

---

### Candidate Portfolio Publish Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Publish Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Backend publish error |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network` | |

---

### Candidate Portfolio Unpublish Button Clicked

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Unpublish Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Unpublish in the editor header |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `unpublish_button` | |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor` | |
| `component` | string | `editor_header_actions` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Unpublish Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Unpublish Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms unpublish |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `is_published` | boolean | `false` | Confirmed unpublished state |

---

### Change Profile Photo Button Clicked

| Field | Value |
|---|---|
| **Event** | `Change Profile Photo Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks change photo when a photo already exists |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action_value` | string | `change_profile_photo` | Button label |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor_overview` | Page |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Profile Photo Remove Button Clicked

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Photo Remove Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks remove on the profile photo |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action_value` | string | `remove_profile_photo` | Button label |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor_overview` | Page |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Profile Photo Remove Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Photo Remove Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Photo removal confirmed |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |

---

### Candidate Profile Photo Remove Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Photo Remove Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Photo removal fails |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `error_reason` | string | | Truncated to 256 chars |

---

# Part C — Dashboard: portfolio management (`/candidate/dashboard`)

The dashboard lists portfolios, has a header **+ Create** button, and each portfolio card has an overflow menu with **Rename Portfolio** and **Delete**. Each portfolio has a unique `portfolio_id`.

### Candidate Portfolio Create Button Clicked

User clicks the **+ Create** button in the dashboard header to start creating another candidate portfolio.

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Create Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks + Create in the dashboard header |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `create_button` | Exact UI action clicked |
| `current_page_context` | string | `candidate_dashboard` | |
| `previous_page_context` | string or null | snake_case or null | Previous page context, if available |
| `component` | string | `candidate_dashboard_header` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Rename Button Clicked

Opens the rename modal.

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Rename Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Rename in the portfolio card overflow menu |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `rename_portfolio` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Rename Succeeded

**Only fires when the name actually changed.** If the user clicks Save without editing, this event does **not** fire.

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Rename Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms rename (name changed) |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `new_name_length` | number | e.g. `42` | Character count of the new name (length only — not the name itself) |
| `previous_name_length` | number | e.g. `60` | Character count of the previous name |

---

### Candidate Portfolio Delete Button Clicked

The delete menu item **deletes immediately with no confirmation dialog**. The click is captured as intent so it can be paired with the backend outcome.

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Delete Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Delete in the portfolio card overflow menu |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `delete` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

---

### Candidate Portfolio Delete Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Portfolio Delete Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms delete |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `was_published` | boolean | `true` / `false` | Whether the deleted portfolio was published |

> **Gap flagged:** Delete has no confirmation step today, so there is no way to measure accidental deletes or a cancel rate. If a confirmation modal is added later, add a `Candidate Portfolio Delete Confirmed` / `Candidate Portfolio Delete Cancelled` pair.

---

# Part D — Anonymous AI screening interview (`/interview/:interviewId`)

A candidate opens an interview link and proceeds through: landing → your information → upload resume → verify identity → screening questions → device check → interview (per-question voice answers) → review & submit → submitted.

**`job_id` note:** `job_id` is null on most frontend events in Part D due to privacy — the job ID is not exposed in the public interview API. It is available on backend events. This is noted here once rather than on each event.

All Part D events carry `interview_id`, `job_id`, and (where indicated) the `job` group. The `job` group is keyed on the job posting being screened for and works even while the candidate is anonymous.

**Redis dedup guard:** `Interview Link Open Succeeded` has a 30-minute TTL Redis dedup guard that prevents React Query refetch duplicates from firing the event more than once per session.

---

## D1 — Landing page

### Get Started Interview Button Clicked

| Field | Value |
|---|---|
| **Event** | `Get Started Interview Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Get Started on the interview landing page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `get_started_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend (not in public API) |
| `current_page_context` | string | `candidate_interview_landing` | |
| `component` | string | `interview_landing_ready_card` | |
| `entity_type` | string | `interview` | |

> **Note on `Page Viewed`:** the existing event fires with `current_page_context = candidate_interview_landing` and `start_source` (new value: `interview_link`, `email_invite`, `job_board`, `direct`). No new event is required.

---

## D2 — Your information

### Candidate Interview Info Next Button Clicked

Fires on "Next". Email is mandatory; first/last names optional. **Do not** put name or email values in properties — only booleans. Email is captured via `posthog.alias(email)` on the person profile, not as an event property.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Info Next Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Next on the info form; triggers posthog.alias(email) |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `has_first_name` | boolean | `true` / `false` | Optional field filled? |
| `has_last_name` | boolean | `true` / `false` | Optional field filled? |
| `current_page_context` | string | `interview_candidate_info` | |
| `component` | string | `interview_candidate_info_form` | |
| `entity_type` | string | `interview` | |

---

## D3 — Upload resume

### What To Expect Link Clicked

The "What to expect" expander. Captures nervousness signal / interest in process.

| Field | Value |
|---|---|
| **Event** | `What To Expect Link Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks What to expect expander |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `what_to_expect` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_upload_resume` | |
| `component` | string | `interview_ai_guided_card` | |
| `entity_type` | string | `interview` | |

---

### Candidate Interview Resume Next Button Clicked

Fires on "Next". Captures whether the candidate proceeded with or without a resume (both allowed).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Resume Next Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Next on the resume step |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `has_resume` | boolean | `true` / `false` | Did they upload a resume before continuing? |
| `agreement_acknowledged` | boolean | `true` | Always true (gated) — kept for auditability |
| `current_page_context` | string | `interview_upload_resume` | |
| `component` | string | `interview_upload_resume_footer` | |
| `entity_type` | string | `interview` | |

---

### Candidate Interview Resume Upload Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Resume Upload Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Resume uploaded successfully in interview context |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |

---

### Candidate Interview Resume Upload Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Resume Upload Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Resume upload fails in interview context |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `error_reason` | string | | Truncated to 256 chars |

---

## D4 — Verify identity

### Open Identity Check Link Clicked

| Field | Value |
|---|---|
| **Event** | `Open Identity Check Link Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Open Identity Check to launch third-party verification |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `open_identity_check` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_card` | |
| `entity_type` | string | `identity_check` | |

---

### Refresh Status Button Clicked

| Field | Value |
|---|---|
| **Event** | `Refresh Status Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Refresh Status to manually check verification status |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `refresh_status_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_card` | |
| `entity_type` | string | `identity_check` | |

---

### Candidate Interview Identity Verification Succeeded

Backend confirmation that the third-party (Persona) identity check passed. Fires when `decision_category = pass`. Identity verification events fire with `candidate_id` as `distinct_id` (no HTTP context); they rely on the email alias from D2 to join the funnel.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms identity verified (decision_category = pass) |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `interview_result_id` | string (UUID) | | Interview result/submission identifier |
| `verification_vendor` | string | `persona` | Third-party identity vendor |
| `attempt_id` | string | | Identity verification attempt ID |
| `decision_category` | enum | `pass` | Identity verification outcome |
| `source` | string | `webhook`, `poll` | Whether result came via webhook or polling |
| `time_to_verify_seconds` | number or null | | Seconds from Open Identity Check to verification |

---

### Candidate Interview Identity Verification Errored

Backend reports ambiguous identity check outcome (inconclusive or unavailable).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Backend identity check inconclusive/unavailable |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `interview_result_id` | string (UUID) | | Interview result/submission identifier |
| `verification_vendor` | string | `persona` | |
| `attempt_id` | string | | Identity verification attempt ID |
| `decision_category` | enum | `inconclusive`, `unavailable` | Ambiguous outcome |
| `source` | string | `webhook`, `poll` | Whether result came via webhook or polling |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `vendor`, `timeout`, `mismatch`, `server` | Why verification failed |

---

### Candidate Interview Identity Verification Rejected

Backend reports definitive identity check failure.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Backend identity check fails (decision_category = fail) |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `interview_result_id` | string (UUID) | | Interview result/submission identifier |
| `verification_vendor` | string | `persona` | |
| `attempt_id` | string | | Identity verification attempt ID |
| `decision_category` | enum | `fail` | Definitive failure |
| `source` | string | `webhook`, `poll` | Whether result came via webhook or polling |

---

### Candidate Interview Identity Verification Auto Redirect Succeeded

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Auto Redirect Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Auto-redirect timer fires and verification status allows continuation |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |

---

### Candidate Interview Identity Verification Auto Redirect Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Auto Redirect Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Auto-redirect timer fires but redirect fails |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |

---

### Candidate Interview Identity Verification Auto Redirect Rejected

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Auto Redirect Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Auto-redirect blocked (canContinue=false) |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |

---

### Candidate Interview Identity Verification Continue Button Clicked

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Identity Verification Continue Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Continue after identity verification |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `continue` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_verify_identity` | |
| `entity_type` | string | `identity_check` | |

---

### Candidate Interview Privacy Email Link Clicked

User clicks the "privacy@seekout.ai" link in the identity check card.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Privacy Email Link Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks privacy@seekout.ai link |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `privacy@seekout.ai` | Exact link text |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_card` | |
| `entity_type` | string | `identity_check` | |

---

### Candidate Interview Persona Privacy Policy Link Clicked

User clicks the "Persona's privacy policy" link in the "What to expect" section.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Persona Privacy Policy Link Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Persona's privacy policy link |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `personas_privacy_policy` | Exact link text in snake_case |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_what_to_expect` | "What to expect" section within identity check card |
| `entity_type` | string | `identity_check` | |

---

## D5 — Screening questions

These are the recruiter's Yes/No screening questions (distinct from the AI voice interview questions in D7). On Yes, a context box is **optional**; on No, an explanation is **mandatory**.

### Candidate Interview Screening Response Next Button Clicked

Fires on "Next" on the first pass through screening (not on save-and-review from edit mode).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Screening Response Next Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Next on screening questions (first pass) |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_screening_questions` | |
| `component` | string | `interview_screening_questions_form` | |
| `entity_type` | string | `screening_response` | |

---

### Candidate Interview Screening Response Submit Succeeded

Fires after the API confirms screening answers saved. Carries aggregate answer composition.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Screening Response Submit Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Screening responses saved after API confirms |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `questions_count` | number | e.g. `3` | Total screening questions shown |
| `yes_count` | number | | Number answered Yes |
| `no_count` | number | | Number answered No |
| `optional_context_provided_count` | number | | # of Yes answers where the optional context box was filled |
| `required_explanation_count` | number | | # of No answers (each requires a mandatory explanation) |

---

### Candidate Interview Screening Response Save And Review Button Clicked

Fires when the user clicks Save & Review from the screening step when returning from the review page to edit answers.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Screening Response Save And Review Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Save & Review on screening edit-from-review |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `save_and_review` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_screening_questions` | |
| `component` | string | `interview_screening_questions_form` | |
| `entity_type` | string | `screening_response` | |

---

## D6 — Device check & interview start

### Allow Device Access Button Clicked

| Field | Value |
|---|---|
| **Event** | `Allow Device Access Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Allow Access for camera/mic |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `allow_access_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_device_check` | |
| `component` | string | `device_check_card` | |
| `entity_type` | string | `device_check` | |

---

### Device Access Grant Succeeded

| Field | Value |
|---|---|
| **Event** | `Device Access Grant Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Browser grants camera and microphone permissions |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `camera_granted` | boolean | `true` / `false` | Camera permission result |
| `mic_granted` | boolean | `true` / `false` | Microphone permission result |

---

### Device Access Rejected

| Field | Value |
|---|---|
| **Event** | `Device Access Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Browser denies camera/microphone permissions |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `camera_granted` | boolean | `true` / `false` | Camera permission result |
| `mic_granted` | boolean | `true` / `false` | Microphone permission result |
| `error_reason` | string | | Permission denial reason, if any |

---

### Candidate Interview Start Button Clicked

Enabled only after device access is granted.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Start Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Start Interview (enabled only after device access granted) |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `start_interview_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_device_check` | |
| `component` | string | `device_check_footer` | |
| `entity_type` | string | `interview` | |

---

### Candidate Interview Started

Dual-fire event. Frontend fires on first question load; backend fires `posthog.alias(candidate_id, anon_id)` at `startInterview()` for identity stitching.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Started` |
| **Area** | Prospect |
| **Type** | Started |
| **Trigger** | Frontend: first question loads; Backend: posthog.alias() at startInterview() |
| **Source** | Frontend + Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend; null on frontend |
| `questions_count` | number | e.g. `4` | Number of AI interview questions |
| `input_mode` | enum | `voice`, `text` | Interview modality |
| `has_resume` | boolean | `true` / `false` | Did the candidate upload a resume? |
| `identity_verified` | boolean | `true` / `false` | Was identity verified before start? |
| `is_test_run` | boolean | `true` / `false` | Whether the interview is a test run |
| `source` | string | Traffic source (e.g. `interview_link`) | How the candidate arrived (from `?source=` param or referrer) |

---

## D7 — Per-question interview

**Note:** Skip and Restart Succeeded events are now backend only and are suppressed in edit/retake mode (`mode='retake'`).

### Candidate Interview Question Answer Succeeded

Fires once per question when the candidate saves their answer. This is the primary per-question signal and powers stacked bar charts by `question_status`. Replaces the previous `Candidate Interview Question Resolve Succeeded` event.

**Triggers:**
- Save & continue → `question_status = answered`
- Save & continue after restarting → `question_status = answered_restarted`

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Answer Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Question answered (save & continue); backend confirms answer saved |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `question_number` | number | `1`–`N` | Position of the question |
| `question_status` | enum | `answered`, `answered_restarted` | Terminal answer status of this question |
| `input_mode` | enum | `voice`, `text` | |
| `response_duration_seconds` | number or null | | Spoken/typed duration |
| `ai_conversation_completed` | boolean | `true` / `false` | Whether the AI conversation completed for this question |

---

### Candidate Interview Question Restart Button Clicked

Clicking "Restart" opens the confirm modal.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Restart Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Restart on a question, opening restart confirmation modal |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `restart` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_recording` | |
| `component` | string | `interview_recording_footer` | |
| `entity_type` | string | `interview_question` | |

---

### Candidate Interview Question Restart Succeeded

Backend confirmation that question restart was successfully re-initialized.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Restart Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms question restarted, recording re-initialized |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `question_number` | number | `1`–`N` | |

---

### Candidate Interview Question Restart Errored

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Restart Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Backend could not re-initialize question recording |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `question_number` | number | `1`–`N` | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network` | |

---

### Candidate Interview Question Skip Button Clicked

Clicking "Skip" opens the skip confirmation modal.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Skip Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Skip on a question, opening skip confirmation modal |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `skip` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_recording` | |
| `component` | string | `interview_recording_footer` | |
| `entity_type` | string | `interview_question` | |

---

### Candidate Interview Question Skip Succeeded

Backend only. Suppressed in retake mode (`mode='retake'`).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Skip Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms question skipped |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `question_number` | number | `1`–`N` | |

---

### Candidate Interview Question Skip Errored

Backend fires on ValueError when skip cannot be processed.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Skip Errored` |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Backend could not process question skip |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `question_number` | number | `1`–`N` | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server` | |

---

### Candidate Interview Question Skip Rejected

The candidate clicks "Go back and answer" in the skip modal.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Question Skip Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | User clicks Go back and answer in the skip confirmation modal |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `go_back_and_answer` | Exact button label |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_recording` | |
| `component` | string | `skip_question_modal` | |
| `entity_type` | string | `interview_question` | |

---

## D8 — Review & submit

### Candidate Interview Screening Response Edit Button Clicked

The "Edit" link next to a screening answer on the review page.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Screening Response Edit Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Edit on a screening answer on the review page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `edit` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `current_page_context` | string | `interview_review` | |
| `entity_type` | string | `screening_response` | |

---

### Candidate Interview Review Answer Button Clicked

For a skipped/missing question on the review page, the "Answer question" button.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Review Answer Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks Answer Question for a skipped/unanswered question on the review page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `answer_question` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_review` | |
| `entity_type` | string | `interview_question` | |

---

### Candidate Interview Retake Question Button Clicked

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Retake Question Button Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User clicks retake on an already-answered question on the review page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `retake` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_review` | |
| `entity_type` | string | `interview_question` | |

---

### Candidate Interview Review Answer Expand Clicked

Fires only on expand (not on collapse).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Review Answer Expand Clicked` |
| **Area** | Prospect |
| **Type** | Interaction |
| **Trigger** | User expands an answer card on the review page (fires only on expand) |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `current_page_context` | string | `interview_review` | |
| `entity_type` | string | `interview_question` | |

---

### Candidate Interview Answers Submit Succeeded

Fires when the last question is saved, marking the end of the recording phase. Separate from `Candidate Interview Submit Succeeded` (which fires after full backend submission).

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Answers Submit Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Last question saved, recording phase complete |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `questions_count` | number | | Total interview questions |

---

### Candidate Interview Answer Retake Succeeded

Fires when the candidate returns from a retake recording to the review page.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Answer Retake Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Retake from review completes and candidate returns to review page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `question_number` | number | `1`–`N` | |
| `mode` | enum | `retake` | Edit-mode indicator |
| `outcome` | enum | `answered`, `skipped` | What happened to the question |
| `previous_state` | string | `answered`, `skipped` | Answer state before retake |
| `ai_conversation_completed` | boolean | `true` / `false` | Whether AI conversation completed |

---

### Candidate Interview Screening Response Edit Succeeded

Fires when screening edit from review is saved. Carries diff properties.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Screening Response Edit Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Screening edit from review saved, candidate returns to review page |
| **Source** | Frontend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) or null | | null on frontend |
| `responses_changed_count` | number | | Number of screening responses changed in edit |
| `context_added_count` | number | | Number of screening contexts added in edit |
| `context_removed_count` | number | | Number of screening contexts removed in edit |

---

### Candidate Interview Submit Succeeded

The headline conversion event for the entire interview flow.

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Submit Succeeded` |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Backend confirms complete interview submitted |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `interview_result_id` | string (UUID) | | Interview result/submission identifier |
| `questions_count` | number | | Total interview questions |
| `screening_questions_count` | number | | Total screening questions |
| `has_resume` | boolean | `true` / `false` | |
| `identity_verified` | boolean | `true` / `false` | |
| `input_mode` | enum | `voice`, `text` | |
| `total_duration_seconds` | number or null | | End-to-end interview duration |
| `is_test_run` | boolean | `true` / `false` | Whether the interview is a test run |
| `source` | string | Traffic source | How the candidate arrived |
| `org_id` | string | | Organization ID |

---

### Candidate Interview Submit Rejected

| Field | Value |
|---|---|
| **Event** | `Candidate Interview Submit Rejected` |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Backend rejects interview submission due to validation or server error |
| **Source** | Backend |
| **Group** | job |

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | Available on backend |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network`, `timeout` | |

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Candidate Handle Add | Job seeker handle add action | Candidate Handle Add Succeeded, Candidate Handle Add Rejected |
| Candidate Previous Resume Select Button | Previous resume select CTA | Candidate Previous Resume Select Button Clicked |
| Candidate Custom Link Delete | Custom link deletion lifecycle | Candidate Custom Link Delete Succeeded, Candidate Custom Link Delete Errored |
| Candidate Custom Link Delete Button | Custom link delete CTA | Candidate Custom Link Delete Button Clicked |
| Candidate Profile Overview Load | Profile overview load state | Candidate Profile Overview Load Succeeded |
| Candidate Profile Tab | Editor tab navigation | Candidate Profile Tab Switched |
| Candidate Resume Download | Resume download action | Candidate Resume Download Succeeded |
| Candidate Portfolio Publish | Portfolio publish lifecycle | Candidate Portfolio Publish Succeeded, Candidate Portfolio Publish Errored |
| Candidate Portfolio Publish Button | Portfolio publish CTA | Candidate Portfolio Publish Button Clicked |
| Candidate Portfolio Unpublish | Portfolio unpublish lifecycle | Candidate Portfolio Unpublish Succeeded |
| Candidate Portfolio Unpublish Button | Portfolio unpublish CTA | Candidate Portfolio Unpublish Button Clicked |
| Change Profile Photo Button | Change profile photo CTA | Change Profile Photo Button Clicked |
| Candidate Profile Photo Remove | Profile photo removal lifecycle | Candidate Profile Photo Remove Succeeded, Candidate Profile Photo Remove Errored |
| Candidate Profile Photo Remove Button | Profile photo remove CTA | Candidate Profile Photo Remove Button Clicked |
| Candidate Portfolio Create Button | Portfolio creation CTA on dashboard | Candidate Portfolio Create Button Clicked |
| Candidate Portfolio Rename | Portfolio rename lifecycle | Candidate Portfolio Rename Succeeded |
| Candidate Portfolio Rename Button | Portfolio rename CTA | Candidate Portfolio Rename Button Clicked |
| Candidate Portfolio Delete | Portfolio delete lifecycle | Candidate Portfolio Delete Succeeded |
| Candidate Portfolio Delete Button | Portfolio delete CTA | Candidate Portfolio Delete Button Clicked |
| Get Started Interview Button | Interview landing CTA | Get Started Interview Button Clicked |
| Candidate Interview Info Next Button | Interview info form CTA | Candidate Interview Info Next Button Clicked |
| What To Expect Link | Interview info expander | What To Expect Link Clicked |
| Candidate Interview Resume Next Button | Resume step CTA | Candidate Interview Resume Next Button Clicked |
| Candidate Interview Resume Upload | Resume upload lifecycle in interview | Candidate Interview Resume Upload Succeeded, Candidate Interview Resume Upload Errored |
| Open Identity Check Link | Open identity check CTA | Open Identity Check Link Clicked |
| Refresh Status Button | Refresh identity check status CTA | Refresh Status Button Clicked |
| Candidate Interview Identity Verification | Third-party identity verification lifecycle | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected |
| Candidate Interview Identity Verification Auto Redirect | Auto-redirect after verification | Candidate Interview Identity Verification Auto Redirect Succeeded, Candidate Interview Identity Verification Auto Redirect Errored, Candidate Interview Identity Verification Auto Redirect Rejected |
| Candidate Interview Identity Verification Continue Button | Continue after verification CTA | Candidate Interview Identity Verification Continue Button Clicked |
| Candidate Interview Privacy Email Link | Privacy email link | Candidate Interview Privacy Email Link Clicked |
| Candidate Interview Persona Privacy Policy Link | Persona privacy policy link | Candidate Interview Persona Privacy Policy Link Clicked |
| Candidate Interview Screening Response Next Button | Screening next CTA | Candidate Interview Screening Response Next Button Clicked |
| Candidate Interview Screening Response Submit | Screening response submission | Candidate Interview Screening Response Submit Succeeded |
| Candidate Interview Screening Response Save And Review Button | Screening save-and-review CTA | Candidate Interview Screening Response Save And Review Button Clicked |
| Allow Device Access Button | Camera/mic permission CTA | Allow Device Access Button Clicked |
| Device Access Grant | Camera/mic grant result | Device Access Grant Succeeded |
| Device Access | Camera/mic permission rejection | Device Access Rejected |
| Candidate Interview Start Button | Start interview CTA | Candidate Interview Start Button Clicked |
| Candidate Interview | Anonymous AI screening interview session | Candidate Interview Started |
| Candidate Interview Question Answer | Per-question answer result | Candidate Interview Question Answer Succeeded |
| Candidate Interview Question Restart | Question restart lifecycle | Candidate Interview Question Restart Succeeded, Candidate Interview Question Restart Errored |
| Candidate Interview Question Restart Button | Question restart CTA | Candidate Interview Question Restart Button Clicked |
| Candidate Interview Question Skip | Question skip lifecycle | Candidate Interview Question Skip Succeeded, Candidate Interview Question Skip Errored, Candidate Interview Question Skip Rejected |
| Candidate Interview Question Skip Button | Question skip CTA | Candidate Interview Question Skip Button Clicked |
| Candidate Interview Screening Response Edit Button | Screening answer edit link | Candidate Interview Screening Response Edit Button Clicked |
| Candidate Interview Review Answer Button | Answer skipped question on review | Candidate Interview Review Answer Button Clicked |
| Candidate Interview Retake Question Button | Retake question on review | Candidate Interview Retake Question Button Clicked |
| Candidate Interview Review Answer Expand | Answer card expand on review | Candidate Interview Review Answer Expand Clicked |
| Candidate Interview Answers Submit | End-of-recording submission | Candidate Interview Answers Submit Succeeded |
| Candidate Interview Answer Retake | Retake completion result | Candidate Interview Answer Retake Succeeded |
| Candidate Interview Screening Response Edit | Screening edit completion | Candidate Interview Screening Response Edit Succeeded |
| Candidate Interview Submit | Full interview submission lifecycle | Candidate Interview Submit Succeeded, Candidate Interview Submit Rejected |

## Catalog Updates

New events from this plan to add to `docs/helix/event-catalog.md` (do **not** merge automatically — run `/merge-tracking-plan`):

**Part A — handle and profile create (modifications + new events):**
- [ ] `Candidate Profile Created` (Backend) — add `has_handle`, `input_method`, `resume_page_count`
- [ ] `Account Created` — moved from Frontend to Backend; `entry_point = interview` now hardcoded on claim path
- [ ] `Candidate Handle Add Succeeded` → Prospect
- [ ] `Candidate Handle Add Rejected` → Prospect
- [ ] `Candidate Previous Resume Select Button Clicked` → Prospect
- [ ] `Candidate Custom Link Delete Button Clicked` → Prospect
- [ ] `Candidate Custom Link Delete Succeeded` → Prospect
- [ ] `Candidate Custom Link Delete Errored` → Prospect

**Part B — Prospect (editor):**
- [ ] Candidate Profile Overview Load Succeeded
- [ ] Candidate Profile Tab Switched
- [ ] Candidate Resume Download Succeeded
- [ ] Candidate Portfolio Publish Button Clicked
- [ ] Candidate Portfolio Publish Succeeded
- [ ] Candidate Portfolio Publish Errored
- [ ] Candidate Portfolio Unpublish Button Clicked
- [ ] Candidate Portfolio Unpublish Succeeded
- [ ] Change Profile Photo Button Clicked
- [ ] Candidate Profile Photo Remove Button Clicked
- [ ] Candidate Profile Photo Remove Succeeded
- [ ] Candidate Profile Photo Remove Errored

**Part C — Prospect (dashboard):**
- [ ] Candidate Portfolio Create Button Clicked
- [ ] Candidate Portfolio Rename Button Clicked
- [ ] Candidate Portfolio Rename Succeeded
- [ ] Candidate Portfolio Delete Button Clicked
- [ ] Candidate Portfolio Delete Succeeded

**Part D — Interview:**
- [ ] Page Viewed — new `current_page_context` values for interview flow steps; `start_source` added on `candidate_interview_landing`
- [ ] Get Started Interview Button Clicked
- [ ] Candidate Interview Info Next Button Clicked
- [ ] What To Expect Link Clicked
- [ ] Candidate Interview Resume Next Button Clicked
- [ ] Candidate Interview Resume Upload Succeeded
- [ ] Candidate Interview Resume Upload Errored
- [ ] Open Identity Check Link Clicked
- [ ] Refresh Status Button Clicked
- [ ] Candidate Interview Identity Verification Succeeded
- [ ] Candidate Interview Identity Verification Errored
- [ ] Candidate Interview Identity Verification Rejected
- [ ] Candidate Interview Identity Verification Auto Redirect Succeeded
- [ ] Candidate Interview Identity Verification Auto Redirect Errored
- [ ] Candidate Interview Identity Verification Auto Redirect Rejected
- [ ] Candidate Interview Identity Verification Continue Button Clicked
- [ ] Candidate Interview Privacy Email Link Clicked
- [ ] Candidate Interview Persona Privacy Policy Link Clicked
- [ ] Candidate Interview Screening Response Next Button Clicked
- [ ] Candidate Interview Screening Response Submit Succeeded
- [ ] Candidate Interview Screening Response Save And Review Button Clicked
- [ ] Allow Device Access Button Clicked
- [ ] Device Access Grant Succeeded
- [ ] Device Access Rejected
- [ ] Candidate Interview Start Button Clicked
- [ ] Candidate Interview Started
- [ ] Candidate Interview Question Answer Succeeded
- [ ] Candidate Interview Question Restart Button Clicked
- [ ] Candidate Interview Question Restart Succeeded
- [ ] Candidate Interview Question Restart Errored
- [ ] Candidate Interview Question Skip Button Clicked
- [ ] Candidate Interview Question Skip Succeeded
- [ ] Candidate Interview Question Skip Errored
- [ ] Candidate Interview Question Skip Rejected
- [ ] Candidate Interview Screening Response Edit Button Clicked
- [ ] Candidate Interview Review Answer Button Clicked
- [ ] Candidate Interview Retake Question Button Clicked
- [ ] Candidate Interview Review Answer Expand Clicked
- [ ] Candidate Interview Answers Submit Succeeded
- [ ] Candidate Interview Answer Retake Succeeded
- [ ] Candidate Interview Screening Response Edit Succeeded
- [ ] Candidate Interview Submit Succeeded
- [ ] Candidate Interview Submit Rejected

- [ ] New objects added to Standard Objects table: **Yes** (see New Standard Objects)
- [ ] Reuse confirmed: `Candidate Resume Upload Button Clicked`, `Candidate Resume Upload Succeeded`, `Candidate Resume Upload Rejected`, `Candidate Resume Upload Errored`, `Candidate Resume Remove Button Clicked`, `Candidate Profile Custom Link Add Succeeded`, `LinkedIn Export Learn How Link Clicked`, `Account Created` (with `entry_point=interview`)

---

## Modifications to Existing Events

These events are not new — they were modified or renamed in PR #739.

**Renamed events:**

| Original Name | New Name | Change |
|---|---|---|
| Resume Upload Button Clicked | Candidate Resume Upload Button Clicked | Prefix rename |
| Resume Uploaded | Candidate Resume Upload Succeeded | Rename to canonical terminal |
| Resume Upload Failed | Candidate Resume Upload Rejected + Candidate Resume Upload Errored | Split: Rejected = client validation, Errored = server extraction |
| Resume Removed | Candidate Resume Remove Button Clicked | Rename to intent event |
| Custom Link Added | Candidate Profile Custom Link Add Succeeded | Rename to canonical terminal |
| LinkedIn Export Learn How Clicked | LinkedIn Export Learn How Link Clicked | Added "Link" |
| Profile Photo Removed | Candidate Profile Photo Remove Button Clicked | Rename to intent event |
| Candidate Question Answered | Candidate Interview Question Answer Succeeded | Rename with namespace |
| Candidate Question Skipped | Candidate Interview Question Skip Succeeded | Rename, moved to backend |
| Candidate Question Restarted | Candidate Interview Question Restart Succeeded | Rename, moved to backend |
| interview_started (snake_case) | Candidate Interview Started | Legacy replacement |
| interview_submitted (snake_case) | Candidate Interview Submit Succeeded | Legacy replacement |

**Modified existing events:**

- `Candidate Profile Created` (Backend) — added `has_handle`, `input_method`, `resume_page_count` properties. `Profile Build Snapshot` frontend event was removed; its data now flows through the `createPortfolio()` API.
- `Account Created` — moved from Frontend to Backend. Fires from `users/analytics.py:fire_account_created()` at two call sites: (1) normal onboarding PATCH /api/users/me on first role assignment, (2) candidate interview claim service. `entry_point` now passed explicitly (hardcoded to `interview` for claim path). Separate `posthog.identify()` call for person properties.
- `Page Viewed` — new `current_page_context` values for interview flow steps; `start_source` property added on `candidate_interview_landing`.

**Removed events (planned but not implemented):**

- `Profile Build Snapshot` — removed entirely; metadata folded into backend Candidate Profile Created
- `Candidate Interview Question Resolve Succeeded` — removed; replaced by per-question `Candidate Interview Question Answer Succeeded` and `Candidate Interview Question Skip Succeeded` events
- `Candidate Interview Submit Button Clicked` — constant exists but capture was never wired
- `Candidate Recording Rehydrated` — removed
- `Candidate Interview Signup Started` — removed

---

## Interaction / Started / Result Pattern

For critical user flows, track the UI interaction or process start separately from the processed result. Each row is one flow with its possible outcomes.

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Publish portfolio | Candidate Portfolio Publish Button Clicked | Candidate Portfolio Publish Succeeded | -- | Candidate Portfolio Publish Errored |
| Unpublish portfolio | Candidate Portfolio Unpublish Button Clicked | Candidate Portfolio Unpublish Succeeded | -- | -- |
| Create portfolio from dashboard | Candidate Portfolio Create Button Clicked | -- | -- | -- |
| Rename portfolio | Candidate Portfolio Rename Button Clicked | Candidate Portfolio Rename Succeeded | -- | -- |
| Delete portfolio | Candidate Portfolio Delete Button Clicked | Candidate Portfolio Delete Succeeded | -- | -- |
| Remove profile photo | Candidate Profile Photo Remove Button Clicked | Candidate Profile Photo Remove Succeeded | -- | Candidate Profile Photo Remove Errored |
| Delete custom link | Candidate Custom Link Delete Button Clicked | Candidate Custom Link Delete Succeeded | -- | Candidate Custom Link Delete Errored |
| Identity verification | Open Identity Check Link Clicked | Candidate Interview Identity Verification Succeeded | Candidate Interview Identity Verification Rejected | Candidate Interview Identity Verification Errored |
| Identity auto-redirect | (timer-based) | Candidate Interview Identity Verification Auto Redirect Succeeded | Candidate Interview Identity Verification Auto Redirect Rejected | Candidate Interview Identity Verification Auto Redirect Errored |
| Device access | Allow Device Access Button Clicked | Device Access Grant Succeeded | Device Access Rejected | -- |
| Start interview | Candidate Interview Start Button Clicked | Candidate Interview Started | -- | -- |
| Answer question | (save & continue) | Candidate Interview Question Answer Succeeded | -- | -- |
| Answer question (retake) | Candidate Interview Retake Question Button Clicked | Candidate Interview Answer Retake Succeeded | -- | -- |
| Restart question | Candidate Interview Question Restart Button Clicked | Candidate Interview Question Restart Succeeded | -- | Candidate Interview Question Restart Errored |
| Skip question | Candidate Interview Question Skip Button Clicked | Candidate Interview Question Skip Succeeded | Candidate Interview Question Skip Rejected | Candidate Interview Question Skip Errored |
| Screening response edit | Candidate Interview Screening Response Edit Button Clicked | Candidate Interview Screening Response Edit Succeeded | -- | -- |
| Submit interview | (backend submission) | Candidate Interview Submit Succeeded | Candidate Interview Submit Rejected | -- |

---

## Metrics → Events Mapping

| Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|
| Interview completion rate | Get Started Interview Button Clicked → Candidate Interview Submit Succeeded | funnel | by `job_id`, `start_source` | Prospect / Hiring |
| Identity verification pass rate | Candidate Interview Identity Verification Succeeded vs Candidate Interview Identity Verification Errored / Rejected | trend (formula) | by `error_category`, `decision_category` | Platform Health |
| Question skip rate | Candidate Interview Question Skip Succeeded | trend | by `question_number` | Hiring |
| Question retake rate | Candidate Interview Question Answer Succeeded (`question_status = answered_restarted`) | trend | by `question_number`, `job_id` | Hiring |
| Resume attach rate at interview | Candidate Interview Resume Next Button Clicked (`has_resume`) | trend | by `has_resume` | Prospect |
| Device-access friction | Allow Device Access Button Clicked → Device Access Grant Succeeded | funnel | by `camera_granted`, `mic_granted` | Platform Health |
| Profile publish rate | Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded | funnel | — | Prospect |
| Handle adoption | Candidate Profile Created (`has_handle`) | trend | by `has_handle` | Prospect |
| Interview → signup conversion | Candidate Interview Submit Succeeded → Account Created (`entry_point=interview`) | funnel | — | Growth / Viral Loop |
| AI conversation completion rate | Candidate Interview Question Answer Succeeded (`ai_conversation_completed`) | trend | by `ai_conversation_completed`, `question_number` | Hiring |
| Test run vs real interview | Candidate Interview Submit Succeeded | trend | by `is_test_run` | Hiring / Platform Health |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Interview completion | Page Viewed → Get Started Interview Button Clicked → Candidate Interview Info Next Button Clicked → Candidate Interview Resume Next Button Clicked → Candidate Interview Identity Verification Succeeded → Candidate Interview Screening Response Submit Succeeded → Candidate Interview Started → Candidate Interview Submit Succeeded | End-to-end candidate conversion; step-level drop-off. Filter Page Viewed by `current_page_context = candidate_interview_landing`. |
| Identity verification | Open Identity Check Link Clicked → Candidate Interview Identity Verification Succeeded | Verification completion / failure rate |
| Device → start | Allow Device Access Button Clicked → Device Access Grant Succeeded → Candidate Interview Started | Camera/mic friction before interview begins |
| Per-question completion | Candidate Interview Started → Candidate Interview Question Answer Succeeded → Candidate Interview Submit Succeeded | Where in the question set candidates drop. Breakdown by `question_number` and `question_status`. |
| Interview → signup | Candidate Interview Submit Succeeded → Account Created | Anonymous candidate → Helix user conversion. Filter Account Created by `entry_point = interview`. |
| Publish conversion | Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded | Publish success rate |
| Screening response edit | Candidate Interview Screening Response Edit Button Clicked → Candidate Interview Screening Response Edit Succeeded | How often candidates edit screening answers from review |
