# Tracking Plan: Hiring Manager Job Post Wizard

**Product:** Helix (SeekOut.ai)
**Feature:** Job post wizard flow (hiring manager persona)
**Date:** 2026-05-11 (v1), 2026-05-28 (v2 — rebased on latest develop)
**Related PRD:** —
**Helix branch:** `posthog-hiring-manager-job-wizard-event-schema-v2` (off latest `develop`)

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## Implementation & Testing Status

All events are implemented and tested on Helix branch `posthog-hiring-manager-job-wizard-event-schema-v2` (off latest `develop`). Frontend tests: 278 files / 3738 tests passing. Backend tests: 4397 passing.

### What was implemented

**Frontend (11 files changed):**
- `frontend/src/lib/jobWizardAnalytics.ts` — NEW: 6 analytics helper functions, page context constants, step metadata
- `frontend/src/lib/posthogEvents.ts` — ADD: 17 new event constants (wizard steps, Sam sessions, archive)
- `frontend/src/components/common/JobInput.tsx` — ADD: Page Viewed, Wizard Started, Job Details Completed
- `frontend/src/pages/interview/JobDetail.tsx` — ADD: Page Viewed, Intake Mode Selected (3 paths), Back Button
- `frontend/src/pages/interview/EmbeddedSamSession.tsx` — ADD: Page Viewed, Sam Session Started, Sam Session Ended
- `frontend/src/pages/interview/RoleRequirements.tsx` — ADD: Page Viewed, Role Requirements Completed, Add Button, Back Button
- `frontend/src/pages/interview/InterviewQuestions.tsx` — ADD: Page Viewed, Interview Questions Completed, Add Button, Back Button
- `frontend/src/pages/interview/JobVerify.tsx` — ADD: Page Viewed, Send Code, Verification Completed, Verification Skipped, Back Button (with auto-skip dedup)
- `frontend/src/pages/interview/JobSuccess.tsx` — ADD: Page Viewed
- `frontend/src/pages/recruiter/JobList.tsx` — MODIFY: Create Job Button Clicked (enriched), ADD: Archive Job Button Clicked
- `frontend/src/stores/voiceStore.ts` — MODIFY: pass `lastSetupFailure` error info for Sam Session Started

**Backend (4 files changed):**
- `backend/app/core/analytics.py` — NEW: `base_job_setup_properties()` and `build_job_setup_analytics_snapshot()` helpers
- `backend/app/shared/posthog_events.py` — ADD: 13 new event constants, `get_current_persona()` helper
- `backend/app/core/router.py` — MODIFY: replace `Job Created` with `Job Posting Draft Created`, ADD: `Screening Configuration Saved`, `Job Posting Published`, `Job Status Changed` (archive), `Job Posting Verified`
- `backend/app/jobflow/router.py` — MODIFY: replace `Job Published` with `Job Posting Published`, ADD: `Screening Configuration Saved`, update all events to use `current_persona`

**Noise reduction (frontend, 5 files):**
- Removed 8 noisy events (widget_displayed, widget_interacted, voice_connected/disconnected, session_started/ended, intake_completed, Chat WebSocket Connected)
- Gated `Career Coach Message Sent` to skip `HM_INTERVIEWER` agent type
- Page Viewed dedup guard on RoleSelection page (Login/SignUp deferred — see Deferred Items)

> **Note:** `main.tsx` auth session restore noise reduction and `authStore.ts` `is_new_user` were deferred from PR 555. See Deferred Items section.

---

## v2 Implementation Reference

This section maps every event to its exact location in the Helix v2 codebase. An LLM reading this should know exactly which file, function, and trigger condition produces each event.

### Frontend Analytics Architecture

All wizard events flow through helper functions in `frontend/src/lib/jobWizardAnalytics.ts`:

| Helper | Fires Event | Adds Standard Properties |
|--------|-------------|------------------------|
| `captureJobWizardStarted()` | `Job Post Wizard Started` | `start_source`, `current_page_context` |
| `captureJobWizardPageViewed(ctx, jobId?, extra?)` | `Page Viewed` | `current_page_context`, `previous_page_context`, `entity_type: 'job'`, `job_id`, `$groups` |
| `captureJobWizardStepCompleted(event, step, jobId, extra?)` | *(passed event name)* | `action: 'click'`, `action_value: 'next_button'`, `current_page_context`, `previous_page_context`, `entity_type: 'job'`, `component: 'job_creation_wizard_footer_cta'`, `job_id`, `$groups`, `step_number`, `step_name` |
| `captureJobWizardInteraction(event, step, jobId, actionValue, component?, extra?)` | *(passed event name)* | Same as above but with custom `action_value` and optional custom `component` |
| `captureSamSessionStarted(jobId, inputMode, sessionId?, voiceStatus?)` | `Sam Session Started` | `current_page_context`, `previous_page_context`, `entity_type: 'job'`, `job_id`, `$groups`, `input_mode`, `session_id`, and if voice: `mic_enabled`, `error_category`, `error_reason` |
| `captureSamSessionEnded(jobId, inputMode, durationSeconds, endedBy, sessionId?)` | `Sam Session Ended` | `current_page_context`, `previous_page_context`, `entity_type: 'job'`, `job_id`, `$groups`, `input_mode`, `duration_seconds`, `ended_by`, `session_id` |

**Constants:** `JOB_WIZARD_PAGE_CONTEXTS` (9 contexts) and `JOB_WIZARD_STEPS` (5 steps with `stepNumber`, `stepName`, `pageContext`).

**Guard pattern — `shouldTrackWizard`:** Used in `RoleRequirements.tsx` and `InterviewQuestions.tsx`. These pages are shared between HM wizard flow and recruiter source-network flow. The guard ensures analytics only fire for the wizard path (HM persona or recruiter on source route), not for recruiters viewing standalone pages.

### Backend Analytics Architecture

All backend job setup events use helpers in `backend/app/core/analytics.py`:

| Helper | Returns | Used By |
|--------|---------|---------|
| `base_job_setup_properties(job)` | `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility` | All backend job events |
| `build_job_setup_analytics_snapshot(job, db)` | Base props + `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `Screening Configuration Saved`, `Job Posting Verified`, `Job Posting Published` |

All backend events include `current_persona: get_current_persona(user.role)` from `shared/posthog_events.py`.

### File-by-File Event Map

#### `frontend/src/components/common/JobInput.tsx` — Step 1: Job Details

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` on mount, `flow === Flow.RECRUITER` | `current_page_context: 'hm_job_creation_wizard_job_details'` | `[]` deps (once) |
| `Job Post Wizard Started` | Same useEffect, `isNewWizard && !isEditMode` | `start_source: 'create_job_button'` | Clears router state after fire |
| `Job Post Wizard Job Details Completed` | After `createCoreJob()` succeeds + analysis ready | Standard step-completed + `step_number: 1` | — |

#### `frontend/src/pages/interview/JobDetail.tsx` — Step 2: Understanding the Role

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when `job` loads | `current_page_context: 'hm_job_creation_wizard_understanding_the_role'`, `job_id` | — |
| `Job Post Wizard Intake Mode Selected` | User clicks "Next" (voice/text selected) | `intake_mode: 'voice' \| 'text'`, `step_number: 2` | — |
| `Job Post Wizard Intake Mode Selected` | User clicks "Skip" | `action_value: 'skip_button'`, `intake_mode: 'skipped'` | — |
| `Job Post Wizard Back Button Clicked` | User clicks "Back" | `step_number: 2`, `step_name: 'understanding_the_role'` | — |

#### `frontend/src/pages/interview/EmbeddedSamSession.tsx` — Sam Conversation

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when `modeChosen && selectedMode && jobId` | `current_page_context: '..._sam_voice_session' \| '..._sam_text_session'`, `input_mode` | `samPageViewed.current` ref |
| `Sam Session Started` | After `startEmbeddedHmSession()` succeeds | `input_mode`, `session_id`, voice: `mic_enabled`, `error_category`, `error_reason` | — |
| `Sam Session Ended` | `intake_summary` widget appears (completed) OR user confirms "End Session" (user) | `input_mode`, `duration_seconds`, `ended_by: 'user' \| 'completed'`, `session_id` | `samSessionEnded.current` ref |

**Voice failure flow:** `voiceStore.ts` catches errors in `startVoice()` catch block → classifies them by checking error message (timeout → 'timeout', permission → 'hardware', else → 'unknown') → stores as `lastSetupFailure: { category, reason }` → `EmbeddedSamSession.tsx` reads it and passes to `captureSamSessionStarted()` as `voiceStatus`.

#### `frontend/src/pages/interview/RoleRequirements.tsx` — Step 3

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when loaded + `shouldTrackWizard` | `current_page_context: 'hm_job_creation_wizard_role_requirements'` | `pageViewed.current` ref |
| `Job Post Wizard Role Requirements Completed` | User clicks "Next" after save + `shouldTrackWizard` | `step_number: 3` | — |
| `Requirement Add Button Clicked` | User clicks "+ Add" (legacy or v2 editor) + `shouldTrackWizard` | `action_value: 'add_question_button'`, `component: 'role_requirements_add_question_cta'` | — |
| `Job Post Wizard Back Button Clicked` | User clicks "Back" + `shouldTrackWizard` | `step_number: 3` | — |

#### `frontend/src/pages/interview/InterviewQuestions.tsx` — Step 4

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when loaded + not generating + `shouldTrackWizard` | `current_page_context: 'hm_job_creation_wizard_interview_questions'` | `pageViewedRef.current` ref |
| `Job Post Wizard Interview Questions Completed` | User clicks "Next" after save + `shouldTrackWizard` | `step_number: 4`, `identity_verification_mode: 'require' \| 'off'` | — |
| `Question Add Button Clicked` | User clicks "+ Add" + `shouldTrackWizard` | `action_value: 'add_question_button'`, `component: 'interview_questions_add_question_cta'` | — |
| `Job Post Wizard Back Button Clicked` | User clicks "Back" + `shouldTrackWizard` | `step_number: 4` | — |

**Special path:** If `hasRecentlyVerifiedEmail` is true when user clicks "Next", the component navigates directly to success (skipping verify step). The `Interview Questions Completed` event still fires.

#### `frontend/src/pages/interview/JobVerify.tsx` — Step 5: Verify

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when loaded | `current_page_context: 'hm_job_creation_wizard_verify'` | `pageViewedRef.current` ref; auto-skip navigates away before this fires |
| `Job Verification Code Send Button Clicked` | User clicks "Send code" with valid email | `action_value: 'send_code_button'`, `step_number: 5` | — |
| `Job Post Wizard Verification Completed` | `handleVerified()` callback after successful code | `step_number: 5` | — |
| `Job Post Wizard Verification Skipped` | User clicks "Maybe later" | `action_value: 'maybe_later_link'` | `autoSkipping.current` guard — does NOT fire on auto-skip paths |
| `Job Post Wizard Back Button Clicked` | User clicks "Back" | `step_number: 5` | — |

**Auto-skip logic (3 paths, no analytics events fire):**
1. `job.is_verified === true` → navigate to success
2. `hasRecentlyVerifiedEmail(alternateEmailAddresses)` → mark complete, navigate to success
3. `!isPersonalEmail(user.email)` (work domain) → mark complete, navigate to success

The `autoSkipping` ref prevents `Verification Skipped` from firing during these paths.

