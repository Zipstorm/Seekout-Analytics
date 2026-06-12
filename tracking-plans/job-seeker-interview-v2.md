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

## A3. `Handle Availability Checked` — *optional, recommended*

The field live-checks availability (✓ available / unavailable). A lightweight event here would tell us how often users try handles, and the unavailable-collision rate. **Recommended but not required** — include only if handle adoption is a tracked goal.

| Field | Value |
|---|---|
| **Event** | `Handle Availability Checked` |
| **Area** | Prospect |
| **Type** | — |
| **Trigger** | Debounced availability check resolves as the user types a handle |
| **Source** | Backend (or frontend after API resolves) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `is_available` | boolean | `true` / `false` | Whether the typed handle was available |
| `handle_length` | number | e.g. `8` | Character count of the checked handle |
| `current_page_context` | string | `candidate_create_profile` | Page |

> **Recommendation:** Implement A1 + A2 now (they cost nothing — properties on events that already fire). Treat A3 as a fast-follow only if handle adoption becomes a KPI.

---

# Part B — Profile editor / overview (`/candidate/editor/:portfolioId`)

**Images 2, 3, 4.** The editor has an Overview / Resume / Github / Portfolio tab bar, a Download action on the Resume tab, and a Publish / Unpublish toggle in the header. v1 deferred all editor events to v2.

## B1. `Profile Overview Loaded`

A content-aware load event for the overview tab — separate from the generic `Page Viewed`, because it carries the profile's completeness state at load time (this is what Image 2 asks for: published?, skills count, journey count, photo?, description?).

| Field | Value |
|---|---|
| **Event** | `Profile Overview Loaded` |
| **Area** | Prospect |
| **Type** | — |
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
| `current_page_context` | string | `candidate_editor_overview` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |

## B2. `Profile Tab Switched`

| Field | Value |
|---|---|
| **Event** | `Profile Tab Switched` |
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

## B3. `Resume Downloaded`

| Field | Value |
|---|---|
| **Event** | `Resume Downloaded` |
| **Area** | Prospect |
| **Type** | user_action |
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

### B4a. `Publish Button Clicked` (intent, frontend)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `publish_button` | |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_editor` | |
| `component` | string | `editor_header_actions` | |
| `entity_type` | string | `candidate_profile` | |

### B4b. `Candidate Profile Published` (success, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `is_published` | boolean | `true` | Confirmed published state |
| `skills_count` | number | | Snapshot of completeness at publish time |
| `journey_count` | number | | |
| `has_profile_photo` | boolean | | |
| `has_description` | boolean | | |
| `has_intro_video` | boolean | | |

### B4c. `Candidate Profile Publish Failed` (failure, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `error_reason` | string | | Truncated to 256 chars |
| `error_category` | enum | `validation`, `server`, `network` | |

### B4d. `Unpublish Button Clicked` (intent) + B4e. `Candidate Profile Unpublished` (success, backend)

Mirror of B4a/B4b. `Unpublish Button Clicked` carries `action_value = unpublish_button`; `Candidate Profile Unpublished` carries `portfolio_id`, `is_published = false`.

---

# Part C — Dashboard: portfolio management (`/candidate/dashboard`)

**Images 5, 6, 7.** The dashboard lists portfolios. The overflow menu has **Rename Portfolio** and **Delete**. Each portfolio has a unique `portfolio_id`.

## C1. `Rename Portfolio Button Clicked` (intent)

Opens the rename modal (Image 7).

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `rename_portfolio` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

## C2. `Rename Portfolio Save Button Clicked` (intent)

Fires when the user clicks **Save** in the modal — carries whether the name actually changed, so the no-op-save rate is visible.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `save_button` | |
| `portfolio_id` | string (UUID) | | |
| `name_changed` | boolean | `true` / `false` | Did the new name differ from the old one? |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `rename_portfolio_modal` | |
| `entity_type` | string | `candidate_profile` | |

## C3. `Portfolio Renamed` (success, backend)

**Only fires when the name actually changed** (`name_changed = true`). If the user clicks Save without editing, C2 fires with `name_changed = false` and C3 does **not** fire.

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string (UUID) | | |
| `new_name_length` | number | e.g. `42` | Character count of the new name (length only — not the name itself) |
| `previous_name_length` | number | e.g. `60` | Character count of the previous name |

