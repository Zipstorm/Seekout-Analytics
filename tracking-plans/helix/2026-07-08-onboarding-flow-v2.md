# Tracking Plan: Onboarding Flow v2

**Product:** Helix (SeekOut.ai)
**Feature:** Onboarding identity stitching fixes, auth boundary cleanup, and naming fixes
**Date:** 2026-07-08
**Related PRD:** —
**Repo:** Zipstorm/helix
**Branch:** —
**PR:** —
**Status:** Draft

## Status History

| Status | Date | Trigger |
|---|---|---|
| Draft | 2026-07-08 | Plan created from onboarding dashboard build bugs (2026-07-07) and v1 deferred backlog |

## Workflow

- [ ] Draft created
- [ ] Validated
- [ ] Codebase implemented
- [ ] Absorbed from codebase
- [ ] Re-validated
- [ ] PR raised
- [ ] PR approved
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/helix/event-schema.md`, and `docs/helix/event-catalog.md`.
> Predecessor: `tracking-plans/helix/archived/2026-07-05-onboarding-flow-v1.md`
> Backlog: `backlog/helix/onboarding-flow-deferred.md`

---

## Scope

This plan fixes bugs found on 2026-07-07 while building the PostHog onboarding dashboard. The signup funnel shows **0% conversion** because `distinct_id` and `helix_session_id` change across the auth boundary, making PostHog treat pre-auth and post-auth events as two different users.

1. **Fixes identity stitching** — adds `posthog.reset()` on auth page mount and logout + `posthog.alias()` on first signup to properly stitch pre-auth anonymous events to the authenticated user
2. **Removes stale `auth_landing` Page Viewed** — old deployed code still fires a Page Viewed with `current_page_context: auth_landing` before the correct `auth_signup` event
3. **Fixes Login Started Button Clicked on production** — OAuth redirect kills the page before PostHog flushes the event; adds `continue_button` action_value for signin email path
4. **Documents `helix_session_id` boundary** — pre-auth and post-auth events have different session IDs by design; funnels spanning auth must not filter by session ID
5. **Adds 1 new event** — `Profile Photo Add Errored` (server-side upload failure — completes the Interaction/Result pattern)
6. **Renames 1 event** — `Profile Photo Upload Failed` → `Profile Photo Add Rejected` (backlog #10: object family alignment + terminal fix)
7. **Adds `wizard_mode` to Property Dictionary** — gap from v1 merge (backlog #8)
8. **Adds Auth Session Restore Errored 401 suppression note** — shipped in v1 but not documented in catalog

### Background

The v1 onboarding tracking plan was merged on 2026-07-07. Events are flowing into PostHog, but two critical identity issues prevent funnel analysis:

- **`distinct_id` contamination:** PostHog JS SDK stores the last identified user's `distinct_id` in localStorage. When a new user visits the signup page, pre-auth events (Page Viewed, Login Started Button Clicked) fire with the PREVIOUS user's `distinct_id` — not an anonymous ID, but another real user's ID. `posthog.reset()` is never called on logout or on auth page mount, so the stale ID persists. `posthog.alias()` exists in the codebase (`posthog.ts:144`) but is never called during signup/login — only in the candidate interview flow.
- **`helix_session_id` split:** `sessionManager.onAuthenticated()` mints a new session ID during `loginWithClerk()`. Pre-auth events carry the old (or no) `helix_session_id`, post-auth events carry the new one. This is expected behavior that needs documentation.
- **Login Started Button Clicked lost on production:** OAuth buttons (Google, Microsoft) trigger an immediate browser redirect. PostHog SDK's batch queue hasn't flushed the event before the page unloads, so the event never reaches PostHog. Additionally, events that DO fire are attributed to the wrong person (stale `distinct_id`), making them invisible when searching under the correct user.

### Why the PostHog SDK stores `distinct_id` (this is by design)

All analytics SDKs (PostHog, Mixpanel, Amplitude) store the `distinct_id` in localStorage. This is not an engineering choice — it's built into the SDK for three reasons:

1. **Anonymous tracking:** When a new visitor arrives (no account), the SDK generates a random UUID and stores it. This tracks anonymous behavior across page refreshes without needing an account.
2. **Session continuity:** When a logged-in user refreshes the page, the SDK needs to know "this is still user-xyz" before the app calls `identify()` again.
3. **Cross-visit attribution:** User visits Monday (anonymous), leaves, returns Wednesday and signs up. The stored anonymous ID lets PostHog link Monday's visit to Wednesday's signup via alias.

The problem is not that the ID is stored — it's that the auth lifecycle doesn't call `posthog.reset()` at the right transition points (logout, auth page mount), so a previous real user's ID bleeds into a new user's pre-auth events.

### Part A — v1 Deviations (already merged)

The following v1 deviations were absorbed into the v1 tracking plan and merged to the catalog. They are listed here for completeness — no action needed in v2:

| # | Deviation | Status |
|---|---|---|
| A1 | Onboarding Complete Succeeded source: frontend, not backend | Merged in v1 |
| A2 | Phone collection events removed entirely | Merged in v1 |
| A3 | `steps_completed` dropped from Onboarding Complete Succeeded | Merged in v1 |
| A4 | Handle Claim events removed from onboarding section | Merged in v1 |
| A5 | 5 event renames (Intro Completed, Login Started, Profile Photo Added, Candidate Profile Created/Creation Failed) | Merged in v1 |
| A6 | `persona` → `current_persona` on Account Create Succeeded | Merged in v1 |
| A7 | `first_surface` $set_once person property removed | Merged in v1 |
| A8 | `current_persona` registered as super-property | Merged in v1 |
| A9 | `wizard_mode: 'onboarding'` enum value | Merged in v1 code, but **`wizard_mode` missing from Property Dictionary** — fixed in this plan |
| A10 | Auth Session Restore Errored suppressed on 401 | Merged in v1 code, but **not documented in catalog** — fixed in this plan |

---

## New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Profile Photo Add Errored | Prospect | Error | Frontend | Server-side photo upload fails (network error, storage failure, server 500) after client validation passes | Completes the Profile Photo Add Interaction/Result pattern — Succeeded and Rejected exist but Error was missing | `upload_method`, `file_size_bytes`, `error_reason`, `error_category`, `current_page_context`, `previous_page_context`, `entity_type`, `mode` | -- | -- | Local |

---

## Property Details

No new properties. `Profile Photo Add Errored` reuses existing properties from the photo upload flow.

---

## Event Specifications

### Profile Photo Add Errored

| Field | Value |
|---|---|
| **Event** | Profile Photo Add Errored |
| **Area** | Prospect |
| **Type** | Error |
| **Trigger** | Photo upload passes client-side validation (size/format ok) but server fails to store it — network error, storage failure (S3), server 500, timeout |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | How the photo was provided |
| `file_size_bytes` | number | positive integer | Size of the file that was attempted |
| `error_reason` | string | error message | What went wrong |
| `error_category` | enum | `network`, `server`, `timeout`, `unknown` | Error classification |
| `current_page_context` | string | page context | Page where upload was attempted |
| `previous_page_context` | string | via `rotatePageContext()` | Previous page |
| `entity_type` | string | `candidate_profile` | Business object |
| `mode` | enum | `onboarding`, `editor` | Context in which the photo was uploaded |

---

## Event Renames

### Rejected Events — Must End "Rejected"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Profile Photo Upload Failed | Profile Photo Add Rejected | Rejected | **Object family fix:** Aligns with `Profile Photo Add Succeeded` (`Add` object, not `Upload`). **Terminal fix:** `Failed` → `Rejected` (photo rejected by client-side size/format validation — user-caused, not system error). Backlog item #10. |

---

## Removed Events

| Event | Reason | Replaced By |
|---|---|---|
| Profile Photo Upload Failed | Renamed (object family + terminal alignment) | Profile Photo Add Rejected |

---

## Existing Event Updates

### B1 — `posthog.reset()` on Auth Page Mount + Remove Stale `auth_landing`

**Bug:** When a user visits `/signup` or `/signin`, pre-auth events (Page Viewed, Login Started Button Clicked) fire with a **previous real user's** `distinct_id` — not an anonymous ID. PostHog's JS SDK stores the last identified user in localStorage. Without calling `posthog.reset()`, that stale ID persists across logouts and new browser sessions.

Additionally, old deployed code fires a Page Viewed with `current_page_context: auth_landing` on component mount before the correct `auth_signup` Page Viewed fires.

**Evidence from PostHog (Metadata tab):**

| Event | distinct_id | timestamp |
|---|---|---|
| Page Viewed (`auth_signup`) | `8c77c708-dc22-49bb-9fd1-fbdb6fd76b6b` (previous user) | 2026-07-07T06:20:17Z |
| Auth Login Succeeded | `49f6c76d-9213-4919-a599-87c75fff5c63` (actual new user) | 2026-07-07T06:20:20Z |

Both events show `sarkar.sombrat@gmail.com` and `connect.seekout.ai/signup`. The Page Viewed has the WRONG person's `distinct_id`. PostHog treats these as two different users. Signup funnel shows 0% conversion.

**Fix — two code changes:**

1. **Call `posthog.reset()` on auth page mount** (`SignUp.tsx` and `SignIn.tsx`): This clears the previous user's stored `distinct_id` and generates a fresh anonymous ID. All pre-auth events (Page Viewed, Login Started Button Clicked) will fire with this clean anonymous ID instead of a previous real user's ID.

2. **Remove the stale `auth_landing` Page Viewed**: The old code fires a Page Viewed with `current_page_context: auth_landing` on first mount. This value was already removed from the catalog in v1 (renamed to `auth_signup`). The code fix eliminates the stale capture call.

**After fix — event timeline for a new signup:**

```
T0  Browser loads /signup
T1  posthog.reset()         → clears previous user's ID, generates fresh "anon-xyz"
T2  Page Viewed             → distinct_id = "anon-xyz", current_page_context = "auth_signup"
T3  Login Started Clicked   → distinct_id = "anon-xyz"
T4  OAuth redirect + callback
T5  posthog.identify("user-B")
T6  posthog.alias("user-B") → merges "anon-xyz" INTO "user-B" (see B4)
T7  Auth Login Succeeded    → distinct_id = "user-B"

