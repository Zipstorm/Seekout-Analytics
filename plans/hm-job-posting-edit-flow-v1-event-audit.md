# HM Job Posting & Edit Flow — Complete Event Audit

**Date:** 2026-06-07
**Branch:** `hm-job-posting-edit-flow-v1`
**Purpose:** Comprehensive inventory of every user action, system event, and analytics event across the HM job posting management flows. Identifies gaps, cross-plan sync issues, and property improvements.

**Sources:**
- `docs/helix/event-catalog.md` — existing Live and Not Started events
- `tracking-plans/helix/archived/hm-job-creation-wizard-v2.md` — 27 wizard events (Merged)
- `tracking-plans/helix/archived/hm-job-creation-wizard-v3.md` — 18 events (Merged)
- `tracking-plans/helix/hm-job-posting-edit-flow-v1.md` — 34 new events + 7 modifications (Review)

---

## Page 1: Job Postings Dashboard (`/hiring-manager/job-postings`)

**Context:** `hm_job_postings`
**When:** HM lands here after login with current role = Hiring Manager

### Every User Action & Event

| # | User Action | Event Fired | Source Plan | Status | Type |
|---|---|---|---|---|---|
| 1.1 | Page loads | `Page Viewed` | Catalog | Live | page_view |
| 1.2 | Page loads with data | `Job Postings Dashboard Loaded` | Edit Flow v1 | Not Started | system |
| 1.3 | Clicks "My jobs" / "Shared with me" / "Archived" tab | `Job Postings Tab Switched` | Edit Flow v1 | Not Started | user_action |
| 1.4 | Clicks "+ Create job" button | `Create Job Button Clicked` | Catalog (v2) | Live | Intent |
| 1.5 | Clicks a job card in the list | `Job Post Clicked` | Edit Flow v1 | Not Started | user_action |
| 1.6 | Clicks a job name in Recent sidebar | `Job Post Clicked` | Edit Flow v1 | Not Started | user_action |
| 1.7 | Clicks "+ Post Interview" on a job card | `Post Interview Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 1.8 | Clicks "Copy link" in share modal | `Post Interview Link Copied` | Edit Flow v1 | Not Started | user_action |
| 1.9 | Clicks "Copy message" in share modal | `Job Share Message Copied` | v3 | Not Started | user_action |
| 1.10 | Clicks "Refine with AI" in share modal | `Job Share Message AI Refined` | v3 | Not Started | user_action |
| 1.11 | Clicks LinkedIn / X / Email in share modal | `Job Share Channel Clicked` | v3 | Not Started | user_action |
| 1.12 | Clicks "⋮" kebab → "Archive this job" | `Archive Job Button Clicked` | Catalog (v2) | Live | Intent |
| 1.13 | Clicks "Archive" in confirmation modal → success | `Job Archived` | Edit Flow v1 | Not Started | Success |
| 1.14 | Clicks "Archive" in confirmation modal → failure | `Job Archive Failed` | Edit Flow v1 | Not Started | Failure |
| 1.15 | Types in "Search job postings" search bar | **⚠️ NO EVENT** | — | Gap | — |

### Event Schemas

**1.2 — Job Postings Dashboard Loaded**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `active_tab` | enum | `my_jobs` (default), `shared_with_me`, `archived` | Default tab shown on page load — almost always `my_jobs` |
| `archived_count` | number | `0`–`N` | Count of jobs in Archived tab. `0` for new HMs |
| `current_page_context` | string | `hm_job_postings` | Always this value on this page |
| `entity_type` | string | `job` | Always `job` |
| `has_jobs` | boolean | `true` / `false` | `false` for brand-new HMs. Useful for new-user segmentation |
| `my_jobs_count` | number | `0`–`N` | e.g., `4` (as seen in screenshots). Core engagement metric |
| `previous_page_context` | string | varies | `null` if first page after login, or the previous page context |
| `recent_jobs_count` | number | `0`–`N` | Jobs in the Recent sidebar. May differ from my_jobs_count if includes shared/archived |
| `shared_with_me_count` | number | `0`–`N` | `0` for solo HMs. Non-zero indicates collaboration |
| `total_jobs_count` | number | `0`–`N` | Sum of my_jobs + shared_with_me + archived |

**1.3 — Job Postings Tab Switched**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always `click` |
| `action_value` | string | `my_jobs`, `shared_with_me`, `archived` | Exact tab label in snake_case |
| `component` | string | `job_postings_tab_bar` | Always this value |
| `current_page_context` | string | `hm_job_postings` | Always |
| `entity_type` | string | `job` | Always |
| `previous_page_context` | string | varies | Previous page |
| `selected_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Same as action_value — the now-active tab |
| `tab_job_count` | number | `0`–`N` | Count of jobs in the selected tab. `0` for empty tabs |

