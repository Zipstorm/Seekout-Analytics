# Tracking Plan: HM Job Posting Management

**Product:** Helix (SeekOut.ai)
**Feature:** Job Postings dashboard, archive flow, posted job page, and recruiter invite lifecycle
**Date:** 2026-06-07
**Related PRD:** —
**Scope:** 23 new events + 4 existing event modifications for the hiring manager job posting management pages: dashboard state + tab switching (2), job archive flow (2), Post Interview button + link copy (2), job post navigation (1), posted job page actions (2), recruiter invite lifecycle (4), posted job header actions (3), intro video script + recording (2 existing enrichments), edit interview flow (3), delete job flow (3). Also modifies all wizard events to support edit mode via `wizard_mode` property.

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.
> Reference: `tracking-plans/hm-job-creation-wizard-v3.md` for the v3 wizard tracking plan (18 events).

---

## User Flow

```text
HM Login (current role: Hiring Manager)
  │
  └─ Job Postings Dashboard  (/hiring-manager/job-postings)
       │
       ├─ Page loads
       │    → fires: Page Viewed (existing, Live)
       │    → fires: Job Postings Dashboard Loaded  ← NEW EVENT
       │
       ├─ User switches tabs: My jobs │ Shared with me │ Archived
       │    → fires: Job Postings Tab Switched  ← NEW EVENT
       │
       ├─ User clicks "⋮" kebab → "Archive this job"
       │    → fires: Archive Job Button Clicked (existing, Live)
       │    → confirmation modal opens
       │    └─ User clicks "Archive" → API call
       │         ├─ success → fires: Job Archived  ← NEW EVENT
       │         └─ failure → fires: Job Archive Failed  ← NEW EVENT
       │
       ├─ User clicks "+ Post Interview" on a job card
       │    → fires: Post Interview Button Clicked  ← NEW EVENT
       │    → share modal opens (v3 share events fire with hm_job_postings context)
       │    └─ User clicks "Copy link"
       │         → fires: Post Interview Link Copied  ← NEW EVENT
       │
       ├─ User clicks a job card (dashboard list)
       │    → fires: Job Post Clicked (entry_point: dashboard_job_card)  ← NEW EVENT
       │    → navigates to posted job page
       │
       └─ User clicks a job name (Recent sidebar)
            → fires: Job Post Clicked (entry_point: recent_sidebar)  ← NEW EVENT
            → navigates to posted job page


Posted Job Page  (/jobs/{job_id}/candidates)
  │
  ├─ Page loads
  │    → fires: Page Viewed (existing, Live)
  │
  ├─ User clicks "Invite recruiter"
  │    → fires: Invite Recruiter Button Clicked  ← NEW EVENT
  │    → "Share candidate list" modal opens
  │    │
  │    ├─ User enters emails → clicks "Send invites"
  │    │    ├─ success → fires: Recruiter Invites Sent  ← NEW EVENT
  │    │    │           → also fires: Team Member Invited (existing, Live, backend, per invite)
  │    │    └─ failure → fires: Team Member Invite Failed (existing, Live, backend)
  │    │
  │    ├─ User clicks "Copy link" on a pending invite
  │    │    → fires: Recruiter Invite Link Copied  ← NEW EVENT
  │    │
  │    ├─ User clicks "Resend" on a pending invite
  │    │    → fires: Recruiter Invite Resent  ← NEW EVENT
  │    │
  │    └─ User clicks "Revoke" on a pending invite
  │         → fires: Recruiter Invite Revoked  ← NEW EVENT
  │
  └─ User clicks "View Interview"
       → fires: View Interview Button Clicked  ← NEW EVENT
```

---

## Page Contexts

| Page | URL Pattern | `current_page_context` |
|------|------------|----------------------|
| Job Postings Dashboard | `/hiring-manager/job-postings` | `hm_job_postings` |
| Posted Job Page | `/jobs/{job_id}/candidates` | `hm_job_posting_detail` |
| Create/Edit Job Posting (wizard) | `/hiring-manager/job-posting?jobId={id}` | Existing wizard page contexts (with `wizard_mode: 'edit'`) |
| Create Intro Video | `/hiring-manager/job-postings/{id}/intro-video` | `hm_intro_video` |
| Edit Interview | `/hiring-manager/job-postings/{id}/create-interview` | `hm_edit_interview` |

---

## Existing Events (no changes)

| Event | Status | Notes |
|-------|--------|-------|
| `Page Viewed` | Live | Fires on both dashboard and posted job page with respective `current_page_context` |
| `Archive Job Button Clicked` | Live | Intent for archive — fires when user clicks "Archive this job" in kebab menu |
| `Job Status Changed` | Live | Backend event — fires when job status transitions (including to `archived`) |
| `Team Member Invited` | Live | Backend event — fires per invite when server confirms delivery |
| `Team Member Invite Failed` | Live | Backend event — fires when invite fails |

---

## Existing Events Used from Different Context