PostHog: all events (T2–T7) belong to one person "user-B". Funnel works.
```

**Catalog impact:**
- No catalog changes. `auth_landing` was already removed from the catalog in v1. This is a code-only fix.

### B2 — Login Started Button Clicked Production Visibility + `continue_button`

**Bug:** `Login Started Button Clicked` is not visible on production PostHog when searching under the authenticated user. Two contributing causes:

1. **Stale `distinct_id`:** The event fires with the previous user's `distinct_id` (B1 issue). When you search PostHog under the correct person, the event doesn't appear — it's attributed to the wrong person. The `posthog.reset()` fix (B1) resolves this.

2. **OAuth redirect may kill the event:** When a user clicks "Sign up with Google" or "Sign up with Microsoft", the browser immediately redirects to the OAuth provider. PostHog SDK's batch queue may not flush before the page unloads. The event is captured in memory but never sent. This affects Google and Microsoft OAuth buttons on both signup and signin pages. Email submit buttons ("Create account", "Continue") do not redirect — they call the Clerk API inline, so the page stays alive and the event flushes normally.

**Fix:**
- B1 (`posthog.reset()`) fixes the attribution issue.
- For the OAuth redirect flush: ensure `posthog.capture()` is called with immediate flush before the OAuth redirect, or use `navigator.sendBeacon()` to survive the page unload.

**`action_value` gap:** The signin page's email submit button says **"Continue"** (not "Create account"). The v1 `action_value` list doesn't include this value. Adding `continue_button` to the allowed values.

**Updated `action_value` list for Login Started Button Clicked:**

| Button text | Page | `action_value` | `auth_method` |
|---|---|---|---|
| Sign up with Google | Signup | `sign_up_with_google_button` | `google` |
| Sign up with Microsoft | Signup | `sign_up_with_microsoft_button` | `microsoft` |
| Create account | Signup | `create_account_button` | `email` |
| Sign in with Google | Signin | `sign_in_with_google_button` | `google` |
| Sign in with Microsoft | Signin | `sign_in_with_microsoft_button` | `microsoft` |
| Continue | Signin | `continue_button` | `email` |

**Signup vs Signin — one event, property filter:** `Login Started Button Clicked` fires on both pages. `current_page_context` separates them:
- `auth_signup` = new user (signing up)
- `auth_signin` = returning user (signing in)

In PostHog funnels, filter by `current_page_context = auth_signup` for the signup funnel, or use it as a breakdown to compare signup vs signin conversion.

**Catalog impact:**
- Add `continue_button` to `action_value` values for Login Started Button Clicked.

### B3 — `helix_session_id` Auth Boundary Documentation

**Behavior:** `sessionManager.onAuthenticated()` in `session.ts:187-204` mints a new `helix_session_id` during `loginWithClerk()`. Pre-auth events have no session ID (cleared by `posthog.reset()` on page mount) or a stale one. Post-auth events have the new one. They will never match.

**After the B1 fix (`posthog.reset()`):**

```
T1  posthog.reset()             → helix_session_id super-property is CLEARED
T2  Page Viewed                 → no helix_session_id
T3  Login Started Button Clicked → no helix_session_id
T4  OAuth flow...
T5  loginWithClerk():
      sessionManager.onAuthenticated() → mints helix_session_id = "hs_2bf8..."
      posthog.register({ helix_session_id: 'hs_2bf8...' })