**1.5/1.6 — Job Post Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `job_post_card` (from list) or `recent_job_link` (from sidebar) | Distinguishes click source |
| `candidates_count` | number | `0`–`N` | From the job card. `null` for recent sidebar clicks (count not visible there) |
| `component` | string | `job_postings_job_card_list` or `recent_sidebar_nav` | Where the click happened |
| `current_page_context` | string | `hm_job_postings` | Always |
| `entity_type` | string | `job` | Always |
| `entry_point` | enum | `dashboard_job_card` or `recent_sidebar` | **Key analysis property** — answers "where do users click more?" |
| `job_id` | string | UUID | Job being navigated to |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | From the card |
| `previous_page_context` | string | varies | Previous page |
| `views_count` | number | `0`–`N` | From the job card. `null` for recent sidebar clicks |

**1.7 — Post Interview Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `post_interview_button` | Exact button text |
| `component` | string | `job_postings_job_card` | Job card on the dashboard |
| `current_page_context` | string | `hm_job_postings` | Always |
| `entity_type` | string | `job` | Always |
| `is_email_verified` | boolean | `true` / `false` | Whether HM completed email verification for this job. Answers: "Are verified HMs more likely to share?" |
| `job_id` | string | UUID | Which job's interview is being shared |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | varies | Previous page |

**1.13 — Job Archived**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `candidates_count` | number | `0`–`N` | How many candidates were in the pipeline when archived. `0` = no traction |
| `current_page_context` | string | `hm_job_postings` | Always from dashboard |
| `days_since_creation` | number | `0`–`N` | Days since job was created. Short lifespan = potential issue |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Archived job |
| `job_title` | string | e.g., `Product Manager...` | For quick identification |
| `previous_page_context` | string | varies | Previous page |
| `previous_status` | enum | `draft`, `open`, `closed` | What status the job was in before archiving. `draft` = never published |
| `views_count` | number | `0`–`N` | How many views before archive. `0` + archive = job never gained traction |

---

## Page 2: Posted Job Page (`/jobs/{job_id}/candidates`)

**Context:** `hm_job_posting_detail`
**When:** HM clicks a job card from dashboard or Recent sidebar

### Every User Action & Event

