# User Action Event Schema

**Schema Version:** 1.0
**Event Type:** `user_action`
**Scope:** This document defines the `user_action` event type ONLY. Separate schema documents exist for: `system_outcome`, `page_view`, `lifecycle`, `error`, `page_context_update`, `flow_registry`.

---

## Purpose

This schema defines how to track `user_action` events in product analytics. A `user_action` event fires ONLY when a user performs a meaningful, intentional interaction in the product.

This schema is designed for use by an agentic AI to:

1. Identify which interactions on a frontend page or design spec qualify as `user_action`
2. Assign the correct event properties with consistent naming
3. Infer user flows from a page or feature
4. Generate tracking plans and instrumentation specs

---

## Definition

A `user_action` event captures:

- **Who** performed the action (identity + role)
- **What** they interacted with (action + target element)
- **Where** in the product it happened (page, component, surface)
- **What business object** it related to (entity type + scope)

---

## When to Fire

Fire a `user_action` ONLY when ALL of these are true:

1. The user intentionally interacts with a visible UI element
2. The interaction changes state, starts a flow, applies a choice, opens content, or triggers a meaningful request
3. The interaction has business meaning beyond passive rendering

### Qualifies as user_action

- Clicking a CTA or navigation element
- Submitting a form or wizard step (captures all field inputs at once — do NOT track individual field typing)
- Toggling a binary control (checkbox, switch, expand/collapse)
- Opening or closing an important modal, drawer, or panel

### Does NOT qualify as user_action

- Automatic page load behavior → use `page_view` event type instead
- Background API calls or data fetches → use `system_outcome` event type instead
- System-rendered defaults or auto-populated fields
- Passive component loading or rendering
- Session replay / instrumentation signals
- Automatic refreshes, polling, or heartbeat calls
- Hover over non-interactive elements (tooltips are edge cases — see Criticality Rules below)

---

## Canonical Shape

The `user_action` event only includes properties that are manually set by the developer. Identity, device, and timing properties are auto-captured by the PostHog SDK and MUST NOT be set manually.

```javascript
capture(EVENT_NAME, {
  action: '',
  action_value: '',
  current_page_context: '',
  previous_page_context: null,
  entry_point: null,
  entity_type: '',
  component: '',
  context_object_type: null,
  context_object_id: null,
});
```

### Auto-Captured Properties (PostHog SDK — do NOT set manually)

These are automatically included on every event by the PostHog SDK:

| Property | Description | Source |
|---|---|---|
| `distinct_id` | User identifier | Set via `posthog.identify()` after auth |
| `$current_url` | Full page URL | PostHog SDK |
| `$referrer` | HTTP referrer | PostHog SDK |
| `$browser` | Browser name | PostHog SDK |
| `$os` | Operating system | PostHog SDK |
| `$device_type` | desktop / mobile / tablet | PostHog SDK |
| `$screen_height` / `$screen_width` | Screen dimensions | PostHog SDK |
| `timestamp` | Event timestamp | PostHog SDK |
| `$session_id` | Session identifier | PostHog SDK |

### Person Properties (set via `identifyUser()`, not per-event)

These are set on the user profile via `posthog.identify()` and are available on all events for that user. They are NOT included in event capture calls.

| Property | Scope | Description |
|---|---|---|
| `email` | `$set` | User's current email |
| `name` | `$set` | User's current name |
| `org_id` | `$set` | User's current organization ID |
| `current_persona` | `$set` | Active persona (updated on login + persona switch) |
| `first_persona` | `$set_once` | First persona chosen during onboarding |
| `account_created_at` | `$set_once` | Account creation timestamp |

---

## Property Requirements

Each property is classified as **Required** (MUST be present, MUST NOT be null/empty) or **Conditional** (include when applicable, set to `null` when not).

**Rule:** When a conditional property does not apply, set it to `null`. Do NOT use empty strings `""` for missing values. Do NOT omit the key entirely — always include it as `null` so the schema shape is consistent across all events.

---

## Property Documentation

### 1. Action Properties

All action properties are **Required**.

