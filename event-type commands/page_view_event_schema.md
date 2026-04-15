# Page View Event Schema

**Schema Version:** 1.0
**Event Type:** `page_view`
**Scope:** This document defines the `page_view` event type ONLY. Separate schema documents exist for: `user_action`, `system_outcome`, `lifecycle`, `error`, `page_context_update`, `flow_registry`.

---

## Purpose

This schema defines how to track `page_view` events in product analytics. A `page_view` event fires when a user lands on or is shown a meaningful product page, screen, or distinct view state.

This schema is designed for use by an agentic AI to:

1. Identify which pages, screens, or routed views qualify as `page_view`
2. Assign the correct page-level properties with consistent naming
3. Infer navigation flows across the product
4. Generate tracking plans and instrumentation specs for page-level analytics

---

## Definition

A `page_view` event captures:

- **Who** viewed the page (identity + role)
- **What** page or screen was viewed
- **Where** the user came from (navigation context)
- **How** the user arrived there (entry attribution)
- **What business scope** the page belonged to
- **What platform/device context** the page was viewed on

A `page_view` event represents a meaningful view of a product surface, not a component render or backend load.

---

## When to Fire

Fire a `page_view` ONLY when ALL of these are true:

1. The user lands on or is shown a meaningful page, screen, or routed product view
2. The view represents a distinct navigational state in the product (not just a UI change)
3. The view is meaningful for journey analysis, funnel analysis, or feature adoption
4. The view is user-visible and represents a meaningful product state, not caused by background processes or system-only updates
5. The page represents a new state in the user journey, either through:
   - navigation (URL/route change), OR
   - a clearly distinct screen/state treated as a page by the product

### Qualifies as page_view

- Initial landing on a page after login or session start
- Moving from one routed page to another (URL/route change)
- Navigating using browser back/forward buttons to a meaningful page
- Re-entering a page via user-initiated browser refresh/reload, deep link, or external entry (email, notification, etc.)
- Opening a full-screen workflow step that is treated as a distinct screen
- Viewing a major tab/state only if it behaves like a separate page in the product
- Landing on a page after completing a redirect chain (final meaningful destination only)
- Viewing a distinct full-page error or fallback screen
- Opening a page in a new tab or window (counts as a separate page view)
- Entering a page with a distinct page identity or business scope through navigation, route change, or a product-defined screen transition

### Does NOT qualify as page_view

- Component render or mount within a page (tables, cards, sections, modules)
- Lazy loading, infinite scroll, or content loading within the same page
- Filter, sort, pagination, or other same-page state changes that do not create a new navigational state
- Modal, drawer, tooltip, or panel opens that do not replace the page context
- Re-renders caused by state updates or UI refreshes
- Background refreshes, polling, or silent data updates
- Intermediate technical redirects (only track the final destination page)
- Scroll-based visibility or viewport exposure of elements
- Hover interactions or passive UI exposure
- Inline errors within a page (handled via error events instead)
- Wizard step transitions if the wizard is treated as a single page (no distinct screen/state)
- Query parameter changes that do not result in a meaningful change in page identity or navigational state
- Same-page context changes that should be tracked through `page_context_update`
- System-triggered refreshes, silent reloads, or background re-fetching of the same page state

---

## Canonical Shape

The `page_view` event only includes properties that are manually set by the developer. Identity, device, and timing properties are auto-captured by the PostHog SDK and MUST NOT be set manually.

