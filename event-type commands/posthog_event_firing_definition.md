# PostHog Event Firing Definitions — Login & Onboarding

**Flow:** `login_onboarding`
**Version:** 1.0
**Last Updated:** April 2026

---

## Purpose

This document provides the exact firing condition, justification, and behavioral proof for every event in the Login & Onboarding flow. Each definition answers three questions:

1. **When exactly does this event fire?** — The precise technical trigger.
2. **Why does it fire here and not earlier/later?** — The behavioral evidence from the product.
3. **What happens if the user drops off before/after this point?** — The state implication.

---

## Backend State Model

Understanding when the backend creates and persists user state is critical to placing events correctly.

| Backend Action | When It Happens | Evidence |
|----------------|-----------------|----------|
| `distinct_id` + email generated | Authorization succeeds (auth callback returns) | User's email and PostHog distinct_id exist in the system immediately after Google/SAML/email auth completes |
| Persona NOT yet persisted | User is on `/onboarding/role` but has not clicked "Continue as [Persona]" | If user logs out or closes tab here, next auth with the same email shows `/onboarding/role` again — the system does not consider this a complete account |
| Persona persisted, account created | User clicks "Continue as [Persona]" and server confirms | If user logs out or closes tab at the intro page (`/onboarding/intro`) or later, next auth with the same email goes **directly to the home page** — the system treats this as a returning user with a complete account |

**This means the true account creation boundary is the "Continue as [Persona]" confirmation.** Everything before it is a provisional auth state; everything after it is a real account.

---

## Event Definitions

### 1. Login Started

| Field | Value |
|-------|-------|
| **Event name** | `Login Started` |
| **Event type** | `user_action` |
| **Source** | Frontend |

**When it fires:** The moment the user clicks "Continue with Google or Email" on the landing page (`/signup`), BEFORE the browser redirects to the external IdP (Google picker, SAML provider, etc.). This IS a user_action — the user clicked a button.

**Why here:**
- This is the last moment we have control before the user leaves Helix for external auth.
- If we fire after the auth callback instead, we lose visibility into users who click the CTA but never complete external auth (e.g., close the Google picker, deny permissions, SAML misconfiguration).
- Firing on click captures the full top-of-funnel, including external auth drop-off.

**What if the user drops off after this?**
- `Login Started` exists with no follow-up event → user abandoned at external auth.
- This is the only way to measure the external auth completion rate: `Login Started` → (`Signup Started` or `Login Succeeded`).

**SAML variation:** For SAML/SSO users who are redirected directly from their org IdP (bypassing `/signup`), `Login Started` fires on the auth callback arrival instead, since Helix never rendered the landing page. Set `auth_method` = `saml` and `entry_point` = `saml_redirect`.

---

### 2. Signup Started

| Field | Value |
|-------|-------|
| **Event name** | `Signup Started` |
| **Event type** | `lifecycle` |
| **Source** | Frontend |
| **Existing?** | Yes — already in event catalog |

**When it fires:** On the auth callback, when the backend determines this is a **new email** (no existing account). The user's `distinct_id` and email are now generated in the system, but no persona has been selected and no account record is finalized.

**Why here and not later:**
- At this point the system has confirmed: (a) auth succeeded, (b) this email has never been seen before.
- This is the earliest moment we can distinguish new vs returning users.
- It fires BEFORE the persona selection page renders — it represents "authenticated new user enters onboarding," not "account exists."

**Why here and not earlier (e.g., on CTA click):**
- On CTA click, we don't yet know if auth will succeed or if this is a new vs returning user. That's why `Login Started` fires on click (captures intent) and `Signup Started` fires on callback (captures confirmed new-user state).

**What if the user drops off after this?**
- `Signup Started` exists but no `Account Created` → user authenticated but never completed onboarding.
- The user's `distinct_id` and email exist in PostHog (from the `identify()` call), but the account is not considered created.
- **Critical behavior:** If this user returns and authenticates with the same email, they will see the persona selection page again — the system does NOT treat them as a returning user until persona is confirmed.

---

### 3. Login Succeeded

| Field | Value |
|-------|-------|
| **Event name** | `Login Succeeded` |
| **Event type** | `lifecycle` |
| **Source** | Backend |

**When it fires:** On the auth callback, when the backend determines this email **already has a completed account** (persona was previously selected and persisted).

**Why here:**
- The backend checks: does this email have a persisted persona? If yes → returning user → `Login Succeeded`.
- This is mutually exclusive with `Signup Started`: a given auth callback produces exactly one of these two events, never both.