#### `frontend/src/pages/interview/JobSuccess.tsx` — Success Page

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` when `job` is truthy | `current_page_context: 'hm_job_creation_wizard_success'` | `pageViewed.current` ref |

#### `frontend/src/pages/recruiter/JobList.tsx` — Job Postings Home

| Event | Trigger | Key Properties | Dedup |
|-------|---------|----------------|-------|
| `Page Viewed` | `useEffect` on mount | `current_page_context: 'recruiter_ai_job_flows' \| 'hiring_manager_job_postings'`, `current_persona` | `previousPageContext === currentPageCtx` guard |
| `Create Job Button Clicked` | User clicks "+ Create job" (header or empty state) | `action_value: 'create_job_posting_button' (recruiter) \| 'create_job_button' (HM)`, `component` varies by location+role, `current_persona` | — |
| `Share Button Clicked` | User clicks share on job card | `action_value: 'share_job_button'`, `component: 'job_card'`, `context_object_id: job.id`, `current_persona` | — |
| `Archive Job Button Clicked` | User clicks archive in overflow menu | `action_value: 'archive_job_menu_item'`, `component: 'job_card_overflow_menu'`, `job_id`, `current_persona` | — |

#### `backend/app/core/router.py` — Core Job Endpoints

| Event | Endpoint | Trigger Condition | Key Properties |
|-------|----------|-------------------|----------------|
| `Job Posting Draft Created` | `POST /api/v1/core/job` | `create_job()` succeeds | `base_job_setup_properties(job)` + `current_persona` |
| `Job Creation Failed` | `POST /api/v1/core/job` | `create_job()` raises exception | `current_persona`, `error_reason` |
| `Screening Configuration Saved` | `PATCH /api/v1/core/job/{job_id}` | `update_job()` transitions wizard_step to verify/COMPLETED from non-verify/COMPLETED, non-ATS only | Full `build_job_setup_analytics_snapshot` |
| `Job Posting Published` | `PATCH /api/v1/core/job/{job_id}` | `update_job()` transitions status to active/published + wizard_step to COMPLETED, non-ATS, first time only | Full snapshot |
| `Job Posting Published` | `POST /api/v1/core/job/{job_id}/finalize` | `finalize_job_setup()` transitions to published/active+COMPLETED | Full snapshot |
| `Job Posting Verified` | `POST /api/v1/core/job/{job_id}/verify/confirm` | `confirm_job_verification()` succeeds with `verified=True` | Full snapshot |
| `Job Status Changed` | `POST /api/v1/core/job/{job_id}/archive` | `archive_job()` | `current_persona`, `job_id`, `from_status`, `to_status: 'archived'` |

**`group_identify`** fires on `Job Posting Draft Created` with: `job_title`, `job_status`, `created_by_user_id`, `created_at`.

#### `backend/app/jobflow/router.py` — Jobflow Endpoints

| Event | Endpoint | Trigger Condition | Key Properties |
|-------|----------|-------------------|----------------|
| `Screening Configuration Saved` | `POST /api/v1/jobs/flow/{job_id}/screening` | `configure_screening()` | Full snapshot |
| `Job Posting Published` | `POST /api/v1/jobs/flow/{job_id}/verify` | `verify_and_publish()` | Full snapshot |
| `Job Status Changed` | `POST /api/v1/jobs/flow/{job_id}/archive` | `archive_job()` | `current_persona`, `job_id`, `from_status`, `to_status: 'archived'` |
| `Job Status Changed` | `POST /api/v1/jobs/flow/{job_id}/unarchive` | `unarchive_job()` | `current_persona`, `job_id`, `from_status: 'archived'`, `to_status: job.status` |
| `Job Shared` | `POST /api/v1/jobs/flow/{job_id}/access` | `grant_access()` succeeds | `current_persona`, `job_id`, `shared_by_user_id`, `share_channel: 'other'` |
| `Job Share Failed` | `POST /api/v1/jobs/flow/{job_id}/access` | `grant_access()` raises | `current_persona`, `job_id`, `error_reason` |
| `Team Member Invited` | `POST /api/v1/jobs/flow/{job_id}/intake/invite-hm` | `invite_hm()` succeeds | `current_persona`, `job_id`, `invited_role_label: 'hiring_manager'`, `invite_method: 'email'` |
| `Team Member Invite Failed` | `POST /api/v1/jobs/flow/{job_id}/intake/invite-hm` | `invite_hm()` raises | `current_persona`, `job_id`, `error_reason` |

**`group_identify`** fires on publish (`job_status`, `job_visibility`), archive (`job_status: 'archived'`), and unarchive (`job_status`).

---

## User Flow

```text
HM Job Postings page (home)
  │
  ├─ Step 0: Clicks "+ Create job" (header or empty state)
  │    → fires: Create Job Button Clicked
  │
  ├─ Wizard Init: Page loads (with router state isNewWizard=true)
  │    → fires: Job Post Wizard Started (once per fresh wizard entry)
  │
  ├─ Step 1: Job Details — paste JD, AI evaluates, click Next
  │    → fires: Page Viewed (hm_job_creation_wizard_job_details)
  │    → fires: Job Post Wizard Job Details Completed — on Next click
  │    → fires: Job Posting Draft Created (backend — draft saved with job_id)
  │
  ├─ Step 2: Understanding the Role — choose Voice / Text / Skip
  │    → fires: Page Viewed (hm_job_creation_wizard_understanding_the_role)
  │    → fires: Job Post Wizard Intake Mode Selected
  │
  ├─ Step 3: Role Requirements — review AI-drafted requirements
  │    → fires: Page Viewed (hm_job_creation_wizard_role_requirements)
  │    → fires: Job Post Wizard Role Requirements Completed
  │
  ├─ Step 4: Interview Questions — review AI-generated questions
  │    → fires: Page Viewed (hm_job_creation_wizard_interview_questions)
  │    → fires: Job Post Wizard Interview Questions Completed
  │
  ├─ Step 5: Verify — email verification
  │    → fires: Page Viewed (hm_job_creation_wizard_verify)
  │    → fires: Job Post Wizard Verification Completed
  │
  └─ Success: Job posting is live
       → fires: Job Posting Published (backend — final)
```

---

## Events

### 1. Create Job Button Clicked

User clicks "+ Create job" to start the job creation wizard.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Intent (for Job Created) |
| **Trigger** | User clicks "+ Create job" button on HM job postings page |
| **Source** | Frontend |
| **Group** | -- (no job_id yet) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `create_job_button` | Both buttons share the label "+ Create job" |
| `current_page_context` | string | `hiring_manager_job_postings` | Always fired from the job postings page |
| `previous_page_context` | string | snake_case page identifier or null | Previous page |
| `entity_type` | string | `job` | Business object being created |
| `component` | string | `hm_job_postings_header_cta` or `hm_job_postings_empty_state_cta` | Distinguishes top-right button vs middle empty-state button |

**PostHog call:**

```javascript
posthog.capture('Create Job Button Clicked', {
  action: 'click',
  action_value: 'create_job_button',
  current_page_context: 'hiring_manager_job_postings',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'hm_job_postings_header_cta',  // or 'hm_job_postings_empty_state_cta'
});
```

**Notes:**
- No `job_id` — the job doesn't exist yet at this point
- `component` is the key differentiator — tells you which button the user clicked
- The empty-state button only appears when the user has 0 jobs

---

### 1b. Job Post Wizard Started

Fires once when the user opens the wizard for a brand new job. This is the **outcome** event for `Create Job Button Clicked` (intent) — confirms the wizard successfully loaded.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Wizard page mounts with `location.state.isNewWizard === true` and no existing `jobId` |
| **Source** | Frontend |
| **Group** | — (no job_id yet) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `start_source` | string | `create_job_button` | Entry point that initiated the wizard |
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Step 1 page |

**How dedup works — router state approach (no backend table needed):**

The "+ Create job" button navigates with `{ state: { isNewWizard: true } }`. The wizard checks this on mount. Browser router state is ephemeral — it exists on fresh navigation and is lost on refresh. This naturally prevents double-firing.

After firing the event, the wizard replaces the history entry to clear the state (prevents back/forward re-firing):

```javascript
// In the "+ Create job" button handler (JobList.tsx → onClick of the header create button)
// Currently: navigate(routes.create);
// Change to:
navigate(routes.create, { state: { isNewWizard: true } });
```

```javascript
// In the wizard page component (JobInput.tsx) on mount
const location = useLocation();
const [searchParams] = useSearchParams();
const isNewWizard = location.state?.isNewWizard === true;
const editJobId = searchParams.get('jobId');
const isEditMode = !!editJobId;

if (isNewWizard && !isEditMode) {
  capture('Job Post Wizard Started', {
    start_source: 'create_job_button',
    current_page_context: 'hm_job_creation_wizard_job_details',
  });

  // Clear router state so back/forward doesn't re-fire
  navigate(location.pathname, { replace: true, state: {} });
}
```

**Guardrails — when the event fires and doesn't fire:**

| Scenario | `isNewWizard` (router state) | `editJobId` (URL param) | Fires? |
|---|---|---|---|
| Fresh "+ Create job" | `true` | absent | **Yes** |
| Page refresh on step 1 | `undefined` (state lost on refresh) | absent | No |
| "Continue setup" (resume draft) | `undefined` (different navigation) | present (`?jobId=abc`) | No |
| Edit published job | `undefined` (navigates to detail page) | present | No |
| Direct URL to wizard | `undefined` | absent | No |
| Browser back then forward | `undefined` (cleared by `replace: true`) | absent | No |
| New wizard after completing previous job | `true` (fresh button click) | absent | **Yes** |

**How to distinguish entry context on wizard step events:**

The wizard can determine why the user is here using existing `jobs` table fields — no new table needed:

```
No jobId in URL          → Brand new wizard (first time)
jobId + status=draft     → Resuming incomplete wizard ("Continue setup")
jobId + status=published → Editing existing live job
```

Use this on step events for richer analytics:

```javascript
posthog.capture('Job Post Wizard Job Details Completed', {
  job_id: jobId,
  step_number: 1,
  step_name: 'job_details',
  entry_context: 'new',  // 'new' | 'resume_draft' | 'edit_published'
});
```

**Abandonment analysis (without a backend table):**

Build a PostHog funnel:
```
Step 1: Job Post Wizard Started
Step 2: Job Post Wizard Job Details Completed
```
Users who completed step 1 but NOT step 2 = wizard abandonment at step 1. PostHog funnels handle this natively — no DB query needed.

**Linking to job_id (without a custom session ID):**

PostHog auto-captures `$session_id` on every event. Both `Job Post Wizard Started` and `Job Post Wizard Job Details Completed` (which carries `job_id`) fire in the same browser session. Query by `$session_id` to link them.

**Notes:**
- No `job_id` on this event — the job doesn't exist yet (created on step 1 "Next" click)
- No backend changes required — uses React Router state (already an established pattern in the Helix codebase)
- `navigate(location.pathname, { replace: true, state: {} })` is critical — without it, browser back/forward can re-fire the event

---

#### Helix Implementation

**No backend changes.** No new table, endpoint, or migration. Frontend-only: 2 files.

##### Codebase Change 1: Add PostHog event constant

**Edit** `frontend/src/lib/posthogEvents.ts` — add:

```typescript
export const JOB_POST_WIZARD_STARTED = 'Job Post Wizard Started';
```

##### Codebase Change 2: Pass router state on navigation

**Edit** `frontend/src/pages/recruiter/JobList.tsx` — in all three "+ Create job" button click handlers (header button, empty state hero, and empty job list button), wherever `navigate(routes.create)` is called, add router state:

```typescript
// Currently:
navigate(routes.create);

// Change to:
navigate(routes.create, { state: { isNewWizard: true } });
```

> This follows the existing codebase pattern — `JobList.tsx` already uses router state for the share/interview flow (`navigate(setupRoutes.createInterview(shareJob.id), { state: { isInbound: shareJob.isInbound } })` inside the `handleShareContinue` callback). The "+ Create job" button currently uses plain `navigate(routes.create)` with no state — this change adds `{ state: { isNewWizard: true } }` using the same router state mechanism. There are three places where `navigate(routes.create)` is called (header button, empty state hero, and empty job list button) — all three must be updated.

##### Codebase Change 3: Fire event on wizard mount

**Edit** `frontend/src/components/common/JobInput.tsx` — add to the component mount logic:

```typescript
// NEW import — add to existing imports:
import { JOB_POST_WIZARD_STARTED } from '@/lib/posthogEvents';

// EXISTING: const routerLocation = useLocation();
// EXISTING: const navigate = useNavigate();
// EXISTING: const launchedFromAgents = isAgentsLauncherState(routerLocation.state);
// EXISTING: const editJobId = ...; const isEditMode = !!editJobId;

// ADD — new check alongside the existing agents launcher check:
const isNewWizard = routerLocation.state?.isNewWizard === true;

// ADD — fire event on mount:
useEffect(() => {
  if (isNewWizard && !isEditMode) {
    capture(JOB_POST_WIZARD_STARTED, {
      start_source: 'create_job_button',
      current_page_context: 'hm_job_creation_wizard_job_details',
    });

    // Clear only the isNewWizard key from router state — preserves other
    // state keys (e.g., agents launcher state) that may also be present
    const { isNewWizard: _, ...remainingState } = (routerLocation.state || {});
    navigate(routerLocation.pathname, { replace: true, state: remainingState });
  }
}, []);  // Run once on mount
```

> **Important context for engineers:** `JobInput.tsx` already reads `routerLocation.state` for the agents launcher check (`isAgentsLauncherState`). The `isNewWizard` check is a separate key on the same state object — they don't conflict. When clearing state after firing the event, we only remove `isNewWizard` and preserve any other state keys (like the agents launcher state) so existing functionality is not broken.

**Files to modify:**

| File | Change | Lines affected |
|---|---|---|
| `frontend/src/lib/posthogEvents.ts` | Add constant | 1 line |
| `frontend/src/pages/recruiter/JobList.tsx` | Add `{ state: { isNewWizard: true } }` to all three `navigate(routes.create)` calls | 3 call sites |
| `frontend/src/components/common/JobInput.tsx` | Add `isNewWizard` check + useEffect with capture + selective state clear | ~15 lines |

---

### Step 1: Job Details

#### 2a. Page Viewed (page load)

Fires when the Job Details wizard step loads. No `job_id` yet — draft hasn't been created.

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_job_details',
  previous_page_context: getPreviousPageContext(),  // 'hiring_manager_job_postings'
  entity_type: 'job',
});
```

---

#### 2b. Job Post Wizard Job Details Completed (user action — Next click)

User clicks "Next →" after pasting JD and AI evaluation completes.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Next →" on a wizard step |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `next_button` | The "Next →" button |
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Current wizard step page |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object context |
| `component` | string | `job_creation_wizard_footer_cta` | Footer area where Next lives |
| `job_id` | UUID | job ID | Job ID — available from step 1 onwards (draft created on this click) |
| `step_number` | number | `1` | Wizard step number (1–5) |
| `step_name` | enum | `job_details` | Wizard step name |

**PostHog call:**

```javascript
posthog.capture('Job Post Wizard Job Details Completed', {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard_job_details',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 1,
  step_name: 'job_details',
});
```

**Notes:**
- Each wizard step has its own event name (`Job Post Wizard Job Details Completed`, `Intake Mode Selected`, `Role Requirements Completed`, `Interview Questions Completed`, `Verification Completed`) — `step_number` and `step_name` properties are also included for programmatic filtering
- `step_name` values across wizard: `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify`
- `job_id` is included from step 1 onwards — the draft is created on this Next click and the ID is available in the response. All subsequent steps carry the same `job_id`.

---

#### 2c. Job Posting Draft Created (backend — draft saved)