T6  Auth Login Succeeded        → helix_session_id = "hs_2bf8..."
T7  All subsequent events       → helix_session_id = "hs_2bf8..."
```

**This is expected and acceptable.** `helix_session_id` is a post-auth concept — it starts at login and tracks the authenticated session. Funnels spanning the auth boundary should rely on `posthog.alias()` for person identity, not `helix_session_id` for session grouping. PostHog's own auto-generated session_id handles cross-auth session tracking.

**Catalog/schema impact:**
- Add documentation note to `docs/helix/event-schema.md`: "`helix_session_id` is only guaranteed present on events fired AFTER `Auth Login Succeeded`. Pre-auth events (e.g., `Page Viewed` on signup/signin) have no `helix_session_id`. Funnels spanning the auth boundary should NOT filter by `helix_session_id` — use PostHog's built-in session tracking or person-level analysis via `posthog.alias()` stitching."

### B4 — Identity Stitching: `posthog.reset()` + `posthog.alias()` + `posthog.reset()` on Logout

**Bug:** The PostHog identity lifecycle is incomplete. Three SDK calls are needed but only `posthog.identify()` is implemented:

| SDK Call | Purpose | Current State |
|---|---|---|
| `posthog.reset()` | Clears stored `distinct_id`, generates fresh anonymous ID | **Never called** — not on logout, not on auth page mount |
| `posthog.identify(userId)` | Sets the `distinct_id` to the authenticated user | ✅ Called in `loginWithClerk()` |
| `posthog.alias(userId)` | Merges the current anonymous `distinct_id` into `userId` | **Never called on signup/login** — only in interview flow (`CandidateEntry.tsx:291,356`) |

Without `reset()`: pre-auth events carry a previous real user's ID → `alias()` would merge two real users → data corruption.
Without `alias()`: pre-auth events (Page Viewed, Login Started Button Clicked) stay attributed to the anonymous ID → PostHog sees them as a different person → funnel breaks.

**Fix — three call sites:**

#### 1. `posthog.reset()` on auth page mount

**Where:** `SignUp.tsx` and `SignIn.tsx`, on component mount (before any `capture()` call).

**What it does:** Clears the previous user's `distinct_id` from localStorage. Generates a fresh anonymous UUID. All subsequent pre-auth events fire with this clean anonymous ID.

**Why this is safe:** The auth pages are only reached when:
- A new visitor arrives (no previous user → reset is a no-op on the anonymous ID)
- A user logged out (reset clears the stale ID)
- A user navigated directly to /signup or /signin (reset clears any identified state)

**Edge case — Auth Login Rejected:** If login fails (wrong OAuth, Clerk error), the user stays on the auth page. `posthog.reset()` already ran on mount — it does NOT run again. The user retries with the same anonymous distinct_id. When they eventually succeed, `alias()` works correctly.

#### 2. `posthog.alias(newUserId)` on first signup only

**Where:** `loginWithClerk()` in `authStore.ts`, immediately after `posthog.identify(newUserId)`.

**What it does:** Tells PostHog "the current anonymous `distinct_id` and `newUserId` are the same person — merge them." PostHog retroactively moves all anonymous events into the real user's timeline.

**Critical: only call on first signup, not on returning signin.**

| Scenario | `identify()` | `alias()` | Why |
|---|---|---|---|
| New user signs up | ✅ Yes | ✅ Yes | Merges anonymous pre-auth events into new user |
| Returning user signs in | ✅ Yes | ❌ No | PostHog already has their person record; `identify()` alone links the anonymous session back |

**How to distinguish:** After `loginWithClerk()` completes, check whether `Account Create Succeeded` fires (new user) or only `Auth Login Succeeded` fires (returning user). Alternatively, check a flag like `isNewAccount` from the Clerk response or the role-selection step.

**Edge case — user visits signup, leaves, comes back days later:**
- Visit 1: `posthog.reset()` → anon-1 → Page Viewed → user leaves
- Visit 2: `posthog.reset()` → anon-2 → Page Viewed → signs up → `alias(real-user)` merges anon-2
- Result: Visit 1 events stay orphaned as anon-1 (different browser session, cookie may have expired). Visit 2 events are correctly stitched. This is acceptable — cross-session anonymous linking requires persistent cookies, which `reset()` clears.

#### 3. `posthog.reset()` on logout

**Where:** The logout handler that fires `Auth Logout Succeeded`, immediately after the capture call.

**What it does:** Clears the authenticated user's `distinct_id` from localStorage. The next visitor on this browser gets a fresh anonymous ID instead of the previous user's.

**Why this was missing:** `Auth Logout Succeeded` was implemented in v1 with the event capture but without the PostHog SDK lifecycle call. This is why the Page Viewed on `/signup` was carrying a previous user's `distinct_id`.

**Edge case — user closes browser without logging out:** `posthog.reset()` on auth page mount (fix #1) handles this case. When the next user visits `/signup`, reset clears the stale ID regardless of whether the previous user logged out.

### Auth Session Restore Errored — 401 Suppression Note (A10)

**Context:** Already shipped in v1 code but not documented in the catalog.

**What happens on every page load:**
1. App loads → auth system checks for refresh token cookie
2. Calls token refresh endpoint
3. If valid token → `Auth Session Restore Succeeded` → user is logged in
4. If no token or expired → endpoint returns HTTP 401
5. Before v1: every 401 fired `Auth Session Restore Errored` → PostHog flooded with "errors" from unauthenticated visitors
6. After v1: 401 is suppressed. Only real failures (500, network error, timeout) fire the event

**Why this matters:** Without the suppression, the Platform Health Dashboard error rates are dominated by false positives (every new visitor = "error"). The suppression makes error metrics meaningful.

**Catalog impact:** Add a note to the Auth Session Restore Errored catalog row: "Does not fire on 401 (expected state for unauthenticated visitors — no refresh token). Only fires on real restore failures (500, network error, timeout)."

### Existing Event Fixes Summary

| Event | Change | Detail |
|---|---|---|
| Page Viewed | Remove stale `auth_landing` (B1) | Old deployed code fires Page Viewed with `current_page_context: auth_landing` — already removed from catalog in v1; code fix removes the stale capture call |
| Login Started Button Clicked | Add `continue_button` (B2) | Signin page email button says "Continue" — this `action_value` was missing from v1 |
| Login Started Button Clicked | Fix OAuth redirect flush (B2) | Ensure event is sent before OAuth redirect kills the page |
| Auth Logout Succeeded | Add `posthog.reset()` after capture (B4) | Clears stored `distinct_id` on logout so next visitor gets clean anonymous ID |
| Auth Session Restore Errored | Add 401 suppression note (A10) | Document that event is suppressed on 401 (unauthenticated visitor, expected state) |
| Profile Photo Upload Failed | Renamed (backlog #10) | → `Profile Photo Add Rejected` — object family + terminal alignment |

### Property Fixes on Existing Events

#### Properties to Add

| Event | Property | Type | Values | Reason |
|---|---|---|---|---|
| Login Started Button Clicked | `action_value` | string | `continue_button` (new) | Signin page email submit button says "Continue" — value was missing from v1 |

---

## Property Dictionary Additions

`wizard_mode` was introduced in the v1 tracking plan and implemented in code, but was not added to the catalog Property Dictionary during the v1 merge. It was treated as an extension to existing events (adding a new `onboarding` value) without realizing the property itself was never in the dictionary — the gap accumulated across the HM Job Creation Wizard v2/v3 plans and the v1 onboarding plan. Adding it now.

| Property | Type | Scope | Allowed Values | Description | Used In |
|---|---|---|---|---|---|
| `wizard_mode` | enum | event | `onboarding`, `create` | Context in which the job post wizard was initiated. `onboarding` = wizard launched during HM onboarding flow (`helix_onboarding_active` set in sessionStorage). `create` = wizard launched from job postings dashboard via "+ Create job" button. | Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Description Evaluated, Job Description Evaluation Failed, Job Post Wizard Intake Mode Selected, Sam Session Started, Sam Session Ended, Sam Session Setup Failed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published, and all Role Requirement / Screening Question CRUD events |

---

## New Standard Objects

No new Standard Objects. `Profile Photo Add` already exists (from `Profile Photo Add Succeeded`). The rename and new error event complete the existing object family.

---

## Catalog Updates

Changes for `docs/helix/event-catalog.md` and `docs/helix/event-schema.md`:

- [ ] `Profile Photo Add Errored` → added to catalog (Prospect Events section)
- [ ] `Profile Photo Upload Failed` → renamed to `Profile Photo Add Rejected` in catalog
- [ ] `Profile Photo Upload Failed` → added to Removed Events table
- [ ] Login Started Button Clicked → add `continue_button` to `action_value` in catalog and Property Dictionary
- [ ] Auth Session Restore Errored → add 401 suppression note to Trigger column
- [ ] Auth Logout Succeeded → add note about `posthog.reset()` call
- [ ] `wizard_mode` → added to Property Dictionary (Enum Properties section)
- [ ] Identity stitching lifecycle → documented in event-schema.md (new section: PostHog Identity Lifecycle)
- [ ] `helix_session_id` boundary note → documented in event-schema.md

---

## Interaction / Started / Result Pattern

Updated pattern for profile photo flow after rename and error event addition:

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Profile photo upload | Add Profile Photo Button Clicked | Profile Photo Add Succeeded | Profile Photo Add Rejected | Profile Photo Add Errored |

---

## Metrics → Events Mapping

| # | Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|---|
| 1 | Signup → First Action conversion (full funnel) | Page Viewed → Login Started Button Clicked → Auth Login Succeeded → Account Create Succeeded → Onboarding Complete Succeeded | Funnel | Breakdown by `current_persona`, `auth_method`. **Previously broken** (0% conversion) due to `distinct_id` contamination — `posthog.reset()` + `posthog.alias()` fix enables this funnel. | Growth |
| 2 | Auth method attempt vs completion | Login Started Button Clicked → Auth Login Succeeded | Funnel | Breakdown by `auth_method`. **Previously invisible** — events attributed to wrong person (stale `distinct_id`). | Growth |
| 3 | Signup vs signin conversion comparison | Login Started Button Clicked → Auth Login Succeeded | Funnel | Breakdown by `current_page_context` (`auth_signup` vs `auth_signin`) | Growth |

---

## Funnels

### 1. Fixed Signup Conversion Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` |
| 2 | Login Started Button Clicked | `current_page_context` = `auth_signup` |
| 3 | Auth Login Succeeded | — |
| 4 | Account Create Succeeded | — |
| 5 | Onboarding Complete Succeeded | — |

