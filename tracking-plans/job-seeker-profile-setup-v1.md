# Tracking Plan: Job Seeker Profile Setup

**Product:** Helix (SeekOut.ai)
**Feature:** Job seeker profile setup — resume upload, photo, links, AI profile generation (`/candidate/create-profile`)
**Date:** 2026-06-02 (drafted) · 2026-06-03 (updated to match implementation)
**Related PRD:** —
**Scope:** v1 — Create Profile page events only. Editor (B) and Dashboard (C) events deferred to v2.
**Status:** Implementation complete — pending tracking plan merge

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.
>
> This is the production implementation reference for the job seeker profile setup analytics. It covers 13 new events across the resume upload, profile photo, and AI profile creation flows on `/candidate/create-profile`, plus modifications to 6 existing events (surface removal, Custom Link rename, Profile Section Updated enum fix). Each event includes the exact property schema, file paths, and capture call code for the Helix codebase.

---

## Implementation Decisions

During implementation, several decisions were made that differ from the original tracking plan:

| Decision | Rationale |
|----------|-----------|
| Resume properties prefixed with `resume_` (`resume_name`, `resume_file_type`, `resume_size_bytes`) instead of generic names (`file_name`, `file_type`, `file_size_bytes`) | Namespace clarity — avoids collision with photo events that also have `file_type` and `file_size_bytes` |
| Backend events omit `current_page_context` | Backend doesn't know which page triggered the request; frontend events already carry page context |
| Standalone `extract_page_count()` function instead of modifying `extract_text_from_pdf()` return type | Avoids breaking 6+ existing callers of `extract_text_from_pdf()` |
| Page count extended to DOCX and TXT (not just PDF) | More comprehensive analytics at minimal cost |
| Page count stored in `extracted` JSONB, not a new column | Avoids a DB migration for one analytics-only property |
| `Custom Link Created` renamed to `Custom Link Added` | Better describes the action (user adds a link to their profile, not "creates" one) |
| `LinkedIn Export Learn How Clicked` event added | Captures intent signal for users interested in LinkedIn PDF import |
| `entry_point` dropped from Page Viewed on create-profile | Not meaningful — users arrive via a single onboarding flow |
| `resume_size_bytes` dropped from Resume Removed | Frontend state doesn't carry file size after upload |
| `action_value` on Resume Upload Button Clicked uses `drop_resume_here_or_click_to_upload` | Matches exact UI text in snake_case per naming conventions |

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
       │    ├─ User clicks "Remove" → fires: Resume Removed
       │    └─ User clicks "Learn how" (LinkedIn export) → fires: LinkedIn Export Learn How Clicked
       │
       ├─ Profile photo section
       │    ├─ User opens photo menu → fires: Add Profile Photo Button Clicked
       │    ├─ Photo successfully added → fires: Profile Photo Added
       │    ├─ Photo upload fails → fires: Profile Photo Upload Failed
       │    └─ User clicks "Remove" on photo → fires: Profile Photo Removed
       │
       └─ Submit
            ├─ User clicks "Build my AI profile" → fires: Build Profile Button Clicked
            ├─ State snapshot captured → fires: Build Profile Snapshot
            ├─ AI generates profile → fires: Candidate Profile Created
            └─ AI generation fails → fires: Candidate Profile Creation Failed
```

---

## Existing Events (reused, no changes needed)

These events already fire in the Helix codebase and are documented in `docs/event-catalog.md`. No modifications required.

| Event | Status | File | Notes |
|-------|--------|------|-------|
| `Page Viewed` | Live | `RoleSelection.tsx`, `ValueProp.tsx` | Already fires on `/onboarding/role` and `/onboarding/intro`. New page context added to `/candidate/create-profile` — see Section 1 below. |
| `Account Created` | Live | `RoleSelection.tsx` → `handleContinue()` | Fires when user clicks "Continue as candidate". Properties match catalog. |
| `Intro Completed` | Live | `ValueProp.tsx` → `handleContinue()` | Fires when user clicks "Let's go". Properties match catalog. |

---

## Existing Event Modifications

These existing events were modified as part of this implementation.

### `Profile Created` → replaced by `Candidate Profile Created`

The existing `Profile Created` event in `backend/app/portfolio/router.py` → `create_portfolio()` has been **replaced** by `Candidate Profile Created` (event 5c below) with richer properties.

**Removed from `backend/app/shared/posthog_events.py`:**
```python
PROFILE_CREATED = "Profile Created"
```

**Removed from `frontend/src/lib/posthogEvents.ts`:**
```typescript
export const PROFILE_CREATED = 'Profile Created';
```

### `Custom Link Created` → renamed to `Custom Link Added`

Event renamed and `surface` property replaced with `current_persona`.

**`backend/app/shared/posthog_events.py`:**
```python
# REMOVED:
CUSTOM_LINK_CREATED = "Custom Link Created"
# ADDED:
CUSTOM_LINK_ADDED = "Custom Link Added"
```

**`frontend/src/lib/posthogEvents.ts`:**
```typescript
// REMOVED:
export const CUSTOM_LINK_CREATED = 'Custom Link Created';
// ADDED:
export const CUSTOM_LINK_ADDED = 'Custom Link Added';
```

**`backend/app/users/router.py` → `create_link()`:**
```python
# BEFORE:
posthog_client.capture(
    current_user.id,
    CUSTOM_LINK_CREATED,
    {PROP_SURFACE: SURFACE_PROSPECT, "link_type": link.link_type, "link_name": link.display_name, "is_job_specific": False},
)

# AFTER:
posthog_client.capture(
    current_user.id,
    CUSTOM_LINK_ADDED,
    {PROP_CURRENT_PERSONA: get_current_persona(current_user.role), "link_type": link.link_type, "link_name": link.display_name, "is_job_specific": False},
)
```

### `Profile Section Updated` — `surface` removed, new `section` values added

**`frontend/src/pages/candidate/PortfolioEditor.tsx`:**

Removed `surface: SURFACE_PROSPECT` from all three existing captures:
```typescript
// BEFORE:
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'summary' });
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'skills' });
capture(PROFILE_SECTION_UPDATED, { surface: SURFACE_PROSPECT, section: 'journey' });

// AFTER:
capture(PROFILE_SECTION_UPDATED, { section: 'summary' });
capture(PROFILE_SECTION_UPDATED, { section: 'skills' });
capture(PROFILE_SECTION_UPDATED, { section: 'journey' });
```

**`frontend/src/components/portfolio/JourneyEditDialog.tsx`:**

Added two new captures for per-entry saves:
```typescript
// In saveExperienceDetail handler, after successful save:
capture(PROFILE_SECTION_UPDATED, { section: 'experience' });