Server creates the job draft after JD evaluation on step 1. The job is persisted — if the user abandons the wizard, it appears on the home page with "Continue setup".

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Server creates job draft via `POST /api/v1/core/job` → `create_job()` in `core/router.py` |
| **Source** | Backend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Actual source | Description |
|---|---|---|---|
| `job_id` | UUID | `job.id` | The newly created job identifier |
| `job_title` | string | `job.title` | Job title extracted from JD |
| `company_name` | string | `job.company_name` | Company name extracted from JD (can be null) |
| `job_location` | string | `job.location` | Location extracted from JD (can be null) |
| `job_status` | enum | `job.status` | Always `"draft"` at this point |

**Property Updates:**

| Operation | Property | Description |
|---|---|---|
| `group(job)` | `job_title`, `job_status`, `created_by_user_id`, `created_at` | Initialize job group properties |

**Helix codebase change — replace existing `JOB_CREATED` in `core/router.py` lines 187-208:**

Remove the existing `JOB_CREATED` capture and `group_identify` block in `core/router.py` → `create_job()`, immediately after the try/except block for job creation:
```python
# REMOVE — find this block after `job = await service.create_job(...)` succeeds
acting_as = get_acting_as(user.role)
posthog_client.capture(
    distinct_id=str(user.user_id),
    event=JOB_CREATED,
    properties={
        PROP_SURFACE: SURFACE_HIRING,
        PROP_ACTING_AS: acting_as,
        PROP_JOB_ID: str(job.id),
    },
    groups={GROUP_JOB: str(job.id)},
)
posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={
        "job_title": job.title,
        "job_status": job.status,
        "hiring_manager_user_id": None,
        "created_by_user_id": str(user.user_id),
        "created_at": job.created_at.isoformat() if job.created_at else None,
    },
)
```

Replace with:
```python
posthog_client.capture(
    distinct_id=str(user.id),
    event="Job Posting Draft Created",
    properties={
        "job_id": str(job.id),
        "job_title": job.title,
        "company_name": job.company_name,
        "job_location": job.location,
        "job_status": job.status,  # "draft"
    },
    groups={GROUP_JOB: str(job.id)},
)
posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={
        "job_title": job.title,
        "job_status": job.status,
        "created_by_user_id": str(user.id),
        "created_at": job.created_at.isoformat() if job.created_at else None,
    },
)
```

Also update `shared/posthog_events.py`:
```python
# Replace:
JOB_CREATED = "Job Created"
# With:
JOB_POSTING_DRAFT_CREATED = "Job Posting Draft Created"
```

> **AuthUser field names by domain:**
> - `core/router.py` → `app.auth.dependencies.AuthUser` → **`user.id`** (str)
> - `jobflow/router.py` → `app.interview.auth.dependencies.AuthUser` → **`user.user_id`** (UUID)

**Notes:**
- Removes the existing `JOB_CREATED` event and its `group_identify` block in `core/router.py`
- `company_name` and `location` can be `None` if not extracted from JD — PostHog handles null values
- `job_id` is now available for all subsequent wizard steps
- If the user abandons and returns via "Continue setup", no new draft event fires — the draft already exists

---

### Step 2: Understanding the Role

Three paths: Voice chat, Text chat, or Skip.

```text
Understanding the Role page loads
  │
  ├─ Page Viewed (hm_job_creation_wizard_understanding_the_role)
  │
  ├─ Path A: User selects Voice + clicks Next
  │    → Job Post Wizard Intake Mode Selected (intake_mode: 'voice')
  │    → Page Viewed (hm_job_creation_wizard_sam_voice_session)
  │    → Sam Session Started (input_mode: 'voice')
  │    → ... user talks with Sam ...
  │    → Sam Session Ended (input_mode: 'voice', duration_seconds, ended_by)
  │
  ├─ Path B: User selects Text + clicks Next
  │    → Job Post Wizard Intake Mode Selected (intake_mode: 'text')
  │    → Page Viewed (hm_job_creation_wizard_sam_text_session)
  │    → Sam Session Started (input_mode: 'text')
  │    → ... user chats with Sam ...
  │    → Sam Session Ended (input_mode: 'text', duration_seconds, ended_by)
  │
  └─ Path C: User clicks "Skip and go to role requirements"
       → Job Post Wizard Intake Mode Selected (intake_mode: 'skipped')
```

#### 3a. Page Viewed (page load)

Fires when the Understanding the Role page loads.

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_understanding_the_role',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 3b. Job Post Wizard Intake Mode Selected (user action — mode selection)

User selects Voice/Text and clicks Next, or clicks Skip.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Next →" (with voice/text selected) or "Skip and go to role requirements" |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `next_button` or `skip_button` | Which button was clicked |
| `current_page_context` | string | `hm_job_creation_wizard_understanding_the_role` | Step 2 page |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object context |
| `component` | string | `job_creation_wizard_footer_cta` | Footer area |
| `job_id` | UUID | job ID | Job identifier |
| `step_number` | number | `2` | Wizard step |
| `step_name` | enum | `understanding_the_role` | Wizard step name |
| `intake_mode` | enum | `voice`, `text`, `skipped` | Which path the user chose |

**PostHog call:**

```javascript
posthog.capture('Job Post Wizard Intake Mode Selected', {
  action: 'click',
  action_value: 'next_button',  // or 'skip_button'
  current_page_context: 'hm_job_creation_wizard_understanding_the_role',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 2,
  step_name: 'understanding_the_role',
  intake_mode: 'voice',  // 'voice', 'text', 'skipped'
});
```

**Notes:**
- `intake_mode` is the key property — tells you what % of users chose voice vs text vs skipped Sam entirely
- Skip path goes directly to Role Requirements — no session events fire

---

#### 3c. Page Viewed (session page load — voice or text)

Fires when the Sam session page loads. The `current_page_context` distinguishes voice from text.

```javascript
// Voice session
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_sam_voice_session',
  previous_page_context: 'hm_job_creation_wizard_understanding_the_role',
  entity_type: 'job',
  job_id: jobId,
});

// Text session
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_sam_text_session',
  previous_page_context: 'hm_job_creation_wizard_understanding_the_role',
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 3d. Sam Session Started

Sam session begins (voice or text). Replaces `Voice Session Started` from the event catalog.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | Sam session initializes after user selects voice or text |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `job_id` | UUID | job ID | Job identifier |
| `input_mode` | enum | `voice`, `text` | Session type — reuses existing `input_mode` property from catalog |

**PostHog call:**

```javascript
posthog.capture('Sam Session Started', {
  job_id: jobId,
  input_mode: 'voice',  // or 'text'
});
```

**Notes:**
- Covers both voice and text sessions under one event name — `input_mode` differentiates
- Fires when the session actually initializes, not on page load
- Replaces `Voice Session Started` from `docs/event-catalog.md` — see Catalog Cleanup section

---

#### 3e. Sam Session Ended

User confirms "End Session" in the confirmation modal, or Sam auto-ends the session. Replaces `Voice Session Ended` from the event catalog.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | User clicks "End Session" in the confirmation modal, or Sam auto-ends |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `job_id` | UUID | job ID | Job identifier |
| `input_mode` | enum | `voice`, `text` | Session type — reuses existing `input_mode` property from catalog |
| `duration_seconds` | number | e.g., 180 | Time from session start to end confirmation |
| `ended_by` | enum | `user`, `completed` | Who ended the session — user clicked "End Session" or intake auto-completed |
| `session_id` | string | e.g., `session-abc` | Session identifier for backend correlation *(added in v2)* |

**PostHog call:**

```javascript
posthog.capture('Sam Session Ended', {
  job_id: jobId,
  input_mode: 'voice',  // or 'text'
  duration_seconds: sessionDuration,
  ended_by: 'user',  // or 'completed'
  session_id: sessionId,  // from initSessionForJob response
});
```

**Notes:**
- Fires on the confirmation modal "End Session" button, NOT on the first "End Session" / "End chat" click
- Covers both voice and text sessions under one event name — `input_mode` differentiates
- `ended_by` tracks whether the user ended the session or the intake auto-completed
- After this fires, user moves to the Role Requirements page
- Replaces `Voice Session Ended` from `docs/event-catalog.md` — see Catalog Cleanup section

---

> **Section 3f removed.** The original `Sam Voice Session Setup Failed` event was removed during implementation (Delta 2). Voice setup failure info is now captured as optional properties (`mic_enabled`, `error_category`, `error_reason`) on `Sam Session Started` instead. This consolidation allows analysts to build a single funnel (`Sam Session Started` → `Sam Session Ended`) and filter by `mic_enabled = false` for failures, rather than unioning two separate events. See Delta 2 for full rationale and property details.

---

### Step 3: Role Requirements

#### 4a. Page Viewed (page load)

Fires when the Role Requirements page loads.

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_role_requirements',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 4b. Job Post Wizard Role Requirements Completed (user action — Next click)

User clicks "Next →" to proceed to Interview Questions.

**PostHog call:**

```javascript
posthog.capture('Job Post Wizard Role Requirements Completed', {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard_role_requirements',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 3,
  step_name: 'role_requirements',
});
```

---

#### 4c. Job Post Wizard Role Requirements Completed (user action — Add question click)

User clicks "+ Add question" to add a new role requirement.

**PostHog call:**

```javascript
posthog.capture('Job Post Wizard Role Requirements Completed', {
  action: 'click',
  action_value: 'add_question_button',
  current_page_context: 'hm_job_creation_wizard_role_requirements',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'role_requirements_add_question_cta',
  job_id: jobId,
  step_number: 3,
  step_name: 'role_requirements',
});
```

**Notes:**
- Same `Job Post Wizard Role Requirements Completed` event name for both actions — differentiated by `action_value`
- `next_button` = moving to next step, `add_question_button` = adding a requirement within the step

---

### Step 4: Interview Questions

#### 5a. Page Viewed (page load)

Fires when the Interview Questions page loads.

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_interview_questions',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 5b. Job Post Wizard Interview Questions Completed (user action — Next click)

User clicks "Next →" to proceed to Verify.

```javascript
posthog.capture('Job Post Wizard Interview Questions Completed', {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard_interview_questions',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 4,
  step_name: 'interview_questions',
});
```

---

#### 5c. Job Post Wizard Interview Questions Completed (user action — Add question click)

User clicks "+ Add question" to add a new screening question.

```javascript
posthog.capture('Job Post Wizard Interview Questions Completed', {
  action: 'click',
  action_value: 'add_question_button',
  current_page_context: 'hm_job_creation_wizard_interview_questions',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'interview_questions_add_question_cta',
  job_id: jobId,
  step_number: 4,
  step_name: 'interview_questions',
});
```

---

#### 5d. Job Post Wizard Interview Questions Completed (user action — Back click)

User clicks "← Back" to go back to Role Requirements.

```javascript
posthog.capture('Job Post Wizard Interview Questions Completed', {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard_interview_questions',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 4,
  step_name: 'interview_questions',
});
```

---

#### 5e. Screening Configuration Saved (backend)

Backend saves the screening config when user clicks Next on step 4. Captures the full screening setup state.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | Backend saves screening config via `POST /api/v1/jobs/flow/{job_id}/screening` → `configure_screening()` |
| **Source** | Backend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Actual source | Description |
|---|---|---|---|
| `job_id` | UUID | `job.id` | Job identifier |
| `job_title` | string | `job.title` | Job posting title |
| `company_name` | string | `job.company_name` | Company name (AI-extracted from JD) |
| `job_location` | string | `job.location` | Job location |
| `questions_count` | number | `len(assessment_questions)` | Total screening questions (`InterviewAssessmentQuestion` where `is_deleted=False`) |
| `ai_generated_questions_count` | number | count where `source == "ai_generated"` | AI-generated questions |
| `manual_questions_count` | number | count where `source == "manual"` | Manually added questions |
| `identity_verification_mode` | enum | `interview.interview_options.integrity.identity_verification_mode` | `'require'` or `'off'` — the "Require ID verification" checkbox |
| `intake_mode` | string | `intake_meeting.mode` | `'ai_copilot'`, `'hm_solo'`, `'manual'`, or null if skipped |

**Helix codebase change — add to `jobflow/router.py` → `configure_screening()` (after the `service.configure_screening()` call, before the return statement):**

```python
# In jobflow/router.py → configure_screening()
# Add after: job = await service.configure_screening(job_id, data)

from sqlalchemy import select, func
from app.database.models.interview import Interview, InterviewAssessmentQuestion

# Questions are already saved in DB (saved as user adds/edits them on the page)
# Screening config (resume settings, ID verification) is saved by configure_screening()
# So at this point both are available for the event

# Query questions for this job
interview_result = await service.db.execute(
    select(Interview).where(Interview.job_id == job_id)
)
interview = interview_result.scalar_one_or_none()

questions = []
if interview:
    q_result = await service.db.execute(
        select(InterviewAssessmentQuestion).where(
            InterviewAssessmentQuestion.interview_id == interview.id,
            InterviewAssessmentQuestion.is_deleted == False,
        )
    )
    questions = q_result.scalars().all()

ai_count = sum(1 for q in questions if q.source == "ai_generated")
manual_count = sum(1 for q in questions if q.source == "manual")

# Get identity verification mode from the screening config we just saved
id_verify_mode = (
    (data.interview_options or {})
    .get("integrity", {})
    .get("identity_verification_mode", "off")
)

