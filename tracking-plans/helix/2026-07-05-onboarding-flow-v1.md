# Tracking Plan: Onboarding Flow v1

**Product:** Helix (SeekOut.ai)
**Feature:** Full onboarding funnel — signup through first meaningful action (portfolio creation for Professional, job post for HM, ATS connect for Recruiter)
**Date:** 2026-07-05
**Related PRD:** —
**Repo:** Zipstorm/helix
**Branch:** —
**PR:** —
**Status:** Draft

## Status History

| Status | Date | Trigger |
|---|---|---|
| Draft | 2026-07-05 | Plan created |

## Workflow

- [x] Draft created — 2026-07-05
- [ ] Validated
- [ ] Codebase implemented
- [ ] Absorbed from codebase
- [ ] Re-validated
- [ ] PR raised
- [ ] PR approved
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/helix/event-schema.md`, and `docs/helix/event-catalog.md`.
> Audit: `plans/helix-onboarding-flow-audit.md`
> Screenshots: `context/helix/screenshots/onboarding/WORKFLOW.md`

---

## Scope

This plan covers the entire onboarding funnel for all personas. It:

1. **Adds 2 new events** — persona card interaction, onboarding completion terminal
2. **Extends Page Viewed** to 3 pages that currently have no page-view tracking
3. **Fixes Login Started** to fire on production Clerk auth paths (currently dev-only)
4. **Adds `mode` property** to events shared between onboarding and post-onboarding
5. **Renames 12 onboarding events** to follow Succeeded/Rejected/Errored terminal rules
6. **Removes 6 dead events** — phone collection (not wired), Login Cancelled (dead code), catalog-only handle names
7. **Fixes properties** — replaces `role` with `current_persona` as event property, moves $set_once attribution, removes deprecated fields
8. **Adds `current_persona` as event property** on all post-persona-selection events so persona is frozen at capture time
9. **Defines 6 funnels** mapped to the user's analytics requirements

### Supersedes

This plan supersedes `tracking-plans/helix/helix-code-changes-login-onboarding.md` (status: Draft, April 2026, never implemented). That plan should be archived after this one is merged.

---

## Part A — New Events

### New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Onboarding Persona Card Clicked | Account | Interaction | Frontend | User clicks "I'm a professional" or "I'm hiring" or a hiring sub-option (Hiring Manager / Recruiter) on `/onboarding/role` | Tracks which persona cards users explore before committing. Fires before persona is set. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Not Started |
| Onboarding Complete Succeeded | Account | Success | Backend | User completes all onboarding steps and lands on the first post-onboarding page | Terminal event marking the end of onboarding. Backend confirms onboarding state is complete. | `current_page_context`, `previous_page_context`, `current_persona`, `first_persona`, `auth_method`, `onboarding_duration_seconds`, `steps_completed` | -- | -- | Not Started |
| Account Create Succeeded | Account | Success | Backend | Server confirms role set via PATCH /users/me on first role selection (rename of Account Created) | Backend fires after persisting the user's first persona. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entry_point`, `entity_type`, `component`, `first_persona`, `auth_method`, `referred_by` | -- | `$set: current_persona, activated_personas`; `$set_once: first_persona, account_created_at, referred_by` | Not Started |
| Onboarding Intro Complete Succeeded | Account | Success | Frontend | User clicks "Let's go" on onboarding intro page (rename of Intro Completed) | Pure UI transition — no backend call. Frontend-only because there is no server-side state change. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `auth_method`, `current_persona` | -- | -- | Not Started |
| Auth Login Rejected | Account | Rejected | Backend | Backend returns auth error on /auth/login (rename of Auth Login Failed) | Server rejected the auth attempt. | `auth_mode`, `clerk_strategy`, `status_code`, `error_detail` | -- | -- | Not Started |
| Auth Email Verify Code Send Succeeded | Account | Success | Backend | Backend sends verification code to user's email (rename of Auth Email Verify Code Sent) | Server dispatched OTP successfully. | `cooldown_seconds` | -- | -- | Not Started |
| Auth Email Verify Code Send Errored | Account | Error | Backend | Backend failed to send verification code (rename of Auth Email Verify Code Send Failed) | Server error dispatching email OTP. | `status_code`, `error_detail` | -- | -- | Not Started |
| Auth Email Verify Succeeded | Account | Success | Backend | Backend confirms OTP code is correct (rename of Auth Email Verified) | Server verified the code. | -- | -- | -- | Not Started |
| Auth Email Verify Rejected | Account | Rejected | Backend | Backend rejects OTP code (rename of Auth Email Verify Failed) | Wrong code — server rejected. | `status_code`, `error_detail`, `attempts_remaining` | -- | -- | Not Started |
| Auth Logout Succeeded | Account | Success | Backend | Backend confirms logout via POST /auth/logout (rename of Auth Logout Completed) | Server revoked the session. | `auth_mode` | -- | -- | Not Started |
| Handle Claim Succeeded | Prospect | Success | Frontend | Handle blur or submit, availability check returns available (rename of Handle Claimed) | User successfully claimed a handle. | `handle_length`, `current_page_context`, `source`, `current_persona` | -- | -- | Not Started |
| Handle Claim Rejected | Prospect | Rejected | Frontend | Handle blur or submit, availability check returns unavailable (rename of Handle Claim Failed) | Handle already taken or invalid. | `reason`, `current_page_context`, `source`, `current_persona` | -- | -- | Not Started |
| Auth Session Restore Errored | Account | Error | Backend | Backend refresh token call fails (rename of Auth Session Restore Failed) | Server could not restore session. | `status_code`, `error_detail` | -- | -- | Not Started |
| Auth Refresh Errored | Account | Error | Backend | Backend token refresh fails (rename of Auth Refresh Failed) | Server error during token refresh. | `source`, `status_code`, `error_detail` | -- | -- | Not Started |

