# Tracking Plan: Hiring Manager Job Post Wizard

**Product:** Helix (SeekOut.ai)
**Feature:** Job post wizard flow (hiring manager persona)
**Date:** 2026-05-11
**Related PRD:** —

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

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
  │    → fires: Job Post Wizard Role Understanding Completed
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
- Each wizard step has its own event name (`Job Post Wizard Job Details Completed`, `Role Understanding Completed`, `Role Requirements Completed`, `Interview Questions Completed`, `Verification Completed`) — `step_number` and `step_name` properties are also included for programmatic filtering
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
| `location` | string | `job.location` | Location extracted from JD (can be null) |
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
        "location": job.location,
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
  │    → Job Post Wizard Role Understanding Completed (intake_mode: 'voice')
  │    → Page Viewed (hm_job_creation_wizard_sam_voice_session)
  │    → Sam Session Started (input_mode: 'voice')
  │    → ... user talks with Sam ...
  │    → Sam Session Ended (input_mode: 'voice', duration_seconds, ended_by)
  │
  ├─ Path B: User selects Text + clicks Next
  │    → Job Post Wizard Role Understanding Completed (intake_mode: 'text')
  │    → Page Viewed (hm_job_creation_wizard_sam_text_session)
  │    → Sam Session Started (input_mode: 'text')
  │    → ... user chats with Sam ...
  │    → Sam Session Ended (input_mode: 'text', duration_seconds, ended_by)
  │
  └─ Path C: User clicks "Skip and go to role requirements"
       → Job Post Wizard Role Understanding Completed (intake_mode: 'skipped')
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