// In saveEducationDetail handler, after successful save:
capture(PROFILE_SECTION_UPDATED, { section: 'education' });
```

**Updated `section` enum values:** `summary`, `skills`, `journey`, `experience`, `education` (removed `timeline`)

### `Profile Link Viewed` — `surface` removed

**`backend/app/portfolio/router.py` → `get_public_portfolio()`:**
```python
# Removed PROP_SURFACE: SURFACE_PROSPECT from the capture properties
posthog_client.capture(
    f"anonymous_{handle}",
    PROFILE_LINK_VIEWED,
    {
        "profile_user_id": data["user_id"],
        "custom_link_id": ref,
        "is_authenticated": False,
    },
)
```

### `Profile Link Engaged` — `surface` removed from frontend

**`frontend/src/pages/public/PublicPortfolio.tsx`:**

Removed `surface: SURFACE_PROSPECT` from all `PROFILE_LINK_ENGAGED` captures (view_full_profile, download_resume, share_dialog_open, share_clicked).

### `Custom Link Shared` — `surface` removed from frontend

**`frontend/src/components/portfolio/ShareModal.tsx`:**

Removed `surface: SURFACE_PROSPECT` from the `CUSTOM_LINK_SHARED` capture.

### `SURFACE_PROSPECT` constant — removal status

After all surface references were removed from capture calls, the `SURFACE_PROSPECT` import was removed from:
- `frontend/src/pages/candidate/PortfolioEditor.tsx`
- `frontend/src/pages/public/PublicPortfolio.tsx`
- `frontend/src/components/portfolio/ShareModal.tsx`
- `backend/app/portfolio/router.py`

> **Migration caution:** Before removing `PROP_SURFACE` / `SURFACE_PROSPECT` / `SURFACE_HIRING` constants entirely from the Helix codebase:
> 1. Search for `PROP_SURFACE`, `SURFACE_PROSPECT`, `SURFACE_HIRING` across all frontend and backend files to confirm no other events use them
> 2. Check PostHog for any saved insights, dashboards, or cohorts filtering on the `surface` property — migrate them to `current_persona` first
> 3. Only then remove the constants from `posthog_events.py` and `posthogEvents.ts`

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Resume Upload | Prospect resume upload flow | Resume Upload Button Clicked, Resume Upload Failed |
| Resume | Prospect resume document | Resume Uploaded, Resume Removed |
| Profile Photo | Prospect profile photo | Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed, Add Profile Photo Button Clicked |
| LinkedIn Export | LinkedIn export help link | LinkedIn Export Learn How Clicked |
| Build Profile | AI profile generation process | Build Profile Button Clicked, Build Profile Snapshot |
| Candidate Profile | AI-generated candidate profile | Candidate Profile Created, Candidate Profile Creation Failed |

## New Events

### 1. Page Viewed (new page context)

The existing `Page Viewed` event fires on `/candidate/create-profile`. This is not a new event — just a new page context.

| Field | Value |
|-------|-------|
| **Event** | `Page Viewed` (existing) |
| **Area** | Navigation |
| **Type** | page_view |
| **Trigger** | User lands on the "Build your profile" page |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `candidate_create_profile` | Page identifier |
| `previous_page_context` | string | snake_case or null | Previous page (typically `onboarding_intro`) |

**Implementation:**

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`
**Location:** `useEffect` on component mount

```typescript
import { capture } from '@/lib/posthog';
import { PAGE_VIEWED, rotatePageContext } from '@/lib/posthogEvents';

useEffect(() => {
  const previousPageContext = rotatePageContext('candidate_create_profile');
  capture(PAGE_VIEWED, {
    current_page_context: 'candidate_create_profile',
    previous_page_context: previousPageContext,
  });
}, []);
```

> **Note:** Uses `rotatePageContext()` which both reads the previous page context AND sets the current one for the next navigation. This is the standard pattern used across Helix page components.

---

### 2a. Resume Upload Button Clicked

User clicks the resume upload area to open the file picker. This is the **intent** event.

| Field | Value |
|-------|-------|
| **Event** | `Resume Upload Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Resume Uploaded) |
| **Trigger** | User clicks the upload area/button in the resume section |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `drop_resume_here_or_click_to_upload` | Exact UI text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_resume_section` | Section within the page |

**Implementation:**

**File:** `frontend/src/components/ResumeDropzone.tsx`
**Location:** `openFileDialog()` callback, before `fileInputRef.current?.click()`

```typescript
import { capture } from '@/lib/posthog';
import { RESUME_UPLOAD_BUTTON_CLICKED, getPreviousPageContext } from '@/lib/posthogEvents';

const openFileDialog = useCallback(() => {
  if (!isUploadDisabled) {
    capture(RESUME_UPLOAD_BUTTON_CLICKED, {
      action: 'click',
      action_value: 'drop_resume_here_or_click_to_upload',
      current_page_context: 'candidate_create_profile',
      previous_page_context: getPreviousPageContext(),
      entity_type: 'candidate_profile',
      component: 'create_profile_resume_section',
    });
    fileInputRef.current?.click();
  }
}, [isUploadDisabled]);
```

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const RESUME_UPLOAD_BUTTON_CLICKED = 'Resume Upload Button Clicked';
```
```python
# backend/app/shared/posthog_events.py
RESUME_UPLOAD_BUTTON_CLICKED = "Resume Upload Button Clicked"
```

---

### 2b. Resume Uploaded

Backend confirms the resume was successfully uploaded, validated, and stored.

| Field | Value |
|-------|-------|
| **Event** | `Resume Uploaded` |
| **Area** | Prospect |
| **Type** | Success (for Resume Upload Button Clicked) |
| **Trigger** | Backend successfully stores resume after validation |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string | UUID | Resume identifier from `Resume.id` |
| `resume_name` | string | e.g., `One Page Resume.pdf` | Original filename |
| `resume_file_type` | string | `pdf`, `doc`, `docx`, `txt` | File format (from extension) |
| `resume_size_bytes` | number | e.g., `245000` | File size in bytes |
| `page_count` | number or null | e.g., `2` | Page count (PDF native, DOCX via page breaks, TXT estimated at ~3000 chars/page; null for .doc or on error) |

**Implementation:**

This event fires from **two** backend endpoints:

**Endpoint 1:** `POST /api/resumes/confirm` (presign flow)

**File:** `backend/app/resumes/router.py`
**Location:** `confirm_resume_upload()`, after resume record is created and committed

```python
from app.shared import posthog_client
from app.shared.posthog_events import RESUME_UPLOADED

posthog_client.capture(
    current_user.id,
    RESUME_UPLOADED,
    {
        "resume_id": str(resume.id),
        "resume_name": filename,
        "resume_file_type": ext,
        "resume_size_bytes": len(file_bytes),
        "page_count": extracted_dict.get("page_count"),
    },
)
```

**Endpoint 2:** `POST /api/users/me/resume` (direct upload flow)

**File:** `backend/app/users/router.py`
**Location:** `upload_user_resume()`, after resume is persisted

```python
from app.session_runtime.services.resume_parser import extract_page_count

page_count = extract_page_count(io.BytesIO(file_bytes), filename)

posthog_client.capture(
    current_user.id,
    RESUME_UPLOADED,
    {
        "resume_id": str(resume.id),
        "resume_name": filename,
        "resume_file_type": ext,
        "resume_size_bytes": len(file_bytes),
        "page_count": page_count,
    },
)
```

**Constants:**
```python
# backend/app/shared/posthog_events.py
RESUME_UPLOADED = "Resume Uploaded"
```
```typescript
// frontend/src/lib/posthogEvents.ts
export const RESUME_UPLOADED = 'Resume Uploaded';
```

---

### 2c. Resume Upload Failed

Backend rejects the resume upload due to validation failure.

| Field | Value |
|-------|-------|
| **Event** | `Resume Upload Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Resume Upload Button Clicked) |
| **Trigger** | Backend rejects file during presign or confirm |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_file_type` | string or null | `pdf`, `doc`, `docx`, `txt`, or the attempted extension | Format of rejected file |
| `resume_size_bytes` | number or null | e.g., `15000000` | Size of rejected file (null at presign stage where bytes aren't yet available) |
| `error_reason` | string | Backend error message | What went wrong |
| `error_category` | enum | `unsupported_format`, `extraction_failed`, `invalid_magic_bytes` | Classification |

**Error responses and categories:**

| Error Message | `error_category` | Endpoint(s) |
|---|---|---|
| `Unsupported file type: {ext}. Supported: doc, docx, pdf, txt` | `unsupported_format` | presign, confirm, direct upload |
| `Unsupported content type: {content_type}` | `unsupported_format` | presign |
| `Failed to extract text: {error}` | `extraction_failed` | confirm, direct upload |
| `Could not extract text from file` | `extraction_failed` | confirm, direct upload |
| Magic byte validation failure message | `invalid_magic_bytes` | direct upload |

**Implementation:**

This event fires from **two** backend files across multiple error paths:

**File 1:** `backend/app/resumes/router.py`
**Locations:** `presign_resume_upload()` (2 error paths) and `confirm_resume_upload()` (3 error paths)

```python
from app.shared import posthog_client
from app.shared.posthog_events import RESUME_UPLOAD_FAILED