```javascript
capture(PAGE_VIEWED, {
  current_page_context: '',
  previous_page_context: null,
  entry_point: null,
  context_object_type: null,
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

### 1. View Context Properties

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
- What it is: The specific mechanism that brought the user to the current page — descriptive enough to distinguish HOW they arrived, not just where they came from.
- What it tracks: Journey source and attribution. Critical for understanding what drives users to key pages. Must NOT duplicate `previous_page_context` — if both would have the same value, `entry_point` is not descriptive enough.
- **Distinction from `previous_page_context`:** `previous_page_context` answers "what page were they on?" while `entry_point` answers "what action or mechanism on that page (or externally) brought them here?"
- Naming rule: Use one of these patterns depending on the source:
  - **In-app navigation:** `<source_page>_<action>_<element>` — describes the page, action type, and element that triggered navigation (e.g., `landing_click_get_started_for_free`)
  - **External sources:** `direct_url`, `email_link`, `referral_link`, `deeplink`, `notification`, `ad_campaign`
  - **Self-load / first page:** `direct_url` (user typed the URL or opened a bookmark)
  - **Browser refresh/reload:** `browser_reload` (user-initiated refresh of the current page)
- Common values:
  - `direct_url` — user navigated directly (typed URL, bookmark, new tab)
  - `email_link` — user clicked a link in an email
  - `referral_link` — user clicked a shared/referral link
  - `notification` — user clicked a push/in-app notification
  - `browser_reload` — user refreshed the page in browser
  - `landing_click_get_started_for_free` — user clicked "Get started for free" on the landing page
  - `dashboard_click_sidebar_navigation` — user clicked sidebar nav from the dashboard
- Example: `"entry_point": "landing_click_get_started_for_free"`
- When unknown: `"entry_point": null`

---

### 2. Scope Properties

These properties identify the container or scope the page view happens within.

#### `context_object_type`
- **Conditional** — Include when the page exists within a specific business scope.
- What it is: The type of business container this page belongs to.
- What it tracks: Which project, workspace, campaign, or container scopes the page view.
- Values: Defined per product in product configuration (e.g., `project`, `workspace`, `campaign`, `board`).
- Example: `"context_object_type": "project"`
- When not scoped: `"context_object_type": null`

---

## Guardrails for Page View

A `page_view` event should represent a meaningful page-level state, not just any visible UI change.

### Core guardrails

- **One page, one view event**
  - Fire one `page_view` when a user meaningfully lands on a page/state.
  - Do NOT fire repeated `page_view` events for the same page because of re-renders, inner component refreshes, state hydration, or other system-driven updates. A user-initiated browser refresh/reload of a meaningful page SHOULD trigger a new `page_view`.

- **Do not track component visibility as page views**
  - Cards, tables, modules, drawers, accordions, and tabs inside a page should not create new `page_view` events unless they are truly separate routed page states.

- **Route/state distinction matters**
  - If the URL or app route changes to a distinct product page/state, this usually qualifies as `page_view`.
  - If the route does not change, only fire `page_view` when the product clearly treats the state as a separate screen in the user journey.

- **Use `page_view` for navigation, `user_action` for interaction**
  - Landing on a page = `page_view`
  - Clicking a tab/button/link = `user_action`
  - If a click causes navigation, both may exist:
    - `user_action` for the click
    - `page_view` for the new page reached

- **Page load does not equal page_view unless meaningful**
  - Technical loads, refreshes, or background page restores should not create duplicate `page_view` events.
  - The event should represent a meaningful arrival, not just code execution.

- **Entry point must reflect true navigation source**
  - Do NOT default `entry_point` blindly
  - If the page is reached via browser refresh/reload, it MUST be set to `browser_reload`
  - If unknown, set to `null` instead of guessing

---

## Triggering Rules

A `page_view` SHOULD be triggered when:

- The user lands on a new page after routing/navigation
- The user opens a distinct workflow screen that is treated as a separate step/page
- A deep link opens a specific page
- A login or redirect lands the user on a meaningful destination page
- A major internal navigation shifts the user into a distinct page context

A `page_view` SHOULD NOT be triggered when:

- The same page re-renders
- Filters, sort, or pagination update results inside the same page
- Content loads below the fold
- A modal or drawer opens over the current page without replacing page context
- A tab switch only changes content inside the same page and is not treated as a separate page state
- Background refresh updates the page silently

---

## Criticality Rules

Not every visible state deserves a `page_view`. Use this decision tree:

```
Has the user landed on or been shown a distinct page/screen/state?
├── NO → Do NOT track as page_view
└── YES
    ├── Is this state meaningful for journey or funnel analysis?
    │   ├── NO → Do NOT track as page_view
    │   └── YES
    │       ├── Is this just a component/modal/drawer inside an existing page?
    │       │   ├── YES → Do NOT track as page_view
    │       │   └── NO → TRACK as page_view