**What if the user drops off after this?**
- `Login Succeeded` exists but no home page `page_view` → user authenticated but the app failed to load or the user closed the tab immediately. This is rare but measurable.

**Distinction from Account Created:**
- `Login Succeeded` = returning user authenticates. Fires every time they log in.
- `Account Created` = new user completes onboarding. Fires exactly once per user, ever.

---

### 4. Login Failed

| Field | Value |
|-------|-------|
| **Event name** | `Login Failed` |
| **Event type** | `lifecycle` |
| **Source** | Backend |

**When it fires:** On the auth callback, when authentication fails. This covers:
- Google OAuth denied/cancelled (user clicks "Deny" on permissions)
- SAML assertion failure (IdP rejects, certificate mismatch, config error)
- Email/password validation failure
- Network errors during auth callback processing
- Token exchange failures

**Why here:**
- The auth callback is the only place we can detect failure — the external IdP doesn't report back to our frontend.
- If the user simply closes the Google picker without completing auth, no callback fires and no event fires. This drop-off is measured as `Login Started` with no follow-up.

**What if the user retries?**
- Each attempt produces its own `Login Started` → `Login Failed` pair. Retry count can be derived from consecutive `Login Failed` events within the same session.

---

### 5. Onboarding Started

| Field | Value |
|-------|-------|
| **Event name** | `Onboarding Started` |
| **Event type** | Lifecycle |
| **Source** | Frontend |

**When it fires:** When the persona selection page (`/onboarding/role`) renders for a new user. Fires once per onboarding attempt.

**Why here:**
- This is the first Helix-controlled page a new user sees after auth. It marks the start of the onboarding funnel.
- It fires on page render, not on any user interaction, because arriving at this page IS the meaningful state change (the user has passed external auth and is now inside the product).

**Why not on `Signup Started` instead?**
- `Signup Started` fires on the auth callback, which is a backend event. `Onboarding Started` fires when the frontend page actually renders. There can be a gap (redirect latency, loading states) — and in edge cases the page might fail to render even though auth succeeded. Separating them gives visibility into auth-to-render drop-off.

**Re-entry behavior:** If a user authenticates, sees the persona page, logs out WITHOUT selecting a persona, and later re-authenticates with the same email — they see the persona page again. `Onboarding Started` fires again on this second visit. This is intentional: it lets us measure retry behavior and multi-session onboarding completion.

---

### 6. Persona Selected

| Field | Value |
|-------|-------|
| **Event name** | `Persona Selected` |
| **Event type** | Lifecycle |
| **Source** | Frontend |
| **Existing?** | Yes — already in event catalog |

**When it fires:** When the user clicks "Continue as [Persona]" (e.g., "Continue as Hiring Manager") on the persona selection page AND the server confirms the persona has been persisted.

**Why on "Continue as [Persona]" and not on the persona card click:**
- Clicking a persona card (e.g., "I'm a hiring manager with an open role") is a **selection**, not a **commitment**. The user can toggle between cards freely before confirming.
- Only the "Continue as [Persona]" button click represents the user's final, deliberate choice.
- The persona card click is tracked separately as a `user_action` event for deliberation analysis, but it is NOT `Persona Selected`.

**Why this is the Account Created boundary:**
- **Behavioral proof:** If a user selects a persona and clicks "Continue as [Persona]", then logs out or closes the tab at the intro page — the next time they authenticate with the same email, they go **directly to the home page**. The system treats them as a returning user with a complete account.
- **Converse proof:** If a user does NOT click "Continue as [Persona]" (e.g., logs out from the persona page), the next time they authenticate they see the persona selection page again. The system does NOT treat them as having an account.
- Therefore, the "Continue as [Persona]" confirmation is the exact moment the backend transitions from provisional auth state to persisted account.

---

### 7. Account Created

| Field | Value |
|-------|-------|
| **Event name** | `Account Created` |
| **Event type** | `lifecycle` |
| **Source** | Backend |
| **Existing?** | Yes — already in event catalog |

**When it fires:** Immediately after `Persona Selected`, when the backend confirms the persona has been persisted and the account record is finalized. This happens as part of the "Continue as [Persona]" server response.

**Why here — the definitive evidence:**

| Test | Before "Continue as [Persona]" | After "Continue as [Persona]" |
|------|-------------------------------|-------------------------------|
| User logs out and re-authenticates | Sees persona selection page again | Goes directly to home page |
| System treats as returning user? | No | Yes |
| distinct_id + email exist? | Yes (from auth callback) | Yes |
| Persona persisted? | No | Yes |
| Account considered complete? | No | **Yes** |