| # | User Action | Event Fired | Source Plan | Status | Type |
|---|---|---|---|---|---|
| 2.1 | Page loads | `Page Viewed` | Catalog | Live | page_view |
| 2.2 | Clicks "Job details" (top-right) | `Job Details Button Clicked` | Edit Flow v1 | Not Started | user_action |
| 2.3 | Clicks "Edit" in Job Details panel | `Edit Job Posting Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 2.4 | Clicks "Record" in Job Details panel | `Record Video Button Clicked` | Catalog | Not Started | Intent |
| 2.5 | Clicks "Open preview" in Job Details panel | `Open Preview Button Clicked` | Edit Flow v1 | Not Started | user_action |
| 2.6 | Clicks "Edit intro video" (after video exists) | `Record Video Button Clicked` | Catalog | Not Started | Intent |
| 2.7 | Clicks "Delete" on intro video (no confirmation) | `Intro Video Deleted` | Catalog | Not Started | user_action |
| 2.8 | Clicks "Share" (top-right) | `Share Button Clicked` | Catalog (v2) | Live | Intent |
| 2.9 | Clicks "Copy link" in share modal | `Post Interview Link Copied` | Edit Flow v1 | Not Started | user_action |
| 2.10 | Clicks "Copy message" in share modal | `Job Share Message Copied` | v3 | Not Started | user_action |
| 2.11 | Clicks "Refine with AI" in share modal | `Job Share Message AI Refined` | v3 | Not Started | user_action |
| 2.12 | Clicks LinkedIn / X / Email | `Job Share Channel Clicked` | v3 | Not Started | user_action |
| 2.13 | Clicks "⋮" chevron → "Edit job posting" | `Edit Job Posting Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 2.14 | Clicks "⋮" chevron → "Edit interview" | `Edit Interview Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 2.15 | Clicks "⋮" chevron → "Delete" | `Delete Job Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 2.16 | Clicks "Delete" in confirmation modal → success | `Job Deleted` | Edit Flow v1 | Not Started | Success |
| 2.17 | Clicks "Delete" in confirmation modal → failure | `Job Delete Failed` | Edit Flow v1 | Not Started | Failure |
| 2.18 | Clicks "Invite recruiter" / "Add team members" | `Invite Recruiter Button Clicked` | Edit Flow v1 | Not Started | Intent |
| 2.19 | Clicks "Send invites" in share candidate list modal | `Recruiter Invites Sent` | Edit Flow v1 | Not Started | Success |
| 2.20 | Clicks "Copy link" on a pending invite row | `Recruiter Invite Link Copied` | Edit Flow v1 | Not Started | user_action |
| 2.21 | Clicks "Resend" on a pending invite row | `Recruiter Invite Resent` | Edit Flow v1 | Not Started | user_action |
| 2.22 | Clicks "Revoke" on an invite row | `Recruiter Invite Revoked` | Edit Flow v1 | Not Started | user_action |
| 2.23 | Clicks "View Interview" | `View Interview Button Clicked` | Edit Flow v1 | Not Started | user_action |
| 2.24 | Clicks "Complete intake →" | **⚠️ NO EVENT** | — | Gap | — |
| 2.25 | Clicks "Back" (top-left) | **⚠️ NO EVENT (low priority)** | — | Gap | — |
| 2.26 | Clicks candidate pipeline tabs (My queue / Accepted / Rejected / All) | **⚠️ NO EVENT** | — | Gap | — |
| 2.27 | Clicks "Filter" on candidate list | **⚠️ NO EVENT (low priority)** | — | Gap | — |
| 2.28 | Clicks "Sort by" on candidate list | **⚠️ NO EVENT (low priority)** | — | Gap | — |
| 2.29 | Dismisses "Your job is live" banner (clicks ×) | **⚠️ NO EVENT (low priority)** | — | Gap | — |

### Event Schemas (new events only — see Page 1 for shared events)

**2.2 — Job Details Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `job_details_button` | Always |
| `component` | string | `posted_job_header` | Top-right header |
| `current_page_context` | string | `hm_job_posting_detail` | Always on this page |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |

**2.3/2.13 — Edit Job Posting Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `edit_button` (from panel) or `edit_job_posting` (from chevron) | Distinguishes the two entry points |
| `component` | string | `job_details_panel` or `posted_job_chevron_menu` | Where the click happened |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `entry_point` | enum | `job_details_panel` or `chevron_menu` | Standardized entry point — follows same pattern as `Job Post Clicked` |
| `is_email_verified` | boolean | `true` / `false` | Whether HM completed email verification for this job |
| `job_id` | string | UUID | Job being edited |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | For quick identification |
| `previous_page_context` | string | varies | Previous page |

**2.5 — Open Preview Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `open_preview_button` | Always |
| `component` | string | `job_details_panel` | Job Details side panel |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `has_intro_video` | boolean | `true` / `false` | Whether intro video exists at preview time |
| `job_id` | string | UUID | Job being previewed |
| `previous_page_context` | string | varies | Previous page |

**2.15 — Delete Job Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `delete` | Menu item text |
| `component` | string | `posted_job_chevron_menu` | Always from chevron |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Job to be deleted |
| `job_title` | string | e.g., `Product Manager...` | For identification |
| `previous_page_context` | string | varies | Previous page |

**2.16 — Job Deleted**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `candidates_count` | number | `0`–`N` | Candidates at time of deletion. Non-zero = data loss concern |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `days_since_creation` | number | `0`–`N` | Job lifespan before deletion |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Deleted job |
| `job_title` | string | e.g., `Product Manager...` | For identification |
| `previous_page_context` | string | varies | Previous page |
| `previous_status` | enum | `draft`, `open`, `closed`, `archived` | Status before deletion |
| `views_count` | number | `0`–`N` | Views before deletion |

**2.18 — Invite Recruiter Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `invite_recruiter_button` or `add_team_members_button` | Label changes to "Add team members" after first invite is sent |
| `component` | string | `posted_job_invite_recruiter_card` | "Invite Your Recruiter" card |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `existing_invites_count` | number | `0`–`N` | `0` for first invite, `2` if 2 invites already exist |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |

**2.19 — Recruiter Invites Sent**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `send_invites_button` | Always |
| `component` | string | `share_candidate_list_modal` | Share modal |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `invite_count` | number | `1`–`N` | Number of emails in this batch. e.g., `2` if two emails entered |
| `job_id` | string | UUID | Current job |
| `pending_invites_count` | number | `0`–`N` | Existing pending invites *before* this send |
| `previous_page_context` | string | varies | Previous page |

**2.23 — View Interview Button Clicked**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `view_interview_button` | Always |
| `component` | string | `posted_job_ai_interview_card` | "AI Interview" card |
| `current_page_context` | string | `hm_job_posting_detail` | Always |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |
| `questions_count` | number | e.g., `5`, `7` | Shown on the card (e.g., "5 questions") |

---

## Page 3: Create/Edit Job Posting Wizard (`/hiring-manager/job-posting?jobId=xxx`)

**Context:** Existing wizard page contexts (e.g., `hm_job_creation_wizard_job_details`)
**When:** User enters via "Edit" (Job Details panel) or "Edit job posting" (chevron) — or via "+ Create job" for new jobs

### Every User Action & Event

All existing wizard events (v2 + v3) fire in both create and edit modes. The new `wizard_mode` property distinguishes them.

| # | User Action | Event Fired | Source Plan | Status | Type | Edit Mode Notes |
|---|---|---|---|---|---|---|
| 3.1 | Wizard page loads | `Page Viewed` | Catalog | Live | page_view | |
| 3.2 | Wizard starts | `Job Post Wizard Started` | v2 | Live | Success | `wizard_mode: 'edit'` when editing |
| 3.3 | JD pasted, AI evaluation succeeds | `Job Description Evaluated` | v3 | Not Started | system | Same in edit mode — re-evaluates pasted JD |
| 3.4 | AI evaluation fails | `Job Description Evaluation Failed` | v3 | Not Started | system | Same in edit mode |
| 3.5 | Clicks "View full details" / "View less" | `Job Description Details Toggled` | v3 | Not Started | user_action | Same in edit mode |
| 3.6 | Edits AI-extracted field and blurs | `Job Description Field Edited` | v3 | Not Started | user_action | Same in edit mode |
| 3.7 | Clicks "Next" on Job Details (step 1) | `Job Post Wizard Job Details Completed` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.8 | Backend creates/updates draft | `Job Posting Draft Created` | v2 | Live | Success | Also fires on edit (updates draft) |
| 3.9 | Selects intake mode (step 2) | `Job Post Wizard Intake Mode Selected` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.10 | Sam session starts (voice/text) | `Sam Session Started` | v2 | Live | -- | Same in edit mode |
| 3.11 | Sam session setup fails | `Sam Session Setup Failed` | v3 | Not Started | system | Same in edit mode |
| 3.12 | Sam session ends | `Sam Session Ended` | v2 | Live | -- | Same in edit mode |
| 3.13 | Clicks "Next" on Role Requirements (step 3) | `Job Post Wizard Role Requirements Completed` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.14 | Clicks "+ Add" on role requirements | `Requirement Add Button Clicked` | v2 | Live | -- | Same in edit mode |
| 3.15 | Deletes a role requirement | `Role Requirement Deleted` | v3 | Not Started | user_action | Same in edit mode |
| 3.16 | Edits a role requirement | `Role Requirement Edited` | v3 | Not Started | user_action | Same in edit mode |
| 3.17 | Adds a role requirement | `Role Requirement Added` | v3 | Not Started | user_action | Same in edit mode |
| 3.18 | Clicks "Next" on Interview Questions (step 4) | `Job Post Wizard Interview Questions Completed` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.19 | Clicks "+ Add" on interview questions | `Question Add Button Clicked` | v2 | Live | -- | Same in edit mode |
| 3.20 | Deletes a screening question | `Screening Question Deleted` | v3 | Not Started | user_action | Same in edit mode |
| 3.21 | Edits a screening question | `Screening Question Edited` | v3 | Not Started | user_action | Same in edit mode |
| 3.22 | Adds a screening question | `Screening Question Added` | v3 | Not Started | user_action | Same in edit mode |
| 3.23 | Clicks "Send code" on Verify (step 5) | `Job Verification Code Send Button Clicked` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.24 | Verification succeeds | `Job Post Wizard Verification Completed` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.25 | Clicks "Maybe later" | `Job Post Wizard Verification Skipped` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.26 | Clicks "Back" on any step | `Job Post Wizard Back Button Clicked` | v2 | Live | -- | `wizard_mode: 'edit'` |
| 3.27 | Backend saves screening config | `Screening Configuration Saved` | v2 | Live | -- | Same in edit mode |
| 3.28 | Backend verifies job | `Job Posting Verified` | v2 | Live | Success | Same in edit mode |
| 3.29 | Backend publishes job | `Job Posting Published` | v2 | Live | -- | Same in edit mode |
| 3.30 | Clicks "×" to close wizard | **⚠️ NO EVENT** | — | Gap | — | Abandonment signal |

