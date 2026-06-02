# Tracking Plan: Job Seeker Profile Setup

**Product:** Helix (SeekOut.ai)
**Feature:** Job seeker profile setup — resume upload, photo, links, AI profile generation (`/candidate/create-profile`)
**Date:** 2026-06-02
**Related PRD:** —
**Scope:** v1 — Create Profile page events only. Editor (B) and Dashboard (C) events deferred to v2.

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## User Flow

```text
Onboarding (existing events — no changes)
  │
  ├─ /onboarding/role — selects "I'm a professional", clicks "Continue as candidate"
  │    → fires: Page Viewed (existing, Live)
  │    → fires: Account Created (existing, Live)
  │
  ├─ /onboarding/intro — clicks "Let's go"
  │    → fires: Page Viewed (existing, Live)
  │    → fires: Intro Completed (existing, Live)
  │
  └─ /candidate/create-profile — "Build your profile" page (THIS TRACKING PLAN)
       │
       ├─ Page loads
       │    → fires: Page Viewed (existing event, new page context)
       │
       ├─ Resume section
       │    ├─ User clicks upload area → fires: Resume Upload Button Clicked
       │    ├─ Backend confirms upload → fires: Resume Uploaded
       │    ├─ Backend rejects upload → fires: Resume Upload Failed
       │    └─ User clicks "Remove" → fires: Resume Removed
       │
       ├─ Profile photo section
       │    ├─ User clicks "Add profile image" → fires: Add Profile Photo Button Clicked
       │    ├─ Photo successfully added → fires: Profile Photo Added
       │    ├─ Photo upload fails → fires: Profile Photo Upload Failed
       │    └─ User clicks "Remove" on photo → fires: Profile Photo Removed
       │
       └─ Submit
            ├─ User clicks "Build my AI profile" → fires: Build Profile Button Clicked
            ├─ State snapshot captured → fires: Profile Build Snapshot
            ├─ AI generates profile → fires: Candidate Profile Created
            └─ AI generation fails → fires: Candidate Profile Creation Failed
```

---

## Existing Events (reused, no changes needed)

These events already fire in the Helix codebase and are documented in `docs/event-catalog.md`. No modifications required.

| Event | Status | File | Notes |
|-------|--------|------|-------|
| `Page Viewed` | Live | `RoleSelection.tsx`, `ValueProp.tsx` | Already fires on `/onboarding/role` and `/onboarding/intro`. Needs to be added to `/candidate/create-profile` — see Section 1 below. |
| `Account Created` | Live | `RoleSelection.tsx` → `handleContinue()` | Fires when user clicks "Continue as candidate". Properties match catalog. |
| `Intro Completed` | Live | `ValueProp.tsx` → `handleContinue()` | Fires when user clicks "Let's go". Properties match catalog. |

---

## Existing Event: Conflict Flag

### `Profile Created` — currently in catalog and Helix code

**What the catalog says** (`docs/event-catalog.md`, Prospect Persona Events):

| Event | Area | Type | Trigger | Source | Properties | Group | Status |
|-------|------|------|---------|--------|------------|-------|--------|
| Profile Created | Prospect | -- | AI generates initial profile from resume | Backend | `input_method` | -- | Not Started |

**What the Helix code actually fires** (`backend/app/portfolio/router.py` → `create_portfolio()` endpoint):

```python
posthog_client.capture(
    current_user.id,
    PROFILE_CREATED,
    {PROP_SURFACE: SURFACE_PROSPECT, "portfolio_id": portfolio.id, "input_method": "resume_upload"},
)
```

**Properties actually sent:**
- `surface`: `"prospect"` — not in catalog
- `portfolio_id`: UUID — not in catalog
- `input_method`: `"resume_upload"` — matches catalog

**Decision needed:** This tracking plan proposes `Candidate Profile Created` (event 8c below) as a richer replacement. It fires at the same trigger point with more properties. Options:
1. **Replace** `Profile Created` with `Candidate Profile Created` — remove the old capture, add the new one
2. **Supplement** — fire both (redundant, not recommended)

> **Action for reviewer:** Decide whether to replace or supplement. This tracking plan is written assuming **replace**.

---

## Existing Event: Conflict Flag #2

### `Profile Section Updated` — `section` enum mismatch

**What the catalog says** (`docs/event-catalog.md`, Property Dictionary):

```
section | enum | event | summary, experience, skills, timeline | Profile Section Updated
```

**What the Helix code actually sends** (`pages/candidate/PortfolioEditor.tsx`):

```typescript
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'summary' });
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'skills' });
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'journey' });
```

**Mismatches:**
- Code sends `journey`, catalog says `timeline` — the UI calls it "Journey", so the code is correct
- Code sends `surface` property — this is a legacy property (`PROP_SURFACE`) that is redundant with `current_persona`. When a user switches persona, they move to that persona's surface (job_seeker → prospect, hiring_manager/recruiter → hiring). The mapping is deterministic, so `surface` adds no signal beyond `current_persona`. It should be **removed from Helix code** and replaced with `current_persona` as an explicit event property.
- Code doesn't send `experience` or `education` — need to add these as new capture calls for individual entry edits