#### 3b. Job Post Wizard Role Understanding Completed (user action — mode selection)

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
| `action_value` | string | `next_button` or `skip_and_go_to_role_requirements_link` | Which button was clicked |
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
posthog.capture('Job Post Wizard Role Understanding Completed', {
  action: 'click',
  action_value: 'next_button',  // or 'skip_and_go_to_role_requirements_link'
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
| `ended_by` | enum | `user`, `sam` | Who ended the session — carried over from `Voice Session Ended` |

**PostHog call:**

```javascript
posthog.capture('Sam Session Ended', {
  job_id: jobId,
  input_mode: 'voice',  // or 'text'
  duration_seconds: sessionDuration,
  ended_by: 'user',  // or 'sam'
});
```

**Notes:**
- Fires on the confirmation modal "End Session" button, NOT on the first "End Session" / "End chat" click
- Covers both voice and text sessions under one event name — `input_mode` differentiates
- `ended_by` tracks whether the user ended the session or Sam auto-ended it
- After this fires, user moves to the Role Requirements page
- Replaces `Voice Session Ended` from `docs/event-catalog.md` — see Catalog Cleanup section

---

#### 3f. Sam Voice Session Setup Failed

Voice session fails to initialize due to mic permission denied or device unavailable. Replaces `Voice Session Setup Failed` from the event catalog.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Failure |
| **Trigger** | Mic permission denied or device unavailable when starting voice session |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `job_id` | UUID | job ID | Job identifier |
| `error_reason` | string | e.g., `mic_permission_denied`, `device_unavailable` | Specific error |
| `error_category` | string | e.g., `permissions`, `hardware` | Error category |

**PostHog call:**

```javascript
capture('Sam Voice Session Setup Failed', {
  job_id: jobId,
  error_reason: 'Permission denied',  // dynamic — from browser/device
  error_category: 'hardware',         // determined by which code path caught the error
});
```

**Notes:**
- Voice-only event — text sessions have no hardware setup that can fail
- Replaces `Voice Session Setup Failed` from `docs/event-catalog.md` — see Catalog Cleanup section
- `error_reason` is never hardcoded — it comes from the browser/device error message (e.g., `"Permission denied"`, `"Requested device not found"`, `"Connection timed out"`)
- `error_category` is determined by where in the code the error was caught: `hardware` (mic/device), `timeout`, or `connection`

**Helix codebase changes:**

There is NO existing PostHog event for voice setup failures. The error handling infrastructure exists but isn't wired to PostHog. The app already tracks `voice_connected` and `voice_disconnected` — this adds the missing failure counterpart.

**Architecture note:** LiveKitClient (the audio specialist) detects mic/device errors but has no knowledge of `job_id` or PostHog. voiceStore (the coordinator) has `job_id` and PostHog access. So the approach is: LiveKitClient passes the error details up to voiceStore via the existing `onConnectionChange` callback, and voiceStore fires the PostHog event.

**Change 1: Add event constant**

**Edit** `frontend/src/lib/posthogEvents.ts` — add:

```typescript
export const SAM_VOICE_SESSION_SETUP_FAILED = 'Sam Voice Session Setup Failed';
```

**Change 2: Expand LiveKitClient callback to include error details**

**Edit** `frontend/src/lib/livekitClient.ts` — in the `RoomEvent.MediaDevicesError` handler (inside the `join()` method, where the room event listeners are set up), pass the error reason and category through the existing `onConnectionChange` callback:

```typescript
// BEFORE (current code):
room.on(RoomEvent.MediaDevicesError, () => {
  logger.error(TAG, 'Media devices error');
  this.handlers?.onConnectionChange('error');
});

// AFTER:
room.on(RoomEvent.MediaDevicesError, (error) => {
  logger.error(TAG, 'Media devices error', error);
  this.handlers?.onConnectionChange('error', {
    reason: error?.message || 'device_unavailable',
    category: 'hardware',
  });
});
```

> LiveKitClient doesn't fire PostHog itself — it just passes the error details to voiceStore via the callback. The `error` object comes from the browser (e.g., `"Permission denied"` when mic is blocked). `category: 'hardware'` is not hardcoded guesswork — this handler ONLY fires for mic/device issues, so the category is always `hardware`.

**Change 3: voiceStore fires PostHog event for all voice failures**

**Edit** `frontend/src/stores/voiceStore.ts` — two changes in this file:

**(a)** Update the `onConnectionChange` callback (inside the `startVoice()` method, where `LiveKitClient` handlers are configured) to handle error details from LiveKitClient:

```typescript
// BEFORE (current code):
onConnectionChange: (connState) => {
  set({ connectionState: connState });
},

// AFTER:
onConnectionChange: (connState, errorInfo) => {
  set({ connectionState: connState });
  if (connState === 'error' && errorInfo) {
    capture(SAM_VOICE_SESSION_SETUP_FAILED, {
      job_id: jobId,
      error_reason: errorInfo.reason,
      error_category: errorInfo.category,
    });
  }
},
```

> This handles mic/device errors that LiveKitClient detects after the connection is established.

**(b)** In the `startVoice()` catch block (the `} catch (e) {` at the end of the method, after the `createdClient.join()` call), add PostHog capture after the existing error handling:

```typescript
// EXISTING code — no changes to lines 192-212:
} catch (e) {
  if (backendStarted) {
    try { await api.stopVoice(sessionId); } catch { }
  }
  client?.destroy();
  client = null;

  const msg = e instanceof Error
    ? e.message.includes('timeout')
      ? 'Connection timed out. Please try again.'
      : e.message
    : 'Voice connection failed. Please try again.';

  set({ connectionState: 'error', error: msg });
  logger.error(TAG, 'Voice connection failed', e);

  // ADD — track voice setup failure in PostHog
  capture(SAM_VOICE_SESSION_SETUP_FAILED, {
    job_id: jobId,
    error_reason: e instanceof Error ? e.message : 'unknown',
    error_category: e instanceof Error && e.message.includes('timeout')
      ? 'timeout'
      : 'connection',
  });
}
```

> This catch block handles connection-level failures (backend call failures, room join failures, timeouts). The `error_reason` is the raw error message from the system; `error_category` is determined by which type of failure occurred.

**Change 4 (optional): Add backend constant**

**Edit** `backend/app/shared/posthog_events.py` — add:

```python
SAM_VOICE_SESSION_SETUP_FAILED = "Sam Voice Session Setup Failed"
```

> Optional — this event is frontend-only, but adding the constant keeps the backend event registry complete.

**How it all flows together:**

```
Scenario A: Mic permission denied
  Browser → LiveKitClient (MediaDevicesError handler)
    → passes { reason: "Permission denied", category: "hardware" } to voiceStore
    → voiceStore fires PostHog event with job_id + error details

Scenario B: Network timeout during connection
  Browser → voiceStore (startVoice catch block)
    → voiceStore fires PostHog event directly with job_id + error details

Scenario C: Backend call fails
  Backend → voiceStore (startVoice catch block)
    → voiceStore fires PostHog event directly with job_id + error details
```

All three scenarios are captured. All PostHog events fire from voiceStore (the coordinator that has `job_id`). LiveKitClient never calls PostHog directly.

**Files to modify:**

| File | Change |
|---|---|
| `frontend/src/lib/posthogEvents.ts` | Add constant |
| `frontend/src/lib/livekitClient.ts` (`RoomEvent.MediaDevicesError` handler in `join()`) | Pass error details through `onConnectionChange` callback |
| `frontend/src/stores/voiceStore.ts` (`onConnectionChange` callback + `startVoice()` catch block) | Receive error details and fire PostHog event |
| `backend/app/shared/posthog_events.py` | Add constant (optional) |

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
| `location` | string | `job.location` | Job location |
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
        "location": job.location,
        "questions_count": len(questions),
        "ai_generated_questions_count": ai_count,
        "manual_questions_count": manual_count,
        "identity_verification_mode": id_verify_mode,
    },
    groups={GROUP_JOB: str(job.id)},
)

posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={
        "questions_count": len(questions),
        "identity_verification_mode": id_verify_mode,
    },
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
| `is_verified` | boolean | `true` | Email verified — always true on this event |

**Helix codebase change — add to `core/router.py` → `confirm_job_verification()` (POST /api/v1/core/job/{job_id}/verify/confirm):**

```python
# Add after successful verification (after job.is_verified = True is set)
posthog_client.capture(
    distinct_id=str(user.id),
    event="Job Posting Verified",
    properties={
        "job_id": str(job.id),
        "job_title": job.title,
        "is_verified": True,
    },
    groups={GROUP_JOB: str(job.id)},
)

posthog_client.group_identify(
    group_type=GROUP_JOB,
    group_key=str(job.id),
    properties={"is_verified": True},
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
| `location` | string | `job.location` | Job location (can be null) |
| `job_status` | enum | `job.status` | `"published"` |
| `is_verified` | boolean | `job.is_verified` | Whether the HM verified their email |
| `visibility` | string | `job.visibility` | `"private"` or `"public"` |
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
        "location": job.location,
        "job_status": job.status,
        "is_verified": job.is_verified,
        "visibility": job.visibility,
        "questions_count": len(questions),
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
        "is_verified": job.is_verified,
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

## New Events

Events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|
| Create Job Button Clicked | Hiring | User clicks "+ Create job" button on HM job postings page | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- |
| Job Post Wizard Started | Hiring | Wizard page mounts with router state isNewWizard=true | `start_source`, `current_page_context` | -- | -- |
| Job Post Wizard Job Details Completed | Hiring | User clicks "Next →" on Job Details step | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | -- | -- |
| Job Posting Draft Created | Hiring | Server creates job draft via POST /api/v1/core/job | `job_id`, `job_title`, `company_name`, `location`, `job_status` | `job` | `group(job): job_title, job_status, created_by_user_id, created_at` |
| Job Post Wizard Role Understanding Completed | Hiring | User clicks "Next →" or "Skip" on Understanding the Role step | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name`, `intake_mode` | `job` | -- |
| Sam Session Started | Hiring | Sam session initializes after user selects voice or text | `job_id`, `input_mode` | `job` | -- |
| Sam Session Ended | Hiring | User clicks "End Session" in confirmation modal or Sam auto-ends | `job_id`, `input_mode`, `duration_seconds`, `ended_by` | `job` | -- |
| Sam Voice Session Setup Failed | Hiring | Mic permission denied or device unavailable | `job_id`, `error_reason`, `error_category` | `job` | -- |
| Job Post Wizard Role Requirements Completed | Hiring | User clicks "Next →" or "+ Add question" on Role Requirements step | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- |
| Job Post Wizard Interview Questions Completed | Hiring | User clicks "Next →", "+ Add question", or "← Back" on Interview Questions step | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- |
| Screening Configuration Saved | Hiring | Backend saves screening config via POST /api/v1/jobs/flow/{job_id}/screening | `job_id`, `job_title`, `company_name`, `location`, `questions_count`, `ai_generated_questions_count`, `manual_questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): questions_count, identity_verification_mode` |
| Job Post Wizard Verification Completed | Hiring | User clicks "Send code", "Maybe later", or "← Back" on Verify step | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `job_id`, `step_number`, `step_name` | `job` | -- |
| Job Posting Verified | Hiring | Backend verifies 6-digit code successfully | `job_id`, `job_title`, `is_verified` | `job` | `group(job): is_verified` |
| Job Posting Published | Hiring | Backend publishes the job via POST /api/v1/jobs/flow/{job_id}/verify | `job_id`, `job_title`, `company_name`, `location`, `job_status`, `is_verified`, `visibility`, `questions_count`, `identity_verification_mode`, `intake_mode` | `job` | `group(job): job_status, is_verified, job_visibility` |

