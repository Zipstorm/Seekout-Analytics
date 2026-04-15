# Login & Onboarding — Property Dictionary

**Flow:** `login_onboarding`
**Last Updated:** April 2026

---

## Person Properties (`$set_once`)

Set once, never overwritten. Persist permanently on the user profile.

| Property | Type | Set By Event | Source | Description |
|----------|------|-------------|--------|-------------|
| `entry_point` | string | Login Started + Account Created | `?context=` URL param or `'direct'` | First-touch attribution — how user originally found Helix |
| `first_referrer` | string or null | Login Started | `document.referrer` | URL that referred user to Helix |
| `first_landing_url` | string | Login Started | `window.location.href` | Full landing URL including query params |
| `first_persona` | enum | Account Created | Role selected on onboarding page | First persona chosen — never changes even if user switches later |
| `account_created_at` | ISO date | Account Created | `new Date().toISOString()` | When account was created |

### `first_persona` allowed values

| Value | UI Label |
|-------|----------|
| `hiring_manager` | "I'm a hiring manager with an open role" |
| `recruiter` | "I'm a recruiter or TA professional" |
| `job_seeker` | "I'm a job seeker" |

### `entry_point` derivation

| URL | entry_point value |
|-----|------------------|
| `/signup?context=job_link` | `job_link` |
| `/signup?context=team_invite` | `team_invite` |
| `/signup?context=direct_prospect` | `direct_prospect` |
| `/signup?context=direct_hiring` | `direct_hiring` |
| `/signup` (no param) | `direct` |

---

## Person Properties (`$set`)

Updated on every login. Always reflect current state.

| Property | Type | Set By | Source | Description |
|----------|------|--------|--------|-------------|
| `email` | string | `identifyUser()` | `/auth/me` response | User's email |
| `name` | string | `identifyUser()` | `/auth/me` response | User's name |
| `current_persona` | enum | `identifyUser()` + persona switch | Derived from role via `ROLE_TO_PERSONA` mapping | Active persona — `hiring_manager`, `recruiter`, `job_seeker` |
| `org_id` | string | `identifyUser()` | `/auth/me` response | Organization ID |

---

## Event Properties — Per Event

### Page Viewed

| Property | Type | Required? | Description |
|----------|------|-----------|-------------|
| `current_page_context` | string | Required | Page identifier — see values table in events.md |
| `previous_page_context` | string or null | Conditional | Previous page |
| `entry_point` | string or null | Conditional | What action/mechanism brought user to this page |

### Login Started

| Property | Type | Value | Description |
|----------|------|-------|-------------|
| `action` | enum | `click` | Physical interaction |
| `action_value` | string | `continue_with_google_or_email_button` | Exact UI element |
| `current_page_context` | string | `auth/landing` | Page |
| `previous_page_context` | null | `null` | No previous page |
| `entry_point` | string | From `?context=` param | How user arrived |
| `entity_type` | string | `account` | Business object |
| `component` | string | `auth_landing_hero_card_cta` | UI container |
| `context_object_type` | null | `null` | No scoping object |
| `context_object_id` | null | `null` | No scoping object |

### Account Created

| Property | Type | Value | Description |
|----------|------|-------|-------------|
| `action` | enum | `click` | Physical interaction |
| `action_value` | string | `continue_as_hiring_manager_button` / `continue_as_recruiter_button` / `continue_as_job_seeker_button` | Dynamic per persona |
| `current_page_context` | string | `onboarding/role_selection` | Page |
| `previous_page_context` | string | `auth/landing` | Previous page |
| `entry_point` | string | Same value from Login Started | How user arrived |
| `entity_type` | string | `onboarding` | Business object — user is in onboarding flow |
| `component` | string | `onboarding_role_selection_footer_cta` | UI container |
| `context_object_type` | null | `null` | No scoping object |
| `context_object_id` | null | `null` | No scoping object |
| `persona` | enum | `hiring_manager` / `recruiter` / `job_seeker` | Selected persona |
| `signup_context` | string | Same as entry_point | How user arrived (for backend compatibility) |
| `auth_method` | enum | `google` / `email` / `saml` | Auth method (known after auth) |

### Intro Completed

| Property | Type | Value | Description |
|----------|------|-------|-------------|
| `action` | enum | `click` | Physical interaction |
| `action_value` | string | `lets_go_button` | Exact UI element |
| `current_page_context` | string | `onboarding/intro` | Page |
| `previous_page_context` | string | `onboarding/role_selection` | Previous page |
| `entry_point` | null | `null` | Not applicable |
| `entity_type` | string | `onboarding` | Business object |
| `component` | string | `onboarding_intro_footer_cta` | UI container |
| `context_object_type` | null | `null` | No scoping object |
| `context_object_id` | null | `null` | No scoping object |

---

## UserRole to Persona Mapping

The codebase uses `UserRole` enum internally. Map to analytics persona values:

| UserRole (code) | persona (analytics) | action_value suffix |
|----------------|--------------------|--------------------|
| `HIRING_MANAGER` | `hiring_manager` | `continue_as_hiring_manager_button` |
| `RECRUITER` | `recruiter` | `continue_as_recruiter_button` |
| `PROFESSIONAL` | `job_seeker` | `continue_as_job_seeker_button` |

Note: The code uses `PROFESSIONAL` but the UI says "Job Seeker" and analytics uses `job_seeker`.

---

## Auto-Captured Properties (PostHog SDK)

Automatically included on every event. Do NOT set manually.

| Property | Description |
|----------|-------------|
| `$current_url` | Full page URL |
| `$referrer` | HTTP referrer |
| `$browser` | Browser name |
| `$os` | Operating system |
| `$device_type` | desktop / mobile / tablet |
| `$screen_height` / `$screen_width` | Screen dimensions |
| `timestamp` | Event timestamp |
| `$session_id` | Session identifier |
| `distinct_id` | Anonymous or identified user ID |