> **Fix (apply during `/merge-tracking-plan`):** Update `section` enum allowed values from `summary, experience, skills, timeline` to `summary, skills, journey, experience, education`. Remove `timeline` from allowed values.
>
> **`surface` removal — Helix code fix:**
>
> 3 backend events currently send `surface`. Replace with `current_persona` on each:
>
> | Event | File | Current | Change to |
> |-------|------|---------|-----------|
> | `Profile Created` | `backend/app/portfolio/router.py` → `create_portfolio()` | `PROP_SURFACE: SURFACE_PROSPECT` | Being **replaced entirely** by `Candidate Profile Created` (see event 8c) |
> | `Custom Link Created` | `backend/app/users/router.py` → `create_link()` | `PROP_SURFACE: SURFACE_PROSPECT` | Replace with `PROP_CURRENT_PERSONA: get_current_persona(user.role)` |
> | `Profile Link Viewed` | `backend/app/portfolio/router.py` → `get_public_portfolio()` | `PROP_SURFACE: SURFACE_PROSPECT` | This is an anonymous/public event (no auth). `current_persona` does not apply. Remove `surface` and leave as-is — the event context is already clear from the event name. |
>
> **Frontend fix:** Remove `surface: SURFACE_PROSPECT` from all `Profile Section Updated` capture calls in `PortfolioEditor.tsx`.
>
> **New capture calls for `experience` and `education`:** Add `Profile Section Updated` captures with `section: 'experience'` and `section: 'education'` in the individual entry edit forms within the Journey edit modal (when user saves a specific experience or education entry). See the Helix codebase changes section below.
>
> **Migration caution:** Before removing `PROP_SURFACE` / `SURFACE_PROSPECT` / `SURFACE_HIRING` constants from the Helix codebase:
> 1. Search for `PROP_SURFACE`, `SURFACE_PROSPECT`, `SURFACE_HIRING` across all frontend and backend files to confirm only the 3 events above + `PortfolioEditor.tsx` use them
> 2. Check PostHog for any saved insights, dashboards, or cohorts filtering on the `surface` property — migrate them to `current_persona` first
> 3. Only then remove the constants from `posthog_events.py`

---

## New Events

### 1. Page Viewed (new page context)

The existing `Page Viewed` event needs to fire on `/candidate/create-profile`. This is not a new event — just a new page context being added.

| Field | Value |
|-------|-------|
| **Event** | `Page Viewed` (existing) |
| **Area** | Navigation |
| **Type** | page_view |
| **Trigger** | User lands on the "Build your profile" page |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `candidate_create_profile` | Page identifier |
| `previous_page_context` | string | snake_case or null | Previous page (typically `onboarding_intro`) |
| `entry_point` | string | `direct`, etc. | Entry context |

**Helix codebase change:**

In `frontend/src/pages/candidate/CreateProfile.tsx` (or the component that renders `/candidate/create-profile`), add a `useEffect` on mount:

```typescript
import { capture, PAGE_VIEWED, getPreviousPageContext } from '@/lib/posthogEvents';

useEffect(() => {
  capture(PAGE_VIEWED, {
    current_page_context: 'candidate_create_profile',
    previous_page_context: getPreviousPageContext(),
    entry_point: null,
  });
}, []);
```

---

### 2a. Resume Upload Button Clicked

User clicks the resume upload area/button to open the file picker. This is the **intent** — the user may select a file or cancel the picker.

| Field | Value |
|-------|-------|
| **Event** | `Resume Upload Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Resume Uploaded) |
| **Trigger** | User clicks the upload area/button in the resume section |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `upload_resume_button` | Button label in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_resume_section` | Section within the page |

**PostHog call:**

```typescript
capture('Resume Upload Button Clicked', {
  action: 'click',
  action_value: 'upload_resume_button',
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
  component: 'create_profile_resume_section',
});
```

**Helix codebase change:**

In `frontend/src/pages/candidate/CreateProfile.tsx` (or the resume upload sub-component, likely `frontend/src/pages/ResumeUpload.tsx` or a similar component rendered on the create-profile page), add capture in the click handler that opens the file input:

```typescript
// In the onClick handler for the resume upload area/button
// BEFORE triggering the file input click
capture(RESUME_UPLOAD_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'upload_resume_button',
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
  component: 'create_profile_resume_section',
});
fileInputRef.current?.click();
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const RESUME_UPLOAD_BUTTON_CLICKED = 'Resume Upload Button Clicked';
```

---

### 2b. Resume Uploaded

Backend confirms the resume was successfully uploaded, validated (magic bytes + text extraction), and stored.

| Field | Value |
|-------|-------|
| **Event** | `Resume Uploaded` |
| **Area** | Prospect |
| **Type** | Success (for Resume Upload Button Clicked) |
| **Trigger** | Backend successfully stores resume after validation (presign → blob upload → confirm) |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string | UUID | Resume identifier from `Resume.id` |
| `file_name` | string | e.g., `One Page Resume.pdf` | Original filename |
| `file_type` | string | `pdf`, `doc`, `docx`, `txt` | File format (from extension) |
| `file_size_bytes` | number | e.g., `245000` | File size in bytes |
| `page_count` | number or null | e.g., `2` | PDF page count (null for non-PDF formats) |
| `current_page_context` | string | `candidate_create_profile` | Page context (passed from frontend via request or inferred) |

**Notes:**
- `page_count` requires a small code change in `resume_parser.py` — see Helix code changes below
- `file_size_bytes` can be read from the blob or from the upload request
- No duplicate detection exists today (no file hash stored). Out of scope for v1.

