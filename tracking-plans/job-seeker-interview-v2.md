# Tracking Plan: Job Seeker Interview v2

**Product:** Helix (SeekOut.ai)
**Feature:** Job seeker v2 — handle on create-profile, profile editor/overview, dashboard portfolio management, and the anonymous AI screening interview flow
**Date:** 2026-06-12
**Related PRD:** —
**Status:** Draft

> Reference: `docs/event-schema.md` for naming conventions and Standard Objects; `docs/event-catalog.md` for the existing event catalog and Property Dictionary.

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

The interview candidate **does not need to be a Helix user**. They open an interview link, provide only an email, and take the interview. This has two consequences for instrumentation:

1. **Anonymous distinct ID.** Until the candidate signs up on the final screen, all interview events fire against an anonymous distinct ID derived from the interview session — e.g. `interview_<interview_id>`. Once the email is captured (info step), the email can be aliased to that ID so all prior events stitch together.
2. **Signup stitching.** If the candidate creates an account on the final screen (Image 28), call `posthog.alias()` to merge the anonymous interview ID into the new user ID so the whole journey (link open → interview → signup) is one person. The resulting `Account Created` should carry `entry_point = interview`.

Every interview event carries `interview_id` and `job_id`, and is attached to the `job` group (the job posting being screened for). The `job` group is keyed on the job, not the person, so it works even while the candidate is anonymous.

---

# Part A — Profile handle (`/candidate/create-profile`)

**Image 1.** The create-profile page now has a "Your handle (optional)" field (`localhost:8001/u/<handle>`) with an availability check (✓ available). This field did not exist in v1.

**Where it goes:** The handle is part of the same final "Build my AI profile" submission that v1 already instruments. Rather than a new submit event, the handle folds into the existing **`Build Profile Snapshot`** (the state-capture event that already records resume/photo/links) and the backend **`Candidate Profile Created`** (to confirm it persisted). No new object is required.

## A1. `Build Profile Snapshot` — add handle properties (modification)

Existing v1 frontend event. Add two properties:

| Property | Type | Values | Description |
|---|---|---|---|
| `has_handle` | boolean | `true` / `false` | Did the user claim a handle before submitting? |
| `handle_length` | number or null | e.g. `8` | Character count of the claimed handle (null if none). Length only — never capture the handle string itself in the snapshot. |

## A2. `Candidate Profile Created` — add handle property (modification)

Existing v1 backend event. Add:

| Property | Type | Values | Description |
|---|---|---|---|
| `has_handle` | boolean | `true` / `false` | Whether a handle was persisted on the created profile. |

## A3. Handle availability — *optional, recommended*

The handle field live-checks availability (✓ available / unavailable). These events tell us how often users try handles, the collision rate, and whether unavailability causes abandonment. **Recommended but not required** — include only if handle adoption is a tracked goal.

**Trigger logic:** Fires once on **blur** (user clicks/tabs out of the handle input) — but **only if the handle value changed** since the last blur or since the field was first focused. This avoids duplicate fires when the user clicks in and out without editing. If the user never blurs (e.g. types a handle and clicks "Build my AI profile" directly), the event fires on the button click before the submit flow begins. Which event fires depends on the most recent availability API response.

### A3a. `Candidate Handle Add Succeeded`

Fires when the handle the user entered is **available**.

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
| `handle_length` | number | e.g. `8` | Character count of the handle |
| `current_page_context` | string | `candidate_create_profile` | Page |

### A3b. `Candidate Handle Add Rejected`

Fires when the handle the user entered is **unavailable** (taken by another user).

| Field | Value |
|---|---|
| **Event** | `Candidate Handle Add Rejected` |
| **Area** | Prospect |
| **Type** | Failure |
| **Trigger** | Handle input blur (if value changed) or "Build my AI profile" click (if handle is dirty and not yet blur-fired), AND the most recent availability check returned unavailable |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `handle_length` | number | e.g. `8` | Character count of the handle |
| `current_page_context` | string | `candidate_create_profile` | Page |

> **Recommendation:** Implement A1 + A2 now (they cost nothing — properties on events that already fire). Treat A3a/A3b as a fast-follow only if handle adoption becomes a KPI.

---

# Part B — Profile editor / overview (`/candidate/editor/:portfolioId`)

**Images 2, 3, 4.** The editor has an Overview / Resume / Github / Portfolio tab bar, a Download action on the Resume tab, and a Publish / Unpublish toggle in the header. v1 deferred all editor events to v2.

## B1. `Candidate Profile Overview Load Succeeded`

A content-aware load event for the overview tab — separate from the generic `Page Viewed`, because it carries the profile's completeness state at load time (published?, skills count, journey count, photo?, description?, intro video?).

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

## B2. `Candidate Profile Tab Switched`

| Field | Value |
|---|---|
| **Event** | `Candidate Profile Tab Switched` |
| **Area** | Prospect |
| **Type** | user_action |
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

## B3. `Candidate Resume Download Succeeded`

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
| `action` | enum | `click` | |
| `action_value` | string | `download_button` | |
| `portfolio_id` | string (UUID) | | |
| `resume_id` | string (UUID) or null | | Resume being downloaded |
| `current_page_context` | string | `candidate_editor_resume` | Page |
| `component` | string | `editor_resume_tab` | |
| `entity_type` | string | `candidate_profile` | |