### `wizard_mode` Property (NEW — applies to ALL wizard events)

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `wizard_mode` | enum | `create`, `edit` | `create` = fresh wizard from "+ Create job". `edit` = re-entering from "Edit" button or "Edit job posting" menu. Derived from `jobId` presence in URL params |

---

## Page 4: Create Intro Video (`/hiring-manager/job-postings/{id}/intro-video`)

**Context:** `hm_intro_video`
**When:** User clicks "Record" in Job Details panel, or "Edit intro video" on existing video

### Every User Action & Event

| # | User Action | Event Fired | Source Plan | Status | Type |
|---|---|---|---|---|---|
| 4.1 | Page loads | `Page Viewed` | Catalog | Live | page_view |
| 4.2 | Clicks "Edit" on script → edits → clicks "Save" | `Intro Script Updated` | Catalog + Edit Flow v1 (enriched) | Not Started | -- |
| 4.3 | Clicks "Regenerate" → enters instruction → clicks "Regenerate" | `Intro Script Updated` | Catalog + Edit Flow v1 (enriched) | Not Started | -- |
| 4.4 | Clicks red "Record" button | `Intro Video Recording Started` | Edit Flow v1 | Not Started | user_action |
| 4.5 | Clicks "Stop" (stops recording) | **⚠️ NO EVENT (not needed)** | — | — | — |
| 4.6 | Clicks "Choose new frame" | **⚠️ NO EVENT (too granular)** | — | — | — |
| 4.7 | Clicks "Use this frame" | **⚠️ NO EVENT (too granular)** | — | — | — |
| 4.8 | Clicks "Use this take" → video uploads | `Intro Video Created` | Catalog + Edit Flow v1 (enriched) | Not Started | Success |
| 4.9 | Clicks "Re-record" | **⚠️ NO EVENT (not needed — next Record click tracked)** | — | — | — |
| 4.10 | Clicks "×" to close without saving | **⚠️ NO EVENT (low priority)** | — | Gap | — |

### Event Schemas

**4.2/4.3 — Intro Script Updated**

**Guard: only fires when the script text actually changed from the original.** If user clicks Edit → doesn't change → clicks Save, the event is skipped. Same guard pattern as v3's `Role Requirement Edited` and `Screening Question Edited`.

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Always on this page |
| `edit_method` | enum | `text` or `ai_regenerate` | `text` = manual edit + Save. `ai_regenerate` = Regenerate modal |
| `entity_type` | string | `job` | Always |
| `has_ai_instruction` | boolean | `true` / `false` | `true` if user typed instruction in regenerate modal. `false` if left blank (full regeneration from scratch). Only relevant when `edit_method = 'ai_regenerate'` |
| `job_id` | string | UUID | Current job |
| `original_script_length` | number | e.g., `410` | Character count of script BEFORE the edit. Compare with `script_length` to see if scripts grow or shrink |
| `previous_page_context` | string | varies | Previous page |
| `script_length` | number | e.g., `450` | Character count of script AFTER save/regeneration |

**4.4 — Intro Video Recording Started**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `record_button` | Red record button |
| `component` | string | `intro_video_recorder` | Video recorder |
| `current_page_context` | string | `hm_intro_video` | Always |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |
| `script_length` | number | e.g., `450` | Script length at time of recording — did user record with the default or edited script? |
| `takes_count` | number | `0`, `1`, `2`... | `0` on first attempt. Increments with each "Re-record" → "Record" cycle |

**4.8 — Intro Video Created**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Always |
| `duration_seconds` | number | e.g., `45` | Video duration. Short = low effort, long = high engagement |
| `entity_type` | string | `job` | Always |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |
| `takes_count` | number | `1`–`N` | Total takes before saving. `1` = nailed it first try. `5` = perfectionist |

---

## Page 5: Edit Interview (`/hiring-manager/job-postings/{id}/create-interview`)

