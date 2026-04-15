# Hiring Manager Home — Firing Rules

**Flow:** `hiring_manager_home`
**Last Updated:** April 2026

---

## Page Viewed (hiring_manager/job_postings)

### Firing Condition

| | |
|---|---|
| **Fires when** | Home page component (`/hiring-manager/job-postings`) mounts in the browser |
| **Fires for** | All authenticated users who land on this page |
| **User state** | Identified (`posthog.identify` already called after auth) |
| **Re-fires on refresh?** | Yes — with `entry_point` = `browser_reload` |
| **Re-fires on return navigation?** | Yes — every time the page mounts |

### Why this page qualifies as a page_view

1. Distinct routed page with its own URL (`/hiring-manager/job-postings`)
2. Primary destination of both login and onboarding flows
3. Meaningful for journey analysis (login → home conversion, onboarding completion)
4. Represents a new navigational state in the user journey

---

## Dynamic `previous_page_context` — Derivation Rules

The home page is reachable through multiple paths. `previous_page_context` MUST reflect the actual previous page in the user's session, not a hardcoded value.

### Path 1: New user completed full onboarding

```
onboarding/intro → "Let's go" click → hiring_manager/job_postings
```

| Property | Value | Why |
|---|---|---|
| `previous_page_context` | `onboarding/intro` | User was on the intro page immediately before |
| `entry_point` | `onboarding_intro_click_lets_go_button` | The "Let's go" button click triggered navigation to home |

**Behavioral evidence:** New user who selected a persona AND clicked "Let's go" on the intro page. The intro page component navigates to `/hiring-manager/job-postings` on CTA click.

### Path 2: New user created account, skipped/cancelled intro, re-logged in

```
Session 1: auth → role selection → Account Created → intro page → [user logs out or closes tab]
Session 2: auth/landing → login → hiring_manager/job_postings (skips intro)
```

| Property | Value | Why |
|---|---|---|
| `previous_page_context` | `auth/landing` | User was on the login page in this session before being redirected |
| `entry_point` | `auth_landing_login_redirect` | System detected existing account and redirected to home |

**Behavioral evidence:** The user's account was created in Session 1 (persona persisted at role selection). In Session 2, the auth callback detects a persisted persona → system treats user as returning → routes directly to home, skipping onboarding entirely.

### Path 3: Returning user — standard login

```
auth/landing → login → hiring_manager/job_postings
```

| Property | Value | Why |
|---|---|---|
| `previous_page_context` | `auth/landing` | User was on the login page before auth redirect |
| `entry_point` | `auth_landing_login_redirect` | Standard login redirect to persona-specific home |

**Behavioral evidence:** Auth callback detects existing account with persisted persona → routes to home page.

### Path 4: Direct URL or bookmark

```
[no previous page] → hiring_manager/job_postings
```

| Property | Value | Why |
|---|---|---|
| `previous_page_context` | `null` | No previous page exists in this session |
| `entry_point` | `direct_url` | User typed URL, used bookmark, or opened from external link |

**Note:** If the user is not authenticated, they will be redirected to auth first. In that case, `previous_page_context` becomes `auth/landing` and `entry_point` becomes `auth_landing_login_redirect` (follows Path 3).

### Path 5: Browser refresh

```
hiring_manager/job_postings → [refresh] → hiring_manager/job_postings
```

| Property | Value | Why |
|---|---|---|
| `previous_page_context` | `hiring_manager/job_postings` | Same page was the previous state |
| `entry_point` | `browser_reload` | User-initiated page refresh |

---

## Implementation: How to derive `previous_page_context`

`previous_page_context` should be derived from session-level navigation state, NOT from user type heuristics.

**Recommended approach — React Router state:**

```javascript
// Source page sets previous_page_context before navigating
navigate('/hiring-manager/job-postings', {
  state: { previousPageContext: 'onboarding/intro' }
});

// Home page reads it on mount
const location = useLocation();
const previousPageContext = location.state?.previousPageContext || null;
```

**For login redirects (no router state available):**

```javascript
// After auth callback, before redirecting to home
sessionStorage.setItem('helix_previous_page_context', 'auth/landing');
sessionStorage.setItem('helix_entry_point', 'auth_landing_login_redirect');

// Home page reads on mount
const previousPageContext = sessionStorage.getItem('helix_previous_page_context') || null;
const entryPoint = sessionStorage.getItem('helix_entry_point') || 'direct_url';

// Clear after reading
sessionStorage.removeItem('helix_previous_page_context');
sessionStorage.removeItem('helix_entry_point');
```