## C4. `Delete Portfolio Button Clicked` (user_action)

The delete menu item **deletes immediately with no confirmation dialog** (per your note). We still capture the click as intent so it can be paired with the backend outcome.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `delete` | Exact menu item text |
| `portfolio_id` | string (UUID) | | |
| `current_page_context` | string | `candidate_dashboard` | |
| `component` | string | `portfolio_card_overflow_menu` | |
| `entity_type` | string | `candidate_profile` | |

## C5. `Portfolio Deleted` (success, backend)

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

### D1b. `Get Started Button Clicked` (intent)

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

### D2b. `Interview Information Submitted`

Fires on "Next". Email is mandatory; first/last names optional. **Do not** put name or email values in properties — only booleans.

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

### D3a. `Agreement Acknowledged` (user_action, toggle)

The "I understand and agree to the above" checkbox gates the Next button.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `toggle` | |
| `action_value` | string | `i_understand_and_agree_to_the_above` | Exact checkbox label |
| `is_checked` | boolean | `true` / `false` | New checkbox state |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_upload_resume` | |
| `component` | string | `interview_recording_data_card` | |
| `entity_type` | string | `interview` | |

### D3b. `What To Expect Link Clicked` (user_action)

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

### D3c. `Upload Resume Step Completed` (user_action)

Fires on "Next". Captures whether the candidate proceeded with or without a resume (both allowed).

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

### D4d. `Identity Verified` (success, backend)

The backend confirmation that the third-party (Persona) identity check succeeded — fires when status flips to verified (Image 15). This is the outcome of D4b.

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `verification_vendor` | string | `persona` | Third-party identity vendor |
| `time_to_verify_seconds` | number or null | | Seconds from Open Identity Check to verification |

### D4e. `Identity Verification Failed` (failure, backend)

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

### D5b. `Screening Responses Submitted` (user_action)

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

### D6c. `Device Access Granted` (success) / D6d. `Device Access Denied` (failure)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `camera_granted` | boolean | `true` / `false` | Camera permission result |
| `mic_granted` | boolean | `true` / `false` | Microphone permission result |
| `error_reason` | string | (denied only) | Permission error, if any |

### D6e. `Start Interview Button Clicked` (intent)

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

### D6f. `Interview Started` (success, backend)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `questions_count` | number | e.g. `4` | Number of AI interview questions |
| `input_mode` | enum | `voice`, `text` | Interview modality |
| `has_resume` | boolean | `true` / `false` | Did the candidate upload a resume earlier? |
| `identity_verified` | boolean | `true` / `false` | Was identity verified before start? |

## D7. Interview — per-question (Images 19, 20, 21, 23)

### D7a. `Interview Question Answered` (user_action)

Fires on **Save & continue** (Image 23) — the AI marks the question complete and the candidate moves on. This is the primary "a question was answered" signal.

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `save_and_continue_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `question_number` | number | `1`–`N` | Position of the answered question |
| `questions_count` | number | | Total interview questions |
| `input_mode` | enum | `voice`, `text` | |
| `response_duration_seconds` | number or null | | Total spoken duration on this question (the "You spoke for…" total) |
| `current_page_context` | string | `interview_recording` | |
| `component` | string | `interview_recording_footer` | |
| `entity_type` | string | `interview_question` | |

### D7b. Restart question (intent → outcome)

- **`Restart Question Button Clicked`** (intent) — clicking "Restart" opens the confirm modal (Image 20). `action_value = restart`.
- **`Interview Question Restarted`** (success) — fires after the candidate clicks "Restart" again to confirm; the question starts over. Properties: `interview_id`, `job_id`, `question_number`.
- **`Interview Question Restart Failed`** (failure) — restart could not be re-initialized. Properties: `interview_id`, `job_id`, `question_number`, `error_reason`, `error_category`.

### D7c. Skip question (intent → outcome)

- **`Skip Question Button Clicked`** (intent) — clicking "Skip" opens the skip modal (Image 21). `action_value = skip`.
- **`Question Skipped`** (success) — fires after the candidate clicks "Skip this question" to confirm. Properties: `interview_id`, `job_id`, `question_number`.
- **`Skip Question Cancelled`** (user_action) — the candidate clicks "Go back and answer" instead. `action_value = go_back_and_answer`. Properties: `interview_id`, `job_id`, `question_number`.