The v3 share modal events fire from the Post Interview modal on the dashboard with `current_page_context: 'hm_job_postings'` instead of `'hm_job_creation_wizard_success'`. No new events needed — the `current_page_context` property already distinguishes the source.

| v3 Event | Original Context | New Context |
|----------|-----------------|-------------|
| `Job Share Message AI Refined` | `hm_job_creation_wizard_success` | `hm_job_postings` |
| `Job Share Message Copied` | `hm_job_creation_wizard_success` | `hm_job_postings` |
| `Job Share Channel Clicked` | `hm_job_creation_wizard_success` | `hm_job_postings` |

> **Implementation note:** The v3 implementation hardcodes `JOB_WIZARD_PAGE_CONTEXTS.success` for these events. The code needs to accept `current_page_context` as a parameter so the same modal can fire events from either page.

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Job Archive | Job archive lifecycle | Job Archive Failed |
| Job Post | Individual job posting card/link | Job Post Clicked |
| Job Postings Dashboard | HM job postings homepage | Job Postings Dashboard Loaded |
| Job Postings Tab | Tab bar on job postings dashboard | Job Postings Tab Switched |
| Invite Recruiter Button | Invite recruiter CTA on posted job page | Invite Recruiter Button Clicked |
| Post Interview Button | Post interview CTA on job card | Post Interview Button Clicked |
| Post Interview Link | Shareable interview URL | Post Interview Link Copied |
| Recruiter Invite | Recruiter invite lifecycle (single) | Recruiter Invite Resent, Recruiter Invite Revoked |
| Recruiter Invite Link | Recruiter invite shareable URL | Recruiter Invite Link Copied |
| Recruiter Invites | Recruiter invite batch action | Recruiter Invites Sent |
| View Interview Button | View interview CTA on posted job page | View Interview Button Clicked |
| Job Details Button | Job details panel CTA on posted job page | Job Details Button Clicked |
| Edit Job Posting Button | Edit job posting CTA | Edit Job Posting Button Clicked |
| Open Preview Button | Public preview CTA in job details panel | Open Preview Button Clicked |
| Edit Interview Button | Edit interview CTA in chevron menu | Edit Interview Button Clicked |
| Interview Details | Interview config step 1 | Interview Details Completed |
| Interview | Interview creation/edit lifecycle | Interview Saved |
| Delete Job Button | Delete job CTA in chevron menu | Delete Job Button Clicked |
| Intro Video Recording | Intro video recording action | Intro Video Recording Started |
| Job Delete | Job deletion lifecycle | Job Delete Failed |

## New Events

### 1. Job Postings Dashboard Loaded

Fires on page load of the Job Postings dashboard. Captures the dashboard state — job counts per tab — so analysts can understand the HM's portfolio at time of visit. Answers: "How many jobs does a typical HM have?", "What % of HMs have shared jobs?", "What % have archived jobs?"

| Field | Value |
|-------|-------|
| **Event** | `Job Postings Dashboard Loaded` |
| **Area** | Hiring |
| **Type** | -- (system, page load companion) |
| **Trigger** | Job Postings page mounts and job data loads |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `active_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Default tab shown on load (typically `my_jobs`) |
| `archived_count` | number | e.g., `2` | Number of archived jobs |
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `has_jobs` | boolean | `true`/`false` | Whether the user has any jobs at all (useful for new-user segmentation) |
| `my_jobs_count` | number | e.g., `4` | Number of jobs the user created |
| `previous_page_context` | string | snake_case or null | Previous page |
| `recent_jobs_count` | number | e.g., `4` | Number of jobs shown in the Recent sidebar |
| `shared_with_me_count` | number | e.g., `0` | Number of jobs shared with the user |
| `total_jobs_count` | number | e.g., `6` | Sum of my_jobs + shared_with_me + archived |

---

### 2. Job Postings Tab Switched

User switches between the "My jobs", "Shared with me", and "Archived" tabs on the dashboard. Measures which tab users visit most and how often they check shared or archived jobs.

| Field | Value |
|-------|-------|
| **Event** | `Job Postings Tab Switched` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks a different tab (My jobs, Shared with me, or Archived) |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `my_jobs` / `shared_with_me` / `archived` | Tab clicked (exact tab label in snake_case) |
| `component` | string | `job_postings_tab_bar` | Tab bar on dashboard |
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `previous_page_context` | string | snake_case or null | Previous page |
| `selected_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Same as action_value — the tab now active |
| `tab_job_count` | number | e.g., `4` | Number of jobs shown in the selected tab |

---

### 3. Job Archived

Job successfully archived after the user confirms in the "Archive job" confirmation modal. The intent event `Archive Job Button Clicked` (already Live) fires when the user first clicks "Archive this job" in the kebab menu. This event fires only after the API confirms the archive.