**Helix codebase changes:**

**Change 1: Add page count extraction to resume parser**

In `backend/app/session_runtime/services/resume_parser.py` → `extract_text_from_pdf()`:

```python
# CURRENT CODE:
def extract_text_from_pdf(file: BinaryIO) -> str:
    import fitz
    content = file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)

# CHANGE TO (return page count alongside text):
def extract_text_from_pdf(file: BinaryIO) -> tuple[str, int]:
    """Extract text from PDF. Returns (text, page_count)."""
    import fitz
    content = file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    page_count = len(doc)
    doc.close()
    return "\n".join(text_parts), page_count
```

> **Note:** This changes the return type from `str` to `tuple[str, int]`. All callers of `extract_text_from_pdf()` need to be updated to unpack the tuple. Check `resume_parser.py` and any files that import this function.

**Change 2: Add PostHog capture to resume confirm endpoint**

In `backend/app/resumes/router.py` → the confirm endpoint (the function that handles `POST /api/resumes/confirm`), add the PostHog capture after the resume record is created and committed:

```python
from app.shared.posthog_events import RESUME_UPLOADED

# After resume is created and committed to DB:
posthog_client.capture(
    distinct_id=str(current_user.user_id),
    event=RESUME_UPLOADED,
    properties={
        "resume_id": str(resume.id),
        "file_name": resume.file_name,
        "file_type": resume.file_name.rsplit(".", 1)[-1].lower() if "." in resume.file_name else "unknown",
        "file_size_bytes": file_size_bytes,  # from blob or request
        "page_count": page_count,  # from extract_text_from_pdf if PDF, else None
        "current_page_context": "candidate_create_profile",
    },
)
```

Also add to `backend/app/shared/posthog_events.py`:
```python
RESUME_UPLOADED = "Resume Uploaded"
```

---

### 2c. Resume Upload Failed

Backend rejects the resume upload due to validation failure.

| Field | Value |
|-------|-------|
| **Event** | `Resume Upload Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Resume Upload Button Clicked) |
| **Trigger** | Backend rejects file during presign or confirm (bad format, corrupt, too large, text extraction fails) |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `file_type` | string or null | `pdf`, `doc`, `docx`, `txt`, or the attempted extension | Format of rejected file |
| `file_size_bytes` | number or null | e.g., `15000000` | Size of rejected file |
| `error_reason` | string | e.g., `File too large. Maximum size is 10 MB`, `Unsupported file type: exe`, `File content does not match .pdf format`, `Could not extract text from file` | Backend error message |
| `error_category` | enum | `size_limit`, `unsupported_format`, `corrupt_file`, `extraction_failed` | Classification |
| `current_page_context` | string | `candidate_create_profile` | Page context |

**Existing backend error responses (from `resumes/router.py` and `users/router.py`):**

| Error Message | `error_category` |
|---|---|
| `File too large. Maximum size is 10 MB` | `size_limit` |
| `Unsupported file type: {ext}. Supported: doc, docx, pdf, txt` | `unsupported_format` |
| `Unsupported content type: {content_type}` | `unsupported_format` |
| `File content does not match .{ext} format — file may be corrupted or renamed` | `corrupt_file` |
| `Could not extract text from file` | `extraction_failed` |

**Helix codebase change:**

In `backend/app/resumes/router.py`, in the exception handlers where `BadRequestException` is raised for file validation failures, add PostHog capture:

```python
from app.shared.posthog_events import RESUME_UPLOAD_FAILED

# In each validation failure catch block:
posthog_client.capture(
    distinct_id=str(current_user.user_id),
    event=RESUME_UPLOAD_FAILED,
    properties={
        "file_type": ext if ext else None,
        "file_size_bytes": file_size_bytes if file_size_bytes else None,
        "error_reason": str(e),
        "error_category": "unsupported_format",  # or size_limit, corrupt_file, extraction_failed
        "current_page_context": "candidate_create_profile",
    },
)
```

Also add to `backend/app/shared/posthog_events.py`:
```python
RESUME_UPLOAD_FAILED = "Resume Upload Failed"
```

---

### 3. Resume Removed

User clicks "Remove" to delete their uploaded resume.

| Field | Value |
|-------|-------|
| **Event** | `Resume Removed` |
| **Area** | Prospect |
| **Type** | -- |
| **Trigger** | User clicks "Remove" link on the resume section |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `remove_resume` | Button text in snake_case |
| `resume_id` | string | UUID | Which resume was removed |
| `file_type` | string | `pdf`, `doc`, `docx`, `txt` | Format of removed file |
| `file_size_bytes` | number | e.g., `245000` | Size of removed file |
| `current_page_context` | string | `candidate_create_profile` or `candidate_editor_overview` | Page — fires wherever Remove is available |
| `component` | string | `create_profile_resume_section` or `editor_resume_section` | Section location varies by page |
| `entity_type` | string | `candidate_profile` | Business object context |

**PostHog call:**

```typescript
capture('Resume Removed', {
  action: 'click',
  action_value: 'remove_resume',
  resume_id: currentResume.id,
  file_type: currentResume.fileName.split('.').pop()?.toLowerCase(),
  file_size_bytes: currentResume.fileSizeBytes,
  current_page_context: 'candidate_create_profile',  // or 'candidate_editor_overview'
  component: 'create_profile_resume_section',          // or 'editor_resume_section'
  entity_type: 'candidate_profile',
});
```

**Helix codebase change:**

In `frontend/src/pages/candidate/CreateProfile.tsx` (or the component rendering the resume section), in the "Remove" button's click handler:

```typescript
// In the Remove button onClick handler, BEFORE calling the delete API
capture(RESUME_REMOVED, {
  action: 'click',
  action_value: 'remove_resume',
  resume_id: resume.id,
  file_type: resume.fileName.split('.').pop()?.toLowerCase(),
  file_size_bytes: resume.fileSizeBytes,  // if available in frontend state
  current_page_context: 'candidate_create_profile',
  component: 'create_profile_resume_section',
  entity_type: 'candidate_profile',
});
```

> **Note:** `file_size_bytes` may not be in the frontend state if the backend doesn't return it in `ResumeResponse`. Check if `ResumeResponse` includes file size — if not, drop this property or add it to the response schema.

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const RESUME_REMOVED = 'Resume Removed';
```