## B4. Publish / Unpublish (intent + outcome)

The user wants a **frontend click (intent)** plus a **backend event that confirms the publish** (outcome). Same pattern applies to unpublish (Image 4 shows the header toggles to "Unpublish" once published).

### B4a. `Candidate Portfolio Publish Button Clicked` (intent, frontend)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `publish_button` | |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor` | |
| `component` | string | `editor_header_actions` | |
| `entity_type` | string | `candidate_profile` | |

### B4b. `Candidate Portfolio Publish Succeeded` (success, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `is_published` | boolean | `true` | Confirmed published state |
| `skills_count` | number | | Snapshot of completeness at publish time |
| `journey_count` | number | | |
| `has_profile_photo` | boolean | | |
| `has_description` | boolean | | |
| `has_intro_video` | boolean | | |

### B4c. `Candidate Portfolio Publish Errored` (error, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network` | |

### B4d. `Candidate Portfolio Unpublish Button Clicked` (intent)

Mirror of B4a. `action_value = unpublish_button`. Same properties: `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type`.

### B4e. `Candidate Portfolio Unpublish Succeeded` (success, backend)

Mirror of B4b. Carries `portfolio_id`, `is_published = false`.

---

# Part C — Dashboard: portfolio management (`/candidate/dashboard`)

**Images 5, 6, 7.** The dashboard lists portfolios. The overflow menu has **Rename Portfolio** and **Delete**. Each portfolio has a unique `portfolio_id`.

## C1. `Candidate Portfolio Rename Button Clicked` (intent)

Opens the rename modal (Image 7).

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `rename_portfolio` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

## C2. `Candidate Portfolio Rename Succeeded` (success, backend)

**Only fires when the name actually changed.** If the user clicks Save without editing, this event does **not** fire.

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `new_name_length` | number | e.g. `42` | Character count of the new name (length only — not the name itself) |
| `previous_name_length` | number | e.g. `60` | Character count of the previous name |

## C3. `Candidate Portfolio Delete Button Clicked` (intent)

The delete menu item **deletes immediately with no confirmation dialog** (per your note). We still capture the click as intent so it can be paired with the backend outcome.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `delete` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

## C4. `Candidate Portfolio Delete Succeeded` (success, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `was_published` | boolean | `true` / `false` | Whether the deleted portfolio was published |

> **Gap flagged:** Delete has no confirmation step today, so there is no way to measure accidental deletes or a cancel rate. If a confirmation modal is added later, add a `Delete Portfolio Confirmed` / `Delete Portfolio Cancelled` pair.
> **Not instrumented (out of scope):** the dashboard's `Create`, `See Analytics`, `Share`, and "Start a session with Max" buttons. Flag for a later plan if needed.

---

# Part D — Anonymous AI screening interview (`/interview/:interviewId`)

**Images 10–28.** A candidate opens an interview link and proceeds through: landing → your information → upload resume → verify identity → screening questions → device check → interview (per-question voice answers) → review & submit → submitted. See the anonymous-distinct-ID note at the top.

All Part D events carry `interview_id`, `job_id`, and the `job` group.

## D1. Landing page (Image 10)

### D1a. `Page Viewed` (existing event, new context + `start_source`)

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `interview_landing` | Page |
| `previous_page_context` | string | null (external entry typical) | |
| `start_source` | enum | `interview_link`, `email_invite`, `job_board`, `direct` | How the candidate arrived at the interview (from `?source=` param or referrer) |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |

### D1b. `Get Started Interview Button Clicked` (intent)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `get_started_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_landing` | |
| `component` | string | `interview_landing_ready_card` | |
| `entity_type` | string | `interview` | |

## D2. Your information (Images 11, 12)

### D2a. `Page Viewed` — `current_page_context = interview_candidate_info`

### D2b. `Candidate Interview Information Submitted`

Fires on "Next". Email is mandatory; first/last names optional. **Do not** put name or email values in properties — only booleans. Email is captured via `posthog.alias()` on the person profile, not as an event property.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `submit` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `has_first_name` | boolean | `true` / `false` | Optional field filled? |
| `has_last_name` | boolean | `true` / `false` | Optional field filled? |
| `current_page_context` | string | `interview_candidate_info` | |
| `component` | string | `interview_candidate_info_form` | |
| `entity_type` | string | `interview` | |

> At this point the email is known — alias the anonymous interview ID to the email so subsequent events stitch.

## D3. Upload resume (Images 13, 13b)

Resume upload reuses the existing v1 events (`Resume Upload Button Clicked`, `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`) with `interview_id` + `job_id` added and `current_page_context = interview_upload_resume`. The "Learn how" LinkedIn-export link reuses the existing **`LinkedIn Export Learn How Link Clicked`**. New events below.

### D3a. `What To Expect Link Clicked` (user_action)