| Field | Value |
|-------|-------|
| **Event** | `Job Archived` |
| **Area** | Hiring |
| **Type** | Success (for Archive Job Button Clicked) |
| **Trigger** | User clicks "Archive" in confirmation modal AND API confirms the job is archived |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `candidates_count` | number | e.g., `0` | Total candidates in the funnel at time of archive |
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `days_since_creation` | number | e.g., `12` | Days between job creation and archive (measures job lifespan) |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `previous_status` | enum | `draft`, `open`, `closed` | Job status before archive |
| `views_count` | number | e.g., `0` | Number of views the job had before archive |

---

### 4. Job Archive Failed

Archive API call fails. Pairs with `Archive Job Button Clicked` (intent) and `Job Archived` (success).

| Field | Value |
|-------|-------|
| **Event** | `Job Archive Failed` |
| **Area** | Hiring |
| **Type** | Failure (for Archive Job Button Clicked) |
| **Trigger** | User clicks "Archive" in confirmation modal AND API returns an error |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `network`, `permission`, `server`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Job has active candidates` | Human-readable error |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 5. Post Interview Button Clicked

User clicks the "+ Post Interview" button on a job card on the dashboard. Opens the share interview modal. Intent event — measures how often HMs want to share their job interviews from the dashboard (vs. from the wizard success page).

| Field | Value |
|-------|-------|
| **Event** | `Post Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "+ Post Interview" on a job card |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `post_interview_button` | Button text |
| `component` | string | `job_postings_job_card` | Job card on the dashboard list |
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 6. Post Interview Link Copied

User clicks "Copy link" in the Post Interview share modal to copy the shareable interview URL. Different from `Job Share Message Copied` (v3) which copies the text message body.

| Field | Value |
|-------|-------|
| **Event** | `Post Interview Link Copied` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Copy link" in the Post Interview / share interview modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `copy_link_button` | Button text |
| `component` | string | `share_interview_modal` | Share modal |
| `current_page_context` | string | `hm_job_postings` or `hm_job_creation_wizard_success` | Page that opened the modal |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Note:** This event can also fire from the wizard success page share modal. The `current_page_context` distinguishes the source.

---

### 7. Job Post Clicked

User clicks a job to navigate to the posted job detail page. Two entry points: clicking a job card on the dashboard list, or clicking a job name in the Recent sidebar. The `entry_point` property distinguishes these — answers: "Are jobs opened more via the dashboard list or via Recent?"

| Field | Value |
|-------|-------|
| **Event** | `Job Post Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks a job card on the dashboard OR a job name in the Recent sidebar |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `job_post_card` or `recent_job_link` | What was clicked |
| `candidates_count` | number | e.g., `0` | Candidates count shown on the card (dashboard only, null for recent) |
| `component` | string | `job_postings_job_card_list` or `recent_sidebar_nav` | Where the click happened |
| `current_page_context` | string | `hm_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | enum | `dashboard_job_card`, `recent_sidebar` | Which UI element was clicked |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `views_count` | number | e.g., `0` | Views count shown on the card (dashboard only, null for recent) |

---

### 8. Invite Recruiter Button Clicked

User clicks "Invite recruiter" on the posted job page. Opens the "Share candidate list" modal. Intent event for the recruiter invite flow.

> **Note:** Replaces the catalog's `Invite Button Clicked` (Not Started, never implemented). See "Existing Event Removal" section below.

| Field | Value |
|-------|-------|
| **Event** | `Invite Recruiter Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Invite recruiter" button on the posted job page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `invite_recruiter_button` | Button text |
| `component` | string | `posted_job_invite_recruiter_card` | "Invite Your Recruiter" card on posted job page |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `existing_invites_count` | number | e.g., `2` | Number of existing invites (pending + accepted + revoked) at time of click |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 9. View Interview Button Clicked

User clicks "View Interview" on the posted job page to view the AI interview questions. Navigation/engagement signal — measures how often HMs review their interview setup after publishing.

| Field | Value |
|-------|-------|
| **Event** | `View Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "View Interview" button on the posted job page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `view_interview_button` | Button text |
| `component` | string | `posted_job_ai_interview_card` | "AI Interview" card on posted job page |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `questions_count` | number | e.g., `7` | Number of interview questions (shown on the card) |

---

### 10. Recruiter Invites Sent

User clicks "Send invites" in the "Share candidate list" modal and invites are successfully created. This is a frontend batch event capturing the user's action; `Team Member Invited` (existing, Live) fires per-invite on the backend.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invites Sent` |
| **Area** | Hiring |
| **Type** | Success (for Invite Recruiter Button Clicked) |
| **Trigger** | User clicks "Send invites" and the API confirms invites are created |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `send_invites_button` | Button text |
| `component` | string | `share_candidate_list_modal` | Share candidate list modal |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_count` | number | e.g., `2` | Number of email addresses submitted in this batch |
| `job_id` | string | UUID | Job identifier |
| `pending_invites_count` | number | e.g., `0` | Number of already-pending invites before this send (measures repeat inviting) |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 11. Recruiter Invite Link Copied

User clicks "Copy link" on a pending invite row in the "Share candidate list" modal. Copies the unique recruiter invite URL.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Link Copied` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Copy link" on an invite row in the Share candidate list modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `copy_link_button` | Button text |
| `component` | string | `share_candidate_list_modal_invite_row` | Individual invite row in the modal |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | `pending`, `accepted` | Status of the invite when link was copied |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 12. Recruiter Invite Resent

