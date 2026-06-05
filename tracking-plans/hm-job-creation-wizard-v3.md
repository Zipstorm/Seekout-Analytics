# Tracking Plan: HM Job Creation Wizard v3

**Product:** Helix (SeekOut.ai)
**Feature:** Job description AI evaluation event — "Job details" step of the hiring manager job posting wizard (`/hiring-manager/job-posting`)
**Date:** 2026-06-05
**Related PRD:** —
**Scope:** v3 — 18 new events + 1 bug fix: 4 for the AI job description evaluation flow (step 1), Sam Session Started split into success/failure (step 2), 3 role requirement CRUD events (step 3), 3 screening question CRUD events with AI tracking (step 4), 7 success page events (share modal, invite, navigation), plus `Job Posting Published` backend bug fix. Also removes `Requirement Modified` and `Question Modified`.

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.
> Reference: `tracking-plans/hm-job-creation-wizard-v2.md` for the v2 wizard tracking plan (22 events).

---

## User Flow

```text
HM Job Posting Wizard — Step 1: Job Details
  │
  ├─ Page loads
  │    → fires: Page Viewed (existing, Live)
  │    → fires: Job Post Wizard Started (existing, Live — if new wizard)
  │
  ├─ User pastes/types job description in textarea
  │    → 1500ms debounce triggers AI analysis
  │    → UI shows: "Evaluating your job description" (loading state)
  │
  ├─ AI evaluation completes successfully
  │    → UI shows: "Job description evaluated" (green bar + extracted fields)
  │    → fires: Job Description Evaluated  ← NEW EVENT
  │
  ├─ AI evaluation fails / returns empty
  │    → UI shows: "Analysis unavailable. Try again."
  │    → fires: Job Description Evaluation Failed  ← NEW EVENT
  │
  ├─ User clicks "View full details" / "View less"
  │    → fires: Job Description Details Toggled  ← NEW EVENT
  │
  ├─ User edits Job title, Location, or Company field and blurs
  │    → fires: Job Description Field Edited (only if value changed)  ← NEW EVENT
  │
  └─ User clicks "Next →"
       → fires: Job Post Wizard Job Details Completed (existing, Live)
```

---

## Existing Events (no changes)

| Event | Status | Notes |
|-------|--------|-------|
| `Page Viewed` | Live | Fires on step 1 mount with `current_page_context: 'hm_job_creation_wizard_job_details'` |
| `Job Post Wizard Started` | Live | Fires once per fresh wizard entry |
| `Job Post Wizard Job Details Completed` | Live | Fires when user clicks "Next →" on step 1 |

---

## New Events

### 1. Job Description Evaluated

AI evaluation of a pasted job description completes successfully and populates the extracted fields (job title, company, location, skills, requirements, compensation, benefits).

| Field | Value |
|-------|-------|
| **Event** | `Job Description Evaluated` |
| **Area** | Hiring |
| **Type** | -- (system outcome, not a user action) |
| **Trigger** | `analyzeJobDescription()` API returns a meaningful result and extracted fields are populated in the UI |
| **Source** | Frontend |
| **Group** | `job` (when job_id is available) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `company_name` | string or null | e.g., `Netflix` | AI-extracted company name |
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Wizard step 1 page |
| `employment_type` | string or null | e.g., `Full-time`, `Contract` | AI-extracted employment type |
| `entity_type` | string | `job` | Business object context |
| `has_benefits` | boolean | `true`/`false` | Whether benefits were extracted |
| `has_compensation` | boolean | `true`/`false` | Whether compensation info was extracted |
| `input_length` | number | e.g., `2450` | Character count of the pasted job description text |
| `job_id` | string or null | UUID | Job ID if draft already exists (null on first paste before "Next" creates the draft) |
| `job_location` | string or null | e.g., `USA - Remote` | AI-extracted location |
| `job_title` | string or null | e.g., `Product Manager, Data Movement` | AI-extracted job title |
| `previous_page_context` | string | snake_case or null | Previous page |
| `requirements_count` | number | e.g., `5` | Number of key requirements extracted |
| `responsibilities_count` | number | e.g., `6` | Number of responsibilities extracted |
| `seniority_level` | string or null | e.g., `Senior`, `Lead` | AI-extracted seniority level |
| `skills_count` | number | e.g., `8` | Number of required skills extracted |
| `step_name` | string | `job_details` | Wizard step name |
| `step_number` | number | `1` | Wizard step number |
| `work_type` | string or null | e.g., `Remote`, `Hybrid`, `On-site` | AI-extracted work type |

**Implementation:**

**File:** `frontend/src/hooks/useJobDescriptionExtractor.ts`
**Location:** `runExtraction()` function, after `analyzeJobDescription()` returns successfully and `hasAny` is true (around line 222)

```typescript
import { capture } from '@/lib/posthog';
import { JOB_DESCRIPTION_EVALUATED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS, JOB_WIZARD_STEPS } from '@/lib/jobWizardAnalytics';

// Inside runExtraction, after setAnalysis(result) and setAnalyzedText(text):
if (hasAny) {
  // ... existing state updates (lines 207-223) ...

  capture(JOB_DESCRIPTION_EVALUATED, {
    company_name: result.company_name || null,
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.jobDetails,
    employment_type: result.employment_type ?? null,
    entity_type: 'job',
    has_benefits: result.benefits.length > 0,
    has_compensation: !!result.compensation_summary,
    input_length: text.length,
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    job_location: result.location || null,
    job_title: result.job_title || null,
    previous_page_context: getPreviousPageContext(),
    requirements_count: result.key_requirements.length,
    responsibilities_count: result.responsibilities.length,
    seniority_level: result.seniority_level ?? null,
    skills_count: result.required_skills.length,
    step_name: JOB_WIZARD_STEPS.jobDetails.stepName,
    step_number: JOB_WIZARD_STEPS.jobDetails.stepNumber,
    work_type: result.work_type ?? null,
  });
}
```

> **Note on `job_id`:** On first paste the job draft hasn't been created yet (that happens on "Next" click). The `job_id` will be null for the first evaluation but available for subsequent evaluations if the user goes back to step 1 and re-pastes. The hook needs access to the current `jobId` — check if it's already available via props or if it needs to be threaded through.

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const JOB_DESCRIPTION_EVALUATED = 'Job Description Evaluated';
```

---

### 2. Job Description Evaluation Failed

AI evaluation fails — either the API returns an empty/non-meaningful result or the request errors out.

| Field | Value |
|-------|-------|
| **Event** | `Job Description Evaluation Failed` |
| **Area** | Hiring |
| **Type** | -- (system failure) |
| **Trigger** | `analyzeJobDescription()` returns empty result for meaningful input, or throws an exception |
| **Source** | Frontend |
| **Group** | `job` (when job_id is available) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Wizard step 1 page |
| `entity_type` | string | `job` | Business object context |
| `error_reason` | string | `empty_result` or `api_error` | What went wrong |
| `input_length` | number | e.g., `2450` | Character count of the pasted text |
| `job_id` | string or null | UUID | Job ID if draft already exists |
| `previous_page_context` | string | snake_case or null | Previous page |
| `step_name` | string | `job_details` | Wizard step name |
| `step_number` | number | `1` | Wizard step number |

**Implementation:**

**File:** `frontend/src/hooks/useJobDescriptionExtractor.ts`
**Location:** Two places in `runExtraction()`:

```typescript
import { JOB_DESCRIPTION_EVALUATION_FAILED } from '@/lib/posthogEvents';

// 1. After hasAny is false (line 224-228):
} else {
  setAnalysisError('Analysis unavailable. Try again.');
  capture(JOB_DESCRIPTION_EVALUATION_FAILED, {
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.jobDetails,
    entity_type: 'job',
    error_reason: 'empty_result',
    input_length: text.length,
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    step_name: JOB_WIZARD_STEPS.jobDetails.stepName,
    step_number: JOB_WIZARD_STEPS.jobDetails.stepNumber,
  });
}

