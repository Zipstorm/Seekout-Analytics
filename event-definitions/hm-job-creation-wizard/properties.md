# HM Job Creation Wizard — Property Dictionary

**Flow:** `hm_job_creation_wizard`
**Last Updated:** April 2026

---

## New Properties Introduced by This Flow

### `modality`

| Property | Type | Scope | Allowed Values | Used In |
|---|---|---|---|---|
| `modality` | enum | event | `voice`, `text` | Sam Chat Modality Selected (UA-8 / UA-9) |

The chat modality the user selected when interacting with Sam. Distinguishes between voice conversation (which triggers a browser mic permission prompt) and text-based chat.

### `requirement_index`

| Property | Type | Scope | Description | Used In |
|---|---|---|---|---|
| `requirement_index` | number | event | The 1-indexed position of the requirement being acted on (e.g., 1, 2, 3...) | Edit Requirement Clicked (UA-15), Delete Requirement Clicked (UA-16) |

### `question_index`

| Property | Type | Scope | Description | Used In |
|---|---|---|---|---|
| `question_index` | number | event | The 1-indexed position of the question being acted on | Edit Question Clicked (UA-23), Delete Question Clicked (UA-24) |

### `prompt_text`

| Property | Type | Scope | Description | Used In |
|---|---|---|---|---|
| `prompt_text` | string | event | The free-text prompt the user submitted to refine screening questions (e.g., `"focus on ai and ml"`) | Refine Questions Submitted (UA-26) |

### `chip_label`

| Property | Type | Scope | Description | Used In |
|---|---|---|---|---|
| `chip_label` | string | event | The label of the suggestion chip clicked or removed (e.g., `"Probe creative tool ecosystem knowledge"`) | Suggestion Chip Clicked (UA-27), Remove Suggestion Chip Clicked (UA-28) |

### `trigger`

| Property | Type | Scope | Allowed Values | Used In |
|---|---|---|---|---|
| `trigger` | enum | event | `apply_button`, `enter_key`, `verify_button` | Refine Questions Submitted (UA-26), Verify Code Submitted (UA-30) |

Captures whether the user submitted via clicking the button or pressing Enter. Useful for measuring keyboard-driven user behavior.

### `modification_type`

| Property | Type | Scope | Allowed Values | Used In |
|---|---|---|---|---|
| `modification_type` | enum | event | `added`, `edited` | Save Requirement Clicked (UA-18) |

Captures whether saving a requirement was for a NEW requirement (added) or an EXISTING one (edited). Same property name as the existing `Requirement Modified` / `Question Modified` events but used here on the user_action save.

> **Note:** `modification_type` already exists in the property dictionary with values `added`, `edited`, `deleted`, `reordered`. This flow uses only `added` and `edited` on the save click.

---

## Reused Properties (Already Defined)

### Standard event properties (from `event-type commands/`)

All wizard events use these standard properties:

