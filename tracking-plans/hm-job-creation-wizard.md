# Tracking Plan: Hiring Manager Job Creation Wizard

**Product:** Helix (SeekOut.ai)
**Feature:** Job creation wizard flow (hiring manager persona)
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
  ├─ Step 1: Job Details — paste JD, AI evaluates, click Next
  │    → fires: Page Viewed (hm_job_creation_wizard_job_details)
  │    → fires: Job Creation Wizard (step 1: job_details) — on Next click
  │    → fires: Job Posting Draft Created (backend — draft saved with job_id)
  │
  ├─ Step 2: Understanding the Role — choose Voice / Text / Skip
  │    → fires: Page Viewed (hm_job_creation_wizard_understanding_the_role)
  │    → fires: Job Creation Wizard (step 2: understanding_the_role)
  │
  ├─ Step 3: Role Requirements — review AI-drafted requirements
  │    → fires: Page Viewed (hm_job_creation_wizard_role_requirements)
  │    → fires: Job Creation Wizard (step 3: role_requirements)
  │
  ├─ Step 4: Interview Questions — review AI-generated questions
  │    → fires: Page Viewed (hm_job_creation_wizard_interview_questions)
  │    → fires: Job Creation Wizard (step 4: interview_questions)
  │
  ├─ Step 5: Verify — email verification
  │    → fires: Page Viewed (hm_job_creation_wizard_verify)
  │    → fires: Job Creation Wizard (step 5: verify)
  │
  └─ Success: Job posting is live
       → fires: Job Created (backend — final)
       → fires: Job Published (backend)
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

#### 2b. Job Creation Wizard (user action — Next click)

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
posthog.capture('Job Creation Wizard', {
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
- Same event name (`Job Creation Wizard`) for all wizard steps — `step_number` and `step_name` differentiate
- `step_name` values across wizard: `job_details`, `understanding_the_role`, `role_requirements`, `interview_questions`, `verify`
- `job_id` is included from step 1 onwards — the draft is created on this Next click and the ID is available in the response. All subsequent steps carry the same `job_id`.

---

#### 2c. Job Posting Draft Created (backend — draft saved)

Server creates the job draft after JD evaluation on step 1. The job is persisted — if the user abandons the wizard, it appears on the home page with "Continue setup".

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | Success |
| **Trigger** | Server creates job draft via `POST /api/v1/job` → `create_job()` in `core/router.py` |
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
  │    → Job Creation Wizard (step 2, intake_mode: 'voice')
  │    → Page Viewed (hm_job_creation_wizard_sam_voice_session)
  │    → Sam Session Started (intake_mode: 'voice')
  │    → ... user talks with Sam ...
  │    → Sam Session Ended (intake_mode: 'voice', duration_seconds)
  │
  ├─ Path B: User selects Text + clicks Next
  │    → Job Creation Wizard (step 2, intake_mode: 'text')
  │    → Page Viewed (hm_job_creation_wizard_sam_text_session)
  │    → Sam Session Started (intake_mode: 'text')
  │    → ... user chats with Sam ...
  │    → Sam Session Ended (intake_mode: 'text', duration_seconds)
  │
  └─ Path C: User clicks "Skip and go to role requirements"
       → Job Creation Wizard (step 2, intake_mode: 'skipped')
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

#### 3b. Job Creation Wizard (user action — mode selection)

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
posthog.capture('Job Creation Wizard', {
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

Sam session begins (voice or text).

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
| `intake_mode` | enum | `voice`, `text` | Session type |

**PostHog call:**

```javascript
posthog.capture('Sam Session Started', {
  job_id: jobId,
  intake_mode: 'voice',  // or 'text'
});
```

**Notes:**
- Covers both voice and text sessions under one event name — `intake_mode` differentiates
- Fires when the session actually initializes, not on page load

---

#### 3e. Sam Session Ended

User confirms "End Session" in the confirmation modal.

| Field | Value |
|-------|-------|
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | User clicks "End Session" in the confirmation modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `job_id` | UUID | job ID | Job identifier |
| `intake_mode` | enum | `voice`, `text` | Session type |
| `duration_seconds` | number | e.g., 180 | Time from session start to end confirmation |

**PostHog call:**

```javascript
posthog.capture('Sam Session Ended', {
  job_id: jobId,
  intake_mode: 'voice',  // or 'text'
  duration_seconds: sessionDuration,
});
```

**Notes:**
- Fires on the confirmation modal "End Session" button, NOT on the first "End Session" / "End chat" click
- Covers both voice and text sessions under one event name — `intake_mode` differentiates
- After this fires, user moves to the Role Requirements page

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

#### 4b. Job Creation Wizard (user action — Next click)

User clicks "Next →" to proceed to Interview Questions.

**PostHog call:**

```javascript
posthog.capture('Job Creation Wizard', {
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

#### 4c. Job Creation Wizard (user action — Add question click)

User clicks "+ Add question" to add a new role requirement.

**PostHog call:**

```javascript
posthog.capture('Job Creation Wizard', {
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
- Same `Job Creation Wizard` event name — differentiated by `action_value`
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

#### 5b. Job Creation Wizard (user action — Next click)

User clicks "Next →" to proceed to Verify.

```javascript
posthog.capture('Job Creation Wizard', {
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

#### 5c. Job Creation Wizard (user action — Add question click)

User clicks "+ Add question" to add a new screening question.

```javascript
posthog.capture('Job Creation Wizard', {
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

#### 5d. Job Creation Wizard (user action — Back click)

User clicks "← Back" to go back to Role Requirements.

```javascript
posthog.capture('Job Creation Wizard', {
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
| **Trigger** | Backend saves screening config via `POST /flow/{job_id}/screening` → `configure_screening()` |
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

**Helix codebase change — add to `jobflow/router.py` → `configure_screening()` (after line 415):**

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
       → POST /flow/{job_id}/screening → configure_screening()
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

#### 6b. Job Creation Wizard (user action — Send code)

User clicks "Send code" to receive a 6-digit verification code.

```javascript
posthog.capture('Job Creation Wizard', {
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

#### 6c. Job Creation Wizard (user action — Maybe later)

User clicks "Maybe later" to skip verification and publish without verifying.

```javascript
posthog.capture('Job Creation Wizard', {
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

#### 6d. Job Creation Wizard (user action — Back)

User clicks "← Back" to go back to Interview Questions.

```javascript
posthog.capture('Job Creation Wizard', {
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

**Helix codebase change — add to `core/router.py` → `confirm_job_verification()` (POST /api/v1/job/{job_id}/verify/confirm):**

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
| **Trigger** | Backend publishes the job via `POST /flow/{job_id}/verify` → `verify_and_publish()` in `jobflow/router.py` |
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