User clicks "Resend" on a pending invite. Fires after the API confirms the invite was resent (notification "Invite resent" appears).

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Resent` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Resend" on a pending invite AND API confirms resend |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `resend_button` | Button text |
| `component` | string | `share_candidate_list_modal_invite_row` | Individual invite row |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | `pending` | Always pending — only pending invites can be resent |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 13. Recruiter Invite Revoked

User clicks "Revoke" on an invite and the API confirms the revocation. The invite status changes to "revoked" and the invitee can no longer access the candidate list.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Revoked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Revoke" on an invite AND API confirms revocation |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `revoke_button` | Button text |
| `component` | string | `share_candidate_list_modal_invite_row` | Individual invite row |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | `pending`, `accepted` | Status before revocation (revoked invites can't be revoked again) |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

## Recommendation: Revoked Invitee Page

When a revoked invitee clicks their invite link, they see an "Invite revoked" error page. **Recommendation: Do not add a dedicated event.** `Page Viewed` with `current_page_context: 'invite_revoked'` is sufficient to track volume. This is a dead-end page with no user actions — a dedicated event adds noise without analytical value. If you later need to measure revoked-link click rates, you can query `Page Viewed` filtered by this context.

---

## Posted Job Page — Header Actions & Flows

### 14. Job Details Button Clicked

User clicks "Job details" button in the top-right of the posted job page. Opens the Job Details side panel showing job info, members, intro video, and public preview options.

| Field | Value |
|-------|-------|
| **Event** | `Job Details Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Job details" button in the posted job page header |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `job_details_button` | Button text |
| `component` | string | `posted_job_header` | Top-right header bar |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 15. Edit Job Posting Button Clicked

User clicks "Edit" in the Job Details panel or "Edit job posting" in the chevron menu. Opens the job post wizard in **edit mode**. The `component` property distinguishes the entry point.

| Field | Value |
|-------|-------|
| **Event** | `Edit Job Posting Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Edit" in Job Details panel or "Edit job posting" in chevron menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `edit_button` or `edit_job_posting` | Which button was clicked |
| `component` | string | `job_details_panel` or `posted_job_chevron_menu` | Where the click happened |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 16. Open Preview Button Clicked

User clicks "Open preview" in the Job Details panel. Opens the candidate-facing preview in a new tab. Measures how often HMs review what candidates will see.

| Field | Value |
|-------|-------|
| **Event** | `Open Preview Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Open preview" in the Job Details panel |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `open_preview_button` | Button text |
| `component` | string | `job_details_panel` | Job Details side panel |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `has_intro_video` | boolean | `true`/`false` | Whether an intro video exists at time of preview |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

## Existing Event Modification: Wizard Edit Mode

All existing `Job Post Wizard *` events gain a new property `wizard_mode` to distinguish first-time creation from post-publish edits. The wizard UI is identical — only the intent differs.

**Add to ALL existing wizard events:**

| Property | Type | Values | Description |
|---|---|---|---|
| `wizard_mode` | enum | `create`, `edit` | `create` when entering the wizard for a new job (existing behavior). `edit` when entering from "Edit" in Job Details panel or "Edit job posting" in chevron menu. |

**Affected events:** `Job Post Wizard Started`, `Job Post Wizard Job Details Completed`, `Job Post Wizard Intake Mode Selected`, `Job Post Wizard Role Requirements Completed`, `Job Post Wizard Interview Questions Completed`, `Job Post Wizard Verification Completed`, `Job Post Wizard Verification Skipped`, `Job Post Wizard Back Button Clicked`

> **Implementation note:** The wizard URL includes `?jobId=xxx` when editing an existing job. The `wizard_mode` can be derived from whether `jobId` is present in the URL params or router state.

---

## Intro Video Flow

The intro video page (`/hiring-manager/job-postings/{id}/intro-video`) lets the HM create a video introduction for candidates. The catalog already defines `Record Video Button Clicked`, `Intro Script Updated`, `Intro Video Created`, and `Intro Video Deleted` (all Not Started). This plan enriches them with the properties needed for implementation.

### Existing Event Enrichment: Record Video Button Clicked

Already in catalog (Not Started). Fires when user clicks "Record" in the Job Details panel, navigating to the intro video page.

**Enriched Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `record_button` | Button text |
| `component` | string | `job_details_panel_intro_video` | Intro video section in Job Details panel |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### Existing Event Enrichment: Intro Script Updated

