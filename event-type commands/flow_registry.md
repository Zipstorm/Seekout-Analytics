# Flow Registry: Login & Onboarding

**Flow ID:** `login_onboarding`
**Version:** 1.0
**Last Updated:** April 2026

---

## Flow Overview

This flow covers the complete login and onboarding experience for Helix, from the landing page through to the persona-specific home page. It distinguishes between **new users** (first-time signup → onboarding) and **returning users** (login → home page directly).

### Auth Methods Covered

| Method | Description |
|--------|-------------|
| `google` | Google OAuth via "Continue with Google or Email" button |
| `email` | Email/password via the same button |
| `saml` | SSO/SAML for enterprise customers (redirects to org IdP) |

### User Paths

```
Landing Page (/signup)
│
├── New User Path:
│   Click "Continue with Google or Email" → Authorization → Signup Started
│   → Persona Selection (/onboarding/role) → "Continue as [Persona]"
│   → Persona Selected + Account Created (fires on persona confirmation)
│   → Intro Page (/onboarding/intro) → Home Page → Onboarding Completed
│
└── Returning User Path:
│   Click "Continue with Google or Email" → Authorization → Login Succeeded
│   → Home Page (persona-specific, skips onboarding)
│
└── SAML/SSO Path:
    Redirect to org IdP → Authorization → Signup Started or Login Succeeded
    → (follows new or returning path above)
```

**Why Account Created fires at persona confirmation, not earlier or later:**

- **Not at auth callback:** At auth, only `distinct_id` + email exist. No persona, no account
  record. If the user logs out before selecting a persona, next auth shows persona selection
  again — the system does not consider this a complete account.
- **Not at home page:** If a user confirms persona but leaves at the intro page, next auth
  routes them directly to home — the account already exists. The intro page is post-account.
- **At persona confirmation:** This is the exact moment the backend persists the persona and
  finalizes the account record. See `posthog_event_firing_definition.md` for full behavioral
  evidence.

---

## Step-by-Step Flow

### Step 1: Landing Page (`/signup`)

**URL:** `helix-dev.seekout.io/signup`

The marketing landing page where all users (new and returning) begin. Displays persona-specific messaging with tabs (For Hiring Managers, For Recruiters, For Candidates) and a single CTA.

#### page_view

| Property | Value |
|----------|-------|
| `event_type` | `page_view` |
| `current_page_context` | `signup/landing` |
| `previous_page_context` | `null` |
| `entry_point` | `direct_url` or `referral_link` or `email_link` (depends on source) |
| `context_object_type` | `null` |

#### user_action events

**1. Persona tab click** — user clicks a marketing tab to view persona-specific messaging

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `for_hiring_managers_tab` / `for_recruiters_tab` / `for_candidates_tab` |
| `current_page_context` | `signup/landing` |
| `previous_page_context` | `null` |
| `entry_point` | `null` |
| `entity_type` | `persona` |
| `component` | `signup_landing_persona_tabs` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

**2. Continue with Google or Email click** — primary CTA that initiates the auth flow

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `continue_with_google_or_email_button` |
| `current_page_context` | `signup/landing` |
| `previous_page_context` | `null` |
| `entry_point` | `null` |
| `entity_type` | `account` |
| `component` | `signup_landing_cta_section` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

#### Handoff notes
- This click triggers **Login Started** (lifecycle event, separate schema)
- The persona tab that was active at the time of CTA click is not captured here — consider adding `active_persona_tab` as a property if marketing wants to correlate messaging → signup conversion

---

### Step 2: Authorization (External)

**URL:** `seekoutdevcustomer.ciamlogin.com/...` (external IdP)

This is the Google/SAML account picker. The user selects or adds an account. This page is **outside Helix's control** — we cannot fire page_view or user_action events here.

#### What fires after authorization completes

The auth callback returns to Helix. The backend determines if this is a new or returning user.

**For new users → fires:**
- `Signup Started` (intent, frontend — already in catalog) — marks that a new user has authenticated but has NOT yet selected a persona. `distinct_id` + email are generated at this point, but the account is NOT yet created.
- `Account Created` fires later — at persona confirmation in Step 3 (see `posthog_event_firing_definition.md` for behavioral evidence)

**For returning users → fires:**
- `Login Succeeded` (new event — see below)

**On auth failure → fires:**
- `Login Failed` (new event — see below)

#### New lifecycle events needed

**Login Started** — fires when auth flow begins (before redirect to IdP)

| Property | Type | Description |
|----------|------|-------------|
| `auth_method` | enum | `google`, `email`, `saml` |
| `signup_page_persona_tab` | enum | `hiring_manager`, `recruiter`, `candidate` — which tab was active when user clicked CTA |

**Login Succeeded** — fires on server-confirmed successful authentication for a **returning user**

