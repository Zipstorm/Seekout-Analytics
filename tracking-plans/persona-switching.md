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
| **Trigger** | Backend confirms persona switch after user selects a different persona |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on before switching |

**Property Updates:**

| Operation | Property | Description |
|---|---|---|
| `$set` | `current_persona` | Updated to the newly selected persona (`hiring_manager`, `recruiter`, `job_seeker`) |
| `$set` | `activated_personas` | Array of all unique personas the user has tried; grows over time, deduplicated |

**PostHog call (Python SDK — backend):**

```python
previous_persona = user.current_persona  # e.g., 'hiring_manager'
new_persona = request.new_persona        # e.g., 'recruiter'

# Only fire if persona actually changed
if new_persona != previous_persona:
    activated = list(set((user.activated_personas or []) + [new_persona]))

    posthog.capture(
        event='Persona Updated',
        distinct_id=str(user.id),
        properties={
            'previous_persona': previous_persona,
            '$set': {
                'current_persona': new_persona,
                'activated_personas': activated,
            },
        },
    )
```

**Notes:**
- Fires from the backend after the API confirms the switch — not on the frontend card click
- Does NOT fire if the persona didn't actually change
- `previous_persona` is an event property; the new persona is captured via `$set: current_persona`
- Switch patterns (e.g., hiring_manager → recruiter) can be analyzed by combining `previous_persona` with the updated `current_persona`
- `activated_personas` is deduplicated server-side

---

### 3. Persona Update Failed (new)

Server returns error when persona switch fails.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | Failure |
| **Trigger** | Backend returns error on persona switch attempt |
| **Source** | Backend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on when the switch was attempted |
| `target_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user tried to switch to |
| `error_reason` | string | system error description | What went wrong |
| `error_category` | enum | `network`, `permission`, `validation`, `server`, `timeout` | Error classification |

**PostHog call (Python SDK — backend):**

```python
posthog.capture(
    event='Persona Update Failed',
    distinct_id=str(user.id),
    properties={
        'previous_persona': user.current_persona,
        'target_persona': request.new_persona,
        'error_reason': str(e),
        'error_category': 'server',  # network, permission, validation, server, timeout
    },
)
```

**Notes:**
- Fires from the backend when the persona switch API returns an error
- `previous_persona` stays unchanged (switch didn't happen)
- `target_persona` captures what the user tried to switch to (distinct from `previous_persona` on Persona Updated which is the "from" persona)

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