Already in catalog (Not Started, has `job_id` and `edit_method`). Fires when the user saves a manual text edit (clicks "Save") OR completes an AI regeneration (clicks "Regenerate" in the regenerate modal). Single event with `edit_method` property to distinguish.

**Enriched Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `edit_method` | enum | `text`, `ai_regenerate` | `text` = manual edit + Save. `ai_regenerate` = Regenerate modal + Regenerate button |
| `entity_type` | string | `job` | Business object context |
| `has_ai_instruction` | boolean | `true`/`false` | Whether user provided instruction text in the regenerate modal (false if left blank) |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Character count of the script after save/regeneration |

> **Note:** The catalog already defines `edit_method` with values `text`, `voice`. For the intro video context, `ai_regenerate` is a new allowed value. `voice` is not applicable here.

---

### Existing Event Enrichment: Intro Video Created

Already in catalog (Not Started, has `job_id`, `duration_seconds`, `takes_count`). Fires when user clicks "Use this take" after recording. The video is uploaded and attached to the job post.

**Enriched Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `duration_seconds` | number | e.g., `45` | Video duration (already in catalog) |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `takes_count` | number | e.g., `3` | Number of recording takes before save (already in catalog) |

---

### Existing Event: Intro Video Deleted

Already in catalog (Not Started, has `job_id`). Fires when user clicks "Delete" in the intro video kebab menu. **No confirmation dialog** — deletes immediately.

> **Note:** No property enrichment needed beyond what the catalog already defines. The `current_page_context` will be `hm_job_posting_detail` (delete happens from the Job Details panel).

---

### 17. Intro Video Recording Started

User clicks the red "Record" button on the intro video page to begin recording. This is distinct from `Record Video Button Clicked` (which fires when the user clicks "Record" in the Job Details panel to navigate to the intro video page). This event captures that the user actually started a recording attempt — useful for measuring the drop-off between visiting the page and recording.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Recording Started` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks the red "Record" button on the intro video page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `record_button` | Red record button |
| `component` | string | `intro_video_recorder` | Video recorder on the intro video page |
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Character count of the script at time of recording |
| `takes_count` | number | e.g., `0` | Number of previous takes in this session (0 for first attempt) |

---

## Edit Interview Flow

The "Edit interview" option in the chevron menu opens a 2-step interview editor (`/hiring-manager/job-postings/{id}/create-interview`). Step 1 captures interview config (name, resume upload, ID verification). Step 2 shows screening + assessment questions for editing. "Create Interview" saves the changes.

### 18. Edit Interview Button Clicked

User clicks "Edit interview" from the chevron menu on the posted job page. Intent event for the edit interview flow.

| Field | Value |
|-------|-------|
| **Event** | `Edit Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Edit interview" in the chevron menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `edit_interview` | Menu item text |
| `component` | string | `posted_job_chevron_menu` | Chevron menu on posted job page |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 19. Interview Details Completed

User clicks "Next" on step 1 of the edit interview flow. Captures the interview configuration state — interview name, resume upload preference, and identity verification setting.

| Field | Value |
|-------|-------|
| **Event** | `Interview Details Completed` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Next" on the Interview Details step |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `next_button` | Button text |
| `component` | string | `edit_interview_details_step` | Step 1 of edit interview |
| `current_page_context` | string | `hm_edit_interview` | Edit interview page |
| `entity_type` | string | `job` | Business object context |
| `identity_verification_mode` | enum | `require`, `off` | Whether government ID verification is enabled |
| `interview_name` | string | e.g., `Initial screening` | Interview name entered |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `resume_upload_option` | enum | `yes_optional`, `yes_required`, `no_resume_upload` | Resume upload setting |

---

### 20. Interview Saved

User clicks "Create Interview" on step 2 of the edit interview flow. Captures the final state of the interview configuration including question counts. Fires after the API confirms the save.

| Field | Value |
|-------|-------|
| **Event** | `Interview Saved` |
| **Area** | Hiring |
| **Type** | Success (for Edit Interview Button Clicked) |
| **Trigger** | User clicks "Create Interview" and API confirms save |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `create_interview_button` | Button text |
| `assessment_questions_count` | number | e.g., `3` | Number of assessment (behavioral) questions |
| `component` | string | `edit_interview_questions_step` | Step 2 of edit interview |
| `current_page_context` | string | `hm_edit_interview` | Edit interview page |
| `entity_type` | string | `job` | Business object context |
| `identity_verification_mode` | enum | `require`, `off` | Whether government ID verification is enabled |
| `interview_name` | string | e.g., `Initial screening` | Interview name |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `resume_upload_option` | enum | `yes_optional`, `yes_required`, `no_resume_upload` | Resume upload setting |
| `screening_questions_count` | number | e.g., `3` | Number of screening (yes/no) questions |
| `total_questions_count` | number | e.g., `6` | Sum of screening + assessment questions |

---

## Delete Job Flow

### 21. Delete Job Button Clicked

User clicks "Delete" from the chevron menu on the posted job page. Opens a "Delete job posting" confirmation modal. Intent event.