posthog_client.capture(
    distinct_id=str(user.user_id),
    event="Screening Configuration Saved",
    properties={
        "job_id": str(job.id),
        "job_title": job.title,
        "company_name": job.company_name,
        "job_location": job.location,
        "questions_count": len(questions),
        "ai_generated_questions_count": ai_count,
        "manual_questions_count": manual_count,
        "identity_verification_mode": id_verify_mode,
        "intake_mode": intake_meeting.mode if intake_meeting else None,
    },
    groups={GROUP_JOB: str(job.id)},
)
```

Also add to `shared/posthog_events.py`:
```python
SCREENING_CONFIGURATION_SAVED = "Screening Configuration Saved"
```

**How the two endpoints work together:**

```text
User on Interview Questions page
  │
  ├─ Questions saved FIRST (as user adds/edits them throughout the page)
  │    → Each question saved via separate API calls to interview_service
  │    → InterviewAssessmentQuestion rows with source: "ai_generated" or "manual"
  │
  └─ Screening config saved SECOND (when user clicks "Next →")
       → POST /api/v1/jobs/flow/{job_id}/screening → configure_screening()
       → Saves interview_options (resume settings, ID verification) to Job.screening_config
       → At this point questions already exist in DB → we query them for the event
       → "Screening Configuration Saved" fires HERE with both question counts AND config
```

**Notes:**
- `configure_screening()` currently has no PostHog events — this is net new
- `identity_verification_mode` comes from the `data` request object (just saved), not from DB
- Questions come from `InterviewAssessmentQuestion` table via DB query
- `user.user_id` — jobflow AuthUser field for user ID
- `service.db` provides the async session for queries

---

### Step 5: Verify

#### 6a. Page Viewed (page load)

Fires when the Verify page loads.

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_verify',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 6b. Job Post Wizard Verification Completed (user action — Send code)

User clicks "Send code" to receive a 6-digit verification code.

```javascript
posthog.capture('Job Post Wizard Verification Completed', {
  action: 'click',
  action_value: 'send_code_button',
  current_page_context: 'hm_job_creation_wizard_verify',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 5,
  step_name: 'verify',
});
```

---

#### 6c. Job Post Wizard Verification Completed (user action — Maybe later)

User clicks "Maybe later" to skip verification and publish without verifying.

```javascript
posthog.capture('Job Post Wizard Verification Completed', {
  action: 'click',
  action_value: 'maybe_later_link',
  current_page_context: 'hm_job_creation_wizard_verify',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 5,
  step_name: 'verify',
});
```

---

#### 6d. Job Post Wizard Verification Completed (user action — Back)

User clicks "← Back" to go back to Interview Questions.

```javascript
posthog.capture('Job Post Wizard Verification Completed', {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard_verify',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  component: 'job_creation_wizard_footer_cta',
  job_id: jobId,
  step_number: 5,
  step_name: 'verify',
});
```

---

#### 6e. Job Posting Verified (backend)

Backend confirms the 6-digit code is correct and the hiring manager's email is verified.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Backend verifies the 6-digit code successfully |
| **Source** | Backend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `job_id` | UUID | `job.id` | Job identifier |
| `job_title` | string | `job.title` | Job posting title |
| `job_verified` | boolean | `true` | Email verified — always true on this event |

**Helix codebase change — add to `core/router.py` → `confirm_job_verification()` (POST /api/v1/core/job/{job_id}/verify/confirm):**

```python
# Add after successful verification (after job.is_verified = True is set)
posthog_client.capture(
    distinct_id=str(user.id),
    event="Job Posting Verified",
    properties={
        "job_id": str(job.id),
        "job_title": job.title,
        "job_verified": True,
    },
    groups={GROUP_JOB: str(job.id)},
)

posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={"job_verified": True},
)
```

Also add to `shared/posthog_events.py`:
```python
JOB_POSTING_VERIFIED = "Job Posting Verified"
```

**Notes:**
- Fires when the 6-digit code auto-verifies (no button click needed after entering code)
- This is a NET NEW event — no existing PostHog event to replace here
- Sets `is_verified` as a job group property so all future events on this job reflect verified status
- Users who click "Maybe later" skip this — their job goes live without verification (`is_verified` stays `false`)

---

### Success: Job Posting Live

#### 7a. Page Viewed (page load)

Fires when the success page loads ("Your job posting is live").

```javascript
posthog.capture('Page Viewed', {
  current_page_context: 'hm_job_creation_wizard_success',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'job',
  job_id: jobId,
});
```

---

#### 7b. Job Posting Published (backend)

Backend publishes the job — it's now live and visible to candidates. This is the final event in the wizard flow.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Backend publishes the job via `POST /api/v1/jobs/flow/{job_id}/verify` → `verify_and_publish()` in `jobflow/router.py` |
| **Source** | Backend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Actual source | Description |
|---|---|---|---|
| `job_id` | UUID | `job.id` | Job identifier |
| `job_title` | string | `job.title` | Job posting title |
| `company_name` | string | `job.company_name` | Company name (can be null) |
| `job_location` | string | `job.location` | Job location (can be null) |
| `job_status` | enum | `job.status` | `"published"` |
| `job_verified` | boolean | `job.is_verified` | Whether the HM verified their email |
| `job_visibility` | string | `job.visibility` | `"private"` or `"public"` |
| `questions_count` | number | queried from DB | Total screening questions |
| `identity_verification_mode` | enum | from `interview.interview_options` | `'require'` or `'off'` |
| `intake_mode` | string | from `IntakeMeeting.mode` | `'ai_copilot'`, `'hm_solo'`, `'manual'` or null |

**Helix codebase change — replace existing `JOB_PUBLISHED` in `jobflow/router.py` lines 432-447:**

Remove the existing `JOB_PUBLISHED` capture and `group_identify` block in `jobflow/router.py` → `verify_and_publish()`, immediately after `job = await service.verify_and_publish(job_id)`:
```python
# REMOVE — find this block after `job = await service.verify_and_publish(job_id)`
posthog_client.capture(
    distinct_id=str(user.user_id),
    event=JOB_PUBLISHED,
    properties={
        PROP_SURFACE: SURFACE_HIRING,
        PROP_ACTING_AS: get_acting_as(user.role),
        PROP_JOB_ID: str(job_id),
        "visibility": job.visibility,
    },
    groups={GROUP_JOB: str(job_id)},
)
posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job_id),
    properties={"job_status": job.status, "job_visibility": job.visibility},
)
```

Replace with:
```python
from sqlalchemy import select
from app.database.models.interview import Interview, InterviewAssessmentQuestion
from app.database.models.intake_meeting import IntakeMeeting

# Query screening questions
interview_result = await service.db.execute(
    select(Interview).where(Interview.job_id == job_id)
)
interview = interview_result.scalar_one_or_none()

questions = []
if interview:
    q_result = await service.db.execute(
        select(InterviewAssessmentQuestion).where(
            InterviewAssessmentQuestion.interview_id == interview.id,
            InterviewAssessmentQuestion.is_deleted == False,
        )
    )
    questions = q_result.scalars().all()

id_verify_mode = (
    (interview.interview_options or {})
    .get("integrity", {})
    .get("identity_verification_mode", "off")
) if interview else "off"

# Query intake meeting mode
intake_result = await service.db.execute(
    select(IntakeMeeting).where(IntakeMeeting.job_id == job_id)
)
intake_meeting = intake_result.scalar_one_or_none()

posthog_client.capture(
    distinct_id=str(user.user_id),
    event="Job Posting Published",
    properties={
        "job_id": str(job.id),
        "job_title": job.title,
        "company_name": job.company_name,
        "job_location": job.location,
        "job_status": job.status,
        "job_verified": job.is_verified,
        "job_visibility": job.visibility,
        "questions_count": len(questions),
        "ai_generated_questions_count": len([q for q in questions if q.source == "ai_generated"]),
        "manual_questions_count": len([q for q in questions if q.source == "manual"]),
        "identity_verification_mode": id_verify_mode,
        "intake_mode": intake_meeting.mode if intake_meeting else None,
    },
    groups={GROUP_JOB: str(job.id)},
)

posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={
        "job_status": job.status,
        "job_verified": job.is_verified,
        "job_visibility": job.visibility,
    },
)
```

Also update `shared/posthog_events.py`:
```python
# Replace:
JOB_PUBLISHED = "Job Published"
# With:
JOB_POSTING_PUBLISHED = "Job Posting Published"
```

**Notes:**
- Removes the existing `JOB_PUBLISHED` event and its `group_identify` block in `jobflow/router.py`
- Captures the full picture: job details, screening config, verification status, intake mode
- `is_verified` tells you whether the user completed email verification or skipped via "Maybe later"
- `intake_mode` tells you how the user went through Understanding the Role (voice/text/skipped)
- This is the END of the wizard — distinct from `Job Posting Draft Created` (step 1)

---

## New Events (updated per Implementation Delta)

Events introduced by this feature. All follow Object-Action, Proper Case. **This table reflects the finalized implementation, incorporating all delta changes.**

| Event | Area | Trigger | Source | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Create Job Button Clicked | Hiring | User clicks "+ Create job" button on job postings page | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | -- | -- |
| Job Post Wizard Started | Hiring | Wizard page mounts with router state isNewWizard=true | Frontend | `start_source`, `current_page_context` | -- | -- |
| Job Post Wizard Job Details Completed | Hiring | User clicks "Next" on Job Details step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Posting Draft Created | Hiring | Server creates job draft via POST /api/v1/core/job | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility` | `job` | `group(job): job_title, job_status, created_by_user_id, created_at` |
| Job Creation Failed | Hiring | Backend exception during POST /api/v1/core/job | Backend | `current_persona`, `error_reason` | -- | -- |
| Job Post Wizard Intake Mode Selected | Hiring | User clicks "Next" (voice/text) or "Skip" on Understanding the Role step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `intake_mode`, `$groups` | `job` | -- |
| Sam Session Started | Hiring | Sam session initializes after user selects voice or text | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `session_id`, `mic_enabled`*, `error_category`*, `error_reason`*, `$groups` | `job` | -- |
| Sam Session Ended | Hiring | User clicks "End Session" or intake auto-completes | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `duration_seconds`, `ended_by` (`user`/`completed`), `session_id`, `$groups` | `job` | -- |
| Job Post Wizard Role Requirements Completed | Hiring | User clicks "Next" on Role Requirements step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Requirement Add Button Clicked | Hiring | User clicks "+ Add" on Role Requirements step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Post Wizard Interview Questions Completed | Hiring | User clicks "Next" on Interview Questions step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `identity_verification_mode`, `$groups` | `job` | -- |
| Question Add Button Clicked | Hiring | User clicks "+ Add" on Interview Questions step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Screening Configuration Saved | Hiring | Backend saves screening config (2 endpoints — see Delta 12) | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | -- |
| Job Verification Code Send Button Clicked | Hiring | User clicks "Send code" on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Post Wizard Verification Completed | Hiring | Email verified successfully on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Post Wizard Verification Skipped | Hiring | User clicks "Maybe later" on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Post Wizard Back Button Clicked | Hiring | User clicks "Back" on any wizard step (2–5) | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | -- |
| Job Posting Verified | Hiring | Backend verifies 6-digit code successfully | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `identity_verification_mode`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `intake_mode` | `job` | `group(job): job_verified` |
| Job Posting Published | Hiring | Backend publishes the job (2 endpoints — see Delta 12) | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): job_status, job_verified, job_visibility` |
| Archive Job Button Clicked | Hiring | User clicks "Archive" in job card overflow menu | Frontend | `action`, `action_value: 'archive_job_menu_item'`, `current_page_context`, `previous_page_context`, `entity_type`, `component: 'job_card_overflow_menu'`, `job_id`, `current_persona` | -- | -- |
| Job Status Changed | Hiring | Job archived or unarchived (core + jobflow endpoints) | Backend | `current_persona`, `job_id`, `from_status`, `to_status` | `job` | `group(job): job_status` |
| Share Button Clicked | Hiring | User clicks share button on job card | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `component`, `context_object_type`, `context_object_id`, `current_persona` | -- | -- |
| Job Shared | Hiring | Backend grants job access successfully | Backend | `current_persona`, `job_id`, `shared_by_user_id`, `share_channel` | `job` | -- |
| Job Share Failed | Hiring | Backend grant access fails | Backend | `current_persona`, `job_id`, `error_reason` | `job` | -- |
| Team Member Invited | Hiring | Backend sends HM invite email successfully | Backend | `current_persona`, `job_id`, `invited_role_label`, `invite_method` | `job` | -- |
| Team Member Invite Failed | Hiring | Backend invite email fails | Backend | `current_persona`, `job_id`, `error_reason` | `job` | -- |

\* `mic_enabled`, `error_category`, `error_reason` — voice mode only, when voiceStatus is present (see Delta 2)

> **Standard property `acting_as`:** Replaced by `current_persona` — sent as explicit event property on all backend events AND available as person property via `$set`. See "Decision" section and Delta 10.
>
> **Standard property `surface`:** Intentionally omitted — `current_page_context` provides more granular surface identification.
>
> **Standard Objects:** `Sam` and `Screening Configuration` are new objects introduced by this plan. To be added to `docs/event-schema.md` Standard Objects table on merge.
>
> **`requirements_count` intentionally omitted:** The old `Job Created` event carried `requirements_count` (AI-generated role requirements from step 3). The new events track `questions_count` / `ai_generated_questions_count` / `manual_questions_count` (screening questions from step 4) instead. Role requirements are intermediate AI artifacts used to generate screening questions — the actionable metric is the final question count, not the requirement count. If needed later, `len(job.key_requirements or [])` can be added to `base_job_setup_properties()`.

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Job Creation | Create Job Button Clicked | Job Post Wizard Started | -- |
| Job Draft Save | Job Post Wizard Job Details Completed | Job Posting Draft Created | Job Creation Failed |
| Email Verification | Job Verification Code Send Button Clicked | Job Posting Verified | -- |
| Job Publish | Job Post Wizard Verification Completed / Job Post Wizard Verification Skipped | Job Posting Published | -- |

> **Note on Job Publish:** The intent is either successful email verification (`Verification Completed`) or skipping it (`Verification Skipped`) — both lead to the backend publishing the job. `Verification Completed` is itself the *outcome* of the email verification flow, but acts as the *intent* for the publish flow. This two-step chain is: Send Code (intent) → Verified (outcome/intent) → Published (outcome).

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Job Post Wizard Completion | Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Post Wizard Intake Mode Selected → Job Post Wizard Role Requirements Completed → Job Post Wizard Interview Questions Completed → Job Post Wizard Verification Completed → Job Posting Published | End-to-end wizard conversion rate |
| Job Post Wizard Abandonment | Job Post Wizard Started → Job Post Wizard Job Details Completed | Step 1 drop-off rate |
| Sam Session Adoption | Job Post Wizard Intake Mode Selected → Sam Session Started → Sam Session Ended | Voice/text session completion rate |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `start_source` | string | `create_job_button` | Entry point that initiated the wizard |
| `step_number` | number | `1`, `2`, `3`, `4`, `5` | Wizard step number |
| `step_name` | enum | `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify` | Wizard step name |
| `intake_mode` | enum | `voice`, `text`, `skipped` | How user chose to interact with Sam on step 2 |
| `input_mode` | enum | `voice`, `text` | Session modality for Sam sessions |
| `ended_by` | enum | `user`, `completed` | Who ended the Sam session |
| `session_id` | string | e.g., `session-abc` | Session identifier for backend correlation |
| `error_reason` | string | `mic_permission_denied`, `device_unavailable`, etc. | Specific error for setup failures |
| `error_category` | string | `timeout`, `hardware`, `unknown` | Error classification |
| `questions_count` | number | e.g., `5` | Total screening questions |
| `ai_generated_questions_count` | number | e.g., `3` | AI-generated screening questions |
| `manual_questions_count` | number | e.g., `2` | Manually added screening questions |
| `identity_verification_mode` | enum | `require`, `off` | Whether ID verification is enabled |
| `entry_context` | enum | `new`, `resume_draft`, `edit_published` | Why the user entered the wizard |
| `company_name` | string | e.g., `Acme Corp` | Company name extracted from JD (can be null) |
| `job_location` | string | e.g., `San Francisco, CA` | Job location extracted from JD (can be null) |
| `job_verified` | boolean | `true`, `false` | Whether hiring manager verified their email |
| `job_title` | string | e.g., `Senior Engineer` | Job posting title |
| `job_status` | enum | `draft`, `published` | Current job status |
| `job_visibility` | enum | `private`, `public` | Job posting visibility |
| `job_id` | UUID | e.g., `abc-123` | Job identifier |

---

## Implementation Delta (2026-05-26, updated 2026-05-28 for v2)

> **What this section is:** During implementation and local PostHog testing on the Helix codebase, several changes were made to the original tracking plan spec above. This section documents every difference so the tracking plan stays in sync with what's actually firing in production.
>
> **Branches:** Deltas 1–19 originated on v1 (`posthog-hiring-manager-job-wizard-event-schema-v1`). Deltas 20–23 are v2-specific changes from cherry-picking onto latest `develop` (`posthog-hiring-manager-job-wizard-event-schema-v2`).
>
> **How to read this:** Each delta entry references the original section number, states what changed, and explains why. The original sections above remain as-is for historical context — this delta is the authoritative override.

---

### Delta 1: Step 2 event renamed

**Original (Section 3b):** `Job Post Wizard Role Understanding Completed`
**Implemented as:** `Job Post Wizard Intake Mode Selected`

**Why:** During testing, "Role Understanding Completed" implied the user finished understanding the role. But the event actually fires when the user selects an intake mode (voice, text, or skip) — a UX decision point, not a comprehension milestone. "Intake Mode Selected" describes the actual user action.

**Properties unchanged** — same properties as Section 3b, including `intake_mode: 'voice' | 'text' | 'skipped'`.

**PostHog call (updated):**

```javascript
captureJobWizardInteraction(
  JOB_POST_WIZARD_INTAKE_MODE_SELECTED,
  JOB_WIZARD_STEPS.roleUnderstanding,
  jobId,
  'next_button',        // or 'skip_button' when skipping
  undefined,
  { intake_mode: selectedMode },  // 'voice', 'text', or 'skipped'
);
```

**Additional change:** When skipping, `action_value` is `'skip_button'` (was `'skip_and_go_to_role_requirements_link'` in the plan). Shortened for consistency with other button action values.

---

### Delta 2: `Sam Voice Session Setup Failed` removed as separate event

**Original (Section 3f):** Standalone event `Sam Voice Session Setup Failed`
**Implemented as:** Voice failure info captured as **properties on `Sam Session Started`** instead

**Why:** During testing, the voice setup flow is: user clicks "Start" → mic check → session connects. If mic fails, the `Sam Session Started` event still fires (it captures the attempt) but includes error properties. This gives a single event to analyze session starts — both successful and failed — rather than requiring analysts to union two separate events.

**How it works now:**

```javascript
captureSamSessionStarted(jobId, 'voice', sessionId, {
  micEnabled: false,
  errorCategory: 'hardware',
  errorReason: 'Permission denied',
});
```

**`Sam Session Started` full properties (updated from Section 3d):**

| Property | Type | Values | Condition | Description |
|---|---|---|---|---|
| `current_page_context` | string | `hm_job_creation_wizard_sam_voice_session` or `hm_job_creation_wizard_sam_text_session` | Always | Page context |
| `previous_page_context` | string | snake_case page identifier | Always | Previous page |
| `entity_type` | string | `job` | Always | Business object |
| `job_id` | UUID | job ID | Always | Job identifier |
| `input_mode` | enum | `voice`, `text` | Always | Session type |
| `session_id` | string | LiveKit session ID | Voice only, when available | Session identifier for debugging |
| `mic_enabled` | boolean | `true`, `false` | Voice only, when voiceStatus present | Whether mic access succeeded |
| `error_category` | string | `timeout`, `hardware`, `unknown` | Voice only, on failure | Error classification |
| `error_reason` | string | e.g., `Permission denied` | Voice only, on failure | Specific error from browser/device |
| `$groups` | object | `{ job: jobId }` | Always | PostHog group association |

**Impact:** Remove `Sam Voice Session Setup Failed` from the New Events table and Catalog Cleanup section.

---

### Delta 3: `Sam Session Ended` — `ended_by` value changed

**Original (Section 3e):** `ended_by: 'user' | 'sam'`
**Implemented as:** `ended_by: 'user' | 'completed'`

**Why:** "sam" implied the AI agent made a decision to end. In reality, the session auto-completes when the intake flow finishes — `'completed'` is more accurate.

**`Sam Session Ended` full properties (updated from Section 3e):**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_creation_wizard_sam_voice_session` or `hm_job_creation_wizard_sam_text_session` | Page context |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `job_id` | UUID | job ID | Job identifier |
| `input_mode` | enum | `voice`, `text` | Session type |
| `duration_seconds` | number | e.g., `180` | Time from start to end |
| `ended_by` | enum | `user`, `completed` | Who ended — user clicked "End Session" or intake auto-completed |
| `session_id` | string | e.g., `session-abc` | Session identifier for backend correlation *(added in v2)* |
| `$groups` | object | `{ job: jobId }` | PostHog group association |

---

### Delta 4: Back button clicks split into separate event

**Original (Sections 5d, 6d):** Back clicks reused step completion events with `action_value: 'back_button'`
**Implemented as:** Separate **`Job Post Wizard Back Button Clicked`** event

**Why:** Reusing the step completion event for back navigation inflated completion counts. A user clicking "Back" on Interview Questions would fire `Job Post Wizard Interview Questions Completed` — misleading in funnel analysis. Splitting it out keeps completion events clean.

**Fires from:** Every wizard step that has a back button (Steps 2–5)

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `back_button` | UI element |
| `current_page_context` | string | Step's page context | Current wizard step |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | `job_creation_wizard_footer_cta` | Footer area |
| `job_id` | UUID | job ID | Job identifier |
| `step_number` | number | `2`, `3`, `4`, `5` | Which step the user is backing from |
| `step_name` | enum | step name | Which step the user is backing from |
| `$groups` | object | `{ job: jobId }` | PostHog group association |

---

### Delta 5: Add button clicks split into separate events

**Original (Sections 4c, 5c):** Add clicks reused step completion events with `action_value: 'add_question_button'`
**Implemented as:** Two separate events:
- **`Requirement Add Button Clicked`** (Role Requirements step)
- **`Question Add Button Clicked`** (Interview Questions step)

**Why:** Same reason as Delta 4 — reusing the completion event for an in-step interaction (adding a question) inflated completion metrics. These are distinct user actions: "I want to add a requirement" vs "I'm done with this step."

**`Requirement Add Button Clicked` properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `add_question_button` | UI element |
| `current_page_context` | string | `hm_job_creation_wizard_role_requirements` | Step 3 page |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | `role_requirements_add_question_cta` | Add button container |
| `job_id` | UUID | job ID | Job identifier |
| `step_number` | number | `3` | Wizard step |
| `step_name` | string | `role_requirements` | Wizard step name |
| `$groups` | object | `{ job: jobId }` | PostHog group association |

**`Question Add Button Clicked` properties:** Same structure, with:
- `current_page_context`: `hm_job_creation_wizard_interview_questions`
- `component`: `interview_questions_add_question_cta`
- `step_number`: `4`
- `step_name`: `interview_questions`

---

### Delta 6: Verification step split into 3 separate events

**Original (Sections 6b, 6c, 6d):** All actions on the Verify page reused `Job Post Wizard Verification Completed`
**Implemented as:** Three separate events:

| User action | Original event | Implemented event |
|---|---|---|
| Clicks "Send code" | `Job Post Wizard Verification Completed` (action_value: send_code_button) | **`Job Verification Code Send Button Clicked`** |
| Email verified successfully | (not a separate event) | **`Job Post Wizard Verification Completed`** |
| Clicks "Maybe later" | `Job Post Wizard Verification Completed` (action_value: maybe_later_link) | **`Job Post Wizard Verification Skipped`** |
| Clicks "Back" | `Job Post Wizard Verification Completed` (action_value: back_button) | **`Job Post Wizard Back Button Clicked`** (see Delta 4) |

**Why:** The original plan used one event for 4 different user actions, differentiated only by `action_value`. During testing, this made funnel analysis confusing — "Verification Completed" should mean the user actually completed verification, not that they clicked "Maybe later" or "Back."

**`Job Verification Code Send Button Clicked` properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `send_code_button` | UI element |
| `current_page_context` | string | `hm_job_creation_wizard_verify` | Step 5 page |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | `job_creation_wizard_footer_cta` | Footer area |
| `job_id` | UUID | job ID | Job identifier |
| `step_number` | number | `5` | Wizard step |
| `step_name` | string | `verify` | Wizard step name |
| `$groups` | object | `{ job: jobId }` | PostHog group association |

**`Job Post Wizard Verification Completed`** now fires ONLY on successful email verification (action_value: `next_button`). Clean signal for the funnel.

**`Job Post Wizard Verification Skipped` properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `maybe_later_link` | UI element |
| `current_page_context` | string | `hm_job_creation_wizard_verify` | Step 5 page |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | `job_creation_wizard_footer_cta` | Footer area |
| `job_id` | UUID | job ID | Job identifier |
| `step_number` | number | `5` | Wizard step |
| `step_name` | string | `verify` | Wizard step name |
| `$groups` | object | `{ job: jobId }` | PostHog group association |

---

### Delta 7: `Create Job Button Clicked` — property values updated

**Original (Section 1):**
- `action_value`: always `create_job_button`
- `component`: `hm_job_postings_header_cta` or `hm_job_postings_empty_state_cta`

**Implemented as:**
- `action_value`: `create_job_posting_button` (recruiter) or `create_job_button` (hiring manager)
- `component`: `job_postings_page_header` (recruiter) or `hm_job_postings_header_cta` (HM) for header; `job_postings_empty_state_cta` (recruiter) or `hm_job_postings_empty_state_cta` (HM) for empty state
- **New property:** `current_persona` added (from `ROLE_TO_PERSONA` mapping)

**Why:** The `JobList.tsx` page is shared between recruiters and hiring managers. During implementation, the button labels and contexts differ by role, so `action_value` and `component` were split to reflect the actual UI text per persona. `current_persona` was added as an explicit event property for filtering without relying on person properties.

**Full property table (replaces Section 1):**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `create_job_posting_button` (recruiter) or `create_job_button` (HM) | Button label in snake_case |
| `current_page_context` | string | `recruiter_ai_job_flows` (recruiter) or `hiring_manager_job_postings` (HM) | Page context |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | See below | UI container |
| `current_persona` | string | `hiring_manager`, `recruiter` | User's active persona |

**Component values by location and persona:**

| Location | Recruiter | Hiring Manager |
|---|---|---|
| Header button | `job_postings_page_header` | `hm_job_postings_header_cta` |
| Empty state button | `job_postings_empty_state_cta` | `hm_job_postings_empty_state_cta` |

---

### Delta 8: `Interview Questions Completed` — `identity_verification_mode` added

**Original (Section 5b):** No `identity_verification_mode` property
**Implemented as:** `identity_verification_mode: 'require' | 'off'` added to `Job Post Wizard Interview Questions Completed`

