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
  │    → fires: Persona Chevron Clicked
  │    → "Choose a role" dropdown opens
  │
  ├─ Step 2: Clicks on a different persona (e.g., Recruiter)
  │    → fires: Persona Updated
  │    → $set: current_persona = "recruiter"
  │    → $set: activated_personas (appends new persona, deduplicated)
  │
  └─ Step 3: New persona's home page loads
       → fires: Page Viewed
       → current_page_context reflects the new persona's landing page
       → current_persona person property is now queryable on this event
```

---

## New Events

### 1. Persona Chevron Clicked

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
posthog.capture('Persona Chevron Clicked', {
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

### 2. Persona Updated (replaces Persona Activated)

User selects a different persona from the "Choose a role" dropdown.

| Field | Value |
|-------|-------|
| **Area** | Account |
| **Type** | user_action |
| **Trigger** | User selects a different persona from "Choose a role" dropdown |
| **Source** | Frontend |
| **Group** | -- |
| **Status** | Not Started |

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | Action type |
| `action_value` | string | `hiring_manager_role_card`, `recruiter_role_card`, `job_seeker_role_card` | Exact card clicked in the dropdown, matches the persona selected |
| `current_page_context` | string | e.g., `hiring_manager_job_postings` | Page BEFORE the switch (user hasn't navigated yet) |
| `previous_page_context` | string | snake_case page identifier or null | Previous page before current one |
| `entity_type` | string | `persona` | Business object being acted on |
| `component` | string | `sidebar_persona_switcher_role_dropdown` | The "Choose a role" dropdown opened from the sidebar |
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on before switching |

**Property Updates:**

| Operation | Property | Description |
|---|---|---|
| `$set` | `current_persona` | Updated to the newly selected persona (`hiring_manager`, `recruiter`, `job_seeker`) |
| `$set` | `activated_personas` | Array of all unique personas the user has tried; grows over time |

**PostHog call:**

```javascript
const previousPersona = currentPersona;               // e.g., 'hiring_manager'
const newPersona = selectedPersona;                    // e.g., 'recruiter'

if (newPersona === previousPersona) {
  return; // no actual switch — do not fire event
}

const nextActivatedPersonas = Array.from(
  new Set([...(activatedPersonas ?? []), newPersona])
);

posthog.capture('Persona Updated', {
  action: 'click',
  action_value: `${newPersona}_role_card`,             // 'recruiter_role_card'
  current_page_context: currentPageContext,             // page BEFORE switch
  previous_page_context: getPreviousPageContext(),
  entity_type: 'persona',
  component: 'sidebar_persona_switcher_role_dropdown',
  previous_persona: previousPersona,
  $set: {
    current_persona: newPersona,
    activated_personas: nextActivatedPersonas,
  },
});
```

**Notes:**
- Does NOT fire if the user clicks on the persona they're already on (no change)
- `previous_persona` is an event property; the new persona is captured via `$set: current_persona`
- Switch patterns (e.g., hiring_manager → recruiter) can be analyzed by combining `previous_persona` with the updated `current_persona`
- `activated_personas` uses `Array.from(new Set([...]))` for deduplication and null-safety

---

### 3. Page Viewed (existing — no changes needed)

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

| Order | Event | What happens | current_persona (person property) |
|-------|-------|-------------|----------------------------------|
| 1 | Persona Chevron Clicked | Dropdown opens | Still the old persona |
| 2 | Persona Updated | User picks new persona | Updated to new persona |
| 3 | Page Viewed | New persona's home page loads | New persona (queryable) |

---

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Persona Switch Completion | Persona Chevron Clicked → Persona Updated | Measures conversion from exploring the switch to actually switching |
| Persona Switch Full Flow | Persona Chevron Clicked → Persona Updated → Page Viewed | Full switch flow including page load |

---

## New Property Details

| Property | Type | Scope | Values | Description |
|---|---|---|---|---|
| `previous_persona` | enum | event | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on before switching. Used only in Persona Updated. |

---

## Catalog Changes (to apply on merge)

### Event Catalog (`docs/event-catalog.md`)

#### 1. Account & Persona Events — add 2 new events, remove Persona Activated

**Remove:**
- `Persona Activated` row

**Add:**
```md
| Persona Chevron Clicked | Account | user_action | User clicks the ⇄ chevron next to current persona in sidebar | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Not Started |
| Persona Updated | Account | user_action | User selects a different persona from "Choose a role" dropdown | Frontend | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `previous_persona` | -- | `$set: current_persona, activated_personas` | Not Started |
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
- `action (user_action)` Used In → add `Persona Chevron Clicked, Persona Updated`
- `action_value` Used In → add `Persona Chevron Clicked, Persona Updated`
- `current_page_context` Used In → add `Persona Chevron Clicked, Persona Updated`
- `previous_page_context` Used In → add `Persona Chevron Clicked, Persona Updated`
- `component` Used In → add `Persona Chevron Clicked, Persona Updated`
- `entity_type` Used In → add `Persona Chevron Clicked, Persona Updated`

### Event Schema (`docs/event-schema.md`)

#### 1. Standard Objects table — update Persona

**Current:** `Persona Activated`
**New:** `Persona Chevron Clicked, Persona Updated`

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

#### 5. Sample code — add persona switching section

Add production-ready PostHog calls for all 3 events (Persona Chevron Clicked, Persona Updated, Page Viewed after switch).

#### 6. Sample code — update existing events

- **Page Viewed:** Add `isLoginPage` check (`window.location.pathname === '/signup'`) for `entry_point` + `$set_once` — fires only on the login page, not on every page view
- **Login Started:** Remove `$set_once` block, remove `context_object_type`, `context_object_id`
- **Account Created:** Remove `entry_point`, add `$set: current_persona, activated_personas: [persona]`
- **Intro Completed:** Remove `entry_point`
- **Share Button Clicked:** Remove `entry_point: null`