| Field | Value |
|-------|-------|
| **Event** | `Delete Job Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Delete" in the chevron menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `delete` | Menu item text |
| `component` | string | `posted_job_chevron_menu` | Chevron menu on posted job page |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 22. Job Deleted

Job successfully deleted after the user confirms in the "Delete job posting" modal. Fires after the API confirms deletion. **This action cannot be undone.**

| Field | Value |
|-------|-------|
| **Event** | `Job Deleted` |
| **Area** | Hiring |
| **Type** | Success (for Delete Job Button Clicked) |
| **Trigger** | User clicks "Delete" in the confirmation modal AND API confirms deletion |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `candidates_count` | number | e.g., `0` | Total candidates in the funnel at time of deletion |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `days_since_creation` | number | e.g., `12` | Days between job creation and deletion |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager, Data Movement Platform` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `previous_status` | enum | `draft`, `open`, `closed`, `archived` | Job status before deletion |
| `views_count` | number | e.g., `5` | Number of views the job had before deletion |

---

### 23. Job Delete Failed

Deletion API call fails. Pairs with `Delete Job Button Clicked` (intent) and `Job Deleted` (success).

| Field | Value |
|-------|-------|
| **Event** | `Job Delete Failed` |
| **Area** | Hiring |
| **Type** | Failure (for Delete Job Button Clicked) |
| **Trigger** | User clicks "Delete" in the confirmation modal AND API returns an error |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `network`, `permission`, `server`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Job has active candidates` | Human-readable error |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

## Note: Invite Recruiter → Add Team Members

After the first invite is sent, the "Invite recruiter" button label changes to "Add team members" (Image #22). The same `Invite Recruiter Button Clicked` event fires for both states — the `action_value` captures the exact button text:
- Before first invite: `action_value: 'invite_recruiter_button'`
- After first invite: `action_value: 'add_team_members_button'`

---

## Existing Event Removal: Invite Button Clicked

`Invite Button Clicked` (Not Started) is a generic placeholder from the original catalog design. It has only `job_id` as a property and was never implemented. `Invite Recruiter Button Clicked` (this plan, event #8) replaces it with richer properties (`action`, `action_value`, `component`, `current_page_context`, `existing_invites_count`, etc.).

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|-------------|
| Invite Button Clicked | Invite Recruiter Button Clicked | Generic placeholder replaced by specific event with full standard properties and invite context | June 2026 |

> **On merge:** Remove `Invite Button Clicked` from `docs/event-catalog.md` Hiring Persona Events table, `docs/event-schema.md` Intent-Outcome table ("Inviting team member" row), and `docs/dashboards.md` Platform Health table. Add to the Removed Events table. Update the Intent-Outcome row to use `Invite Recruiter Button Clicked` as the intent.

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Archiving a job | Archive Job Button Clicked | Job Archived | Job Archive Failed |
| Sharing job interview | Post Interview Button Clicked | Post Interview Link Copied | -- |
| Inviting a recruiter | Invite Recruiter Button Clicked | Recruiter Invites Sent | -- |
| Editing a job posting | Edit Job Posting Button Clicked | -- | -- |
| Editing an interview | Edit Interview Button Clicked | Interview Saved | -- |
| Deleting a job | Delete Job Button Clicked | Job Deleted | Job Delete Failed |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Archive Completion Rate | Archive Job Button Clicked → Job Archived | % of archive intents that complete (vs cancelled from confirmation modal) |
| Post Interview Share Rate | Post Interview Button Clicked → Post Interview Link Copied | % of HMs who open the share modal and copy the link or share to a channel |
| Recruiter Invite Funnel | Invite Recruiter Button Clicked → Recruiter Invites Sent | % of HMs who open the invite modal and send at least one invite |
| Dashboard → Job Detail | Job Postings Dashboard Loaded → Job Post Clicked | % of dashboard visits that lead to opening a specific job |
| Edit Job Posting Funnel | Edit Job Posting Button Clicked → Job Post Wizard Job Details Completed | % of edit intents that complete at least step 1 |
| Edit Interview Funnel | Edit Interview Button Clicked → Interview Saved | % of edit interview intents that complete |
| Intro Video Creation | Record Video Button Clicked → Intro Video Recording Started → Intro Video Created | % of HMs who visit the page, start recording, and save a take |
| Delete Completion Rate | Delete Job Button Clicked → Job Deleted | % of delete intents that confirm (vs cancel) |

---

## New Events Summary

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|
| Job Postings Dashboard Loaded | Hiring | Page loads with job data | `current_page_context`, `previous_page_context`, `entity_type`, `my_jobs_count`, `shared_with_me_count`, `archived_count`, `total_jobs_count`, `has_jobs`, `active_tab`, `recent_jobs_count` | -- | -- |
| Job Postings Tab Switched | Hiring | User switches dashboard tab | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `selected_tab`, `tab_job_count` | -- | -- |
| Job Archived | Hiring | Archive API confirms success | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `previous_status`, `candidates_count`, `views_count`, `days_since_creation` | `job` | -- |
| Job Archive Failed | Hiring | Archive API returns error | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `error_category`, `error_reason` | `job` | -- |
| Post Interview Button Clicked | Hiring | User clicks "+ Post Interview" on job card | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title` | `job` | -- |
| Post Interview Link Copied | Hiring | User clicks "Copy link" in share modal | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id` | `job` | -- |
| Job Post Clicked | Hiring | User clicks a job card or recent sidebar link | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `entry_point`, `job_id`, `job_title`, `views_count`, `candidates_count` | `job` | -- |
| Invite Recruiter Button Clicked | Hiring | User clicks "Invite recruiter" on posted job page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `existing_invites_count` | `job` | -- |
| View Interview Button Clicked | Hiring | User clicks "View Interview" on posted job page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `questions_count` | `job` | -- |
| Recruiter Invites Sent | Hiring | "Send invites" succeeds | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_count`, `pending_invites_count` | `job` | -- |
| Recruiter Invite Link Copied | Hiring | User copies an invite link | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Recruiter Invite Resent | Hiring | Resend API confirms | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Recruiter Invite Revoked | Hiring | Revoke API confirms | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Job Details Button Clicked | Hiring | User clicks "Job details" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id` | `job` | -- |
| Edit Job Posting Button Clicked | Hiring | User clicks "Edit" or "Edit job posting" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title` | `job` | -- |
| Open Preview Button Clicked | Hiring | User clicks "Open preview" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_intro_video` | `job` | -- |
| Intro Video Recording Started | Hiring | User clicks red "Record" on intro video page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `script_length`, `takes_count` | `job` | -- |
| Edit Interview Button Clicked | Hiring | User clicks "Edit interview" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id` | `job` | -- |
| Interview Details Completed | Hiring | User clicks "Next" on edit interview step 1 | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `interview_name`, `resume_upload_option`, `identity_verification_mode` | `job` | -- |
| Interview Saved | Hiring | User clicks "Create Interview" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `interview_name`, `resume_upload_option`, `identity_verification_mode`, `screening_questions_count`, `assessment_questions_count`, `total_questions_count` | `job` | -- |
| Delete Job Button Clicked | Hiring | User clicks "Delete" in chevron | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title` | `job` | -- |
| Job Deleted | Hiring | Delete API confirms | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `previous_status`, `candidates_count`, `views_count`, `days_since_creation` | `job` | -- |
| Job Delete Failed | Hiring | Delete API fails | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `error_category`, `error_reason` | `job` | -- |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `active_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Default tab shown when dashboard loads |
| `archived_count` | number | -- | Number of jobs in the Archived tab |
| `candidates_count` | number | -- | Total candidates in the job funnel |
| `days_since_creation` | number | -- | Days between job creation and the current action (e.g., archive) |
| `entry_point` | enum | `dashboard_job_card`, `recent_sidebar` | Where the user clicked to navigate to the posted job page |
| `existing_invites_count` | number | -- | Total existing invites (any status) when invite modal is opened |
| `has_jobs` | boolean | true / false | Whether the user has any jobs at all |
| `invite_count` | number | -- | Number of email addresses submitted in a single "Send invites" batch |
| `invite_status` | enum | `pending`, `accepted`, `revoked` | Status of the invite at time of action |
| `my_jobs_count` | number | -- | Number of jobs the user owns |
| `pending_invites_count` | number | -- | Number of pending invites before a new send |
| `previous_status` | enum | `draft`, `open`, `closed` | Job status before archive |
| `recent_jobs_count` | number | -- | Number of jobs shown in the Recent sidebar |
| `selected_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Currently active tab after switch |
| `shared_with_me_count` | number | -- | Number of jobs shared with the user |
| `tab_job_count` | number | -- | Number of jobs displayed in the selected tab |
| `total_jobs_count` | number | -- | Sum of my_jobs + shared_with_me + archived |
| `views_count` | number | -- | Number of views the job has received |
| `wizard_mode` | enum | `create`, `edit` | Whether the wizard was opened for initial creation or post-publish editing |
| `edit_method` | enum | `text`, `ai_regenerate` | How the intro script was edited (existing catalog property, adding `ai_regenerate` value) |
| `script_length` | number | -- | Character count of the intro video script after save/regeneration |
| `has_ai_instruction` | boolean | true / false | Whether user provided instruction text in the regenerate modal |
| `has_intro_video` | boolean | true / false | Whether an intro video exists at time of action |
| `interview_name` | string | -- | Interview name from the edit interview form |
| `resume_upload_option` | enum | `yes_optional`, `yes_required`, `no_resume_upload` | Resume upload setting in edit interview |
| `assessment_questions_count` | number | -- | Number of behavioral assessment questions |
| `screening_questions_count` | number | -- | Number of yes/no screening questions |
| `total_questions_count` | number | -- | Sum of screening + assessment questions |

> **Note:** `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `error_reason`, `error_category`, `questions_count`, `identity_verification_mode`, `duration_seconds`, and `takes_count` are existing catalog properties — not listed here.

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

