# HM Job Creation Wizard — Event Catalog

**Flow:** `hm_job_creation_wizard`
**Last Updated:** April 2026

---

## Overview

The job creation wizard is a 5-step flow (+ success page) triggered when a Hiring Manager clicks "+ Create Job Posting" on the home page. The URL changes from a generic `/hiring-manager/job-posting` (step 1) to `/hiring-manager/job-postings/{job_id}/...` once the job is saved (after step 1 Next click).

**Wizard steps:**
1. **Job details** — Paste JD or URL, AI extracts job title/location/company
2. **Understanding the role** — Meet Sam (AI recruiter), option to skip or start a conversation
   - **2b. Chat modality selection** — "How would you like to chat with Sam?" page (Voice / Text options)
3. **Role requirements** — AI-extracted requirements, user can edit/delete/add
4. **Interview questions** — AI-generated screening questions, user can refine/edit/delete/add
5. **Verify** — Email verification via OTP to publish the job
6. **Success** — Job is live, options to preview/share/invite team

**Key behavior:**
- The job is saved (persisted) when the user pastes a JD on step 1 and clicks Next. If the user exits at any later step (X or Back to dashboard), the job appears on the dashboard with "Continue setup" CTA.
- The wizard has its own header (with X button) — no sidebar is shown during the wizard flow.

---

## Page View Events

All wizard steps are distinct routed pages. Each gets a `page_view` on mount. All events from PV-2 onwards include `job_id` (read from URL params). Step 1 events have no `job_id` since the job hasn't been created yet — `session_id` (auto-captured by PostHog) groups them with later events.

| # | current_page_context | URL | Trigger |
|---|---|---|---|
| PV-1 | `hm_job_creation_wizard/job_details` | `/hiring-manager/job-posting` | Step 1 loads |
| PV-2 | `hm_job_creation_wizard/understanding_the_role` | `/hiring-manager/job-postings/{id}` | Step 2 loads |
| PV-2b | `hm_job_creation_wizard/sam_chat_modality_selection` | `/hiring-manager/job-postings/{id}/chat-modality` _(URL TBD)_ | Step 2b loads — "How would you like to chat with Sam?" |
| PV-3 | `hm_job_creation_wizard/role_requirements` | `/hiring-manager/job-postings/{id}/role-requirements` | Step 3 loads |
| PV-4 | `hm_job_creation_wizard/interview_questions` | `/hiring-manager/job-postings/{id}/questions` | Step 4 loads |
| PV-5 | `hm_job_creation_wizard/verify` | `/hiring-manager/job-postings/{id}/verify` | Step 5 loads |
| PV-6 | `hm_job_creation_wizard/success` | `/hiring-manager/job-postings/{id}/success` | Success page loads |

### Page Viewed — previous_page_context mapping

| Page | previous_page_context | entry_point |
|---|---|---|
| `hm_job_creation_wizard/job_details` | `hiring_manager/job_postings` | `job_postings_page_header_click_create_job_posting_button` or `job_postings_empty_state_cta_click_create_job_posting_button` |
| `hm_job_creation_wizard/understanding_the_role` | `hm_job_creation_wizard/job_details` | `hm_job_creation_wizard_job_details_click_next_button` |
| `hm_job_creation_wizard/sam_chat_modality_selection` | `hm_job_creation_wizard/understanding_the_role` | `hm_job_creation_wizard_understanding_the_role_click_start_talking_to_sam_button` |
| `hm_job_creation_wizard/role_requirements` | `hm_job_creation_wizard/understanding_the_role` or `hm_job_creation_wizard/sam_chat_modality_selection` | `hm_job_creation_wizard_understanding_the_role_click_skip_link` or `hm_job_creation_wizard_sam_chat_modality_selection_click_voice_option` or `hm_job_creation_wizard_sam_chat_modality_selection_click_text_option` (after session completes) |
| `hm_job_creation_wizard/interview_questions` | `hm_job_creation_wizard/role_requirements` | `hm_job_creation_wizard_role_requirements_click_next_button` |
| `hm_job_creation_wizard/verify` | `hm_job_creation_wizard/interview_questions` | `hm_job_creation_wizard_interview_questions_click_next_button` |
| `hm_job_creation_wizard/success` | `hm_job_creation_wizard/verify` | `hm_job_creation_wizard_verify_click_verify_button` |

**Re-entry from dashboard (continue setup):**

| Page | previous_page_context | entry_point |
|---|---|---|
| `hm_job_creation_wizard/understanding_the_role` | `hiring_manager/job_postings` | `job_postings_job_card_click_continue_setup_button` |

---

## User Action Events