---

### 4a. Add Profile Photo Button Clicked

User clicks "Add profile image" to open the method selector (Take a photo / Upload a photo).

| Field | Value |
|-------|-------|
| **Event** | `Add Profile Photo Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Profile Photo Added) |
| **Trigger** | User clicks "Add profile image" link |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `add_profile_image_button` | Button text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_photo_section` | Section location |

**Helix codebase change:**

In the component that renders the "Add profile image" link (likely `frontend/src/components/HeadshotUpload.tsx` or similar), add capture in the click handler:

```typescript
capture(ADD_PROFILE_PHOTO_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'add_profile_image_button',
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
  component: 'create_profile_photo_section',
});
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const ADD_PROFILE_PHOTO_BUTTON_CLICKED = 'Add Profile Photo Button Clicked';
```

---

### 4b. Profile Photo Added

Photo is successfully uploaded and stored (via camera capture or file upload).

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Added` |
| **Area** | Prospect |
| **Type** | Success (for Add Profile Photo Button Clicked) |
| **Trigger** | Photo successfully saved to Azure Blob and `headshot_blob_path` updated |
| **Source** | Frontend (fires after confirm API returns success) |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | How the photo was added — "Take a photo" vs "Upload a photo" |
| `file_type` | string | `jpg`, `png`, `gif`, `webp` | Image format |
| `file_size_bytes` | number | e.g., `120000` | Image file size |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `entity_type` | string | `candidate_profile` | Business object context |

**PostHog call:**

```typescript
capture('Profile Photo Added', {
  upload_method: method,  // 'take_photo' or 'upload'
  file_type: file.type.split('/')[1],  // 'jpeg' → 'jpg' mapping needed
  file_size_bytes: file.size,
  current_page_context: 'candidate_create_profile',
  entity_type: 'candidate_profile',
});
```

**Helix codebase change:**

In `frontend/src/components/HeadshotUpload.tsx` (or the component handling photo upload), after the `POST /api/users/me/headshot/confirm` API call succeeds:

```typescript
// After headshot confirm API returns success:
capture(PROFILE_PHOTO_ADDED, {
  upload_method: isCameraCapture ? 'take_photo' : 'upload',
  file_type: fileExtension,
  file_size_bytes: file.size,
  current_page_context: 'candidate_create_profile',
  entity_type: 'candidate_profile',
});
```

> **Note:** The component needs to track whether the photo came from camera (`Take a photo`) or file picker (`Upload a photo`). This may require passing a flag through the upload flow.

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const PROFILE_PHOTO_ADDED = 'Profile Photo Added';
```

---

### 4c. Profile Photo Upload Failed

Photo upload rejected by backend or frontend validation.

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Upload Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Add Profile Photo Button Clicked) |
| **Trigger** | File too large (backend: 15MB, frontend: 5MB), unsupported format, or upload error |
| **Source** | Frontend (for size check) or Backend (for presign/confirm failure) |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | Which method was attempted |
| `file_size_bytes` | number or null | e.g., `20000000` | Size of rejected file |
| `error_reason` | string | e.g., `Image too large. Maximum size is 5 MB.`, `File too large. Maximum size is 15 MB` | Error message |
| `error_category` | enum | `size_limit`, `unsupported_format`, `upload_error` | Classification |
| `current_page_context` | string | `candidate_create_profile` | Page |

**Existing validation points:**
- Frontend (`HeadshotUpload.tsx`): 5MB limit → `Image too large. Maximum size is 5 MB.`
- Backend presign (`users/router.py`): 15MB limit → `File too large. Maximum size is 15 MB`

**Helix codebase change:**

In `frontend/src/components/HeadshotUpload.tsx`, in the validation failure handler (where `setUploadError` is called):

```typescript
capture(PROFILE_PHOTO_UPLOAD_FAILED, {
  upload_method: isCameraCapture ? 'take_photo' : 'upload',
  file_size_bytes: file.size,
  error_reason: 'Image too large. Maximum size is 5 MB.',
  error_category: 'size_limit',
  current_page_context: 'candidate_create_profile',
});
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const PROFILE_PHOTO_UPLOAD_FAILED = 'Profile Photo Upload Failed';
```

---

### 5. Profile Photo Removed