### `docs/event-catalog.md`

**Hiring Persona Events table — add 23 new events.**

Additionally:
- Remove `Invite Button Clicked` (Not Started, never implemented) from the Hiring Persona Events table and add to Removed Events. Replaced by `Invite Recruiter Button Clicked`.
- Add `wizard_mode` property to all existing `Job Post Wizard *` events.
- Enrich `Record Video Button Clicked`, `Intro Script Updated`, `Intro Video Created` with the properties specified in this plan.
- Add `ai_regenerate` to the `edit_method` enum allowed values.

**Property Dictionary updates:**

| Section | Property | Change |
|---------|----------|--------|
| Enum | `active_tab` | New property. Values: `my_jobs`, `shared_with_me`, `archived`. Used In: `Job Postings Dashboard Loaded` |
| Enum | `selected_tab` | New property. Values: `my_jobs`, `shared_with_me`, `archived`. Used In: `Job Postings Tab Switched` |
| Enum | `entry_point` | Existing — append `dashboard_job_card`, `recent_sidebar` to Allowed Values. Append `Job Post Clicked` to Used In |
| Enum | `invite_status` | New property. Values: `pending`, `accepted`, `revoked`. Used In: `Recruiter Invite Link Copied`, `Recruiter Invite Resent`, `Recruiter Invite Revoked` |
| Enum | `previous_status` | New property. Values: `draft`, `open`, `closed`. Used In: `Job Archived` |
| Boolean | `has_jobs` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `my_jobs_count` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `shared_with_me_count` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `archived_count` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `total_jobs_count` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `recent_jobs_count` | New property. Used In: `Job Postings Dashboard Loaded` |
| Numeric | `tab_job_count` | New property. Used In: `Job Postings Tab Switched` |
| Numeric | `invite_count` | New property. Used In: `Recruiter Invites Sent` |
| Numeric | `pending_invites_count` | New property. Used In: `Recruiter Invites Sent` |
| Numeric | `existing_invites_count` | New property. Used In: `Invite Recruiter Button Clicked` |
| Numeric | `candidates_count` | New property. Used In: `Job Archived`, `Job Post Clicked` |
| Numeric | `views_count` | New property. Used In: `Job Archived`, `Job Post Clicked` |
| Numeric | `days_since_creation` | New property. Used In: `Job Archived` |

