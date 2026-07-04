# Tracking Plan: HM Job Posting Edit Flow v1

**Product:** Helix (SeekOut.ai)
**Feature:** Job Postings dashboard, archive flow, posted job page, recruiter invite lifecycle, intro video flow, edit interview, and delete job
**Date:** 2026-06-07 (draft) → 2026-06-10 (revised after local testing)
**Related PRD:** —
**Helix PR:** [Zipstorm/helix#619](https://github.com/Zipstorm/helix/pull/619)
**Scope:** 34 new events + 7 existing event modifications. Covers: dashboard state + tab switching (2), archive failure (1), Post Interview button + link copy (2), job post navigation (1), posted job page header actions (4), recruiter invite lifecycle (4), intro video flow (10), edit interview (3), delete job (3), share modal additions (3), interview link (1), backend republish (1). Also modifies all wizard events to support edit mode via `wizard_mode` + `job_post_status` properties.

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.
> Reference: `tracking-plans/archived/hm-job-creation-wizard-v3.md` for the v3 wizard tracking plan.

---

## Revision Log

Changes from the original draft (2026-06-07) based on local testing and Helix PR #619:

| # | Change | Reason |
|---|---|---|
| R1 | `Job Archived` removed as PostHog event | Archive success is tracked via session-analysis only. Backend `Job Status Changed` with `to_status: 'archived'` covers PostHog analytics. |
| R2 | `Job Archive Failed` → `Job Status Change Failed` | Generalized to cover any status change failure, not just archive. Added `from_status`, `to_status`. |
| R3 | `Record Video Button Clicked` enrichment → split into `Intro Video Record Button Clicked` + `Intro Video Edit Button Clicked` | Separate events for Job Details panel navigation (new vs existing video). The existing `Record Video Button Clicked` now fires on the intro video page itself alongside `Intro Video Recording Started`. |
| R4 | Added 12 new events not in original plan (+ 2 existing event enrichments moved to M-sections) | `More Actions Button Clicked`, `Intro Video Record/Edit/Delete Button Clicked`, `Intro Video Re-record Button Clicked`, `Intro Video Script Regenerate/Edit Button Clicked`, `Intro Video Recreated`, `Refine with AI Button Clicked`, `Job Share Message AI Refine Failed`, `Job Posting Republished`, `Interview Link Clicked`. Enrichments: `Intro Video Deleted` (M5), `Record Video Button Clicked` (M2). |
| R5 | `Intro Script Updated` source changed Backend → Frontend | `edit_method` values: `manual`, `ai_regenerate`, `ai_guided_regenerate`. Added `intro_video_status`. |
| R6 | `Intro Video Created` source changed Backend → Frontend, split with `Intro Video Recreated` | First-time saves fire `Intro Video Created`; re-records fire `Intro Video Recreated`. |
| R7 | `Intro Video Deleted` source changed Backend → Frontend | Now fires from frontend after delete API success. |
| R8 | `team_members_count` added to most posted-job events | Counts non-owner collaborators on the job. |
| R9 | `intro_video_status` (`create`/`edit`) added to all intro video events | Distinguishes first video creation from editing/replacing an existing one. |
| R10 | `job_post_status` (`draft`/`active`/`null`) added alongside `wizard_mode` | Finer granularity than `wizard_mode` alone. |
| R11 | Recruiter invite `component` values changed | `share_candidate_list_modal_invite_row` → `recruiter_invite_dialog` |
| R12 | Job Details panel `component` values changed | `job_details_panel` → `job_details_sheet` in some events |
| R13 | `recent_jobs_count` removed from Dashboard Loaded | Not available in dashboard API response. |
| R14 | `Recruiter Invites Sent` lost `action`/`action_value`/`component` | Event fires as a system event (no user-interaction metadata). |
| R15 | `Go To Job Posting Page Clicked` → `Go To Job Posting Page Link Clicked` | v3 event rename that happened in this PR. |

---

## User Flow

```text
HM Login (current role: Hiring Manager)
  │
  └─ Job Postings Dashboard  (/hiring-manager/job-postings)
       │
       ├─ Page loads
       │    → fires: Page Viewed (existing, Live)
       │    → fires: Job Postings Dashboard Loaded  ← NEW
       │
       ├─ User switches tabs: My jobs │ Shared with me │ Archived
       │    → fires: Job Postings Tab Switched  ← NEW
       │
       ├─ User clicks "⋮" kebab → "Archive this job"
       │    → fires: Archive Job Button Clicked (existing, Live)
       │    → confirmation modal opens
       │    └─ User clicks "Archive" → API call
       │         ├─ success → fires: track('Job Archived') (session-analysis only)
       │         │           → backend fires: Job Status Changed (existing, Live)
       │         └─ failure → fires: Job Status Change Failed  ← NEW (was "Job Archive Failed")
       │
       ├─ User clicks "+ Post Interview" on a job card
       │    → fires: Post Interview Button Clicked  ← NEW
       │    → share modal opens
       │    ├─ User clicks "Copy link"
       │    │    → fires: Post Interview Link Copied  ← NEW
       │    ├─ User clicks interview thumbnail
       │    │    → fires: Interview Link Clicked  ← NEW
       │    ├─ User clicks "Refine with AI"
       │    │    → fires: Refine with AI Button Clicked  ← NEW
       │    │    └─ AI refinement
       │    │         ├─ success → fires: Job Share Message AI Refined (existing, Live)
       │    │         └─ failure → fires: Job Share Message AI Refine Failed  ← NEW
       │    ├─ User copies message → fires: Job Share Message Copied (existing, Live)
       │    └─ User clicks channel → fires: Job Share Channel Clicked (existing, Live)
       │
       ├─ User clicks a job card (dashboard list)
       │    → fires: Job Post Clicked (entry_point: dashboard_job_card)  ← NEW
       │    → navigates to posted job page
       │
       └─ User clicks a job name (Recent sidebar)
            → fires: Job Post Clicked (entry_point: recent_sidebar)  ← NEW
            → navigates to posted job page


Posted Job Page  (/jobs/{job_id}/candidates)
  │
  ├─ Page loads → fires: Page Viewed (existing, Live)
  │
  ├─ User clicks "Share" → fires: Share Button Clicked (existing, Live)
  │    → share modal opens (same events as dashboard share modal above)
  │
  ├─ User clicks "Job details"
  │    → fires: Job Details Button Clicked  ← NEW
  │    → Job Details side panel opens
  │    │
  │    ├─ User clicks "Edit" (pencil icon)
  │    │    → fires: Edit Job Posting Button Clicked (entry_point: job_details_panel)  ← NEW
  │    │    → navigates to wizard in edit mode
  │    │
  │    ├─ User clicks "Open preview"
  │    │    → fires: Open Preview Button Clicked  ← NEW
  │    │    → opens candidate-facing preview in new tab
  │    │
  │    ├─ Intro video section (no video exists):
  │    │    └─ User clicks "Record"
  │    │         → fires: Intro Video Record Button Clicked  ← NEW
  │    │         → navigates to intro video page
  │    │
  │    └─ Intro video section (video exists):
  │         ├─ User clicks "Edit intro video"
  │         │    → fires: Intro Video Edit Button Clicked  ← NEW
  │         │    → navigates to intro video page
  │         └─ User clicks "Delete"
  │              → fires: Intro Video Delete Button Clicked  ← NEW
  │              └─ API call
  │                   └─ success → fires: Intro Video Deleted  ← NEW (frontend)
  │
  ├─ User clicks "⋮" (More actions) dropdown
  │    → fires: More Actions Button Clicked  ← NEW
  │    │
  │    ├─ "Edit job posting"
  │    │    → fires: Edit Job Posting Button Clicked (entry_point: chevron_menu)  ← NEW
  │    │    → navigates to wizard in edit mode
  │    │
  │    ├─ "Edit interview"
  │    │    → fires: Edit Interview Button Clicked  ← NEW
  │    │    → navigates to edit interview page
  │    │
  │    └─ "Delete"
  │         → fires: Delete Job Button Clicked  ← NEW
  │         → confirmation modal opens
  │         └─ User clicks "Delete"
  │              ├─ success → fires: Job Deleted  ← NEW
  │              └─ failure → fires: Job Delete Failed  ← NEW
  │
  ├─ User clicks "Invite recruiter" / "Add team members"
  │    → fires: Invite Recruiter Button Clicked  ← NEW
  │    → recruiter invite dialog opens
  │    │
  │    ├─ User enters emails → clicks "Send invites"
  │    │    ├─ success → fires: Recruiter Invites Sent  ← NEW
  │    │    │           → also fires: Team Member Invited (existing, Live, backend, per invite)
  │    │    └─ failure → fires: Team Member Invite Failed (existing, Live, backend)
  │    │
  │    ├─ User clicks "Copy link" on an invite
  │    │    → fires: Recruiter Invite Link Copied  ← NEW
  │    │
  │    ├─ User clicks "Resend" on an invite
  │    │    → fires: Recruiter Invite Resent  ← NEW
  │    │
  │    └─ User clicks "Revoke" on an invite
  │         → fires: Recruiter Invite Revoked  ← NEW
  │
  └─ User clicks "View Interview"
       → fires: View Interview Button Clicked  ← NEW


Intro Video Page  (/hiring-manager/job-postings/{id}/intro-video)
  │
  ├─ User clicks "Regenerate" (script section)
  │    → fires: Intro Video Script Regenerate Button Clicked  ← NEW
  │
  ├─ User clicks "Edit" (script section)
  │    → fires: Intro Video Script Edit Button Clicked  ← NEW
  │
  ├─ User saves script edit or AI regeneration completes (only if changed)
  │    → fires: Intro Script Updated  ← ENRICHED (now frontend)
  │
  ├─ User clicks red "Record" button
  │    → fires: Record Video Button Clicked  ← ENRICHED (now fires on intro page)
  │    → fires: Intro Video Recording Started  ← NEW
  │    → recording begins
  │
  ├─ User clicks "Re-record" after reviewing a take
  │    → fires: Intro Video Re-record Button Clicked  ← NEW
  │
  └─ User clicks "Use this take" → upload completes
       → fires: Intro Video Created (first video)  ← ENRICHED (now frontend)
       → OR fires: Intro Video Recreated (replacing existing)  ← NEW


Edit Interview Page  (/hiring-manager/job-postings/{id}/create-interview)
  │
  ├─ Step 1: Interview Details → User clicks "Next"
  │    → fires: Interview Details Completed  ← NEW
  │
  └─ Step 2: Questions → User clicks "Create Interview"
       └─ API confirms save
            → fires: Interview Saved  ← NEW


Wizard Edit Mode (any wizard page with existing job)
  │
  └─ All existing wizard events now include:
       → wizard_mode: 'create' | 'edit'
       → job_post_status: 'draft' | 'active' | null
  │
  └─ Backend: when edit-mode save republishes a live job
       → fires: Job Posting Republished  ← NEW (backend)
```

---

## Page Contexts

| Page | URL Pattern | `current_page_context` |
|------|------------|----------------------|
| Job Postings Dashboard | `/hiring-manager/job-postings` | `hiring_manager_job_postings` (existing) |
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
| `Job Status Changed` | Live | Backend event — fires when job status transitions (including to `archived`). Serves as the PostHog success event for archive. |
| `Team Member Invited` | Live | Backend event — fires per invite when server confirms delivery |
| `Team Member Invite Failed` | Live | Backend event — fires when invite fails |

---

## Existing Events Used from Different Context

The v3 share modal events now fire from both the dashboard and posted job page via a parameterized page context. The `current_page_context` property distinguishes the source.

| v3 Event | Original Context | New Contexts |
|----------|-----------------|-------------|
| `Job Share Message AI Refined` | `hm_job_creation_wizard_success` | `hiring_manager_job_postings`, `hm_job_posting_detail` |
| `Job Share Message Copied` | `hm_job_creation_wizard_success` | `hiring_manager_job_postings`, `hm_job_posting_detail` |
| `Job Share Channel Clicked` | `hm_job_creation_wizard_success` | `hiring_manager_job_postings`, `hm_job_posting_detail` |

**Status:** ✅ Tested locally. The share modal now accepts a page context parameter, defaulting to the wizard success context for backward compatibility.

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Job Postings Dashboard | HM job postings homepage | Job Postings Dashboard Loaded |
| Job Postings Tab | Tab bar on job postings dashboard | Job Postings Tab Switched |
| Post Interview | Post interview share action | Post Interview Button Clicked, Post Interview Link Copied |
| Job Post | Individual job posting card/link | Job Post Clicked |
| Recruiter Invite | Recruiter invite lifecycle | Recruiter Invites Sent, Recruiter Invite Link Copied, Recruiter Invite Resent, Recruiter Invite Revoked |
| Invite Recruiter Button | Invite recruiter CTA on posted job page | Invite Recruiter Button Clicked |
| View Interview Button | View interview CTA on posted job page | View Interview Button Clicked |
| Job Details Button | Job details panel CTA on posted job page | Job Details Button Clicked |
| More Actions Button | Overflow menu on posted job header | More Actions Button Clicked |
| Edit Job Posting Button | Edit job posting CTA | Edit Job Posting Button Clicked |
| Open Preview Button | Public preview CTA in job details panel | Open Preview Button Clicked |
| Edit Interview Button | Edit interview CTA in chevron menu | Edit Interview Button Clicked |
| Interview Details | Interview config step 1 | Interview Details Completed |
| Interview | Interview creation/edit lifecycle | Interview Saved |
| Delete Job Button | Delete job CTA in chevron menu | Delete Job Button Clicked |
| Job Delete | Job deletion lifecycle | Job Delete Failed |
| Intro Video Recording | Intro video recording action | Intro Video Recording Started |
| Intro Video Record Button | Record CTA in Job Details panel (no video) | Intro Video Record Button Clicked |
| Intro Video Edit Button | Edit CTA in Job Details panel (video exists) | Intro Video Edit Button Clicked |
| Intro Video Delete Button | Delete CTA in Job Details panel | Intro Video Delete Button Clicked |
| Intro Video Re-record Button | Re-record CTA after reviewing a take | Intro Video Re-record Button Clicked |
| Intro Video Script | Intro video script section actions | Intro Video Script Edit Button Clicked, Intro Video Script Regenerate Button Clicked |
| Interview Link | Interview link in share/invite modals | Interview Link Clicked |
| Refine with AI Button | AI refine CTA in share modal | Refine with AI Button Clicked |
| Job Share Message AI Refine | AI refine failure | Job Share Message AI Refine Failed |
| Job Status Change | Generic job status change failure | Job Status Change Failed |

## New Events

### 1. Job Postings Dashboard Loaded

Fires once when the Job Postings dashboard loads with job data. Captures dashboard state for portfolio analysis.

| Field | Value |
|-------|-------|
| **Event** | `Job Postings Dashboard Loaded` |
| **Area** | Hiring |
| **Type** | -- (system, page load companion) |
| **Trigger** | Job data loads on dashboard mount (guarded: fires once per mount) |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `active_tab` | enum | `my_jobs`, `shared_with_me`, `archived` (or recruiter tabs) | Default tab shown on load |
| `archived_count` | number | e.g., `2` | Number of archived jobs |
| `current_page_context` | string | `hiring_manager_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `has_jobs` | boolean | `true`/`false` | Whether the user has any jobs at all |
| `jobs_with_intro_video_count` | number | e.g., `1` | Number of jobs with a recorded intro video |
| `my_jobs_count` | number | e.g., `4` | Number of jobs the user created |
| `previous_page_context` | string | snake_case or null | Previous page |
| `shared_with_me_count` | number | e.g., `0` | Number of jobs shared with the user |
| `team_members_count` | number | e.g., `3` | Total non-owner collaborators across all jobs |
| `total_jobs_count` | number | e.g., `6` | Sum of my_jobs + shared_with_me + archived |

> **Changed from draft:** Removed `recent_jobs_count` (not available in API). Added `jobs_with_intro_video_count`, `team_members_count`.

---

### 2. Job Postings Tab Switched

User switches between dashboard tabs. Measures tab engagement.

| Field | Value |
|-------|-------|
| **Event** | `Job Postings Tab Switched` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks a different tab |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | tab value (e.g., `my_jobs`) | Tab clicked |
| `component` | string | `job_postings_tab_bar` | Tab bar on dashboard |
| `current_page_context` | string | `hiring_manager_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `previous_page_context` | string | snake_case or null | Previous page |
| `selected_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | The tab now active |
| `tab_job_count` | number | e.g., `4` | Number of jobs shown in the selected tab |

---

### 3. Job Status Change Failed

Status change API call fails. Replaces the original `Job Archive Failed` — generalized to cover any status transition failure.

| Field | Value |
|-------|-------|
| **Event** | `Job Status Change Failed` |
| **Area** | Hiring |
| **Type** | Failure |
| **Trigger** | Status change API returns error (e.g., archive attempt fails) |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table. Do NOT add `Job Archive Failed` (original plan name — superseded).

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hiring_manager_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `network`, `permission`, `server`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Request failed` | Human-readable error |
| `from_status` | string | e.g., `active` | Job status before the failed change |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `to_status` | string | e.g., `archived` | Target status that failed |

> **Changed from draft:** Renamed from `Job Archive Failed`. Added `from_status`, `to_status`. Errors are classified into standard categories.

---

### 4. Post Interview Button Clicked

User clicks "+ Post Interview" on a job card on the dashboard. Opens the share interview modal.

| Field | Value |
|-------|-------|
| **Event** | `Post Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "+ Post Interview" on a job card |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `post_interview_button` | Button text |
| `component` | string | `job_postings_job_card` | Job card on the dashboard list |
| `current_page_context` | string | `hiring_manager_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `has_intro_video` | boolean | `true`/`false` | Whether job has a recorded intro video |
| `is_email_verified` | boolean | `true`/`false` | Whether HM has completed email verification |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** Added `has_intro_video`.

---

### 5. Post Interview Link Copied

User clicks "Copy link" in the share interview modal.

| Field | Value |
|-------|-------|
| **Event** | `Post Interview Link Copied` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Copy link" in the share interview modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `copy_link_button` | Button text |
| `component` | string | `share_interview_modal` | Share modal |
| `current_page_context` | string | varies by caller | Page that opened the modal |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 6. Job Post Clicked

User clicks a job to navigate to the posted job detail page. Two entry points: dashboard job card and Recent sidebar.

| Field | Value |
|-------|-------|
| **Event** | `Job Post Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks a job card on the dashboard OR a job name in the Recent sidebar |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties (dashboard entry):**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `job_post_card` | What was clicked |
| `component` | string | `job_postings_job_card_list` | Where the click happened |
| `current_page_context` | string | `hiring_manager_job_postings` | Dashboard page |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | enum | `dashboard_job_card` | Which UI element was clicked |
| `has_intro_video` | boolean | `true`/`false` | Whether job has recorded intro video |
| `job_id` | string | UUID | Job identifier |
| `job_post_status` | enum | `draft`, `active`, `null` | Job lifecycle state |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |

**Properties (sidebar entry):**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `recent_job_link` | What was clicked |
| `component` | string | `recent_sidebar_nav` | Where the click happened |
| `current_page_context` | string | dynamic (route-derived) | Current page when sidebar link clicked |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | enum | `recent_sidebar` | Which UI element was clicked |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | dynamic or null | Previous page |

> **Changed from draft:** Dashboard adds `has_intro_video`, `job_post_status`. Removed `views_count`/`candidates_count` (not available on list API). Sidebar `current_page_context` is dynamic (not always `hm_job_postings`).

---

### 7. Invite Recruiter Button Clicked

User clicks "Invite recruiter" (or "Add team members" after first invite) on the posted job page.

| Field | Value |
|-------|-------|
| **Event** | `Invite Recruiter Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Invite recruiter" / "Add team members" button |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table. Remove `Invite Button Clicked` (Not Started, never implemented) and add to Removed Events.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `invite_recruiter_button` or `add_team_members_button` | Exact button text (changes after first invite) |
| `component` | string | `posted_job_hiring_team_card` | Hiring team card on posted job page |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `existing_invites_count` | number | e.g., `2` | Number of pending invite emails at time of click |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** `component` changed from `posted_job_invite_recruiter_card` → `posted_job_hiring_team_card`. Added `team_members_count`.

---

### 8. View Interview Button Clicked

User clicks "View Interview" on the posted job page.

| Field | Value |
|-------|-------|
| **Event** | `View Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "View Interview" on the posted job page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `view_interview_button` | Button text |
| `component` | string | `posted_job_ai_interview_card` | AI interview card |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `questions_count` | number | e.g., `7` | Number of interview questions |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** Added `team_members_count`.

---

### 9. Recruiter Invites Sent

User sends invites from the recruiter invite dialog. Fires after API confirms.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invites Sent` |
| **Area** | Hiring |
| **Type** | Success (for Invite Recruiter Button Clicked) |
| **Trigger** | "Send invites" API confirms invites are created |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_count` | number | e.g., `2` | Number of invites in this batch |
| `job_id` | string | UUID | Job identifier |
| `pending_invites_count` | number | e.g., `1` | Pending invites from the response |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** Removed `action`, `action_value`, `component` — fires as a system event, not a user interaction.

---

### 10. Recruiter Invite Link Copied

User clicks "Copy link" on an invite row.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Link Copied` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Copy link" on an invite row |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `copy_invite_link` | Action performed |
| `component` | string | `recruiter_invite_dialog` | Invite dialog |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | invite status value | Status of the invite when link was copied |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** `action_value` changed `copy_link_button` → `copy_invite_link`. `component` changed `share_candidate_list_modal_invite_row` → `recruiter_invite_dialog`.

---

### 11. Recruiter Invite Resent

User resends a pending invite.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Resent` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | Resend API confirms |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `resend_invite` | Action performed |
| `component` | string | `recruiter_invite_dialog` | Invite dialog |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | invite status from response | Status after resend |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** `action_value` changed `resend_button` → `resend_invite`. `component` changed to `recruiter_invite_dialog`.

---

### 12. Recruiter Invite Revoked

User revokes an invite.

| Field | Value |
|-------|-------|
| **Event** | `Recruiter Invite Revoked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | Revoke API confirms |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `revoke_invite` | Action performed |
| `component` | string | `recruiter_invite_dialog` | Invite dialog |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `invite_status` | enum | invite status before revocation | Status before revoke |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** `action_value` changed `revoke_button` → `revoke_invite`. `component` changed to `recruiter_invite_dialog`.

---

### 13. Job Details Button Clicked

User clicks "Job details" on the posted job page header.

| Field | Value |
|-------|-------|
| **Event** | `Job Details Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Job details" button |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `job_details_button` | Button text |
| `component` | string | `posted_job_header` | Top header bar |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** Added `team_members_count`.

---

### 14. More Actions Button Clicked

User opens the "⋮" (more actions) dropdown on the posted job page header. Not in original plan — added during local testing.

| Field | Value |
|-------|-------|
| **Event** | `More Actions Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User opens the more actions dropdown |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `more_actions_button` | Button text |
| `component` | string | `posted_job_header` | Top header bar |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `has_candidates` | boolean | `true`/`false` | Whether job has candidates |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

---

### 15. Edit Job Posting Button Clicked

User clicks "Edit" in Job Details panel or "Edit job posting" in chevron menu.

| Field | Value |
|-------|-------|
| **Event** | `Edit Job Posting Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks edit from either surface |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `edit_job_posting` | Action performed |
| `component` | string | `posted_job_chevron_menu` or `job_details_sheet` | Where the click happened |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | enum | `chevron_menu`, `job_details_panel` | Which UI surface |
| `has_candidates` | boolean | `true`/`false` | Whether job has candidates |
| `is_email_verified` | boolean | `true`/`false` | Whether HM has completed email verification |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** `component` for details panel is `job_details_sheet` (not `job_details_panel`). Added `has_candidates`, `team_members_count`.

---

### 16. Open Preview Button Clicked

User clicks "Open preview" in the Job Details panel.

| Field | Value |
|-------|-------|
| **Event** | `Open Preview Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Open preview" |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `open_preview_button` | Button text |
| `component` | string | `job_details_sheet` | Job Details side panel |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `has_intro_video` | boolean | `true`/`false` | Whether intro video exists |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

> **Changed from draft:** `component` is `job_details_sheet` (not `job_details_panel`). Sends with `{ send_instantly: true }`.

---

### 17. Edit Interview Button Clicked

User clicks "Edit interview" from the chevron menu.

| Field | Value |
|-------|-------|
| **Event** | `Edit Interview Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Edit interview" in chevron menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `edit_interview` | Menu item text |
| `component` | string | `posted_job_chevron_menu` | Chevron menu |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** Added `team_members_count`.

---

### 18. Interview Details Completed

User clicks "Next" on step 1 of the edit interview flow.

| Field | Value |
|-------|-------|
| **Event** | `Interview Details Completed` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Next" on Interview Details step |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_edit_interview` | Edit interview page |
| `entity_type` | string | `job` | Business object context |
| `identity_verification_mode` | enum | `require`, `off` | Whether ID verification is enabled |
| `interview_name` | string | e.g., `Initial screening` | Interview name |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `resume_upload_option` | string | form value | Resume upload setting |

> **Changed from draft:** No `action`/`action_value`/`component` — fires as a system event, not a user interaction.

---

### 19. Interview Saved

User clicks "Create Interview" on step 2 and API confirms.

| Field | Value |
|-------|-------|
| **Event** | `Interview Saved` |
| **Area** | Hiring |
| **Type** | Success (for Edit Interview Button Clicked) |
| **Trigger** | API confirms interview save |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `assessment_questions_count` | number | e.g., `3` | Number of assessment questions |
| `current_page_context` | string | `hm_edit_interview` | Edit interview page |
| `entity_type` | string | `job` | Business object context |
| `identity_verification_mode` | enum | `require`, `off` | Whether ID verification is enabled |
| `interview_name` | string | e.g., `Initial screening` | Interview name |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `resume_upload_option` | string | form value | Resume upload setting |
| `screening_questions_count` | number | e.g., `3` | Number of screening questions |
| `total_questions_count` | number | e.g., `6` | Sum of screening + assessment |

---

### 20. Delete Job Button Clicked

User clicks "Delete" from the chevron menu.

| Field | Value |
|-------|-------|
| **Event** | `Delete Job Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Delete" in chevron menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `delete_job` | Menu item |
| `component` | string | `posted_job_chevron_menu` | Chevron menu |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `team_members_count` | number | e.g., `1` | Non-owner collaborators |

> **Changed from draft:** `action_value` is `delete_job` (not `delete`). Added `team_members_count`.

---

### 21. Job Deleted

Job successfully deleted after confirmation. Fires after API confirms.

| Field | Value |
|-------|-------|
| **Event** | `Job Deleted` |
| **Area** | Hiring |
| **Type** | Success (for Delete Job Button Clicked) |
| **Trigger** | Delete API confirms |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `candidates_count` | number | e.g., `0` | Total candidates at time of deletion |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `days_since_creation` | number or null | e.g., `12` | Days between creation and deletion |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `job_title` | string | e.g., `Product Manager` | Job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `previous_status` | string or null | e.g., `active` | Job status before deletion |
| `views_count` | number | `0` | Best-effort (hardcoded) |

---

### 22. Job Delete Failed

Delete API fails.

| Field | Value |
|-------|-------|
| **Event** | `Job Delete Failed` |
| **Area** | Hiring |
| **Type** | Failure (for Delete Job Button Clicked) |
| **Trigger** | Delete API returns error |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `network`, `permission`, `server`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Request failed` | Human-readable error |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

---

## Intro Video Flow — New Events

### 23. Intro Video Record Button Clicked

User clicks "Record" in Job Details panel (no existing video). Navigates to intro video page.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Record Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Record" in Job Details panel |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `record_intro_video_button` | Button text |
| `component` | string | `job_details_intro_video_section` | Intro video section in panel |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | string | `job_details_panel` | Where initiated |
| `has_existing_video` | boolean | `false` | Always false for this event |
| `intro_video_status` | enum | `create` | Always create for this event |
| `job_id` | string | UUID | Job identifier |
| `job_post_status` | enum | `draft`, `active`, `null` | Job lifecycle state |
| `previous_page_context` | string | snake_case or null | Previous page |

> **New event:** Replaces the plan's enrichment of `Record Video Button Clicked` for the Job Details panel surface. The existing `Record Video Button Clicked` name is now used on the intro video recording page.

---

### 24. Intro Video Edit Button Clicked

User clicks "Edit intro video" in Job Details panel (video exists). Navigates to intro video page.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Edit Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Edit intro video" in Job Details panel |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:** Same as #23 but `action_value: 'edit_intro_video_button'`, `component: 'job_details_intro_video_menu'`, `has_existing_video: true`, `intro_video_status: 'edit'`.

---

### 25. Intro Video Delete Button Clicked

User clicks "Delete" on intro video in Job Details panel. Intent event.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Delete Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Delete" in intro video menu |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:** Same as #24 but `action_value: 'delete_intro_video_button'`.

---

### 26. Intro Video Script Regenerate Button Clicked

User clicks "Regenerate" to open the AI regeneration popover.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Script Regenerate Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Regenerate" button on intro video page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `regenerate_intro_script_button` | Button text |
| `component` | string | `intro_video_script_section` | Script section on intro page |
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `entity_type` | string | `job` | Business object context |
| `has_existing_video` | boolean | `true`/`false` | Whether video already exists |
| `intro_video_status` | enum | `create`, `edit` | Create vs edit mode |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Current script character count |

---

### 27. Intro Video Script Edit Button Clicked

User clicks "Edit" to enter the script text editor.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Script Edit Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Edit" on script section |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:** Same as #27 but `action_value: 'edit_intro_script_button'`.

---

### 28. Intro Video Recording Started

User clicks red "Record" button on the intro video page. Fires simultaneously with `Record Video Button Clicked`.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Recording Started` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks the red "Record" button on intro video page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `record_button` | Red record button |
| `component` | string | `intro_video_recorder` | Video recorder |
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `entity_type` | string | `job` | Business object context |
| `has_existing_video` | boolean | `true`/`false` | Whether replacing an existing video |
| `intro_video_status` | enum | `create`, `edit` | Create vs edit mode |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Script character count at recording time |
| `takes_count` | number | e.g., `1` | Current take number (1-indexed) |

> **Changed from draft:** Added `has_existing_video`, `intro_video_status`.

---

### 29. Intro Video Re-record Button Clicked

User clicks "Re-record" after reviewing a take.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Re-record Button Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Re-record" in video review |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:** Same as #29 but `action_value: 're_record_intro_video_button'`, `component: 'intro_video_review'`.

---

### 30. Intro Video Recreated

User saves a new take over an existing video. Split from `Intro Video Created`.

| Field | Value |
|-------|-------|
| **Event** | `Intro Video Recreated` |
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Upload completes for a re-recorded video |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `duration_seconds` | number or null | e.g., `45` | Video duration |
| `entity_type` | string | `job` | Business object context |
| `intro_video_status` | enum | `edit` | Always edit for recreate |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `takes_count` | number or null | e.g., `3` | Takes before save |

---

## Share Modal — New Events

### 31. Refine with AI Button Clicked

User clicks "Refine with AI" in the share interview modal.

| Field | Value |
|-------|-------|
| **Event** | `Refine with AI Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Refine with AI" button |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `refine_with_ai_button` | Button text |
| `component` | string | `share_interview_modal` | Share modal |
| `current_page_context` | string | varies by caller | Page that opened the modal |
| `entity_type` | string | `job` | Business object context |
| `job_id` | string | UUID | Job identifier |
| `message_length` | number | e.g., `200` | Current message length |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 32. Job Share Message AI Refine Failed

AI refinement API fails.

| Field | Value |
|-------|-------|
| **Event** | `Job Share Message AI Refine Failed` |
| **Area** | Hiring |
| **Type** | Failure (for Refine with AI Button Clicked) |
| **Trigger** | Refinement API returns error |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `generate_message_button` | Button that triggered the refinement |
| `component` | string | `share_interview_modal` | Share modal |
| `current_page_context` | string | varies by caller | Page context |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `network`, `permission`, `server`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Request failed` | Error message |
| `instruction_length` | number | e.g., `50` | User's AI instruction length |
| `job_id` | string | UUID | Job identifier |
| `original_message_length` | number | e.g., `200` | Message length before refinement attempt |
| `previous_page_context` | string | snake_case or null | Previous page |

---

### 33. Interview Link Clicked

User clicks the interview link (thumbnail or inline link).

| Field | Value |
|-------|-------|
| **Event** | `Interview Link Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks the interview link in share/invite modal |
| **Source** | Frontend |
| **Group** | `job` (optional) |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `interview_link` | What was clicked |
| `component` | string | varies (`share_interview_modal_thumbnail`, etc.) | Where the click happened |
| `current_page_context` | string | varies by caller | Page context |
| `entity_type` | string | `interview` | Note: different from `job` |
| `interview_id` | string or undefined | extracted from URL | Interview ID from the link |
| `job_id` | string | UUID | Job identifier (optional) |
| `previous_page_context` | string | snake_case or null | Previous page |

---

## Backend — New Events

### 34. Job Posting Republished

Backend event for edit-mode re-publish. Fires when a live job is updated and remains published.

| Field | Value |
|-------|-------|
| **Event** | `Job Posting Republished` |
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | Edit-mode save on a job that was already published |
| **Source** | Backend |
| **Group** | `job` |
| **Status** | Tested locally |

→ On merge: add to `docs/event-catalog.md` Hiring Persona Events table.

**Properties:** Same as `Job Posting Published` (full job snapshot from `build_job_setup_analytics_snapshot`) + `wizard_mode: 'edit'`.

---

## Existing Event Modifications

### M1. Wizard Edit Mode (`wizard_mode` + `job_post_status`)

All existing wizard events gain two new properties:

| Property | Type | Values | Description |
|---|---|---|---|
| `wizard_mode` | enum | `create`, `edit` | `create` for new jobs, `edit` for post-publish edits |
| `job_post_status` | enum | `draft`, `active`, `null` | Normalized job lifecycle state |

**Affected events:** `Job Post Wizard Started`, `Job Post Wizard Job Details Completed`, `Job Post Wizard Intake Mode Selected`, `Job Post Wizard Role Requirements Completed`, `Job Post Wizard Interview Questions Completed`, `Job Post Wizard Verification Completed`, `Job Post Wizard Verification Skipped`, `Job Post Wizard Back Button Clicked`, `Sam Session Started`, `Sam Session Setup Failed`, `Sam Session Ended`, `Job Posting Published`.

**Status:** Tested locally. Frontend wizard helpers derive `wizard_mode` and `job_post_status` from job state. Backend adds `wizard_mode` on `Job Posting Published`.

→ On merge: add `wizard_mode` and `job_post_status` to all listed events in `docs/event-catalog.md`. Add to Property Dictionary.

> **Changed from draft:** Plan only specified `wizard_mode`. Revision also adds `job_post_status`.

---

### M2. Record Video Button Clicked (enriched — now fires on intro page)

The existing catalog event `Record Video Button Clicked` now fires on the intro video recording page (when user clicks the red record button) instead of from the Job Details panel. The Job Details panel navigation is handled by the new `Intro Video Record Button Clicked` (#23) and `Intro Video Edit Button Clicked` (#24).

**New context and properties on the intro page:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `record_button` or `edit_intro_video` | Depends on has_existing_video |
| `component` | string | `intro_video_recorder` | Video recorder on intro page |
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `entity_type` | string | `job` | Business object context |
| `has_existing_video` | boolean | `true`/`false` | Whether replacing existing video |
| `intro_video_status` | enum | `create`, `edit` | Create vs edit mode |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Script character count |
| `takes_count` | number | e.g., `1` | Current take number |

**Status:** Tested locally.

→ On merge: update `Record Video Button Clicked` in `docs/event-catalog.md` — enrich properties, update Source to Frontend.

---

### M3. Intro Script Updated (enriched — source changed to Frontend)

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `edit_method` | enum | `manual`, `ai_regenerate`, `ai_guided_regenerate` | How the script was edited |
| `entity_type` | string | `job` | Business object context |
| `has_ai_instruction` | boolean | `true`/`false` | Whether user provided guidance (for AI methods) |
| `intro_video_status` | enum | `create`, `edit` | Create vs edit mode |
| `job_id` | string | UUID | Job identifier |
| `original_script_length` | number | e.g., `410` | Script length before edit |
| `previous_page_context` | string | snake_case or null | Previous page |
| `script_length` | number | e.g., `450` | Script length after edit |

**Guard:** Only fires when script actually changed (compares original vs new text). Tested locally.

→ On merge: update `Intro Script Updated` in `docs/event-catalog.md` — change Source to Frontend, update `edit_method` values (add `manual`, `ai_guided_regenerate`; keep `ai_regenerate`), add all properties.

> **Changed from draft:** `edit_method` value `text` → `manual`. Added `ai_guided_regenerate` (regenerate with user guidance). Added `intro_video_status`.

---

### M4. Intro Video Created (enriched — source changed to Frontend)

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_intro_video` | Intro video page |
| `duration_seconds` | number or null | e.g., `45` | Video duration |
| `entity_type` | string | `job` | Business object context |
| `intro_video_status` | enum | `create` | Always create for first video |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `takes_count` | number or null | e.g., `3` | Takes before save |

**Status:** Tested locally.

→ On merge: update `Intro Video Created` in `docs/event-catalog.md` — change Source to Frontend, add properties. Note: only fires for first-time video. Re-records fire `Intro Video Recreated` (#31).

---

### M5. Intro Video Deleted (enriched — source changed to Frontend)

Already in catalog (Not Started, Backend, has `job_id`). Now fires from frontend after delete API success. Success event for `Intro Video Delete Button Clicked` (#25).

**Enriched Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `component` | string | `job_details_intro_video_menu` | Where the delete happened |
| `current_page_context` | string | `hm_job_posting_detail` | Posted job page |
| `entity_type` | string | `job` | Business object context |
| `entry_point` | string | `job_details_panel` | Where initiated |
| `has_existing_video` | boolean | `true` | Always true for delete |
| `intro_video_status` | enum | `edit` | Always edit for delete |
| `job_id` | string | UUID | Job identifier (already in catalog) |
| `job_post_status` | enum | `draft`, `active`, `null` | Job lifecycle state |
| `previous_page_context` | string | snake_case or null | Previous page |

**Status:** Tested locally.

→ On merge: update existing `Intro Video Deleted` in `docs/event-catalog.md` — change Source from Backend to Frontend, add properties above.

---

### M6. Job Share Message AI Refined (enriched)

Added `instruction_length` and `original_message_length` properties. Tested locally.

→ On merge: update in `docs/event-catalog.md` — add `instruction_length`, `original_message_length` to properties.

---

### M7. Go To Job Posting Page Clicked → Go To Job Posting Page Link Clicked

Renamed in both frontend and backend.

→ On merge: rename in `docs/event-catalog.md`. Add old name to Removed Events table.

---

## Existing Event Removal: Invite Button Clicked

Same as original plan. `Invite Button Clicked` (Not Started, never implemented) is replaced by `Invite Recruiter Button Clicked` (#7).

→ On merge: remove from `docs/event-catalog.md` Hiring Persona Events table. Add to Removed Events table. Update `docs/event-schema.md` Intent-Outcome row.

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Archiving a job | Archive Job Button Clicked | Job Status Changed | Job Status Change Failed |
| Sharing job interview | Post Interview Button Clicked | Post Interview Link Copied | -- |
| Refining share message | Refine with AI Button Clicked | Job Share Message AI Refined | Job Share Message AI Refine Failed |
| Inviting a recruiter | Invite Recruiter Button Clicked | Recruiter Invites Sent | -- |
| Editing a job posting | Edit Job Posting Button Clicked | Job Posting Republished | -- |
| Editing an interview | Edit Interview Button Clicked | Interview Saved | -- |
| Deleting a job | Delete Job Button Clicked | Job Deleted | Job Delete Failed |
| Recording intro video (first time) | Record Video Button Clicked | Intro Video Created | -- |
| Recording intro video (re-record) | Record Video Button Clicked | Intro Video Recreated | -- |
| Deleting intro video | Intro Video Delete Button Clicked | Intro Video Deleted | -- |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Archive Completion Rate | Archive Job Button Clicked → Job Status Changed | % of archive intents that complete (filter `to_status = 'archived'`) |
| Post Interview Share Rate | Post Interview Button Clicked → Post Interview Link Copied | % of HMs who copy the link after opening share modal |
| Recruiter Invite Funnel | Invite Recruiter Button Clicked → Recruiter Invites Sent | % of HMs who send at least one invite |
| Dashboard → Job Detail | Job Postings Dashboard Loaded → Job Post Clicked | % of dashboard visits that open a job |
| Edit Job Posting Funnel | Edit Job Posting Button Clicked → Job Posting Republished | % of edit intents that complete |
| Edit Interview Funnel | Edit Interview Button Clicked → Interview Saved | % of edit interview intents that complete |
| Intro Video Creation | Intro Video Record Button Clicked → Intro Video Recording Started → Intro Video Created | % of HMs who navigate, start recording, and save |
| Delete Completion Rate | Delete Job Button Clicked → Job Deleted | % of delete intents that confirm |
| Share Message Refinement | Refine with AI Button Clicked → Job Share Message AI Refined | % of refinement attempts that succeed |

---

## Property Details

→ On merge: add all new properties to `docs/event-catalog.md` Property Dictionary.

| Property | Type | Values | Description | Used In |
|---|---|---|---|---|
| `active_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Default tab on dashboard load | Job Postings Dashboard Loaded |
| `archived_count` | number | -- | Archived jobs count | Job Postings Dashboard Loaded |
| `assessment_questions_count` | number | -- | Assessment question count | Interview Saved |
| `candidates_count` | number | -- | Total candidates | Job Deleted |
| `days_since_creation` | number | -- | Days between creation and action | Job Deleted |
| `entry_point` | enum | (append) `dashboard_job_card`, `recent_sidebar`, `job_details_panel`, `chevron_menu` | UI surface origin | Job Post Clicked, Edit Job Posting Button Clicked, Intro Video Record/Edit/Delete Button Clicked |
| `existing_invites_count` | number | -- | Pending invite emails at time of click | Invite Recruiter Button Clicked |
| `from_status` | string | job status values | Status before failed change | Job Status Change Failed |
| `has_ai_instruction` | boolean | true/false | Whether user provided guidance text in the regenerate modal | Intro Script Updated (M3) |
| `has_candidates` | boolean | true/false | Whether job has candidates | More Actions Button Clicked, Edit Job Posting Button Clicked |
| `has_existing_video` | boolean | true/false | Whether intro video exists | Intro video events |
| `has_jobs` | boolean | true/false | Whether user has any jobs | Job Postings Dashboard Loaded |
| `instruction_length` | number | -- | AI instruction length | Job Share Message AI Refined, AI Refine Failed |
| `interview_id` | string | UUID | Interview identifier | Interview Link Clicked |
| `interview_name` | string | -- | Interview name | Interview Details Completed, Interview Saved |
| `intro_video_status` | enum | `create`, `edit` | First video vs re-record | All intro video events |
| `invite_count` | number | -- | Invites in batch | Recruiter Invites Sent |
| `invite_status` | enum | invite status value | Status at time of action | Recruiter Invite Link Copied, Resent, Revoked |
| `is_email_verified` | boolean | true/false | HM email verification status | Post Interview Button Clicked, Edit Job Posting Button Clicked |
| `job_post_status` | enum | `draft`, `active`, `null` | Normalized job lifecycle | Wizard events, Job Post Clicked, intro video events |
| `jobs_with_intro_video_count` | number | -- | Jobs with intro video | Job Postings Dashboard Loaded |
| `my_jobs_count` | number | -- | User's own jobs count | Job Postings Dashboard Loaded |
| `original_message_length` | number | -- | Message length before refinement | Job Share Message AI Refined, AI Refine Failed |
| `original_script_length` | number | -- | Script length before edit | Intro Script Updated |
| `pending_invites_count` | number | -- | Pending invites from response | Recruiter Invites Sent |
| `previous_status` | string | job status values | Status before deletion | Job Deleted |
| `resume_upload_option` | string | form value | Resume upload setting | Interview Details Completed, Interview Saved |
| `screening_questions_count` | number | -- | Screening question count | Interview Saved |
| `script_length` | number | -- | Script character count | Intro Video Recording Started, Intro Script Updated, script button events |
| `selected_tab` | enum | `my_jobs`, `shared_with_me`, `archived` | Active tab after switch | Job Postings Tab Switched |
| `shared_with_me_count` | number | -- | Shared jobs count | Job Postings Dashboard Loaded |
| `tab_job_count` | number | -- | Jobs in selected tab | Job Postings Tab Switched |
| `takes_count` | number | -- | Recording takes count | Intro Video Recording Started, Intro Video Created, Recreated, Re-record |
| `team_members_count` | number | -- | Non-owner collaborators | Multiple posted-job events |
| `to_status` | string | job status values | Target status that failed | Job Status Change Failed |
| `total_jobs_count` | number | -- | Sum of all jobs | Job Postings Dashboard Loaded |
| `total_questions_count` | number | -- | Sum of screening + assessment | Interview Saved |
| `views_count` | number | -- | Job view count (best-effort) | Job Deleted |
| `wizard_mode` | enum | `create`, `edit` | Wizard create vs edit mode | All wizard events |

---

## New Events

All events tested locally.

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|
| Job Postings Dashboard Loaded | Hiring | Job data loads on dashboard mount | `current_page_context`, `previous_page_context`, `entity_type`, `my_jobs_count`, `shared_with_me_count`, `archived_count`, `total_jobs_count`, `has_jobs`, `active_tab`, `jobs_with_intro_video_count`, `team_members_count` | -- | -- |
| Job Postings Tab Switched | Hiring | User switches dashboard tab | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `selected_tab`, `tab_job_count` | -- | -- |
| Job Status Change Failed | Hiring | Status change API returns error | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `error_category`, `error_reason`, `from_status`, `to_status` | `job` | -- |
| Post Interview Button Clicked | Hiring | User clicks "+ Post Interview" on job card | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `is_email_verified`, `has_intro_video` | `job` | -- |
| Post Interview Link Copied | Hiring | User clicks "Copy link" in share modal | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id` | `job` | -- |
| Job Post Clicked | Hiring | User clicks a job card or recent sidebar link | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `entry_point`, `job_id`, `job_title`, `has_intro_video`, `job_post_status` | `job` | -- |
| Invite Recruiter Button Clicked | Hiring | User clicks "Invite recruiter" on posted job page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `existing_invites_count`, `team_members_count` | `job` | -- |
| View Interview Button Clicked | Hiring | User clicks "View Interview" on posted job page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `questions_count`, `team_members_count` | `job` | -- |
| Recruiter Invites Sent | Hiring | "Send invites" API confirms | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_count`, `pending_invites_count` | `job` | -- |
| Recruiter Invite Link Copied | Hiring | User copies an invite link | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Recruiter Invite Resent | Hiring | Resend API confirms | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Recruiter Invite Revoked | Hiring | Revoke API confirms | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `invite_status` | `job` | -- |
| Job Details Button Clicked | Hiring | User clicks "Job details" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `team_members_count` | `job` | -- |
| More Actions Button Clicked | Hiring | User opens more actions dropdown | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `has_candidates`, `team_members_count` | `job` | -- |
| Edit Job Posting Button Clicked | Hiring | User clicks "Edit" or "Edit job posting" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `entry_point`, `is_email_verified`, `has_candidates`, `team_members_count` | `job` | -- |
| Open Preview Button Clicked | Hiring | User clicks "Open preview" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_intro_video` | `job` | -- |
| Edit Interview Button Clicked | Hiring | User clicks "Edit interview" | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `team_members_count` | `job` | -- |
| Interview Details Completed | Hiring | User clicks "Next" on edit interview step 1 | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `interview_name`, `resume_upload_option`, `identity_verification_mode` | `job` | -- |
| Interview Saved | Hiring | User clicks "Create Interview" | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `interview_name`, `resume_upload_option`, `identity_verification_mode`, `screening_questions_count`, `assessment_questions_count`, `total_questions_count` | `job` | -- |
| Delete Job Button Clicked | Hiring | User clicks "Delete" in chevron menu | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `team_members_count` | `job` | -- |
| Job Deleted | Hiring | Delete API confirms | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `job_title`, `previous_status`, `candidates_count`, `views_count`, `days_since_creation` | `job` | -- |
| Job Delete Failed | Hiring | Delete API fails | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `error_category`, `error_reason` | `job` | -- |
| Intro Video Record Button Clicked | Hiring | User clicks "Record" in Job Details panel (no video) | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `entry_point`, `has_existing_video`, `intro_video_status`, `job_post_status` | `job` | -- |
| Intro Video Edit Button Clicked | Hiring | User clicks "Edit intro video" in Job Details panel | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `entry_point`, `has_existing_video`, `intro_video_status`, `job_post_status` | `job` | -- |
| Intro Video Delete Button Clicked | Hiring | User clicks "Delete" on intro video | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `entry_point`, `has_existing_video`, `intro_video_status`, `job_post_status` | `job` | -- |
| Intro Video Script Regenerate Button Clicked | Hiring | User clicks "Regenerate" on intro video page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_existing_video`, `intro_video_status`, `script_length` | `job` | -- |
| Intro Video Script Edit Button Clicked | Hiring | User clicks "Edit" on intro video script | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_existing_video`, `intro_video_status`, `script_length` | `job` | -- |
| Intro Video Recording Started | Hiring | User clicks red "Record" on intro video page | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_existing_video`, `intro_video_status`, `script_length`, `takes_count` | `job` | -- |
| Intro Video Re-record Button Clicked | Hiring | User clicks "Re-record" after reviewing take | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `has_existing_video`, `intro_video_status`, `script_length`, `takes_count` | `job` | -- |
| Intro Video Recreated | Hiring | Upload completes for re-recorded video | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `duration_seconds`, `takes_count`, `intro_video_status` | `job` | -- |
| Refine with AI Button Clicked | Hiring | User clicks "Refine with AI" in share modal | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `message_length` | `job` | -- |
| Job Share Message AI Refine Failed | Hiring | AI refinement API fails | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `error_category`, `error_reason`, `instruction_length`, `original_message_length` | `job` | -- |
| Interview Link Clicked | Hiring | User clicks interview link in share/invite modal | `action`, `action_value`, `component`, `current_page_context`, `previous_page_context`, `entity_type`, `interview_id`, `job_id` | `job` | -- |
| Job Posting Republished | Hiring | Edit-mode save republishes a live job | `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode`, `wizard_mode` | `job` | -- |

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

### `docs/event-catalog.md`

**Hiring Persona Events table:**
- [ ] Add 35 new events (see summary table above)
- [ ] Update `Record Video Button Clicked` — enrich properties, change trigger description
- [ ] Update `Intro Script Updated` — change Source to Frontend, update `edit_method` values, add properties
- [ ] Update `Intro Video Created` — change Source to Frontend, add properties, note: first-time only
- [ ] Update `Intro Video Deleted` — change Source to Frontend, add properties
- [ ] Update `Job Posting Published` — add `wizard_mode: 'create'`
- [ ] Update `Job Share Message AI Refined` — add `instruction_length`, `original_message_length`
- [ ] Remove `Invite Button Clicked` → add to Removed Events
- [ ] Rename `Go To Job Posting Page Clicked` → `Go To Job Posting Page Link Clicked` → add old name to Removed Events
- [ ] Add `wizard_mode` and `job_post_status` to all wizard events
- [ ] Add all new properties to Property Dictionary (see New Properties Summary)

### `docs/event-schema.md`

- [ ] Add new Standard Objects (see table above)
- [ ] Add Intent-Outcome rows for new flows
- [ ] Update `edit_method` enum — add `manual`, `ai_guided_regenerate`
- [ ] Add `intro_video_status` enum — `create`, `edit`
- [ ] Add `job_post_status` enum — `draft`, `active`, `null`
- [ ] Update Intent-Outcome row for "Inviting team member": `Invite Button Clicked` → `Invite Recruiter Button Clicked`
- [ ] Update Intent-Outcome row for "Recording intro video": add `Intro Video Recreated` as alternate success

### `docs/dashboards.md`

- [ ] No dashboard changes initially. Events supplement the existing Hiring Dashboard.