// 2. In the catch block (line 241-243):
} catch {
  setAnalysisError('Analysis unavailable. Try again.');
  capture(JOB_DESCRIPTION_EVALUATION_FAILED, {
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.jobDetails,
    entity_type: 'job',
    error_reason: 'api_error',
    input_length: text.length,
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    step_name: JOB_WIZARD_STEPS.jobDetails.stepName,
    step_number: JOB_WIZARD_STEPS.jobDetails.stepNumber,
  });
}
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const JOB_DESCRIPTION_EVALUATION_FAILED = 'Job Description Evaluation Failed';
```

---

### 3. Job Description Details Toggled

User clicks "View full details" or "View less" on the "Job description evaluated" card. Measures engagement with the AI extraction results — if most users never expand, the detailed view may not be adding value.

| Field | Value |
|-------|-------|
| **Event** | `Job Description Details Toggled` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "View full details" or "View less" on the evaluation card |
| **Source** | Frontend |
| **Group** | `job` (when job_id is available) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `view_full_details` or `view_less` | Exact button text in snake_case |
| `component` | string | `job_details_evaluation_card` | The "Job description evaluated" card |
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Wizard step 1 page |
| `entity_type` | string | `job` | Business object context |
| `expanded` | boolean | `true`/`false` | true = user expanded, false = user collapsed |
| `job_id` | string or null | UUID | Job ID if draft already exists |
| `previous_page_context` | string | snake_case or null | Previous page |
| `step_name` | string | `job_details` | Wizard step name |
| `step_number` | number | `1` | Wizard step number |

**Implementation:**

**File:** `frontend/src/components/common/JobDescriptionAnalysisCard.tsx`
**Location:** `JobDescriptionAnalysisExtracted` component, in the toggle button's `onClick` handler (line 255)

```typescript
import { capture } from '@/lib/posthog';
import { JOB_DESCRIPTION_DETAILS_TOGGLED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS, JOB_WIZARD_STEPS } from '@/lib/jobWizardAnalytics';

// Replace the existing onClick:
// onClick={() => setExpanded((v) => !v)}
// With:
onClick={() => {
  const nextExpanded = !expanded;
  setExpanded(nextExpanded);
  capture(JOB_DESCRIPTION_DETAILS_TOGGLED, {
    action: 'click',
    action_value: nextExpanded ? 'view_full_details' : 'view_less',
    component: 'job_details_evaluation_card',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.jobDetails,
    entity_type: 'job',
    expanded: nextExpanded,
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    step_name: JOB_WIZARD_STEPS.jobDetails.stepName,
    step_number: JOB_WIZARD_STEPS.jobDetails.stepNumber,
  });
}}
```

> **Note:** The component currently doesn't receive `jobId` as a prop. It will need to be threaded through from `JobInput.tsx` → `JobDescriptionAnalysisExtracted`.

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const JOB_DESCRIPTION_DETAILS_TOGGLED = 'Job Description Details Toggled';
```

---

### 4. Job Description Field Edited

User modifies one of the three AI-extracted editable fields (Job title, Location, Company) in the "Job description evaluated" card. This is a **satisfaction signal** — it measures how often users correct the AI extraction, which fields are corrected most, and what the corrections look like.

| Field | Value |
|-------|-------|
| **Event** | `Job Description Field Edited` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User changes a field value and blurs (leaves the input), AND the new value differs from the AI-extracted original |
| **Source** | Frontend |
| **Group** | `job` (when job_id is available) |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `component` | string | `job_details_evaluation_card` | The "Job description evaluated" card |
| `current_page_context` | string | `hm_job_creation_wizard_job_details` | Wizard step 1 page |
| `entity_type` | string | `job` | Business object context |
| `field_name` | enum | `job_title`, `job_location`, `company_name` | Which field was edited |
| `job_id` | string or null | UUID | Job ID if draft already exists |
| `new_value` | string | e.g., `Product Manager` | Value after edit |
| `original_value` | string or null | e.g., `Product Manager, Data Movement` | AI-extracted value before edit |
| `previous_page_context` | string | snake_case or null | Previous page |
| `step_name` | string | `job_details` | Wizard step name |
| `step_number` | number | `1` | Wizard step number |

**Implementation:**

**File:** `frontend/src/components/common/JobDescriptionAnalysisCard.tsx`
**Location:** Add `onBlur` handlers to the three `<Input>` elements (lines 132, 147, 162)

```typescript
import { capture } from '@/lib/posthog';
import { JOB_DESCRIPTION_FIELD_EDITED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS, JOB_WIZARD_STEPS } from '@/lib/jobWizardAnalytics';

// Add onBlur to each input. Example for Job title (line 132-137):
<Input
  id="extracted-job-title"
  value={title}
  onChange={(e) => onFieldChange('title', e.target.value)}
  onBlur={() => {
    if (title !== originalTitle) {
      capture(JOB_DESCRIPTION_FIELD_EDITED, {
        component: 'job_details_evaluation_card',
        current_page_context: JOB_WIZARD_PAGE_CONTEXTS.jobDetails,
        entity_type: 'job',
        field_name: 'job_title',
        ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
        new_value: title,
        original_value: originalTitle ?? null,
        previous_page_context: getPreviousPageContext(),
        step_name: JOB_WIZARD_STEPS.jobDetails.stepName,
        step_number: JOB_WIZARD_STEPS.jobDetails.stepNumber,
      });
    }
  }}
  placeholder="e.g. Senior AI Engineer"
/>
```

> **Guard: only fire when value actually changed.** The `onBlur` handler compares the current input value against the original AI-extracted value. If the user clicks the field, doesn't change anything (or types the same text back), the event is skipped.
>
> **Original values:** The component needs access to the original AI-extracted values (before any user edits). These come from the `analysis` result object stored in the extractor hook. Pass them as new props: `originalTitle` (from `analysis.job_title`), `originalLocation` (from `analysis.location`), `originalCompany` (from `analysis.company_name`).
>
> **Props needed:** The `JobDescriptionAnalysisExtracted` component needs two new props: `jobId` (string or null) and `originalAnalysis` (the raw analysis result) or individual `originalTitle`/`originalLocation`/`originalCompany` props.

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const JOB_DESCRIPTION_FIELD_EDITED = 'Job Description Field Edited';
```

---

## Existing Event Modification: Sam Session Started → Split

### Current Problem

`Sam Session Started` currently fires for both successful session starts AND voice setup failures. When voice setup fails (timeout, hardware error, permission denied), the event name says "Started" but the session never actually started. The `error_category` and `error_reason` properties on a "Started" event are semantically misleading.

**Current behavior in code** (`frontend/src/pages/interview/EmbeddedSamSession.tsx` → `handleStart()`):

```typescript
// Fires AFTER startEmbeddedHmSession() returns — regardless of voice connection state
const voiceState = useVoiceStore.getState();
const voiceStatus = selectedMode === 'voice'
  ? {
      micEnabled: voiceState.connectionState === 'connected',
      errorCategory: voiceState.lastSetupFailure?.category ?? null,
      errorReason: voiceState.lastSetupFailure?.reason ?? null,
    }
  : undefined;
captureSamSessionStarted(jobId, selectedMode, sessionId, voiceStatus);
```

### Fix: Split into two events

**`Sam Session Started`** — fires only when the session successfully starts (no error properties).

**`Sam Session Setup Failed`** — fires only when voice setup fails (carries error details).

### 5a. Sam Session Started (modified — success only)

| Field | Value |
|-------|-------|
| **Event** | `Sam Session Started` (existing, modified) |
| **Area** | Hiring |
| **Type** | -- |
| **Trigger** | Session starts successfully — voice connected or text mode selected |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Live (needs modification) |

**Properties (success only — error properties removed):**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_creation_wizard_sam_voice_session` or `hm_job_creation_wizard_sam_text_session` | Session page |
| `entity_type` | string | `job` | Business object context |
| `input_mode` | enum | `voice`, `text` | Session mode |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `session_id` | string | UUID | Session identifier |

### 5b. Sam Session Setup Failed (new)