**Why:** The Interview Questions step includes a "Require ID verification" checkbox. Capturing the state of this toggle at step completion tells us what % of HMs enable ID verification — useful for product decisions without waiting for the backend `Screening Configuration Saved` event.

---

### Delta 9: Backend events — property name changes

**Original (Section 2c, 5e, 6e, 7b):** Used `location` as property name
**Implemented as:** `job_location` in all backend events via `base_job_setup_properties()`

**Why:** `location` is a generic name that could conflict with PostHog's built-in `$geoip_city` / browser location properties. `job_location` is unambiguous.

**Additional backend snapshot properties not in original plan:**

| Property | Type | Source | Description |
|---|---|---|---|
| `job_verified` | boolean | `job.is_verified` | Whether HM email is verified |
| `job_visibility` | string | `job.visibility` | `private` or `public` |

These were added to `base_job_setup_properties()` so every backend event carries the full job state. Not in the original plan because they were deemed redundant with `Job Posting Verified` — but during testing, having them on every event simplified debugging.

---

### Delta 10: `current_persona` added as explicit backend event property

**Original (Section "Decision: acting_as replaced by current_persona"):** Recommended relying on `current_persona` person property (`$set`) — no per-event property needed
**Implemented as:** `current_persona` sent as an **explicit event property** on ALL backend events via `get_current_persona(user.role)`

**Why:** Person properties in PostHog are eventually consistent — there's a small window where the `$set` hasn't propagated. Sending `current_persona` per-event guarantees it's always available on the event itself, with no dependency on person property propagation timing. The person property `$set` is still maintained for user profile queries.

**Applies to:** `Job Posting Draft Created`, `Job Creation Failed`, `Screening Configuration Saved`, `Job Posting Verified`, `Job Posting Published`, `Job Status Changed`, `Job Shared`, `Job Share Failed`, `Team Member Invited`, `Team Member Invite Failed`

---

### Delta 11: `Job Posting Verified` — full snapshot properties

**Original (Section 6e):** Only `job_id`, `job_title`, `is_verified`
**Implemented as:** Full `build_job_setup_analytics_snapshot()` properties

**Why:** During testing, we needed to debug verification issues and having the full job state at verification time (questions count, intake mode, etc.) saved multiple PostHog queries. The marginal cost of extra properties is near zero.

**Updated properties:**

| Property | Type | Description |
|---|---|---|
| `current_persona` | string | User's active persona |
| `job_id` | UUID | Job identifier |
| `job_title` | string | Job posting title |
| `company_name` | string | Company name |
| `job_location` | string | Job location |
| `job_status` | string | Current status |
| `job_verified` | boolean | Verification state |
| `job_visibility` | string | `private` or `public` |
| `identity_verification_mode` | string | `require` or `off` |
| `questions_count` | number | Total screening questions |
| `ai_generated_questions_count` | number | AI-generated questions |
| `manual_questions_count` | number | Manual questions |
| `intake_mode` | string | `ai_copilot`, `hm_solo`, `manual`, or null |

---

### Delta 12: `Screening Configuration Saved` — fires from multiple endpoints

**Original (Section 5e):** Fires from `POST /api/v1/jobs/flow/{job_id}/screening` only
**Implemented as:** Fires from TWO endpoints:
1. `POST /api/v1/jobs/flow/{job_id}/screening` (jobflow/router.py) — original
2. `PATCH /api/v1/core/job/{job_id}` (core/router.py) — conditional

**Why:** The core PATCH endpoint can also transition a job to verify/completed state (e.g., ATS imports, admin actions). The conditional guard ensures it only fires when transitioning TO verify/completed step AND the job wasn't already there — preventing duplicates.

**Condition (core/router.py):**
```python
# Only fires if:
# 1. Not ATS source
# 2. wizard_step or status is being updated to verify/completed/active/published
# 3. Job wasn't already in verify/completed state before this update
```

---

### Delta 13: New events not in original plan

The following events were added during implementation. They're part of the broader hiring manager job management flow but were not in the original wizard-focused tracking plan:

#### Job Creation Failed

| Field | Value |
|---|---|
| **Trigger** | Backend exception during `POST /api/v1/core/job` |
| **Source** | Backend |
| **Properties** | `current_persona`, `error_reason` |
| **Group** | -- (no job_id — creation failed) |
| **Note** | Original plan said "not yet covered" — now implemented. `error_category` intentionally omitted — Helix backend only sends `error_reason` (the raw exception message). If error classification is needed later, it can be added as a follow-up. |

#### Job Status Changed

| Field | Value |
|---|---|
| **Trigger** | Job archived or unarchived |
| **Source** | Backend |
| **Endpoints** | `POST /api/v1/jobs/flow/{job_id}/archive` or `/unarchive` (jobflow) AND `POST /api/v1/core/job/{job_id}/archive` (core) — see Delta 17 |
| **Properties** | `current_persona`, `job_id`, `from_status`, `to_status` |
| **Group** | `job` |
| **Note** | Post-publish lifecycle event — not part of wizard but part of job management |

#### Archive Job Button Clicked

| Field | Value |
|---|---|
| **Trigger** | User clicks "Archive" in the job card overflow menu (intent signal — fires before confirmation dialog) |
| **Source** | Frontend |
| **Properties** | `action: 'click'`, `action_value: 'archive_job_menu_item'`, `current_page_context`, `previous_page_context`, `entity_type: 'job'`, `component: 'job_card_overflow_menu'`, `job_id`, `current_persona` |
| **Group** | -- |
| **Note** | Intent event for `Job Status Changed` (archive). Added in Helix commit `7b6a751d` |

#### Share Button Clicked

| Field | Value |
|---|---|
| **Trigger** | User clicks share button on job card in JobList page |
| **Source** | Frontend |
| **Properties** | `action`, `action_value: 'share_job_button'`, `current_page_context`, `previous_page_context`, `component: 'job_card'`, `context_object_type: 'job'`, `context_object_id`, `current_persona` |
| **Group** | -- |

#### Job Shared / Job Share Failed

| Field | Value |
|---|---|
| **Trigger** | Backend `POST /api/v1/jobs/flow/{job_id}/access` succeeds or fails |
| **Source** | Backend |
| **Properties (success)** | `current_persona`, `job_id`, `shared_by_user_id`, `share_channel: 'other'` |
| **Properties (failure)** | `current_persona`, `job_id`, `error_reason` |
| **Group** | `job` |

#### Team Member Invited / Team Member Invite Failed

| Field | Value |
|---|---|
| **Trigger** | Backend `POST /api/v1/jobs/flow/{job_id}/intake/invite-hm` succeeds or fails |
| **Source** | Backend |
| **Properties (success)** | `current_persona`, `job_id`, `invited_role_label: 'hiring_manager'`, `invite_method: 'email'` |
| **Properties (failure)** | `current_persona`, `job_id`, `error_reason` |
| **Group** | `job` |

---

### Delta 14: `$groups` on all frontend wizard events

**Original:** `$groups: { job: jobId }` mentioned in some sections but not consistently shown
**Implemented as:** ALL frontend wizard events include `$groups: { job: jobId }` when `jobId` is available (every event after Step 1 completion)

**Why:** PostHog group analytics requires `$groups` on every event to associate it with the job entity. The `captureJobWizardStepCompleted` and `captureJobWizardInteraction` helpers automatically inject this.

---

### Delta 15: Page context slashes fixed

**Original:** Not specified
**Implemented as:** The `pathnameToPageContext()` helper was updated to handle leading slashes correctly. Previously, URLs like `/interview/job-details` could produce `_interview_job_details` (leading underscore). Now correctly produces `interview_job_details` (segments joined with `_`, not `/`).

**Helix commit:** `8baba215` — "fix(analytics): replace acting_as with current_persona and fix page context slashes"

---

### Delta 16: `Archive Job Button Clicked` — new frontend intent event

**Original:** Not in plan
**Implemented as:** New event `Archive Job Button Clicked`

**Why:** The archive flow has two steps: (1) user clicks "Archive" in the job card menu, (2) confirmation dialog appears, (3) backend archives the job and fires `Job Status Changed`. The frontend intent event captures step 1 — useful for measuring how often users consider archiving vs actually confirming.

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `archive_job_menu_item` | Menu item clicked |
| `current_page_context` | string | `hiring_manager_job_postings` or `recruiter_ai_job_flows` | Page context |
| `previous_page_context` | string | snake_case page identifier | Previous page |
| `entity_type` | string | `job` | Business object |
| `component` | string | `job_card_overflow_menu` | Overflow menu on job card |
| `job_id` | UUID | job ID | Job being archived |
| `current_persona` | string | `hiring_manager`, `recruiter` | User's active persona |

**Helix commit:** `7b6a751d` — "fix(analytics): add archive job analytics and fix missing core archive event"

---

### Delta 17: `Job Status Changed` — fires from core archive endpoint too

**Original (Delta 13):** `Job Status Changed` fires from jobflow endpoints only (`/api/v1/jobs/flow/{job_id}/archive` and `/unarchive`)
**Implemented as:** Now ALSO fires from `POST /api/v1/core/job/{job_id}/archive` (core/router.py)

**Why:** The frontend uses the core route for archiving, not the legacy jobflow route. Without this fix, archive events from the UI were not being captured.