The "What to expect" expander (Image 13). Captures intent / nervousness signal.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `what_to_expect` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_upload_resume` | |
| `component` | string | `interview_ai_guided_card` | |
| `entity_type` | string | `interview` | |

### D3b. `Interview Resume Step Next Button Clicked` (intent)

Fires on "Next". Captures whether the candidate proceeded with or without a resume (both allowed). This is a frontend click event only — resume upload is confirmed separately by the existing backend `Resume Uploaded` event.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `has_resume` | boolean | `true` / `false` | Did they upload a resume before continuing? |
| `agreement_acknowledged` | boolean | `true` | Always true (gated) — kept for auditability |
| `current_page_context` | string | `interview_upload_resume` | |
| `component` | string | `interview_upload_resume_footer` | |
| `entity_type` | string | `interview` | |

## D4. Verify identity (Images 14, 15)

### D4a. `Page Viewed` — `current_page_context = interview_verify_identity`

### D4b. `Open Identity Check Button Clicked` (intent)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `open_identity_check_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_card` | |
| `entity_type` | string | `identity_check` | |

### D4c. `Refresh Status Button Clicked` (user_action)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `refresh_status_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_verify_identity` | |
| `component` | string | `secure_identity_check_card` | |
| `entity_type` | string | `identity_check` | |

### D4d. `Identity Verification Succeeded` (success, backend)

The backend confirmation that the third-party (Persona) identity check succeeded — fires when status flips to verified (Image 15). This is the outcome of D4b.

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `verification_vendor` | string | `persona` | Third-party identity vendor |
| `time_to_verify_seconds` | number or null | | Seconds from Open Identity Check to verification |

### D4e. `Identity Verification Errored` (error, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `verification_vendor` | string | `persona` | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `vendor`, `timeout`, `mismatch`, `server` | Why verification failed |

## D5. Screening questions (Images 16, 17)

These are the recruiter's Yes/No screening questions (distinct from the AI voice interview questions in D7). On Yes, a context box is **optional**; on No, an explanation is **mandatory**.

### D5a. `Page Viewed` — `current_page_context = interview_screening_questions`

### D5b. `Candidate Interview Screening Responses Submitted` (user_action)

Fires on "Next" with aggregate answer composition — avoids per-keystroke noise while still answering "how often is context provided, and how often is the mandatory No-explanation filled?"

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `submit` | |
| `action_value` | string | `next_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `questions_count` | number | e.g. `3` | Total screening questions shown |
| `yes_count` | number | | Number answered Yes |
| `no_count` | number | | Number answered No |
| `optional_context_provided_count` | number | | # of Yes answers where the optional context box was filled |
| `required_explanation_count` | number | | # of No answers (each requires a mandatory explanation) |
| `current_page_context` | string | `interview_screening_questions` | |
| `component` | string | `interview_screening_questions_form` | |
| `entity_type` | string | `screening_response` | |

> **Optional per-question detail:** if response-level analysis is needed, add `Screening Question Answered` (`answer` = yes/no, `has_context`, `context_required`) fired on blur. Start with the aggregate; add only if drop-off on a specific question needs investigating.

## D6. Device check & interview start (Image 18)

### D6a. `Page Viewed` — `current_page_context = interview_device_check`

### D6b. `Allow Access Button Clicked` (intent)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `allow_access_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_device_check` | |
| `component` | string | `device_check_card` | |
| `entity_type` | string | `device_check` | |

### D6c. `Device Access Grant Succeeded` (success) / D6d. `Device Access Rejected` (failure)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `camera_granted` | boolean | `true` / `false` | Camera permission result |
| `mic_granted` | boolean | `true` / `false` | Microphone permission result |
| `error_reason` | string | (denied only) | Permission error, if any |

### D6e. `Interview Start Button Clicked` (intent)

Enabled only after access is granted.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `start_interview_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_device_check` | |
| `component` | string | `device_check_footer` | |
| `entity_type` | string | `interview` | |

### D6f. `Candidate Interview Started` (success, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `questions_count` | number | e.g. `4` | Number of AI interview questions |
| `input_mode` | enum | `voice`, `text` | Interview modality |
| `has_resume` | boolean | `true` / `false` | Did the candidate upload a resume earlier? |
| `identity_verified` | boolean | `true` / `false` | Was identity verified before start? |

## D7. Interview — per-question (Images 19, 20, 21, 23)

### D7a. `Candidate Interview Question Resolve Succeeded` (per-question terminal event)

Fires once per question when it reaches a terminal state — whether answered, answered after a restart, or skipped. This is the primary per-question signal and powers stacked bar charts by `question_status`.

**Triggers:**
- **Save & continue** click → `question_status = answered`
- **Save & continue** click after restarting the question → `question_status = answered_restarted`
- **Skip this question** confirmation → `question_status = skipped`

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `question_number` | number | `1`–`N` | Position of the question |
| `questions_count` | number | | Total interview questions |
| `question_status` | enum | `answered`, `answered_restarted`, `skipped` | Terminal status of this question |
| `input_mode` | enum | `voice`, `text` | |
| `response_duration_seconds` | number or null | | Spoken duration (null if skipped) |
| `current_page_context` | string | `interview_recording` | |
| `component` | string | `interview_recording_footer` or `skip_question_modal` | |
| `entity_type` | string | `interview_question` | |

### D7b. Restart question (intent → outcome)