**Purpose:** End-to-end signup conversion. Previously broken (0% conversion) due to `distinct_id` contamination. Fixed by `posthog.reset()` (B1) + `posthog.alias()` (B4).

**Note:** Do NOT filter by `helix_session_id` across the auth boundary — session ID is only present on post-auth events.

### 2. Auth Method Comparison Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Login Started Button Clicked | `current_page_context` = `auth_signup` |
| 2 | Auth Login Succeeded | — |

**Purpose:** Compare auth method conversion. Breakdown by `auth_method` (google / microsoft / email).

---

## Implementation Notes

### PostHog Identity Lifecycle — Complete Fix Chain

The identity stitching fix requires three SDK calls at specific points in the auth lifecycle. All three are currently missing (except `identify`).

```
AUTH PAGE MOUNT (SignUp.tsx / SignIn.tsx):
┌────────────────────────────────────────────────────┐
│ posthog.reset()                                     │
│   → Clears previous user's distinct_id              │
│   → Generates fresh anonymous ID "anon-xyz"         │
│   → Clears all super-properties (helix_session_id)  │
│                                                     │
│ posthog.capture('Page Viewed', { ... })              │
│   → distinct_id = "anon-xyz" (clean)                │
│                                                     │
│ User clicks auth button                             │
│ posthog.capture('Login Started Button Clicked')     │
│   → distinct_id = "anon-xyz" (same clean ID)        │
│   → Must flush before OAuth redirect!               │
└────────────────────────────────────────────────────┘

loginWithClerk() SUCCESS:
┌────────────────────────────────────────────────────┐
│ posthog.identify("user-B")                          │
│   → Sets distinct_id to real user                   │
│                                                     │
│ if (isNewUser) {                                    │
│   posthog.alias("user-B")                           │
│   → Merges "anon-xyz" INTO "user-B"                 │
│   → PostHog retroactively attributes all anon-xyz   │
│     events to user-B                                │
│ }                                                   │
│                                                     │
│ sessionManager.onAuthenticated()                    │
│   → Mints new helix_session_id                      │
│   → posthog.register({ helix_session_id: ... })     │
│                                                     │
│ posthog.capture('Auth Login Succeeded')              │
│   → distinct_id = "user-B"                          │
│   → helix_session_id = "hs_2bf8..."                 │
└────────────────────────────────────────────────────┘

LOGOUT:
┌────────────────────────────────────────────────────┐
│ posthog.capture('Auth Logout Succeeded')            │
│                                                     │
│ posthog.reset()                                     │
│   → Clears "user-B" from localStorage               │
│   → Next visitor gets clean anonymous ID             │
└────────────────────────────────────────────────────┘
```