| Field | Value |
|-------|-------|
| **Event** | `Sam Session Setup Failed` |
| **Area** | Hiring |
| **Type** | -- (system failure) |
| **Trigger** | Voice setup fails — timeout, hardware error, or permission denied |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `hm_job_creation_wizard_sam_voice_session` | Always voice — text mode can't fail setup |
| `entity_type` | string | `job` | Business object context |
| `error_category` | enum | `timeout`, `hardware`, `unknown` | Failure classification |
| `error_reason` | string | e.g., `Connection timed out. Please try again.` | Human-readable error message |
| `input_mode` | enum | `voice` | Always voice — only voice sessions can fail setup |
| `job_id` | string | UUID | Job identifier |
| `mic_enabled` | boolean | `true`/`false` | Whether microphone was accessible |
| `previous_page_context` | string | snake_case or null | Previous page |
| `session_id` | string | UUID | Session identifier |

**Known error scenarios:**

| Error | `error_category` | `error_reason` |
|---|---|---|
| Backend timeout | `timeout` | `Connection timed out. Please try again.` |
| No microphone found | `hardware` | `No microphone found. Connect a microphone and try again, or use Text chat instead.` |
| Microphone access blocked | `hardware` | `Microphone access is blocked. Allow microphone access in your browser, then try again.` |
| Microphone in use | `hardware` | `Your microphone is in use by another app. Close it and try again.` |
| Other errors | `unknown` | Actual error message or `Voice connection failed. Please try again.` |

**Implementation:**

**File 1:** `frontend/src/lib/jobWizardAnalytics.ts`
**Change:** Split `captureSamSessionStarted` into two functions

```typescript
import { SAM_SESSION_STARTED, SAM_SESSION_SETUP_FAILED } from '@/lib/posthogEvents';

// SUCCESS — fires only when session actually starts
export function captureSamSessionStarted(
  jobId: string,
  inputMode: 'voice' | 'text',
  sessionId: string,
): void {
  capture(SAM_SESSION_STARTED, {
    current_page_context: inputMode === 'voice'
      ? JOB_WIZARD_PAGE_CONTEXTS.samVoice
      : JOB_WIZARD_PAGE_CONTEXTS.samText,
    entity_type: 'job',
    input_mode: inputMode,
    ...jobGroup(jobId),
    previous_page_context: getPreviousPageContext(),
    session_id: sessionId,
  });
}

// FAILURE — fires only when voice setup fails
export function captureSamSessionSetupFailed(
  jobId: string,
  sessionId: string,
  voiceStatus: { micEnabled: boolean; errorCategory: string; errorReason: string },
): void {
  capture(SAM_SESSION_SETUP_FAILED, {
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.samVoice,
    entity_type: 'job',
    error_category: voiceStatus.errorCategory,
    error_reason: voiceStatus.errorReason,
    input_mode: 'voice',
    ...jobGroup(jobId),
    mic_enabled: voiceStatus.micEnabled,
    previous_page_context: getPreviousPageContext(),
    session_id: sessionId,
  });
}
```

**File 2:** `frontend/src/pages/interview/EmbeddedSamSession.tsx`
**Change:** In `handleStart()`, conditionally call one or the other

```typescript
import { captureSamSessionStarted, captureSamSessionSetupFailed } from '@/lib/jobWizardAnalytics';

// After startEmbeddedHmSession() returns:
if (jobId) {
  const voiceState = useVoiceStore.getState();
  const hasVoiceError = selectedMode === 'voice' && voiceState.lastSetupFailure;

  if (hasVoiceError) {
    captureSamSessionSetupFailed(jobId, sessionId, {
      micEnabled: voiceState.connectionState === 'connected',
      errorCategory: voiceState.lastSetupFailure.category,
      errorReason: voiceState.lastSetupFailure.reason,
    });
  } else {
    captureSamSessionStarted(jobId, selectedMode, sessionId);
  }
}
```

**File 3:** `frontend/src/lib/posthogEvents.ts`
**Change:** Add new constant

```typescript
export const SAM_SESSION_SETUP_FAILED = 'Sam Session Setup Failed';
```

---

### 6. Requirement Deleted

User clicks the trash icon to delete a role requirement question. Captures which question was removed and its metadata.

| Field | Value |
|-------|-------|
| **Event** | `Requirement Deleted` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks the delete (trash) icon on a role requirement question card |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `delete_question_button` | Trash icon button |
| `category` | enum | `compensation`, `work_arrangement`, `visa_authorization`, `security_clearance`, `licensing`, `background_check`, `physical_requirements`, `travel`, `other` | Question category |
| `component` | string | `role_requirements_question_card` | Question card UI |
| `current_page_context` | string | `hm_job_creation_wizard_role_requirements` | Step 3 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_source` | enum | `ai_generated`, `manual` | Whether AI or user created the question |
| `question_text` | string | e.g., `Are you comfortable with an annual salary range of...` | The question that was deleted |
| `question_type` | enum | `yes_no`, `multiple_choice`, `free_text` | Question type |
| `step_name` | string | `role_requirements` | Wizard step |
| `step_number` | number | `3` | Wizard step number |

**Implementation:**

**File:** `frontend/src/pages/interview/RoleRequirements.tsx`
**Location:** `deleteQuestion()` (line 687), capture before removing from state

```typescript
import { capture } from '@/lib/posthog';
import { REQUIREMENT_DELETED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS, JOB_WIZARD_STEPS } from '@/lib/jobWizardAnalytics';

const deleteQuestion = (questionId: string) => {
  const question = roleRequirementQuestions.find((q) => q.id === questionId);
  if (question) {
    capture(REQUIREMENT_DELETED, {
      action: 'click',
      action_value: 'delete_question_button',
      category: question.requirement_category ?? 'other',
      component: 'role_requirements_question_card',
      current_page_context: JOB_WIZARD_PAGE_CONTEXTS.roleRequirements,
      entity_type: 'job',
      ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
      previous_page_context: getPreviousPageContext(),
      question_source: question.source ?? 'manual',
      question_text: question.question,
      question_type: question.type,
      step_name: JOB_WIZARD_STEPS.roleRequirements.stepName,
      step_number: JOB_WIZARD_STEPS.roleRequirements.stepNumber,
    });
  }
  // ... existing delete logic ...
};
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const REQUIREMENT_DELETED = 'Requirement Deleted';
```

---

### 7. Requirement Edited

User edits a question's text and clicks the tick (save). **Only fires if the text changed from the original.**

| Field | Value |
|-------|-------|
| **Event** | `Requirement Edited` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User modifies question text and clicks save (tick), AND the new text differs from the original |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `category` | enum | `compensation`, `work_arrangement`, `visa_authorization`, `security_clearance`, `licensing`, `background_check`, `physical_requirements`, `travel`, `other` | Question category |
| `component` | string | `role_requirements_question_card` | Question card UI |
| `current_page_context` | string | `hm_job_creation_wizard_role_requirements` | Step 3 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `new_text` | string | e.g., `Are you comfortable with a salary range of $400K-$700K?` | Edited question text |
| `original_text` | string | e.g., `Are you comfortable with an annual salary range of...` | Text before edit |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_source` | enum | `ai_generated`, `manual` | Whether AI or user created it |
| `question_type` | enum | `yes_no`, `multiple_choice`, `free_text` | Question type |
| `step_name` | string | `role_requirements` | Wizard step |
| `step_number` | number | `3` | Wizard step number |

**Implementation:**

**File:** `frontend/src/pages/interview/RoleRequirements.tsx`
**Location:** `confirmQuestionEdit()` (line 376), after text comparison passes

```typescript
import { REQUIREMENT_EDITED } from '@/lib/posthogEvents';

// Inside confirmQuestionEdit, after nextText is computed:
const originalText = question.seed_question_text ?? question.question;
if (nextText !== originalText.trim()) {
  capture(REQUIREMENT_EDITED, {
    category: question.requirement_category ?? 'other',
    component: 'role_requirements_question_card',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.roleRequirements,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    new_text: nextText,
    original_text: originalText.trim(),
    previous_page_context: getPreviousPageContext(),
    question_source: question.source ?? 'manual',
    question_type: question.type,
    step_name: JOB_WIZARD_STEPS.roleRequirements.stepName,
    step_number: JOB_WIZARD_STEPS.roleRequirements.stepNumber,
  });
}
```