**Context:** `hm_edit_interview`
**When:** User clicks "Edit interview" from the chevron menu

### Every User Action & Event

| # | User Action | Event Fired | Source Plan | Status | Type |
|---|---|---|---|---|---|
| 5.1 | Step 1 page loads | `Page Viewed` | Catalog | Live | page_view |
| 5.2 | Changes interview name | **No event (captured on Next)** | — | — | — |
| 5.3 | Changes resume upload option | **No event (captured on Next)** | — | — | — |
| 5.4 | Toggles government ID verification | **No event (captured on Next)** | — | — | — |
| 5.5 | Clicks "Next" on step 1 | `Interview Details Completed` | Edit Flow v1 | Not Started | user_action |
| 5.6 | Step 2 page loads | `Page Viewed` | Catalog | Live | page_view |
| 5.7 | Adds a screening question | **⚠️ NO EVENT** | — | Gap | — |
| 5.8 | Adds an assessment question | **⚠️ NO EVENT** | — | Gap | — |
| 5.9 | Deletes a question | **⚠️ NO EVENT** | — | Gap | — |
| 5.10 | Reorders a question | **⚠️ NO EVENT** | — | Gap | — |
| 5.11 | Clicks "Create Interview" | `Interview Saved` | Edit Flow v1 | Not Started | Success |
| 5.12 | Clicks "Back" on step 2 | **⚠️ NO EVENT (low priority)** | — | Gap | — |

### Event Schemas

**5.5 — Interview Details Completed**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `next_button` | Always |
| `component` | string | `edit_interview_details_step` | Step 1 |
| `current_page_context` | string | `hm_edit_interview` | Always |
| `entity_type` | string | `job` | Always |
| `identity_verification_mode` | enum | `require` or `off` | `require` = gov ID checkbox is ticked. `off` = unticked |
| `interview_name` | string | e.g., `Initial screening` | What the HM named the interview |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |
| `resume_upload_option` | enum | `yes_optional`, `yes_required`, `no_resume_upload` | Which radio button is selected |

**5.11 — Interview Saved**

| Property | Type | Expected Values | When/Why |
|---|---|---|---|
| `action` | enum | `click` | Always |
| `action_value` | string | `create_interview_button` | Button text |
| `assessment_questions_count` | number | `0`–`N` | e.g., `3`. Behavioral questions answered via voice/writing |
| `component` | string | `edit_interview_questions_step` | Step 2 |
| `current_page_context` | string | `hm_edit_interview` | Always |
| `entity_type` | string | `job` | Always |
| `identity_verification_mode` | enum | `require`, `off` | Carried from step 1 |
| `interview_name` | string | e.g., `Initial screening` | Carried from step 1 |
| `job_id` | string | UUID | Current job |
| `previous_page_context` | string | varies | Previous page |
| `resume_upload_option` | enum | `yes_optional`, `yes_required`, `no_resume_upload` | Carried from step 1 |
| `screening_questions_count` | number | `0`–`N` | e.g., `3`. Yes/No quick screen questions |
| `total_questions_count` | number | `0`–`N` | Sum of screening + assessment |

---

## Page 6: Share Interview Modal (appears on multiple pages)

**Context:** Inherits from parent page (`hm_job_postings`, `hm_job_posting_detail`, or `hm_job_creation_wizard_success`)
**When:** Opened via "+ Post Interview" (dashboard), "Share" (posted job page), or "Share →" (wizard success page)

### Every User Action & Event

| # | User Action | Event Fired | Source Plan | Status | Context |
|---|---|---|---|---|---|
| 6.1 | Modal opens (from wizard success) | `Success Page Share Button Clicked` | v3 | Not Started | `hm_job_creation_wizard_success` |
| 6.2 | Modal opens (from dashboard) | `Post Interview Button Clicked` | Edit Flow v1 | Not Started | `hm_job_postings` |
| 6.3 | Modal opens (from posted job page) | `Share Button Clicked` | Catalog (v2) | Live | `hm_job_posting_detail` |
| 6.4 | Clicks "Copy link" (interview URL) | `Post Interview Link Copied` | Edit Flow v1 | Not Started | Inherits from parent |
| 6.5 | Clicks "Copy message" | `Job Share Message Copied` | v3 | Not Started | Inherits from parent |
| 6.6 | Clicks "Refine with AI" → "Generate message" | `Job Share Message AI Refined` | v3 | Not Started | Inherits from parent |
| 6.7 | Clicks LinkedIn / X / Email | `Job Share Channel Clicked` | v3 | Not Started | Inherits from parent |
| 6.8 | Clicks "Done" | **⚠️ NO EVENT (not needed)** | — | — | — |