### Edge Cases

| # | Scenario | Behavior | Safe? |
|---|---|---|---|
| 1 | Previous user logged out, new user visits signup | `reset()` on mount clears stale ID → fresh anon → `alias()` merges anon into new user | ✅ |
| 2 | Previous user closed browser without logout | `reset()` on mount clears stale ID (same as #1) | ✅ |
| 3 | Login fails (Auth Login Rejected), user retries | `reset()` already ran on mount, not re-run. Same anon ID for retry. `alias()` runs on eventual success. | ✅ |
| 4 | Returning user goes to /signin | `reset()` on mount clears their identified state → fresh anon. `identify()` after login links back to existing person. `alias()` is NOT called (returning user). | ✅ |
| 5 | User visits signup, leaves, comes back days later | Visit 1: anon-1 events stay orphaned. Visit 2: `reset()` → anon-2 → `alias()` merges anon-2 into real user. Anon-1 is lost. | ✅ (acceptable) |
| 6 | Same user signs up on two different browsers | Each browser has its own PostHog localStorage. `identify()` on both browsers links to same user. Only the browser where signup happened gets alias. | ✅ |
| 7 | `posthog.alias()` called for returning user by mistake | PostHog would try to merge the anon ID into an existing person. Since `reset()` was called, the anon ID is clean — this creates a harmless extra merge of one anonymous session. Not ideal but not data corruption. | ⚠️ Avoid |

### How to Distinguish New User vs Returning User for `alias()`

The `alias()` call must only fire on first signup. Options:

1. **Check Clerk response:** If the Clerk `signUp` flow was used (vs `signIn`), it's a new user.
2. **Check route:** If the user came from `/signup` (not `/signin`), they're signing up. Store this in sessionStorage before the OAuth redirect.
3. **Check Account Create Succeeded:** If this event fires after login, the user is new. But this is a backend event that fires asynchronously — may be too late for the `alias()` call.

**Recommended:** Use the route/flow approach. Store `isNewSignup = true` in sessionStorage when the user clicks a signup button, and check it after `loginWithClerk()` returns.

### OAuth Redirect Flush for Login Started Button Clicked

When a user clicks "Sign up with Google" or "Sign up with Microsoft", the browser redirects immediately to the OAuth provider. The `posthog.capture()` call is made but the SDK's batch queue may not flush before the page unloads.

**Fix options:**

1. **Capture with callback, then redirect:**
   ```
   posthog.capture('Login Started Button Clicked', props, {
     onCapture: () => { window.location.href = oauthUrl }
   })
   ```
   This ensures the event is sent before the redirect.

2. **Use `navigator.sendBeacon()`:** Survives page unloads. PostHog SDK may support this natively via configuration.

3. **Add a small delay:** `setTimeout(() => redirect, 100)` — less reliable but simplest.

### Profile Photo Event Rename

Rename the constant in both:
- `posthogEvents.ts` (frontend): `PROFILE_PHOTO_UPLOAD_FAILED` → `PROFILE_PHOTO_ADD_REJECTED`
- `posthog_events.py` (backend, if parity needed): mirror the rename

Add `PROFILE_PHOTO_ADD_ERRORED` constant for the new error event.

Old event data persists under `Profile Photo Upload Failed` in PostHog; new events fire as `Profile Photo Add Rejected` / `Profile Photo Add Errored` from deploy date.

### Files That Will Change in the v2 Helix Branch

| File | Change |
|------|--------|
| `frontend/src/pages/SignUp.tsx` | Add `posthog.reset()` on mount; remove stale `auth_landing` Page Viewed |
| `frontend/src/pages/SignIn.tsx` | Add `posthog.reset()` on mount |
| `frontend/src/stores/authStore.ts` | Add `posthog.alias(newUserId)` after `posthog.identify()` in `loginWithClerk()` (new users only) |
| `frontend/src/stores/authStore.ts` | Add `posthog.reset()` in logout handler after `Auth Logout Succeeded` capture |
| `frontend/src/components/auth/SignUpForm.tsx` | Fix OAuth redirect flush — ensure Login Started Button Clicked is sent before redirect |
| `frontend/src/components/auth/SignInForm.tsx` | Fix OAuth redirect flush; add `continue_button` action_value for email submit |
| `frontend/src/lib/posthogEvents.ts` | Rename `PROFILE_PHOTO_UPLOAD_FAILED` → `PROFILE_PHOTO_ADD_REJECTED`; add `PROFILE_PHOTO_ADD_ERRORED` |
| `backend/app/shared/posthog_events.py` | Mirror renames (if parity needed) |
| `frontend/src/components/profile/HeadshotUpload.tsx` | Add `Profile Photo Add Errored` capture on server-side upload failure |

---

## Backlog Items Addressed

| # | Item | Resolution in v2 |
|---|---|---|
| B1 | Pre-auth events carry stale `distinct_id` from previous user | `posthog.reset()` on auth page mount clears stale ID; remove stale `auth_landing` Page Viewed |
| B2 | Login Started Button Clicked not visible on production | Attribution fixed by B1; OAuth redirect flush ensures event reaches PostHog; `continue_button` action_value added |
| B3 | `helix_session_id` inconsistency across auth boundary | Documented as expected behavior — `helix_session_id` is post-auth only; funnels must not filter by it across auth |
| B4 | `distinct_id` mismatch breaks signup funnel (0% conversion) | `posthog.alias()` on first signup merges anonymous pre-auth events into authenticated user; `posthog.reset()` on logout prevents stale ID contamination |
| Backlog #10 | Profile Photo Upload Failed — split object family + stale terminal | Renamed to `Profile Photo Add Rejected`; added `Profile Photo Add Errored` for server failures |
| Backlog #8 | `wizard_mode` not in Property Dictionary | Added to Property Dictionary with full definition and Used In references |
| A10 | Auth Session Restore Errored 401 suppression undocumented | Added catalog note documenting the suppression behavior |

## Backlog Items NOT Addressed (Remain Deferred)

| # | Item | Reason |
|---|---|---|
| #1 | Job Post Wizard Dismissed during onboarding | Enhancement, not a fix. Pickup after v2 funnel has baseline data. |
| #2 | Persona-specific intro content tracking | A/B testing not planned yet |
| #3 | Email signup path walkthrough | Low priority (OAuth dominant path) |
| #4 | Interview → Signup → Onboarding path | Separate user journey, deserves own tracking plan |
| #5 | Onboarding time-per-step breakdown | Enhancement after baseline funnel data available |
| #6 | "Finish Setup" widget tracking | Post-onboarding scope, separate plan |
| #7 | Returning user / sign-in path | Separate plan; auth lifecycle events cover basics |
| #11 | Recruiter wizard-completion terminal | Needs walkthrough and screenshots first |