This behavioral test proves that the backend commits the account at persona confirmation. The `distinct_id` and email existing from auth are necessary but NOT sufficient — the account is only "created" when the persona is persisted.

**Why NOT at the home page (Step 5):**
- If the user confirms persona, sees the intro page, then logs out — they skip onboarding on re-entry and go straight to home. The account already exists.
- The intro page is a post-account, pre-first-use informational screen. Dropping off here does not undo the account.

**Why NOT at auth callback (Step 2):**
- At auth callback, only `distinct_id` and email exist. No persona, no account record.
- A user who authenticates but never selects a persona is NOT a created account — they will be prompted for persona selection again on next auth.

**Firing sequence (all happen within the "Continue as [Persona]" request-response):**
1. User clicks "Continue as [Persona]" → `user_action` fires (frontend)
2. Frontend sends persona to backend → backend persists persona + creates account record
3. Backend confirms → `Persona Selected` fires (frontend, on server confirmation)
4. Backend confirms → `Account Created` fires (backend, same server response)
5. Frontend navigates to intro page

**Relationship to Signup Started:**
- `Signup Started` = "a new email authenticated" (provisional state)
- `Account Created` = "the account is real" (persisted state)
- The funnel `Signup Started` → `Account Created` measures onboarding completion rate
- Users who have `Signup Started` but no `Account Created` = abandoned onboarding at persona selection

---

### 8. Onboarding Completed

| Field | Value |
|-------|-------|
| **Event name** | `Onboarding Completed` |
| **Event type** | Lifecycle |
| **Source** | Frontend |

**When it fires:** When a new user reaches the home page for the first time after completing the full onboarding flow (persona selection → intro page → home page).

**Why here and not at Account Created:**
- `Account Created` fires at persona confirmation (Step 3) — this is the account boundary.
- `Onboarding Completed` fires at home page arrival (Step 5) — this is the experience boundary.
- They are intentionally separate events because they measure different things:
  - `Account Created` = "is this a real account?" (conversion metric)
  - `Onboarding Completed` = "did the user finish the onboarding experience?" (activation metric)

**Why the distinction matters:**
- A user who confirms persona but drops off at the intro page has a created account (`Account Created` fired) but has NOT completed onboarding (`Onboarding Completed` did NOT fire).
- On re-entry, this user goes straight to home (account exists), and `Onboarding Completed` fires then.
- This lets you measure: of all created accounts, how many completed the full onboarding experience before their first real session?

**Re-entry behavior:**
- If a user creates an account (persona confirmed), leaves at intro, and re-enters → they land on home page → `Onboarding Completed` fires at that point.
- `Onboarding Completed` fires exactly once per user, ever. It tracks when the user first reaches the home page, regardless of whether it happened in the same session as account creation.

---

## page_view Firing Definitions

### PV-1: signup/landing

| Field | Value |
|-------|-------|
| **Fires when** | Landing page (`/signup`) renders in the browser |
| **User type** | All (new and returning) |
| **Re-fires on refresh?** | Yes — with `entry_point` = `browser_reload` |

**Justification:** This is a distinct routed page with its own URL. It is the entry point for all non-SAML users. Every session that starts with the signup flow must have this page_view.

**SAML exception:** SAML users who are redirected from their org IdP may never see this page. For them, the first page_view is either `onboarding/role_selection` (new) or the home page (returning).

---

### PV-2: onboarding/role_selection

| Field | Value |
|-------|-------|
| **Fires when** | Persona selection page (`/onboarding/role`) renders |
| **User type** | New users only |
| **Re-fires on re-entry?** | Yes — if user left without selecting persona and re-authenticates, this page renders again and fires again |

**Justification:** Distinct routed page, different URL from landing page, represents a meaningful step in the onboarding funnel. Users who see this page have passed external auth but have not yet created an account.

---

### PV-3: onboarding/intro

| Field | Value |
|-------|-------|
| **Fires when** | Intro page (`/onboarding/intro`) renders |
| **User type** | New users only (account already created at this point) |
| **Re-fires on re-entry?** | No — if user leaves and re-enters, they go to home page, not intro page. This page is shown only once, on the first session after persona confirmation. |

**Justification:** Distinct routed page with persona-specific content. It is the only page between account creation and first home page visit. Tracking it separately lets you measure the intro page drop-off (created account but never reached home in same session).