---

## Gaps Identified

### Intentional Gaps (reviewed, decided not to track)

| # | Page | User Action | Suggested Event | Decision |
|---|---|---|---|---|
| G1 | Posted Job Page | Clicks "Complete intake →" | `Complete Intake Button Clicked` | **Intentional gap** — deferred for now |
| G2 | Edit Interview (step 2) | Adds/deletes/reorders questions | `Interview Question Modified` | **Intentional gap** — `Interview Saved` captures final state, granular CRUD deferred |
| G3 | Posted Job Page | Switches candidate pipeline tabs | `Candidate Pipeline Tab Switched` | **Intentional gap** — deferred for now |

### Low Priority (can defer)

| # | Page | User Action | Suggested Event | Why |
|---|---|---|---|---|
| G4 | Dashboard | Types in search box | `Job Search Performed` | Useful at scale but low priority with <50 jobs per HM |
| G5 | Wizard | Clicks "×" to close wizard | `Job Post Wizard Abandoned` | Measures wizard abandonment (mid-flow exits). Currently only measurable via funnel drop-off |
| G6 | Intro Video | Clicks "×" without saving | `Intro Video Abandoned` | Same concept — page exit without recording |
| G7 | Posted Job Page | Clicks "Back" | Not needed | `Page Viewed` on dashboard captures the navigation |
| G8 | Posted Job Page | Dismisses "Your job is live" banner | Not needed | Low analytical value |

---

## Cross-Plan Sync Issues

### Issue 1: `wizard_mode` must propagate to v3 events

**Problem:** The Edit Flow v1 plan adds `wizard_mode` to v2 wizard events, but v3 events (`Job Description Evaluated`, `Job Description Details Toggled`, `Job Description Field Edited`, `Role Requirement Deleted/Edited/Added`, `Screening Question Deleted/Edited/Added`, `Sam Session Setup Failed`) fire WITHIN the wizard and don't mention `wizard_mode`.

**Fix:** Add `wizard_mode: 'create' | 'edit'` to ALL v3 events that fire inside the wizard. This is critical — without it, analysts can't distinguish edits from first-time creation in the v3 events.

**Affected v3 events (all 11 wizard-context events):**
- `Job Description Evaluated`
- `Job Description Evaluation Failed`
- `Job Description Details Toggled`
- `Job Description Field Edited`
- `Sam Session Setup Failed`
- `Role Requirement Deleted`
- `Role Requirement Edited`
- `Role Requirement Added`
- `Screening Question Deleted`
- `Screening Question Edited`
- `Screening Question Added`

### Issue 2: `Record Video Button Clicked` needs `entry_context` for edit vs new — ✅ RESOLVED

**Problem:** The catalog's `Record Video Button Clicked` fires both when clicking "Record" in Job Details panel (no video exists yet) and when clicking "Edit intro video" (video already exists). These are different intents but the same event.

**Fix:** Added `has_existing_video: boolean` and distinct `action_value` (`record_button` vs `edit_intro_video`) to the tracking plan. Implemented in Edit Flow v1.

### Issue 3: Share modal events need consistent `current_page_context`

**Problem:** The v3 share modal events (`Job Share Message AI Refined`, `Job Share Message Copied`, `Job Share Channel Clicked`) were implemented with hardcoded `current_page_context: JOB_WIZARD_PAGE_CONTEXTS.success`. When the same modal opens from the dashboard or posted job page, the context must be dynamic.

**Fix:** Already documented in the Edit Flow v1 tracking plan's "Existing Events Used from Different Context" section. Implementation needs to parameterize the context.

### Issue 4: `Post Interview Link Copied` fires from multiple pages

**Problem:** The "Copy link" button in the share modal copies the interview URL. This fires `Post Interview Link Copied` from three different contexts: wizard success page, dashboard, and posted job page.

**Status:** Already handled — `current_page_context` distinguishes the source. No change needed.

### Issue 5: v3's `Team Member Invite Sent` vs Edit Flow v1's `Recruiter Invites Sent`

**Problem:** v3 defines `Team Member Invite Sent` (frontend, from wizard success page, per-invite via mailto) and the Edit Flow v1 defines `Recruiter Invites Sent` (frontend, from posted job page, batch via API). These are different flows but similar names.