#### `action`
- **Required**
- What it is: The physical user interaction type.
- What it tracks: HOW the user interacted.
- Allowed values (closed list — do NOT invent new values):

| Value | Use when |
|-------|----------|
| `click` | User clicks/taps a button, link, card, row, or any clickable element |
| `submit` | User submits a form, wizard step, or multi-field entry (distinct from a single click) |
| `toggle` | User switches a binary control (on/off, expand/collapse, checkbox) |

- Example: `"action": "click"`
- **Note:** For `user_action` events, the `action` value IS the event name in the analytics platform. The event is logged as `click`, `select`, `submit`, etc. All other context (what was clicked, why, where) comes from the accompanying properties.

#### `action_value`
- **Required**
- What it is: The specific UI element the user interacted with.
- What it tracks: WHAT was acted upon in the interface.
- Naming pattern: `<object>_<element_type>` in `snake_case`.
- MUST be specific and descriptive. MUST NOT be generic.

| Good | Bad | Why bad |
|------|-----|---------|
| `start_sequence_button` | `button` | No specificity — which button? |
| `candidate_row_checkbox` | `checkbox` | No context — checkbox for what? |
| `project_filter_dropdown` | `dropdown` | No business meaning |
| `search_input_field` | `input` | Ambiguous |
| `save_search_button` | `cta` | Generic, meaningless |
| `job_title_link` | `submit` | Describes the action, not the element |

- Example: `"action_value": "start_sequence_button"`

---

### 2. Context Properties

#### `current_page_context`
- **Required**
- What it is: The product page or workflow screen where the action happened.
- What it tracks: WHERE in the user journey the event occurred.
- Naming: Use `snake_case`. Use `/` separator for hierarchical pages.
- Format options:
  - Simple: `search`, `dashboard`, `settings`
  - Hierarchical: `search/results_page`, `workspace/sequence_setup`, `settings/notifications`
- Example: `"current_page_context": "search/results_page"`

#### `previous_page_context`
- **Conditional** — Include when navigation context is available.
- What it is: The immediately previous page or screen before the current one.
- What it tracks: Step-to-step navigation context for path analysis.
- Same naming convention as `current_page_context`.
- Example: `"previous_page_context": "search/results_page"`
- When not available: `"previous_page_context": null`

#### `entry_point`
- **Conditional** — Include when attribution context is known.
- What it is: How the user arrived at the current page or flow.
- What it tracks: Journey source and attribution. Critical for understanding what drives users to key actions.
- Common values: `sidebar_navigation`, `email_link`, `search_results`, `notification`, `direct_url`, `deeplink`, `referral_link`, `in_app_banner`
- Example: `"entry_point": "search_results"`
- When unknown: `"entry_point": null`

---

### 3. Scope Properties

These properties identify the container or scope the action happens within. Distinct from Entity properties (which capture WHAT the action targets), scope properties capture the CONTEXT the action occurs inside.

#### `context_object_type`
- **Conditional** — Include when the action occurs within a specific business scope.
- What it is: The type of business container this action belongs to.
- What it tracks: Which project, workspace, campaign, or container scopes the action.
- Values: Defined per product in product configuration (e.g., `project`, `workspace`, `campaign`, `board`).
- Example: `"context_object_type": "project"`
- When not scoped: `"context_object_type": null`

#### `context_object_id`
- **Conditional** — MUST be present whenever `context_object_type` is present.
- What it is: The unique identifier of the scoping business object.
- What it tracks: Which specific project/workspace/campaign this action occurred within.
- Example: `"context_object_id": "proj_333"`
- When not scoped: `"context_object_id": null`

---

### 4. Entity Properties

Entity properties capture WHAT business object the action targets.

#### `entity_type`
- **Required**
- What it is: The business object the action is about.
- What it tracks: What real product entity the user is acting on.
- Values: Defined per product in product configuration (e.g., `candidate`, `job`, `project`, `sequence`, `message`, `filter`).
- Example: `"entity_type": "candidate"`