User removes their profile photo.

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Removed` |
| **Area** | Prospect |
| **Type** | -- |
| **Trigger** | User clicks "Remove" on their profile photo |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `remove_profile_photo` | Button text in snake_case |
| `current_page_context` | string | `candidate_create_profile` or `candidate_editor_overview` | Page — fires wherever option is available |
| `component` | string | `create_profile_photo_section` or `editor_photo_modal` | UI location |
| `entity_type` | string | `candidate_profile` | Business object context |

**Notes:**
- No `photo_id` available — the backend only stores `headshot_blob_path` (a string path, not a separate entity with an ID)
- Fires on both create-profile page and editor page (different `current_page_context` and `component`)
- On create-profile: "Remove" link next to the photo
- On editor: "Remove" option in the "Change Profile Photo" modal (no "Take a photo" option on editor — only "Change" and "Remove")

**Helix codebase change:**

In `frontend/src/components/HeadshotUpload.tsx` (or wherever the Remove button handler lives), capture before calling the remove API:

```typescript
capture(PROFILE_PHOTO_REMOVED, {
  action: 'click',
  action_value: 'remove_profile_photo',
  current_page_context: pageContext,  // 'candidate_create_profile' or 'candidate_editor_overview'
  component: componentContext,         // 'create_profile_photo_section' or 'editor_photo_modal'
  entity_type: 'candidate_profile',
});
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const PROFILE_PHOTO_REMOVED = 'Profile Photo Removed';
```

---

### 8a. Build Profile Button Clicked

User clicks "Build my AI profile" — the submit CTA. This is a pure user action event. Profile state is captured separately in event 8b.

| Field | Value |
|-------|-------|
| **Event** | `Build Profile Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Candidate Profile Created) |
| **Trigger** | User clicks "Build my AI profile →" button |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `build_my_ai_profile_button` | Exact CTA text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_footer_cta` | Button location |

**PostHog call:**

```typescript
capture('Build Profile Button Clicked', {
  action: 'click',
  action_value: 'build_my_ai_profile_button',
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
  component: 'create_profile_footer_cta',
});
```

**Helix codebase change:**

In `frontend/src/pages/candidate/CreateProfile.tsx`, in the "Build my AI profile" button's click handler, BEFORE initiating the API call:

```typescript
capture(BUILD_PROFILE_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'build_my_ai_profile_button',
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
  component: 'create_profile_footer_cta',
});
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const BUILD_PROFILE_BUTTON_CLICKED = 'Build Profile Button Clicked';
```

---

### 8b. Profile Build Snapshot

Captures the full state of what the user provided before AI profile generation starts. Fires immediately after `Build Profile Button Clicked`, before the backend call.

| Field | Value |
|-------|-------|
| **Event** | `Profile Build Snapshot` |
| **Area** | Prospect |
| **Type** | -- (state capture, not an action) |
| **Trigger** | Fires programmatically immediately after Build Profile Button Clicked, before backend API call |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `has_resume` | boolean | `true`/`false` | Did the user upload a resume? |
| `resume_id` | string or null | UUID | Resume ID if uploaded |
| `resume_file_type` | string or null | `pdf`, `doc`, `docx`, `txt` | Resume format if uploaded |
| `resume_page_count` | number or null | e.g., `2` | PDF page count if available |
| `has_photo` | boolean | `true`/`false` | Did the user add a profile photo? |
| `photo_upload_method` | enum or null | `take_photo`, `upload` | How the photo was added (null if no photo) |
| `links_count` | number | e.g., `2` | Total links added |
| `link_types` | array | `['github', 'linkedin']` | All platform types of added links |
| `current_page_context` | string | `candidate_create_profile` | Page |

**PostHog call:**

```typescript
capture('Profile Build Snapshot', {
  has_resume: !!resume,
  resume_id: resume?.id ?? null,
  resume_file_type: resume ? resume.fileName.split('.').pop()?.toLowerCase() : null,
  resume_page_count: resume?.pageCount ?? null,
  has_photo: !!headshotBlobPath,
  photo_upload_method: photoMethod ?? null,  // tracked in component state
  links_count: userLinks.length,
  link_types: userLinks.map(l => l.linkType),
  current_page_context: 'candidate_create_profile',
});
```

**Helix codebase change:**

Same handler as `Build Profile Button Clicked`, fired immediately after it:

```typescript
// Step 1: Fire click event
capture(BUILD_PROFILE_BUTTON_CLICKED, { ... });

// Step 2: Fire state snapshot
capture(PROFILE_BUILD_SNAPSHOT, {
  has_resume: !!resume,
  resume_id: resume?.id ?? null,
  resume_file_type: resume ? resume.fileName.split('.').pop()?.toLowerCase() : null,
  resume_page_count: resume?.pageCount ?? null,
  has_photo: !!user.headshotBlobPath,
  photo_upload_method: photoUploadMethod,
  links_count: userLinks.length,
  link_types: userLinks.map(l => l.linkType),
  current_page_context: 'candidate_create_profile',
});