# Example — unsupported extension at presign:
error_msg = f"Unsupported file type: {ext}. Supported: {', '.join(sorted(_RESUME_EXTS))}"
posthog_client.capture(
    current_user.id,
    RESUME_UPLOAD_FAILED,
    {"resume_file_type": ext or None, "resume_size_bytes": None, "error_reason": error_msg, "error_category": "unsupported_format"},
)
raise BadRequestException(error_msg)

# Example — text extraction failure at confirm:
error_msg = f"Failed to extract text: {str(e)}"
posthog_client.capture(
    current_user.id,
    RESUME_UPLOAD_FAILED,
    {"resume_file_type": ext or None, "resume_size_bytes": len(file_bytes), "error_reason": error_msg, "error_category": "extraction_failed"},
)
raise BadRequestException(error_msg)
```

**File 2:** `backend/app/users/router.py`
**Location:** `upload_user_resume()` — 4 error paths (bad extension, magic bytes, extraction failure, empty text)

```python
# Example — magic byte validation failure:
posthog_client.capture(
    current_user.id,
    RESUME_UPLOAD_FAILED,
    {"resume_file_type": ext or None, "resume_size_bytes": len(file_bytes), "error_reason": magic_err, "error_category": "invalid_magic_bytes"},
)
raise BadRequestException(magic_err)
```

**Constants:**
```python
# backend/app/shared/posthog_events.py
RESUME_UPLOAD_FAILED = "Resume Upload Failed"
```
```typescript
// frontend/src/lib/posthogEvents.ts
export const RESUME_UPLOAD_FAILED = 'Resume Upload Failed';
```

---

### 2d. Resume Removed

User clicks "Remove" to delete their uploaded resume.

| Field | Value |
|-------|-------|
| **Event** | `Resume Removed` |
| **Area** | Prospect |
| **Type** | -- |
| **Trigger** | User clicks "Remove" link on the resume section |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `remove_resume` | Button text in snake_case |
| `resume_id` | string or null | UUID | Which resume was removed (resolved from state or API) |
| `resume_file_type` | string or null | `pdf`, `doc`, `docx`, `txt` | Format of removed file |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `component` | string | `create_profile_resume_section` | Section location |
| `entity_type` | string | `candidate_profile` | Business object context |

**Implementation:**

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`
**Location:** `handleRemoveResume()`, before calling the delete API

```typescript
import { capture } from '@/lib/posthog';
import { RESUME_REMOVED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleRemoveResume = async () => {
  let effectiveResumeId = resumeId;
  if (!effectiveResumeId) {
    try {
      const resumes = await listResumes();
      effectiveResumeId = (resumes.find((r) => r.isDefault) ?? resumes[0])?.id ?? null;
    } catch {
      effectiveResumeId = null;
    }
  }
  capture(RESUME_REMOVED, {
    action: 'click',
    action_value: 'remove_resume',
    resume_id: effectiveResumeId,
    resume_file_type: resumeFileName?.split('.').pop()?.toLowerCase() ?? null,
    current_page_context: 'candidate_create_profile',
    previous_page_context: getPreviousPageContext(),
    component: 'create_profile_resume_section',
    entity_type: 'candidate_profile',
  });
  // ... then calls deleteUserResume() ...
};
```

> **Note:** `resume_id` is resolved by checking local state first, then falling back to an API call if needed. This ensures the ID is captured even when the component state doesn't have it directly.

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const RESUME_REMOVED = 'Resume Removed';
```
```python
# backend/app/shared/posthog_events.py
RESUME_REMOVED = "Resume Removed"
```

---

### 3. LinkedIn Export Learn How Clicked

User clicks the "Learn how" link to see instructions for exporting their LinkedIn profile as a PDF. This event was **not in the original tracking plan** — it was added during implementation as a useful intent signal.

| Field | Value |
|-------|-------|
| **Event** | `LinkedIn Export Learn How Clicked` |
| **Area** | Prospect |
| **Type** | -- |
| **Trigger** | User clicks "Learn how" link in the LinkedIn export tip below the resume upload area |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `learn_how_export_linkedin_pdf` | Link text context in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_resume_section` | Section location |

**Implementation:**

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`
**Location:** `onClick` handler on the "Learn how" `<a>` tag

```typescript
import { capture } from '@/lib/posthog';
import { LINKEDIN_EXPORT_LEARN_HOW_CLICKED, getPreviousPageContext } from '@/lib/posthogEvents';

<a
  href="..."
  target="_blank"
  rel="noopener noreferrer"
  className="..."
  onClick={() => capture(LINKEDIN_EXPORT_LEARN_HOW_CLICKED, {
    action: 'click',
    action_value: 'learn_how_export_linkedin_pdf',
    current_page_context: 'candidate_create_profile',
    previous_page_context: getPreviousPageContext(),
    entity_type: 'candidate_profile',
    component: 'create_profile_resume_section',
  })}
>
  Learn how
  <ArrowRight className="size-4" aria-hidden="true" />
</a>
```

**Constant (frontend only — no backend constant):**
```typescript
// frontend/src/lib/posthogEvents.ts
export const LINKEDIN_EXPORT_LEARN_HOW_CLICKED = 'LinkedIn Export Learn How Clicked';
```

---

### 4a. Add Profile Photo Button Clicked

User opens the photo action menu (Take a photo / Upload a photo).

| Field | Value |
|-------|-------|
| **Event** | `Add Profile Photo Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Profile Photo Added) |
| **Trigger** | User opens the photo dropdown menu |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `add_profile_image_button` | Button text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_photo_section` | Section location |

**Implementation:**

**File:** `frontend/src/components/HeadshotUpload.tsx`
**Location:** `DropdownMenu` `onOpenChange` handler (fires when menu opens)

```typescript
import { capture } from '@/lib/posthog';
import { ADD_PROFILE_PHOTO_BUTTON_CLICKED, getPreviousPageContext } from '@/lib/posthogEvents';

<DropdownMenu
  onOpenChange={(open) => {
    if (open) {
      if (document.activeElement instanceof HTMLElement) {
        cameraTriggerRef.current = document.activeElement;
      }
      capture(ADD_PROFILE_PHOTO_BUTTON_CLICKED, {
        action: 'click',
        action_value: 'add_profile_image_button',
        current_page_context: 'candidate_create_profile',
        previous_page_context: getPreviousPageContext(),
        entity_type: 'candidate_profile',
        component: 'create_profile_photo_section',
      });
    }
  }}
>
```

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const ADD_PROFILE_PHOTO_BUTTON_CLICKED = 'Add Profile Photo Button Clicked';
```
```python
# backend/app/shared/posthog_events.py
ADD_PROFILE_PHOTO_BUTTON_CLICKED = "Add Profile Photo Button Clicked"
```

---

### 4b. Profile Photo Added