**For browser refresh detection:**

```javascript
// Check performance API for reload
const isReload = performance.getEntriesByType('navigation')[0]?.type === 'reload';
if (isReload) {
  previousPageContext = currentPageContext; // same page
  entryPoint = 'browser_reload';
}
```

---

## `current_persona` — Update Rule

| | |
|---|---|
| **Updates when** | Every home page load (via `identifyUser()`) and on persona switch (UA-5) |
| **Scope** | Person property (`$set`) |
| **Value** | The active persona shown in the sidebar (e.g., `hiring_manager`) |

This update happens as part of user identification, not as a separate event. It ensures PostHog always knows the user's current persona for segmentation.

**Required update to `identifyUser()` in `lib/posthog.ts`:**

```javascript
// Current implementation sets: email, name, role, org_id
// Add current_persona to $set properties:
export function identifyUser(user: User): void {
  const persona = ROLE_TO_PERSONA[user.role] || 'unknown';
  identify(
    user.id,
    {
      email: user.email,
      name: user.name,
      org_id: user.orgId,
      current_persona: persona,  // NEW — replaces role and acting_as
    },
    {
      account_created_at: user.createdAt,
    },
  );
}
```

---

## Drop-off Scenarios

| Scenario | Events Fired | What It Means |
|---|---|---|
| User lands on home, does nothing, leaves | Page Viewed (home) | User saw the home page but took no action — possible confusion or low intent |
| User lands on home after onboarding, no Onboarding Completed | Page Viewed (home) — but Onboarding Completed should also fire | Bug — investigate if Onboarding Completed logic is correct |
| Auth succeeds but home page never loads | Login Succeeded (or Account Created) with no home Page Viewed | App load failure or immediate tab close — measure auth → home conversion |

---

## Canonical Event Definitions

All events follow the exact `capture()` pattern used in the Helix frontend (`@/lib/posthog`). Identity properties (`user_id`, `org_id`), device properties (`platform`, `device_type`, `browser`), and timing properties (`timestamp`, `session_id`) are auto-captured by the PostHog SDK — do NOT set manually.

---

### PV-1: Page Viewed — New user from onboarding intro

```javascript
// In HiringManagerJobPostings.tsx — useEffect on mount
// Fires after new user clicks "Let's go" on onboarding intro page
capture(PAGE_VIEWED, {
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: 'onboarding/intro',
  entry_point: 'onboarding_intro_click_lets_go_button',
});
```

### PV-1b: Page Viewed — Returning user (or new user who skipped intro and re-logged)

```javascript
// In HiringManagerJobPostings.tsx — useEffect on mount
// Fires after login redirect for returning user or re-logged new user
capture(PAGE_VIEWED, {
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: 'auth/landing',
  entry_point: 'auth_landing_login_redirect',
});
```

### PV-1c: Page Viewed — Direct URL / bookmark

```javascript
// In HiringManagerJobPostings.tsx — useEffect on mount
// Fires when user navigates directly (already authenticated)
capture(PAGE_VIEWED, {
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: null,
  entry_point: 'direct_url',
});
```

### PV-1d: Page Viewed — Browser refresh

```javascript
// In HiringManagerJobPostings.tsx — useEffect on mount
// Fires on user-initiated page refresh
capture(PAGE_VIEWED, {
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: 'hiring_manager/job_postings',
  entry_point: 'browser_reload',
});
```

---

### UA-1: "+ Create Job Posting" button click (header)

```javascript
// In HiringManagerJobPostings.tsx — header CTA onClick
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

**Fires when:** User clicks "+ Create Job Posting" button in the top-right header.
**Does NOT fire if:** Button is disabled or blocked.

---

### UA-2: Job status tab click

```javascript
// In HiringManagerJobPostings.tsx — tab filter onClick
// action_value changes per tab: 'all_tab', 'draft_tab', 'active_tab', 'archived_tab'
capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'draft_tab',  // dynamic per tab clicked
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'job_postings_status_filter_tabs',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks any tab filter (All, Draft, Active, Archived).
**Does NOT fire:** On page load for the default "All" tab — only on explicit user clicks.

**`action_value` mapping:**

| Tab Label | action_value |
|---|---|
| All | `all_tab` |
| Draft | `draft_tab` |
| Active | `active_tab` |
| Archived | `archived_tab` |

---