// Step 3: Call backend API to generate profile
await createPortfolio({ resumeId: resume.id });
```

Also add to `frontend/src/lib/posthogEvents.ts`:
```typescript
export const PROFILE_BUILD_SNAPSHOT = 'Profile Build Snapshot';
```

> **Note:** `photo_upload_method` requires the component to track how the photo was added (camera vs upload) in local state. This state needs to survive until the "Build my AI profile" click. Use a `useState` or store value set during the photo upload flow.

---

### 8c. Candidate Profile Created

Backend successfully generates the AI profile from the resume. **Replaces** the existing `Profile Created` event with richer properties.

| Field | Value |
|-------|-------|
| **Event** | `Candidate Profile Created` |
| **Area** | Prospect |
| **Type** | Success (for Build Profile Button Clicked) |
| **Trigger** | Backend successfully generates portfolio from resume via `POST /api/portfolios` |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string | UUID | Generated portfolio identifier |
| `resume_id` | string or null | UUID | Resume used for generation |
| `input_method` | enum | `resume_upload` | How the profile was created (matches existing property, extensible for future `linkedin_import`) |
| `has_resume` | boolean | `true`/`false` | Was a resume used? |
| `has_photo` | boolean | `true`/`false` | Did the user have a profile photo at creation time? |
| `links_count` | number | e.g., `2` | Total external links on the user's profile |
| `link_types` | array | `['github', 'linkedin']` | Platform types of user's links |
| `current_page_context` | string | `candidate_create_profile` | Page context |

**Helix codebase change:**

In `backend/app/portfolio/router.py` → the `create_portfolio()` endpoint (the function handling `POST /api/portfolios`), **replace** the existing `Profile Created` capture:

```python
# REMOVE existing:
posthog_client.capture(
    current_user.id,
    PROFILE_CREATED,
    {PROP_SURFACE: SURFACE_PROSPECT, "portfolio_id": portfolio.id, "input_method": "resume_upload"},
)

# REPLACE WITH:
from app.shared.posthog_events import CANDIDATE_PROFILE_CREATED

# Query user's links for the snapshot
user_links = await db.execute(
    select(UserLink).where(UserLink.user_id == current_user.user_id, UserLink.is_deleted == False)
)
links = user_links.scalars().all()

posthog_client.capture(
    distinct_id=str(current_user.user_id),
    event=CANDIDATE_PROFILE_CREATED,
    properties={
        "portfolio_id": str(portfolio.id),
        "resume_id": str(resume.id) if resume else None,
        "input_method": "resume_upload",
        "has_resume": resume is not None,
        "has_photo": bool(current_user.headshot_blob_path),
        "links_count": len(links),
        "link_types": [link.link_type for link in links],
        "current_page_context": "candidate_create_profile",
    },
)
```

Also update `backend/app/shared/posthog_events.py`:
```python
# REMOVE or comment out:
# PROFILE_CREATED = "Profile Created"

# ADD:
CANDIDATE_PROFILE_CREATED = "Candidate Profile Created"
```

> **Impact of replacing `Profile Created`:** The existing constant `PROFILE_CREATED` is used in `portfolio/router.py` (line 127). No other backend files reference it. The frontend defines it in `posthogEvents.ts` (line 50) but does NOT capture it anywhere — it's backend-only. Safe to replace.

---

### 8d. Candidate Profile Creation Failed

Backend fails to generate the AI profile.

| Field | Value |
|-------|-------|
| **Event** | `Candidate Profile Creation Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Build Profile Button Clicked) |
| **Trigger** | Backend exception during portfolio generation |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string or null | UUID | Resume that was used |
| `error_reason` | string | Error message (truncated to 256 chars) | What went wrong |
| `error_category` | enum | `ai_generation`, `server`, `timeout` | Classification |
| `current_page_context` | string | `candidate_create_profile` | Page context |

**Helix codebase change:**

In `backend/app/portfolio/router.py` → the `create_portfolio()` endpoint, add a try/except around the portfolio generation logic:

```python
from app.shared.posthog_events import CANDIDATE_PROFILE_CREATION_FAILED

try:
    portfolio = await service.create_portfolio(...)
    # ... capture Candidate Profile Created (above)
except Exception as e:
    posthog_client.capture(
        distinct_id=str(current_user.user_id),
        event=CANDIDATE_PROFILE_CREATION_FAILED,
        properties={
            "resume_id": str(resume_id) if resume_id else None,
            "error_reason": str(e)[:256],
            "error_category": "ai_generation",  # or "server", "timeout" depending on exception type
            "current_page_context": "candidate_create_profile",
        },
    )
    raise  # re-raise to return error to frontend
```

Also add to `backend/app/shared/posthog_events.py`:
```python
CANDIDATE_PROFILE_CREATION_FAILED = "Candidate Profile Creation Failed"
```

---

## New Events Summary