| Property | Type | Description |
|----------|------|-------------|
| `auth_method` | enum | `google`, `email`, `saml` |
| `is_new_user` | boolean | `false` for returning users (always false; new users get `Account Created` instead) |
| `days_since_last_login` | number | Days since previous login (for re-engagement analysis) |
| `surface` | enum | `prospect`, `hiring` — last active surface |

**Login Failed** — fires on auth failure

| Property | Type | Description |
|----------|------|-------------|
| `auth_method` | enum | `google`, `email`, `saml` |
| `error_reason` | string | System error description |
| `error_category` | enum | `network`, `permission`, `validation`, `server`, `timeout` |

#### Property addition to existing events

**Account Created** (already in catalog) — add:

| Property | Type | Description |
|----------|------|-------------|
| `auth_method` | enum | `google`, `email`, `saml` — how the user authenticated |

---

### Step 3: Persona Selection (`/onboarding/role`)

**URL:** `helix-dev.seekout.io/onboarding/role`

New users only. The user selects their persona: "I'm a hiring manager with an open role", "I'm a recruiter or TA professional", or "I'm a job seeker". The button at the bottom starts as "Select a role" (disabled) and becomes "Continue as [Persona]" after selection.

#### page_view

| Property | Value |
|----------|-------|
| `event_type` | `page_view` |
| `current_page_context` | `onboarding/role_selection` |
| `previous_page_context` | `signup/landing` |
| `entry_point` | `signup_landing_click_continue_with_google_or_email_button` |
| `context_object_type` | `null` |

#### Lifecycle event: Onboarding Started

Fires once when the persona selection page loads for a new user. Marks the beginning of the onboarding funnel.