- **`Interview Question Restart Button Clicked`** (intent) — clicking "Restart" opens the confirm modal (Image 20). `action_value = restart`.
- **`Interview Question Restart Succeeded`** (success) — fires after the candidate clicks "Restart" again to confirm; the question starts over. Properties: `interview_id`, `job_id`, `question_number`.
- **`Interview Question Restart Errored`** (failure) — restart could not be re-initialized. Properties: `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category`.

### D7c. Skip question (intent → outcome)

- **`Interview Question Skip Button Clicked`** (intent) — clicking "Skip" opens the skip modal (Image 21). `action_value = skip`.
- **`Interview Question Skip Succeeded`** (success) — fires after the candidate clicks "Skip this question" to confirm. Properties: `interview_id`, `job_id`, `question_number`.
- **`Interview Question Skip Rejected`** (user_action) — the candidate clicks "Go back and answer" instead. `action_value = go_back_and_answer`. Properties: `interview_id`, `job_id`, `question_number`.

All carry `current_page_context = interview_recording`, `component = interview_recording_footer` (or `skip_question_modal` / `restart_question_modal` for the confirm/cancel actions), `entity_type = interview_question`.

## D8. Review & submit (Images 24, 25, 26, 28)

### D8a. `Page Viewed` — `current_page_context = interview_review`

### D8b. `Interview Screening Response Edit Button Clicked` (user_action)

The "Edit" link next to a screening answer (Image 24). `action_value = edit`, `entity_type = screening_response`, plus `interview_id`, `job_id`.

### D8c. `Interview Review Answer Question Button Clicked` (user_action)

For a skipped/missing question on the review page, the "Answer question" button (Image 26). `action_value = answer_question`, `entity_type = interview_question`, plus `interview_id`, `job_id`, `question_number`. Completing the answer fires `Candidate Interview Question Resolve Succeeded` (D7a) with `question_status = answered`.

### D8d. `Candidate Interview Submit Button Clicked` (intent)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `submit_interview_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_review` | |
| `component` | string | `interview_review_footer` | |
| `entity_type` | string | `interview` | |

### D8e. `Candidate Interview Submit Succeeded` (success, backend)

The completion event — the headline conversion for the whole flow.

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `answered_count` | number | | Questions answered |
| `skipped_count` | number | | Questions skipped |
| `retaken_count` | number | | Questions retaken at least once |
| `questions_count` | number | | Total interview questions |
| `screening_questions_count` | number | | Total screening questions |
| `has_resume` | boolean | `true` / `false` | |
| `identity_verified` | boolean | `true` / `false` | |
| `input_mode` | enum | `voice`, `text` | |
| `total_duration_seconds` | number or null | | End-to-end interview duration |

### D8f. `Candidate Interview Submit Rejected` (rejected, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network`, `timeout` | |

### D8h. Post-submit signup (Image 28) — reuse existing auth

The "Sign up to find out…" card is the existing signup flow. **Reuse `Account Created`** with `entry_point = interview` (new value), and call `posthog.alias()` to merge the anonymous interview ID into the new user. No new event — this is the bridge from anonymous candidate to Helix user, so attribution must carry through.

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Candidate Handle Add | Job seeker handle add action | Candidate Handle Add Succeeded, Candidate Handle Add Rejected |
| Candidate Profile Overview Load | Profile overview load state | Candidate Profile Overview Load Succeeded |
| Candidate Profile Tab | Editor tab navigation | Candidate Profile Tab Switched |
| Candidate Resume Download | Resume download action | Candidate Resume Download Succeeded |
| Candidate Portfolio Publish | Portfolio publish lifecycle | Candidate Portfolio Publish Succeeded, Candidate Portfolio Publish Errored |
| Candidate Portfolio Publish Button | Portfolio publish CTA | Candidate Portfolio Publish Button Clicked |
| Candidate Portfolio Unpublish | Portfolio unpublish lifecycle | Candidate Portfolio Unpublish Succeeded |
| Candidate Portfolio Unpublish Button | Portfolio unpublish CTA | Candidate Portfolio Unpublish Button Clicked |
| Candidate Portfolio Rename | Portfolio rename lifecycle | Candidate Portfolio Rename Succeeded |
| Candidate Portfolio Rename Button | Portfolio rename CTA | Candidate Portfolio Rename Button Clicked |
| Candidate Portfolio Delete | Portfolio delete lifecycle | Candidate Portfolio Delete Succeeded |
| Candidate Portfolio Delete Button | Portfolio delete CTA | Candidate Portfolio Delete Button Clicked |
| Get Started Interview Button | Interview landing CTA | Get Started Interview Button Clicked |
| Candidate Interview Information | Candidate info form submission | Candidate Interview Information Submitted |
| Candidate Interview Screening Responses | Screening question aggregate submission | Candidate Interview Screening Responses Submitted |
| Candidate Interview Question Resolve | Per-question terminal status | Candidate Interview Question Resolve Succeeded |
| Candidate Interview Submit | Interview submission lifecycle | Candidate Interview Submit Succeeded, Candidate Interview Submit Rejected |
| Candidate Interview Submit Button | Interview submit CTA | Candidate Interview Submit Button Clicked |
| Candidate Interview | Anonymous AI screening interview session | Candidate Interview Started |
| Interview Start Button | Start interview CTA | Interview Start Button Clicked |
| Interview Resume Step Next Button | Resume step progression CTA | Interview Resume Step Next Button Clicked |
| Interview Question Restart | Question restart lifecycle | Interview Question Restart Succeeded, Interview Question Restart Errored |
| Interview Question Restart Button | Question restart CTA | Interview Question Restart Button Clicked |
| Interview Question Skip | Question skip lifecycle | Interview Question Skip Succeeded, Interview Question Skip Rejected |
| Interview Question Skip Button | Question skip CTA | Interview Question Skip Button Clicked |
| Interview Screening Response Edit Button | Screening answer edit link | Interview Screening Response Edit Button Clicked |
| Interview Review Answer Question Button | Answer skipped question on review | Interview Review Answer Question Button Clicked |
| Identity Verification | Third-party identity verification | Identity Verification Succeeded, Identity Verification Errored |
| Open Identity Check Button | Open identity check CTA | Open Identity Check Button Clicked |
| Refresh Status Button | Refresh identity check status CTA | Refresh Status Button Clicked |
| Device Access Grant | Camera/mic grant result | Device Access Grant Succeeded |
| Device Access | Camera/mic permission rejection | Device Access Rejected |
| Allow Access Button | Camera/mic permission CTA | Allow Access Button Clicked |
| What To Expect Link | Interview info expander | What To Expect Link Clicked |


