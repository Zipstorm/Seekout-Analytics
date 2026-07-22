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

- [x] Draft created
- [x] Validated
- [x] Codebase implemented
- [x] Absorbed from codebase (8 deviations applied from helix/.plans/2026-07/2026-07-08-onboarding-flow-v2/tracking-plan-deviations.md)
- [x] Re-validated (13/13 TP rules passed — 2026-07-22)
- [x] PR raised ([#43](https://github.com/Zipstorm/Seekout-Analytics/pull/43))
- [x] PR approved (self-reviewed — solo contributor, GitHub blocks self-approval)
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/helix/event-schema.md`, and `docs/helix/event-catalog.md`.
> Predecessor: `tracking-plans/helix/archived/2026-07-05-onboarding-flow-v1.md`
> Backlog: `backlog/helix/onboarding-flow-deferred.md`

---

## Scope

This plan fixes bugs found on 2026-07-07 while building the PostHog onboarding dashboard. The signup funnel shows **0% conversion** because `distinct_id` and `helix_session_id` change across the auth boundary, making PostHog treat pre-auth and post-auth events as two different users.

1. **Fixes identity stitching** — adds `posthog.reset()` on auth page mount (guarded by `!isLoading && !isAuthenticated && !hasPendingOAuthStrategy()`) + unconditional `posthog.alias()` before `posthog.identify()` to properly stitch pre-auth anonymous events to the authenticated user. Logout `posthog.reset()` was already present — no change needed there.
2. **Removes stale `auth_landing` Page Viewed** — old deployed code still fires a Page Viewed with `current_page_context: auth_landing` before the correct `auth_signup` event
3. **Fixes Login Started Button Clicked on production** — OAuth redirect flush via `{ send_instantly: true }` was already implemented before v2 (verified, no code change needed); adds `continue_button` action_value for signin email path (replaces v1's `sign_in_with_email_button`)
4. **Documents `helix_session_id` boundary** — pre-auth and post-auth events have different session IDs by design; funnels spanning auth must not filter by session ID
5. **Adds 2 new events** — `Profile Photo Add Errored` (server-side upload failure — completes the Interaction/Result pattern) and `Auth Page Switch Link Clicked` (tracks signup↔signin navigation intent)
6. **Renames 1 event** — `Profile Photo Upload Failed` → `Profile Photo Add Rejected` (backlog #10: object family alignment + terminal fix)
7. **Adds signin funnel** — basic returning-user funnel now possible with identity fixes
8. **Adds `wizard_mode` to Property Dictionary** — gap from v1 merge (backlog #8), now with all three values (`onboarding`, `create`, `edit`)
9. **Adds Auth Session Restore Errored 401 suppression note** — shipped in v1 but not documented in catalog
10. **Updates `dashboards.md`** — adds identity stitching requirement notes to onboarding funnels
11. **Adds `is_new_user` to Auth Login Succeeded** — boolean event property (`user.role === null`), distinguishes first-time signups from returning logins for funnel filtering

### Background

The v1 onboarding tracking plan was merged on 2026-07-07. Events are flowing into PostHog, but two critical identity issues prevent funnel analysis:

- **`distinct_id` contamination:** PostHog JS SDK stores the last identified user's `distinct_id` in localStorage. When a new user visits the signup page, pre-auth events (Page Viewed, Login Started Button Clicked) fire with the PREVIOUS user's `distinct_id` — not an anonymous ID, but another real user's ID. `posthog.reset()` on logout already existed in the codebase but was not called on auth page mount, so the stale ID persists when a user closes the browser without logging out. `posthog.alias()` exists in the codebase (`posthog.ts:144`) but is never called during signup/login — only in the candidate interview flow.
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
| Auth Page Switch Link Clicked | Account | Interaction | Frontend | User clicks "Sign in" link on signup page or "Sign up" link on signin page | Tracks users switching between auth pages — reveals confusion (e.g., existing users landing on signup) or intent changes. Currently only the destination Page Viewed captures the switch. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |

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
| **Trigger** | Photo upload passes client-side validation (size/format ok) but server fails to store it — server 500, storage failure, API error. `error_reason` is truncated to 256 characters. |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `upload_method` | enum | `take_photo`, `upload` | How the photo was provided |
| `file_size_bytes` | number | positive integer | Size of the file that was attempted |
| `error_reason` | string | error message | What went wrong |
| `error_category` | enum | `server` | Error classification. The upload stack uses XHR+axios which throws `ApiError`/`AxiosError`, so all server-path failures normalize to `server`. Values `network`, `timeout`, `unknown` are reserved for future enrichment if the upload stack is refactored. |
| `current_page_context` | string | page context | Page where upload was attempted |
| `previous_page_context` | string | via `rotatePageContext()` | Previous page |
| `entity_type` | string | `candidate_profile` | Business object |
| `mode` | enum | `onboarding`, `editor` | Context in which the photo was uploaded |

### Auth Page Switch Link Clicked

| Field | Value |
|---|---|
| **Event** | Auth Page Switch Link Clicked |
| **Area** | Account |
| **Type** | Interaction |
| **Trigger** | User clicks "Sign in" link on signup page (`/signup`) or "Sign up" link on signin page (`/signin`) |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User action type |
| `action_value` | string | `sign_in_link`, `sign_up_link` | Exact link text in snake_case. `sign_in_link` = "Sign in" on signup page. `sign_up_link` = "Sign up" on signin page. |
| `current_page_context` | string | `auth_signup`, `auth_signin` | Page where the link was clicked (source page, not destination) |
| `previous_page_context` | string | via `rotatePageContext()` | Previous page |
| `entity_type` | string | `account` | Business object |
| `component` | string | `auth_signup_card_footer`, `auth_signin_card_footer` | UI location of the link (bottom of the auth card) |

**Analytics value:** Reveals users who land on the wrong auth page:
- High "Sign in" clicks on signup = existing users arriving via signup links (consider redirect or detection)
- High "Sign up" clicks on signin = new users confused about whether they have an account

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
| Profile Photo Upload Failed | Renamed (object family + terminal alignment). Shipped with `error_category` values: `unsupported_format`, `size_limit`. Also carries `previous_page_context` and `entity_type: candidate_profile` for consistency with Errored. | Profile Photo Add Rejected |
| Auth Email Verify Code Send Succeeded | Never implemented — defined in v1 catalog speculatively but no codebase instrumentation exists. Email signup path deferred (backlog #3, OAuth is dominant path). | — |
| Auth Email Verify Code Send Errored | Never implemented — same as above. | — |
| Auth Email Verify Resend Clicked | Never implemented — same as above. | — |
| Auth Email Verify Rejected | Never implemented — same as above. | — |

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

1. **Call `posthog.reset()` on auth page mount** (`SignUp.tsx` and `SignIn.tsx`): Guarded by three conditions — `!isLoading && !isAuthenticated && !hasPendingOAuthStrategy()`. Only fires when auth restore is complete, the visitor is genuinely unauthenticated, and the page is not returning from an OAuth redirect.
   - `!isLoading` — waits for `tryRestoreSession()` to finish before deciding whether to reset. Without this, `reset()` could fire during the initial auth check, then the restore succeeds and the user is authenticated — but `reset()` already wiped their PostHog identity.
   - `!isAuthenticated` — prevents `reset()` from wiping an already-logged-in user's PostHog identity when they hit an auth page via bookmark or back button.
   - `!hasPendingOAuthStrategy()` — suppresses analytics only during OAuth callback returns (`oauth_google` / `oauth_microsoft`). Email OTP (`email_code`) and ticket strategies do NOT suppress — those flows don't redirect away from the page.
   - A `useRef` guard (`authPageAnalyticsCapturedRef`) ensures the effect fires at most once per component mount.

2. **Remove the stale `auth_landing` Page Viewed**: The old code fires a Page Viewed with `current_page_context: auth_landing` on first mount. This value was already removed from the catalog in v1 (renamed to `auth_signup`). The code fix eliminates the stale capture call.

**After fix — event timeline for a new signup:**

```
T0  Browser loads /signup
T1  Auth restore completes (!isLoading), visitor is !isAuthenticated, no pending OAuth
T2  posthog.reset()         → clears previous user's ID, generates fresh "anon-xyz"
T3  Page Viewed             → distinct_id = "anon-xyz", current_page_context = "auth_signup"
T4  Login Started Clicked   → distinct_id = "anon-xyz" (with { send_instantly: true } for OAuth)
T5  OAuth redirect + callback
T6  posthog.alias("user-B") → merges "anon-xyz" INTO "user-B" (BEFORE identify)
T7  posthog.identify("user-B") → sets distinct_id to real user (AFTER alias)
T8  Auth Login Succeeded    → distinct_id = "user-B", is_new_user = true/false

PostHog: all events (T3–T8) belong to one person "user-B". Funnel works.
```

**Catalog impact:**
- No catalog changes. `auth_landing` was already removed from the catalog in v1. This is a code-only fix.

### B2 — Login Started Button Clicked Production Visibility + `continue_button`

**Bug:** `Login Started Button Clicked` is not visible on production PostHog when searching under the authenticated user. Two contributing causes:

1. **Stale `distinct_id`:** The event fires with the previous user's `distinct_id` (B1 issue). When you search PostHog under the correct person, the event doesn't appear — it's attributed to the wrong person. The `posthog.reset()` fix (B1) resolves this.

2. **OAuth redirect may kill the event:** When a user clicks "Sign up with Google" or "Sign up with Microsoft", the browser immediately redirects to the OAuth provider. PostHog SDK's batch queue may not flush before the page unloads. The event is captured in memory but never sent. This affects Google and Microsoft OAuth buttons on both signup and signin pages. Email submit buttons ("Create account", "Continue") do not redirect — they call the Clerk API inline, so the page stays alive and the event flushes normally.

**Fix:**
- B1 (`posthog.reset()`) fixes the attribution issue.
- OAuth redirect flush via `{ send_instantly: true }` was **already implemented** before v2 on both `SignUpForm.tsx` and `SignInForm.tsx` OAuth button captures. No code change needed — verified by tests added in v2.

**`action_value` change:** The signin page's email submit button says **"Continue"** (not "Create account"). The v1 value `sign_in_with_email_button` is replaced by `continue_button` in v2 to match the actual button label. Old PostHog data still has the v1 value — dashboards filtering by `action_value` need updating.

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

### B4 — Identity Stitching: `posthog.reset()` on Auth Page Mount + `posthog.alias()` Before `posthog.identify()`

**Bug:** The PostHog identity lifecycle is incomplete. Two SDK calls are needed at auth transition points:

| SDK Call | Purpose | Pre-v2 State |
|---|---|---|
| `posthog.reset()` | Clears stored `distinct_id`, generates fresh anonymous ID | ✅ Called on logout (already existed). **Not called on auth page mount** — stale ID persists when user closes browser without logging out. |
| `posthog.identify(userId)` | Sets the `distinct_id` to the authenticated user | ✅ Called in `loginWithClerk()` |
| `posthog.alias(userId)` | Merges the current anonymous `distinct_id` into `userId` | **Never called on signup/login** — only in interview flow (`CandidateEntry.tsx:291,356`) |

Without `reset()` on auth page mount: if the previous user closed the browser without logging out, pre-auth events carry their real ID → `alias()` would merge two real users → data corruption.
Without `alias()`: pre-auth events (Page Viewed, Login Started Button Clicked) stay attributed to the anonymous ID → PostHog sees them as a different person → funnel breaks.

**Fix — two call sites (logout reset already existed):**

#### 1. `posthog.reset()` on auth page mount

**Where:** `SignUp.tsx` and `SignIn.tsx`, guarded by `!isLoading && !isAuthenticated && !hasPendingOAuthStrategy()`.

**What it does:** Clears the previous user's `distinct_id` from localStorage. Generates a fresh anonymous UUID. All subsequent pre-auth events fire with this clean anonymous ID.

**Why the guards matter:**
- `!isLoading` — waits for `tryRestoreSession()` to complete before deciding
- `!isAuthenticated` — prevents wiping an already-logged-in user's identity (bookmark/back button)
- `!hasPendingOAuthStrategy()` — suppresses during OAuth callback returns (`oauth_google`/`oauth_microsoft` only; email OTP and ticket strategies do NOT suppress)
- A `useRef` guard ensures the effect fires at most once per mount.

**Edge case — Auth Login Rejected:** If login fails (wrong OAuth, Clerk error), the user stays on the auth page. `posthog.reset()` already ran on mount — it does NOT run again. The user retries with the same anonymous distinct_id. When they eventually succeed, `alias()` works correctly.

#### 2. `posthog.alias(userId)` BEFORE `posthog.identify(userId)` — unconditionally

**Where:** `loginWithClerk()` in `authStore.ts`, immediately **before** `posthog.identify(userId)` (via `identifyUser()`).

**Critical: `alias()` must be called BEFORE `identify()`.** After `identify(userId)`, PostHog's current `distinct_id` is already `userId`, so `alias(userId)` would be a self-merge (userId → userId) — a no-op that never creates a `$create_alias` event. By calling `alias()` first, the current `distinct_id` is still the anonymous ID from `reset()`, so the SDK creates a proper merge: `anonymous-abc → userId`.

**Unconditional — called for both new and returning users.** The `reset()` on auth page mount guarantees a clean anonymous ID every time. For returning users, this creates a harmless merge of a throwaway anonymous session into the existing user — PostHog handles this gracefully.

**Edge case — user visits signup, leaves, comes back days later:**
- Visit 1: `posthog.reset()` → anon-1 → Page Viewed → user leaves
- Visit 2: `posthog.reset()` → anon-2 → Page Viewed → signs up → `alias(real-user)` merges anon-2
- Result: Visit 1 events stay orphaned as anon-1 (different browser session, cookie may have expired). Visit 2 events are correctly stitched. This is acceptable.

#### Logout — `posthog.reset()` already existed (no v2 change)

`posthog.reset()` on logout was already present before v2. The code order in `authStore.ts` logout is:
1. `capture(AUTH_LOGOUT_SUCCEEDED, { auth_mode })` — fires with the authenticated user's `distinct_id` still set
2. `resetPostHog()` — clears `distinct_id` and all super-properties

This order is intentional: the logout event is attributed to the user who logged out (not anonymous), then the state is cleared for the next session.

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
| Login Started Button Clicked | `continue_button` replaces `sign_in_with_email_button` (B2) | Signin page email button says "Continue" — v2 replaces the v1 value to match actual button label |
| Login Started Button Clicked | OAuth redirect flush verified (B2) | `{ send_instantly: true }` was already implemented — verified by tests, no code change needed |
| Auth Login Succeeded | Add `is_new_user` property | Boolean, derived from `user.role === null`. Event-level only (not a person property). |
| Auth Logout Succeeded | Logout `posthog.reset()` verified (B4) | Already existed before v2 — capture fires with authenticated identity, then reset clears state. No change needed. |
| Auth Session Restore Errored | Add 401 suppression note (A10) | Document that event is suppressed on 401 (unauthenticated visitor, expected state) |
| Profile Photo Upload Failed | Renamed (backlog #10) | → `Profile Photo Add Rejected` — object family + terminal alignment. Shipped with `error_category`: `unsupported_format`, `size_limit`. Also carries `previous_page_context` and `entity_type: candidate_profile`. |
| Account Create Succeeded | Remove `action`, `action_value`, `component` from catalog | Success type event — these are Interaction-type properties that don't belong. Codebase never sends them (confirmed: missing on 2/2 sampled PostHog rows). `current_page_context` also missing from PostHog data — remove if not sent by code. |
| Onboarding Persona Card Clicked | Update status from Dev to Live | Event is firing in production. Confirmed intentional — promote catalog status. |

### Property Fixes on Existing Events

#### Properties to Add

| Event | Property | Type | Values | Reason |
|---|---|---|---|---|
| Login Started Button Clicked | `action_value` | string | `continue_button` (replaces v1's `sign_in_with_email_button`) | Signin page email submit button says "Continue" — v2 uses the actual button label. Old PostHog data retains the v1 value. |
| Auth Login Succeeded | `is_new_user` | boolean | `true`, `false` | Derived from `user.role === null`. `true` = first-time signup (no role assigned yet). `false` = returning user. Event-level property, not `$set_once` — computed fresh each login. |

#### Properties to Remove

| Event | Property | Reason |
|---|---|---|
| Account Create Succeeded | `action` | Success type event — Interaction-type property. Never sent by codebase. |
| Account Create Succeeded | `action_value` | Same — never sent by codebase. |
| Account Create Succeeded | `component` | Same — never sent by codebase. |
| Account Create Succeeded | `current_page_context` | Missing from PostHog data — remove if confirmed not sent by code. |

---

## Property Dictionary Additions

`wizard_mode` was introduced in the v1 tracking plan and implemented in code, but was not added to the catalog Property Dictionary during the v1 merge. It was treated as an extension to existing events (adding a new `onboarding` value) without realizing the property itself was never in the dictionary — the gap accumulated across the HM Job Creation Wizard v2/v3 plans and the v1 onboarding plan. Adding it now.

| Property | Type | Scope | Allowed Values | Description | Used In |
|---|---|---|---|---|---|
| `wizard_mode` | enum | event | `onboarding`, `create`, `edit` | Context in which the job post wizard was initiated. `onboarding` = wizard launched during HM onboarding flow (`helix_onboarding_active` set in sessionStorage). `create` = wizard launched from job postings dashboard via "+ Create job" button. `edit` = wizard opened to edit an existing job posting. | Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Description Evaluated, Job Description Evaluation Failed, Job Post Wizard Intake Mode Selected, Sam Session Started, Sam Session Ended, Sam Session Setup Failed, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Posting Draft Created, Screening Configuration Saved, Job Posting Verified, Job Posting Published, and all Role Requirement / Screening Question CRUD events |

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Auth Page Switch Link | Navigation links between signup and signin pages | Auth Page Switch Link Clicked |

`Profile Photo Add` already exists as a Standard Object (from `Profile Photo Add Succeeded`). The rename and new error event complete the existing object family — no new object needed for that.

---

## Catalog Updates

Changes for `docs/helix/event-catalog.md` and `docs/helix/event-schema.md`:

- [ ] `Profile Photo Add Errored` → added to catalog (Prospect Events section). **Verify during implementation:** confirm `HeadshotUpload.tsx` has a server-error handling path. If the component only does client-side validation with no server error catch, this event needs a capture call added in the error handler.
- [ ] `Auth Page Switch Link Clicked` → added to catalog (Login & Onboarding Events section)
- [ ] `Profile Photo Upload Failed` → renamed to `Profile Photo Add Rejected` in catalog
- [ ] `Profile Photo Upload Failed` → added to Removed Events table
- [ ] Login Started Button Clicked → add `continue_button` to `action_value` in catalog and Property Dictionary
- [ ] Auth Session Restore Errored → add 401 suppression note to Trigger column
- [ ] Auth Logout Succeeded → add note about `posthog.reset()` call
- [ ] `wizard_mode` → added to Property Dictionary (Enum Properties section) with values `onboarding`, `create`, `edit`
- [ ] Identity stitching lifecycle → documented in event-schema.md (new section: PostHog Identity Lifecycle)
- [ ] `helix_session_id` boundary note → documented in event-schema.md
- [ ] Auth Login Succeeded → add `is_new_user` (boolean) to property list
- [ ] `is_new_user` → added to Property Dictionary: boolean, event-level, `true` when `user.role === null` (first signup), `false` for returning users
- [ ] `dashboards.md` → add identity stitching notes to Growth Dashboard onboarding funnels: `posthog.alias()` required, do NOT filter by `helix_session_id` across auth boundary
- [ ] Account Create Succeeded → remove `action`, `action_value`, `component`, `current_page_context` from catalog Properties column (Success type — Interaction properties never sent by codebase)
- [ ] Auth Email Verify Code Send Succeeded → removed from catalog (never implemented)
- [ ] Auth Email Verify Code Send Errored → removed from catalog (never implemented)
- [ ] Auth Email Verify Resend Clicked → removed from catalog (never implemented)
- [ ] Auth Email Verify Rejected → removed from catalog (never implemented)
- [ ] Onboarding Persona Card Clicked → update status from Dev to Live in catalog

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
| 4 | Returning user signin conversion | Page Viewed → Login Started Button Clicked → Auth Login Succeeded | Funnel | Filter: `current_page_context` = `auth_signin`. Breakdown by `auth_method`. | Growth |
| 5 | Auth page switch rate | Auth Page Switch Link Clicked | Trend | Breakdown by `action_value` (`sign_in_link` vs `sign_up_link`) — high sign-in clicks on signup = existing users arriving via signup links | Growth |

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

### 2. Signin Conversion Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signin` |
| 2 | Login Started Button Clicked | `current_page_context` = `auth_signin` |
| 3 | Auth Login Succeeded | — |

**Purpose:** Returning user signin conversion. Breakdown by `auth_method` to compare Google vs Microsoft vs email. Now possible because `posthog.reset()` (B1) ensures pre-auth events have clean anonymous distinct_id and `posthog.identify()` links them back to the existing user.

### 3. Auth Method Comparison Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Login Started Button Clicked | — |
| 2 | Auth Login Succeeded | — |

**Purpose:** Compare auth method conversion across both signup and signin. Breakdown by `auth_method` (google / microsoft / email). Optionally breakdown by `current_page_context` to compare signup vs signin conversion.

---

## Implementation Notes

### PostHog Identity Lifecycle — Complete Fix Chain

The identity stitching fix requires SDK calls at specific points in the auth lifecycle. `reset()` on auth page mount and `alias()` before `identify()` were added in v2. `reset()` on logout and `identify()` already existed.

```
AUTH PAGE MOUNT (SignUp.tsx / SignIn.tsx):
┌────────────────────────────────────────────────────┐
│ Wait for auth restore (!isLoading)                  │
│                                                     │
│ Guard: !isAuthenticated && !hasPendingOAuthStrategy()│
│   (oauth_google/oauth_microsoft suppress;           │
│    email_code/ticket do NOT suppress)               │
│   useRef guard: fires at most once per mount        │
│                                                     │
│ posthog.reset()                                     │
│   → Clears previous user's distinct_id              │
│   → Generates fresh anonymous ID "anon-xyz"         │
│   → Clears all super-properties (helix_session_id)  │
│                                                     │
│ posthog.capture('Page Viewed', { ... })              │
│   → distinct_id = "anon-xyz" (clean)                │
│                                                     │
│ User clicks auth button                             │
│ posthog.capture('Login Started Button Clicked',     │
│   props, { send_instantly: true })  ← OAuth buttons │
│   → distinct_id = "anon-xyz" (same clean ID)        │
└────────────────────────────────────────────────────┘

loginWithClerk() SUCCESS:
┌────────────────────────────────────────────────────┐
│ posthog.alias("user-B")         ← BEFORE identify  │
│   → current distinct_id is still "anon-xyz"         │
│   → Merges "anon-xyz" INTO "user-B"                 │
│   → PostHog retroactively attributes all anon-xyz   │
│     events to user-B                                │
│   → Called unconditionally (both new + returning)   │
│                                                     │
│ posthog.identify("user-B")      ← AFTER alias      │
│   → Sets distinct_id to real user going forward     │
│                                                     │
│ sessionManager.onAuthenticated()                    │
│   → Mints new helix_session_id                      │
│   → posthog.register({ helix_session_id: ... })     │
│                                                     │
│ posthog.capture('Auth Login Succeeded',             │
│   { ..., is_new_user: user.role === null })          │
│   → distinct_id = "user-B"                          │
│   → helix_session_id = "hs_2bf8..."                 │
└────────────────────────────────────────────────────┘

LOGOUT (pre-existing — no v2 change):
┌────────────────────────────────────────────────────┐
│ posthog.capture('Auth Logout Succeeded')            │
│   → Fires with authenticated user's distinct_id    │
│                                                     │
│ posthog.reset()                                     │
│   → Clears "user-B" from localStorage               │
│   → Next visitor gets clean anonymous ID             │
└────────────────────────────────────────────────────┘
```

### `posthog.reset()` Clears ALL Super-Properties

`posthog.reset()` does not just clear `distinct_id` — it clears ALL registered super-properties. Currently these are:
- `current_persona` — set via `posthog.register()` in `identifyUser()`
- `helix_session_id` — set via `posthog.register()` in `sessionManager.onAuthenticated()`

This is safe on auth page mount because both super-properties are re-set during `loginWithClerk()` after successful authentication. Pre-auth events (Page Viewed, Login Started Button Clicked) will NOT have `current_persona` or `helix_session_id` — this is correct and expected since the user hasn't authenticated yet.

On logout, `posthog.reset()` clears these after `Auth Logout Succeeded` has already been captured with the correct values. No data loss.

**If new super-properties are added in the future**, verify that they are re-set after login, or they will be lost when `posthog.reset()` fires on the next auth page mount.

### Edge Cases

| # | Scenario | Behavior | Safe? |
|---|---|---|---|
| 1 | Previous user logged out, new user visits signup | `reset()` on mount clears stale ID → fresh anon → `alias()` merges anon into new user | ✅ |
| 2 | Previous user closed browser without logout | `reset()` on mount clears stale ID (same as #1) | ✅ |
| 3 | Login fails (Auth Login Rejected), user retries | `reset()` already ran on mount, not re-run. Same anon ID for retry. `alias()` runs on eventual success. | ✅ |
| 4 | Returning user goes to /signin | `reset()` on mount clears their identified state → fresh anon. `alias()` merges anon into existing person (harmless — throwaway anon session). `identify()` sets distinct_id back to real user. | ✅ |
| 5 | User visits signup, leaves, comes back days later | Visit 1: anon-1 events stay orphaned. Visit 2: `reset()` → anon-2 → `alias()` merges anon-2 into real user. Anon-1 is lost. | ✅ (acceptable) |
| 6 | Same user signs up on two different browsers | Each browser has its own PostHog localStorage. `identify()` on both browsers links to same user. Only the browser where signup happened gets alias. | ✅ |
| 7 | Authenticated user hits auth page via bookmark | `!isAuthenticated` guard prevents `reset()` and `Page Viewed` from firing. User is redirected away. No PostHog identity wiped. | ✅ |
| 8 | OAuth callback return (Google/Microsoft) | `!hasPendingOAuthStrategy()` guard suppresses `reset()` and analytics. The form's exchange effect handles identity via `loginWithClerk()`. | ✅ |

### OAuth Redirect Flush for Login Started Button Clicked

OAuth button captures (Google, Microsoft) on both `SignUpForm.tsx` and `SignInForm.tsx` pass `{ send_instantly: true }` as the third argument to `capture()`. This forces the PostHog SDK to flush immediately before the browser redirects to the OAuth provider, preventing event loss.

This was **already implemented before v2** — verified by test assertions added in v2. No code change was needed.

### Profile Photo Event Rename

Constants renamed/added in both frontend and backend:
- `posthogEvents.ts` (frontend): `PROFILE_PHOTO_UPLOAD_FAILED` → `PROFILE_PHOTO_ADD_REJECTED`; added `PROFILE_PHOTO_ADD_ERRORED`
- `posthog_events.py` (backend): mirrored renames, both marked `# shared` for automated parity test coverage (`backend/tests/shared/test_posthog_events.py`)

Frontend/backend parity for these constants is enforced by the shared-constant parity test, not just by convention.

Old event data persists under `Profile Photo Upload Failed` in PostHog; new events fire as `Profile Photo Add Rejected` / `Profile Photo Add Errored` from deploy date.

### Files That Will Change in the v2 Helix Branch

| File | Change | Status |
|------|--------|--------|
| `frontend/src/pages/SignUp.tsx` | Add guarded `posthog.reset()` on mount (`!isLoading && !isAuthenticated && !hasPendingOAuthStrategy()`); remove stale `auth_landing` Page Viewed; add `Auth Page Switch Link Clicked` on "Sign in" link | Shipped |
| `frontend/src/pages/SignIn.tsx` | Add guarded `posthog.reset()` on mount; add `Auth Page Switch Link Clicked` on "Sign up" link | Shipped |
| `frontend/src/stores/authStore.ts` | Add `posthog.alias(userId)` BEFORE `identifyUser()` in `loginWithClerk()` (unconditional); add `is_new_user: user.role === null` to Auth Login Succeeded | Shipped |
| `frontend/src/components/auth/SignUpForm.tsx` | OAuth `send_instantly` verified (already existed) — test assertion added | Shipped |
| `frontend/src/components/auth/SignInForm.tsx` | `action_value` changed from `sign_in_with_email_button` to `continue_button` for email submit; OAuth `send_instantly` verified | Shipped |
| `frontend/src/lib/posthogEvents.ts` | Rename `PROFILE_PHOTO_UPLOAD_FAILED` → `PROFILE_PHOTO_ADD_REJECTED`; add `PROFILE_PHOTO_ADD_ERRORED` | Shipped |
| `backend/app/shared/posthog_events.py` | Mirror renames, both marked `# shared` for parity test | Shipped |
| `frontend/src/components/profile/HeadshotUpload.tsx` | Add `Profile Photo Add Errored` capture on server failure; add `previous_page_context` and `entity_type` to Rejected captures; simplify `error_category` to `server` only | Shipped |
| `knowledge-base/observability/posthog-analytics.md` | Add PostHog Identity Lifecycle section; update event taxonomy rows | Shipped |

---

## Backlog Items Addressed

| # | Item | Resolution in v2 |
|---|---|---|
| B1 | Pre-auth events carry stale `distinct_id` from previous user | Guarded `posthog.reset()` on auth page mount clears stale ID (`!isLoading && !isAuthenticated && !hasPendingOAuthStrategy()`); remove stale `auth_landing` Page Viewed |
| B2 | Login Started Button Clicked not visible on production | Attribution fixed by B1; OAuth `{ send_instantly: true }` was already present (verified); `continue_button` replaces `sign_in_with_email_button` |
| B3 | `helix_session_id` inconsistency across auth boundary | Documented as expected behavior — `helix_session_id` is post-auth only; funnels must not filter by it across auth |
| B4 | `distinct_id` mismatch breaks signup funnel (0% conversion) | Unconditional `posthog.alias()` BEFORE `posthog.identify()` merges anonymous pre-auth events into authenticated user; `posthog.reset()` on logout already existed (no v2 change) |
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