---

## Property Details

New properties introduced by this plan. Properties already in the catalog Property Dictionary are not repeated here.

| Property | Type | Values | Description |
|---|---|---|---|
| `onboarding_duration_seconds` | number | positive integer | Seconds elapsed from the first auth Page Viewed (signup/signin page) to Onboarding Complete Succeeded. Computed client-side: `(Date.now() - sessionStorage.helix_onboarding_start_ts) / 1000`. |
| `steps_completed` | number | 3–6 | Number of onboarding steps the user completed. Varies by persona (Professional has more steps) and by whether conditional steps (email verification, phone collection) were shown. |
| `had_email_verification` | boolean | true/false | Whether the user went through the email verification step during onboarding. False for Google/Microsoft OAuth signups. |
| `had_phone_collection` | boolean | true/false | Whether the user saw the phone collection step during onboarding. |
| `clerk_strategy` | enum | `oauth_google`, `oauth_microsoft`, `email_code`, `ticket`, `dev` | Which Clerk auth strategy was used. Already exists on Auth Login Succeeded; added to Auth Login Rejected for parity. |

---

## Part B — Page Viewed Coverage

These pages currently do **not** fire Page Viewed. This plan adds Page Viewed to each.

| Page | Route | `current_page_context` value | Notes |
|---|---|---|---|
| Email Verification | `/verify-email` | `onboarding_verify_email` | Skipped for Google/Microsoft OAuth (email pre-verified) |
| Create Profile | `/candidate/create-profile` | `candidate_create_profile` | Mandatory for Professional persona. Page Viewed already fires from ProfileBuilderCards.tsx. |
| Activate Profile | `/candidate/activate` | `candidate_activate_profile` | Interview→signup path only (resume_copied = true) |

Each Page Viewed fires on component mount with standard properties:
- `current_page_context` — value from table above
- `previous_page_context` — via `rotatePageContext()`
- `entry_point` — from `?context=` URL param or `'direct'`

---

## Part C — Login Started Production Fix

