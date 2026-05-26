# Tracking Plan: Persona Switching

**Product:** Helix (SeekOut.ai)
**Feature:** Persona switching flow
**Date:** 2026-05-11
**Related PRD:** —

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## User Flow

```text
User is on any page (e.g., HM Job Postings)
  │
  ├─ Step 1: Clicks ⇄ chevron next to current persona in sidebar
  │    → fires: Switch Persona Button Clicked (Frontend)
  │    → "Choose a role" dropdown opens
  │
  ├─ Step 2: Clicks on a different persona (e.g., Recruiter)
  │    → Frontend calls API to switch persona
  │    ├─ Success → fires: Persona Updated (Backend)
  │    │    → $set: current_persona = "recruiter"
  │    │    → $set: activated_personas (deduplicated)
  │    └─ Failure → fires: Persona Update Failed (Backend)
  │         → current_persona unchanged
  │
  └─ Step 3: New persona's home page loads (on success only)
       → fires: Page Viewed (Frontend)
       → current_page_context reflects the new persona's landing page
       → current_persona person property is now queryable on this event
```

---

## New Events

### 1. Switch Persona Button Clicked

User explores the persona switching option by clicking the ⇄ chevron.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | user_action |
| **Trigger** | User clicks the ⇄ chevron next to current persona in sidebar |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `persona_switch_chevron` | The ⇄ icon has no visible text — this identifies the chevron toggle |
| `current_page_context` | string | e.g., `hiring_manager_job_postings`, `recruiter_home`, `job_seeker_home` | Page the user was on when they clicked the chevron |
| `previous_page_context` | string | snake_case page identifier or null | Previous page before current one |
| `entity_type` | string | `persona` | Business object being acted on |
| `component` | string | `sidebar_persona_switcher` | The persona label + chevron area in the left sidebar |

**PostHog call:**

```javascript
posthog.capture('Switch Persona Button Clicked', {
  action: 'click',
  action_value: 'persona_switch_chevron',
  current_page_context: currentPageContext,           // e.g., 'hiring_manager_job_postings'
  previous_page_context: getPreviousPageContext(),
  entity_type: 'persona',
  component: 'sidebar_persona_switcher',
});
```

**Notes:**
- Fires regardless of whether the user actually switches personas
- Useful for measuring awareness/exploration of persona switching
- `current_persona` is available as a person property — tells us which persona they were in when they clicked

---

### 2. Persona Updated (replaces Persona Activated) — Success

Server confirms persona switch succeeded.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | Success |
| **Trigger** | Backend confirms persona switch via `PATCH /api/users/me` with `{ role: "..." }` |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Helix code context:**
- **API endpoint:** `PATCH /api/users/me` in `users/router.py` → `update_my_profile()`
- **Service:** `users/service.py` → `update_user()` — validates `UserRole` enum, updates `user.role` + `user.org_id`
- **User model:** `user.role` (enum: `HIRING_MANAGER`, `RECRUITER`, `PROFESSIONAL`, `ADMIN`) — no `current_persona` column; persona is derived via `ROLE_TO_PERSONA` mapping
- **PostHog client:** `shared/posthog_client.py` → `capture(distinct_id, event, properties, groups)`
- **Event constants:** `shared/posthog_events.py` — add new constants here

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `user.role` BEFORE the update via `ROLE_TO_PERSONA` |

**Property Updates:**

| Operation | Property | Description |
|---|---|---|
| `$set` | `current_persona` | Updated to the newly selected persona (`hiring_manager`, `recruiter`, `job_seeker`) |
| `$set` | `activated_personas` | Array of all unique personas the user has tried; grows over time, deduplicated |

**PostHog call — add to `users/router.py` → `update_my_profile()`:**