**Properties (identical to jobflow version):**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_persona` | string | `hiring_manager`, `recruiter` | User's active persona |
| `job_id` | UUID | job ID | Job being archived |
| `from_status` | string | previous status | Status before archive |
| `to_status` | string | `archived` | Always "archived" for archive action |

**Helix commit:** `7b6a751d`

---

### Delta 18: `is_verified` renamed to `job_verified` in backend snapshot

**Original (Section 6e, 7b):** Property name `is_verified`
**Implemented as:** `job_verified` in `base_job_setup_properties()` and all events using the snapshot

**Why:** Consistency with other job-prefixed properties (`job_title`, `job_status`, `job_location`, `job_visibility`). All job entity properties now follow the `job_*` naming pattern.

**Applies to:** `Job Posting Draft Created`, `Screening Configuration Saved`, `Job Posting Verified`, `Job Posting Published`

**Helix commit:** `7e271e18` (initial rename) + `7b6a751d` (missed test assertion fix)

---

### Delta 19: Noisy legacy events removed from Helix codebase

**Not in tracking plan** — these are existing Helix events that were cleaned up during implementation to reduce noise in PostHog.

**Removed events:**

| Event | Why removed |
|---|---|
| `widget_displayed` | A2UI renderer noise — fired on every widget render, not a meaningful user action |
| `widget_interacted` | A2UI renderer noise — too granular, replaced by specific wizard step events |
| `voice_connected` | LiveKit internal state — replaced by `Sam Session Started` |
| `voice_disconnected` | LiveKit internal state — replaced by `Sam Session Ended` |
| `session_started` (HM flow) | Session store noise — duplicate of wizard started |
| `session_ended` (coaching store) | Coaching store cleanup — not relevant to HM flow |
| `intake_completed` | Replaced by `Job Post Wizard Intake Mode Selected` + backend events |
| `Chat WebSocket Connected` | WebSocket lifecycle noise — not a user action |

**Additionally:** `Career Coach Message Sent` now skips `HM_INTERVIEWER` agent type so Sam text sessions in the job wizard don't pollute career coaching metrics.

**Helix commit:** `7e271e18` — "fix(analytics): clean up noisy events and consolidate Sam session tracking"

---

### Delta 20: `Sam Session Ended` — `session_id` property added (v2)

**Original (Section 3e):** No `session_id` property
**Implemented as:** `session_id` added as optional 5th parameter to `captureSamSessionEnded()`

**Why:** Correlates the frontend session-ended event with backend session records. The `session_id` comes from the `initSessionForJob` response and is already available on `Sam Session Started` — adding it to the ended event completes the pair.

**Updated `captureSamSessionEnded` signature:**

```typescript
captureSamSessionEnded(
  jobId: string,
  inputMode: 'voice' | 'text',
  durationSeconds: number | null,
  endedBy: 'user' | 'completed',
  sessionId?: string | null,  // NEW in v2
)
```

**Helix commit:** `c0ef45df` — "fix(analytics): add session_id to Sam Session Ended event"

---

### Delta 21: Verification Skipped — duplicate prevention on auto-skip (v2)

**Original:** `Job Post Wizard Verification Skipped` could fire when the page auto-navigated away (work email auto-skip or recently verified email)
**Implemented as:** `autoSkipping` ref gate prevents the skip event from firing during auto-skip paths

**Why:** On develop, `JobVerify.tsx` gained auto-skip logic: users with a work email or a recently verified alternate email skip verification silently. The `handleSkip` function (triggered by "Maybe later") was also called during auto-skip cleanup, causing a spurious `Verification Skipped` event. The `autoSkipping` ref is set to `true` on all three auto-skip paths (already verified, recently verified email, work email), and `handleSkip` checks it before firing the analytics event.

**Auto-skip conditions (3 paths, none fire analytics events):**
1. `job.is_verified === true` — job already verified → navigate to success
2. `hasRecentlyVerifiedEmail(alternateEmailAddresses)` — user has a recently verified work email → mark complete, navigate to success
3. `!isPersonalEmail(user.email)` — user signed up with a work domain → mark complete, navigate to success

**Helix commit:** `94073165` — "fix(analytics): prevent duplicate Verification Skipped event on auto-skip"

---

### Delta 22: Verify step — work email auto-skip (v2)

**Original (Section 6):** All users see the verify form
**Implemented as:** Users who signed up with a non-personal email (work domain) skip verification automatically

**Why:** Develop introduced `isPersonalEmail()` in `JobVerify.tsx`. If the user's signup email is not from a personal provider (gmail, yahoo, hotmail, outlook), the verify step is skipped — the work email is trusted as job verification. This means fewer `Page Viewed`, `Verification Completed`, and `Verification Skipped` events fire for work-email users.

**Impact on analytics:**
- Work-email users: no verify step events fire (Page Viewed, send code, verification, skip)
- Personal-email users: full verify step flow as documented in sections 6a–6e

---

### Delta 23: Success page `Page Viewed` — fires for all roles (v2)

**Original (Section 7a):** `Page Viewed` for success page was suppressed for recruiters on non-source routes
**Implemented as:** `Page Viewed` for `hm_job_creation_wizard_success` fires unconditionally for all roles

**Why:** Develop redesigned `JobSuccess.tsx` into a single unified layout — the separate recruiter-specific render path (which had the guard) was removed. The `captureJobWizardPageViewed` call now runs for all users who reach the success page.

---

### Delta Summary Table

| # | Change Type | Original | Implemented | Why |
|---|---|---|---|---|
| 1 | Renamed | `Job Post Wizard Role Understanding Completed` | `Job Post Wizard Intake Mode Selected` | Describes actual user action (selecting intake mode) |
| 2 | Removed | `Sam Voice Session Setup Failed` (separate event) | Properties on `Sam Session Started` | Single event for all session start attempts |
| 3 | Value change | `ended_by: 'sam'` | `ended_by: 'completed'` | Session auto-completes, not agent decision |
| 4 | Split out | Back clicks on step completion events | `Job Post Wizard Back Button Clicked` | Avoid inflating completion metrics |
| 5 | Split out | Add clicks on step completion events | `Requirement Add Button Clicked`, `Question Add Button Clicked` | Avoid inflating completion metrics |
| 6 | Split out | All verify actions on one event | 3 events: `Code Send Button Clicked`, `Verification Completed`, `Verification Skipped` | Clean funnel signal |
| 7 | Values updated | `create_job_button` / `hm_*` components | Role-specific `action_value` and `component` | Shared page between recruiter and HM |
| 8 | Property added | No `identity_verification_mode` on step 4 | Added to `Interview Questions Completed` | Capture toggle state at step completion |
| 9 | Property renamed | `location` | `job_location` | Avoid conflict with PostHog built-in geo properties |
| 10 | Property added | No per-event `current_persona` | `current_persona` on all backend events | Guarantee availability without person property propagation delay |
| 11 | Properties expanded | `Job Posting Verified`: 3 properties | Full snapshot (13 properties) | Full job state at verification for debugging |
| 12 | Trigger expanded | `Screening Configuration Saved`: 1 endpoint | 2 endpoints (conditional) | Core PATCH can also transition job state |
| 13 | New events | Not in plan | `Job Creation Failed`, `Job Status Changed`, `Share Button Clicked`, `Job Shared/Failed`, `Team Member Invited/Failed` | Broader job lifecycle coverage |
| 14 | Consistency | `$groups` inconsistent | `$groups` on all frontend events with jobId | Required for PostHog group analytics |
| 15 | Bug fix | Leading slash issue | `pathnameToPageContext()` fixed | Correct page context values |
| 16 | New event | Not in plan | `Archive Job Button Clicked` | Intent signal before archive confirmation |
| 17 | Trigger expanded | `Job Status Changed`: jobflow only | Also fires from core archive endpoint | Frontend uses core route, not legacy jobflow |
| 18 | Property renamed | `is_verified` | `job_verified` | Consistency with `job_*` naming pattern |
| 19 | Cleanup | Legacy noisy events in Helix | 8 events removed, 1 gated | Reduce PostHog noise, replaced by wizard events |
| 20 | Property added (v2) | No `session_id` on `Sam Session Ended` | `session_id` added | Correlate frontend ended event with backend session record |
| 21 | Bug fix (v2) | `Verification Skipped` fired on auto-skip | `autoSkipping` ref gate prevents it | Work-email and recently-verified users shouldn't fire skip event |
| 22 | Behavior change (v2) | All users see verify form | Work-email users auto-skip | Develop added `isPersonalEmail()` trust logic |
| 23 | Behavior change (v2) | Success `Page Viewed` suppressed for some recruiters | Fires for all roles | Develop removed recruiter-specific render path |

---

### Deferred Items (not in Helix PR #555)

The following items were in the original v2 tracking plan but were intentionally excluded from Helix PR #555. They remain unimplemented on `develop`:

| Item | Reason deferred | Original tracking plan reference |
|------|----------------|--------------------------------|
| Login/SignUp Page Viewed dedup guards | PR 555 left Login/SignUp pages untouched due to ongoing Clerk integration churn | Implementation Status section, line "Page Viewed dedup guards on Login, SignUp, RoleSelection pages" |
| `main.tsx` auth session restore noise reduction | Not included in PR 555 scope | Implementation Status section, line "Auth session restore skipped for first-time visitors" |
| `authStore.ts` `is_new_user` on Auth Login Succeeded | Not included in PR 555 scope | Not in event catalog — was a v1 branch addition |
| `livekitClient.ts` structured error forwarding | voiceStore handles error classification directly in catch block; livekitClient modification unnecessary | v2 Implementation Reference, voice failure flow |

> **Note:** RoleSelection.tsx Page Viewed dedup guard (`if (previousPageContext === 'onboarding_role_selection') return`) WAS implemented in PR 555 — only Login/SignUp were excluded.

---

## Catalog Cleanup: Replace Existing Events

The following events in `docs/event-catalog.md` must be **removed** on merge — they are replaced by events in this tracking plan:

### Wizard Events (lines 145-146)

| Remove from catalog | Replaced by | Reason |
|---|---|---|
| `Job Wizard Started` | `Job Post Wizard Started` | Renamed for clarity — "Job Post Wizard" is more explicit than "Job Wizard" |
| `Job Wizard Step Completed` | Per-step events (see below) | Umbrella event replaced by distinct per-step events for easier PostHog filtering |

**Replacement mapping:**

| Old (remove) | New (add) |
|---|---|
| `Job Wizard Started` | `Job Post Wizard Started` |
| `Job Wizard Step Completed` (step_name: job_details) | `Job Post Wizard Job Details Completed` |
| `Job Wizard Step Completed` (step_name: understanding_the_role) | `Job Post Wizard Intake Mode Selected` *(renamed — see Delta 1)* |
| `Job Wizard Step Completed` (step_name: role_requirements) | `Job Post Wizard Role Requirements Completed` |
| `Job Wizard Step Completed` (step_name: interview_questions) | `Job Post Wizard Interview Questions Completed` |
| `Job Wizard Step Completed` (step_name: verify) | `Job Post Wizard Verification Completed` |

> All new event names follow the Object-Action past-tense convention per `docs/event-schema.md`. `step_number` and `step_name` properties are retained on all per-step events for programmatic filtering.

### Hiring Job Events (lines 131-133)

| Remove from catalog | Replaced by | Reason |
|---|---|---|
| `Create Job Button Clicked` (no properties) | `Create Job Button Clicked` (6 properties) | Same event name, enriched with `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` |
| `Job Created` | `Job Posting Draft Created` | Renamed — draft is created on step 1 "Next", not on final publish. Properties updated. |
| `Job Creation Failed` | `Job Creation Failed` (enriched with `current_persona`, `error_reason`) | Same event name, enriched properties — see Delta 13 |
| `Job Published` | `Job Posting Published` | Renamed + enriched with full job snapshot properties |

### Voice Session Events (lines 147-149)

| Remove from catalog | Replaced by | Reason |
|---|---|---|
| `Voice Session Started` | `Sam Session Started` | Now covers both voice AND text sessions via `input_mode` property |
| `Voice Session Ended` | `Sam Session Ended` | Now covers both modalities; carries over `duration_seconds` and `ended_by` (values changed: `sam` → `completed`) |
| `Voice Session Setup Failed` | *(removed — voice failure info captured as properties on `Sam Session Started`; see Delta 2)* | Single event for all session start attempts simplifies analysis |

**Property changes:**

| Old property | New property | Reason |
|---|---|---|
| — (not on Voice Session) | `input_mode` (`voice`/`text`) | Reuses existing catalog property `input_mode`; differentiates voice vs text |
| `ended_by` (`user`/`sam`) | `ended_by` (`user`/`completed`) | `sam` renamed to `completed` — session auto-completes, not agent decision *(see Delta 3)* |
| — (not on Voice Session) | `session_id` | Correlates frontend event with backend session record *(see Delta 20)* |

---

## Decision: `acting_as` replaced by `current_persona`

**CLAUDE.md** requires `acting_as` on all hiring surface events. After reviewing the Helix codebase, `acting_as` is redundant with `current_persona`:

- `acting_as` maps from `UserRole` → `hiring_manager`, `recruiter`, `team_member` (per-event property)
- `current_persona` maps from `UserRole` → `hiring_manager`, `recruiter`, `job_seeker` (person property via `$set`)
- Both derive from the same `user.role` field — they capture the same information
- The job access system (`owner`, `editor`, `viewer`) is a separate permission model unrelated to persona/acting_as
- A hiring manager invited to another HM's job remains `acting_as: hiring_manager` — same as their `current_persona`

**Decision:** Drop `acting_as` from all hiring events. Use `current_persona` (person property) instead — it's automatically available on all events in PostHog queries without passing it per-event.

**Helix codebase update (`shared/posthog_events.py`):** A new `JOB_SEEKER` constant was added to the acting_as/persona constants:

```python
ACTING_HIRING_MANAGER = "hiring_manager"
ACTING_RECRUITER = "recruiter"
ACTING_TEAM_MEMBER = "team_member"
ACTING_JOB_SEEKER = "job_seeker"          # NEW — added for persona mapping
```

`PROFESSIONAL` maps to `job_seeker` for persona context. The new `JOB_SEEKER` constant is an alias for the same value — added for clarity in the codebase.

**On merge, apply to this repo:**
- `CLAUDE.md`: Replace `acting_as required on all hiring surface events` with `Persona context on hiring events is captured via the current_persona person property ($set) — no per-event acting_as needed`
- `scripts/validate-analytics-docs.py`: Remove `acting_as` check from `tp_rule_05` and update `rule_04` docstring
- Validator Rule 4 errors for missing `acting_as` will resolve automatically

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

This section documents all changes that must be applied to `docs/event-catalog.md`, `docs/event-schema.md`, and `docs/dashboards.md` when this tracking plan is merged via `/merge-tracking-plan`. These are precise instructions for the merge operation.

### `docs/event-catalog.md`

**Hiring Persona Events section header — replace:**

| Remove | Add |
|--------|-----|
| `All hiring persona events include job_id. The user's persona context is available via the current_persona person property ($set) — no need to pass it per-event. See Schema for standard event properties.` | `All hiring persona events include job_id. Backend events include current_persona as an explicit event property; frontend events inherit it from the person property ($set). See Schema for standard event properties.` |

**Hiring Persona Events table — replace existing events:**