**Problem:** Login Started only fires for the dev login button. Production users using Clerk OAuth (Google/Microsoft) or email-code never trigger Login Started. This breaks the production signup funnel.

**Fix:** Fire Login Started when the user clicks "Sign up with Google", "Sign up with Microsoft", "Create account" (email), or the equivalent sign-in buttons.

### Login Started — Updated Specification

| Field | Value |
|---|---|
| **Event** | Login Started |
| **Area** | Account |
| **Type** | Started |
| **Trigger** | User clicks an auth CTA: "Sign up with Google", "Sign up with Microsoft", "Create account" (email submit), or equivalent sign-in buttons |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User action type |
| `action_value` | string | `sign_up_with_google_button`, `sign_up_with_microsoft_button`, `create_account_button`, `sign_in_with_google_button`, `sign_in_with_microsoft_button`, `dev_login_button` | Exact button text in snake_case |
| `auth_method` | enum | `google`, `microsoft`, `email`, `dev` | Which auth method was initiated |
| `current_page_context` | string | `auth_signup`, `auth_signin` | Page where login was initiated |
| `previous_page_context` | string | via `rotatePageContext()` | Previous page |
| `entry_point` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct`, `interview` | From `?context=` URL param |
| `entity_type` | string | `account` | Business object |
| `component` | string | `auth_signup_card_cta`, `auth_signin_card_cta` | UI container |

**Also:** Move `$set_once` attribution (`entry_point`, `first_referrer`, `first_landing_url`) from Login Started to **Page Viewed** on the signup/signin pages. This captures attribution even if the user bounces before clicking a login button.

### Page Viewed — Attribution Update

When `current_page_context` is `auth_signup` or `auth_signin`, Page Viewed additionally sends:

| Property | Type | Values | Description |
|---|---|---|---|
| `$set_once: entry_point` | enum | see entry_point values | First-touch attribution |
| `$set_once: first_referrer` | string | `document.referrer` or null | HTTP referrer at first visit |
| `$set_once: first_landing_url` | string | `window.location.href` | Full landing URL with query params |

**Note:** `current_page_context` for SignUp.tsx changes from `auth_landing` to `auth_signup` for consistency with `auth_signin` on Login.tsx.

---

## Part D — CreateProfile.tsx Event Wiring

CreateProfile.tsx (`/candidate/create-profile`) currently has **zero** `capture()` calls. The following existing events need to be wired up on this page. Each gets a new `mode` property to distinguish onboarding from post-onboarding usage.

### `mode` Property Extension

| Property | Type | Values | Description |
|---|---|---|---|
| `mode` | enum | `onboarding`, `editor`, `dashboard`, `retake` | Context in which the action occurred. `onboarding` = during initial onboarding flow; `editor` = from portfolio editor; `dashboard` = from candidate dashboard. Existing value `retake` remains for interview retake events. |

### Events to Wire on CreateProfile.tsx (with `mode: 'onboarding'`)

All events below already exist in the catalog. The change is: (a) they now fire on CreateProfile.tsx during onboarding, and (b) they include `mode: 'onboarding'`.

| Event | Trigger on CreateProfile | mode value | New properties added |
|---|---|---|---|
| Candidate Resume Upload Button Clicked | User clicks resume upload area | `onboarding` | `mode` |
| Candidate Resume Upload Succeeded | Backend confirms resume stored | `onboarding` | `mode` |
| Candidate Resume Upload Rejected | Client-side validation rejects | `onboarding` | `mode` |
| Candidate Resume Upload Errored | Server extraction fails | `onboarding` | `mode` |
| Candidate Resume Remove Button Clicked | User clicks "Remove" on uploaded resume | `onboarding` | `mode` |
| LinkedIn Export Learn How Link Clicked | User clicks "Learn how" link under "No resume?" | `onboarding` | `mode` |
| Add Profile Photo Button Clicked | User clicks "Add profile image" | `onboarding` | `mode` |
| Profile Photo Added | Photo saved successfully | `onboarding` | `mode` |
| Profile Photo Upload Failed | Photo rejected (size/format) | `onboarding` | `mode` |
| Handle Claim Succeeded | Handle blur, availability = available (rename of Handle Claimed) | `onboarding` | `mode`, `current_persona` |
| Handle Claim Rejected | Handle blur, availability = unavailable (rename of Handle Claim Failed) | `onboarding` | `mode`, `current_persona` |
| Candidate Profile Custom Link Add Succeeded | User adds a link (GitHub, LinkedIn, etc.) | `onboarding` | `mode` |
| Candidate Custom Link Delete Button Clicked | User clicks trash on an added link | `onboarding` | `mode` |
| Candidate Custom Link Delete Succeeded | Link deletion confirmed | `onboarding` | `mode` |
| Build Profile Button Clicked | User clicks "Build my portfolio" | `onboarding` | `mode` |
| Candidate Profile Created | Backend generates portfolio | `onboarding` | `mode` |
| Candidate Profile Creation Failed | Backend portfolio generation fails | `onboarding` | `mode` |

**Post-onboarding events** on the editor and dashboard pages should send `mode: 'editor'` or `mode: 'dashboard'` respectively. This is a future update — existing editor events continue as-is until they adopt the `mode` property.

---

## Part E — Event Renames (Onboarding Scope)

These events currently violate the naming rules from `docs/shared/naming-and-event-types.md`. Each rename updates both the catalog and the codebase constant.

### Success Events → Must End "Succeeded"

| Current Name | New Name | Type | Constant in posthogEvents.ts |
|---|---|---|---|
| Account Created | Account Create Succeeded | Success | `ACCOUNT_CREATED` → `ACCOUNT_CREATE_SUCCEEDED` |
| Intro Completed | Onboarding Intro Complete Succeeded | Success | `INTRO_COMPLETED` → `ONBOARDING_INTRO_COMPLETE_SUCCEEDED` |
| Auth Logout Completed | Auth Logout Succeeded | Success | `AUTH_LOGOUT_COMPLETED` → `AUTH_LOGOUT_SUCCEEDED` |
| Auth Email Verify Code Sent | Auth Email Verify Code Send Succeeded | Success | `AUTH_EMAIL_VERIFY_CODE_SENT` → `AUTH_EMAIL_VERIFY_CODE_SEND_SUCCEEDED` |
| Auth Email Verified | Auth Email Verify Succeeded | Success | `AUTH_EMAIL_VERIFIED` → `AUTH_EMAIL_VERIFY_SUCCEEDED` |
| Handle Claimed | Handle Claim Succeeded | Success | `HANDLE_CLAIMED` → `HANDLE_CLAIM_SUCCEEDED` |

### Rejected Events → Must End "Rejected"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Login Failed | Auth Login Rejected | Rejected | User-initiated auth declined by system |
| Auth Email Verify Failed | Auth Email Verify Rejected | Rejected | Wrong code entered by user |
| Handle Claim Failed | Handle Claim Rejected | Rejected | Handle taken or invalid |

### Error Events → Must End "Errored"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Session Restore Failed | Auth Session Restore Errored | Error | System/network error, not user-caused |
| Auth Refresh Failed | Auth Refresh Errored | Error | Token refresh is a system process |
| Auth Email Verify Code Send Failed | Auth Email Verify Code Send Errored | Error | Server failed to send email |

### Removed Events

| Event | Reason | Replaced By |
|---|---|---|
| Account Created | Renamed | Account Create Succeeded |
| Intro Completed | Renamed | Onboarding Intro Complete Succeeded |
| Auth Logout Completed | Renamed | Auth Logout Succeeded |
| Auth Login Failed | Renamed | Auth Login Rejected |
| Auth Email Verify Code Sent | Renamed | Auth Email Verify Code Send Succeeded |
| Auth Email Verified | Renamed | Auth Email Verify Succeeded |
| Auth Email Verify Failed | Renamed | Auth Email Verify Rejected |
| Auth Email Verify Code Send Failed | Renamed | Auth Email Verify Code Send Errored |
| Auth Session Restore Failed | Renamed | Auth Session Restore Errored |
| Auth Refresh Failed | Renamed | Auth Refresh Errored |
| Handle Claimed | Renamed | Handle Claim Succeeded |
| Handle Claim Failed | Renamed | Handle Claim Rejected |
| Login Cancelled | Removed | Dead code — was for old MSAL popup, never called since Clerk migration |
| Auth Phone Submitted | Removed | Phone collection not wired into app router |
| Auth Phone Submit Failed | Removed | Phone collection not wired into app router |
| Auth Phone Skipped | Removed | Phone collection not wired into app router |
| Candidate Handle Add Succeeded | Removed | Catalog name never matched code — code fires Handle Claimed |
| Candidate Handle Add Rejected | Removed | Catalog name never matched code — code fires Handle Claim Failed |

---

## Part F — Property Fixes on Existing Events

### Properties to Remove

| Event | Property | Reason |
|---|---|---|
| Intro Completed (→ Onboarding Intro Complete Succeeded) | `context_object_type` | Deprecated, hardcoded to null |
| Intro Completed (→ Onboarding Intro Complete Succeeded) | `context_object_id` | Deprecated, hardcoded to null |

### Properties to Rename

| Event | Current Property | New Property | Reason |
|---|---|---|---|
| Auth Login Succeeded | `role` | `current_persona` | `role` is raw enum (HIRING_MANAGER); `current_persona` uses mapped values (hiring_manager). Frozen as event property so persona switches don't retroactively change historical data. |
| Auth Dev Login Succeeded | `role` | `current_persona` | Same as above |
| Auth Session Restore Succeeded | `role` | `current_persona` | Same as above |
| Auth Email Verified (→ Auth Email Verify Succeeded) | `role` | `current_persona` | Same as above |

### Properties to Add

| Event | Property | Type | Values | Reason |
|---|---|---|---|---|
| Auth Dev Login Failed (→ Auth Dev Login Rejected) | `error_detail` | string | error message | Parity with Auth Login Rejected |
| Auth Email Verify Code Send Failed (→ Auth Email Verify Code Send Errored) | `error_detail` | string | error message | Already in catalog but not in codebase |
| Auth Session Restore Failed (→ Auth Session Restore Errored) | `error_detail` | string | error message | Parity with other failure events |
| Auth Refresh Failed (→ Auth Refresh Errored) | `error_detail` | string | error message | Parity with other failure events |
| Auth Phone Submit Failed (→ Auth Phone Submit Errored) | `error_detail` | string | error message | Already in catalog but not in codebase |

### Property Rename

| Event | Current Property | New Property | Reason |
|---|---|---|---|
| Page Viewed (signup) | `current_page_context: 'auth_landing'` | `current_page_context: 'auth_signup'` | Consistency with `auth_signin` on Login.tsx |

---

## Event Specifications

### Onboarding Persona Card Clicked

| Field | Value |
|---|---|
| **Event** | Onboarding Persona Card Clicked |
| **Area** | Account |
| **Type** | Interaction |
| **Trigger** | User clicks "I'm a professional" card, "I'm hiring" card, "Hiring Manager" sub-option, or "Recruiter" sub-option on the persona selection page |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User action type |
| `action_value` | string | `im_a_professional_card`, `im_hiring_card`, `hiring_manager_option`, `recruiter_option` | Exact card/option clicked in snake_case |
| `current_page_context` | string | `onboarding_role_selection` | Page context |
| `previous_page_context` | string | via `rotatePageContext()` | Previous page |
| `entity_type` | string | `onboarding` | Business object |
| `component` | string | `onboarding_role_selection_card_group` | UI container |

### Onboarding Complete Succeeded

| Field | Value |
|---|---|
| **Event** | Onboarding Complete Succeeded |
| **Area** | Account |
| **Type** | Success |
| **Trigger** | User lands on the first post-onboarding page after completing all onboarding steps. For Professional: portfolio editor (`/candidate/editor/:id`). For HM: job postings dashboard or wizard success page. For Recruiter: job postings dashboard. |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `candidate_editor`, `hiring_manager_job_posting`, `recruiter_ats_connect` | Landing page after onboarding |
| `previous_page_context` | string | via `rotatePageContext()` | Last onboarding step |
| `current_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Active persona at the time of event capture. Frozen as event property so persona switches don't retroactively change historical data. |
| `first_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Persona selected during onboarding. Reuses existing person property ($set_once). |
| `auth_method` | enum | `google`, `microsoft`, `email` | How the user authenticated |
| `onboarding_duration_seconds` | number | positive integer | Seconds from Page Viewed on auth page to this event. Computed client-side from sessionStorage timestamp set on first auth Page Viewed. |
| `steps_completed` | number | 3–6 | Number of onboarding steps completed (varies by persona and whether email/phone were shown) |
| `had_email_verification` | boolean | true/false | Whether the user went through the email verification step |
| `had_phone_collection` | boolean | true/false | Whether the user saw the phone collection step |
| `has_resume` | boolean | true/false | Whether user uploaded a resume (Professional only) |
| `has_photo` | boolean | true/false | Whether user added a profile photo |
| `has_handle` | boolean | true/false | Whether user claimed a handle |
| `links_count` | number | 0+ | Number of links added during onboarding |

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Onboarding Persona Card | Persona selection card on onboarding page | Onboarding Persona Card Clicked |
| Onboarding Complete | Full onboarding flow lifecycle | Onboarding Complete Succeeded |
| Account Create | User account creation (rename of Account) | Account Create Succeeded |
| Onboarding Intro Complete | Onboarding intro screen completion (rename of Intro) | Onboarding Intro Complete Succeeded |
| Auth Login | Authentication login lifecycle | Auth Login Rejected |
| Auth Email Verify Code Send | Email OTP dispatch lifecycle | Auth Email Verify Code Send Succeeded, Auth Email Verify Code Send Errored |
| Auth Email Verify | Email verification lifecycle | Auth Email Verify Succeeded, Auth Email Verify Rejected |
| Auth Logout | Logout lifecycle (rename of Auth) | Auth Logout Succeeded |
| Auth Session Restore | Session restore lifecycle | Auth Session Restore Errored |
| Auth Refresh | Token refresh lifecycle | Auth Refresh Errored |
| Handle Claim | Handle claim lifecycle (rename of Handle Claimed/Claim Failed) | Handle Claim Succeeded, Handle Claim Rejected |

## Catalog Updates

New events from this plan to add to `docs/helix/event-catalog.md`:

- [ ] Onboarding Persona Card Clicked → Login & Onboarding Events
- [ ] Onboarding Complete Succeeded → Login & Onboarding Events
- [ ] New object added to Standard Objects table: Yes — Onboarding Persona Card, Onboarding
- [ ] `mode` property extended with values `onboarding`, `editor`, `dashboard`
- [ ] 14 events renamed (old names → Removed Events table)
- [ ] Page Viewed → add `auth_signup` as `current_page_context` value (replaces `auth_landing`)
- [ ] Page Viewed → 4 new `current_page_context` values: `onboarding_verify_email`, `onboarding_phone`, `candidate_create_profile`, `candidate_activate_profile`

---

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Login / Signup | Login Started | Account Create Succeeded (new user) or Auth Login Succeeded (returning) | Auth Login Rejected | -- |
| Email verification | -- | Auth Email Verify Code Send Succeeded | Auth Email Verify Rejected | Auth Email Verify Code Send Errored |
| Persona selection | Onboarding Persona Card Clicked | Account Create Succeeded | -- | -- |
| Intro completion | -- | Onboarding Intro Complete Succeeded | -- | -- |
| Resume upload (onboarding) | Candidate Resume Upload Button Clicked | Candidate Resume Upload Succeeded | Candidate Resume Upload Rejected | Candidate Resume Upload Errored |
| Profile photo (onboarding) | Add Profile Photo Button Clicked | Profile Photo Added | Profile Photo Upload Failed | -- |
| Handle claim | -- | Handle Claim Succeeded | Handle Claim Rejected | -- |
| Profile creation (onboarding) | Build Profile Button Clicked | Candidate Profile Created | Candidate Profile Creation Failed | -- |
| Onboarding completion | -- | Onboarding Complete Succeeded | -- | -- |
| Session restore | -- | Auth Session Restore Succeeded | -- | Auth Session Restore Errored |

---

## Metrics → Events Mapping

| # | Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|---|
| 1 | How many people land on the site | Page Viewed (filter: `current_page_context` in `auth_signup`, `auth_signin`) | Trend | Breakdown by `current_page_context`, `entry_point` | Growth |
| 2 | How many create an account | Account Create Succeeded | Trend | Breakdown by `first_persona`, `auth_method` | Growth |
| 3 | Where is the drop-off | Full onboarding funnel (see Funnels below) | Funnel | Breakdown by `current_persona`, `auth_method` | Growth |
| 4 | Which persona is selected most | Account Create Succeeded | Trend | Breakdown by `first_persona` | Growth |
| 5 | Friction detection — error rates | Auth Login Rejected, Auth Email Verify Rejected, Auth Email Verify Code Send Errored, Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Profile Photo Upload Failed, Candidate Profile Creation Failed, Handle Claim Rejected | Trend | Breakdown by `error_category` | Platform Health |
| 6 | Traffic source attribution | Page Viewed (filter: `current_page_context` in `auth_signup`, `auth_signin`) | Trend | Breakdown by `$set_once: entry_point`, `$set_once: first_referrer` | Growth |
| 7 | Time to complete onboarding | Onboarding Complete Succeeded | Trend (avg/median) | Breakdown by `current_persona`, `auth_method`; property: `onboarding_duration_seconds` | Growth |
| 8 | Resume upload success rate during onboarding | Candidate Resume Upload Button Clicked → Candidate Resume Upload Succeeded (filter: `mode = onboarding`) | Funnel | Breakdown by `resume_file_type` | Prospect |
| 9 | Profile photo adoption during onboarding | Add Profile Photo Button Clicked → Profile Photo Added (filter: `mode = onboarding`) | Funnel | -- | Prospect |
| 10 | Handle claim rate during onboarding | Handle Claim Succeeded (filter: `mode = onboarding`) / Onboarding Complete Succeeded (filter: `current_persona = job_seeker`) | Formula | -- | Prospect |
| 11 | Persona exploration behavior | Onboarding Persona Card Clicked | Trend | Breakdown by `action_value` | Growth |
| 12 | Email verification completion rate | Page Viewed (filter: `current_page_context = onboarding_verify_email`) → Auth Email Verify Succeeded | Funnel | -- | Growth |
| 13 | Time per onboarding step | Onboarding Complete Succeeded | Trend | Property: `onboarding_duration_seconds`, breakdown by `steps_completed` | Growth |

---

## Funnels

### 1. Full Onboarding Funnel (Professional)

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` or `auth_signin` |
| 2 | Login Started | — |
| 3 | Auth Login Succeeded | — |
| 4 | Page Viewed | `current_page_context` = `onboarding_role_selection` |
| 5 | Account Create Succeeded | `first_persona` = `job_seeker` |
| 6 | Onboarding Intro Complete Succeeded | — |
| 7 | Page Viewed | `current_page_context` = `candidate_create_profile` |
| 8 | Candidate Resume Upload Succeeded | `mode` = `onboarding` |
| 9 | Build Profile Button Clicked | `mode` = `onboarding` |
| 10 | Candidate Profile Created | `mode` = `onboarding` |
| 11 | Onboarding Complete Succeeded | `current_persona` = `job_seeker` |

