# Login & Onboarding — Firing Rules

**Flow:** `login_onboarding`
**Last Updated:** April 2026

---

## Backend State Model

| Backend Action | When It Happens | Evidence |
|----------------|-----------------|----------|
| `distinct_id` + email generated | Auth succeeds (MSAL callback) | PostHog distinct_id and email exist after auth |
| Role NOT persisted | User is on `/onboarding/role` but hasn't clicked CTA | If user logs out, next auth shows role selection again |
| Role persisted, account created | User clicks "Continue as [Persona]" and server confirms | If user logs out at intro or later, next auth goes to home page |

**Account creation boundary = "Continue as [Persona]" + server confirmation.**

---

## Firing Rules — Chronological

### 1. Page Viewed (auth/landing)

| | |
|---|---|
| **Fires when** | Auth landing page (`/signup`) renders |
| **Fires for** | All users (new and returning) |
| **User state** | Anonymous (no auth yet) |
| **Re-fires on refresh?** | Yes |

### 2. Login Started ✅ (implemented)

| | |
|---|---|
| **Fires when** | User clicks "Continue with Google or Email" |
| **User state** | Anonymous |
| **Drop-off meaning** | Login Started with no follow-up = user abandoned at MSAL popup |

### 3. Page Viewed (onboarding/role_selection)

| | |
|---|---|
| **Fires when** | Role selection page (`/onboarding/role`) renders |
| **Fires for** | New users only |
| **User state** | Identified (posthog.identify already called after auth) |
| **Re-fires?** | Yes — if user logs out without selecting role and re-authenticates |

### 4. Account Created

| | |
|---|---|
| **Fires when** | User clicks "Continue as [Persona]" AND the `updateRole()` API call returns successfully |
| **Fires for** | New users only |
| **SDK** | Frontend JS — after server response confirms role persisted |
| **Fires once per user** | Yes |

**Why frontend, not backend:**
- The frontend knows the API succeeded (got 200)
- The frontend has PostHog JS initialized with identified user
- The frontend can set `$set_once` person properties
- If API fails, frontend shows error and doesn't fire the event

**Why at role CTA click, not earlier or later:**
- If user logs out BEFORE clicking CTA → next auth shows role page again (no account)
- If user logs out AFTER clicking CTA → next auth goes to home (account exists)
- The intro page is informational — skipping it doesn't affect account state

**What happens to the backend Account Created:**
- Currently fires in `auth/router.py:148-156` using a 5-second heuristic
- **REMOVE this.** It fires at auth callback before the user has selected a role — wrong timing
- The frontend Account Created event replaces it entirely

### 5. Page Viewed (onboarding/intro)

| | |
|---|---|
| **Fires when** | Intro page (`/onboarding/intro`) renders |
| **Fires for** | New users only (after account is already created) |
| **Re-fires?** | No — if user leaves and re-enters, they go to home, not intro |

### 6. Intro Completed

| | |
|---|---|
| **Fires when** | User clicks "Let's go" button on intro page |
| **Fires for** | New users who engage with the intro page |
| **Drop-off meaning** | Page Viewed (intro) without Intro Completed = user saw intro but didn't actively click through (may have closed tab or navigated directly) |

### 7. Page Viewed (home)

| | |
|---|---|
| **Fires when** | Home page renders (e.g., `/hiring-manager/job-postings`) |
| **Fires for** | All users |
| **For new users** | Marks first time in the product |
| **For returning users** | Regular login landing (will be implemented with old user flow) |

---

## Drop-off Scenarios

| Dropped off at | Events fired | Account? | Next auth |
|----------------|-------------|----------|-----------|
| MSAL popup (cancelled) | Page Viewed, Login Started, Login Cancelled | No | Auth landing |
| Role selection (logged out) | Page Viewed ×2, Login Started | No | Role selection again |
| Intro page (closed tab) | Page Viewed ×3, Login Started, Account Created | **Yes** | Home page |
| Completed full flow | All 8 events | **Yes** | Home page |

---

## Complete Firing Sequence — New User Happy Path

```
 #  | Event              | Type        | Trigger
----|---------------------|-------------|------------------------------------------
 1  | Page Viewed         | page_view   | /signup renders
 2  | Login Started       | user_action | "Continue with Google or Email" click
 3  | [MSAL popup]        | --          | External auth — no events
 4  | Page Viewed         | page_view   | /onboarding/role renders
 5  | Account Created     | user_action | "Continue as Hiring Manager" + server OK
 6  | Page Viewed         | page_view   | /onboarding/intro renders
 7  | Intro Completed     | user_action | "Let's go" click
 8  | Page Viewed         | page_view   | /hiring-manager/job-postings renders
```