| Remove | Add | Notes |
|--------|-----|-------|
| `Create Job Button Clicked` (no properties) | `Create Job Button Clicked` with `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | Same event name, enriched properties |
| `Job Created` | `Job Posting Draft Created` (Backend, Success) with `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility` | Renamed — draft created on step 1 "Next" |
| `Job Creation Failed` (old properties) | `Job Creation Failed` with `current_persona`, `error_reason` | Enriched, group changed from `job` to `--` (job_id may not exist when creation fails before draft is persisted) |
| `Job Published` | `Job Posting Published` (Backend, Success) with full snapshot properties | Renamed + enriched |
| `Job Wizard Started` | _(remove entirely — replaced by Job Post Wizard Started below)_ | |
| `Job Wizard Step Completed` | _(remove entirely — replaced by per-step events below)_ | |
| `Voice Session Started` | _(remove entirely — replaced by Sam Session Started below)_ | |
| `Voice Session Ended` | _(remove entirely — replaced by Sam Session Ended below)_ | |
| `Voice Session Setup Failed` | _(remove entirely — folded into Sam Session Started properties)_ | |

> **Note:** For full row details (Area, Type, Trigger, Source, Properties, Group, Property Updates, Status) of replaced events (`Job Posting Draft Created`, `Job Creation Failed`, `Job Posting Published`), refer to the **New Events Summary** table in the "New Events" section above.

**Add new events (insert after `Archive Job Button Clicked`, before `Share Button Clicked`):**

| Event | Area | Type | Trigger | Source | Properties | Group | Status |
|-------|------|------|---------|--------|------------|-------|--------|
| `Job Post Wizard Started` | Hiring | Success | Wizard page mounts with router state isNewWizard=true | Frontend | `start_source`, `current_page_context` | -- | Not Started |
| `Job Post Wizard Job Details Completed` | Hiring | -- | User clicks "Next" on Job Details step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Post Wizard Intake Mode Selected` | Hiring | -- | User clicks "Next" (voice/text) or "Skip" on Understanding the Role step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `intake_mode`, `$groups` | `job` | Not Started |
| `Sam Session Started` | Hiring | -- | Sam session initializes after user selects voice or text | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `session_id`, `mic_enabled`\*, `error_category`\*, `error_reason`\*, `$groups` | `job` | Not Started |
| `Sam Session Ended` | Hiring | -- | User clicks "End Session" or intake auto-completes | Frontend | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_mode`, `duration_seconds`, `ended_by`, `session_id`, `$groups` | `job` | Not Started |
| `Job Post Wizard Role Requirements Completed` | Hiring | -- | User clicks "Next" on Role Requirements step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Requirement Add Button Clicked` | Hiring | -- | User clicks "+ Add" on Role Requirements step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Post Wizard Interview Questions Completed` | Hiring | -- | User clicks "Next" on Interview Questions step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `identity_verification_mode`, `$groups` | `job` | Not Started |
| `Question Add Button Clicked` | Hiring | -- | User clicks "+ Add" on Interview Questions step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Screening Configuration Saved` | Hiring | -- | Backend saves screening config (core + jobflow endpoints) | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | Not Started |
| `Job Verification Code Send Button Clicked` | Hiring | -- | User clicks "Send code" on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Post Wizard Verification Completed` | Hiring | -- | Email verified successfully on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Post Wizard Verification Skipped` | Hiring | -- | User clicks "Maybe later" on Verify step | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Post Wizard Back Button Clicked` | Hiring | -- | User clicks "Back" on any wizard step (2–5) | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `$groups` | `job` | Not Started |
| `Job Posting Verified` | Hiring | Success | Backend verifies 6-digit code successfully | Backend | `current_persona`, `job_id`, `job_title`, `company_name`, `job_location`, `job_status`, `job_verified`, `job_visibility`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | Not Started |
| `Archive Job Button Clicked` | Hiring | Intent | User clicks "Archive" in job card overflow menu | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `current_persona` | -- | Not Started |

\* `mic_enabled`, `error_category`, `error_reason` — voice mode only, when voiceStatus is present

**Update existing events:**

| Event | Change |
|-------|--------|
| `Share Button Clicked` | Update properties to: `action`, `action_value`, `current_page_context`, `previous_page_context`, `component`, `context_object_type`, `context_object_id`, `current_persona`. Note: `share_source` is in catalog but NOT sent by `JobList.tsx` — analytics gap to address separately |
| `Job Status Changed` | Add `current_persona` to properties |
| `Team Member Invited` | Add `current_persona` to properties |
| `Team Member Invite Failed` | Add `current_persona` to properties |
| `Job Shared` | Add `current_persona` to properties |
| `Job Share Failed` | Add `current_persona` to properties |

**Retired Events table — add:**

| Old Event | Replacement | Reason | Date |
|-----------|-------------|--------|------|
| `Job Created` | `Job Posting Draft Created` | Renamed — draft is created on step 1 "Next", not on final publish | May 2026 |
| `Job Published` | `Job Posting Published` | Renamed + enriched with full job snapshot properties | May 2026 |
| `Job Wizard Started` | `Job Post Wizard Started` | Renamed for clarity | May 2026 |
| `Job Wizard Step Completed` | Per-step events (`Job Post Wizard * Completed`) | Umbrella event replaced by distinct per-step events | May 2026 |
| `Voice Session Started` | `Sam Session Started` | Now covers both voice AND text sessions via `input_mode` | May 2026 |
| `Voice Session Ended` | `Sam Session Ended` | Now covers both modalities; `ended_by` changed from `user`/`sam` to `user`/`completed` | May 2026 |
| `Voice Session Setup Failed` | _(removed — properties on `Sam Session Started`)_ | Voice failure info captured as `mic_enabled`, `error_category`, `error_reason` | May 2026 |

**Chat WebSocket Events table — update:**

| Event | Change |
|-------|--------|
| `Chat WebSocket Connected` | Change Status from `Live` to `Removed`. Add note: "Removed as noise reduction in Helix PR #555 — capture call removed from `coachingSocket.ts`" |

**Property Dictionary updates:**

| Property | Change |
|----------|--------|
| `error_category` | Add `hardware` and `unknown` to Allowed Values (new: `network`, `permission`, `validation`, `server`, `timeout`, `hardware`, `unknown`). Sam Session Started voice failures use `timeout`, `hardware`, `unknown` per `voiceStore.ts`. |
| `ended_by` | Change values from `user`, `sam` to `user`, `completed` |
| `action` (user_action) | Add to Used In: `Job Post Wizard Intake Mode Selected`, all split events (Back Button, Add Button, Code Send, Verification Skipped), `Archive Job Button Clicked` |
| `step_number` | Change description from `Wizard step (1–4)` to `Wizard step (1–5)`. Add to Used In: all new wizard step events |
| `step_name` | Add `verify` to Allowed Values (new: `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify`). Add to Used In: all new wizard step events |
| `action_value` | Add to Used In: all new wizard step events, `Archive Job Button Clicked` |
| `current_page_context` | Change description from `"/ hierarchy"` to `"_ hierarchy"` (reflects `pathnameToPageContext()` fix). Add to Used In: Sam Session Started, Sam Session Ended, all wizard events |
| `session_id` | Add new string property: `Backend session identifier for Sam conversations`, Used In: `Sam Session Started`, `Sam Session Ended` |
| `job_location` | Add new string property (replaces `location`): `Job location extracted from JD (can be null)`, Used In: `Job Posting Draft Created`, `Screening Configuration Saved`, `Job Posting Verified`, `Job Posting Published` |

**Boolean Properties — add new entries:**

| Property | Type | Scope | Used In |
|----------|------|-------|---------|
| `job_verified` | boolean | event | `Job Posting Draft Created`, `Screening Configuration Saved`, `Job Posting Verified`, `Job Posting Published` |
| `mic_enabled` | boolean | event | `Sam Session Started` (voice mode only) |

**Enum Properties — remove orphaned row:**

| Remove | Reason |
|--------|--------|
| `visibility` row (Used In: `Job Posting Published`) | Orphaned — old `Job Published` event used `visibility`, but `Job Posting Published` sends `job_visibility` instead. The `job_visibility` group property row already exists. |
| `resume_requirement` row (Used In: `Job Created`) | Orphaned — `Job Created` is retired and replaced by `Job Posting Draft Created`, which does not send `resume_requirement`. |
| `voice_session_completed` row (Used In: `Job Created`) | Orphaned — `Job Created` is retired and replaced by `Job Posting Draft Created`, which does not send `voice_session_completed`. |

**Enum Properties — update `job_visibility` scope:**

| Property | Change |
|----------|--------|
| `job_visibility` | Change scope from `group (job)` to `event, group (job)`. Update Used In to: `Job Posting Draft Created`, `Job Posting Published`, `All events in job group (group property)` |

**Numeric Properties — update Used In:**

| Property | Change |
|----------|--------|
| `ai_generated_questions_count` | Add `Job Posting Verified` to Used In |
| `manual_questions_count` | Add `Job Posting Verified` to Used In |

**Enum Properties — update Used In:**

| Property | Change |
|----------|--------|
| `intake_mode` | Add `Job Posting Verified` to Used In |
| `identity_verification_mode` | Add `Job Posting Verified` to Used In |

**String Properties — update Used In:**

| Property | Change |
|----------|--------|
| `company_name` | Add `Job Posting Verified` to Used In |

### `docs/event-schema.md`

**Code sample fix — `identifyUser()` (lines 157 and 300):**

Both `posthog.identify()` code samples contain a broken placeholder `first_surface: ...`. `first_surface` was a draft property name that was replaced by `first_persona` before launch. Replace both occurrences:

| Remove | Add |
|--------|-----|
| `{ account_created_at: user.createdAt, first_surface: ... }  // $set_once` | `{ account_created_at: user.createdAt }  // $set_once` |

> Note: `first_persona` is set by `Account Created`, not by `identifyUser()`. The `$set_once` object in `identifyUser()` only needs `account_created_at`. Other `$set_once` properties (`entry_point`, `first_referrer`, `first_landing_url`) are set earlier on `Login Started`.

**Property naming convention — update (line 49):**

| Remove | Add |
|--------|-----|
| `For current_page_context and previous_page_context values, use underscores for hierarchy:` | `For current_page_context and previous_page_context values, use underscores (_) for hierarchy, not slashes (/):` |

**Standard Event Properties note — replace:**

| Remove | Add |
|--------|-----|
| `> **Note:** The user's active persona is tracked via the current_persona person property ($set), which is automatically available on all events. No need to pass persona per-event.` | `> **Note:** The user's active persona is tracked via the current_persona person property ($set). Backend events also include current_persona as an explicit event property to guarantee availability without $set propagation delay.` |

**Standard Objects table — replace:**

| Remove | Add |
|--------|-----|
| `Job Wizard` row | `Job Post Wizard` — events: Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked |
| `Job Wizard Step` row | _(remove — merged into Job Post Wizard)_ |
| `Voice Session` row | _(remove — replaced by Sam)_ |
| `Sam Voice Session` row (if exists) | _(remove — folded into Sam Session Started)_ |

**Add:**

| Object | Entity | Example Events |
|--------|--------|---------------|
| `Job Posting` | Job posting lifecycle (draft, verified, published) | Job Posting Draft Created, Job Posting Verified, Job Posting Published |
| `Sam` | AI hiring partner (Sam) conversation | Sam Session Started, Sam Session Ended |
| `Job Verification Code` | Email verification code | Job Verification Code Send Button Clicked |
| `Screening Configuration` | Job screening setup (questions, ID verification) | Screening Configuration Saved |

**Consolidate existing:**

| Object | Update |
|--------|--------|
| `Requirement` | Merge events: `Requirement Add Button Clicked, Requirement Modified` |
| `Question` | Merge events: `Question Add Button Clicked, Question Modified` |
| `Job` | Update example events: `Job Posting Draft Created, Job Shared` (was `Job Created, Job Shared`) |

**Intent → Outcome table — replace:**

| Remove | Add |
|--------|-----|
| `Creating a job \| Create Job Button Clicked \| Job Created \| Job Creation Failed` | `Creating a job (wizard start) \| Create Job Button Clicked \| Job Post Wizard Started \| --` |
| | `Creating a job (draft save) \| Job Post Wizard Job Details Completed \| Job Posting Draft Created \| Job Creation Failed` |
| | `Email verification \| Job Verification Code Send Button Clicked \| Job Posting Verified \| --` |
| | `Publishing a job \| Job Post Wizard Verification Completed / Job Post Wizard Verification Skipped \| Job Posting Published \| --` |

**Intent vs Outcome section — add note after the table:**

> **Exception:** `Sam Session Started` carries optional failure properties (`mic_enabled`, `error_category`, `error_reason`) for voice setup failures instead of using a separate failure event. This allows analysts to build a single funnel (`Sam Session Started` → `Sam Session Ended`) and filter by `mic_enabled = false` for failures, rather than unioning two separate events.

### `docs/dashboards.md`

**Growth Dashboard — update:**

| Remove | Add |
|--------|-----|
| `Onboarding-to-job conversion: Account Created → Persona Selected → Job Wizard Started → Job Wizard Step Completed (step 1) → Job Created` | `Onboarding-to-job conversion: Account Created → Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Posting Draft Created → Job Posting Published` |

**Hiring Dashboard — replace wizard/voice metrics:**

| Remove | Add |
|--------|-----|
| `Job wizard completion funnel — ... (Job Wizard Started → Job Wizard Step Completed step 1 → 2 → 3 → 4 → Job Created)` | `Job post wizard completion funnel — step-by-step drop-off rates (Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Post Wizard Intake Mode Selected → Job Post Wizard Role Requirements Completed → Job Post Wizard Interview Questions Completed → Job Post Wizard Verification Completed → Job Posting Published)` |
| | `Job post wizard abandonment — Step 1 drop-off rate (Job Post Wizard Started → Job Post Wizard Job Details Completed)` |
| | `Sam session adoption — voice/text session completion rate (Job Post Wizard Intake Mode Selected → Sam Session Started → Sam Session Ended), broken down by input_mode` |
| | `Sam voice setup failure rate — Sam Session Started where mic_enabled = false, error_category distribution (timeout / hardware / unknown)` |
| `Voice session stats — completion rate (Voice Session Started → Voice Session Ended), avg duration_seconds` | `Voice session stats — completion rate (Sam Session Started → Sam Session Ended), avg duration_seconds` |
| `AI content modification rate — ... counts vs Job Created` | `AI content modification rate — ... counts vs Job Posting Published` |

**Platform Health Dashboard — replace/add:**

| Remove | Add |
|--------|-----|
| `Job creation \| Create Job Button Clicked \| Job Created \| Job Creation Failed` | `Creating a job (wizard start) \| Create Job Button Clicked \| Job Post Wizard Started \| --` |
| | `Creating a job (draft save) \| Job Post Wizard Job Details Completed \| Job Posting Draft Created \| Job Creation Failed` |
| | `Email verification \| Job Verification Code Send Button Clicked \| Job Posting Verified \| --` |
| | `Publishing a job \| Job Post Wizard Verification Completed / Job Post Wizard Verification Skipped \| Job Posting Published \| --` |

### Known analytics gaps (to address separately)

| Gap | Description | Severity |
|-----|-------------|----------|
| `share_source` missing from `Share Button Clicked` | Catalog requires `share_source` (`success_screen`, `dashboard`, `overflow_menu`) but `JobList.tsx` does not send it. Cannot distinguish share origin. | Low — `component` partially covers this |
| `mode_switched` lowercase event | Pre-existing event in `coachingStore.ts` — fires `mode_switched` (lowercase) instead of Proper Case. Not introduced by this plan. | Low — pre-existing, not in catalog |
| `role` person property superseded by `current_persona` | `identifyUser()` sends both `role` (raw DB enum: `HIRING_MANAGER`, `PROFESSIONAL`) and `current_persona` (analytics-friendly: `hiring_manager`, `job_seeker`). `current_persona` is strictly better — snake_case, updates on persona switch and account creation (not just login), and uses user-facing labels. `role` should be removed from `identifyUser()` in a future Helix PR. Existing PostHog cohorts filtering on `role` will need migration to `current_persona`. | Low — pre-existing, no data loss |