**Purpose:** End-to-end Professional onboarding conversion. Identify the biggest drop-off points.

### 2. Full Onboarding Funnel (Hiring Manager)

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` or `auth_signin` |
| 2 | Login Started | — |
| 3 | Auth Login Succeeded | — |
| 4 | Account Create Succeeded | `first_persona` = `hiring_manager` |
| 5 | Onboarding Intro Complete Succeeded | — |
| 6 | Onboarding Complete Succeeded | `current_persona` = `hiring_manager` |

**Purpose:** HM onboarding conversion. Shorter funnel since HM goes directly to job wizard.

### 3. Auth Method Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` in (`auth_signup`, `auth_signin`) |
| 2 | Login Started | — |
| 3 | Auth Login Succeeded | — |

**Purpose:** Compare conversion rates across auth methods. Breakdown by `auth_method`.

### 4. Email Verification Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `onboarding_verify_email` |
| 2 | Auth Email Verify Code Send Succeeded | — |
| 3 | Auth Email Verify Succeeded | — |

**Purpose:** Email verification completion rate. Only for non-OAuth paths.

### 5. Resume Upload Funnel (Onboarding)

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `candidate_create_profile` |
| 2 | Candidate Resume Upload Button Clicked | `mode` = `onboarding` |
| 3 | Candidate Resume Upload Succeeded | `mode` = `onboarding` |
| 4 | Build Profile Button Clicked | `mode` = `onboarding` |