Photo successfully uploaded and stored (via camera capture or file upload).

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Added` |
| **Area** | Prospect |
| **Type** | Success (for Add Profile Photo Button Clicked) |
| **Trigger** | Photo successfully saved after upload/camera capture |
| **Source** | Frontend (fires after confirm API returns success) |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | How the photo was added — "Take a photo" vs "Upload a photo" |
| `file_type` | string | `jpg`, `png`, `gif`, `webp` | Image format |
| `file_size_bytes` | number | e.g., `120000` | Image file size |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |

**Implementation:**

**File:** `frontend/src/components/HeadshotUpload.tsx`
**Location:** `handleFile()` callback, after `uploadHeadshot()` and `refreshProfile()` succeed

```typescript
import { capture } from '@/lib/posthog';
import { PROFILE_PHOTO_ADDED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleFile = useCallback(async (file: File, method: 'take_photo' | 'upload' = 'upload') => {
  // ... validation ...
  try {
    await uploadHeadshot(file);
    await refreshProfile();
    capture(PROFILE_PHOTO_ADDED, {
      upload_method: method,
      file_type: ext,
      file_size_bytes: file.size,
      current_page_context: 'candidate_create_profile',
      previous_page_context: getPreviousPageContext(),
      entity_type: 'candidate_profile',
    });
    onUploadMethodChange?.(method);  // propagates to CreateProfile for snapshot
    onChangeComplete?.();
    return true;
  } catch { ... }
}, [onChangeComplete, onUploadMethodChange, preview, refreshProfile]);
```

> **Camera vs upload:** When the camera captures a photo, `handleFile` is called with `method: 'take_photo'`:
> ```typescript
> // In capturePhoto callback:
> const file = new File([blob], 'profile-photo.jpg', { type: 'image/jpeg' });
> await handleFile(file, 'take_photo');
> ```

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const PROFILE_PHOTO_ADDED = 'Profile Photo Added';
```
```python
# backend/app/shared/posthog_events.py
PROFILE_PHOTO_ADDED = "Profile Photo Added"
```

---

### 4c. Profile Photo Upload Failed

Photo upload rejected by frontend validation.

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Upload Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Add Profile Photo Button Clicked) |
| **Trigger** | File too large (5MB frontend limit) or unsupported format |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | Which method was attempted |
| `file_size_bytes` | number | e.g., `20000000` | Size of rejected file |
| `error_reason` | string | Error message | What went wrong |
| `error_category` | enum | `size_limit`, `unsupported_format` | Classification |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |

**Validation points and error messages:**

| Error Message | `error_category` |
|---|---|
| `Unsupported image type. Use JPG, PNG, GIF, or WebP.` | `unsupported_format` |
| `Image too large. Maximum size is 5 MB.` | `size_limit` |

**Implementation:**

**File:** `frontend/src/components/HeadshotUpload.tsx`
**Location:** `handleFile()` callback, in validation checks before upload