> **Guard:** Only fires when `nextText !== originalText`. If user clicks edit, doesn't change anything (or types the same text back), the event is skipped. Original text comes from `seed_question_text` (AI-generated original) or falls back to `question` (current text).

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const REQUIREMENT_EDITED = 'Requirement Edited';
```

---

### 8. Requirement Added

User fills the add question form (Type + Category + Question text) and clicks "Save question". This is the **outcome** event — the intent is already captured by `Requirement Add Button Clicked` (Live).

| Field | Value |
|-------|-------|
| **Event** | `Requirement Added` |
| **Area** | Hiring |
| **Type** | Success (for Requirement Add Button Clicked) |
| **Trigger** | User fills Type, Category, Question text and clicks "Save question", and the API confirms creation |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `category` | enum | `compensation`, `work_arrangement`, `visa_authorization`, `security_clearance`, `licensing`, `background_check`, `physical_requirements`, `travel`, `other` | Selected category |
| `component` | string | `role_requirements_add_question_form` | Add question form |
| `current_page_context` | string | `hm_job_creation_wizard_role_requirements` | Step 3 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_text` | string | e.g., `Do you have active security clearance?` | The question text entered |
| `question_type` | enum | `yes_no`, `multiple_choice`, `free_text` | Selected type |
| `step_name` | string | `role_requirements` | Wizard step |
| `step_number` | number | `3` | Wizard step number |

**Implementation:**

**File:** `frontend/src/pages/interview/RoleRequirements.tsx`
**Location:** `confirmQuestionEditor()` (line 514), after `createRoleRequirementQuestion()` API succeeds

```typescript
import { REQUIREMENT_ADDED } from '@/lib/posthogEvents';

// Inside confirmQuestionEditor, after API returns the new question:
const newQuestion = await interviewApi.createRoleRequirementQuestion(jobId, payload);
capture(REQUIREMENT_ADDED, {
  category: payload.category,
  component: 'role_requirements_add_question_form',
  current_page_context: JOB_WIZARD_PAGE_CONTEXTS.roleRequirements,
  entity_type: 'job',
  ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
  previous_page_context: getPreviousPageContext(),
  question_text: payload.label,
  question_type: payload.type,
  step_name: JOB_WIZARD_STEPS.roleRequirements.stepName,
  step_number: JOB_WIZARD_STEPS.roleRequirements.stepNumber,
});
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const REQUIREMENT_ADDED = 'Requirement Added';
```

---

## Existing Event Modification: Requirement Modified → Removed

`Requirement Modified` (currently Not Started in catalog) is replaced by the three granular events above. It should be moved to the Removed Events table during merge.

| Old Event | Replaced By | Why |
|-----------|-------------|-----|
| Requirement Modified | Requirement Deleted, Requirement Edited, Requirement Added | Generic `modification_type` replaced by specific events with richer properties (question text, category, type, source, before/after for edits) |

---

### 9. Screening Question Deleted

User clicks the trash icon to delete a screening question on the Interview Questions step.

| Field | Value |
|-------|-------|
| **Event** | `Screening Question Deleted` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks the delete (trash) icon on a screening question card |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `delete_question_button` | Trash icon button |
| `component` | string | `interview_questions_question_card` | Question card UI |
| `current_page_context` | string | `hm_job_creation_wizard_interview_questions` | Step 4 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_number` | number | e.g., `2` | Position in the list (from `sort_order`) |
| `question_source` | enum | `ai_generated`, `manual` | Whether AI or user created it |
| `question_text` | string | The question that was deleted | Question text |
| `step_name` | string | `interview_questions` | Wizard step |
| `step_number` | number | `4` | Wizard step number |

**Implementation:**

**File:** `frontend/src/pages/interview/InterviewQuestions.tsx`
**Location:** `handleDelete()` (line 193), capture before API call

```typescript
import { capture } from '@/lib/posthog';
import { SCREENING_QUESTION_DELETED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS, JOB_WIZARD_STEPS } from '@/lib/jobWizardAnalytics';

const handleDelete = async (questionId: string) => {
  if (!jobId) return;
  const question = questions.find((q) => q.id === questionId);
  if (question) {
    capture(SCREENING_QUESTION_DELETED, {
      action: 'click',
      action_value: 'delete_question_button',
      component: 'interview_questions_question_card',
      current_page_context: JOB_WIZARD_PAGE_CONTEXTS.interviewQuestions,
      entity_type: 'job',
      ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
      previous_page_context: getPreviousPageContext(),
      question_number: question.sort_order,
      question_source: question.source ?? 'manual',
      question_text: question.question,
      step_name: JOB_WIZARD_STEPS.interviewQuestions.stepName,
      step_number: JOB_WIZARD_STEPS.interviewQuestions.stepNumber,
    });
  }
  await interviewApi.deleteScreeningQuestion(jobId, questionId);
  loadQuestions();
};
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const SCREENING_QUESTION_DELETED = 'Screening Question Deleted';
```

---

### 10. Screening Question Edited

User edits a screening question's text and clicks the tick (save), OR uses "Refine with AI". **Only fires if the text changed from the original.** Captures whether AI refinement was used.

| Field | Value |
|-------|-------|
| **Event** | `Screening Question Edited` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User modifies question text and clicks save (tick) or uses "Refine with AI", AND the new text differs from the original |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `ai_refined` | boolean | `true`/`false` | Whether "Refine with AI" was used for this edit |
| `component` | string | `interview_questions_question_card` | Question card UI |
| `current_page_context` | string | `hm_job_creation_wizard_interview_questions` | Step 4 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `new_text` | string | Edited question text | Text after save |
| `original_text` | string | Original question text | Text before edit |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_source` | enum | `ai_generated`, `manual` | Whether AI or user originally created it |
| `step_name` | string | `interview_questions` | Wizard step |
| `step_number` | number | `4` | Wizard step number |

**Implementation:**

Fires in two places:

**1. Manual edit — File:** `InterviewQuestions.tsx`, `handleSaveEdit()` (line 186)

```typescript
import { SCREENING_QUESTION_EDITED } from '@/lib/posthogEvents';

const handleSaveEdit = async () => {
  if (!editingId || !jobId || !editText.trim()) return;
  const question = questions.find((q) => q.id === editingId);
  const originalText = question?.question ?? '';
  const nextText = editText.trim();
  if (nextText !== originalText) {
    capture(SCREENING_QUESTION_EDITED, {
      ai_refined: false,
      component: 'interview_questions_question_card',
      current_page_context: JOB_WIZARD_PAGE_CONTEXTS.interviewQuestions,
      entity_type: 'job',
      ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
      new_text: nextText,
      original_text: originalText,
      previous_page_context: getPreviousPageContext(),
      question_source: question?.source ?? 'manual',
      step_name: JOB_WIZARD_STEPS.interviewQuestions.stepName,
      step_number: JOB_WIZARD_STEPS.interviewQuestions.stepNumber,
    });
  }
  await interviewApi.updateScreeningQuestion(jobId, editingId, { question: nextText });
  setEditingId(null);
  loadQuestions();
};
```

**2. AI refine — File:** `InterviewQuestions.tsx`, `handleAIRefine()` (line 215)

```typescript
const handleAIRefine = async (args: AIPopoverArgs) => {
  if (!jobId || !editingId) return;
  const question = questions.find((q) => q.id === editingId);
  const originalText = question?.question ?? '';
  const refined = await interviewApi.refineScreeningQuestion(jobId, editingId, buildAIPayload(args));
  if (refined.question !== originalText) {
    capture(SCREENING_QUESTION_EDITED, {
      ai_refined: true,
      component: 'interview_questions_question_card',
      current_page_context: JOB_WIZARD_PAGE_CONTEXTS.interviewQuestions,
      entity_type: 'job',
      ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
      new_text: refined.question,
      original_text: originalText,
      previous_page_context: getPreviousPageContext(),
      question_source: question?.source ?? 'manual',
      step_name: JOB_WIZARD_STEPS.interviewQuestions.stepName,
      step_number: JOB_WIZARD_STEPS.interviewQuestions.stepNumber,
    });
  }
  setEditingId(null);
  setEditText(refined.question);
  setQuestions((prev) => prev.map((q) => (q.id === refined.id ? refined : q)));
};
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const SCREENING_QUESTION_EDITED = 'Screening Question Edited';
```