```

### Edge Cases

- **Tabs:** Track as `page_view` only if the tab behaves like a separate page/state in the product and is meaningful for navigation analysis. Otherwise, track the tab click as `user_action` only.
- **Modals / Drawers / Panels:** Do not track as `page_view` by default. Track only if they function as a full-screen or route-level state that product teams analyze like a page.
- **Multi-step Wizards:** Each step can be tracked as a `page_view` if each step represents a distinct, meaningful page/screen in the flow. If the wizard is a single-page form with internal step transitions that are not treated as separate screens, do not emit separate `page_view` events.
- **Redirect chains:** Track only the final meaningful destination page. Do not fire page views for intermediate technical redirects unless they are visible and meaningful to the user.
- **Same page with changed query params:** Do not automatically fire a new `page_view`. Fire a new `page_view` only if the query param change creates a new navigational page/state that the product explicitly treats as distinct. If the query param change only updates the state, filters, scope, or results of the same logical page, track it through `page_context_update` instead.

---

## Full Examples

### Example 1: User lands on search results page from dashboard

```javascript
capture(PAGE_VIEWED, {
  current_page_context: 'search/results_page',
  previous_page_context: 'dashboard',
  entry_point: 'dashboard_click_sidebar_navigation',
  context_object_type: null,
});
```

### Example 2: User opens a specific project page from search results

```javascript
capture(PAGE_VIEWED, {
  current_page_context: 'project/details_page',
  previous_page_context: 'search/results_page',
  entry_point: 'search_results_click_project_card',
  context_object_type: 'project',
});
```

### Example 3: User reaches job creation step 1 after clicking "Create Job"

```javascript
capture(PAGE_VIEWED, {
  current_page_context: 'job_creation/job_details',
  previous_page_context: 'jobs/list_page',
  entry_point: 'jobs_list_click_create_job',
  context_object_type: null,
});
```

### Example 4: Hiring Manager home page — returning user after login

```javascript
capture(PAGE_VIEWED, {
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: 'auth/landing',
  entry_point: 'auth_landing_login_redirect',
  context_object_type: null,
});
```

---

## Rules for Agentic AI

When reviewing a frontend page or design spec, the AI MUST follow these rules to identify and generate `page_view` events.

### A. Classification Rules

A view qualifies as `page_view` if ALL of these are true:
1. The user lands on a meaningful page, screen, or routed view
2. The state is distinct for navigation, funnel, or adoption analysis
3. The state is more than a component-level UI change

A view does NOT qualify as `page_view` if ANY of these are true:
1. The visible change is only a component render inside a page
2. The state is caused by background refresh or lazy loading
3. The state is a technical redirect or hydration step with no user-facing page meaning
4. The visible change is a modal/drawer/panel that does not replace or function as a page
5. The state is a same-page context change that should be tracked as `page_context_update`

### B. Property Assignment Rules

For every `page_view` event, the AI MUST determine:

| Property | How to determine | Fallback if unknown |
|----------|------------------|---------------------|
| `current_page_context` | Read from the page/screen name in the design or spec | MUST be provided — use the most specific page name available |
| `previous_page_context` | Infer from the navigation source or prior step | Use `null` if unknown |
| `entry_point` | Identify the specific mechanism (page + action + element) that brought the user here. For external sources use `direct_url`, `email_link`, etc. For browser refresh use `browser_reload` | Use `null` if unknown |
| `context_object_type` | Identify whether the page is scoped to a business object | Use `null` if not scoped |

### C. Completeness Rules

For every feature or flow reviewed, the AI MUST ensure:
1. Every major routed page has a corresponding `page_view`
2. Every meaningful workflow step that acts as a distinct screen has a `page_view`
3. The same page/state is not duplicated because of component loads or re-renders
4. `page_view` coverage aligns with user journey analysis needs, not visual fragmentation

### D. What to Flag for Human Review

The AI MUST flag (not skip, not guess) when:
1. It is unclear whether a tab/state should be treated as a page or just an in-page interaction
2. A modal/drawer appears large or important, but the spec does not clarify whether it is a separate page-state
3. A wizard step may or may not deserve its own `page_view`
4. The page name in the design/spec is ambiguous
5. A view appears meaningful, but the navigation source is unclear

---

## Naming Quick Reference

### `event_type`
`page_view`

### `current_page_context` — Pattern
Use `snake_case`, with `/` for hierarchy:
- `dashboard`
- `search/results_page`
- `project/details_page`
- `workspace/sequence_setup`
- `job_creation/job_details`

### `entry_point` — Use descriptive mechanism
- **In-app:** `<source_page>_<action>_<element>` (e.g., `dashboard_click_sidebar_navigation`)
- **External:** `direct_url` · `email_link` · `referral_link` · `deeplink` · `notification` · `ad_campaign`
- **Refresh:** `browser_reload`

---

## AI Workflow: Generating a Tracking Plan from a Design Spec

When given a page, screen, or feature spec, the AI MUST follow this sequence:

1. **Scan** — Identify all meaningful pages, routed screens, and workflow states in the feature.
2. **Filter** — Apply the Classification Rules (Section A) to determine which states qualify as `page_view`. Discard component-only and technical states.
3. **Assign** — For each qualifying page/state, determine all Required properties using the Property Assignment Rules (Section B).
4. **Validate** — Apply Completeness Rules (Section C). Ensure all meaningful pages and workflow steps are covered.
5. **Flag** — Flag any ambiguities per Section D. Do NOT guess — mark for human review.
6. **Output** — Produce a structured page view list grouped by feature or flow, with all properties filled.
7. **Handoff** — Note where corresponding `user_action`, `system_outcome`, or `error` events should exist.


