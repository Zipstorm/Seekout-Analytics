# HM Job Creation Wizard — Firing Rules

**Flow:** `hm_job_creation_wizard`
**Last Updated:** April 2026

---

## Session & Job Identification

This flow does NOT use a custom `wizard_session_id`. Instead, we rely on:

| Identifier | Source | Available on |
|---|---|---|
| `session_id` | PostHog SDK (auto-captured) | All events |
| `job_id` | URL params `/hiring-manager/job-postings/{job_id}/...` | All events from PV-2 onwards |

**Why no custom wizard ID:**
- `session_id` already groups all events in a browser session
- `job_id` groups all events for a specific job (persists across sessions if user resumes)
- Step 1 events have no `job_id` yet, but `session_id` is sufficient since users rarely start multiple wizards in one browser session

---

## Job ID Availability

| Step | job_id available? |
|---|---|
| PV-1 (Job Details page load) | No — null |
| UA-1 (Next on Job Details) | No — null at click time. Backend creates job in response. |
| All events from PV-2 onwards | Yes — read from URL params: `/hiring-manager/job-postings/{job_id}/...` |

```javascript
// In wizard pages from Step 2 onwards
import { useParams } from 'react-router';
const { jobId } = useParams();
```

---

## New Event Constants Needed

Add these to `posthogEvents.ts` (alongside the existing `CREATE_JOB_BUTTON_CLICKED`, `JOB_CREATED`, etc.):

```typescript
// HM Job Creation Wizard
export const JOB_WIZARD_NEXT_CLICKED = 'Job Wizard Next Clicked';
export const JOB_WIZARD_BACK_CLICKED = 'Job Wizard Back Clicked';
export const JOB_WIZARD_CLOSE_CLICKED = 'Job Wizard Close Clicked';
export const START_TALKING_TO_SAM_CLICKED = 'Start Talking To Sam Clicked';
export const SKIP_SAM_CLICKED = 'Skip Sam Clicked';
export const SAM_CHAT_MODALITY_SELECTED = 'Sam Chat Modality Selected';
export const EDIT_REQUIREMENT_CLICKED = 'Edit Requirement Clicked';
export const DELETE_REQUIREMENT_CLICKED = 'Delete Requirement Clicked';
export const ADD_REQUIREMENT_CLICKED = 'Add Requirement Clicked';
export const SAVE_REQUIREMENT_CLICKED = 'Save Requirement Clicked';
export const CANCEL_REQUIREMENT_CLICKED = 'Cancel Requirement Clicked';
export const EDIT_QUESTION_CLICKED = 'Edit Question Clicked';
export const DELETE_QUESTION_CLICKED = 'Delete Question Clicked';
export const ADD_QUESTION_CLICKED = 'Add Question Clicked';
export const REFINE_QUESTIONS_SUBMITTED = 'Refine Questions Submitted';
export const SUGGESTION_CHIP_CLICKED = 'Suggestion Chip Clicked';
export const REMOVE_SUGGESTION_CHIP_CLICKED = 'Remove Suggestion Chip Clicked';
export const SEND_CODE_CLICKED = 'Send Code Clicked';
export const VERIFY_CODE_SUBMITTED = 'Verify Code Submitted';
export const SKIP_VERIFICATION_CLICKED = 'Skip Verification Clicked';
export const EDIT_EMAIL_CLICKED = 'Edit Email Clicked';
export const JOB_PREVIEW_CLICKED = 'Job Preview Clicked';
export const GO_TO_JOB_POSTING_CLICKED = 'Go To Job Posting Clicked';
export const CONTINUE_SETUP_CLICKED = 'Continue Setup Clicked';
```

**Already exists in `posthogEvents.ts`** — reuse:
- `PAGE_VIEWED` — for all wizard page views
- `CREATE_JOB_BUTTON_CLICKED` — fired from home page (already implemented)
- `SHARE_BUTTON_CLICKED` — UA-36 on success page
- `INVITE_BUTTON_CLICKED` — UA-37 on success page
- `JOB_CREATED` — backend confirmation after UA-1 (system event, separate from this user_action plan)

---

## Page View Events

### PV-1: Job Details (Step 1)

```javascript
// In JobDetailsPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/job_details',
  previous_page_context: previousPageContext, // 'hiring_manager/job_postings'
  entry_point: entryPoint, // 'job_postings_page_header_click_create_job_posting_button' or 'job_postings_empty_state_cta_click_create_job_posting_button'
  context_object_type: null,
  job_id: null, // job not yet created
});
```

### PV-2: Understanding the Role (Step 2)