---

### 11. Screening Question Added

User adds a new screening question — either by typing text and clicking save, or using "Create with AI". This is the **outcome** event — the intent is already captured by `Question Add Button Clicked` (Live).

| Field | Value |
|-------|-------|
| **Event** | `Screening Question Added` |
| **Area** | Hiring |
| **Type** | Success (for Question Add Button Clicked) |
| **Trigger** | User saves a new question (manual text or AI-created), and the API confirms creation |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `ai_created` | boolean | `true`/`false` | Whether "Create with AI" was used |
| `component` | string | `interview_questions_add_question_form` | Add question form |
| `current_page_context` | string | `hm_job_creation_wizard_interview_questions` | Step 4 page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `question_text` | string | The question text | Question that was added |
| `step_name` | string | `interview_questions` | Wizard step |
| `step_number` | number | `4` | Wizard step number |

**Implementation:**

Fires in two places:

**1. Manual add — File:** `InterviewQuestions.tsx`, `handleAdd()` (line 199)

```typescript
import { SCREENING_QUESTION_ADDED } from '@/lib/posthogEvents';

const handleAdd = async () => {
  if (!jobId || !newText.trim()) return;
  await interviewApi.createScreeningQuestion(jobId, { question: newText.trim() });
  capture(SCREENING_QUESTION_ADDED, {
    ai_created: false,
    component: 'interview_questions_add_question_form',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.interviewQuestions,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    question_text: newText.trim(),
    step_name: JOB_WIZARD_STEPS.interviewQuestions.stepName,
    step_number: JOB_WIZARD_STEPS.interviewQuestions.stepNumber,
  });
  setNewText('');
  setAddingNew(false);
  loadQuestions();
};
```

**2. AI create — File:** `InterviewQuestions.tsx`, `handleAICreate()` (line 207)

```typescript
const handleAICreate = async (args: AIPopoverArgs) => {
  if (!jobId) return;
  const created = await interviewApi.aiCreateScreeningQuestion(jobId, buildAIPayload(args));
  capture(SCREENING_QUESTION_ADDED, {
    ai_created: true,
    component: 'interview_questions_add_question_form',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.interviewQuestions,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    question_text: created.question,
    step_name: JOB_WIZARD_STEPS.interviewQuestions.stepName,
    step_number: JOB_WIZARD_STEPS.interviewQuestions.stepNumber,
  });
  setNewText('');
  setAddingNew(false);
  loadQuestions();
};
```

**Constant:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const SCREENING_QUESTION_ADDED = 'Screening Question Added';
```

---

## Existing Event Modification: Question Modified → Removed

`Question Modified` (currently Not Started in catalog) is replaced by the three granular events above. It should be moved to the Removed Events table during merge.

| Old Event | Replaced By | Why |
|-----------|-------------|-----|
| Question Modified | Screening Question Deleted, Screening Question Edited, Screening Question Added | Generic `modification_type` replaced by specific events with richer properties (question text, source, AI usage, before/after for edits) |

---

## Bug Fix: `Job Posting Published` not firing

`Job Posting Published` is marked Live in the catalog but is **not reliably firing** due to a race condition in the backend dedup logic.

**Root cause:** In `backend/app/core/router.py`, `_should_capture_published()` (lines 185-195) checks if the pre-update state already has `wizard_step=completed`. The Verify step's PATCH often sets `wizard_step=COMPLETED` before the status reaches `active` (because `_ensure_job_can_publish` throws when the rubric isn't ready). Later, when `finalize-setup` actually transitions the job to `active`, the dedup guard sees `wizard_step` was already `completed` and **suppresses the event**.

Additionally, if finalization retries via the background worker (`finalize_default_rubric_task`), that worker has **no PostHog capture code**.

**Fix options:**
1. Change `_should_capture_published` to only dedup on `status` (not `wizard_step`): `return not _is_active_or_published(pre_state.get("status"))`
2. Or add a PostHog capture in `finalize_job_setup` service method after the status is set to `active` (line 824 in `core/service.py`), independent of `_should_capture_published`
3. Or add capture in the background worker retry path

**Files to fix:**
- `backend/app/core/router.py` — `_should_capture_published()` at lines 185-195
- `backend/app/core/service.py` — `finalize_job_setup()` at line 824 (status set to active)

---

## Success Page Events

### 12. Success Page Share Button Clicked

User clicks "Share →" button on the success page, opening the share modal. Intent/exploration signal.

| Field | Value |
|-------|-------|
| **Event** | `Success Page Share Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Share →" on the success page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `share_button` | Button text |
| `component` | string | `success_page_share_cta` | Share section on success page |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/pages/interview/JobSuccess.tsx`
**Location:** Share button `onClick` handler (line 317)

```typescript
import { capture } from '@/lib/posthog';
import { SUCCESS_PAGE_SHARE_BUTTON_CLICKED, getPreviousPageContext } from '@/lib/posthogEvents';
import { JOB_WIZARD_PAGE_CONTEXTS } from '@/lib/jobWizardAnalytics';