#### `entity_count`
- **Conditional** — Include ONLY for bulk actions where count > 1.
- What it is: Number of entities involved in the action.
- What it tracks: Scope of bulk operations. Omit for single-entity actions — if absent, count is implicitly 1.
- Rule: For bulk actions, set to the actual count. Do NOT fire one event per entity for bulk actions; fire one event with the total count.
- Example (bulk): `"entity_count": 25`
- When single entity or not applicable: omit the property entirely.

---

### 5. UI Context Properties

#### `component`
- **Required**
- What it is: The specific UI container or surface where the action occurred.
- What it tracks: Which part of the interface generated the event. Critical for understanding UI performance and layout effectiveness.
- Naming pattern: `<feature/page>_<section>` in `snake_case`. MUST be specific and descriptive — do NOT use generic names like `form`, `header`, `modal`.
- Wizard rule: When the screen is part of a multi-step funnel or wizard (e.g., job creation, resume builder, onboarding) where the end goal is to produce something from user input, add `_wizard_` between the feature name and the section (e.g., `job_creation_wizard_form`). This distinguishes step-based flows from standalone pages.
- Naming consistency rule: All components on the same page or wizard MUST share the same prefix (e.g., `job_creation_wizard_form`, `job_creation_wizard_header` — not `job_details_form`, `job_creation_wizard_header`). The prefix should match the feature/wizard name, and the suffix should identify the sub-section.

| Good | Bad | Why bad |
|------|-----|---------|
| `job_creation_wizard_form` | `form` | Too generic — which form? |
| `job_creation_wizard_header` | `header` | No context — header of what? |
| `resume_builder_wizard_form` | `resume_form` | Missing wizard prefix, not specific |
| `candidate_search_sidebar` | `sidebar` | Ambiguous |
| `pipeline_review_table` | `table` | No business context |

- Examples: `"component": "job_creation_wizard_form"`, `"component": "candidate_search_results_grid"`, `"component": "onboarding_wizard_header"`

---

## Criticality Rules

Not every interaction deserves an event. Use this decision tree:

```
Is the interaction intentional and user-initiated?
├── NO → Do NOT track as user_action
└── YES
    ├── Does it change state, start a flow, or trigger a request?
    │   ├── YES → TRACK as user_action
    │   └── NO
    │       ├── Does it reveal significant content (e.g., expanding a drawer, opening a modal)?
    │       │   ├── YES → TRACK as user_action
    │       │   └── NO
    │       │       ├── Is it a navigation action (tab switch, page link)?
    │       │       │   ├── YES → TRACK as user_action
    │       │       │   └── NO → Do NOT track as user_action
    │       │       └── (e.g., tooltip hover, accordion toggle for non-critical content → SKIP)
```

**Edge cases:**

- **Tooltips:** Do NOT track unless the tooltip contains critical decision-making information.
- **Accordion toggles:** Track only if the section contains a distinct workflow or content block.
- **Tab switches within a page:** TRACK — these represent meaningful navigation choices.
- **Infinite scroll / lazy load triggers:** Do NOT track as user_action (these are system behaviors triggered by scroll position).
- **Copy-to-clipboard:** TRACK — this is an intentional action with clear intent.

---

## Full Examples

### Example 1: User clicks "Start Sequence" for 25 selected candidates

```javascript
capture('Start Sequence Button Clicked', {
  action: 'click',
  action_value: 'start_sequence_button',
  current_page_context: 'outreach/sequence_setup',
  previous_page_context: 'search/results_page',
  entry_point: 'search_results',
  entity_type: 'candidate',
  entity_count: 25,
  component: 'outreach_sequence_modal',
  context_object_type: 'project',
  context_object_id: 'proj_333',
});
```

### Example 2: User clicks Next on job details step

```javascript
capture('Job Wizard Step Completed', {
  action: 'click',
  action_value: 'next_button',
  current_page_context: 'job_creation/job_details',
  previous_page_context: null,
  entry_point: null,
  entity_type: 'job',
  component: 'job_creation_wizard_form',
  context_object_type: null,
  context_object_id: null,
});
```

### Example 3: User clicks Close to exit job creation