**Purpose:** Resume upload → portfolio creation conversion during onboarding. Breakdown by `resume_file_type`.

### 6. Signup-to-First-Value Funnel (All Personas)

| Step | Event | Filter |
|---|---|---|
| 1 | Account Create Succeeded | — |
| 2 | Onboarding Intro Complete Succeeded | — |
| 3 | Onboarding Complete Succeeded | — |

**Purpose:** Post-account-creation completion rate. Breakdown by `current_persona` to compare personas.

---

## Implementation Notes

### CreateProfile.tsx — Zero to Full Coverage

`CreateProfile.tsx` at `helix-app/frontend/src/pages/candidate/CreateProfile.tsx` currently has no `import { capture } from '@/lib/posthog'` and no analytics calls. The implementation needs to:

1. Import `capture` from `@/lib/posthog` and relevant event constants from `@/lib/posthogEvents`
2. Add `useEffect` for Page Viewed on mount
3. Wire resume upload events (the upload component likely already fires these — verify during absorption)
4. Wire photo upload events
5. Wire handle validation events
6. Wire link add/delete events
7. Wire Build Profile Button Clicked on the "Build my portfolio" button
8. All events on this page include `mode: 'onboarding'`

### Onboarding Duration Tracking

To compute `onboarding_duration_seconds` on Onboarding Complete Succeeded:
1. On the first auth Page Viewed (`auth_signup` or `auth_signin`), store `Date.now()` in `sessionStorage` as `helix_onboarding_start_ts`
2. On Onboarding Complete Succeeded, compute `(Date.now() - helix_onboarding_start_ts) / 1000`
3. Clear the key after firing

### Login Started — Clerk Integration Points

Login Started needs to fire at the Clerk component level:
- **OAuth buttons:** When user clicks "Sign up with Google" or "Sign up with Microsoft" — fire before the OAuth redirect
- **Email submit:** When user clicks "Create account" after entering email — fire before the OTP flow begins
- **Sign-in equivalents:** Same for the sign-in page

The Clerk SDK exposes `onSubmit` and button click handlers where these can be captured.

### Event Rename Migration

Each rename requires coordinated changes:
1. **posthogEvents.ts** (frontend) — rename constant and string value
2. **posthog_events.py** (backend) — rename constant and string value (for backend-emitted events)
3. **PostHog** — old event name data persists; new name starts capturing from deploy date
4. **Dashboards/funnels** — update any PostHog saved insights to use new event names
5. **Catalog** — old name moves to Removed Events table

Renames should be batched in a single PR to minimize dashboard disruption.