**Property Dictionary — update "Used In" for existing properties:**

| Property | Append to "Used In" |
|----------|---------------------|
| `action` (user_action) | Job Postings Tab Switched, Post Interview Button Clicked, Post Interview Link Copied, Job Post Clicked, Invite Recruiter Button Clicked, View Interview Button Clicked, Recruiter Invites Sent, Recruiter Invite Link Copied, Recruiter Invite Resent, Recruiter Invite Revoked |
| `action_value` | Same as above |
| `component` | Same as above |
| `current_page_context` | All 13 new events |
| `previous_page_context` | All 13 new events |
| `entity_type` | All 13 new events |
| `job_id` | Job Archived, Job Archive Failed, Post Interview Button Clicked, Post Interview Link Copied, Job Post Clicked, Invite Recruiter Button Clicked, View Interview Button Clicked, Recruiter Invites Sent, Recruiter Invite Link Copied, Recruiter Invite Resent, Recruiter Invite Revoked |
| `job_title` | Job Archived, Post Interview Button Clicked, Job Post Clicked |
| `error_reason` | Job Archive Failed |
| `error_category` | Job Archive Failed |
| `questions_count` | View Interview Button Clicked |

### `docs/event-schema.md`

**Standard Objects table — add:**

| Object | Entity | Example Events |
|--------|--------|----------------|
| Job Postings Dashboard | HM job postings homepage | Job Postings Dashboard Loaded |
| Job Postings Tab | Tab bar on job postings dashboard | Job Postings Tab Switched |
| Post Interview | Post interview share action | Post Interview Button Clicked, Post Interview Link Copied |
| Job Post | Individual job posting card/link | Job Post Clicked |
| Recruiter Invite | Recruiter invite to share candidate list | Recruiter Invites Sent, Recruiter Invite Link Copied, Recruiter Invite Resent, Recruiter Invite Revoked |

**Intent-Outcome table — add:**

| Flow | Intent Event | Success Event | Failure Event |
|------|-------------|---------------|---------------|
| Archiving a job | Archive Job Button Clicked | Job Archived | Job Archive Failed |
| Inviting a recruiter | Invite Recruiter Button Clicked | Recruiter Invites Sent | Team Member Invite Failed (backend) |

### `docs/dashboards.md`

No dashboard changes needed initially. These events supplement the existing Hiring Dashboard.