| Event | Area | Type | Trigger | Source | Properties | Group | Status |
|-------|------|------|---------|--------|------------|-------|--------|
| `Resume Upload Button Clicked` | Prospect | Intent | User clicks resume upload area | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | Not Started |
| `Resume Uploaded` | Prospect | Success | Backend confirms resume stored | Backend | `resume_id`, `file_name`, `file_type`, `file_size_bytes`, `page_count`, `current_page_context` | -- | Not Started |
| `Resume Upload Failed` | Prospect | Failure | Backend rejects resume | Backend | `file_type`, `file_size_bytes`, `error_reason`, `error_category`, `current_page_context` | -- | Not Started |
| `Resume Removed` | Prospect | -- | User clicks Remove on resume | Frontend | `action`, `action_value`, `resume_id`, `file_type`, `file_size_bytes`, `current_page_context`, `component`, `entity_type` | -- | Not Started |
| `Add Profile Photo Button Clicked` | Prospect | Intent | User clicks Add profile image | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | Not Started |
| `Profile Photo Added` | Prospect | Success | Photo saved successfully | Frontend | `upload_method`, `file_type`, `file_size_bytes`, `current_page_context`, `entity_type` | -- | Not Started |
| `Profile Photo Upload Failed` | Prospect | Failure | Photo rejected (size/format) | Frontend/Backend | `upload_method`, `file_size_bytes`, `error_reason`, `error_category`, `current_page_context` | -- | Not Started |
| `Profile Photo Removed` | Prospect | -- | User clicks Remove on photo | Frontend | `action`, `action_value`, `current_page_context`, `component`, `entity_type` | -- | Not Started |
| `Build Profile Button Clicked` | Prospect | Intent | User clicks "Build my AI profile" | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | Not Started |
| `Profile Build Snapshot` | Prospect | -- | State capture before AI generation | Frontend | `has_resume`, `resume_id`, `resume_file_type`, `resume_page_count`, `has_photo`, `photo_upload_method`, `links_count`, `link_types`, `current_page_context` | -- | Not Started |
| `Candidate Profile Created` | Prospect | Success | Backend generates portfolio | Backend | `portfolio_id`, `resume_id`, `input_method`, `has_resume`, `has_photo`, `links_count`, `link_types`, `current_page_context` | -- | Not Started |
| `Candidate Profile Creation Failed` | Prospect | Failure | Backend portfolio generation fails | Backend | `resume_id`, `error_reason`, `error_category`, `current_page_context` | -- | Not Started |

---

## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Resume Upload | Resume Upload Button Clicked | Resume Uploaded | Resume Upload Failed |
| Profile Photo | Add Profile Photo Button Clicked | Profile Photo Added | Profile Photo Upload Failed |
| Profile Creation | Build Profile Button Clicked | Candidate Profile Created | Candidate Profile Creation Failed |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Onboarding → Profile Creation | Account Created → Intro Completed → Page Viewed (create_profile) → Build Profile Button Clicked → Candidate Profile Created | End-to-end new user conversion from signup to AI profile |
| Resume Upload Conversion | Resume Upload Button Clicked → Resume Uploaded | % of users who start upload and succeed |
| Profile Photo Adoption | Add Profile Photo Button Clicked → Profile Photo Added | % of users who add a photo |
| Profile Completeness at Creation | Profile Build Snapshot (filter by has_resume=true, has_photo=true, links_count>0) | % of users who provide all optional items |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string (UUID) | e.g., `a1b2c3d4-...` | Resume identifier from `Resume.id` |
| `file_name` | string | e.g., `One Page Resume.pdf` | Original uploaded filename |
| `file_type` | string | `pdf`, `doc`, `docx`, `txt` | File format extension |
| `file_size_bytes` | number | e.g., `245000` | File size in bytes |
| `page_count` | number or null | e.g., `2` | PDF page count (null for non-PDF) |
| `upload_method` | enum | `take_photo`, `upload` | How profile photo was added |
| `has_resume` | boolean | `true`, `false` | Whether user uploaded a resume |
| `has_photo` | boolean | `true`, `false` | Whether user added a profile photo |
| `photo_upload_method` | enum or null | `take_photo`, `upload` | How photo was added (null if no photo) |
| `links_count` | number | e.g., `2` | Total external links |
| `link_types` | array of strings | `['github', 'linkedin']` | Platform types of added links |
| `portfolio_id` | string (UUID) | e.g., `x1y2z3-...` | Generated portfolio identifier |
| `error_reason` | string | Error message text | What went wrong (truncated to 256 chars on backend) |
| `error_category` | enum | `size_limit`, `unsupported_format`, `corrupt_file`, `extraction_failed`, `ai_generation`, `server`, `timeout`, `upload_error` | Error classification |

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

### `docs/event-catalog.md`

**Prospect Persona Events table — replace existing event:**

| Remove | Add | Notes |
|--------|-----|-------|
| `Profile Created` with `input_method` | `Candidate Profile Created` with `portfolio_id`, `resume_id`, `input_method`, `has_resume`, `has_photo`, `links_count`, `link_types` | Renamed + enriched. Same trigger point, richer properties. |

**Prospect Persona Events table — add new events:**

All 11 new events listed in the New Events Summary table above should be inserted into the Prospect Persona Events section.

**Property Dictionary updates:**

| Section | Property | Change |
|---------|----------|--------|
| Enum | `section` | Change allowed values from `summary, experience, skills, timeline` to `summary, skills, journey, experience, education`. `journey` = the whole timeline section, `experience` = individual work entry edit, `education` = individual education entry edit. Remove `timeline`. |
| Enum | `input_method` | Add to Used In: `Candidate Profile Created` (was: `Profile Created`) |
| Enum | `error_category` | Add values: `size_limit`, `unsupported_format`, `corrupt_file`, `extraction_failed`, `ai_generation`, `upload_error`. Add to Used In: `Resume Upload Failed`, `Profile Photo Upload Failed`, `Candidate Profile Creation Failed` |
| Enum | `upload_method` | New property. Values: `take_photo`, `upload`. Used In: `Profile Photo Added`, `Profile Photo Upload Failed` |
| Enum | `file_type` | New property. Values: `pdf`, `doc`, `docx`, `txt`, `jpg`, `png`, `gif`, `webp`. Used In: `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`, `Profile Photo Added` |
| Boolean | `has_resume` | New property. Used In: `Profile Build Snapshot`, `Candidate Profile Created` |
| Boolean | `has_photo` | New property. Used In: `Profile Build Snapshot`, `Candidate Profile Created` |
| String | `resume_id` | New property. Used In: `Resume Uploaded`, `Resume Removed`, `Profile Build Snapshot`, `Candidate Profile Created`, `Candidate Profile Creation Failed` |
| String | `file_name` | New property. Used In: `Resume Uploaded` |
| String | `portfolio_id` | New property. Used In: `Candidate Profile Created` |
| Numeric | `file_size_bytes` | New property. Used In: `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`, `Profile Photo Added`, `Profile Photo Upload Failed` |
| Numeric | `page_count` | New property. Description: `PDF page count (null for non-PDF)`. Used In: `Resume Uploaded` |
| Numeric | `links_count` | New property. Used In: `Profile Build Snapshot`, `Candidate Profile Created` |