All three carry `current_page_context = interview_recording`, `component = interview_recording_footer` (or `skip_question_modal` / `restart_question_modal` for the confirm/cancel actions), `entity_type = interview_question`.

## D8. Review & submit (Images 24, 25, 26, 28)

### D8a. `Page Viewed` — `current_page_context = interview_review`

### D8b. `Edit Screening Response Button Clicked` (user_action)

The "Edit" link next to a screening answer (Image 24). `action_value = edit`, `entity_type = screening_response`, plus `interview_id`, `job_id`.

### D8c. `Interview Question Retaken` (distinct event)

Retaking a video question (Image 25). Kept as its **own event** so retake volume is measurable separately from first answers. Fires after the retake's "Save & next" returns the candidate to the review page.

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `question_number` | number | | Which question was retaken |
| `input_mode` | enum | `voice`, `text` | |
| `response_duration_seconds` | number or null | | Duration of the retake answer |

> The "Retake this question" link itself can fire an intent `Retake Question Button Clicked` (`action_value = retake_this_question`) if click-to-completion drop-off matters; the success event D8c is the one that powers "how many questions get retaken."

### D8d. `Answer Question Button Clicked` (user_action)

For a skipped/missing question, the "Answer question" button (Image 26). `action_value = answer_question`, `entity_type = interview_question`, plus `interview_id`, `job_id`, `question_number`. Completing the answer then fires `Interview Question Answered` (D7a) again.

### D8e. `Submit Interview Button Clicked` (intent)

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | |
| `action_value` | string | `submit_interview_button` | |
| `interview_id` | string (UUID) | | |
| `job_id` | string (UUID) | | |
| `current_page_context` | string | `interview_review` | |
| `component` | string | `interview_review_footer` | |
| `entity_type` | string | `interview` | |

### D8f. `Interview Submitted` (success, backend)

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

### D8g. `Interview Submission Failed` (failure, backend)

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

Add to the Standard Objects table in `docs/event-schema.md`:

| Object | Entity | Example Events |
|---|---|---|
| Profile Overview | Job seeker profile editor overview tab | Profile Overview Loaded |
| Profile Tab | Editor tab navigation | Profile Tab Switched |
| Portfolio | A job seeker's portfolio (dashboard card) | Rename Portfolio Button Clicked, Portfolio Renamed, Portfolio Deleted |
| Interview | Anonymous AI screening interview session | Get Started Button Clicked, Interview Started, Interview Submitted |
| Identity Check | Third-party (Persona) identity verification | Open Identity Check Button Clicked, Identity Verified, Identity Verification Failed |
| Screening Response | Candidate's answers to recruiter Yes/No screening questions | Screening Responses Submitted |
| Interview Question | An individual AI interview question | Interview Question Answered, Question Skipped, Interview Question Restarted, Interview Question Retaken |
| Device Check | Camera/mic permission check before interview | Allow Access Button Clicked, Device Access Granted |

> `Candidate Profile`, `Resume`, `Resume Upload`, `Build Profile`, and `LinkedIn Export` objects already exist from Job Seeker v1 and are reused.

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Publish profile | Publish Button Clicked | Candidate Profile Published | Candidate Profile Publish Failed |
| Unpublish profile | Unpublish Button Clicked | Candidate Profile Unpublished | — |
| Rename portfolio | Rename Portfolio Save Button Clicked | Portfolio Renamed (only if `name_changed`) | — |
| Delete portfolio | Delete Portfolio Button Clicked | Portfolio Deleted | — |
| Identity verification | Open Identity Check Button Clicked | Identity Verified | Identity Verification Failed |
| Device access | Allow Access Button Clicked | Device Access Granted | Device Access Denied |
| Start interview | Start Interview Button Clicked | Interview Started | — |
| Restart question | Restart Question Button Clicked | Interview Question Restarted | Interview Question Restart Failed |
| Skip question | Skip Question Button Clicked | Question Skipped | (Skip Question Cancelled = abandon intent) |
| Submit interview | Submit Interview Button Clicked | Interview Submitted | Interview Submission Failed |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Interview completion | Page Viewed (`interview_landing`) → Get Started Button Clicked → Interview Information Submitted → Upload Resume Step Completed → Identity Verified → Screening Responses Submitted → Interview Started → Interview Submitted | End-to-end candidate conversion; step-level drop-off |
| Identity verification | Open Identity Check Button Clicked → Identity Verified | Verification completion / failure rate |
| Device → start | Allow Access Button Clicked → Device Access Granted → Interview Started | Camera/mic friction before interview begins |
| Per-question completion | Interview Started → Interview Question Answered (breakdown by `question_number`) → Interview Submitted | Where in the question set candidates drop |
| Interview → signup | Interview Submitted → Account Created (`entry_point = interview`) | Anonymous candidate → Helix user conversion |
| Publish conversion | Publish Button Clicked → Candidate Profile Published | Publish success rate |