```python
# In users/router.py — after service.update_user() succeeds and before return
# Only fire when the role field was part of the update and actually changed

from app.shared.posthog_events import (
    PERSONA_UPDATED,
    PERSONA_UPDATE_FAILED,
    get_acting_as,  # maps UserRole → persona string
)

ROLE_TO_PERSONA = {
    "HIRING_MANAGER": "hiring_manager",
    "RECRUITER": "recruiter",
    "PROFESSIONAL": "job_seeker",
}

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    dto: UpdateUserDto,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    previous_role = current_user.role  # role BEFORE update
    previous_persona = ROLE_TO_PERSONA.get(previous_role, "unknown") if previous_role else "unknown"

    try:
        result = await service.update_user(db, current_user.id, dto)
        await db.commit()

        # Fire Persona Updated only when role actually changed
        if dto.role is not None and dto.role != previous_role:
            new_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
            posthog_client.capture(
                str(current_user.id),
                PERSONA_UPDATED,
                {
                    "previous_persona": previous_persona,
                    "$set": {
                        "current_persona": new_persona,
                        "activated_personas": list(set(
                            (current_user.activated_personas or []) + [new_persona]
                        )),
                    },
                },
            )

        return result

    except Exception as e:
        if dto.role is not None:
            target_persona = ROLE_TO_PERSONA.get(dto.role, "unknown")
            posthog_client.capture(
                str(current_user.id),
                PERSONA_UPDATE_FAILED,
                {
                    "previous_persona": previous_persona,
                    "target_persona": target_persona,
                    "error_reason": str(e),
                    "error_category": "validation" if isinstance(e, (ValueError, BadRequestException)) else "server",
                },
            )
        raise
```

**New constants for `shared/posthog_events.py`:**

```python
# Persona switching
PERSONA_UPDATED = "Persona Updated"
PERSONA_UPDATE_FAILED = "Persona Update Failed"
```

**Notes:**
- Fires from `users/router.py` after `service.update_user()` + `db.commit()` succeeds
- Only fires when `dto.role` is set AND differs from `current_user.role`
- `user.role` is a `UserRole` enum (`HIRING_MANAGER`, `RECRUITER`, `PROFESSIONAL`) — mapped to persona strings via `ROLE_TO_PERSONA`
- `activated_personas` is stored as a JSONB column on the `users` table (added via Alembic migration `6617a6ad20a5`). The service layer (`users/service.py`) appends the new persona on every role change, so the DB array accumulates over time. The router reads it from `current_user.activated_personas` and sends it to PostHog via `$set`.
- `current_persona` is NOT stored in DB — it is derived from `ROLE_TO_PERSONA` at event-capture time and set as a PostHog person property only

---

### 3. Persona Update Failed (new)

Server returns error when persona switch fails.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | Failure |
| **Trigger** | `service.update_user()` raises exception during persona switch |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `current_user.role` (unchanged — switch failed) |
| `target_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Derived from `dto.role` — what the user tried to switch to |
| `error_reason` | string | system error description | `str(e)` from the caught exception |
| `error_category` | enum | `validation`, `server` | `validation` for `ValueError`/`BadRequestException`, `server` for others |

**Notes:**
- Fires in the `except` block of `update_my_profile()` when `dto.role` is set
- `previous_persona` stays unchanged (switch didn't happen)
- Common failure: invalid role enum value → `ValueError` from `UserRole(dto.role)` in `service.update_user()`
- Org resolution failure in `ensure_org_for_role()` would also trigger this

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
  current_page_context: newPersonaPageContext,          // e.g., 'recruiter_home'
  previous_page_context: previousPageContext,           // page before the switch
});
```

**Notes:**
- No changes needed to this event — it already exists and is Live
- No `$set_once` needed — first-touch attribution is handled by the Page Viewed on the login page (`/signup` URL)
- After Persona Updated fires, `current_persona` person property is already updated, so this Page Viewed is automatically associated with the new persona in PostHog queries

---

## Event Sequence

| Order | Event | Source | What happens | current_persona (person property) |
|-------|-------|--------|-------------|----------------------------------|
| 1 | Switch Persona Button Clicked | Frontend | Dropdown opens | Still the old persona |
| 2a | Persona Updated | Backend | Server confirms switch | Updated to new persona |
| 2b | Persona Update Failed | Backend | Server returns error | Unchanged (switch failed) |
| 3 | Page Viewed | Frontend | New persona's home page loads | New persona (queryable) |

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

---

## Catalog Changes (to apply on merge)

### Event Catalog (`docs/event-catalog.md`)

#### 1. Account & Persona Events — add 3 new events, remove Persona Activated

**Remove:**
- `Persona Activated` row