```typescript
import { capture } from '@/lib/posthog';
import { PROFILE_PHOTO_UPLOAD_FAILED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleFile = useCallback(async (file: File, method: 'take_photo' | 'upload' = 'upload') => {
  const ext = file.name.toLowerCase().split('.').pop();
  if (!ACCEPTED_IMAGE_EXTENSIONS.includes(ext ?? '')) {
    const errorMsg = 'Unsupported image type. Use JPG, PNG, GIF, or WebP.';
    capture(PROFILE_PHOTO_UPLOAD_FAILED, {
      upload_method: method,
      file_size_bytes: file.size,
      error_reason: errorMsg,
      error_category: 'unsupported_format',
      current_page_context: 'candidate_create_profile',
      previous_page_context: getPreviousPageContext(),
      entity_type: 'candidate_profile',
    });
    setUploadError(errorMsg);
    return false;
  }
  if (file.size > 5 * 1024 * 1024) {
    const errorMsg = 'Image too large. Maximum size is 5 MB.';
    capture(PROFILE_PHOTO_UPLOAD_FAILED, {
      upload_method: method,
      file_size_bytes: file.size,
      error_reason: errorMsg,
      error_category: 'size_limit',
      current_page_context: 'candidate_create_profile',
      previous_page_context: getPreviousPageContext(),
      entity_type: 'candidate_profile',
    });
    setUploadError(errorMsg);
    return false;
  }
  // ... proceed with upload ...
}, [...]);
```

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const PROFILE_PHOTO_UPLOAD_FAILED = 'Profile Photo Upload Failed';
```
```python
# backend/app/shared/posthog_events.py
PROFILE_PHOTO_UPLOAD_FAILED = "Profile Photo Upload Failed"
```

---

### 4d. Profile Photo Removed

User removes their profile photo.

| Field | Value |
|-------|-------|
| **Event** | `Profile Photo Removed` |
| **Area** | Prospect |
| **Type** | -- |
| **Trigger** | User clicks "Remove" on their profile photo |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `remove_profile_photo` | Button text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `component` | string | `create_profile_photo_section` | UI location |
| `entity_type` | string | `candidate_profile` | Business object context |

**Implementation:**

**File:** `frontend/src/components/HeadshotUpload.tsx`
**Location:** `handleRemove()`, before calling `deleteHeadshot()`

```typescript
import { capture } from '@/lib/posthog';
import { PROFILE_PHOTO_REMOVED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleRemove = async () => {
  capture(PROFILE_PHOTO_REMOVED, {
    action: 'click',
    action_value: 'remove_profile_photo',
    current_page_context: 'candidate_create_profile',
    previous_page_context: getPreviousPageContext(),
    component: 'create_profile_photo_section',
    entity_type: 'candidate_profile',
  });
  setRemoving(true);
  try {
    await deleteHeadshot();
    // ...
    onUploadMethodChange?.(null);  // resets photo method for snapshot
    onChangeComplete?.();
  } catch { ... }
};
```

> **Note on editor page:** The current implementation hardcodes `candidate_create_profile` and `create_profile_photo_section`. Editor page support (with `candidate_editor_overview` and `editor_photo_modal`) is deferred to v2.

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const PROFILE_PHOTO_REMOVED = 'Profile Photo Removed';
```
```python
# backend/app/shared/posthog_events.py
PROFILE_PHOTO_REMOVED = "Profile Photo Removed"
```

---

### 5a. Build Profile Button Clicked

User clicks "Build my AI profile" — the submit CTA. This is a pure user action event. Profile state is captured separately in event 5b.

| Field | Value |
|-------|-------|
| **Event** | `Build Profile Button Clicked` |
| **Area** | Prospect |
| **Type** | Intent (for Candidate Profile Created) |
| **Trigger** | User clicks "Build my AI profile →" button |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `build_my_ai_profile_button` | Exact CTA text in snake_case |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |
| `component` | string | `create_profile_footer_cta` | Button location |

**Implementation:**

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`
**Location:** `handleCreateProfile()`, at the top of the handler before any async work

```typescript
import { capture } from '@/lib/posthog';
import { BUILD_PROFILE_BUTTON_CLICKED, getPreviousPageContext } from '@/lib/posthogEvents';

const handleCreateProfile = async () => {
  if (!resumeFileName || headshotBusy) return;

  capture(BUILD_PROFILE_BUTTON_CLICKED, {
    action: 'click',
    action_value: 'build_my_ai_profile_button',
    current_page_context: 'candidate_create_profile',
    previous_page_context: getPreviousPageContext(),
    entity_type: 'candidate_profile',
    component: 'create_profile_footer_cta',
  });

  setSaving(true);
  // ... rest of handler ...
};
```

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const BUILD_PROFILE_BUTTON_CLICKED = 'Build Profile Button Clicked';
```
```python
# backend/app/shared/posthog_events.py
BUILD_PROFILE_BUTTON_CLICKED = "Build Profile Button Clicked"
```

---

### 5b. Build Profile Snapshot

Captures the full state of what the user provided before AI profile generation starts. Fires after `Build Profile Button Clicked` and resume validation, but before the backend API call.

| Field | Value |
|-------|-------|
| **Event** | `Build Profile Snapshot` |
| **Area** | Prospect |
| **Type** | -- (state capture, not an action) |
| **Trigger** | Fires programmatically after Build Profile Button Clicked, after resume validation, before backend API call |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `has_resume` | boolean | `true`/`false` | Did the user upload a resume? |
| `resume_id` | string or null | UUID | Resume ID if uploaded |
| `resume_file_type` | string or null | `pdf`, `doc`, `docx`, `txt` | Resume format if uploaded |
| `resume_page_count` | number or null | e.g., `2` | Page count if available (from `ResumeDto.pageCount`) |
| `has_photo` | boolean | `true`/`false` | Did the user add a profile photo? |
| `photo_upload_method` | enum or null | `take_photo`, `upload` | How the photo was added (null if no photo) |
| `links_count` | number | e.g., `2` | Total links added |
| `link_types` | array | `['github', 'linkedin']` | All platform types of added links. Allowed values: `github`, `linkedin`, `portfolio`, `personal_website`, `other`. |
| `current_page_context` | string | `candidate_create_profile` | Page |
| `previous_page_context` | string | snake_case or null | Previous page |
| `entity_type` | string | `candidate_profile` | Business object context |

**Implementation:**

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`
**Location:** `handleCreateProfile()`, after resume validation passes, before `createPortfolio()` call

```typescript
import { capture } from '@/lib/posthog';
import { BUILD_PROFILE_SNAPSHOT, getPreviousPageContext } from '@/lib/posthogEvents';

// State tracked across the component:
const [photoUploadMethod, setPhotoUploadMethod] = useState<'take_photo' | 'upload' | null>(null);

// Inside handleCreateProfile, after defaultResume validation:
const resumeExt = resumeFileName?.split('.').pop()?.toLowerCase() ?? null;
capture(BUILD_PROFILE_SNAPSHOT, {
  has_resume: !!resumeFileName,
  resume_id: resumeId ?? defaultResume?.id ?? null,
  resume_file_type: resumeExt,
  resume_page_count: defaultResume?.pageCount ?? null,
  has_photo: !!user?.hasHeadshot,
  photo_upload_method: photoUploadMethod,
  links_count: allLinks.length,
  link_types: allLinks.map((l) => l.linkType),
  current_page_context: 'candidate_create_profile',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'candidate_profile',
});

const linkIds = allLinks.length > 0 ? allLinks.map((l) => l.id) : undefined;
const portfolio = await createPortfolio(defaultResume.id, { linkIds });
```

> **`photo_upload_method` tracking:** The `photoUploadMethod` state is set by `HeadshotUpload` via the `onUploadMethodChange` callback prop. It's set to `'take_photo'` or `'upload'` when a photo is added, and reset to `null` when a photo is removed.

> **`pageCount` availability:** The `defaultResume?.pageCount` value comes from the `ResumeDto` type, which includes a `pageCount` field derived from the backend's `ResumeResponse.page_count` (stored in `extracted` JSONB). See Supporting Infrastructure section.

**Constants:**
```typescript
// frontend/src/lib/posthogEvents.ts
export const BUILD_PROFILE_SNAPSHOT = 'Build Profile Snapshot';
```
```python
# backend/app/shared/posthog_events.py
BUILD_PROFILE_SNAPSHOT = "Build Profile Snapshot"
```

---

### 5c. Candidate Profile Created

Backend successfully generates the AI profile from the resume. **Replaces** the old `Profile Created` event with richer properties.

| Field | Value |
|-------|-------|
| **Event** | `Candidate Profile Created` |
| **Area** | Prospect |
| **Type** | Success (for Build Profile Button Clicked) |
| **Trigger** | Backend successfully generates portfolio via `POST /api/portfolios` |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `portfolio_id` | string | UUID | Generated portfolio identifier |
| `resume_id` | string or null | UUID | Resume used for generation |
| `input_method` | enum | `resume_upload` | How the profile was created (extensible for future `linkedin_import`) |
| `has_resume` | boolean | `true`/`false` | Was a resume used? |
| `has_photo` | boolean | `true`/`false` | Did the user have a profile photo at creation time? |
| `links_count` | number | e.g., `2` | Total external links on the user's profile |
| `link_types` | array | `['github', 'linkedin']` | Platform types of user's links. Allowed values: `github`, `linkedin`, `portfolio`, `personal_website`, `other`. |

**Implementation:**

**File:** `backend/app/portfolio/router.py`
**Location:** `create_portfolio()`, after portfolio is committed to DB

```python
from app.database.models.user_link import UserLink
from app.shared import posthog_client
from app.shared.posthog_events import CANDIDATE_PROFILE_CREATED

# Query user links after successful creation
user_links_result = await db.execute(
    select(UserLink).where(UserLink.user_id == current_user.id)
)
links = user_links_result.scalars().all()

posthog_client.capture(
    current_user.id,
    CANDIDATE_PROFILE_CREATED,
    {
        "portfolio_id": str(portfolio.id),
        "resume_id": dto.resume_id,
        "input_method": "resume_upload",
        "has_resume": dto.resume_id is not None,
        "has_photo": bool(current_user.headshot_blob_path),
        "links_count": len(links),
        "link_types": [link.link_type for link in links],
    },
)
```

> **Note:** UserLink rows are hard-deleted (DELETE endpoint), not soft-deleted. No `is_deleted` filter needed on the query.

**Constants:**
```python
# backend/app/shared/posthog_events.py
CANDIDATE_PROFILE_CREATED = "Candidate Profile Created"
```
```typescript
// frontend/src/lib/posthogEvents.ts
export const CANDIDATE_PROFILE_CREATED = 'Candidate Profile Created';
```

---

### 5d. Candidate Profile Creation Failed

Backend fails to generate the AI profile.

| Field | Value |
|-------|-------|
| **Event** | `Candidate Profile Creation Failed` |
| **Area** | Prospect |
| **Type** | Failure (for Build Profile Button Clicked) |
| **Trigger** | Backend exception during portfolio generation |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Implemented |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string or null | UUID | Resume that was used |
| `error_reason` | string | Error message (truncated to 256 chars) | What went wrong |
| `error_category` | enum | `ai_generation`, `server` | Classification |

**Implementation:**

**File:** `backend/app/portfolio/router.py`
**Location:** `create_portfolio()`, in except handlers wrapping the portfolio generation

```python
from app.shared import posthog_client
from app.shared.posthog_events import CANDIDATE_PROFILE_CREATION_FAILED

try:
    # ... portfolio generation ...
    await db.commit()
    await db.refresh(portfolio)
except ValueError as e:
    posthog_client.capture(
        current_user.id,
        CANDIDATE_PROFILE_CREATION_FAILED,
        {
            "resume_id": dto.resume_id,
            "error_reason": str(e)[:256],
            "error_category": "ai_generation",
        },
    )
    raise BadRequestException(str(e))
except Exception as e:
    posthog_client.capture(
        current_user.id,
        CANDIDATE_PROFILE_CREATION_FAILED,
        {
            "resume_id": dto.resume_id,
            "error_reason": str(e)[:256],
            "error_category": "server",
        },
    )
    raise
```

**Constants:**
```python
# backend/app/shared/posthog_events.py
CANDIDATE_PROFILE_CREATION_FAILED = "Candidate Profile Creation Failed"
```
```typescript
// frontend/src/lib/posthogEvents.ts
export const CANDIDATE_PROFILE_CREATION_FAILED = 'Candidate Profile Creation Failed';
```

---

## Supporting Infrastructure

### Page Count Extraction

**File:** `backend/app/session_runtime/services/resume_parser.py`

Two new functions added. The existing `extract_text_from_pdf()` is **NOT modified** — this avoids breaking its 6+ existing callers.

```python
def extract_pdf_page_count(file: BinaryIO) -> int | None:
    """Return the page count of a PDF file, or None for non-PDF / on error."""
    try:
        import fitz  # PyMuPDF
        content = file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return None


def extract_page_count(file: BinaryIO, filename: str) -> int | None:
    """Return the page count for any supported resume format, or None on error."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    try:
        if ext == "pdf":
            return extract_pdf_page_count(file)
        elif ext == "docx":
            from docx import Document
            doc = Document(file)
            body = doc.element.body
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            page_breaks = body.findall(".//w:lastRenderedPageBreak", ns)
            explicit_breaks = body.findall('.//w:br[@w:type="page"]', ns)
            return len(page_breaks) + len(explicit_breaks) + 1
        elif ext == "doc":
            return None  # python-docx doesn't support .doc
        elif ext == "txt":
            content = file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            return max(1, (len(content) + 2999) // 3000)  # ~3000 chars/page
        else:
            return None
    except Exception:
        return None
```

> **DOCX caveat:** `lastRenderedPageBreak` is only present if Word rendered the document. Files from Google Docs or LibreOffice may lack it, returning 1 regardless of actual length.

### Page Count in Resume Response

**Backend schema — File:** `backend/app/resumes/schemas.py`

```python
class ResumeResponse(BaseModel):
    # ... existing fields ...
    page_count: int | None = Field(default=None, serialization_alias="pageCount")
    # ... existing fields ...

    @model_validator(mode="after")
    def _derive_page_count_from_extracted(self) -> Self:
        """Derive page_count from extracted JSONB if not explicitly set."""
        if self.page_count is None and self.extracted:
            self.page_count = self.extracted.get("page_count")
        return self
```

**Frontend type — File:** `frontend/src/lib/portfolioApi.ts`

```typescript
export interface ResumeDto {
  // ... existing fields ...
  pageCount: number | null;
  // ... existing fields ...
}
```

### Page Count Storage in Confirm Endpoint

**File:** `backend/app/resumes/router.py` → `confirm_resume_upload()`

After text extraction, page count is extracted and stored in the `extracted` JSONB:

```python
extracted = await analyze_resume_with_gemini(raw_text)
extracted_dict = extracted.model_dump()

from app.session_runtime.services.resume_parser import extract_page_count
page_count = extract_page_count(io.BytesIO(file_bytes), filename)
if page_count is not None:
    extracted_dict["page_count"] = page_count

# extracted_dict (with page_count) is then stored in the Resume record
```

### Photo Upload Method Callback

**File:** `frontend/src/components/HeadshotUpload.tsx`

New prop added to communicate upload method to parent:
```typescript
interface HeadshotUploadProps {
  // ... existing props ...
  onUploadMethodChange?: (method: 'take_photo' | 'upload' | null) => void;
}
```

**File:** `frontend/src/pages/candidate/CreateProfile.tsx`

Parent tracks the method in state:
```typescript
const [photoUploadMethod, setPhotoUploadMethod] = useState<'take_photo' | 'upload' | null>(null);

// Passed to HeadshotUpload:
<HeadshotUpload
  // ...
  onUploadMethodChange={setPhotoUploadMethod}
/>
```

---

## New Events Summary

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|-------|------|---------|----------------|-------|------------------|
| Resume Upload Button Clicked | Prospect | User clicks resume upload area | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- |
| Resume Uploaded | Prospect | Backend confirms resume stored | `resume_id`, `resume_name`, `resume_file_type`, `resume_size_bytes`, `page_count` | -- | -- |
| Resume Upload Failed | Prospect | Backend rejects resume | `resume_file_type`, `resume_size_bytes`, `error_reason`, `error_category` | -- | -- |
| Resume Removed | Prospect | User clicks Remove on resume | `action`, `action_value`, `resume_id`, `resume_file_type`, `current_page_context`, `previous_page_context`, `component`, `entity_type` | -- | -- |
| LinkedIn Export Learn How Clicked | Prospect | User clicks "Learn how" link | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- |
| Add Profile Photo Button Clicked | Prospect | User opens photo action menu | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- |
| Profile Photo Added | Prospect | Photo saved successfully | `upload_method`, `file_type`, `file_size_bytes`, `current_page_context`, `previous_page_context`, `entity_type` | -- | -- |
| Profile Photo Upload Failed | Prospect | Photo rejected (size/format) | `upload_method`, `file_size_bytes`, `error_reason`, `error_category`, `current_page_context`, `previous_page_context`, `entity_type` | -- | -- |
| Profile Photo Removed | Prospect | User clicks Remove on photo | `action`, `action_value`, `current_page_context`, `previous_page_context`, `component`, `entity_type` | -- | -- |
| Build Profile Button Clicked | Prospect | User clicks "Build my AI profile" | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- |
| Build Profile Snapshot | Prospect | State capture before AI generation | `has_resume`, `resume_id`, `resume_file_type`, `resume_page_count`, `has_photo`, `photo_upload_method`, `links_count`, `link_types`, `current_page_context`, `previous_page_context`, `entity_type` | -- | -- |
| Candidate Profile Created | Prospect | Backend generates portfolio | `portfolio_id`, `resume_id`, `input_method`, `has_resume`, `has_photo`, `links_count`, `link_types` | -- | -- |
| Candidate Profile Creation Failed | Prospect | Backend portfolio generation fails | `resume_id`, `error_reason`, `error_category` | -- | -- |

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
| Onboarding → Profile Creation | Account Created → Intro Completed → Page Viewed → Build Profile Button Clicked → Candidate Profile Created | End-to-end new user conversion from signup to AI profile. Filter Page Viewed by `current_page_context` = `candidate_create_profile`. |
| Resume Upload Conversion | Resume Upload Button Clicked → Resume Uploaded | % of users who start upload and succeed |
| Profile Photo Adoption | Add Profile Photo Button Clicked → Profile Photo Added | % of users who add a photo |
| Profile Completeness at Creation | Build Profile Snapshot | Single-event funnel filtered by `has_resume` = true, `has_photo` = true, `links_count` > 0. Measures % providing all optional items. |

---

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `resume_id` | string | UUID | Resume identifier from `Resume.id` |
| `resume_name` | string | -- | Original uploaded filename |
| `resume_file_type` | string | pdf / doc / docx / txt | File format extension — used on resume events and Build Profile Snapshot |
| `resume_size_bytes` | number | -- | Resume file size in bytes |
| `resume_page_count` | number | -- | Resume page count in Build Profile Snapshot |
| `page_count` | number | -- | Page count: PDF native, DOCX via page breaks, TXT estimated. Null for .doc or on error. |
| `upload_method` | enum | take_photo / upload | How profile photo was added |
| `file_type` | string | jpg / png / gif / webp | Image format (photo events only) |
| `file_size_bytes` | number | -- | Image file size (photo events only) |
| `photo_upload_method` | enum | take_photo / upload | How photo was added — used in Build Profile Snapshot (null if no photo) |
| `has_resume` | boolean | true / false | Whether user uploaded a resume |
| `has_photo` | boolean | true / false | Whether user added a profile photo |
| `links_count` | number | -- | Total external links |
| `link_types` | array | github / linkedin / portfolio / personal_website / other | Platform types of added links |
| `portfolio_id` | string | UUID | Generated portfolio identifier |
| `input_method` | enum | resume_upload | How the profile was created |
| `error_reason` | string | -- | What went wrong (truncated to 256 chars on backend) |
| `error_category` | enum | unsupported_format / extraction_failed / invalid_magic_bytes / size_limit / ai_generation / server | Error classification |

**`error_category` values by event:**

| Value | Used In |
|---|---|
| `unsupported_format` | Resume Upload Failed, Profile Photo Upload Failed |
| `extraction_failed` | Resume Upload Failed |
| `invalid_magic_bytes` | Resume Upload Failed |
| `size_limit` | Profile Photo Upload Failed |
| `ai_generation` | Candidate Profile Creation Failed |
| `server` | Candidate Profile Creation Failed |

---

## Constants Reference

### Backend: `backend/app/shared/posthog_events.py`

```python
# Job Seeker Profile Setup v1
RESUME_UPLOAD_BUTTON_CLICKED = "Resume Upload Button Clicked"
RESUME_UPLOADED = "Resume Uploaded"
RESUME_UPLOAD_FAILED = "Resume Upload Failed"
RESUME_REMOVED = "Resume Removed"
ADD_PROFILE_PHOTO_BUTTON_CLICKED = "Add Profile Photo Button Clicked"
PROFILE_PHOTO_ADDED = "Profile Photo Added"
PROFILE_PHOTO_UPLOAD_FAILED = "Profile Photo Upload Failed"
PROFILE_PHOTO_REMOVED = "Profile Photo Removed"
BUILD_PROFILE_BUTTON_CLICKED = "Build Profile Button Clicked"
BUILD_PROFILE_SNAPSHOT = "Build Profile Snapshot"
CANDIDATE_PROFILE_CREATED = "Candidate Profile Created"
CANDIDATE_PROFILE_CREATION_FAILED = "Candidate Profile Creation Failed"

# Also changed:
CUSTOM_LINK_ADDED = "Custom Link Added"  # was CUSTOM_LINK_CREATED = "Custom Link Created"
# REMOVED: PROFILE_CREATED = "Profile Created"
```

### Frontend: `frontend/src/lib/posthogEvents.ts`

```typescript
// Job Seeker Profile Setup v1
export const RESUME_UPLOAD_BUTTON_CLICKED = 'Resume Upload Button Clicked';
export const RESUME_UPLOADED = 'Resume Uploaded';
export const RESUME_UPLOAD_FAILED = 'Resume Upload Failed';
export const RESUME_REMOVED = 'Resume Removed';
export const LINKEDIN_EXPORT_LEARN_HOW_CLICKED = 'LinkedIn Export Learn How Clicked';
export const ADD_PROFILE_PHOTO_BUTTON_CLICKED = 'Add Profile Photo Button Clicked';
export const PROFILE_PHOTO_ADDED = 'Profile Photo Added';
export const PROFILE_PHOTO_UPLOAD_FAILED = 'Profile Photo Upload Failed';
export const PROFILE_PHOTO_REMOVED = 'Profile Photo Removed';
export const BUILD_PROFILE_BUTTON_CLICKED = 'Build Profile Button Clicked';
export const BUILD_PROFILE_SNAPSHOT = 'Build Profile Snapshot';
export const CANDIDATE_PROFILE_CREATED = 'Candidate Profile Created';
export const CANDIDATE_PROFILE_CREATION_FAILED = 'Candidate Profile Creation Failed';

// Also changed:
export const CUSTOM_LINK_ADDED = 'Custom Link Added';  // was CUSTOM_LINK_CREATED
// REMOVED: export const PROFILE_CREATED = 'Profile Created';
```

> **Note:** Backend has 12 new constants, frontend has 13 (includes `LINKEDIN_EXPORT_LEARN_HOW_CLICKED` which is frontend-only).

---

## Catalog & Schema Updates Required on `/merge-tracking-plan`

### `docs/event-catalog.md`

**Prospect Persona Events table — replace existing events:**

| Remove | Add | Notes |
|--------|-----|-------|
| `Profile Created` with `input_method` | `Candidate Profile Created` with `portfolio_id`, `resume_id`, `input_method`, `has_resume`, `has_photo`, `links_count`, `link_types` | Renamed + enriched. Same trigger point, richer properties. |
| `Custom Link Created` with `link_name`, `is_job_specific`, `target_job_title`, `target_company` | `Custom Link Added` with `current_persona`, `link_type`, `link_name`, `is_job_specific`, `target_job_title`, `target_company` | Renamed. Properties updated: `surface` → `current_persona`; remove stale `Custom Link Created` references from schema and Property Dictionary. |

**Prospect Persona Events table — add new events:**

All 13 new events listed in the New Events Summary table above should be inserted into the Prospect Persona Events section.

**Property Dictionary updates:**

| Section | Property | Change |
|---------|----------|--------|
| Enum | `section` | Change allowed values from `summary, experience, skills, timeline` to `summary, skills, journey, experience, education`. Remove `timeline`. |
| Enum | `input_method` | Update Used In: `Candidate Profile Created` (was: `Profile Created`) |
| Enum | `error_category` | Append new values to existing enum: `unsupported_format`, `extraction_failed`, `invalid_magic_bytes`, `size_limit`, `ai_generation`. (`server` already exists — no change needed.) Append to Used In: `Resume Upload Failed`, `Profile Photo Upload Failed`, `Candidate Profile Creation Failed` |
| Enum | `upload_method` | New property. Values: `take_photo`, `upload`. Used In: `Profile Photo Added`, `Profile Photo Upload Failed` |
| Enum | `resume_file_type` | New property. Values: `pdf`, `doc`, `docx`, `txt`. Used In: `Resume Uploaded`, `Resume Upload Failed`, `Resume Removed`, `Build Profile Snapshot` |
| Enum | `file_type` | New property (photo events). Values: `jpg`, `png`, `gif`, `webp`. Used In: `Profile Photo Added` |
| Boolean | `has_resume` | Already exists (Used In: `Interest Expressed`). Append to Used In: `Build Profile Snapshot`, `Candidate Profile Created` |
| Boolean | `has_photo` | New property. Used In: `Build Profile Snapshot`, `Candidate Profile Created` |
| Boolean | `is_job_specific` | Existing property. Replace Used In: `Custom Link Created` → `Custom Link Added`; keep `Custom Link Shared`. |
| String | `resume_id` | New property. Used In: `Resume Uploaded`, `Resume Removed`, `Build Profile Snapshot`, `Candidate Profile Created`, `Candidate Profile Creation Failed` |
| String | `resume_name` | New property. Used In: `Resume Uploaded` |
| String | `portfolio_id` | New property. Used In: `Candidate Profile Created` |
| Enum | `link_type` | New property. Values: `general`, `job_specific`. Used In: `Custom Link Added`. |
| String | `link_name` | Existing property. Replace Used In: `Custom Link Created` → `Custom Link Added`. |
| String | `target_job_title` | Existing property. Replace Used In: `Custom Link Created` → `Custom Link Added`. |
| String | `target_company` | Existing property. Replace Used In: `Custom Link Created` → `Custom Link Added`. |
| Numeric | `resume_size_bytes` | New property. Used In: `Resume Uploaded`, `Resume Upload Failed` |
| Numeric | `file_size_bytes` | New property (photo events). Used In: `Profile Photo Added`, `Profile Photo Upload Failed` |
| Numeric | `page_count` | New property. Description: `Page count (PDF native, DOCX via page breaks, TXT estimated; null for .doc or on error)`. Used In: `Resume Uploaded` |
| Numeric | `links_count` | New property. Used In: `Build Profile Snapshot`, `Candidate Profile Created` |
| Numeric | `resume_page_count` | New property. Description: `Resume page count in Build Profile Snapshot`. Used In: `Build Profile Snapshot` |
| Array | `link_types` | New property. Values: `github`, `linkedin`, `portfolio`, `personal_website`, `other`. Description: `Platform types of added links`. Used In: `Build Profile Snapshot`, `Candidate Profile Created` |
| Enum | `photo_upload_method` | New property. Values: `take_photo`, `upload`. Description: `How photo was added (null if no photo) — snapshot only`. Used In: `Build Profile Snapshot` |

**Property Dictionary — update "Used In" for existing properties:**

| Property | Append to "Used In" |
|----------|---------------------|
| `action` (user_action) | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Removed, Build Profile Button Clicked |
| `action_value` | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Removed, Build Profile Button Clicked |
| `current_page_context` | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed, Build Profile Button Clicked, Build Profile Snapshot |
| `previous_page_context` | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed, Build Profile Button Clicked, Build Profile Snapshot |
| `entity_type` | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed, Build Profile Button Clicked, Build Profile Snapshot |
| `current_persona` | Custom Link Added |
| `component` | Resume Upload Button Clicked, Resume Removed, LinkedIn Export Learn How Clicked, Add Profile Photo Button Clicked, Profile Photo Removed, Build Profile Button Clicked |
| `error_reason` | Resume Upload Failed, Profile Photo Upload Failed, Candidate Profile Creation Failed |

**Removed Events table — add:**

| Old Event | Replaced By | Why | Removed Date |
|-----------|-------------|-----|--------------|
| Profile Created | Candidate Profile Created | Enriched with resume, photo, and link state; same trigger point | June 2026 |
| Custom Link Created | Custom Link Added | Renamed for clearer action wording; properties updated from `surface` to `current_persona` | June 2026 |

### `docs/event-schema.md`

**Standard Objects table — add:**

| Object | Entity | Example Events |
|--------|--------|---------------|
| Resume Upload | User's resume upload flow | Resume Upload Button Clicked, Resume Upload Failed |
| Resume | User's uploaded resume document | Resume Uploaded, Resume Removed |
| Profile Photo | User's profile headshot image | Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed |
| LinkedIn Export | LinkedIn export help link | LinkedIn Export Learn How Clicked |
| Build Profile | AI profile generation process | Build Profile Button Clicked, Build Profile Snapshot |
| Candidate Profile | Job seeker's AI-generated career profile | Candidate Profile Created, Candidate Profile Creation Failed |

**Standard Objects table — update:**

| Object | Change |
|--------|--------|
| Profile | Remove `Profile Created` from example events (replaced by `Candidate Profile Created` under new Candidate Profile object). Resulting examples: `Profile Section Updated` |
| Custom Link | Replace `Custom Link Created` with `Custom Link Added`. Resulting examples: `Custom Link Added`, `Custom Link Shared` |

**Standard Event Properties — `entity_type`:**

Add `candidate_profile` as a valid value for job seeker profile setup events.

**Intent vs Outcome table — add new flows:**

| Flow | Intent Event | Success Event | Failure Event |
|------|-------------|---------------|---------------|
| Resume upload | Resume Upload Button Clicked | Resume Uploaded | Resume Upload Failed |
| Profile photo | Add Profile Photo Button Clicked | Profile Photo Added | Profile Photo Upload Failed |
| Profile creation | Build Profile Button Clicked | Candidate Profile Created | Candidate Profile Creation Failed |

### `docs/dashboards.md`

**Prospect Dashboard — append to bullet list:**

- Onboarding → Profile Creation funnel: `Account Created` → `Intro Completed` → `Page Viewed` (candidate_create_profile) → `Build Profile Button Clicked` → `Candidate Profile Created`
- Resume upload conversion: `Resume Upload Button Clicked` → `Resume Uploaded`
- Profile photo adoption rate: `Add Profile Photo Button Clicked` → `Profile Photo Added`
- Profile completeness at creation: `Build Profile Snapshot` filtered by `has_resume` = true, `has_photo` = true, `links_count` > 0

---

## Helix Code Changes Summary

| File | Change | Events Affected |
|------|--------|----------------|
| `frontend/src/lib/posthogEvents.ts` | Add 13 new event constants, rename `CUSTOM_LINK_CREATED` → `CUSTOM_LINK_ADDED`, remove `PROFILE_CREATED` | All |
| `frontend/src/pages/candidate/CreateProfile.tsx` | Add `Page Viewed` on mount, `Build Profile Button Clicked`, `Build Profile Snapshot`, `Resume Removed`, `LinkedIn Export Learn How Clicked` captures. Track `photoUploadMethod` state via `onUploadMethodChange` prop. | Page Viewed, Build Profile Button Clicked, Build Profile Snapshot, Resume Removed, LinkedIn Export Learn How Clicked |
| `frontend/src/components/ResumeDropzone.tsx` | Add `Resume Upload Button Clicked` capture in `openFileDialog()` | Resume Upload Button Clicked |
| `frontend/src/components/HeadshotUpload.tsx` | Add `onUploadMethodChange` prop. Add captures for photo add/fail/remove. Pass `method` param through `handleFile()`. | Add Profile Photo Button Clicked, Profile Photo Added, Profile Photo Upload Failed, Profile Photo Removed |
| `frontend/src/pages/candidate/PortfolioEditor.tsx` | Remove `surface: SURFACE_PROSPECT` from `Profile Section Updated` captures (summary, skills, journey) | Profile Section Updated |
| `frontend/src/components/portfolio/JourneyEditDialog.tsx` | Add `Profile Section Updated` captures with `section: 'experience'` and `section: 'education'` in per-entry save handlers | Profile Section Updated |
| `frontend/src/components/portfolio/ShareModal.tsx` | Remove `surface: SURFACE_PROSPECT` from `Custom Link Shared` | Custom Link Shared |
| `frontend/src/pages/public/PublicPortfolio.tsx` | Remove `surface: SURFACE_PROSPECT` from all `Profile Link Engaged` captures | Profile Link Engaged |
| `frontend/src/lib/portfolioApi.ts` | Add `pageCount` field to `ResumeDto` interface | Build Profile Snapshot (`resume_page_count` property) |
| `backend/app/shared/posthog_events.py` | Add 12 new event constants, rename `CUSTOM_LINK_CREATED` → `CUSTOM_LINK_ADDED`, remove `PROFILE_CREATED` | All backend events |
| `backend/app/portfolio/router.py` | Replace `Profile Created` with `Candidate Profile Created` (enriched). Add `Candidate Profile Creation Failed` in try/except. Remove `surface` from `Profile Link Viewed`. Query `UserLink` for link analytics. Import `UserLink` model. | Candidate Profile Created, Candidate Profile Creation Failed, Profile Link Viewed |
| `backend/app/resumes/router.py` | Add `Resume Uploaded` on confirm success. Add `Resume Upload Failed` on 5 validation error paths. Store page count in `extracted` JSONB via `extract_page_count()`. Import `posthog_client` and event constants. | Resume Uploaded, Resume Upload Failed |
| `backend/app/resumes/schemas.py` | Add `page_count` field to `ResumeResponse` with `@model_validator(mode="after")` to derive from `extracted` JSONB. Import `Self`, `model_validator`. | Resume Uploaded (supports `page_count`), Build Profile Snapshot (supports `resume_page_count`) |
| `backend/app/users/router.py` | Replace `surface` with `current_persona` on `Custom Link Added`. Add `Resume Uploaded` and `Resume Upload Failed` captures on direct upload endpoint (4 error paths + 1 success). Import `io`, `extract_page_count`, new event constants, `get_current_persona`. | Custom Link Added, Resume Uploaded, Resume Upload Failed |
| `backend/app/session_runtime/services/resume_parser.py` | Add `extract_pdf_page_count()` and `extract_page_count()` functions (PDF, DOCX, TXT support). No changes to existing functions. | Resume Uploaded (`page_count` property) |

---

## Known Analytics Gaps

| Gap | Description | Severity | Status |
|-----|-------------|----------|--------|
| Profile link validation bug | User can select "GitHub" link type and paste a LinkedIn URL — frontend accepts it | Medium | Open |
| No duplicate resume detection | Backend doesn't store file hash — can't detect re-uploads of the same file | Low | Open |
| `resume_size_bytes` not on Resume Removed | Frontend doesn't have file size in component state after upload — dropped from event | Low | Accepted |
| DOCX page count approximation | `lastRenderedPageBreak` only present if Word rendered the doc; Google Docs/LibreOffice exports may return 1 regardless of length | Low | Documented in code |
| `photo_upload_method` resets on page refresh | If user adds photo, refreshes the page, then clicks Build, `photo_upload_method` will be null in snapshot even though photo exists | Low | Accepted |
| Editor page photo/resume events hardcode create-profile context | Photo and resume events hardcode `candidate_create_profile` — editor page support (different `current_page_context` and `component` values) deferred to v2 | Low | Deferred to v2 |
| Backend 15MB presign limit not captured | Backend presign endpoint has a 15MB file size limit, but this error path doesn't capture `Resume Upload Failed` | Low | Open |