| Property | Type | Description |
|---|---|---|
| `action` | enum | `click` or `submit` |
| `action_value` | string | Specific UI element interacted with (snake_case) |
| `current_page_context` | string | Wizard step page identifier (`hm_job_creation_wizard/...`) |
| `previous_page_context` | string or null | Previous page in session |
| `entry_point` | string or null | Mechanism that brought user to current page |
| `entity_type` | string | Business object: `job`, `requirement`, `question`, `verification`, `voice_session`, `chat_session` |
| `component` | string | UI container where action occurred |
| `context_object_type` | string or null | `null` for all wizard events (the wizard itself isn't a scoped business container) |
| `context_object_id` | string or null | `null` for all wizard events |

### Job identification

| Property | Type | Scope | Available On | Description |
|---|---|---|---|---|
| `job_id` | UUID | event | All wizard events from PV-2 onwards | The job being created. Read from URL params. `null` on PV-1 and UA-1 since the job doesn't exist yet. |

### Sharing (reused on Success page)

| Property | Type | Allowed Values | Used In |
|---|---|---|---|
| `share_source` | enum | `success_screen`, `dashboard`, `overflow_menu` | Share Button Clicked (UA-36) — set to `success_screen` |

---

## Page Context Values

All page contexts introduced by this flow:

| Page | current_page_context |
|---|---|
| Job Details (Step 1) | `hm_job_creation_wizard/job_details` |
| Understanding the Role (Step 2) | `hm_job_creation_wizard/understanding_the_role` |
| Sam Chat Modality Selection (Step 2b) | `hm_job_creation_wizard/sam_chat_modality_selection` |
| Role Requirements (Step 3) | `hm_job_creation_wizard/role_requirements` |
| Interview Questions (Step 4) | `hm_job_creation_wizard/interview_questions` |
| Verify (Step 5) | `hm_job_creation_wizard/verify` |
| Success (Step 6) | `hm_job_creation_wizard/success` |

---

## Component Names

All `component` values introduced by this flow:

| Component | Where |
|---|---|
| `hm_job_creation_wizard_header` | Top bar (X close icon) — shared across all steps |
| `hm_job_creation_wizard_job_details_footer` | Step 1 footer (Back, Next) |
| `hm_job_creation_wizard_understanding_the_role_footer` | Step 2 footer (Back, Skip, Start talking to Sam) |
| `hm_job_creation_wizard_sam_chat_modality_selection_options` | Step 2b modality cards (Voice, Text) |
| `hm_job_creation_wizard_sam_chat_modality_selection_footer` | Step 2b footer (Back) |
| `hm_job_creation_wizard_role_requirements_footer` | Step 3 footer (Back, Next) |
| `hm_job_creation_wizard_role_requirements_list` | Step 3 requirement cards (edit, delete, add, save, cancel icons) |
| `hm_job_creation_wizard_interview_questions_footer` | Step 4 footer (Back, Next) |
| `hm_job_creation_wizard_interview_questions_list` | Step 4 question cards (edit, delete, add icons) |
| `hm_job_creation_wizard_interview_questions_refine_bar` | Step 4 AI prompt bar (refine input, suggestion chips) |
| `hm_job_creation_wizard_verify_form` | Step 5 email + send code form |
| `hm_job_creation_wizard_verify_otp_modal` | Step 5 OTP entry modal |
| `hm_job_creation_wizard_verify_footer` | Step 5 footer (Back) |
| `hm_job_creation_wizard_success_job_card` | Step 6 job card (Preview button) |
| `hm_job_creation_wizard_success_share_section` | Step 6 share section (Share button) |
| `hm_job_creation_wizard_success_invite_section` | Step 6 invite section (Invite team button) |
| `hm_job_creation_wizard_success_footer` | Step 6 footer (Go to job posting page link) |
| `job_postings_job_card` | Dashboard job card (Continue Setup button) |

---

## Auto-Captured Properties (PostHog SDK)

Automatically included on every event. Do NOT set manually.

| Property | Description |
|---|---|
| `distinct_id` | User identifier (set via `posthog.identify()` after auth) |
| `$current_url` | Full page URL |
| `$referrer` | HTTP referrer |
| `$browser` | Browser name |
| `$os` | Operating system |
| `$device_type` | desktop / mobile / tablet |
| `$screen_height` / `$screen_width` | Screen dimensions |
| `timestamp` | Event timestamp |
| `$session_id` | Browser session identifier — used to group all wizard events in a single session |

---

## Person Properties (Available on All Events)

These are set on the user profile via `identifyUser()` and are available on every event for that user:

| Property | Scope | Description |
|---|---|---|
| `email`, `name`, `org_id` | `$set` | User identity |
| `current_persona` | `$set` | Active persona (`hiring_manager` for users in this flow) |
| `first_persona` | `$set_once` | First persona chosen during onboarding |
| `account_created_at` | `$set_once` | Account creation timestamp |
