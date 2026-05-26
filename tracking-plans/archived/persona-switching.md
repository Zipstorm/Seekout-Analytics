# Tracking Plan: Persona Switching

**Product:** Helix (SeekOut.ai)
**Feature:** Persona switching flow
**Date:** 2026-05-11 (updated 2026-05-20)
**Related PRD:** —

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## Implementation Status

**None of these changes have been implemented in the Helix codebase yet.** This tracking plan is the single source of truth. When feeding this file to the Helix codebase LLM, it should implement ALL changes described below from scratch.

### What needs to be implemented

| Area | Summary |
|---|---|
| **Backend: `activated_personas` column** | New JSONB column on `users` table via Alembic migration, wired through User model → AuthUser → UserResponse → service → router |
| **Backend: `ROLE_TO_PERSONA` mapping** | New mapping in `posthog_events.py` — `PROFESSIONAL` → `"job_seeker"` (separate from existing `_ROLE_TO_ACTING_AS`) |
| **Backend: `Persona Updated` event** | PostHog event fired from `users/router.py` on successful persona switch, with guard logic to skip onboarding |
| **Backend: `Persona Update Failed` event** | PostHog event fired from `users/router.py` on failed role-only PATCH |
| **Frontend: Rename switch event** | `Persona Switch Chevron Clicked` → `Switch Persona Button Clicked`, align properties, remove `Persona Switched` |
| **Frontend: `identifyUser()` fix** | Add `current_persona` to the `posthog.identify()` call so all users have this person property |

---

## User Flow

```text
User is on any page (e.g., HM Job Postings)
  │
  ├─ Step 1: Clicks ⇄ ArrowLeftRight icon next to current persona in sidebar
  │    → fires: Switch Persona Button Clicked (Frontend)
  │    → "Choose a role" dropdown opens
  │
  ├─ Step 2: Clicks on a different persona card (e.g., Recruiter)
  │    → Frontend calls PATCH /api/users/me with { role: "RECRUITER" }
  │    ├─ Success → fires: Persona Updated (Backend)
  │    │    → $set: current_persona = "recruiter"
  │    │    → $set: activated_personas (accumulated, deduplicated)
  │    └─ Failure → fires: Persona Update Failed (Backend)
  │         → current_persona unchanged
  │
  └─ Step 3: New persona's home page loads (on success only)
       → fires: Page Viewed (Frontend)
       → current_page_context reflects the new persona's landing page
```

---

## New Events

### 1. Switch Persona Button Clicked

User explores the persona switching option by clicking the ⇄ icon (ArrowLeftRight from lucide-react).

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | user_action |
| **Trigger** | User clicks the ⇄ ArrowLeftRight icon next to current persona label in sidebar |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `persona_switch_chevron` | Icon-only button — no visible text, `aria-label="Switch role"`. Uses descriptive identifier per icon-only convention. |
| `current_page_context` | string | e.g., `hiring_manager/job_postings`, `recruiter/ai_job_flows`, `candidate/dashboard` | Page the user was on when they clicked |
| `previous_page_context` | string | snake_case page identifier or null | Previous page before current one |
| `entity_type` | string | `persona` | Business object being acted on |
| `component` | string | `sidebar_persona_switcher` | The persona label + icon area in the left sidebar |
| `current_persona` | string | `hiring_manager`, `recruiter`, `job_seeker` | The user's persona at the time of the click. Derived from `ROLE_TO_PERSONA[user.role]`. Passed as event property (not person property) so historical queries show the persona at event time, not the latest value. |

**PostHog call:**

```javascript
posthog.capture('Switch Persona Button Clicked', {
  action: 'click',
  action_value: 'persona_switch_chevron',
  current_page_context: currentPageCtx,
  previous_page_context: getPreviousPageContext(),
  entity_type: 'persona',
  component: 'sidebar_persona_switcher',
  current_persona: currentPersona,
});
```

**Notes:**
- Fires regardless of whether the user actually switches personas
- Useful for measuring awareness/exploration of persona switching
- `current_persona` is an event property — tells us which persona the user was in when they clicked, frozen at event time
- The icon is `ArrowLeftRight` from lucide-react (a bidirectional arrow), not a chevron — the property name `persona_switch_chevron` is the canonical identifier from the tracking plan

### Helix Implementation: Switch Persona Button Clicked

**The current codebase has a different event name and properties that must be changed.**

**Current state (what exists today):**
- Constant `PERSONA_SWITCH_CHEVRON_CLICKED = 'Persona Switch Chevron Clicked'` in `frontend/src/lib/posthogEvents.ts` — **wrong name**
- Constant `PERSONA_SWITCHED = 'Persona Switched'` fires on persona card click — **must be removed** (backend handles this)
- `action_value: 'persona_switch_toggle'` — **wrong value**
- `component: 'sidebar_persona_section'` — **wrong value**
- Sends null properties: `entry_point: null`, `context_object_type: null`, `context_object_id: null` — **unnecessary, remove**

**Changes required:**

**File 1: `frontend/src/lib/posthogEvents.ts`**