### Step 1: Job Details

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-1 | `click` | `next_button` | `hm_job_creation_wizard_job_details_footer` | `job` | Submits JD, triggers AI extraction + job save |
| UA-2 | `click` | `back_button` | `hm_job_creation_wizard_job_details_footer` | `job` | Returns to dashboard |
| UA-3 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |

### Step 2: Understanding the Role

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-4 | `click` | `start_talking_to_sam_button` | `hm_job_creation_wizard_understanding_the_role_footer` | `job` | Opens the chat modality selection page (does NOT start session immediately) |
| UA-5 | `click` | `skip_link` | `hm_job_creation_wizard_understanding_the_role_footer` | `job` | Skips Sam, uses JD to generate questions directly |
| UA-6 | `click` | `back_button` | `hm_job_creation_wizard_understanding_the_role_footer` | `job` | Returns to Job Details step |
| UA-7 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |

### Step 2b: Chat Modality Selection ("How would you like to chat with Sam?")

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-8 | `click` | `voice_modality_option` | `hm_job_creation_wizard_sam_chat_modality_selection_options` | `voice_session` | Selects Voice — starts voice session, triggers browser mic permission prompt |
| UA-9 | `click` | `text_modality_option` | `hm_job_creation_wizard_sam_chat_modality_selection_options` | `chat_session` | Selects Text — starts text-based chat session |
| UA-10 | `click` | `back_button` | `hm_job_creation_wizard_sam_chat_modality_selection_footer` | `job` | Returns to Understanding the Role step |
| UA-11 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |

> **Note on browser mic permission prompt:** After UA-8 (Voice click), the browser shows a native permission dialog ("Allow this time" / "Allow while visiting the site" / "Never allow"). These are browser-native interactions that cannot be tracked as `user_action` events. The OUTCOME (granted/denied) should be tracked separately as `system_outcome` events (e.g., `Mic Permission Granted`, `Mic Permission Denied`) — flagged for future addition.

### Step 3: Role Requirements

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-12 | `click` | `next_button` | `hm_job_creation_wizard_role_requirements_footer` | `requirement` | Proceeds to Interview Questions |
| UA-13 | `click` | `back_button` | `hm_job_creation_wizard_role_requirements_footer` | `requirement` | Returns to Understanding the Role |
| UA-14 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |
| UA-15 | `click` | `edit_requirement_icon` | `hm_job_creation_wizard_role_requirements_list` | `requirement` | Opens inline edit for a requirement |
| UA-16 | `click` | `delete_requirement_icon` | `hm_job_creation_wizard_role_requirements_list` | `requirement` | Deletes a requirement immediately (no confirmation) |
| UA-17 | `click` | `add_requirement_button` | `hm_job_creation_wizard_role_requirements_list` | `requirement` | Opens new requirement input |
| UA-18 | `click` | `save_requirement_tick` | `hm_job_creation_wizard_role_requirements_list` | `requirement` | Saves edited or new requirement |
| UA-19 | `click` | `cancel_requirement_cross` | `hm_job_creation_wizard_role_requirements_list` | `requirement` | Cancels edit or new requirement |

### Step 4: Interview Questions

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-20 | `click` | `next_button` | `hm_job_creation_wizard_interview_questions_footer` | `question` | Proceeds to Verify |
| UA-21 | `click` | `back_button` | `hm_job_creation_wizard_interview_questions_footer` | `question` | Returns to Role Requirements |
| UA-22 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |
| UA-23 | `click` | `edit_question_icon` | `hm_job_creation_wizard_interview_questions_list` | `question` | Opens inline edit for a question |
| UA-24 | `click` | `delete_question_icon` | `hm_job_creation_wizard_interview_questions_list` | `question` | Deletes a question |
| UA-25 | `click` | `add_question_button` | `hm_job_creation_wizard_interview_questions_list` | `question` | Opens new question input |
| UA-26 | `submit` | `refine_screening_questions_input` | `hm_job_creation_wizard_interview_questions_refine_bar` | `question` | Submits AI prompt to refine questions. Fires on Apply button click OR Enter key press when input is focused. |
| UA-27 | `click` | `suggestion_chip` | `hm_job_creation_wizard_interview_questions_refine_bar` | `question` | Clicks a pre-built suggestion chip (e.g., "Probe creative tool ecosystem knowledge") |
| UA-28 | `click` | `remove_suggestion_chip` | `hm_job_creation_wizard_interview_questions_refine_bar` | `question` | Removes a suggestion chip (clicks X on chip) |