---

### PV-4: Home Page (persona-specific)

| Field | Value |
|-------|-------|
| **Fires when** | Home page renders (e.g., `/hiring-manager/job-postings`) |
| **User type** | All |
| **current_page_context** | `hiring_manager/job_postings` (HM), TBD (recruiter), TBD (job seeker) |

**Justification:** Distinct routed page, the primary destination of both login and onboarding flows. For new users, this is where `Onboarding Completed` fires. For returning users, this is the first meaningful page after `Login Succeeded`.

---

## user_action Firing Definitions

### UA-1: Persona tab click (landing page)

| Field | Value |
|-------|-------|
| **Fires when** | User clicks "For Hiring Managers", "For Recruiters", or "For Candidates" tab on the landing page |
| **Does NOT fire** | On initial page load (the default active tab is not a user action) |

**Justification:** These tabs change the marketing messaging displayed. Tracking which tab the user views before clicking the CTA helps correlate messaging with signup conversion. The default tab is NOT tracked — only explicit tab switches.

---

### UA-2: Continue with Google or Email click (= Login Started)

| Field | Value |
|-------|-------|
| **Fires when** | User clicks the "Continue with Google or Email" button |
| **Does NOT fire** | If the button is disabled or if the click is prevented by a blocker |
| **Same event as** | `Login Started` — this click IS Login Started, not a separate event |

**Justification:** This is the primary CTA that initiates the entire auth flow. It is the last trackable interaction before the user leaves Helix for external auth. There is no separate lifecycle event — the `user_action` click is the Login Started event.

---

### UA-3: Persona card click

| Field | Value |
|-------|-------|
| **Fires when** | User clicks a persona card ("I'm a hiring manager...", "I'm a recruiter...", "I'm a job seeker...") |
| **Fires again if** | User clicks a different persona card (toggling between options) |
| **Does NOT represent** | A committed persona choice — that is the "Continue as [Persona]" click |

**Justification:** Tracking card clicks shows deliberation behavior — how many users explore multiple personas before committing. A user who clicks all three cards before selecting "Hiring Manager" is a different signal than one who clicks "Hiring Manager" immediately.

---

### UA-4: Continue as [Persona] click

| Field | Value |
|-------|-------|
| **Fires when** | User clicks "Continue as Hiring Manager" / "Continue as Recruiter" / "Continue as Job Seeker" |
| **Does NOT fire if** | The button is still in its disabled "Select a role" state (no persona card selected) |
| **Triggers** | `Persona Selected` (lifecycle) and `Account Created` (lifecycle) on server confirmation |

**Justification:** This is the most critical user action in the entire onboarding flow. It is the moment the user commits to a persona AND the moment the backend creates the account. It simultaneously triggers two lifecycle events and navigates to the intro page.

---

### UA-5: Log out click (onboarding)

| Field | Value |
|-------|-------|
| **Fires when** | User clicks "Log out" link in the top-right corner of the onboarding pages |
| **Significance** | Onboarding abandonment signal |