Find and replace these two constants:
```typescript
// REMOVE these two lines:
export const PERSONA_SWITCH_CHEVRON_CLICKED = 'Persona Switch Chevron Clicked';
export const PERSONA_SWITCHED = 'Persona Switched';

// REPLACE with this single line:
export const SWITCH_PERSONA_BUTTON_CLICKED = 'Switch Persona Button Clicked';
```

**File 2: `frontend/src/components/layout/Sidebar/RoleSwitcherDropdown.tsx`**

This component has two analytics calls. Replace them as follows:

*Import change:*
```typescript
// CURRENT:
import { PERSONA_SWITCH_CHEVRON_CLICKED, PERSONA_SWITCHED, getPreviousPageContext, pathnameToPageContext, ROLE_TO_PERSONA } from '@/lib/posthogEvents';

// CHANGE TO:
import { SWITCH_PERSONA_BUTTON_CLICKED, getPreviousPageContext, pathnameToPageContext, ROLE_TO_PERSONA } from '@/lib/posthogEvents';
```

*Toggle click handler (`handleToggleClick`):*
```typescript
// CURRENT:
capture(PERSONA_SWITCH_CHEVRON_CLICKED, {
  action: 'click',
  action_value: 'persona_switch_toggle',
  current_page_context: currentPageCtx,
  previous_page_context: getPreviousPageContext(),
  entry_point: null,
  entity_type: 'persona',
  component: 'sidebar_persona_section',
  context_object_type: null,
  context_object_id: null,
  current_persona: currentPersona,
});

// CHANGE TO:
capture(SWITCH_PERSONA_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'persona_switch_chevron',
  current_page_context: currentPageCtx,
  previous_page_context: getPreviousPageContext(),
  entity_type: 'persona',
  component: 'sidebar_persona_switcher',
  current_persona: currentPersona,
});
```

*Card click handler (`handleSwitch`):*

Remove the entire `capture(PERSONA_SWITCHED, ...)` block from `handleSwitch()`. The backend `Persona Updated` event is the source of truth for successful switches. The frontend was firing this BEFORE the API call, causing false positives when the API failed.

**File 3: `frontend/src/components/layout/__tests__/RoleSwitcherDropdown.test.tsx`**

Update tests to:
- Assert `'Switch Persona Button Clicked'` as event name (not `'Persona Switch Chevron Clicked'`)
- Assert `action_value: 'persona_switch_chevron'` (not `'persona_switch_toggle'`)
- Assert `component: 'sidebar_persona_switcher'` (not `'sidebar_persona_section'`)
- Assert no frontend capture on persona card click (the `PERSONA_SWITCHED` call was removed)

---

### 2. Persona Updated — Success

Server confirms persona switch succeeded.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | Success |
| **Trigger** | Backend confirms persona switch via `PATCH /api/users/me` with `{ role: "..." }` — only fires when `previous_role is not None AND dto.role != previous_role` (skips initial onboarding role pick) |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `user.role` BEFORE the update via `ROLE_TO_PERSONA` |
| `current_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The NEW persona after the switch. Must be sent as a regular event property (not just inside `$set`) so PostHog queries on historical events reflect the persona at the time of the event, not the latest value. |

**Property Updates:**

| Operation | Property | Description |
|---|---|---|
| `$set` | `current_persona` | Updated to the newly selected persona |
| `$set` | `activated_personas` | Array of all unique personas the user has tried via switching; grows over time, deduplicated, read from the DB column |

**PostHog call:**

```python
# In users/router.py → update_my_profile(), after service.update_user() + db.commit() succeeds
# Only fire when: dto.role is not None AND previous_role is not None AND dto.role != previous_role

from app.shared.posthog_events import PERSONA_UPDATED, ROLE_TO_PERSONA

previous_persona = ROLE_TO_PERSONA.get(previous_role, "unknown")
new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")

posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATED,
    {
        "previous_persona": previous_persona,
        "current_persona": new_persona,        # regular event property — frozen at event time
        "$set": {
            "current_persona": new_persona,
            "activated_personas": result.activated_personas or [],
        },
    },
)
```

**Guard logic — when the event fires and doesn't fire:**

| Scenario | `previous_role` | `dto.role` | Fires? | Why |
|---|---|---|---|---|
| Actual switch (HM → Recruiter) | `"HIRING_MANAGER"` | `"RECRUITER"` | **Yes** | Role changed |
| Initial onboarding (null → HM) | `None` | `"HIRING_MANAGER"` | No | `previous_role is None` — onboarding, not a switch |
| Same role selected | `"RECRUITER"` | `"RECRUITER"` | No | `dto.role == previous_role` — no actual change |
| Non-role update (phone only) | `"HIRING_MANAGER"` | `None` | No | `dto.role is None` — not a role change |

**Notes:**
- Fires from `users/router.py` after `service.update_user()` + `db.commit()` succeeds
- Backend is the source of truth — the frontend `Persona Switched` event must be removed because it fires BEFORE the API call (causing false positives when the API fails)
- `activated_personas` is read from `result.activated_personas` (the `UserResponse` returned by `service.update_user()`), which reads from the DB column
- `ROLE_TO_PERSONA` maps `UserRole` strings to persona labels: `HIRING_MANAGER` → `"hiring_manager"`, `RECRUITER` → `"recruiter"`, `PROFESSIONAL` → `"job_seeker"`
- This mapping is SEPARATE from `_ROLE_TO_ACTING_AS` (which maps `PROFESSIONAL` → `"team_member"`) — they serve different analytics contexts
- `current_persona` is sent BOTH as a regular event property AND inside `$set`. The event property freezes the value at event time for historical analysis. The `$set` updates the person property for current-state queries.

### Helix Implementation: Persona Updated

**The current codebase has NO PostHog events in the persona switch path. All of this is new.**

**Current state:** `users/router.py` → `update_my_profile()` calls `service.update_user()` and returns the result. No PostHog capture, no try/except, no persona event logic.

**Changes required:**

See [Helix Implementation: Backend Router Changes](#helix-implementation-backend-router-changes) for the full `update_my_profile()` rewrite that covers both `Persona Updated` and `Persona Update Failed`.

---

### 3. Persona Update Failed

Server returns error when persona switch fails.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | Failure |
| **Trigger** | `service.update_user()` raises exception during a role-only PATCH (guard: `role_only_update and dto.role is not None and previous_role is not None`) |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `current_user.role` (unchanged — switch failed) |
| `target_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `dto.role` — what the user tried to switch to |
| `error_reason` | string | system error description | `str(e)[:256]` from the caught exception — truncated to 256 chars for safety |
| `error_category` | enum | `validation`, `server` | `validation` for `ValueError`/`BadRequestException`, `server` for others |

**PostHog call:**

```python
# In users/router.py → update_my_profile() except block
# Only fire when: role_only_update AND dto.role is not None AND previous_role is not None

posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATE_FAILED,
    {
        "previous_persona": previous_persona,
        "target_persona": target_persona,
        "error_reason": str(e)[:256],
        "error_category": "validation" if isinstance(e, (ValueError, BadRequestException)) else "server",
    },
)
```

**Guard logic — `role_only_update`:**

The failure event uses `role_only_update = set(updated_fields) == {"role"}` to only fire when the PATCH body contains ONLY the role field. This prevents false attribution when an unrelated field (like phone) causes the error in a combined PATCH. In practice, the frontend always sends role and phone as separate requests, but the guard is a safety net.