| Property | Type | Description |
|----------|------|-------------|
| `auth_method` | enum | `google`, `email`, `saml` |
| `signup_context` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite` |

#### user_action events

**1. Persona card click** — user selects a persona

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `hiring_manager_persona_card` / `recruiter_persona_card` / `job_seeker_persona_card` |
| `current_page_context` | `onboarding/role_selection` |
| `previous_page_context` | `signup/landing` |
| `entry_point` | `null` |
| `entity_type` | `persona` |
| `component` | `onboarding_role_selection_persona_list` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

**2. Continue as [Persona] click** — user confirms persona and proceeds

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `continue_as_hiring_manager_button` / `continue_as_recruiter_button` / `continue_as_job_seeker_button` |
| `current_page_context` | `onboarding/role_selection` |
| `previous_page_context` | `signup/landing` |
| `entry_point` | `null` |
| `entity_type` | `persona` |
| `component` | `onboarding_role_selection_footer` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

**3. Log out click** — user abandons onboarding

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `log_out_link` |
| `current_page_context` | `onboarding/role_selection` |
| `previous_page_context` | `signup/landing` |
| `entry_point` | `null` |
| `entity_type` | `account` |
| `component` | `onboarding_role_selection_header` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

#### Lifecycle events at this step

**Persona Selected** (already in catalog) — fires when server confirms persona persisted.

**Account Created** (already in catalog) — fires immediately after Persona Selected, in the same server response. This is the true account creation moment.

**Behavioral proof:** If a user confirms persona and then leaves at the intro page or later, next auth goes directly to home page — the account exists. If a user leaves BEFORE confirming persona, next auth shows persona selection again — no account.

See `posthog_event_firing_definition.md` → Section 7 (Account Created) for the full decision boundary evidence.

#### Handoff notes
- The persona card click is a toggle-like selection — user can switch between cards before confirming. Only the final "Continue as..." click matters for the funnel, but tracking card clicks shows deliberation behavior.

---

### Step 4: Intro Page (`/onboarding/intro`)

**URL:** `helix-dev.seekout.io/onboarding/intro`

New users only. Persona-specific intro page showing the value prop and steps ahead. Content varies by persona. The hiring manager version shows a 5-step preview: "Understand the job details → Compare sample candidates → Create screening questions → Configure AI screening avatar → Share with your network."

#### page_view

| Property | Value |
|----------|-------|
| `event_type` | `page_view` |
| `current_page_context` | `onboarding/intro` |
| `previous_page_context` | `onboarding/role_selection` |
| `entry_point` | `onboarding_role_selection_click_continue_as_persona_button` |
| `context_object_type` | `null` |

#### user_action events

**1. Let's go click** — user proceeds to the home page / first-use experience

| Property | Value |
|----------|-------|
| `event_type` | `user_action` |
| `action` | `click` |
| `action_value` | `lets_go_button` |
| `current_page_context` | `onboarding/intro` |
| `previous_page_context` | `onboarding/role_selection` |
| `entry_point` | `null` |
| `entity_type` | `account` |
| `component` | `onboarding_intro_cta_section` |
| `context_object_type` | `null` |
| `context_object_id` | `null` |

---

### Step 5: Home Page (Persona-Specific)

**URL (Hiring Manager):** `helix-dev.seekout.io/hiring-manager/job-postings`
**URL (Recruiter):** TBD
**URL (Job Seeker):** TBD

The landing page after onboarding completes (new users) or after login (returning users). Content varies by persona. The sidebar shows the active persona (e.g., "Hiring Manager") and persona-specific navigation.

For full event definitions on the Hiring Manager home page, see [`event-definitions/hiring-manager-home/`](../event-definitions/hiring-manager-home/).

#### page_view

| Property | Value (new user — completed intro) | Value (new user — skipped intro, re-logged) | Value (returning user) |
|----------|-----------------------------------|---------------------------------------------|----------------------|
| `event_type` | `page_view` | `page_view` | `page_view` |
| `current_page_context` | `hiring_manager/job_postings` | `hiring_manager/job_postings` | `hiring_manager/job_postings` |
| `previous_page_context` | `onboarding/intro` | `auth/landing` | `auth/landing` |
| `entry_point` | `onboarding_intro_click_lets_go_button` | `auth_landing_login_redirect` | `auth_landing_login_redirect` |
| `context_object_type` | `null` | `null` | `null` |

**Dynamic `previous_page_context` rules:**

| User Journey | previous_page_context | entry_point | Why |
|---|---|---|---|
| New user completed full onboarding (intro → home) | `onboarding/intro` | `onboarding_intro_click_lets_go_button` | User clicked "Let's go" on intro page |
| New user created account, skipped/cancelled intro or logged out from intro, re-logged in | `auth/landing` | `auth_landing_login_redirect` | Account exists, system routes to home after login |
| Returning user logged in | `auth/landing` | `auth_landing_login_redirect` | Standard login → home redirect |
| Direct URL or bookmark | `null` | `direct_url` | No previous page in session |
| Browser refresh | `hiring_manager/job_postings` | `browser_reload` | Same page reloaded |

#### Person property update: `current_persona`

On every home page load, the user's `current_persona` person property is updated via `$set` to reflect the active persona. This is distinct from `first_persona` (`$set_once`, set at onboarding, never changes).

| Property | Type | Scope | Values | Set By |
|---|---|---|---|---|
| `current_persona` | enum | person (`$set`) | `hiring_manager`, `recruiter`, `job_seeker` | `identifyUser()` on login + persona switch |

See [`event-definitions/hiring-manager-home/properties.md`](../event-definitions/hiring-manager-home/properties.md) for full definition.

> **Note:** `current_page_context` values per persona:
> - Hiring Manager: `hiring_manager/job_postings`
> - Recruiter: TBD (define when recruiter home page is known)
> - Job Seeker: TBD (define when job seeker home page is known)

#### Lifecycle event: Onboarding Completed

Fires once when a new user reaches the home page for the first time after completing onboarding. Does NOT fire for returning users. May fire in a different session than `Account Created` if the user left at the intro page and returned later.

| Property | Type | Description |
|----------|------|-------------|
| `persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` |
| `onboarding_duration_seconds` | number | Time from Onboarding Started to Onboarding Completed |
| `auth_method` | enum | `google`, `email`, `saml` |

> **Note:** `Account Created` fires at Step 3 (persona confirmation), NOT here. A user can have `Account Created` without `Onboarding Completed` if they left at the intro page. See `posthog_event_firing_definition.md` for the full behavioral evidence.

---

## New vs Returning User Summary

| Signal | New User | Returning User |
|--------|----------|----------------|
| Auth result | `Signup Started` (auth confirmed, onboarding begins) | `Login Succeeded` |
| Sees onboarding? | Yes (persona selection → intro) | No (straight to home) |
| `Onboarding Started` fires? | Yes | No |
| `Persona Selected` fires? | Yes | No |
| `Account Created` fires? | Yes — **at persona confirmation** | No |
| `Onboarding Completed` fires? | Yes — at home page arrival | No |
| `is_new_user` on Login Succeeded | N/A (gets Signup Started → Account Created) | `false` |

### Drop-off scenarios for new users

| Dropped off at | Events that fired | Account Created? | Next auth behavior |
|----------------|-------------------|-----------------|-------------------|
| Auth page (closed Google picker) | Login Started | No | Shows landing page |
| Persona selection (logged out or closed tab) | Login Started → Signup Started → Onboarding Started | No | Shows persona selection AGAIN |
| Intro page (closed tab) | Login Started → Signup Started → Onboarding Started → Persona Selected → **Account Created** | **Yes** | Goes to home page (skips onboarding) |
| Completed full flow | Login Started → Signup Started → Onboarding Started → Persona Selected → **Account Created** → Onboarding Completed | **Yes** | Goes to home page |

---

## Complete Event Inventory for This Flow

### page_view events

| # | current_page_context | User Type | Notes |
|---|---------------------|-----------|-------|
| 1 | `signup/landing` | All | Landing page |
| 2 | `onboarding/role_selection` | New only | Persona picker |
| 3 | `onboarding/intro` | New only | Persona-specific intro |
| 4 | `hiring_manager/job_postings` (or per-persona equivalent) | All | Home page |

### user_action events

| # | action | action_value | Page | Notes |
|---|--------|-------------|------|-------|
| 1 | `click` | `for_hiring_managers_tab` / `for_recruiters_tab` / `for_candidates_tab` | `signup/landing` | Marketing tab switch |
| 2 | `click` | `continue_with_google_or_email_button` | `signup/landing` | Primary CTA |
| 3 | `click` | `hiring_manager_persona_card` / `recruiter_persona_card` / `job_seeker_persona_card` | `onboarding/role_selection` | Persona selection |
| 4 | `click` | `continue_as_hiring_manager_button` / `continue_as_recruiter_button` / `continue_as_job_seeker_button` | `onboarding/role_selection` | Confirm persona |
| 5 | `click` | `log_out_link` | `onboarding/role_selection` | Abandon onboarding |
| 6 | `click` | `lets_go_button` | `onboarding/intro` | Proceed to home |

### Lifecycle / system events (new — need lifecycle schema)

| # | Event Name | Type | Trigger | User Type |
|---|-----------|------|---------|-----------|
| 1 | Login Started | user_action | User clicks "Continue with Google or Email" CTA | All |
| 2 | Login Succeeded | lifecycle | Server confirms returning user auth | Returning |
| 3 | Login Failed | lifecycle | Auth error | All |
| 4 | Onboarding Started | lifecycle | Persona selection page loads for new user | New |
| 5 | Onboarding Completed | lifecycle | New user reaches home page | New |

### Existing catalog events that fire in this flow

| Event | Where it fires | User Type |
|-------|---------------|-----------|
| Signup Started | After auth callback — new email detected, before persona selection | New |
| Persona Selected | After "Continue as [Persona]" click — server confirms persona persisted | New |
| Account Created | Immediately after Persona Selected — same server response, account finalized | New |

---

## New Properties Introduced

| Property | Type | Scope | Used In |
|----------|------|-------|---------|
| `auth_method` | enum (`google`, `email`, `saml`) | event | Login Started, Login Succeeded, Login Failed, Account Created, Onboarding Started, Onboarding Completed |
| `is_new_user` | boolean | event | Login Succeeded |
| `days_since_last_login` | number | event | Login Succeeded |
| `signup_page_persona_tab` | enum (`hiring_manager`, `recruiter`, `candidate`) | event | Login Started |
| `onboarding_duration_seconds` | number | event | Onboarding Completed |

---

## Funnel Definitions

### New User Signup Funnel

```
signup/landing (page_view)
  → continue_with_google_or_email_button (user_action)
    → Login Started (lifecycle)
      → [external auth — no Helix events]
        → Signup Started (lifecycle — auth confirmed, new user detected)
          → onboarding/role_selection (page_view)
            → Onboarding Started (lifecycle)
              → hiring_manager_persona_card (user_action — selection, not commitment)
                → continue_as_[persona]_button (user_action — commitment)
                  → Persona Selected (lifecycle — persona persisted)
                    → Account Created (lifecycle — account finalized, same response)
                      → onboarding/intro (page_view)
                        → lets_go_button (user_action)
                          → home page (page_view)
                            → Onboarding Completed (lifecycle)
```

### Returning User Login Funnel

```
signup/landing (page_view)
  → continue_with_google_or_email_button (user_action)
    → Login Started (lifecycle)
      → [external auth — no Helix events]
        → Login Succeeded (lifecycle — returning user detected)
          → home page (page_view)
```

---

## Flags for Human Review

1. **SAML redirect entry:** When users come via SAML/SSO, they may bypass the landing page entirely (org IdP redirects directly). Clarify with engineering whether `signup/landing` page_view fires for SAML users or if they land on a different entry URL.
2. **Recruiter and Job Seeker home pages:** URLs and `current_page_context` values need to be defined once those persona flows are built.
3. **Persona tab on landing page:** Confirm whether these tabs change the URL/route or are purely client-side. If client-side only, they are `user_action` (as defined above). If they change the route, they might also warrant a `page_context_update`.
4. **"Use another account" on Google picker:** This is outside Helix's control. The auth_method will still be captured when the callback returns.
5. **Login Started timing:** Confirm with engineering if Login Started should fire on CTA click (before redirect) or on auth callback initiation. Recommendation: fire on CTA click so we capture users who drop off during the external auth step.