onClick={() => {
  capture(SUCCESS_PAGE_SHARE_BUTTON_CLICKED, {
    action: 'click',
    action_value: 'share_button',
    component: 'success_page_share_cta',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.success,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  setShareModalOpen(true);
}}
```

**Constant:**
```typescript
export const SUCCESS_PAGE_SHARE_BUTTON_CLICKED = 'Success Page Share Button Clicked';
```

---

### 13. Job Share Message AI Refined

User clicks "Refine with AI" in the share modal and generates a new message.

| Field | Value |
|-------|-------|
| **Event** | `Job Share Message AI Refined` |
| **Area** | Hiring |
| **Type** | -- (AI action) |
| **Trigger** | User enters instruction and clicks "Generate message" in the Refine with AI popover |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `component` | string | `success_page_share_modal` | Share modal |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/components/interview/ShareInterviewModal.tsx`
**Location:** `handleGeneratePost()` (line 223), after API returns successfully

```typescript
import { capture } from '@/lib/posthog';
import { JOB_SHARE_MESSAGE_AI_REFINED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleGeneratePost = async () => {
  // ... existing logic ...
  const result = await interviewApi.refineJobSocialPost(jobId, postText, instruction, shareUrl);
  capture(JOB_SHARE_MESSAGE_AI_REFINED, {
    component: 'success_page_share_modal',
    current_page_context: 'hm_job_creation_wizard_success',
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  // ... rest of existing logic ...
};
```

**Constant:**
```typescript
export const JOB_SHARE_MESSAGE_AI_REFINED = 'Job Share Message AI Refined';
```

---

### 14. Job Share Message Copied

User clicks "Copy message" in the share modal.

| Field | Value |
|-------|-------|
| **Event** | `Job Share Message Copied` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Copy message" button in the share modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `copy_message_button` | Button text |
| `component` | string | `success_page_share_modal` | Share modal |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/components/interview/ShareInterviewModal.tsx`
**Location:** `handleCopy()` (line 200)

```typescript
import { JOB_SHARE_MESSAGE_COPIED } from '@/lib/posthogEvents';

const handleCopy = () => {
  navigator.clipboard.writeText(postText);
  capture(JOB_SHARE_MESSAGE_COPIED, {
    action: 'click',
    action_value: 'copy_message_button',
    component: 'success_page_share_modal',
    current_page_context: 'hm_job_creation_wizard_success',
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  setCopied(true);
  persistEdit();
  setTimeout(() => setCopied(false), 2000);
};
```

**Constant:**
```typescript
export const JOB_SHARE_MESSAGE_COPIED = 'Job Share Message Copied';
```

---

### 15. Job Share Channel Clicked

User clicks LinkedIn, X, or Email button in the share modal to distribute the job posting.

| Field | Value |
|-------|-------|
| **Event** | `Job Share Channel Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks a share platform button (LinkedIn, X, Email) in the share modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `share_to_linkedin` / `share_to_x` / `share_to_email` | Which channel button |
| `component` | string | `success_page_share_modal` | Share modal |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |
| `share_channel` | enum | `linkedin` / `x` / `email` | Distribution channel |

**Implementation:**

**File:** `frontend/src/components/interview/ShareInterviewModal.tsx`
**Location:** `handlePlatformShare()` (line 207)

```typescript
import { JOB_SHARE_CHANNEL_CLICKED } from '@/lib/posthogEvents';

const handlePlatformShare = (getUrl: PlatformUrlFn) => {
  const url = getUrl(shareUrl, postText, jobTitle);
  capture(JOB_SHARE_CHANNEL_CLICKED, {
    action: 'click',
    action_value: `share_to_${platform.id}`,
    component: 'success_page_share_modal',
    current_page_context: 'hm_job_creation_wizard_success',
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
    share_channel: platform.id,  // 'linkedin', 'x', or 'email'
  });
  window.open(url, '_blank');
  persistEdit();
};
```

> **Note:** The platform `id` values from the PLATFORMS array are: `linkedin`, `x`, `email`. These map directly to the `share_channel` enum.

**Constant:**
```typescript
export const JOB_SHARE_CHANNEL_CLICKED = 'Job Share Channel Clicked';
```

---

### 16. Invite Teammates Button Clicked

User clicks "Invite teammates" on the success page, opening the invite modal.

| Field | Value |
|-------|-------|
| **Event** | `Invite Teammates Button Clicked` |
| **Area** | Hiring |
| **Type** | Intent |
| **Trigger** | User clicks "Invite teammates" button on the success page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `invite_teammates_button` | Button text |
| `component` | string | `success_page_invite_cta` | Invite section |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/pages/interview/JobSuccess.tsx`
**Location:** Invite teammates button `onClick` handler (line 340)

```typescript
import { INVITE_TEAMMATES_BUTTON_CLICKED } from '@/lib/posthogEvents';

onClick={() => {
  capture(INVITE_TEAMMATES_BUTTON_CLICKED, {
    action: 'click',
    action_value: 'invite_teammates_button',
    component: 'success_page_invite_cta',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.success,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  setInviteModalOpen(true);
}}
```

**Constant:**
```typescript
export const INVITE_TEAMMATES_BUTTON_CLICKED = 'Invite Teammates Button Clicked';
```

---

### 17. Team Member Invite Sent

User fills the invite form (email, role) and clicks "Send invite". Captures the role and invite count. Note: this opens the email client via `mailto:` — no backend API call is made.

| Field | Value |
|-------|-------|
| **Event** | `Team Member Invite Sent` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Send invite" in the invite modal |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `send_invite_button` | Button text |
| `component` | string | `success_page_invite_modal` | Invite modal |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `invite_count` | number | e.g., `2` | Number of email addresses entered |
| `invite_role` | enum | `recruiter` / `other` | Selected role for the invitee |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/components/interview/InviteModal.tsx`
**Location:** `handleSendInvite()` (line 44), capture before opening mailto

```typescript
import { capture } from '@/lib/posthog';
import { TEAM_MEMBER_INVITE_SENT, getPreviousPageContext } from '@/lib/posthogEvents';

const handleSendInvite = () => {
  if (!email) return;
  const emailList = email.split(',').map((e) => e.trim()).filter(Boolean);
  capture(TEAM_MEMBER_INVITE_SENT, {
    action: 'click',
    action_value: 'send_invite_button',
    component: 'success_page_invite_modal',
    current_page_context: 'hm_job_creation_wizard_success',
    entity_type: 'job',
    invite_count: emailList.length,
    invite_role: role,
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  const subject = encodeURIComponent(`You're invited to review candidates for ${jobTitle}`);
  const body = encodeURIComponent(draftMessage);
  window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
};
```

> **Note:** The `jobId` prop needs to be threaded into `InviteModal` from `JobSuccess.tsx` — it's not currently a prop.

**Constant:**
```typescript
export const TEAM_MEMBER_INVITE_SENT = 'Team Member Invite Sent';
```

---

### 18. Go To Job Posting Page Clicked

User clicks "Go to job posting page" link at the bottom of the success page.

| Field | Value |
|-------|-------|
| **Event** | `Go To Job Posting Page Clicked` |
| **Area** | Hiring |
| **Type** | user_action |
| **Trigger** | User clicks "Go to job posting page" link on the success page |
| **Source** | Frontend |
| **Group** | `job` |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `go_to_job_posting_page` | Link text |
| `component` | string | `success_page_footer` | Footer area |
| `current_page_context` | string | `hm_job_creation_wizard_success` | Success page |
| `entity_type` | string | `job` | Business object |
| `job_id` | string | UUID | Job identifier |
| `previous_page_context` | string | snake_case or null | Previous page |

**Implementation:**

**File:** `frontend/src/pages/interview/JobSuccess.tsx`
**Location:** "Go to job posting page" button `onClick` handler (line 355)

```typescript
import { GO_TO_JOB_POSTING_PAGE_CLICKED } from '@/lib/posthogEvents';

onClick={() => {
  capture(GO_TO_JOB_POSTING_PAGE_CLICKED, {
    action: 'click',
    action_value: 'go_to_job_posting_page',
    component: 'success_page_footer',
    current_page_context: JOB_WIZARD_PAGE_CONTEXTS.success,
    entity_type: 'job',
    ...(jobId ? { job_id: jobId, $groups: { job: jobId } } : {}),
    previous_page_context: getPreviousPageContext(),
  });
  navigate(routes.detailPage(jobId));
}}
```

**Constant:**
```typescript
export const GO_TO_JOB_POSTING_PAGE_CLICKED = 'Go To Job Posting Page Clicked';
```

---

## New Events Summary

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|-------|------|---------|----------------|-------|------------------|
| Job Description Evaluated | Hiring | AI analysis returns meaningful result | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_length`, `job_title`, `company_name`, `job_location`, `skills_count`, `requirements_count`, `responsibilities_count`, `has_compensation`, `has_benefits`, `seniority_level`, `work_type`, `employment_type`, `step_number`, `step_name` | `job` | -- |
| Job Description Evaluation Failed | Hiring | AI analysis fails or returns empty | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `input_length`, `error_reason`, `step_number`, `step_name` | `job` | -- |
| Job Description Details Toggled | Hiring | User clicks "View full details" or "View less" | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `action`, `action_value`, `component`, `expanded`, `step_number`, `step_name` | `job` | -- |
| Job Description Field Edited | Hiring | User edits an AI-extracted field and blurs | `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `field_name`, `original_value`, `new_value`, `component`, `step_number`, `step_name` | `job` | -- |
| Sam Session Setup Failed | Hiring | Voice session setup fails (timeout, hardware, permission) | `current_page_context`, `entity_type`, `error_category`, `error_reason`, `input_mode`, `job_id`, `mic_enabled`, `previous_page_context`, `session_id` | `job` | -- |
| Requirement Deleted | Hiring | User clicks trash icon on a role requirement | `action`, `action_value`, `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_source`, `question_text`, `question_type`, `step_name`, `step_number` | `job` | -- |
| Requirement Edited | Hiring | User edits question text and saves (only if changed) | `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `new_text`, `original_text`, `previous_page_context`, `question_source`, `question_type`, `step_name`, `step_number` | `job` | -- |
| Requirement Added | Hiring | User fills add form and clicks "Save question" | `category`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_text`, `question_type`, `step_name`, `step_number` | `job` | -- |
| Screening Question Deleted | Hiring | User clicks trash icon on a screening question | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_number`, `question_source`, `question_text`, `step_name`, `step_number` | `job` | -- |
| Screening Question Edited | Hiring | User edits question text and saves (only if changed) | `ai_refined`, `component`, `current_page_context`, `entity_type`, `job_id`, `new_text`, `original_text`, `previous_page_context`, `question_source`, `step_name`, `step_number` | `job` | -- |
| Screening Question Added | Hiring | User saves a new screening question | `ai_created`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `question_text`, `step_name`, `step_number` | `job` | -- |
| Success Page Share Button Clicked | Hiring | User clicks "Share →" on success page | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- |
| Job Share Message AI Refined | Hiring | User refines share message with AI | `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- |
| Job Share Message Copied | Hiring | User clicks "Copy message" in share modal | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- |
| Job Share Channel Clicked | Hiring | User clicks LinkedIn/X/Email in share modal | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context`, `share_channel` | `job` | -- |
| Invite Teammates Button Clicked | Hiring | User clicks "Invite teammates" on success page | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- |
| Team Member Invite Sent | Hiring | User clicks "Send invite" in invite modal | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `invite_count`, `invite_role`, `job_id`, `previous_page_context` | `job` | -- |
| Go To Job Posting Page Clicked | Hiring | User clicks "Go to job posting page" link | `action`, `action_value`, `component`, `current_page_context`, `entity_type`, `job_id`, `previous_page_context` | `job` | -- |

---

## Intent vs Outcome

The JD evaluation events don't follow the standard intent/outcome pattern — there's no user intent event since the evaluation triggers automatically via debounce.

The Sam session split is a modification of an existing event (not a new flow). `Sam Session Started` already exists in the catalog; `Sam Session Setup Failed` is the new failure counterpart. No new Intent vs Outcome row needed — the existing v2 tracking plan's Sam flow covers this.

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| JD Evaluation → Step Completion | Job Description Evaluated → Job Post Wizard Job Details Completed | % of users who get a successful evaluation and proceed to step 2. Note: `Job Post Wizard Job Details Completed` is a v2 event — ensure v2 is merged first. |
| Evaluation Success Rate | Job Description Evaluated | Single-event insight. Compare count of `Job Description Evaluated` vs `Job Description Evaluation Failed` to measure AI evaluation reliability. |
| Requirement Add Conversion | Requirement Add Button Clicked → Requirement Added | % of add-button clicks that result in a saved requirement |
| Screening Question Add Conversion | Question Add Button Clicked → Screening Question Added | % of add-button clicks that result in a saved screening question |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `input_length` | number | -- | Character count of the pasted job description text |
| `job_title` | string | -- | AI-extracted job title from the job description |
| `company_name` | string | -- | AI-extracted company name |
| `job_location` | string | -- | AI-extracted location |
| `skills_count` | number | -- | Number of required skills AI extracted |
| `requirements_count` | number | -- | Number of key requirements AI extracted |
| `responsibilities_count` | number | -- | Number of responsibilities AI extracted |
| `has_compensation` | boolean | true / false | Whether compensation info was found in the JD |
| `has_benefits` | boolean | true / false | Whether benefits were found in the JD |
| `seniority_level` | string | -- | AI-extracted seniority level (e.g., Senior, Lead, Staff) |
| `work_type` | string | -- | AI-extracted work type (e.g., Remote, Hybrid, On-site) |
| `employment_type` | string | -- | AI-extracted employment type (e.g., Full-time, Contract) |
| `expanded` | boolean | true / false | Whether user expanded or collapsed the details card |
| `field_name` | enum | job_title / job_location / company_name | Which AI-extracted field was edited |
| `original_value` | string | -- | AI-extracted value before user edit |
| `new_value` | string | -- | Value after user edit |
| `mic_enabled` | boolean | true / false | Whether microphone was accessible at time of voice setup failure |
| `session_id` | string | UUID | Sam session identifier |
| `question_text` | string | -- | Role requirement question text (deleted or added) |
| `original_text` | string | -- | Original question text before edit |
| `new_text` | string | -- | Edited question text after save |
| `question_type` | enum | yes_no / multiple_choice / free_text | Role requirement question type |
| `question_source` | enum | ai_generated / manual | Whether AI or user created the question |
| `category` | enum | compensation / work_arrangement / visa_authorization / security_clearance / licensing / background_check / physical_requirements / travel / other | Role requirement question category |
| `question_number` | number | -- | Position of the screening question in the list (from sort_order) |
| `ai_refined` | boolean | true / false | Whether "Refine with AI" was used during edit |
| `ai_created` | boolean | true / false | Whether "Create with AI" was used to generate the question |
| `share_channel` | enum | linkedin / x / email | Distribution channel in share modal |
| `invite_count` | number | -- | Number of email addresses entered in invite form |
| `invite_role` | enum | recruiter / other | Selected role for the invited team member |

> **Note:** `current_page_context`, `previous_page_context`, `entity_type`, `job_id`, `step_number`, `step_name`, `error_reason`, `error_category`, `action`, `action_value`, `component`, and `input_mode` are existing catalog properties — not listed here.

---

## Constants Reference

```typescript
// frontend/src/lib/posthogEvents.ts
export const JOB_DESCRIPTION_EVALUATED = 'Job Description Evaluated';
export const JOB_DESCRIPTION_EVALUATION_FAILED = 'Job Description Evaluation Failed';
export const JOB_DESCRIPTION_DETAILS_TOGGLED = 'Job Description Details Toggled';
export const JOB_DESCRIPTION_FIELD_EDITED = 'Job Description Field Edited';
export const SAM_SESSION_SETUP_FAILED = 'Sam Session Setup Failed';
export const REQUIREMENT_DELETED = 'Requirement Deleted';
export const REQUIREMENT_EDITED = 'Requirement Edited';
export const REQUIREMENT_ADDED = 'Requirement Added';
export const SCREENING_QUESTION_DELETED = 'Screening Question Deleted';
export const SCREENING_QUESTION_EDITED = 'Screening Question Edited';
export const SCREENING_QUESTION_ADDED = 'Screening Question Added';
export const SUCCESS_PAGE_SHARE_BUTTON_CLICKED = 'Success Page Share Button Clicked';
export const JOB_SHARE_MESSAGE_AI_REFINED = 'Job Share Message AI Refined';
export const JOB_SHARE_MESSAGE_COPIED = 'Job Share Message Copied';
export const JOB_SHARE_CHANNEL_CLICKED = 'Job Share Channel Clicked';
export const INVITE_TEAMMATES_BUTTON_CLICKED = 'Invite Teammates Button Clicked';
export const TEAM_MEMBER_INVITE_SENT = 'Team Member Invite Sent';
export const GO_TO_JOB_POSTING_PAGE_CLICKED = 'Go To Job Posting Page Clicked';
```

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

### `docs/event-catalog.md`

**Hiring Persona Events table — add new events:**

All 18 new events should be inserted into the Hiring Persona Events section. Additionally:
- Update the existing `Sam Session Started` row to remove `error_category`, `error_reason`, and `mic_enabled` from its properties (those now belong to `Sam Session Setup Failed` only).
- Remove the existing `Requirement Modified` row (replaced by Requirement Deleted, Requirement Edited, Requirement Added).
- Remove the existing `Question Modified` row (replaced by Screening Question Deleted, Screening Question Edited, Screening Question Added).

**Removed Events table — add:**

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|--------------|
| Requirement Modified | Requirement Deleted, Requirement Edited, Requirement Added | Generic `modification_type` replaced by specific events with richer properties (question text, category, type, source, before/after for edits) | June 2026 |
| Question Modified | Screening Question Deleted, Screening Question Edited, Screening Question Added | Generic `modification_type` replaced by specific events with richer properties (question text, source, AI usage, before/after for edits) | June 2026 |

**Property Dictionary updates:**

| Section | Property | Change |
|---------|----------|--------|
| Numeric | `input_length` | New property. Used In: `Job Description Evaluated`, `Job Description Evaluation Failed` |
| Numeric | `skills_count` | New property. Used In: `Job Description Evaluated` |
| Numeric | `requirements_count` | New property. Used In: `Job Description Evaluated` |
| Numeric | `responsibilities_count` | New property. Used In: `Job Description Evaluated` |
| Boolean | `has_compensation` | New property. Used In: `Job Description Evaluated` |
| Boolean | `has_benefits` | New property. Used In: `Job Description Evaluated` |
| String | `seniority_level` | New property. Used In: `Job Description Evaluated` |
| String | `work_type` | New property. Used In: `Job Description Evaluated` |
| String | `employment_type` | New property. Used In: `Job Description Evaluated` |
| Boolean | `mic_enabled` | New property. Used In: `Sam Session Setup Failed` |
| String | `session_id` | New property. Used In: `Sam Session Setup Failed`. Also update Used In to include existing `Sam Session Started`, `Sam Session Ended`. |
| Boolean | `expanded` | New property. Used In: `Job Description Details Toggled` |
| Boolean | `ai_refined` | New property. Used In: `Screening Question Edited` |
| Boolean | `ai_created` | New property. Used In: `Screening Question Added` |
| Enum | `share_channel` | Already exists. Append to Used In: `Job Share Channel Clicked` |
| Numeric | `invite_count` | New property. Used In: `Team Member Invite Sent` |
| Enum | `invite_role` | New property. Values: `recruiter`, `other`. Used In: `Team Member Invite Sent` |
| String | `question_text` | New property. Used In: `Requirement Deleted`, `Requirement Added`, `Screening Question Deleted`, `Screening Question Added` |
| String | `original_text` | New property. Used In: `Requirement Edited`, `Screening Question Edited` |
| String | `new_text` | New property. Used In: `Requirement Edited`, `Screening Question Edited` |
| Enum | `question_type` | New property. Values: `yes_no`, `multiple_choice`, `free_text`. Used In: `Requirement Deleted`, `Requirement Edited`, `Requirement Added` |
| Enum | `question_source` | New property. Values: `ai_generated`, `manual`. Used In: `Requirement Deleted`, `Requirement Edited`, `Screening Question Deleted`, `Screening Question Edited` |
| Enum | `category` (requirement) | New property. Values: `compensation`, `work_arrangement`, `visa_authorization`, `security_clearance`, `licensing`, `background_check`, `physical_requirements`, `travel`, `other`. Used In: `Requirement Deleted`, `Requirement Edited`, `Requirement Added` |
| Enum | `field_name` | New property. Values: `job_title`, `job_location`, `company_name`. Used In: `Job Description Field Edited` |
| String | `original_value` | New property. Used In: `Job Description Field Edited` |
| String | `new_value` | New property. Used In: `Job Description Field Edited` |

**Property Dictionary — update "Used In" for existing properties:**

| Property | Append to "Used In" |
|----------|---------------------|
| `current_page_context` | Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited |
| `previous_page_context` | Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited |
| `entity_type` | Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited |
| `action` (user_action) | Job Description Details Toggled |
| `action_value` | Job Description Details Toggled |
| `component` | Job Description Details Toggled, Job Description Field Edited |
| `error_reason` | Job Description Evaluation Failed |
| `action` (user_action) | Requirement Deleted, Screening Question Deleted |
| `action_value` | Requirement Deleted, Screening Question Deleted |
| `component` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `current_page_context` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `previous_page_context` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `entity_type` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added, all success page events |
| `step_number` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `step_name` | Requirement Deleted, Requirement Edited, Requirement Added, Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `current_page_context` | all success page events (Success Page Share Button Clicked, Job Share Message AI Refined, Job Share Message Copied, Job Share Channel Clicked, Invite Teammates Button Clicked, Team Member Invite Sent, Go To Job Posting Page Clicked) |
| `previous_page_context` | all success page events |

> **Note:** `job_title`, `company_name`, `job_location`, `job_id`, `step_number`, `step_name` already exist in the catalog from v2 wizard events — update their "Used In" lists to include `Job Description Evaluated`.

### `docs/event-schema.md`

**Standard Objects table — update:**

| Object | Change |
|--------|--------|
| Job Wizard | Append to example events: `Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited` |
| Voice Session | Update example events: replace `Voice Session Setup Failed` with `Sam Session Setup Failed` (if present). Append `Sam Session Setup Failed` if not listed. |

No new Standard Objects needed — "Job Description" events match the existing "Job" prefix object via the validator's prefix matching. However, semantically they belong to the "Job Wizard" object family.

### `docs/dashboards.md`

No dashboard changes needed — the Hiring Dashboard already tracks the wizard flow. These events supplement existing funnel visibility.

---

## Helix Code Changes Summary

| File | Change | Events Affected |
|------|--------|----------------|
| `frontend/src/lib/posthogEvents.ts` | Add 18 new event constants | All 18 events |
| `frontend/src/hooks/useJobDescriptionExtractor.ts` | Add capture calls in `runExtraction()` after success (hasAny=true) and in both failure paths (hasAny=false, catch block) | Job Description Evaluated, Job Description Evaluation Failed |
| `frontend/src/components/common/JobDescriptionAnalysisCard.tsx` | Add capture in toggle button `onClick`. Add `onBlur` handlers to 3 editable inputs with value-change guard. Thread `jobId` and original analysis values as new props. | Job Description Details Toggled, Job Description Field Edited |
| `frontend/src/lib/jobWizardAnalytics.ts` | Split `captureSamSessionStarted()` into success-only version + new `captureSamSessionSetupFailed()` function. Remove `voiceStatus` param from `captureSamSessionStarted`. | Sam Session Started (modified), Sam Session Setup Failed |
| `frontend/src/pages/interview/EmbeddedSamSession.tsx` | Update `handleStart()` to conditionally call `captureSamSessionStarted` or `captureSamSessionSetupFailed` based on `voiceState.lastSetupFailure` | Sam Session Started (modified), Sam Session Setup Failed |
| `frontend/src/pages/interview/RoleRequirements.tsx` | Add capture in `deleteQuestion()` before state removal. Add capture in `confirmQuestionEdit()` with text-change guard. Add capture in `confirmQuestionEditor()` after API success. | Requirement Deleted, Requirement Edited, Requirement Added |
| `frontend/src/pages/interview/InterviewQuestions.tsx` | Add capture in `handleDelete()` before API call. Add capture in `handleSaveEdit()` and `handleAIRefine()` with text-change guard. Add capture in `handleAdd()` and `handleAICreate()` after API success. | Screening Question Deleted, Screening Question Edited, Screening Question Added |
| `frontend/src/pages/interview/JobSuccess.tsx` | Add captures for Share, Invite teammates, and Go to job posting page buttons. | Success Page Share Button Clicked, Invite Teammates Button Clicked, Go To Job Posting Page Clicked |
| `frontend/src/components/interview/ShareInterviewModal.tsx` | Add captures in `handleGeneratePost()`, `handleCopy()`, and `handlePlatformShare()`. Thread `jobId` as prop. | Job Share Message AI Refined, Job Share Message Copied, Job Share Channel Clicked |
| `frontend/src/components/interview/InviteModal.tsx` | Add capture in `handleSendInvite()` with role and email count. Thread `jobId` as prop. | Team Member Invite Sent |
| `backend/app/core/router.py` | Fix `_should_capture_published()` dedup logic — only dedup on `status`, not `wizard_step` | Job Posting Published (bug fix) |

---

## Known Analytics Gaps

| Gap | Description | Severity | Status |
|-----|-------------|----------|--------|
| `job_id` null on first evaluation | Job draft isn't created until "Next" click — first evaluation fires with null `job_id`. Subsequent evaluations (if user re-pastes) will have it. | Low | Accepted |
| Re-evaluation not deduplicated | If user edits the JD text multiple times, the debounce fires multiple evaluations. Each success fires the event. No dedup by content hash. | Low | Accepted — volume is useful signal |
| URL-based JD fetch not covered | When user pastes a URL and the system fetches the JD from it, the extraction flow is slightly different (`isFetchingUrl` state). The same evaluation event will fire once the extracted text is analyzed. | Low | Covered — same `runExtraction()` path |