**Clarification:**
- `Team Member Invite Sent` (v3) — wizard success page → mailto link, `invite_count: 1`, `invite_role: recruiter/other`
- `Recruiter Invites Sent` (Edit Flow v1) — posted job page → API batch, `invite_count: 1-N`
- `Team Member Invited` (catalog, backend, Live) — fires per-invite from the server

These are three distinct events at different layers. No conflict, but worth documenting for clarity.

---

## Property Improvement Suggestions

### 1. Add `job_age_days` to all posted job page events

**Current:** Only `Job Archived` and `Job Deleted` have `days_since_creation`.
**Suggestion:** Add `job_age_days` (or rename `days_since_creation` to `job_age_days` for consistency) to all events fired on the posted job page: `Job Details Button Clicked`, `Invite Recruiter Button Clicked`, `View Interview Button Clicked`, `Edit Job Posting Button Clicked`, etc.
**Why:** Enables analysis like "Do HMs engage more with job settings in the first week vs after 30 days?" and "At what job age do HMs typically invite recruiters?"

### 2. Add `candidates_count` to more posted job page events

**Current:** Only `Job Archived`, `Job Deleted`, and `Job Post Clicked` carry `candidates_count`.
**Suggestion:** Add to `Invite Recruiter Button Clicked`, `View Interview Button Clicked`, `Edit Job Posting Button Clicked`, `Edit Interview Button Clicked`.
**Why:** Segments actions by pipeline stage. "Do HMs edit interviews before or after getting candidates?" "Do HMs invite recruiters when they have 0 candidates vs many?"

### 3. Add `team_members_count` to posted job page events

**Current:** No event carries this.
**Suggestion:** Add to `Job Postings Dashboard Loaded` (per-job) and key posted job page events.
**Why:** Distinguishes solo HMs from collaborative ones. "Do HMs with team members archive less?"

### 4. Add `has_intro_video` to more events

**Current:** Only `Open Preview Button Clicked`.
**Suggestion:** Add to `Job Post Clicked`, `Job Postings Dashboard Loaded` (as aggregate `jobs_with_intro_video_count`), `Share Button Clicked`, `Post Interview Button Clicked`.
**Why:** Measures intro video adoption impact. "Are jobs with intro videos shared more often?"

### 5. Add `intake_mode` to posted job page events

**Current:** Only on wizard/backend events.
**Suggestion:** Add to `Job Post Clicked`, `View Interview Button Clicked`.
**Why:** Segments by how the job was created. "Do AI copilot jobs get more interview views?"

### 6. Add `is_email_verified` to posted job page events — ✅ IMPLEMENTED

**Current:** Only on backend events (as `job_verified`).
**Implemented:** Added `is_email_verified: boolean` to `Post Interview Button Clicked` and `Edit Job Posting Button Clicked`.
**Why:** "Are verified HMs more likely to share/edit jobs?" Helps measure verification ROI.

### 7. Add script change guard to `Intro Script Updated` — ✅ IMPLEMENTED

**Current:** Event fires on save regardless.
**Implemented:** Added guard — event only fires when script text actually changed. Added `original_script_length` property so analysts can compare before/after without storing full text. Follows v3's `Role Requirement Edited` and `Screening Question Edited` pattern.

### 8. Standardize `entry_point` usage across the flow — ✅ IMPLEMENTED

**Current:** `Job Post Clicked` uses `entry_point: 'dashboard_job_card' | 'recent_sidebar'`.
**Implemented:** Added `entry_point: 'job_details_panel' | 'chevron_menu'` to `Edit Job Posting Button Clicked`. `component` kept alongside for specificity. Follows existing `entry_point` pattern from `Page Viewed`, `Login Started`, and `Job Post Clicked`.

---

## Summary Statistics

| Category | Count |
|---|---|
| **Total unique events across all pages** | **60+** (catalog + v2 + v3 + edit flow v1) |
| **Events in this tracking plan (Edit Flow v1)** | 23 new + 4 enrichments |
| **Events from v3 (wizard enrichments)** | 18 |
| **Events from v2/catalog (existing Live)** | 27 |
| **Intentional gaps (deferred)** | 3 |
| **Low-priority gaps (deferred)** | 5 |
| **Cross-plan sync issues** | 5 (2 resolved, 3 pending) |
| **Property improvements** | 8 (3 implemented, 5 open suggestions) |