**Justification:** A user who explicitly logs out during onboarding is actively choosing to leave. This is a stronger abandonment signal than closing the tab (which we can't track). Measuring this helps identify friction in the onboarding flow.

---

### UA-6: Let's go click (intro page)

| Field | Value |
|-------|-------|
| **Fires when** | User clicks "Let's go" button on the intro page |
| **Triggers** | Navigation to the home page, where `Onboarding Completed` fires |

**Justification:** This is the final user action in the onboarding flow. It transitions the user from the informational intro to the active product experience.

---

## Complete Firing Sequence

### New User — Happy Path (no drop-offs)

```
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | page_view (signup/landing)                 | page_view   | Landing page renders
 2  | click: for_recruiters_tab                  | user_action | User switches marketing tab
 3  | Login Started                              | user_action | User clicks "Continue with Google or Email"
 4  | [external auth — no events]                | --          | Google/SAML picker
 5  | Signup Started                             | lifecycle   | Auth callback — new email detected
 6  | page_view (onboarding/role_selection)       | page_view   | Persona selection page renders
 7  | Onboarding Started                         | lifecycle   | Fires on page render
 8  | click: hiring_manager_persona_card         | user_action | User clicks persona card
 9  | click: continue_as_hiring_manager_button   | user_action | User confirms persona
10  | Persona Selected                           | lifecycle   | Server confirms persona persisted
11  | Account Created                            | lifecycle   | Server confirms account finalized (same response as #10)
12  | page_view (onboarding/intro)               | page_view   | Intro page renders
13  | click: lets_go_button                      | user_action | User clicks "Let's go"
14  | page_view (hiring_manager/job_postings)    | page_view   | Home page renders
15  | Onboarding Completed                       | lifecycle   | First home page arrival for this user
```

### New User — Drops off at persona selection, returns later

```
Session 1:
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | page_view (signup/landing)                 | page_view   | Landing page renders
 2  | Login Started                              | user_action | User clicks "Continue with Google or Email"
 3  | [external auth — no events]                | --          | Google picker
 4  | Signup Started                             | lifecycle   | Auth callback — new email detected
 5  | page_view (onboarding/role_selection)       | page_view   | Persona selection page renders
 6  | Onboarding Started                         | lifecycle   | Fires on page render
 7  | click: log_out_link                        | user_action | User logs out — SESSION ENDS
    |                                            |             | ❌ No Account Created

Session 2 (same email, days later):
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | page_view (signup/landing)                 | page_view   | Landing page renders
 2  | Login Started                              | user_action | User clicks "Continue with Google or Email"
 3  | [external auth — no events]                | --          | Google picker (same email)
 4  | Signup Started                             | lifecycle   | Auth callback — no persona → still treated as new
 5  | page_view (onboarding/role_selection)       | page_view   | Persona page renders AGAIN
 6  | Onboarding Started                         | lifecycle   | Fires again (second attempt)
 7  | click: recruiter_persona_card              | user_action | User selects persona
 8  | click: continue_as_recruiter_button        | user_action | User confirms
 9  | Persona Selected                           | lifecycle   | Server confirms
10  | Account Created                            | lifecycle   | ✅ Account now exists
11  | page_view (onboarding/intro)               | page_view   | Intro page renders
12  | click: lets_go_button                      | user_action | User clicks "Let's go"
13  | page_view (recruiter/home)                 | page_view   | Home page renders
14  | Onboarding Completed                       | lifecycle   | First home page arrival
```

### New User — Creates account, drops off at intro, returns later

```
Session 1:
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1–11 | [same as happy path through Account Created] |          |
12  | page_view (onboarding/intro)               | page_view   | Intro page renders
13  | [user closes tab]                          | --          | No event — SESSION ENDS
    |                                            |             | ✅ Account Created already fired
    |                                            |             | ❌ No Onboarding Completed

Session 2 (same email, later):
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | page_view (signup/landing)                 | page_view   | Landing page renders
 2  | Login Started                              | user_action | User clicks "Continue with Google or Email"
 3  | [external auth — no events]                | --          | Google picker
 4  | Login Succeeded                            | lifecycle   | Auth callback — email has persona → RETURNING USER
 5  | page_view (hiring_manager/job_postings)    | page_view   | Home page renders (skips intro)
 6  | Onboarding Completed                       | lifecycle   | First home page arrival (delayed from Session 1)
```

### Returning User — Standard login

```
 #  | Event                                      | Type        | Trigger
----|--------------------------------------------|-------------|------------------------------------------------
 1  | page_view (signup/landing)                 | page_view   | Landing page renders
 2  | Login Started                              | user_action | User clicks "Continue with Google or Email"
 3  | [external auth — no events]                | --          | Google picker
 4  | Login Succeeded                            | lifecycle   | Auth callback — returning user
 5  | page_view (hiring_manager/job_postings)    | page_view   | Home page renders
```

---

## Decision Boundary Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| When does a `distinct_id` exist? | At auth callback success | Email + ID generated immediately on auth |
| When is the user considered "new"? | Auth callback returns and email has no persisted persona | System shows persona selection page |
| When is the account considered "created"? | "Continue as [Persona]" click + server confirmation | User who leaves after this point → returns to home page (not persona selection) |
| When is onboarding "complete"? | User reaches home page for the first time | May happen in the same session as account creation or a later session |
| When is the user considered "returning"? | Auth callback returns and email has a persisted persona | System routes directly to home page, skipping onboarding |
| Can `Account Created` fire without `Onboarding Completed`? | Yes | User confirms persona → closes tab at intro → account exists but onboarding not complete |
| Can `Onboarding Completed` fire without `Account Created`? | No | You must have an account to reach the home page |
| Can `Signup Started` fire multiple times for the same email? | Yes | User authenticates, leaves at persona, returns → `Signup Started` fires again |
| Does `Account Created` fire more than once? | No | `$set_once` semantics — fires exactly once per distinct_id |