```javascript
// In UnderstandingTheRolePage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/understanding_the_role',
  previous_page_context: previousPageContext, // 'hm_job_creation_wizard/job_details' or 'hiring_manager/job_postings' (continue setup)
  entry_point: entryPoint, // 'hm_job_creation_wizard_job_details_click_next_button' or 'job_postings_job_card_click_continue_setup_button'
  context_object_type: null,
  job_id: jobId,
});
```

### PV-2b: Sam Chat Modality Selection (Step 2b)

```javascript
// In SamChatModalitySelectionPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/sam_chat_modality_selection',
  previous_page_context: 'hm_job_creation_wizard/understanding_the_role',
  entry_point: 'hm_job_creation_wizard_understanding_the_role_click_start_talking_to_sam_button',
  context_object_type: null,
  job_id: jobId,
});
```

### PV-3: Role Requirements (Step 3)

```javascript
// In RoleRequirementsPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext, // 'hm_job_creation_wizard/understanding_the_role' or 'hm_job_creation_wizard/sam_chat_modality_selection'
  entry_point: entryPoint,
  context_object_type: null,
  job_id: jobId,
});
```

### PV-4: Interview Questions (Step 4)

```javascript
// In InterviewQuestionsPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: 'hm_job_creation_wizard_role_requirements_click_next_button',
  context_object_type: null,
  job_id: jobId,
});
```

### PV-5: Verify (Step 5)

```javascript
// In VerifyPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: 'hm_job_creation_wizard_interview_questions_click_next_button',
  context_object_type: null,
  job_id: jobId,
});
```

### PV-6: Success (Step 6)

```javascript
// In SuccessPage.tsx — useEffect on mount
capture(PAGE_VIEWED, {
  current_page_context: 'hm_job_creation_wizard/success',
  previous_page_context: 'hm_job_creation_wizard/verify',
  entry_point: 'hm_job_creation_wizard_verify_click_verify_button' or 'hm_job_creation_wizard_verify_click_skip_for_now_link',
  context_object_type: null,
  job_id: jobId,
});
```

---

## User Action Events

### Step 1: Job Details

#### UA-1: Next click (creates job)

```javascript
// In JobDetailsPage.tsx — Next button onClick
capture(JOB_WIZARD_NEXT_CLICKED, {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard/job_details',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_job_details_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: null, // job not yet created
});
// Backend will fire JOB_CREATED separately with the new job_id
```

#### UA-2: Back click

```javascript
// In JobDetailsPage.tsx — Back button onClick
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/job_details',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_job_details_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: null,
});
```

#### UA-3: Close (X) click

```javascript
// In JobWizardHeader.tsx — Close icon onClick
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/job_details',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: null,
});
```

---

### Step 2: Understanding the Role

#### UA-4: Start talking to Sam click

