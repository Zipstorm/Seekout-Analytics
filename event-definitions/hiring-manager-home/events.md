# Hiring Manager Home — Event Catalog

**Flow:** `hiring_manager_home`
**Last Updated:** April 2026

---

## Overview

The Hiring Manager home page (`/hiring-manager/job-postings`) is the primary landing surface for users with the Hiring Manager persona. Users arrive here after completing onboarding (new users) or after login (returning users).

This page shows:
- Welcome banner with user's name
- Job postings list with tab filters (All, Draft, Active, Archived)
- Search job postings bar (live filter — results update as user types, no submit action)
- "+ Create Job Posting" CTA (header and empty state)
- Left sidebar with persona label, persona switch toggle, navigation (Job postings, Shared AI Job Flows), recent items, user profile, and notification bell

---

## User Paths to This Page

```
New User (completed full onboarding):
  onboarding/intro → "Let's go" click → hiring_manager/job_postings

New User (created account, skipped intro, re-logged in):
  auth/landing → login → hiring_manager/job_postings (skips intro)

Returning User:
  auth/landing → login → hiring_manager/job_postings
```

---

## Events

### 1. Page View

| # | Event | Type | current_page_context | Trigger | Notes |
|---|-------|------|---------------------|---------|-------|
| 1 | Page Viewed | page_view | `hiring_manager/job_postings` | Home page component mounts | Fires for all authenticated users landing on this page |

#### Page Viewed — Property Matrix

| Property | New user (from intro) | New user (skipped intro, re-logged) | Returning user | Direct URL | Browser refresh |
|---|---|---|---|---|---|
| `current_page_context` | `hiring_manager/job_postings` | `hiring_manager/job_postings` | `hiring_manager/job_postings` | `hiring_manager/job_postings` | `hiring_manager/job_postings` |
| `previous_page_context` | `onboarding/intro` | `auth/landing` | `auth/landing` | `null` | `hiring_manager/job_postings` |
| `entry_point` | `onboarding_intro_click_lets_go_button` | `auth_landing_login_redirect` | `auth_landing_login_redirect` | `direct_url` | `browser_reload` |
| `context_object_type` | `null` | `null` | `null` | `null` | `null` |

#### Person Property Updates on Page Load

| Property | Scope | Action | Value |
|---|---|---|---|
| `current_persona` | person (`$set`) | Update on every page load | `hiring_manager` (from active persona in sidebar) |

---

### 2. User Action Events — Header

#### UA-1: "+ Create Job Posting" button click (header)

The primary CTA in the top-right corner of the page header. Always visible regardless of whether jobs exist.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `create_job_posting_button` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `job` |
| `component` | `job_postings_page_header` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

---

### 3. User Action Events — Tab Filters

#### UA-2: Job status tab click

User clicks one of the tab filters (All, Draft, Active, Archived) to filter the job postings list. The "All" tab is selected by default on page load — do NOT fire for the default state, only for explicit user clicks.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `all_tab` / `draft_tab` / `active_tab` / `archived_tab` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `job` |
| `component` | `job_postings_status_filter_tabs` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

**`action_value` mapping:**

| Tab Label | action_value |
|---|---|
| All | `all_tab` |
| Draft | `draft_tab` |
| Active | `active_tab` |
| Archived | `archived_tab` |

---

### 4. User Action Events — Empty State

#### UA-3: "+ Create Job Posting" button click (empty state)

The CTA shown in the empty state when no jobs exist. Functionally identical to the header CTA but tracked separately via `component` to measure which CTA drives more job creation.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `create_job_posting_button` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `job` |
| `component` | `job_postings_empty_state_cta` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

> **Note:** `action_value` is the same (`create_job_posting_button`) for both header and empty state CTAs. The `component` field distinguishes them: `job_postings_page_header` vs `job_postings_empty_state_cta`.

---

### 5. User Action Events — Sidebar