### Step 5: Verify

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-29 | `click` | `send_code_button` | `hm_job_creation_wizard_verify_form` | `verification` | Sends OTP to email |
| UA-30 | `submit` | `verification_code_input` | `hm_job_creation_wizard_verify_otp_modal` | `verification` | Submits OTP code. Fires on Verify button click OR Enter key press when last digit is entered. |
| UA-31 | `click` | `skip_for_now_link` | `hm_job_creation_wizard_verify_form` | `verification` | Skips verification |
| UA-32 | `click` | `back_button` | `hm_job_creation_wizard_verify_footer` | `job` | Returns to Interview Questions |
| UA-33 | `click` | `close_button` | `hm_job_creation_wizard_header` | `job` | Exits wizard, returns to dashboard |
| UA-34 | `click` | `edit_email_icon` | `hm_job_creation_wizard_verify_form` | `verification` | Edits email address |

### Step 6: Success Page

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-35 | `click` | `preview_button` | `hm_job_creation_wizard_success_job_card` | `job` | Opens job preview |
| UA-36 | `click` | `share_button` | `hm_job_creation_wizard_success_share_section` | `job` | Opens share flow |
| UA-37 | `click` | `invite_team_button` | `hm_job_creation_wizard_success_invite_section` | `job` | Opens invite flow |
| UA-38 | `click` | `go_to_job_posting_page_link` | `hm_job_creation_wizard_success_footer` | `job` | Navigates to job detail page |

### Dashboard: Continue Setup

| # | action | action_value | component | entity_type | Notes |
|---|---|---|---|---|---|
| UA-39 | `click` | `continue_setup_button` | `job_postings_job_card` | `job` | Resumes wizard from where user left off |

---

## Elements NOT Tracked

| Element | Why Not Tracked |
|---|---|
| Pasting JD text into textarea | Passive input — no discrete submit. The submit is the Next button (UA-1). |
| "Extracting job info..." loading state | System behavior, not user action |
| "Creating Job" / "Analyzing..." / "Generating questions..." loading modals | System behavior, not user action |
| Editing extracted fields (Job Title, Location, Company) | Inline edits with no submit button — auto-saved. Low analytics value. |
| Reordering questions via drag handle | Low priority — confirmed not needed for now |
| "Resend code in 0:39" countdown | System behavior |
| Browser mic permission dialog (Allow / Never allow) | Browser-native, not trackable as user_action. The OUTCOME should be tracked as a separate `system_outcome` event (future). |
| Sidebar nav links | Sidebar is not shown during the wizard flow — wizard has its own header only |

---

## Complete Event Inventory

### page_view events (7)

| # | current_page_context |
|---|---|
| PV-1 | `hm_job_creation_wizard/job_details` |
| PV-2 | `hm_job_creation_wizard/understanding_the_role` |
| PV-2b | `hm_job_creation_wizard/sam_chat_modality_selection` |
| PV-3 | `hm_job_creation_wizard/role_requirements` |
| PV-4 | `hm_job_creation_wizard/interview_questions` |
| PV-5 | `hm_job_creation_wizard/verify` |
| PV-6 | `hm_job_creation_wizard/success` |

### user_action events (39)

| Step | Events | Count |
|---|---|---|
| Job Details | UA-1 to UA-3 | 3 |
| Understanding the Role | UA-4 to UA-7 | 4 |
| Sam Chat Modality Selection | UA-8 to UA-11 | 4 |
| Role Requirements | UA-12 to UA-19 | 8 |
| Interview Questions | UA-20 to UA-28 | 9 |
| Verify | UA-29 to UA-34 | 6 |
| Success | UA-35 to UA-38 | 4 |
| Dashboard (continue setup) | UA-39 | 1 |

---

## Total Event Count

| Type | Count |
|---|---|
| page_view | 7 |
| user_action | 39 |
| **Total** | **46 events** |

---

## Flags for Human Review / Future Additions

1. **Browser mic permission outcome:** After UA-8 (Voice modality click), the browser shows a native mic permission prompt. The outcome (granted / denied) should be tracked as a `system_outcome` event (`Mic Permission Granted` / `Mic Permission Denied`). Not in scope for this user_action plan but should be added when implementing voice session events.
2. **PV-2b URL:** Confirm the actual URL for the chat modality selection page once implemented (currently marked TBD).
3. **Voice session events:** When voice conversation with Sam happens (after UA-8 + mic permission granted), additional events will be needed: `Voice Session Started`, `Voice Session Ended`, `Voice Session Setup Failed` (mic denied / device unavailable). Out of scope for this plan.
4. **Text session events:** Similar — when text chat with Sam happens (after UA-9), need `Chat Session Started`, `Chat Message Sent`, etc. Out of scope.