```javascript
// In UnderstandingTheRolePage.tsx — "Start talking to Sam" button onClick
capture(START_TALKING_TO_SAM_CLICKED, {
  action: 'click',
  action_value: 'start_talking_to_sam_button',
  current_page_context: 'hm_job_creation_wizard/understanding_the_role',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_understanding_the_role_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-5: Skip click

```javascript
// In UnderstandingTheRolePage.tsx — "Skip (just use the JD...)" link onClick
capture(SKIP_SAM_CLICKED, {
  action: 'click',
  action_value: 'skip_link',
  current_page_context: 'hm_job_creation_wizard/understanding_the_role',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_understanding_the_role_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-6: Back click

```javascript
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/understanding_the_role',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_understanding_the_role_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-7: Close (X) click

```javascript
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/understanding_the_role',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

---

### Step 2b: Sam Chat Modality Selection

#### UA-8: Voice modality click

```javascript
// In SamChatModalitySelectionPage.tsx — Voice option onClick
capture(SAM_CHAT_MODALITY_SELECTED, {
  action: 'click',
  action_value: 'voice_modality_option',
  current_page_context: 'hm_job_creation_wizard/sam_chat_modality_selection',
  previous_page_context: 'hm_job_creation_wizard/understanding_the_role',
  entry_point: null,
  entity_type: 'voice_session',
  component: 'hm_job_creation_wizard_sam_chat_modality_selection_options',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  modality: 'voice',
});
```

#### UA-9: Text modality click

```javascript
capture(SAM_CHAT_MODALITY_SELECTED, {
  action: 'click',
  action_value: 'text_modality_option',
  current_page_context: 'hm_job_creation_wizard/sam_chat_modality_selection',
  previous_page_context: 'hm_job_creation_wizard/understanding_the_role',
  entry_point: null,
  entity_type: 'chat_session',
  component: 'hm_job_creation_wizard_sam_chat_modality_selection_options',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  modality: 'text',
});
```

#### UA-10: Back click

```javascript
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/sam_chat_modality_selection',
  previous_page_context: 'hm_job_creation_wizard/understanding_the_role',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_sam_chat_modality_selection_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-11: Close (X) click

```javascript
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/sam_chat_modality_selection',
  previous_page_context: 'hm_job_creation_wizard/understanding_the_role',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

---

### Step 3: Role Requirements

#### UA-12: Next click

```javascript
capture(JOB_WIZARD_NEXT_CLICKED, {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-13: Back click

```javascript
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-14: Close (X) click

```javascript
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-15: Edit requirement icon click

```javascript
capture(EDIT_REQUIREMENT_CLICKED, {
  action: 'click',
  action_value: 'edit_requirement_icon',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  requirement_index: requirementIndex, // e.g., 1, 2, 3
});
```

#### UA-16: Delete requirement icon click

```javascript
capture(DELETE_REQUIREMENT_CLICKED, {
  action: 'click',
  action_value: 'delete_requirement_icon',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  requirement_index: requirementIndex,
});
```

#### UA-17: Add requirement button click

```javascript
capture(ADD_REQUIREMENT_CLICKED, {
  action: 'click',
  action_value: 'add_requirement_button',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-18: Save requirement (tick) click

```javascript
capture(SAVE_REQUIREMENT_CLICKED, {
  action: 'click',
  action_value: 'save_requirement_tick',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  modification_type: isNew ? 'added' : 'edited', // 'added' for new requirement, 'edited' for existing
});
```

#### UA-19: Cancel requirement (cross) click

```javascript
capture(CANCEL_REQUIREMENT_CLICKED, {
  action: 'click',
  action_value: 'cancel_requirement_cross',
  current_page_context: 'hm_job_creation_wizard/role_requirements',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'requirement',
  component: 'hm_job_creation_wizard_role_requirements_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

---

### Step 4: Interview Questions

#### UA-20: Next click

```javascript
capture(JOB_WIZARD_NEXT_CLICKED, {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-21: Back click

```javascript
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-22: Close (X) click

```javascript
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-23: Edit question icon click

```javascript
capture(EDIT_QUESTION_CLICKED, {
  action: 'click',
  action_value: 'edit_question_icon',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  question_index: questionIndex,
});
```

#### UA-24: Delete question icon click

```javascript
capture(DELETE_QUESTION_CLICKED, {
  action: 'click',
  action_value: 'delete_question_icon',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  question_index: questionIndex,
});
```

#### UA-25: Add question button click

```javascript
capture(ADD_QUESTION_CLICKED, {
  action: 'click',
  action_value: 'add_question_button',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_list',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-26: Refine questions submit (Apply click or Enter key)

```javascript
// Fires on Apply button click OR Enter key press when input is focused
capture(REFINE_QUESTIONS_SUBMITTED, {
  action: 'submit',
  action_value: 'refine_screening_questions_input',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_refine_bar',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  prompt_text: promptText, // e.g., "focus on ai and ml"
  trigger: triggerType, // 'apply_button' or 'enter_key'
});
```

#### UA-27: Suggestion chip click

```javascript
capture(SUGGESTION_CHIP_CLICKED, {
  action: 'click',
  action_value: 'suggestion_chip',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_refine_bar',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  chip_label: chipLabel, // e.g., 'Probe creative tool ecosystem knowledge'
});
```

#### UA-28: Remove suggestion chip click

```javascript
capture(REMOVE_SUGGESTION_CHIP_CLICKED, {
  action: 'click',
  action_value: 'remove_suggestion_chip',
  current_page_context: 'hm_job_creation_wizard/interview_questions',
  previous_page_context: 'hm_job_creation_wizard/role_requirements',
  entry_point: null,
  entity_type: 'question',
  component: 'hm_job_creation_wizard_interview_questions_refine_bar',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  chip_label: chipLabel,
});
```

---

### Step 5: Verify

#### UA-29: Send code click

```javascript
capture(SEND_CODE_CLICKED, {
  action: 'click',
  action_value: 'send_code_button',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'verification',
  component: 'hm_job_creation_wizard_verify_form',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-30: Verify OTP submit (Verify button click or Enter key)

```javascript
capture(VERIFY_CODE_SUBMITTED, {
  action: 'submit',
  action_value: 'verification_code_input',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'verification',
  component: 'hm_job_creation_wizard_verify_otp_modal',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  trigger: triggerType, // 'verify_button' or 'enter_key'
});
```

#### UA-31: Skip for now click

```javascript
capture(SKIP_VERIFICATION_CLICKED, {
  action: 'click',
  action_value: 'skip_for_now_link',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'verification',
  component: 'hm_job_creation_wizard_verify_form',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-32: Back click

```javascript
capture(JOB_WIZARD_BACK_CLICKED, {
  action: 'click',
  action_value: 'back_button',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_verify_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-33: Close (X) click

```javascript
capture(JOB_WIZARD_CLOSE_CLICKED, {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-34: Edit email icon click

```javascript
capture(EDIT_EMAIL_CLICKED, {
  action: 'click',
  action_value: 'edit_email_icon',
  current_page_context: 'hm_job_creation_wizard/verify',
  previous_page_context: 'hm_job_creation_wizard/interview_questions',
  entry_point: null,
  entity_type: 'verification',
  component: 'hm_job_creation_wizard_verify_form',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

---

### Step 6: Success Page

#### UA-35: Preview click

```javascript
capture(JOB_PREVIEW_CLICKED, {
  action: 'click',
  action_value: 'preview_button',
  current_page_context: 'hm_job_creation_wizard/success',
  previous_page_context: 'hm_job_creation_wizard/verify',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_success_job_card',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-36: Share button click

```javascript
// Reuses existing SHARE_BUTTON_CLICKED constant
capture(SHARE_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'share_button',
  current_page_context: 'hm_job_creation_wizard/success',
  previous_page_context: 'hm_job_creation_wizard/verify',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_success_share_section',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
  share_source: 'success_screen',
});
```

#### UA-37: Invite team click

```javascript
// Reuses existing INVITE_BUTTON_CLICKED constant
capture(INVITE_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'invite_team_button',
  current_page_context: 'hm_job_creation_wizard/success',
  previous_page_context: 'hm_job_creation_wizard/verify',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_success_invite_section',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

#### UA-38: Go to job posting page click

```javascript
capture(GO_TO_JOB_POSTING_CLICKED, {
  action: 'click',
  action_value: 'go_to_job_posting_page_link',
  current_page_context: 'hm_job_creation_wizard/success',
  previous_page_context: 'hm_job_creation_wizard/verify',
  entry_point: null,
  entity_type: 'job',
  component: 'hm_job_creation_wizard_success_footer',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId,
});
```

---

### Dashboard: Continue Setup (UA-39)

```javascript
// In JobPostingsListPage.tsx — Continue Setup button onClick on incomplete job card
capture(CONTINUE_SETUP_CLICKED, {
  action: 'click',
  action_value: 'continue_setup_button',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'job_postings_job_card',
  context_object_type: null,
  context_object_id: null,
  job_id: jobId, // the job that is being resumed
});
```

---

## Complete Firing Sequence — Happy Path

```
 #  | Event                                              | Type        | job_id
----|----------------------------------------------------|-------------|--------
  1 | Page Viewed (hm_job_creation_wizard/job_details)       | page_view   | null
  2 | Job Wizard Next Clicked                            | user_action | null
  3 | [Job Created — backend system event]                | system      | job_xyz
  4 | Page Viewed (understanding_the_role)                | page_view   | job_xyz
  5 | Start Talking To Sam Clicked                       | user_action | job_xyz
  6 | Page Viewed (sam_chat_modality_selection)           | page_view   | job_xyz
  7 | Sam Chat Modality Selected (modality=voice)        | user_action | job_xyz
  8 | [Voice Session Started — system event]              | system      | job_xyz
  9 | Page Viewed (role_requirements)                     | page_view   | job_xyz
 10 | Job Wizard Next Clicked                            | user_action | job_xyz
 11 | Page Viewed (interview_questions)                   | page_view   | job_xyz
 12 | Job Wizard Next Clicked                            | user_action | job_xyz
 13 | Page Viewed (verify)                                | page_view   | job_xyz
 14 | Send Code Clicked                                  | user_action | job_xyz
 15 | Verify Code Submitted                              | user_action | job_xyz
 16 | Page Viewed (success)                               | page_view   | job_xyz
 17 | [Job Published — system event]                      | system      | job_xyz
```

All events also share the same auto-captured `session_id` from PostHog SDK.

## Drop-off & Resume Sequence

```
Session 1:
  Page Viewed (job_details) → Next → Job Created → Page Viewed (understanding_the_role) → Close (X)
  → Returns to dashboard. Job appears with "Continue setup" CTA.

Session 2 (later):
  Page Viewed (hiring_manager/job_postings) → Continue Setup Clicked
  → Page Viewed (understanding_the_role) with previous_page_context='hiring_manager/job_postings'
  → All events in Session 2 have the same job_id as Session 1 (resume tracked via job_id)
```
