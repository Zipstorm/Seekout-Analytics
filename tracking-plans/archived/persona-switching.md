# Tracking Plan: Persona Switching

**Product:** Helix (SeekOut.ai)
**Feature:** Persona switching flow
**Date:** 2026-05-11 (updated 2026-05-20)
**Related PRD:** —
**Related Helix PR:** [#494 — feat: add PostHog persona switching events and activated_personas column](https://github.com/Zipstorm/helix/pull/494) (open, not merged)

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## Implementation Status

PR #494 in the Helix repo implements most of this tracking plan. This section documents what PR #494 covers, what it does NOT cover, and what still needs to be done after PR #494 merges.

### What PR #494 implements

- **Backend `Persona Updated` event** — fires from `users/router.py` → `update_my_profile()` after `service.update_user()` succeeds, only on actual persona switches (not onboarding)
- **Backend `Persona Update Failed` event** — fires from the `except` block when a role-only PATCH fails
- **`activated_personas` JSONB column** — Alembic migration `29de6d7dba88` adds the column to the `users` table; service layer accumulates personas on role change
- **Backend `ROLE_TO_PERSONA` mapping** — added to `posthog_events.py` with `PROFESSIONAL` → `"job_seeker"` (separate from `_ROLE_TO_ACTING_AS` which maps `PROFESSIONAL` → `"team_member"`)
- **Frontend event rename** — `Persona Switch Chevron Clicked` → `Switch Persona Button Clicked` with tracking-plan-aligned properties
- **Frontend duplicate removal** — removed the `Persona Switched` frontend event; backend `Persona Updated` is now the source of truth
- **Frontend property alignment** — `action_value` → `persona_switch_chevron`, `component` → `sidebar_persona_switcher`, stripped null properties, kept `current_persona` as event property

### What PR #494 does NOT implement (remaining work)

These items must be addressed in a follow-up PR after #494 merges:

1. **`identifyUser()` must set `current_persona`** — Currently, `identifyUser()` in `frontend/src/lib/posthog.ts` does NOT set `current_persona` as a person property. Users who never switch personas will have no `current_persona` in PostHog. See [Helix Implementation: identifyUser fix](#helix-implementation-identifyuser-fix) for the exact change.

2. **`current_persona` must also be a regular event property on `Persona Updated`** — PR #494 sends `current_persona` only inside `$set` (person property update), not as a standalone event property. Person properties in PostHog reflect the LATEST value, not the value at event time. If a user switches personas multiple times, querying by `current_persona` person property on historical events will show the wrong value. The fix is to add `current_persona` as a regular event property alongside `$set`. See [Helix Implementation: Persona Updated fix](#helix-implementation-persona-updated-fix).

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

**PR #494 status: IMPLEMENTED** — PR #494 renames the event constant and aligns properties to this tracking plan. After PR #494 merges, this event is fully implemented.

**Files changed by PR #494:**

| File | Change |
|---|---|
| `frontend/src/lib/posthogEvents.ts` | Renamed `PERSONA_SWITCH_CHEVRON_CLICKED` to `SWITCH_PERSONA_BUTTON_CLICKED` with value `"Switch Persona Button Clicked"`. Removed `PERSONA_SWITCHED` constant. |
| `frontend/src/components/layout/Sidebar/RoleSwitcherDropdown.tsx` | Updated import, changed `action_value` to `'persona_switch_chevron'`, `component` to `'sidebar_persona_switcher'`. Removed `entry_point: null`, `context_object_type: null`, `context_object_id: null`. Kept `current_persona`. Removed `capture(PERSONA_SWITCHED, ...)` from `handleSwitch()`. |
| `frontend/src/components/layout/__tests__/RoleSwitcherDropdown.test.tsx` | Updated tests to assert new event name and properties. |

**Codebase state BEFORE PR #494 (current `main`):**
- Event constant: `PERSONA_SWITCH_CHEVRON_CLICKED = 'Persona Switch Chevron Clicked'` — **wrong name**
- Also fires: `PERSONA_SWITCHED = 'Persona Switched'` on card click — **should not exist** (backend handles this)
- `action_value: 'persona_switch_toggle'` — **wrong value**
- `component: 'sidebar_persona_section'` — **wrong value**
- Sends null properties: `entry_point: null`, `context_object_type: null`, `context_object_id: null` — **unnecessary noise**

**Codebase state AFTER PR #494:**
- Event constant: `SWITCH_PERSONA_BUTTON_CLICKED = 'Switch Persona Button Clicked'` — **correct**
- `PERSONA_SWITCHED` removed entirely — **correct**
- `action_value: 'persona_switch_chevron'` — **correct**
- `component: 'sidebar_persona_switcher'` — **correct**
- Null properties stripped — **correct**
- `current_persona` kept as event property — **correct**

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
- Backend is the source of truth — the frontend `Persona Switched` event was removed because it fired BEFORE the API call (causing false positives when the API failed)
- `activated_personas` is read from `result.activated_personas` (the `UserResponse` returned by `service.update_user()`), which reads from the DB column
- `ROLE_TO_PERSONA` maps `UserRole` strings to persona labels: `HIRING_MANAGER` → `"hiring_manager"`, `RECRUITER` → `"recruiter"`, `PROFESSIONAL` → `"job_seeker"`
- This mapping is SEPARATE from `_ROLE_TO_ACTING_AS` (which maps `PROFESSIONAL` → `"team_member"`) — they serve different analytics contexts

### Helix Implementation: Persona Updated

**PR #494 status: PARTIALLY IMPLEMENTED** — PR #494 adds the event but sends `current_persona` only inside `$set`, not as a regular event property. A follow-up change is needed.

**Files changed by PR #494:**

| File | Change |
|---|---|
| `backend/app/shared/posthog_events.py` | Added `PERSONA_UPDATED = "Persona Updated"`, `PERSONA_UPDATE_FAILED = "Persona Update Failed"`, and `ROLE_TO_PERSONA` dict |
| `backend/app/users/router.py` | Added try/except around `service.update_user()`, fires `Persona Updated` on success with guard logic |
| `backend/app/users/service.py` | Added `ROLE_TO_PERSONA` import, persona accumulation in `update_user()` (append-only, dedup) |

<a id="helix-implementation-persona-updated-fix"></a>
**Follow-up fix needed — add `current_persona` as regular event property:**

In `backend/app/users/router.py` → `update_my_profile()`, inside the success block where `Persona Updated` is captured, add `"current_persona": new_persona` as a top-level property alongside `"previous_persona"`:

```python
# CURRENT (PR #494):
posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATED,
    {
        "previous_persona": previous_persona,
        "$set": {
            "current_persona": new_persona,
            "activated_personas": result.activated_personas or [],
        },
    },
)

# CHANGE TO:
posthog_client.capture(
    str(current_user.id),
    PERSONA_UPDATED,
    {
        "previous_persona": previous_persona,
        "current_persona": new_persona,        # ADD THIS LINE
        "$set": {
            "current_persona": new_persona,
            "activated_personas": result.activated_personas or [],
        },
    },
)
```

**Why:** PostHog person properties (`$set`) always reflect the LATEST value. If a user switches HM → Recruiter → Job Seeker, and you query the `Persona Updated` event from the first switch, the `current_persona` person property will show `"job_seeker"` (the latest), not `"recruiter"` (what it was at event time). Adding `current_persona` as a regular event property freezes the value at event time, making historical analysis accurate.

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

**PR #494 status: IMPLEMENTED** — PR #494 adds the failure event with all guards and error truncation. No follow-up needed.

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

## Helix Implementation: `activated_personas` Column

**PR #494 status: IMPLEMENTED** — PR #494 adds the column, migration, and accumulation logic. No follow-up needed.

**What PR #494 adds:**

| File | Change |
|---|---|
| `backend/alembic/versions/29de6d7dba88_add_activated_personas_to_users.py` | Alembic migration: `ADD COLUMN activated_personas JSONB NULLABLE` on `users` table. Non-blocking in PostgreSQL. Reversible via `alembic downgrade -1`. |
| `backend/app/database/models/user.py` | Added `activated_personas: Mapped[list[str] \| None] = mapped_column(JSONB, nullable=True)` after `alternate_email_addresses` |
| `backend/app/auth/dependencies.py` | Added `activated_personas: list[str] \| None = None` to `AuthUser` dataclass, wired in `_user_to_auth_user()` |
| `backend/app/auth/schemas.py` | Added `activated_personas: list[str] \| None = Field(default=None, serialization_alias="activatedPersonas")` to `UserResponse` |
| `backend/app/users/service.py` | In `update_user()`: after setting `user.role` and `user.org_id`, looks up new persona via `ROLE_TO_PERSONA`, appends to `user.activated_personas` if not already present (ordered, dedup). Also added to `_user_to_response()`. |
| `backend/app/users/router.py` | Added `activated_personas=current_user.activated_personas` to `GET /me` response |
| `backend/app/auth/router.py` | Added `activated_personas=user.activated_personas` to the auth router's `_user_to_response()` |

**Accumulation logic (in `service.py` → `update_user()`):**

```python
# After user.role = new_role and user.org_id = new_org_id:
new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
existing = user.activated_personas or []
if new_persona not in existing:
    user.activated_personas = existing + [new_persona]
```

**Key design decisions:**
- `activated_personas` is persisted in the DB (not PostHog-only) because PostHog's `$set` overwrites the array each time — without DB persistence, the accumulating array would be lost between sessions
- `null` means "never switched via the chevron" — distinct from `[]` (which shouldn't happen)
- The array only grows via the persona switch flow, NOT during initial onboarding
- The `previous_role is not None` guard in the router ensures onboarding (null → first role) doesn't fire events or accumulate personas

---

<a id="helix-implementation-identifyuser-fix"></a>
## Helix Implementation: `identifyUser()` Fix

**PR #494 status: NOT IMPLEMENTED** — This requires a follow-up change.

**Problem:** `identifyUser()` in `frontend/src/lib/posthog.ts` currently sets `email`, `name`, `role`, `org_id` via `$set` and `account_created_at`, `first_surface` via `$set_once`. It does NOT set `current_persona`. This means users who never switch personas will have no `current_persona` person property in PostHog, making cohort analysis by persona incomplete.

**Fix — edit `frontend/src/lib/posthog.ts` → `identifyUser()` function:**

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
| `activated_personas` | array | person ($set) + DB column | e.g., `["recruiter", "job_seeker"]` | All unique personas the user has tried via the switch flow. Persisted in DB as JSONB, sent to PostHog via `$set`. Only grows via persona switching, not onboarding. `null` in DB means never switched. |

---

## Backend Constants Reference

**File: `backend/app/shared/posthog_events.py`**

After PR #494 merges, this file will contain:

```python
# Persona Switching
PERSONA_UPDATED = "Persona Updated"
PERSONA_UPDATE_FAILED = "Persona Update Failed"

# Persona labels for PostHog persona-switching events.
# PROFESSIONAL maps to "job_seeker" (not "team_member") to match the
# user-facing label in the UI and the frontend analytics mapping.
ROLE_TO_PERSONA = {
    "HIRING_MANAGER": "hiring_manager",
    "RECRUITER": "recruiter",
    "PROFESSIONAL": "job_seeker",
}
```

**Important:** `ROLE_TO_PERSONA` is deliberately separate from `_ROLE_TO_ACTING_AS`. They map `PROFESSIONAL` to different values:
- `ROLE_TO_PERSONA["PROFESSIONAL"]` → `"job_seeker"` (analytics persona label, matches UI)
- `_ROLE_TO_ACTING_AS["PROFESSIONAL"]` → `"team_member"` (legacy acting_as property)

---

## Catalog Changes (applied on merge)

### Event Catalog (`docs/event-catalog.md`)

#### 1. Account & Persona Events — 3 events (already applied)

```md
| Switch Persona Button Clicked | Account | Intent  | User clicks the ⇄ chevron next to current persona in sidebar        | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `current_persona` | -- | -- | Not Started |
| Persona Updated               | Account | Success | Backend confirms persona switch after user selects a different persona | Backend  | `previous_persona`, `current_persona` | -- | `$set: current_persona, activated_personas` | Not Started |
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

### Event Schema (`docs/event-schema.md`)

#### 1. Standard Objects table — Persona row updated (already applied)

Example Events: `Switch Persona Button Clicked, Persona Updated`

#### 2. Intent vs Outcome table — row added (already applied)

```md
| Persona switch | Switch Persona Button Clicked | Persona Updated | Persona Update Failed |
```

---

## Summary: All Helix Codebase Changes

### Already done by PR #494 (will land on merge)

| File | Change |
|---|---|
| `backend/alembic/versions/29de6d7dba88_...py` | Migration: `ADD COLUMN activated_personas JSONB NULLABLE` |
| `backend/app/database/models/user.py` | Added `activated_personas` JSONB column |
| `backend/app/auth/dependencies.py` | Added `activated_personas` to `AuthUser` + `_user_to_auth_user()` |
| `backend/app/auth/schemas.py` | Added `activated_personas` to `UserResponse` |
| `backend/app/auth/router.py` | Added `activated_personas` to auth `_user_to_response()` |
| `backend/app/shared/posthog_events.py` | Added `PERSONA_UPDATED`, `PERSONA_UPDATE_FAILED`, `ROLE_TO_PERSONA` |
| `backend/app/users/service.py` | Added persona accumulation in `update_user()`, `activated_personas` in `_user_to_response()` |
| `backend/app/users/router.py` | Added try/except with `Persona Updated` + `Persona Update Failed` events, `activated_personas` in GET /me |
| `backend/tests/users/test_persona_switching.py` | 8 tests: success, onboarding skip, failure, non-role error skip, accumulation, dedup, onboarding→switch, GET /me |
| `frontend/src/lib/posthogEvents.ts` | Renamed to `SWITCH_PERSONA_BUTTON_CLICKED`, removed `PERSONA_SWITCHED` |
| `frontend/src/components/layout/Sidebar/RoleSwitcherDropdown.tsx` | Aligned properties, removed duplicate event |
| `frontend/src/components/layout/__tests__/RoleSwitcherDropdown.test.tsx` | Updated tests |

### Still needed (follow-up after PR #494 merges)

| File | Change | Why |
|---|---|---|
| `backend/app/users/router.py` | Add `"current_persona": new_persona` as regular event property in `Persona Updated` capture call (alongside `$set`) | Person properties show latest value, not value at event time — event property freezes it |
| `frontend/src/lib/posthog.ts` | Add `current_persona` to `identifyUser()` `$set` properties using `ROLE_TO_PERSONA` mapping | Users who never switch will otherwise have no `current_persona` in PostHog |