**Add:**
```md
| Switch Persona Button Clicked | Account | Intent  | User clicks the ⇄ chevron next to current persona in sidebar        | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Not Started |
| Persona Updated               | Account | Success | Backend confirms persona switch after user selects a different persona | Backend  | `previous_persona` | -- | `$set: current_persona, activated_personas` | Not Started |
| Persona Update Failed          | Account | Failure | Backend returns error on persona switch attempt                       | Backend  | `previous_persona`, `target_persona`, `error_reason`, `error_category` | -- | -- | Not Started |
```

#### 2. Account Created — add `$set: current_persona, activated_personas`

**Current:** `$set_once: first_persona, account_created_at, referred_by`
**New:** `$set: current_persona, activated_personas`; `$set_once: first_persona, account_created_at, referred_by`

#### 3. Login & Onboarding Events — clean up entry_point

**Page Viewed:**
- Remove `entry_point` from event properties (keep only `current_page_context`, `previous_page_context`)
- Add `entry_point` as event property **only on the login page** (detected via `window.location.pathname === '/signup'`)
- Move `$set_once: entry_point, first_referrer, first_landing_url` here (from Login Started) — fires only on the `/signup` page

**Login Started:**
- Keep `entry_point` as event property
- Remove `$set_once` block (moved to Page Viewed)

**Account Created:**
- Remove `entry_point` from event properties

**Intro Completed:**
- Remove `entry_point` from event properties

#### 4. Removed Events table — add entry

```md
| Persona Activated | Persona Updated | Renamed — "Activated" implied adding a new persona; "Updated" reflects switching between existing personas | May 2026 |
```

#### 5. Property Dictionary — updates

**Remove:**
- `persona` (no longer used)
- `trigger` (no longer used)

**Add:**
- `previous_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | Persona Updated

**Update:**
- `first_persona` Scope → `event, person ($set_once)` (currently says `person ($set_once)` only — missing event scope)
- `current_persona` Used In → `Account Created, Persona Updated (person property)`
- `entry_point` Used In → `Page Viewed, Login Started`
- `action (user_action)` Used In → add `Switch Persona Button Clicked`
- `action_value` Used In → add `Switch Persona Button Clicked`
- `current_page_context` Used In → add `Switch Persona Button Clicked`
- `previous_page_context` Used In → add `Switch Persona Button Clicked`
- `component` Used In → add `Switch Persona Button Clicked`
- `entity_type` Used In → add `Switch Persona Button Clicked`
- `error_reason` Used In → add `Persona Update Failed`
- `error_category` Used In → add `Persona Update Failed`

**Add:**
- `target_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | Persona Update Failed

### Event Schema (`docs/event-schema.md`)

#### 1. Standard Objects table — update Persona

**Current:** `Persona Activated`
**New:** `Switch Persona Button Clicked, Persona Updated`

#### 2. Person Properties `$set_once` table

**Update Set By:**
- `entry_point` → `Page Viewed (login page — `/signup` URL)`
- `first_referrer` → `Page Viewed (login page — `/signup` URL)`
- `first_landing_url` → `Page Viewed (login page — `/signup` URL)`

#### 3. Person Properties `$set` table

**Update:**
- `current_persona` Set By → `Account Created, Persona Updated, identifyUser()`
- `activated_personas` Set By → `Account Created, Persona Updated`

#### 4. Three persona properties explanation

Update to mention:
- `activated_personas` is seeded with `[first_persona]` on Account Created
- `current_persona` is set on Account Created and updated via Persona Updated

#### 5. Intent vs Outcome table — add persona switching row

```md
| Persona switch | Switch Persona Button Clicked | Persona Updated | Persona Update Failed |
```

#### 6. Sample code — add persona switching section

Add production-ready PostHog calls for all 4 events (Switch Persona Button Clicked, Persona Updated, Persona Update Failed, Page Viewed after switch).

#### 7. Sample code — update existing events

- **Page Viewed:** Add `isLoginPage` check (`window.location.pathname === '/signup'`) for `entry_point` + `$set_once` — fires only on the login page, not on every page view
- **Login Started:** Remove `$set_once` block, remove `context_object_type`, `context_object_id`
- **Account Created:** Remove `entry_point`, add `$set: current_persona, activated_personas: [persona]`
- **Intro Completed:** Remove `entry_point`
- **Share Button Clicked:** Remove `entry_point: null`