---

## Metrics → Events Mapping

| Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|
| Interview completion rate | Get Started Button Clicked → Interview Submitted | funnel | by `job_id`, `start_source` | Prospect / Hiring |
| Identity verification pass rate | Identity Verified vs Identity Verification Failed | trend (formula) | by `error_category` | Platform Health |
| Question skip rate | Question Skipped / Interview Question Answered | trend | by `question_number` | Hiring |
| Question retake rate | Interview Question Retaken | trend | by `question_number`, `job_id` | Hiring |
| Resume attach rate at interview | Upload Resume Step Completed (`has_resume`) | trend | by `has_resume` | Prospect |
| Device-access friction | Allow Access Button Clicked → Device Access Granted | funnel | by `camera_granted`, `mic_granted` | Platform Health |
| Profile publish rate | Publish Button Clicked → Candidate Profile Published | funnel | — | Prospect |
| Handle adoption | Build Profile Snapshot (`has_handle`) | trend | by `has_handle` | Prospect |
| Interview → signup conversion | Interview Submitted → Account Created (`entry_point=interview`) | funnel | — | Growth / Viral Loop |

---

## Property Details (new properties)

| Property | Type | Values | Description |
|---|---|---|---|
| `interview_id` | UUID | | Anonymous AI interview session identifier (from URL) |
| `is_published` | boolean | `true` / `false` | Profile published state — Profile Overview Loaded, Candidate Profile Published/Unpublished |
| `skills_count` | number | | Skills on the profile — Profile Overview Loaded, Candidate Profile Published |
| `journey_count` | number | | Journey/timeline entries — Profile Overview Loaded, Candidate Profile Published |
| `has_description` | boolean | `true` / `false` | Summary present — Profile Overview Loaded, Candidate Profile Published |
| `has_handle` | boolean | `true` / `false` | Handle claimed — Build Profile Snapshot, Candidate Profile Created |
| `handle_length` | number or null | | Handle character count — Build Profile Snapshot, Handle Availability Checked |
| `is_available` | boolean | `true` / `false` | Handle availability — Handle Availability Checked |
| `tab_name` | enum | `overview`, `resume`, `github`, `portfolio` | Editor tab — Profile Tab Switched |
| `name_changed` | boolean | `true` / `false` | Whether a rename actually changed the name — Rename Portfolio Save Button Clicked |
| `new_name_length` | number | | New portfolio name length — Portfolio Renamed |
| `previous_name_length` | number | | Previous portfolio name length — Portfolio Renamed |
| `was_published` | boolean | `true` / `false` | Whether a deleted portfolio was published — Portfolio Deleted |
| `start_source` | enum | `interview_link`, `email_invite`, `job_board`, `direct` (+ existing `create_job_button`) | How a candidate reached the interview — Page Viewed (interview_landing) |
| `has_first_name` | boolean | `true` / `false` | Optional name field filled — Interview Information Submitted |
| `has_last_name` | boolean | `true` / `false` | Optional name field filled — Interview Information Submitted |
| `agreement_acknowledged` | boolean | `true` | Recording/data agreement accepted — Upload Resume Step Completed |
| `is_checked` | boolean | `true` / `false` | Checkbox state — Agreement Acknowledged |
| `verification_vendor` | string | `persona` | Identity vendor — Identity Verified / Failed |
| `time_to_verify_seconds` | number or null | | Seconds to verify identity — Identity Verified |
| `camera_granted` | boolean | `true` / `false` | Camera permission — Device Access Granted/Denied, Interview Started |
| `mic_granted` | boolean | `true` / `false` | Mic permission — Device Access Granted/Denied |
| `input_mode` | enum | `voice`, `text` | *(reuses existing enum)* Interview modality — Interview Started, Interview Question Answered, etc. |
| `question_number` | number | `1`–`N` | *(reuses existing property)* Question position — interview question events |
| `questions_count` | number | | *(reuses existing property)* Total interview questions — Interview Started, Interview Submitted |
| `response_duration_seconds` | number or null | | Spoken duration on a question — Interview Question Answered, Interview Question Retaken |
| `yes_count` | number | | Yes answers on screening — Screening Responses Submitted |
| `no_count` | number | | No answers on screening — Screening Responses Submitted |
| `optional_context_provided_count` | number | | Yes answers with optional context filled — Screening Responses Submitted |
| `required_explanation_count` | number | | No answers (mandatory explanation) — Screening Responses Submitted |
| `answered_count` | number | | Questions answered — Interview Submitted |
| `skipped_count` | number | | Questions skipped — Interview Submitted |
| `retaken_count` | number | | Questions retaken — Interview Submitted |
| `screening_questions_count` | number | | Screening question count — Interview Submitted |
| `total_duration_seconds` | number or null | | Full interview duration — Interview Submitted |

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
- [ ] `Handle Availability Checked` *(optional)* → Prospect