> **Note:** `Create Job Button Clicked` exists in the catalog but with no properties (`--`). This plan replaces it with 6 enriched properties. On merge, update the catalog entry to match.
>
> **Standard property `acting_as`:** Intentionally omitted from all events — replaced by `current_persona` person property. See "Decision: `acting_as` replaced by `current_persona`" section below. Validator TP5 errors for `acting_as` will resolve when the validator is updated on merge.
>
> **Standard property `surface`:** Intentionally omitted — the existing `current_page_context` property provides more granular surface identification. Validator TP5 errors for `surface` are expected.
>
> **Standard Objects:** `Sam` and `Screening Configuration` are new objects introduced by this plan. To be added to `docs/event-schema.md` Standard Objects table on merge.

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Job Creation | Create Job Button Clicked | Job Post Wizard Started | -- |
| Job Draft Save | Job Post Wizard Job Details Completed | Job Posting Draft Created | -- |
| Job Publish | Job Post Wizard Verification Completed | Job Posting Published | -- |
| Email Verification | Job Post Wizard Verification Completed | Job Posting Verified | -- |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Job Post Wizard Completion | Job Post Wizard Started → Job Post Wizard Job Details Completed → Job Post Wizard Role Understanding Completed → Job Post Wizard Role Requirements Completed → Job Post Wizard Interview Questions Completed → Job Post Wizard Verification Completed → Job Posting Published | End-to-end wizard conversion rate |
| Job Post Wizard Abandonment | Job Post Wizard Started → Job Post Wizard Job Details Completed | Step 1 drop-off rate |
| Sam Session Adoption | Job Post Wizard Role Understanding Completed → Sam Session Started → Sam Session Ended | Voice/text session completion rate |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `start_source` | string | `create_job_button` | Entry point that initiated the wizard |
| `step_number` | number | `1`, `2`, `3`, `4`, `5` | Wizard step number |
| `step_name` | enum | `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify` | Wizard step name |
| `intake_mode` | enum | `voice`, `text`, `skipped` | How user chose to interact with Sam on step 2 |
| `input_mode` | enum | `voice`, `text` | Session modality for Sam sessions |
| `ended_by` | enum | `user`, `sam` | Who ended the Sam session |
| `error_reason` | string | `mic_permission_denied`, `device_unavailable`, etc. | Specific error for setup failures |
| `error_category` | string | `permissions`, `hardware`, `timeout`, `connection` | Error classification |
| `questions_count` | number | e.g., `5` | Total screening questions |
| `ai_generated_questions_count` | number | e.g., `3` | AI-generated screening questions |
| `manual_questions_count` | number | e.g., `2` | Manually added screening questions |
| `identity_verification_mode` | enum | `require`, `off` | Whether ID verification is enabled |
| `entry_context` | enum | `new`, `resume_draft`, `edit_published` | Why the user entered the wizard |
| `company_name` | string | e.g., `Acme Corp` | Company name extracted from JD (can be null) |
| `location` | string | e.g., `San Francisco, CA` | Job location extracted from JD (can be null) |
| `is_verified` | boolean | `true`, `false` | Whether hiring manager verified their email |
| `job_title` | string | e.g., `Senior Engineer` | Job posting title |
| `job_status` | enum | `draft`, `published` | Current job status |
| `visibility` | enum | `private`, `public` | Job posting visibility |
| `job_id` | UUID | e.g., `abc-123` | Job identifier |

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
| `Job Wizard Step Completed` (step_name: understanding_the_role) | `Job Post Wizard Role Understanding Completed` |
| `Job Wizard Step Completed` (step_name: role_requirements) | `Job Post Wizard Role Requirements Completed` |
| `Job Wizard Step Completed` (step_name: interview_questions) | `Job Post Wizard Interview Questions Completed` |
| `Job Wizard Step Completed` (step_name: verify) | `Job Post Wizard Verification Completed` |

> All new event names follow the Object-Action past-tense convention per `docs/event-schema.md`. `step_number` and `step_name` properties are retained on all per-step events for programmatic filtering.

### Hiring Job Events (lines 131-133)

| Remove from catalog | Replaced by | Reason |
|---|---|---|
| `Create Job Button Clicked` (no properties) | `Create Job Button Clicked` (6 properties) | Same event name, enriched with `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` |
| `Job Created` | `Job Posting Draft Created` | Renamed — draft is created on step 1 "Next", not on final publish. Properties updated. |
| `Job Creation Failed` | -- (not yet covered) | Existing failure event kept until a replacement is defined |
| `Job Published` | `Job Posting Published` | Renamed + enriched with full job snapshot properties |

### Voice Session Events (lines 147-149)

| Remove from catalog | Replaced by | Reason |
|---|---|---|
| `Voice Session Started` | `Sam Session Started` | Now covers both voice AND text sessions via `input_mode` property |
| `Voice Session Ended` | `Sam Session Ended` | Now covers both modalities; carries over `duration_seconds` and `ended_by` |
| `Voice Session Setup Failed` | `Sam Voice Session Setup Failed` | Renamed to Sam namespace; voice-only (text has no hardware setup) |

**Property changes:**

| Old property | New property | Reason |
|---|---|---|
| — (not on Voice Session) | `input_mode` (`voice`/`text`) | Reuses existing catalog property `input_mode`; differentiates voice vs text |
| `ended_by` (`user`/`sam`) | `ended_by` (`user`/`sam`) | Carried over unchanged from `Voice Session Ended` |

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