**Removed Events table — add:**

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|--------------|
| Profile Created | Candidate Profile Created | Enriched with resume, photo, and link state; same trigger point | June 2026 |

### `docs/event-schema.md`

**Standard Objects table — add:**

| Object | Entity | Example Events |
|--------|--------|---------------|
| Resume | User's uploaded resume document | Resume Upload Button Clicked, Resume Uploaded, Resume Upload Failed, Resume Removed |
| Profile Photo | User's profile headshot image | Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed |
| Profile Build | AI profile generation process | Build Profile Button Clicked, Profile Build Snapshot, Candidate Profile Created, Candidate Profile Creation Failed |

**Standard Objects table — update:**

| Object | Change |
|--------|--------|
| Profile | Update example events: `Candidate Profile Created, Profile Section Updated` (was: `Profile Created, Profile Section Updated`) |

**Standard Event Properties — `entity_type`:**

Current description lists: `account`, `onboarding`, `job`, `persona`, etc. Add `candidate_profile` as a valid value for job seeker profile setup events.

### `docs/dashboards.md`

**Prospect Dashboard — add funnels:**

| Funnel | Steps |
|--------|-------|
| Onboarding → Profile Creation | `Account Created → Intro Completed → Page Viewed (candidate_create_profile) → Build Profile Button Clicked → Candidate Profile Created` |
| Resume Upload Conversion | `Resume Upload Button Clicked → Resume Uploaded` |

---

## Helix Code Changes Summary

| File | Change | Events Affected |
|------|--------|----------------|
| `frontend/src/lib/posthogEvents.ts` | Add 8 new event constants | All new frontend events |
| `frontend/src/pages/candidate/CreateProfile.tsx` | Add `Page Viewed` on mount, capture handlers for resume/photo/build actions | Page Viewed, Build Profile Button Clicked, Profile Build Snapshot |
| `frontend/src/pages/ResumeUpload.tsx` (or resume component) | Add capture for upload button click | Resume Upload Button Clicked |
| `frontend/src/components/HeadshotUpload.tsx` | Add capture for photo button click, photo added, photo failed, photo removed | Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed |
| `frontend/src/pages/candidate/PortfolioEditor.tsx` | Remove `surface: SURFACE_PROSPECT` from existing `Profile Section Updated` captures. Add new captures with `section: 'experience'` in the experience edit form save handler and `section: 'education'` in the education edit form save handler (both inside the Journey edit modal). | Profile Section Updated (experience, education) |
| `backend/app/shared/posthog_events.py` | Add 4 new event constants, remove/replace `PROFILE_CREATED`. Remove `PROP_SURFACE`, `SURFACE_PROSPECT`, `SURFACE_HIRING` constants (after confirming no other usages). | All new backend events |
| `backend/app/users/router.py` | In `create_link()`: replace `PROP_SURFACE: SURFACE_PROSPECT` with `PROP_CURRENT_PERSONA: get_current_persona(user.role)` on `Custom Link Created` capture | Custom Link Created (surface → current_persona migration) |
| `backend/app/portfolio/router.py` | Replace `Profile Created` capture with `Candidate Profile Created`, add failure capture. On `Profile Link Viewed`: remove `PROP_SURFACE` (anonymous event, no persona applies). | Candidate Profile Created, Candidate Profile Creation Failed, Profile Link Viewed |
| `backend/app/resumes/router.py` | Add capture on confirm success and validation failures | Resume Uploaded, Resume Upload Failed |
| `backend/app/session_runtime/services/resume_parser.py` | Modify `extract_text_from_pdf()` to return `(text, page_count)` tuple | Resume Uploaded (page_count property) |

---

## Known Analytics Gaps (to address separately)

| Gap | Description | Severity |
|-----|-------------|----------|
| Profile link validation bug | User can select "GitHub" link type and paste a LinkedIn URL — frontend accepts it. Backend auto-detects type from domain but the UI doesn't enforce consistency. | Medium |
| No duplicate resume detection | Backend doesn't store file hash — can't detect re-uploads of the same file. | Low |
| `file_size_bytes` not in `ResumeResponse` | Frontend may not have file size after upload. Either add to response schema or capture from the File object before upload. | Low |
| `page_count` requires code change | `resume_parser.py` needs to return page count — currently discards it. Small change but touches parsing pipeline. | Low |
| `photo_upload_method` state tracking | Frontend needs to remember whether photo came from camera or upload until the "Build my AI profile" click. Requires a `useState` or store value. | Low |