```javascript
capture('Job Wizard Exited', {
  action: 'click',
  action_value: 'close_button',
  current_page_context: 'job_creation/job_details',
  previous_page_context: null,
  entry_point: null,
  entity_type: 'job',
  component: 'job_creation_wizard_header',
  context_object_type: null,
  context_object_id: null,
});
```

### Example 4: User clicks "+ Create Job Posting" on HM home page (header)

```javascript
capture(CREATE_JOB_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'create_job_posting_button',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'job_postings_page_header',
  context_object_type: null,
  context_object_id: null,
});
```

---

## Rules for Agentic AI

When reviewing a frontend page or design spec, the AI MUST follow these rules to identify and generate `user_action` events.

### A. Classification Rules

An interaction qualifies as `user_action` if ALL of these are true:
1. The user intentionally interacts with a visible UI element
2. The action changes state, starts a flow, applies a choice, opens content, or triggers a meaningful request
3. The action has business meaning beyond passive rendering

An interaction does NOT qualify as `user_action` if ANY of these are true:
1. The event happens automatically on page load
2. The system fetches or computes in the background
3. The event is only a technical API call with no user trigger
4. The event is a component render/mount with no user intent

### B. Property Assignment Rules

For every `user_action` event, the AI MUST determine:

| Property | How to determine | Fallback if unknown |
|----------|------------------|---------------------|
| `action` | Match the physical interaction to the allowed values list (`click`, `submit`, `toggle`) | MUST match list — if unsure, default to `click` |
| `action_value` | Identify the specific UI element from the design/spec | MUST be specific — never use generic names |
| `current_page_context` | Read from the page/screen name in the design or spec | MUST be provided — use the most specific page name available |
| `entity_type` | Identify the business object being acted upon | MUST be provided — check product configuration for valid values |
| `entity_count` | Include ONLY when bulk action (count > 1) | Omit for single-entity actions |
| `component` | Identify the UI container (modal, sidebar, table, etc.) | MUST be provided — use the most specific container name |

### C. Completeness Rules

For every page or screen reviewed, the AI MUST ensure:
1. Every CTA (primary and secondary) has a corresponding `user_action` event
2. Every form submission has a `user_action` event
3. Every navigation action that leaves the page has a `user_action` event
4. Bulk actions are tracked as a single event with `entity_count`, not per-entity events

### D. What to Flag for Human Review

The AI MUST flag (not skip, not guess) when:
1. A UI element's purpose is ambiguous and the correct `action_value` cannot be determined
2. An interaction could be either `user_action` or `system_outcome` (e.g., auto-save on blur)
3. A page has no identifiable `user_action` events (this may indicate a passive/display-only screen, or a gap in the spec)
4. An `entity_type` is not in the product configuration

---

## Naming Quick Reference

### `action` — Closed list (do not extend without schema update)
`click` · `submit` · `toggle`

### `action_value` — Pattern: `<object>_<element_type>`
`start_sequence_button` · `candidate_card` · `next_button` · `close_button` · `save_search_button` · `submit_button`

---

## AI Workflow: Generating a Tracking Plan from a Design Spec

When given a page, screen, or feature spec, the AI MUST follow this sequence:

1. **Scan** — Identify all interactive elements on the page (buttons, links, forms, toggles, cards, modals).
2. **Filter** — Apply the Classification Rules (Section A) to determine which interactions qualify as `user_action`. Discard passive/system behaviors. For form-heavy screens, track the form `submit` rather than individual field inputs — field state is captured by the backend.
3. **Assign** — For each qualifying interaction, determine all Required properties using the Property Assignment Rules (Section B).
4. **Validate** — Apply Completeness Rules (Section C). Ensure every CTA, form, and navigation element has coverage.
5. **Flag** — Flag any ambiguities per Section D. Do NOT guess — mark for human review.
6. **Output** — Produce a structured event list grouped by page/screen, with all properties filled.
7. **Handoff** — Note where corresponding `system_outcome`, `page_view`, or `error` events should exist (these will be defined in their respective schema documents).