**Part B — Prospect:**
- [ ] Profile Overview Loaded
- [ ] Profile Tab Switched
- [ ] Resume Downloaded
- [ ] Publish Button Clicked
- [ ] Candidate Profile Published
- [ ] Candidate Profile Publish Failed
- [ ] Unpublish Button Clicked
- [ ] Candidate Profile Unpublished

**Part C — Prospect:**
- [ ] Rename Portfolio Button Clicked
- [ ] Rename Portfolio Save Button Clicked
- [ ] Portfolio Renamed
- [ ] Delete Portfolio Button Clicked
- [ ] Portfolio Deleted

**Part D — Interview (new Interview / Identity Check / Screening Response / Interview Question / Device Check areas):**
- [ ] Page Viewed (new contexts + `start_source`) — existing event, no catalog row change beyond property note
- [ ] Get Started Button Clicked
- [ ] Interview Information Submitted
- [ ] Agreement Acknowledged
- [ ] What To Expect Link Clicked
- [ ] Upload Resume Step Completed
- [ ] Open Identity Check Button Clicked
- [ ] Refresh Status Button Clicked
- [ ] Identity Verified
- [ ] Identity Verification Failed
- [ ] Screening Responses Submitted
- [ ] Allow Access Button Clicked
- [ ] Device Access Granted
- [ ] Device Access Denied
- [ ] Start Interview Button Clicked
- [ ] Interview Started
- [ ] Interview Question Answered
- [ ] Restart Question Button Clicked
- [ ] Interview Question Restarted
- [ ] Interview Question Restart Failed
- [ ] Skip Question Button Clicked
- [ ] Question Skipped
- [ ] Skip Question Cancelled
- [ ] Edit Screening Response Button Clicked
- [ ] Retake Question Button Clicked *(optional intent)*
- [ ] Interview Question Retaken
- [ ] Answer Question Button Clicked
- [ ] Submit Interview Button Clicked
- [ ] Interview Submitted
- [ ] Interview Submission Failed

- [ ] New objects added to Standard Objects table: **Yes** (8 — see New Standard Objects)
- [ ] Reuse confirmed: `Resume Upload Button Clicked`, `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`, `LinkedIn Export Learn How Link Clicked`, `Account Created` (with `entry_point=interview`)

---

## Open questions / decisions for review

1. **Handle event A3** — implement the optional `Handle Availability Checked` now, or defer? (Default: defer.)
2. **Per-question screening detail (D5)** — aggregate-only on submit (current default) vs. per-response `Screening Question Answered`.
3. **Retake intent (D8c)** — track the `Retake Question Button Clicked` intent, or only the `Interview Question Retaken` success? (Default: success only.)
4. **Anonymous → user stitching** — confirm engineering can `alias()` the interview ID to the email at D2b and again to the user ID at signup (D8h). Without it, the interview→signup funnel breaks.