---

## New Events

Events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Type | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Candidate Handle Add Succeeded | Prospect | Success | Handle input blur or submit, availability = available | `handle_length`, `current_page_context` | -- | -- |
| Candidate Handle Add Rejected | Prospect | Rejected | Handle input blur or submit, availability = unavailable | `handle_length`, `current_page_context` | -- | -- |
| Candidate Profile Overview Load Succeeded | Prospect | Success | Overview tab finishes loading | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video`, `profile_completeness_rate`, `current_page_context`, `previous_page_context` | -- | -- |
| Candidate Profile Tab Switched | Prospect | Interaction | User clicks a tab in the editor | `action`, `action_value`, `portfolio_id`, `tab_name`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Resume Download Succeeded | Prospect | Success | User clicks Download on Resume tab | `action`, `action_value`, `portfolio_id`, `resume_id`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Portfolio Publish Button Clicked | Prospect | Interaction | User clicks Publish in editor header | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Portfolio Publish Succeeded | Prospect | Success | Backend confirms publish | `portfolio_id`, `is_published`, `skills_count`, `journey_count`, `has_profile_photo`, `has_description`, `has_intro_video` | -- | -- |
| Candidate Portfolio Publish Errored | Prospect | Error | Backend publish error | `portfolio_id`, `error_reason`, `error_category` | -- | -- |
| Candidate Portfolio Unpublish Button Clicked | Prospect | Interaction | User clicks Unpublish in editor header | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Portfolio Unpublish Succeeded | Prospect | Success | Backend confirms unpublish | `portfolio_id`, `is_published` | -- | -- |
| Candidate Portfolio Rename Button Clicked | Prospect | Interaction | User clicks Rename in overflow menu | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Portfolio Rename Succeeded | Prospect | Success | Backend confirms rename (name changed) | `portfolio_id`, `new_name_length`, `previous_name_length` | -- | -- |
| Candidate Portfolio Delete Button Clicked | Prospect | Interaction | User clicks Delete in overflow menu | `action`, `action_value`, `portfolio_id`, `current_page_context`, `component`, `entity_type` | -- | -- |
| Candidate Portfolio Delete Succeeded | Prospect | Success | Backend confirms delete | `portfolio_id`, `was_published` | -- | -- |
| Get Started Interview Button Clicked | Prospect | Interaction | User clicks Get Started on interview landing | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Candidate Interview Information Submitted | Prospect | Interaction | User clicks Next on info form | `action`, `action_value`, `interview_id`, `job_id`, `has_first_name`, `has_last_name`, `current_page_context`, `component`, `entity_type` | job | -- |
| What To Expect Link Clicked | Prospect | Interaction | User clicks What to expect expander | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Interview Resume Step Next Button Clicked | Prospect | Interaction | User clicks Next on resume step | `action`, `action_value`, `interview_id`, `job_id`, `has_resume`, `agreement_acknowledged`, `current_page_context`, `component`, `entity_type` | job | -- |
| Open Identity Check Button Clicked | Prospect | Interaction | User clicks Open Identity Check | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Refresh Status Button Clicked | Prospect | Interaction | User clicks Refresh Status | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Identity Verification Succeeded | Prospect | Success | Backend confirms identity verified | `interview_id`, `job_id`, `verification_vendor`, `time_to_verify_seconds` | job | -- |
| Identity Verification Errored | Prospect | Error | Backend identity check fails | `interview_id`, `job_id`, `verification_vendor`, `error_reason`, `error_category` | job | -- |
| Candidate Interview Screening Responses Submitted | Prospect | Interaction | User clicks Next on screening questions | `action`, `action_value`, `interview_id`, `job_id`, `questions_count`, `yes_count`, `no_count`, `optional_context_provided_count`, `required_explanation_count`, `current_page_context`, `component`, `entity_type` | job | -- |
| Allow Access Button Clicked | Prospect | Interaction | User clicks Allow Access for camera/mic | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Device Access Grant Succeeded | Prospect | Success | Browser grants camera/mic | `interview_id`, `job_id`, `camera_granted`, `mic_granted` | job | -- |
| Device Access Rejected | Prospect | Rejected | Browser denies camera/mic | `interview_id`, `job_id`, `camera_granted`, `mic_granted`, `error_reason` | job | -- |
| Interview Start Button Clicked | Prospect | Interaction | User clicks Start Interview | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Candidate Interview Started | Prospect | Started | Backend initializes interview session | `interview_id`, `job_id`, `questions_count`, `input_mode`, `has_resume`, `identity_verified` | job | -- |
| Candidate Interview Question Resolve Succeeded | Prospect | Success | Question reaches terminal state (answered/restarted/skipped) | `interview_id`, `job_id`, `question_number`, `questions_count`, `question_status`, `input_mode`, `response_duration_seconds`, `current_page_context`, `component`, `entity_type` | job | -- |
| Interview Question Restart Button Clicked | Prospect | Interaction | User clicks Restart on a question | `action`, `action_value`, `interview_id`, `job_id`, `question_number`, `current_page_context`, `component`, `entity_type` | job | -- |
| Interview Question Restart Succeeded | Prospect | Success | Question restart confirmed | `interview_id`, `job_id`, `question_number` | job | -- |
| Interview Question Restart Errored | Prospect | Error | Question restart could not initialize | `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category` | job | -- |
| Interview Question Skip Button Clicked | Prospect | Interaction | User clicks Skip on a question | `action`, `action_value`, `interview_id`, `job_id`, `question_number`, `current_page_context`, `component`, `entity_type` | job | -- |
| Interview Question Skip Succeeded | Prospect | Success | Skip confirmed | `interview_id`, `job_id`, `question_number` | job | -- |
| Interview Question Skip Rejected | Prospect | Rejected | User clicks Go back and answer | `action`, `action_value`, `interview_id`, `job_id`, `question_number` | job | -- |
| Interview Screening Response Edit Button Clicked | Prospect | Interaction | User clicks Edit on a screening answer | `action`, `action_value`, `interview_id`, `job_id`, `entity_type` | job | -- |
| Interview Review Answer Question Button Clicked | Prospect | Interaction | User clicks Answer Question on review page | `action`, `action_value`, `interview_id`, `job_id`, `question_number`, `entity_type` | job | -- |
| Candidate Interview Submit Button Clicked | Prospect | Interaction | User clicks Submit Interview | `action`, `action_value`, `interview_id`, `job_id`, `current_page_context`, `component`, `entity_type` | job | -- |
| Candidate Interview Submit Succeeded | Prospect | Success | Backend confirms interview submitted | `interview_id`, `job_id`, `answered_count`, `skipped_count`, `retaken_count`, `questions_count`, `screening_questions_count`, `has_resume`, `identity_verified`, `input_mode`, `total_duration_seconds` | job | -- |
| Candidate Interview Submit Rejected | Prospect | Rejected | Backend rejects interview submission | `interview_id`, `job_id`, `error_reason`, `error_category` | job | -- |

---

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Publish portfolio | Candidate Portfolio Publish Button Clicked | Candidate Portfolio Publish Succeeded | -- | Candidate Portfolio Publish Errored |
| Unpublish portfolio | Candidate Portfolio Unpublish Button Clicked | Candidate Portfolio Unpublish Succeeded | -- | -- |
| Rename portfolio | Candidate Portfolio Rename Button Clicked | Candidate Portfolio Rename Succeeded | -- | -- |
| Delete portfolio | Candidate Portfolio Delete Button Clicked | Candidate Portfolio Delete Succeeded | -- | -- |
| Identity verification | Open Identity Check Button Clicked | Identity Verification Succeeded | -- | Identity Verification Errored |
| Device access | Allow Access Button Clicked | Device Access Grant Succeeded | Device Access Rejected | -- |
| Start interview | Interview Start Button Clicked | Candidate Interview Started | -- | -- |
| Restart question | Interview Question Restart Button Clicked | Interview Question Restart Succeeded | -- | Interview Question Restart Errored |
| Skip question | Interview Question Skip Button Clicked | Interview Question Skip Succeeded | Interview Question Skip Rejected | -- |
| Submit interview | Candidate Interview Submit Button Clicked | Candidate Interview Submit Succeeded | Candidate Interview Submit Rejected | -- |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Interview completion | Page Viewed → Get Started Interview Button Clicked → Candidate Interview Information Submitted → Interview Resume Step Next Button Clicked → Identity Verification Succeeded → Candidate Interview Screening Responses Submitted → Candidate Interview Started → Candidate Interview Submit Succeeded | End-to-end candidate conversion; step-level drop-off. Filter Page Viewed by `current_page_context = interview_landing`. |
| Identity verification | Open Identity Check Button Clicked → Identity Verification Succeeded | Verification completion / failure rate |
| Device → start | Allow Access Button Clicked → Device Access Grant Succeeded → Candidate Interview Started | Camera/mic friction before interview begins |
| Per-question completion | Candidate Interview Started → Candidate Interview Question Resolve Succeeded → Candidate Interview Submit Succeeded | Where in the question set candidates drop. Breakdown by `question_number` and `question_status`. |
| Interview → signup | Candidate Interview Submit Succeeded → Account Created | Anonymous candidate → Helix user conversion. Filter Account Created by `entry_point = interview`. |
| Publish conversion | Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded | Publish success rate |

---

## Metrics → Events Mapping

| Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|
| Interview completion rate | Get Started Interview Button Clicked → Candidate Interview Submit Succeeded | funnel | by `job_id`, `start_source` | Prospect / Hiring |
| Identity verification pass rate | Identity Verification Succeeded vs Identity Verification Errored | trend (formula) | by `error_category` | Platform Health |
| Question skip rate | Candidate Interview Question Resolve Succeeded (`question_status = skipped`) | trend | by `question_number` | Hiring |
| Question retake rate | Candidate Interview Question Resolve Succeeded (`question_status = answered_restarted`) | trend | by `question_number`, `job_id` | Hiring |
| Resume attach rate at interview | Interview Resume Step Next Button Clicked (`has_resume`) | trend | by `has_resume` | Prospect |
| Device-access friction | Allow Access Button Clicked → Device Access Grant Succeeded | funnel | by `camera_granted`, `mic_granted` | Platform Health |
| Profile publish rate | Candidate Portfolio Publish Button Clicked → Candidate Portfolio Publish Succeeded | funnel | — | Prospect |
| Handle adoption | Build Profile Snapshot (`has_handle`) | trend | by `has_handle` | Prospect |
| Interview → signup conversion | Candidate Interview Submit Succeeded → Account Created (`entry_point=interview`) | funnel | — | Growth / Viral Loop |

---

## Property Details (new properties)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | UUID | | Portfolio/profile identifier — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish/Unpublish/Rename/Delete events |
| `has_profile_photo` | boolean | `true` / `false` | Profile photo present — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `resume_id` | UUID or null | | Resume identifier — Candidate Resume Download Succeeded *(reuses existing v1 property)* |
| `identity_verified` | boolean | `true` / `false` | Whether identity was verified before start — Candidate Interview Started, Candidate Interview Submit Succeeded |
| `interview_id` | UUID | | Anonymous AI interview session identifier (from URL) |
| `is_published` | boolean | `true` / `false` | Profile published state — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded / Unpublish Succeeded |
| `skills_count` | number | | Skills on the profile — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `journey_count` | number | | Journey/timeline entries — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `has_description` | boolean | `true` / `false` | Summary present — Candidate Profile Overview Load Succeeded, Candidate Portfolio Publish Succeeded |
| `profile_completeness_rate` | number | `0`–`100` | Percentage of completeness steps filled — Candidate Profile Overview Load Succeeded |
| `has_handle` | boolean | `true` / `false` | Handle claimed — Build Profile Snapshot, Candidate Profile Created |
| `handle_length` | number or null | | Handle character count — Build Profile Snapshot, Candidate Handle Add Succeeded, Candidate Handle Add Rejected |
| `tab_name` | enum | `overview`, `resume`, `github`, `portfolio` | Editor tab — Candidate Profile Tab Switched |
| `new_name_length` | number | | New portfolio name length — Candidate Portfolio Rename Succeeded |
| `previous_name_length` | number | | Previous portfolio name length — Candidate Portfolio Rename Succeeded |
| `was_published` | boolean | `true` / `false` | Whether a deleted portfolio was published — Candidate Portfolio Delete Succeeded |
| `start_source` | enum | `interview_link`, `email_invite`, `job_board`, `direct` (+ existing `create_job_button`) | How a candidate reached the interview — Page Viewed (interview_landing) |
| `has_first_name` | boolean | `true` / `false` | Optional name field filled — Candidate Interview Information Submitted |
| `has_last_name` | boolean | `true` / `false` | Optional name field filled — Candidate Interview Information Submitted |
| `agreement_acknowledged` | boolean | `true` | Recording/data agreement accepted — Interview Resume Step Next Button Clicked |
| `verification_vendor` | string | `persona` | Identity vendor — Identity Verification Succeeded / Errored |
| `time_to_verify_seconds` | number or null | | Seconds to verify identity — Identity Verification Succeeded |
| `camera_granted` | boolean | `true` / `false` | Camera permission — Device Access Grant Succeeded / Rejected, Candidate Interview Started |
| `mic_granted` | boolean | `true` / `false` | Mic permission — Device Access Grant Succeeded / Rejected |
| `input_mode` | enum | `voice`, `text` | *(reuses existing enum)* Interview modality — Candidate Interview Started, Candidate Interview Question Resolve Succeeded, etc. |
| `question_status` | enum | `answered`, `answered_restarted`, `skipped` | Terminal status of a question — Candidate Interview Question Resolve Succeeded |
| `question_number` | number | `1`–`N` | *(reuses existing property)* Question position — interview question events |
| `questions_count` | number | | *(reuses existing property)* Total interview questions — Candidate Interview Started, Candidate Interview Submit Succeeded |
| `response_duration_seconds` | number or null | | Spoken duration on a question — Candidate Interview Question Resolve Succeeded |
| `yes_count` | number | | Yes answers on screening — Candidate Interview Screening Responses Submitted |
| `no_count` | number | | No answers on screening — Candidate Interview Screening Responses Submitted |
| `optional_context_provided_count` | number | | Yes answers with optional context filled — Candidate Interview Screening Responses Submitted |
| `required_explanation_count` | number | | No answers (mandatory explanation) — Candidate Interview Screening Responses Submitted |
| `answered_count` | number | | Questions answered — Candidate Interview Submit Succeeded |
| `skipped_count` | number | | Questions skipped — Candidate Interview Submit Succeeded |
| `retaken_count` | number | | Questions retaken — Candidate Interview Submit Succeeded |
| `screening_questions_count` | number | | Screening question count — Candidate Interview Submit Succeeded |
| `total_duration_seconds` | number or null | | Full interview duration — Candidate Interview Submit Succeeded |

**Property Dictionary updates needed on merge:**

- `error_category` — append values: `vendor`, `mismatch` (identity), and confirm `validation`, `server`, `network`, `timeout` already exist.
- `start_source` — extend allowed values with `interview_link`, `email_invite`, `job_board`, `direct`.
- `entry_point` — extend allowed values with `interview`.
- `entity_type` — add values: `interview`, `identity_check`, `screening_response`, `interview_question`, `device_check`, `candidate_profile`.

---

## Catalog Updates

New events from this plan to add to `docs/event-catalog.md` (do **not** merge automatically — run `/merge-tracking-plan`):

**Part A (modifications to v1 events):**
- [ ] `Build Profile Snapshot` — add `has_handle`, `handle_length`
- [ ] `Candidate Profile Created` — add `has_handle`
- [ ] `Candidate Handle Add Succeeded` *(optional)* → Prospect
- [ ] `Candidate Handle Add Rejected` *(optional)* → Prospect

**Part B — Prospect:**
- [ ] Candidate Profile Overview Load Succeeded
- [ ] Candidate Profile Tab Switched
- [ ] Candidate Resume Download Succeeded
- [ ] Candidate Portfolio Publish Button Clicked
- [ ] Candidate Portfolio Publish Succeeded
- [ ] Candidate Portfolio Publish Errored
- [ ] Candidate Portfolio Unpublish Button Clicked
- [ ] Candidate Portfolio Unpublish Succeeded

**Part C — Prospect:**
- [ ] Candidate Portfolio Rename Button Clicked
- [ ] Candidate Portfolio Rename Succeeded
- [ ] Candidate Portfolio Delete Button Clicked
- [ ] Candidate Portfolio Delete Succeeded

**Part D — Interview (new Interview / Identity Check / Screening Response / Interview Question / Device Check areas):**
- [ ] Page Viewed (new contexts + `start_source`) — existing event, no catalog row change beyond property note
- [ ] Get Started Interview Button Clicked
- [ ] Candidate Interview Information Submitted
- [ ] What To Expect Link Clicked
- [ ] Interview Resume Step Next Button Clicked
- [ ] Open Identity Check Button Clicked
- [ ] Refresh Status Button Clicked
- [ ] Identity Verification Succeeded
- [ ] Identity Verification Errored
- [ ] Candidate Interview Screening Responses Submitted
- [ ] Allow Access Button Clicked
- [ ] Device Access Grant Succeeded
- [ ] Device Access Rejected
- [ ] Interview Start Button Clicked
- [ ] Candidate Interview Started
- [ ] Candidate Interview Question Resolve Succeeded
- [ ] Interview Question Restart Button Clicked
- [ ] Interview Question Restart Succeeded
- [ ] Interview Question Restart Errored
- [ ] Interview Question Skip Button Clicked
- [ ] Interview Question Skip Succeeded
- [ ] Interview Question Skip Rejected
- [ ] Interview Screening Response Edit Button Clicked
- [ ] Interview Review Answer Question Button Clicked
- [ ] Candidate Interview Submit Button Clicked
- [ ] Candidate Interview Submit Succeeded
- [ ] Candidate Interview Submit Rejected

- [ ] New objects added to Standard Objects table: **Yes** (8 — see New Standard Objects)
- [ ] Reuse confirmed: `Resume Upload Button Clicked`, `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`, `LinkedIn Export Learn How Link Clicked`, `Account Created` (with `entry_point=interview`)

---

## Open questions / decisions for review

1. **Handle event A3** — implement the optional `Candidate Handle Add Succeeded` / `Candidate Handle Add Rejected` now, or defer? (Default: defer.)
2. **Per-question screening detail (D5)** — aggregate-only on submit (current default) vs. per-response `Screening Question Answered`.
3. **Rejected vs Failed naming** — some failure events use "Rejected" (user/system denied) vs "Failed" (technical error). Validate against naming rules after pulling latest from main.
4. **Anonymous → user stitching** — confirm engineering can `alias()` the interview ID to the email at D2b and again to the user ID at signup (D8h). Without it, the interview→signup funnel breaks.