### UA-3: "+ Create Job Posting" button click (empty state)

```javascript
// In HiringManagerJobPostings.tsx — empty state CTA onClick
capture(CREATE_JOB_BUTTON_CLICKED, {
  action: 'click',
  action_value: 'create_job_posting_button',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'job',
  component: 'job_postings_empty_state_cta',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks "+ Create Job Posting" in the empty state ("No jobs yet. Create your first job posting to get started.").
**Only visible when:** No job postings exist.
**Same `action_value` as UA-1** — differentiated by `component`.

---

### UA-4: Persona switch toggle click

```javascript
// In Sidebar.tsx — persona switch icon onClick
capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'persona_switch_toggle',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'persona',
  component: 'sidebar_persona_section',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks the ↔ persona switch icon next to "Hiring Manager" in the sidebar.
**What happens next:** "Choose a role" popover opens showing Recruiter and Job Seeker cards.

---

### UA-5: Persona card click — switch persona

```javascript
// In Sidebar.tsx — persona card onClick in "Choose a role" popover
// action_value changes per card: 'recruiter_persona_card', 'job_seeker_persona_card'
const newPersona = ROLE_TO_PERSONA[selectedRole];

capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'recruiter_persona_card',  // dynamic per card clicked
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'persona',
  component: 'sidebar_persona_switch_popover',
  context_object_type: null,
  context_object_id: null,
});

// Update current_persona person property
posthog.people.set({ current_persona: newPersona });
```

**Fires when:** User clicks a persona card in the "Choose a role" popover.
**Person property update:** `$set: { current_persona: "recruiter" }` (or `"job_seeker"`)
**What happens next:** User is navigated to the selected persona's home page.

**`action_value` mapping:**

| Persona Card | action_value |
|---|---|
| Recruiter | `recruiter_persona_card` |
| Job Seeker | `job_seeker_persona_card` |

---

### UA-6: Sidebar navigation — "Shared AI Job Flows" link

```javascript
// In Sidebar.tsx — "Shared AI Job Flows" nav link onClick
capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'shared_ai_job_flows_nav_link',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'navigation',
  component: 'sidebar_navigation',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks "Shared AI Job Flows" in the sidebar.
**What happens next:** Navigates to the Shared AI Job Flows page.

---

### UA-7: User profile click

```javascript
// In Sidebar.tsx — user profile avatar/name onClick
capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'user_profile_avatar',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'account',
  component: 'sidebar_user_section',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks their profile name/avatar ("Soum") in the bottom-left of the sidebar.

---

### UA-8: Notification bell click

```javascript
// In Sidebar.tsx — notification bell icon onClick
capture(PAGE_VIEWED, {
  action: 'click',
  action_value: 'notification_bell_icon',
  current_page_context: 'hiring_manager/job_postings',
  previous_page_context: previousPageContext,
  entry_point: null,
  entity_type: 'notification',
  component: 'sidebar_user_section',
  context_object_type: null,
  context_object_id: null,
});
```

**Fires when:** User clicks the notification bell icon next to their profile.

---

## Complete Firing Sequence — Returning User Session Example

```
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | Page Viewed (hiring_manager/job_postings)   | page_view   | Home page renders after login redirect
    | → $set: { current_persona: 'hiring_manager' } via identifyUser()
 2  | click: draft_tab                           | user_action | User clicks Draft tab to filter
 3  | click: all_tab                             | user_action | User clicks All tab to reset
 4  | click: create_job_posting_button            | user_action | User clicks "+ Create Job Posting" (header)
    | → navigates to job creation wizard
```

## Complete Firing Sequence — New User First Session (from onboarding)

```
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | Page Viewed (hiring_manager/job_postings)   | page_view   | Home page renders after "Let's go" click
    | → $set: { current_persona: 'hiring_manager' } via identifyUser()
 2  | click: create_job_posting_button            | user_action | User clicks "+ Create Job Posting" (empty state)
    | → navigates to job creation wizard
```

## Complete Firing Sequence — User Switches Persona

```
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | Page Viewed (hiring_manager/job_postings)   | page_view   | Home page renders
    | → $set: { current_persona: 'hiring_manager' } via identifyUser()
 2  | click: persona_switch_toggle               | user_action | User clicks ↔ icon — popover opens
 3  | click: recruiter_persona_card              | user_action | User clicks Recruiter card
    | → $set: { current_persona: 'recruiter' } via posthog.people.set()
    | → navigates to recruiter home page
```