Sidebar events are scoped per-page (via `current_page_context`) because sidebar content varies by persona. Each persona's home page defines its own sidebar events with the relevant nav links.

#### UA-4: Persona switch toggle click

User clicks the persona switch icon (↔ arrows) next to "Hiring Manager" in the sidebar. Opens the "Choose a role" popover showing available personas to switch to (excludes the currently active persona).

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `persona_switch_toggle` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `persona` |
| `component` | `sidebar_persona_section` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

#### UA-5: Persona card click (switch persona)

User clicks a persona card in the "Choose a role" popover to switch their active persona. This is the actual switch action — it changes the user's surface and navigates to the new persona's home page.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `recruiter_persona_card` / `job_seeker_persona_card` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `persona` |
| `component` | `sidebar_persona_switch_popover` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

**`action_value` mapping:**

| Persona Card | action_value |
|---|---|
| Recruiter | `recruiter_persona_card` |
| Job Seeker | `job_seeker_persona_card` |

> **Note:** The popover only shows personas the user can switch TO (excludes the current persona). Since the user is on Hiring Manager, only Recruiter and Job Seeker are shown. On this click, `current_persona` person property updates via `$set` to the selected persona.

#### UA-6: Sidebar navigation — "Shared AI Job Flows" link

User clicks "Shared AI Job Flows" in the sidebar. Navigates to a different page.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `shared_ai_job_flows_nav_link` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `navigation` |
| `component` | `sidebar_navigation` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

#### UA-7: User profile click

User clicks their profile name/avatar ("Soum") in the bottom-left of the sidebar.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `user_profile_avatar` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `account` |
| `component` | `sidebar_user_section` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

#### UA-8: Notification bell click

User clicks the notification bell icon next to their profile.

| Property | Value |
|---|---|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `notification_bell_icon` |
| `current_page_context` | `hiring_manager/job_postings` |
| `previous_page_context` | _(carried from page load)_ |
| `entry_point` | `null` |
| `entity_type` | `notification` |
| `component` | `sidebar_user_section` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

---

## Elements NOT Tracked

| Element | Why Not Tracked |
|---|---|
| "Search job postings" input | Live filter — results update as user types via backend string match. No discrete submit action. Not a `user_action`. |
| "Job postings" sidebar nav link | On this page, clicking it reloads the same page (no-op). No meaningful state change. The page_view on reload already captures the re-visit. |

---

## Complete Event Inventory

### page_view events

| # | current_page_context | Trigger |
|---|---------------------|---------|
| 1 | `hiring_manager/job_postings` | Home page renders |

### user_action events

| # | action | action_value | component | entity_type |
|---|--------|-------------|-----------|-------------|
| UA-1 | `click` | `create_job_posting_button` | `job_postings_page_header` | `job` |
| UA-2 | `click` | `all_tab` / `draft_tab` / `active_tab` / `archived_tab` | `job_postings_status_filter_tabs` | `job` |
| UA-3 | `click` | `create_job_posting_button` | `job_postings_empty_state_cta` | `job` |
| UA-4 | `click` | `persona_switch_toggle` | `sidebar_persona_section` | `persona` |
| UA-5 | `click` | `recruiter_persona_card` / `job_seeker_persona_card` | `sidebar_persona_switch_popover` | `persona` |
| UA-6 | `click` | `shared_ai_job_flows_nav_link` | `sidebar_navigation` | `navigation` |
| UA-7 | `click` | `user_profile_avatar` | `sidebar_user_section` | `account` |
| UA-8 | `click` | `notification_bell_icon` | `sidebar_user_section` | `notification` |

### Person property updates

| Property | Scope | Trigger |
|---|---|---|
| `current_persona` | person (`$set`) | Every page load |

---

## Total Event Count

| Type | Count |
|---|---|
| page_view | 1 |
| user_action | 8 (UA-1 through UA-8) |
| person property updates | 1 (`current_persona` via `$set`) |
| **Total** | **9 events + 1 property update** |