**Notes:**
- `previous_persona` stays unchanged (switch didn't happen)
- `error_reason` is truncated to 256 chars to prevent verbose exception details leaking to PostHog
- Common failure: invalid role enum value → `ValueError` from `UserRole(dto.role)` in `service.update_user()`
- Org resolution failure in `ensure_org_for_role()` (called in `service.update_user()`) would also trigger this

### Helix Implementation: Persona Update Failed

See [Helix Implementation: Backend Router Changes](#helix-implementation-backend-router-changes) — the failure event is part of the same try/except block.

---

### 4. Page Viewed (existing — no changes needed)

The new persona's home page loads after the switch.

| Field | Value |
|-------|-------|
| **Area** | Navigation |
| **Type** | page_view |
| **Trigger** | User lands on a meaningful page |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Live |

**PostHog call:**

```javascript
posthog.capture('Page Viewed', {
  current_page_context: newPersonaPageContext,          // e.g., 'recruiter/ai_job_flows'
  previous_page_context: previousPageContext,           // page before the switch
});
```

**Post-switch landing pages:**
- Hiring Manager → `/hiring-manager/job-postings` → `hiring_manager/job_postings`
- Recruiter → `/recruiter/ai-job-flows` → `recruiter/ai_job_flows`
- Job Seeker → `/candidate/dashboard` → `candidate/dashboard` (or `/candidate/create-profile` if no resume)

**Notes:**
- No changes needed to this event — it already exists and is Live
- After `Persona Updated` fires, `current_persona` person property is already updated via `$set`, so this Page Viewed is automatically associated with the new persona in PostHog queries

---

## Helix Implementation: Backend Event Constants and ROLE_TO_PERSONA

**File: `backend/app/shared/posthog_events.py`**

Add the following after the existing `REVIEW_DECISION_MADE` constant (in the "Hiring Surface" section):

```python
# Persona Switching
PERSONA_UPDATED = "Persona Updated"
PERSONA_UPDATE_FAILED = "Persona Update Failed"
```

Add the following after the existing `_ROLE_TO_ACTING_AS` dict and `get_acting_as()` function:

```python
# Persona labels for PostHog persona-switching events.
# PROFESSIONAL maps to "job_seeker" (not "team_member") to match the
# user-facing label in the UI and the frontend analytics mapping.
# This is deliberately separate from _ROLE_TO_ACTING_AS which maps
# PROFESSIONAL to "team_member" for the legacy acting_as property.
ROLE_TO_PERSONA = {
    "HIRING_MANAGER": "hiring_manager",
    "RECRUITER": "recruiter",
    "PROFESSIONAL": "job_seeker",
}
```

**Important:** `ROLE_TO_PERSONA` is deliberately separate from `_ROLE_TO_ACTING_AS`. They map `PROFESSIONAL` to different values:
- `ROLE_TO_PERSONA["PROFESSIONAL"]` → `"job_seeker"` (analytics persona label, matches UI)
- `_ROLE_TO_ACTING_AS["PROFESSIONAL"]` → `"team_member"` (legacy acting_as property)

Do NOT modify `_ROLE_TO_ACTING_AS` — it's used by existing events.

---

## Helix Implementation: `activated_personas` Database Column

**This column does not exist yet. It must be created from scratch.**

### Step 1: Alembic migration

Create a new migration file in `backend/alembic/versions/`. Run `alembic revision --autogenerate -m "add activated_personas to users"` or create manually:

```python
"""add activated_personas to users"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column("users", sa.Column("activated_personas", sa.dialects.postgresql.JSONB, nullable=True))

def downgrade() -> None:
    op.drop_column("users", "activated_personas")
```

This is a non-blocking `ADD COLUMN NULLABLE` in PostgreSQL. No backfill needed — `null` means "never switched."

### Step 2: User model

**File: `backend/app/database/models/user.py`**

Add the column to the `User` class, after the `alternate_email_addresses` field:

```python
# Analytics — accumulating set of personas the user has tried via switching
activated_personas: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
```

This follows the same pattern as the existing `alternate_email_addresses` JSONB column on the same model.

### Step 3: AuthUser dataclass

**File: `backend/app/auth/dependencies.py`**

Add to the `AuthUser` dataclass (after the `timezone` field):

```python
activated_personas: list[str] | None = None
```

Wire it in `_user_to_auth_user()` function — add to the constructor:

```python
activated_personas=user.activated_personas,
```

### Step 4: UserResponse schema

**File: `backend/app/auth/schemas.py`**

Add to the `UserResponse` model (after the `timezone` field):

```python
activated_personas: list[str] | None = Field(default=None, serialization_alias="activatedPersonas")
```

### Step 5: Service layer — accumulation logic

**File: `backend/app/users/service.py`**

Add import at top:
```python
from app.shared.posthog_events import ROLE_TO_PERSONA
```

In the `update_user()` function, after `user.role = new_role` and `user.org_id = new_org_id` (inside the `if dto.role is not None:` block), add:

```python
new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
existing = user.activated_personas or []
if new_persona not in existing:
    user.activated_personas = existing + [new_persona]
```

Also add `activated_personas` to `_user_to_response()`:
```python
activated_personas=user.activated_personas,
```

### Step 6: Router — wire into GET /me and auth responses

**File: `backend/app/users/router.py`** — In the `get_my_profile()` function, add to the `UserResponse(...)` constructor:

```python
activated_personas=current_user.activated_personas,
```

**File: `backend/app/auth/router.py`** — In the `_user_to_response()` function, add:

```python
activated_personas=user.activated_personas,
```

### Key design decisions

- `activated_personas` is persisted in the DB (not PostHog-only) because PostHog's `$set` overwrites the array each time — without DB persistence, the accumulating array would be lost between sessions
- `null` means "never switched via the chevron" — distinct from `[]` (which shouldn't happen)
- The array only grows via the persona switch flow, NOT during initial onboarding
- The `previous_role is not None` guard in the router ensures onboarding (null → first role) doesn't fire events or accumulate personas

---

<a id="helix-implementation-backend-router-changes"></a>
## Helix Implementation: Backend Router Changes

**File: `backend/app/users/router.py`**

This is the most significant change. The `update_my_profile()` function must be wrapped in try/except to fire PostHog events on success/failure.

**Add imports at top of file:**

```python
from app.shared.posthog_events import (
    CUSTOM_LINK_CREATED,
    PERSONA_UPDATED,
    PERSONA_UPDATE_FAILED,
    PROP_SURFACE,
    ROLE_TO_PERSONA,
    SURFACE_PROSPECT,
)
```

**Replace the body of `update_my_profile()` (the `PATCH /me` handler) with:**

```python
@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    dto: UpdateUserDto,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update current user profile."""
    set_context(pipeline="onboarding", pipeline_stage="profile_update")
    updated_fields = list(dto.model_dump(exclude_unset=True).keys())
    logger.info(
        "User profile update requested",
        extra={
            "pipeline_stage": "profile_update_requested",
            "user_id": str(current_user.id),
            "org_id": str(current_user.org_id) if current_user.org_id else None,
            "updated_fields": ",".join(updated_fields) if updated_fields else "",
        },
    )
    previous_role = current_user.role  # capture role BEFORE update
    role_only_update = set(updated_fields) == {"role"}
    try:
        result = await service.update_user(db, current_user.id, dto)
        await db.commit()

        # Fire Persona Updated only on actual persona switches (not onboarding)
        if dto.role is not None and previous_role is not None and dto.role != previous_role:
            previous_persona = ROLE_TO_PERSONA.get(previous_role, "unknown")
            new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
            posthog_client.capture(
                str(current_user.id),
                PERSONA_UPDATED,
                {
                    "previous_persona": previous_persona,
                    "current_persona": new_persona,
                    "$set": {
                        "current_persona": new_persona,
                        "activated_personas": result.activated_personas or [],
                    },
                },
            )

        logger.info(
            "User profile update completed",
            extra={
                "pipeline_stage": "profile_update_completed",
                "user_id": str(current_user.id),
                "role": result.role,
                "phone_present": bool(result.phone),
            },
        )
        return result
    except Exception as e:
        # Only fire Persona Update Failed when role is the sole field
        # being updated, so unrelated field errors (e.g. phone validation)
        # don't pollute persona analytics.
        if role_only_update and dto.role is not None and previous_role is not None:
            previous_persona = ROLE_TO_PERSONA.get(previous_role, "unknown")
            target_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
            posthog_client.capture(
                str(current_user.id),
                PERSONA_UPDATE_FAILED,
                {
                    "previous_persona": previous_persona,
                    "target_persona": target_persona,
                    "error_reason": str(e)[:256],
                    "error_category": "validation" if isinstance(e, (ValueError, BadRequestException)) else "server",
                },
            )
        raise
```

**Key implementation notes:**
- `previous_role = current_user.role` MUST be captured before calling `service.update_user()` — after the call, the user object has the new role
- `role_only_update` scopes the failure event to role-only PATCHes — prevents phone validation errors from triggering persona failure events
- `result.activated_personas` comes from the `UserResponse` returned by `service.update_user()`, which reads from the DB column populated in Step 5
- `BadRequestException` is already imported in the current router — check imports if not

---

## Helix Implementation: `identifyUser()` Fix

**File: `frontend/src/lib/posthog.ts`**

**Problem:** `identifyUser()` currently sets `email`, `name`, `role`, `org_id` via `$set` and `account_created_at`, `first_surface` via `$set_once`. It does NOT set `current_persona`. This means users who never switch personas will have no `current_persona` person property in PostHog, making cohort analysis by persona incomplete.

**Change the `identifyUser()` function:**

```typescript
// CURRENT:
import { SURFACE_PROSPECT, SURFACE_HIRING } from '@/lib/posthogEvents';

export function identifyUser(user: User): void {
  const setOnce: Record<string, unknown> = {
    account_created_at: user.createdAt,
  };
  if (user.role) {
    setOnce.first_surface =
      user.role === UserRole.PROFESSIONAL ? SURFACE_PROSPECT : SURFACE_HIRING;
  }
  identify(
    user.id,
    { email: user.email, name: user.name, role: user.role, org_id: user.orgId },
    setOnce,
  );
}

// CHANGE TO:
import { SURFACE_PROSPECT, SURFACE_HIRING, ROLE_TO_PERSONA } from '@/lib/posthogEvents';

export function identifyUser(user: User): void {
  const setOnce: Record<string, unknown> = {
    account_created_at: user.createdAt,
  };
  if (user.role) {
    setOnce.first_surface =
      user.role === UserRole.PROFESSIONAL ? SURFACE_PROSPECT : SURFACE_HIRING;
  }
  const currentPersona = user.role ? (ROLE_TO_PERSONA[user.role] ?? 'unknown') : null;
  identify(
    user.id,
    {
      email: user.email,
      name: user.name,
      role: user.role,
      org_id: user.orgId,
      current_persona: currentPersona,
    },
    setOnce,
  );
}
```

**What this achieves:**
- Every user gets `current_persona` set as a person property on every login/session restore
- Users who never switch personas still have `current_persona` in PostHog (derived from their role)
- `ROLE_TO_PERSONA` mapping already exists in `posthogEvents.ts` — no new code needed for the mapping
- The `$set` in `Persona Updated` (backend) will override this on switch, which is correct

**Where `identifyUser()` is called:**
- `frontend/src/stores/authStore.ts` — after successful login and session restore
- This means `current_persona` gets set on every app load for authenticated users

---

## Event Sequence

| Order | Event | Source | What happens | current_persona |
|-------|-------|--------|-------------|-----------------|
| 1 | Switch Persona Button Clicked | Frontend | Dropdown opens | Old persona (event property) |
| 2a | Persona Updated | Backend | Server confirms switch | New persona (event property + $set) |
| 2b | Persona Update Failed | Backend | Server returns error | Unchanged (no event property needed — `previous_persona` covers it) |
| 3 | Page Viewed | Frontend | New persona's home page loads | New persona (person property from $set) |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Persona Switch Completion | Switch Persona Button Clicked → Persona Updated | Measures conversion from exploring the switch to actually switching |
| Persona Switch Full Flow | Switch Persona Button Clicked → Persona Updated → Page Viewed | Full switch flow including page load |

---

## New Property Details

| Property | Type | Scope | Values | Description |
|---|---|---|---|---|
| `previous_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on before switching. Used in Persona Updated and Persona Update Failed. |
| `target_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user tried to switch to. Used only in Persona Update Failed. |
| `current_persona` | enum | event + person ($set) | `hiring_manager`, `recruiter`, `job_seeker` | The user's active persona. Set as person property via `identifyUser()` on every login and via `$set` in Persona Updated. Also sent as regular event property on Switch Persona Button Clicked and Persona Updated so historical queries reflect the persona at event time. |
| `activated_personas` | array | event + person ($set) + DB column | e.g., `["recruiter", "job_seeker"]` | All unique personas the user has ever been in. Sent as top-level event property on Persona Updated (frozen at event time) and as person property via `$set`. Persisted in DB as JSONB. Accumulates on all role updates including onboarding. `null` in DB means no role set yet. |

---

## Catalog Changes (applied on merge)

### Event Catalog (`docs/event-catalog.md`)

#### 1. Account & Persona Events — 3 events (already applied)

```md
| Switch Persona Button Clicked | Account | Intent  | User clicks the ⇄ chevron next to current persona in sidebar        | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | -- | -- | Not Started |
| Persona Updated               | Account | Success | Backend confirms persona switch after user selects a different persona | Backend  | `previous_persona`, `current_persona`, `activated_personas` | -- | `$set: current_persona, activated_personas` | Not Started |
| Persona Update Failed          | Account | Failure | Backend returns error on persona switch attempt                       | Backend  | `previous_persona`, `target_persona`, `error_reason`, `error_category` | -- | -- | Not Started |
```

#### 2. Removed Events table entry (already applied)

```md
| Persona Activated | Persona Updated | Renamed — "Activated" implied adding a new persona; "Updated" reflects switching between existing personas | May 2026 |
```

#### 3. Property Dictionary updates (already applied)

- `previous_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | Persona Updated, Persona Update Failed
- `target_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | Persona Update Failed
- `current_persona` Used In → `Account Created, Persona Updated, Switch Persona Button Clicked (person property + event property)`
- `activated_personas` | array | event, person ($set) | e.g., `["recruiter", "job_seeker"]` | Persona Updated (event property + person property via `$set`), Account Created (person property via `$set`)

### Event Schema (`docs/event-schema.md`)

#### 1. Standard Objects table — Persona row updated (already applied)

Example Events: `Switch Persona Button Clicked, Persona Updated`

#### 2. Intent vs Outcome table — row added (already applied)

```md
| Persona switch | Switch Persona Button Clicked | Persona Updated | Persona Update Failed |
```

---

## Summary: All Helix Codebase Changes

Every change below must be implemented. Nothing has been done yet.

### Backend changes

| File | Change |
|---|---|
| `backend/alembic/versions/<new>_add_activated_personas_to_users.py` | **NEW FILE** — Migration: `ADD COLUMN activated_personas JSONB NULLABLE` on `users` table |
| `backend/app/database/models/user.py` | **ADD** `activated_personas: Mapped[list[str] \| None] = mapped_column(JSONB, nullable=True)` after `alternate_email_addresses` |
| `backend/app/auth/dependencies.py` | **ADD** `activated_personas: list[str] \| None = None` to `AuthUser` dataclass + wire in `_user_to_auth_user()` |
| `backend/app/auth/schemas.py` | **ADD** `activated_personas: list[str] \| None = Field(default=None, serialization_alias="activatedPersonas")` to `UserResponse` |
| `backend/app/auth/router.py` | **ADD** `activated_personas=user.activated_personas` to `_user_to_response()` |
| `backend/app/shared/posthog_events.py` | **ADD** `PERSONA_UPDATED`, `PERSONA_UPDATE_FAILED` constants + `ROLE_TO_PERSONA` dict |
| `backend/app/users/service.py` | **ADD** `ROLE_TO_PERSONA` import, persona accumulation in `update_user()`, `activated_personas` in `_user_to_response()` |
| `backend/app/users/router.py` | **REWRITE** `update_my_profile()` with try/except, `Persona Updated` + `Persona Update Failed` events, `activated_personas` in GET /me |

### Frontend changes

| File | Change |
|---|---|
| `frontend/src/lib/posthogEvents.ts` | **RENAME** `PERSONA_SWITCH_CHEVRON_CLICKED` → `SWITCH_PERSONA_BUTTON_CLICKED`, **REMOVE** `PERSONA_SWITCHED` |
| `frontend/src/components/layout/Sidebar/RoleSwitcherDropdown.tsx` | **UPDATE** import, `action_value`, `component`; **REMOVE** `capture(PERSONA_SWITCHED, ...)` from `handleSwitch()` |
| `frontend/src/components/layout/__tests__/RoleSwitcherDropdown.test.tsx` | **UPDATE** tests to match new event name and properties |
| `frontend/src/lib/posthog.ts` | **UPDATE** `identifyUser()` to add `current_persona` via `ROLE_TO_PERSONA` |

### Tests to include

| Test | What it verifies |
|---|---|
| `test_persona_updated_fires_on_role_switch` | HM → Recruiter fires `Persona Updated` with correct `previous_persona`, `current_persona`, `$set` |
| `test_persona_updated_skips_onboarding` | null → HM (initial role pick) does NOT fire `Persona Updated` |
| `test_persona_update_failed_fires_on_role_error` | Invalid role with role-only PATCH fires `Persona Update Failed` |
| `test_persona_update_failed_skips_non_role_error` | Phone error with role in combined PATCH does NOT fire failure event |
| `test_persona_switch_accumulates_activated_personas` | HM → Recruiter → Job Seeker accumulates `["recruiter", "job_seeker"]` |
| `test_duplicate_switch_does_not_duplicate` | HM → Recruiter → HM → Recruiter has no duplicates in array |
| `test_onboarding_then_switch_fires_only_on_switch` | null → HM = no event; HM → Recruiter = event |
| `test_get_me_includes_activated_personas` | GET /me response includes `activatedPersonas` field |

---

## Implementation Delta (2026-05-26)

> **What this section is:** During implementation on the Helix codebase (`soumabrata/persona-switching-v2` branch), several changes were made relative to the original tracking plan spec above. This section documents every difference so the tracking plan stays in sync with what's actually firing in production.
>
> **How to read this:** Each delta entry references the original section, states what changed, and explains why. The original sections above remain as-is for historical context — this delta is the authoritative override.

---

### Delta 1: `activated_personas` added as top-level event property on Persona Updated

**Original (Section 2 — Persona Updated):**

The PostHog call only included `activated_personas` inside the `$set` operator (person property update). The top-level event properties were `previous_persona` and `current_persona` only.

```python
posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATED,
    {
        "previous_persona": previous_persona,
        "current_persona": new_persona,
        "$set": {
            "current_persona": new_persona,
            "activated_personas": result.activated_personas or [],
        },
    },
)
```

**Implemented as:**

`activated_personas` is also sent as a regular top-level event property alongside the `$set`:

```python
posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATED,
    {
        "previous_persona": previous_persona,
        "current_persona": new_persona,
        "activated_personas": result.activated_personas or [],
        "$set": {
            "current_persona": new_persona,
            "activated_personas": result.activated_personas or [],
        },
    },
)
```

**Why:** Sending `activated_personas` as a top-level event property means historical queries on `Persona Updated` events can see the full persona list at the exact moment of the switch, without relying on the person property (which only reflects the latest state via `$set`). This is the same intent-vs-snapshot pattern used for `current_persona`, which is already both a top-level event property and a `$set` person property.

**Updated properties table for Persona Updated:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Persona before the switch |
| `current_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Persona after the switch (event property + `$set`) |
| `activated_personas` | array | e.g., `["recruiter", "job_seeker"]` | All personas tried so far, frozen at event time (event property + `$set`) |

---

### Delta 2: `identifyUser()` must set `current_persona` as person property — NOT YET IMPLEMENTED

**Original (Section — Helix Implementation: `identifyUser()` Fix):**

The spec correctly called for updating `identifyUser()` in `frontend/src/lib/posthog.ts` to include `current_persona` in the `$set` properties. This was not picked up during initial implementation but is **required**.

**Current state (what exists today):**

```typescript
// frontend/src/lib/posthog.ts → identifyUser()
identify(
  user.id,
  { email: user.email, name: user.name, role: user.role, org_id: user.orgId },
  setOnce,
);
```

No `current_persona` in `$set`. The person property is only set via `Persona Updated` (backend `$set` on switch), meaning users who never switch personas have no `current_persona` person property in PostHog.

**Must be implemented as:**

```typescript
// frontend/src/lib/posthog.ts → identifyUser()
import { ROLE_TO_PERSONA } from '@/lib/posthogEvents';

export function identifyUser(user: User): void {
  const setOnce: Record<string, unknown> = {
    account_created_at: user.createdAt,
  };
  if (user.role) {
    setOnce.first_surface =
      user.role === UserRole.PROFESSIONAL ? SURFACE_PROSPECT : SURFACE_HIRING;
  }
  const currentPersona = user.role ? (ROLE_TO_PERSONA[user.role] ?? 'unknown') : null;
  identify(
    user.id,
    {
      email: user.email,
      name: user.name,
      role: user.role,
      org_id: user.orgId,
      ...(currentPersona && { current_persona: currentPersona }),
    },
    setOnce,
  );
}
```

**Why this is required:** Without this, `current_persona` as a person property only exists for users who have switched personas at least once. That's a tiny minority. Any PostHog query that filters by `current_persona` (funnels, cohorts, retention, dashboards) would silently exclude the vast majority of users. This makes the person property useless for segmentation until the fix is in place.

**What this achieves:**
- Every user gets `current_persona` set as a person property on every login/session restore
- `ROLE_TO_PERSONA` already exists in `posthogEvents.ts` — no new mapping needed
- The `$set` in `Persona Updated` (backend) overrides this on switch, which is correct
- Users with no role yet (pre-onboarding) get `null` — no false data

**Where `identifyUser()` is called:**
- `frontend/src/stores/authStore.ts` — after successful login and session restore
- Fires on every app load for authenticated users

---

### Delta 3: `activated_personas` accumulates on onboarding role pick

**Original (Section — `activated_personas` Database Column, Key design decisions):**

The spec stated:
- "The array only grows via the persona switch flow, NOT during initial onboarding"
- "`null` means 'never switched via the chevron' — distinct from `[]`"
- "The `previous_role is not None` guard in the router ensures onboarding (null → first role) doesn't fire events **or accumulate personas**"

**Implemented as:**

The `activated_personas` accumulation logic lives in `service.py` inside the `if dto.role is not None:` block, which runs for **all** role updates — including the initial onboarding role pick:

```python
# In service.py → update_user(), inside `if dto.role is not None:`
new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
existing = user.activated_personas or []
if new_persona not in existing:
    user.activated_personas = existing + [new_persona]
```

The router guard (`previous_role is not None`) only prevents the **PostHog event** from firing on onboarding — it does NOT prevent the DB column from accumulating. So a user who picks Hiring Manager during onboarding will have `activated_personas = ["hiring_manager"]` in the DB even though no `Persona Updated` event fired.

**Why:** Accumulating from onboarding provides a complete history of every persona a user has ever been in, not just personas reached via switching. This is more useful for analytics — a user with `activated_personas = ["hiring_manager", "recruiter"]` means they've been in both personas regardless of whether the first one was set during onboarding or via switching. The PostHog person property (`$set`) only gets updated on switches (since the event guard still applies), so the DB column is the authoritative source.

**Updated semantics:**

| DB value | Meaning (spec) | Meaning (implemented) |
|---|---|---|
| `null` | Never switched | Never had any role set (brand new user, pre-onboarding) |
| `["hiring_manager"]` | N/A (wouldn't happen without a switch) | Picked HM during onboarding, never switched |
| `["hiring_manager", "recruiter"]` | Switched from HM to Recruiter | Has been in both personas (onboarding + switch, or two switches) |

**Test confirmation:** `test_onboarding_then_switch_fires_only_on_switch` verifies this behavior — null → HM populates `["hiring_manager"]` in the DB without firing a PostHog event.

---

### Delta 4: `Account Created` must `$set` `current_persona` during onboarding — NOT YET IMPLEMENTED

**Original (not in tracking plan spec):**

The original persona switching tracking plan did not address `Account Created` because onboarding was considered out of scope. However, `Account Created` is the first moment a user has a persona, and it must set `current_persona` as a person property so PostHog has it from the very first session.

**Current state (what exists today):**

```typescript
// frontend/src/pages/RoleSelection.tsx → handleContinue()
capture(ACCOUNT_CREATED, {
  action: 'click',
  action_value: ROLE_TO_ACTION_VALUE[selectedRole] || 'continue_as_unknown_button',
  current_page_context: 'onboarding/role_selection',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  context_object_type: null,
  context_object_id: null,
  persona,
  signup_context: entryPoint,
  $set_once: {
    first_persona: persona,
    entry_point: entryPoint,
    account_created_at: new Date().toISOString(),
  },
});
```

The event sends `persona` as an event property and `first_persona` via `$set_once`, but does **not** `$set` `current_persona`. This means even after onboarding completes, the user has no `current_persona` person property until they switch personas (which most users never do).

**Must be implemented as:**

Add a `$set` block alongside the existing `$set_once`:

```typescript
capture(ACCOUNT_CREATED, {
  action: 'click',
  action_value: ROLE_TO_ACTION_VALUE[selectedRole] || 'continue_as_unknown_button',
  current_page_context: 'onboarding/role_selection',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  context_object_type: null,
  context_object_id: null,
  persona,
  signup_context: entryPoint,
  $set: {
    current_persona: persona,
  },
  $set_once: {
    first_persona: persona,
    entry_point: entryPoint,
    account_created_at: new Date().toISOString(),
  },
});
```

**Why this is required:** `Account Created` fires once during onboarding when the user picks their role. Without `$set: { current_persona }` here, users start their lifecycle with no `current_persona` person property. The `identifyUser()` fix (Delta 2) will set it on subsequent logins, but there's a gap between account creation and the first re-login where queries by persona would miss the user. Setting it at the point of creation closes this gap completely.

**Relationship between the two fixes:**

| Fix | When it fires | Purpose |
|---|---|---|
| Delta 2: `identifyUser()` | Every login / session restore | Ensures `current_persona` is always up-to-date for returning users |
| Delta 4: `Account Created` | Once, during onboarding | Ensures `current_persona` is set from the very first moment the user has a role |
| Existing: `Persona Updated` `$set` | On persona switch | Updates `current_persona` when the user switches |

All three are needed for complete coverage.

---

## Delta Summary Table

| # | Change Type | Status | Original | Implemented / Required | Why |
|---|---|---|---|---|---|
| 1 | Property added | Done | `activated_personas` only inside `$set` on Persona Updated | Also sent as top-level event property | Historical queries can see the full persona list at event time without relying on person property |
| 2 | Must implement | **Not yet done** | `identifyUser()` updated to set `current_persona` person property on every login | `identifyUser()` unchanged — must add `current_persona` to `$set` via `ROLE_TO_PERSONA` | Without this, users who never switch have no `current_persona` person property — breaks all persona-based filtering |
| 3 | Behavior change | Done | `activated_personas` only grows via persona switching, not onboarding | Accumulates on ALL role updates including onboarding first-pick | Complete persona history is more useful; DB is authoritative, PostHog `$set` still guarded to switches only |
| 4 | Must implement | **Not yet done** | `Account Created` only uses `$set_once: { first_persona }` | Must add `$set: { current_persona: persona }` alongside existing `$set_once` | Closes the gap between account creation and first re-login — user has `current_persona` from the very first moment |
