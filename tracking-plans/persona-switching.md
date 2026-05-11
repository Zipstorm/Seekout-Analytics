# Tracking Plan: Persona Switching

**Product:** Helix (SeekOut.ai)
**Feature:** Persona switching flow
**Date:** 2026-05-11
**Related PRD:** —

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## User Flow

```
User is on any page (e.g., HM Job Postings)
  │
  ├─ Step 1: Clicks ⇄ chevron next to current persona in sidebar
  │    → fires: Persona Chevron Clicked
  │    → "Choose a role" dropdown opens
  │
  ├─ Step 2: Clicks on a different persona (e.g., Recruiter)
  │    → fires: Persona Updated
  │    → $set: current_persona = "recruiter"
  │    → $set: activated_personas (appends new persona)
  │
  └─ Step 3: New persona's home page loads
       → fires: Page Viewed
       → current_page_context reflects the new persona's landing page
       → current_persona person property is now queryable on this event
```

---

## Events

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

### 2. Persona Updated

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
    activated_personas: [...activatedPersonas, newPersona],  // append if not already present
  },
});
```

**Notes:**
- Does NOT fire if the user clicks on the persona they're already on (no change)
- `previous_persona` is an event property; the new persona is captured via `$set: current_persona`
- Switch patterns (e.g., hiring_manager → recruiter) can be analyzed by combining `previous_persona` with the updated `current_persona`

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

**Properties:**

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | e.g., `recruiter_home`, `hiring_manager_job_postings`, `job_seeker_home` | The new persona's landing page |
| `previous_page_context` | string | e.g., `hiring_manager_job_postings` | The page before the switch |

**PostHog call:**

```javascript
posthog.capture('Page Viewed', {
  current_page_context: newPersonaPageContext,          // e.g., 'recruiter_home'
  previous_page_context: previousPageContext,           // page before the switch
});
```

**Notes:**
- No changes needed to this event — it already exists and is Live
- No `$set_once` needed — first-touch attribution (`entry_point`, `first_referrer`, `first_landing_url`) is handled by Login Started
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

## Property Details

| Property | Type | Values | Description |
|---|---|---|---|
| `previous_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | The persona the user was on before switching. Used only in Persona Updated. |
| `current_page_context` | string | snake_case page identifier | Page where the chevron was clicked. Already exists in Property Dictionary. |

---

## Catalog Updates

- [x] Persona Chevron Clicked → Account & Persona Events (already in catalog)
- [x] Persona Updated → Account & Persona Events (already in catalog, renamed from Persona Activated)
- [ ] Page Viewed → no changes needed (already Live)
- [x] New property added to Property Dictionary: `previous_persona`
- [x] Removed properties from Property Dictionary: `persona`, `trigger`
- [x] Removed event entry added: Persona Activated → Persona Updated
