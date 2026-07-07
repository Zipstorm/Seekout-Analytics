# Tracking Plan: Onboarding Flow v1

**Product:** Helix (SeekOut.ai)
**Feature:** Full onboarding funnel — signup through first meaningful action (portfolio creation for Professional, job post for HM, ATS connect for Recruiter)
**Date:** 2026-07-05
**Related PRD:** —
**Repo:** Zipstorm/helix
**Branch:** soumabrata/2026-07-06-onboarding-flow-v1
**PR:** https://github.com/Zipstorm/Seekout-Analytics/pull/36
**Status:** Approved

## Status History

| Status | Date | Trigger |
|---|---|---|
| Draft | 2026-07-05 | Plan created |
| Absorbed | 2026-07-06 | Codebase absorption from helix branch — 13 deviations applied |
| Review | 2026-07-07 | PR #36 updated after validator and review feedback; validator all clear |
| Approved | 2026-07-07 | PR #36 approved |

## Workflow

- [x] Draft created — 2026-07-05
- [ ] Validated — skipped (plan went to implementation before validation)
- [x] Codebase implemented — 2026-07-06
- [x] Absorbed from codebase — 2026-07-06
- [x] Re-validated — 2026-07-07 (All clear — 13 validation rules passed)
- [x] PR raised — 2026-07-06
- [x] PR approved — 2026-07-07
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/helix/event-schema.md`, and `docs/helix/event-catalog.md`.
> Audit: `plans/helix-onboarding-flow-audit.md`
> Screenshots: `context/helix/screenshots/onboarding/WORKFLOW.md`
> Deviations: `.plans/2026-07/2026-07-06-onboarding-flow-v1/tracking-plan-deviations.md` (helix repo)

---

## Scope

This plan covers the entire onboarding funnel for all personas. After codebase absorption it:

1. **Adds 4 catalog events** — persona card interaction, onboarding completion terminal, plus Handle Claim Succeeded/Rejected catalog cleanup entries replacing never-wired Candidate Handle Add rows
2. **Renames 16 onboarding events** — 12 for Succeeded/Rejected/Errored terminal rules, 2 for type reclassification (Started/Success → Interaction), 2 for convention alignment
3. **Removes 6 dead/never-wired events** — phone collection (not wired), Login Cancelled (dead code), catalog-only Candidate Handle Add names
4. **Extends Page Viewed** to 2 pages with no page-view tracking (email verification, activate profile)
5. **Fixes Login Started Button Clicked** to fire on production Clerk auth paths (was dev-only)
6. **Adds `mode` property** to events shared between onboarding and post-onboarding
7. **Registers `current_persona` as super-property** — automatically rides on all frontend events after login
8. **Fixes properties** — renames `role`/`persona` to `current_persona`, moves `$set_once` attribution to Page Viewed, adds `error_detail` parity, removes deprecated fields
9. **Adds `wizard_mode: 'onboarding'`** to job wizard events during HM onboarding
10. **Defines 6 funnels** mapped to analytics requirements

### Supersedes

This plan supersedes `tracking-plans/helix/helix-code-changes-login-onboarding.md` (status: Draft, April 2026, never implemented). That plan should be archived after this one is merged.

---

## New Events Summary

Overview of new catalog entries introduced by this plan. Renames are in the Event Renames section; Handle Claim rows are catalog cleanup entries that replace never-wired Candidate Handle Add catalog names.

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Onboarding Persona Card Clicked | Account | Interaction | Frontend | User clicks "I'm a professional" or "I'm hiring" or a hiring sub-option on `/onboarding/role` | Tracks which persona cards users explore before committing. Fires before persona is set. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Dev |
| Onboarding Complete Succeeded | Account | Success | Frontend | User lands on the first post-onboarding page after completing all onboarding steps | Terminal event marking the end of onboarding. Frontend fires via `maybeFireOnboardingComplete()` on terminal page mount: Professional portfolio/dashboard, HM dashboard or wizard success page, or Recruiter dashboard. | `current_page_context`, `previous_page_context`, `current_persona`, `auth_method`, `onboarding_duration_seconds`, `had_email_verification`, `has_resume`, `has_photo`, `has_handle`, `links_count` | -- | `$set_once: first_persona` | Dev |
| Handle Claim Succeeded | Prospect | Success | Frontend | Handle blur or submit, availability check returns available | User successfully claimed a handle. Catalog previously listed this as `Candidate Handle Add Succeeded` (never matched code). Code fired `Handle Claimed`, now renamed. | `handle_length`, `current_page_context`, `source`, `current_persona` | -- | -- | Dev |
| Handle Claim Rejected | Prospect | Rejected | Frontend | Handle blur or submit, availability check returns unavailable | Handle already taken or invalid. Catalog previously listed this as `Candidate Handle Add Rejected` (never matched code). Code fired `Handle Claim Failed`, now renamed. | `reason`, `current_page_context`, `source`, `current_persona` | -- | -- | Dev |

---

## Property Details

New or modified properties introduced by this plan. Properties already in the catalog Property Dictionary are not repeated.

| Property | Type | Values | Description |
|---|---|---|---|
| `onboarding_duration_seconds` | number | positive decimal seconds | Seconds elapsed from the first auth Page Viewed to Onboarding Complete Succeeded. Computed client-side as `(Date.now() - sessionStorage.helix_onboarding_start_ts) / 1000`; fractional precision is preserved. |
| `had_email_verification` | boolean | true/false | Whether the user went through the email verification step during onboarding. False for Google/Microsoft OAuth signups. |
| `has_resume` | boolean | true/false | Whether user uploaded a resume during onboarding (Professional only). |
| `has_photo` | boolean | true/false | Whether user added a profile photo during onboarding. |
| `has_handle` | boolean | true/false | Whether user claimed a handle during onboarding. |
| `links_count` | number | 0+ | Number of custom links added during onboarding. |
| `clerk_strategy` | enum | `oauth_google`, `oauth_microsoft`, `email_code`, `ticket`, `dev` | Which Clerk auth strategy was used. Already exists on Auth Login Succeeded; added to Auth Login Rejected for parity. |
| `mode` | enum | `onboarding`, `editor`, `dashboard`, `retake` | Context in which the action occurred. `onboarding` = during initial onboarding flow. Other values are existing or future. |
| `first_referrer` | string | hostname from `document.referrer` or null | HTTP referrer hostname at first visit. `$set_once` on auth Page Viewed. |
| `first_landing_url` | string | `window.location.href` | Full landing URL with query params. `$set_once` on auth Page Viewed. |

---

## Event Specifications

Detailed per-event specs. Updated after codebase absorption to reflect actuals.

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
| **Trigger** | User lands on the first post-onboarding page after completing all onboarding steps. Professional: portfolio editor or candidate dashboard. Hiring Manager: job postings dashboard when the wizard is skipped, or wizard success page when the wizard is completed. Recruiter: recruiter job postings dashboard when the ATS wizard is skipped. |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `candidate_editor`, `candidate_dashboard`, `hiring_manager_job_postings`, `hm_job_creation_wizard_success`, `recruiter_ai_job_flows` | Terminal landing page after onboarding: Professional portfolio/dashboard, HM skip path, HM wizard-complete path, or Recruiter skip path |
| `previous_page_context` | string | via `rotatePageContext()` | Last onboarding step |
| `current_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Active persona. Auto-stamped via super-property. |
| `auth_method` | enum | `google`, `microsoft`, `email` | How the user authenticated. Read from `sessionStorage.helix_auth_method`. |
| `onboarding_duration_seconds` | number | positive decimal seconds | Seconds from first auth Page Viewed to this event. Computed from `sessionStorage.helix_onboarding_start_ts`; fractional precision is preserved. |
| `had_email_verification` | boolean | true/false | Whether user went through email verification |
| `has_resume` | boolean | true/false | Whether user uploaded a resume (Professional only) |
| `has_photo` | boolean | true/false | Whether user added a profile photo |
| `has_handle` | boolean | true/false | Whether user claimed a handle |
| `links_count` | number | 0+ | Number of custom links added during onboarding |

**Property Updates:** `$set_once: first_persona`

**Deviation from original plan:**
- **Source changed:** Backend → Frontend. No single backend endpoint knows onboarding is complete. This is a navigation event — frontend owns the sessionStorage state, page context, and landing page detection. (Deviation #1)
- **`steps_completed` dropped.** Redundant — derivable from `current_persona`, `had_email_verification`, and terminal `current_page_context`. PostHog funnels already show per-step drop-off. (Deviation #3)

### Handle Claim Succeeded

| Field | Value |
|---|---|
| **Event** | Handle Claim Succeeded |
| **Area** | Prospect |
| **Type** | Success |
| **Trigger** | Handle blur or submit confirms the requested handle is available |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `handle_length` | number | 0+ | Character count of the requested handle |
| `current_page_context` | string | page context | Page where handle claim happened |
| `source` | string | `settings`, `profile_editor` | Surface that initiated the handle check, when available |
| `current_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Active persona |

**Catalog cleanup:** Replaces the never-wired catalog row `Candidate Handle Add Succeeded`. Code historically fired `Handle Claimed`; the catalog should use `Handle Claim Succeeded`.

### Handle Claim Rejected

| Field | Value |
|---|---|
| **Event** | Handle Claim Rejected |
| **Area** | Prospect |
| **Type** | Rejected |
| **Trigger** | Handle blur or submit confirms the requested handle is unavailable or invalid |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `reason` | string | backend reason | Why the handle was rejected |
| `current_page_context` | string | page context | Page where handle claim happened |
| `source` | string | `settings`, `profile_editor` | Surface that initiated the handle check, when available |
| `current_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Active persona |

**Catalog cleanup:** Replaces the never-wired catalog row `Candidate Handle Add Rejected`. Code historically fired `Handle Claim Failed`; the catalog should use `Handle Claim Rejected`.

### Login Started Button Clicked

| Field | Value |
|---|---|
| **Event** | Login Started Button Clicked |
| **Area** | Account |
| **Type** | Interaction |
| **Trigger** | User clicks an auth CTA: "Sign up with Google", "Sign up with Microsoft", "Create account" (email submit), or equivalent sign-in buttons. Fires on production Clerk paths — was previously dev-login only. |
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

**Deviation from original plan:** Renamed from `Login Started` to `Login Started Button Clicked`. This is a click event (user clicks an OAuth or email button), not a state transition. The `Button Clicked` suffix matches the actual user action. Type changed from Started to Interaction. (Deviation #6)

### Account Create Succeeded

| Field | Value |
|---|---|
| **Event** | Account Create Succeeded |
| **Area** | Account |
| **Type** | Success |
| **Trigger** | Server confirms role set via PATCH /users/me on first role selection |
| **Source** | Backend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_persona` | enum | `job_seeker`, `hiring_manager`, `recruiter` | Persona selected. Renamed from `persona` for consistency with all other events. (Deviation #9) |
| `auth_method` | enum | `google`, `microsoft`, `email` | How the user authenticated. Passed from frontend via sessionStorage. |

**Property Updates:** `$set: current_persona, activated_personas`; `$set_once: first_persona, account_created_at, referred_by`

**Deviation from original plan:** `first_surface` removed from `$set_once` — fully derivable from `first_persona`. (Deviation #10)

---

## Event Renames

Existing events renamed during this implementation. Organized by the type of change.

### Type Reclassification — Started/Success → Interaction

| Current Name | New Name | Old Type | New Type | Constant | Rationale |
|---|---|---|---|---|---|
| Login Started | Login Started Button Clicked | Started | Interaction | `LOGIN_STARTED` → `LOGIN_STARTED_BUTTON_CLICKED` | Click event, not state transition (Deviation #6) |
| Intro Completed | Onboarding Intro Complete Button Clicked | Success | Interaction | `INTRO_COMPLETED` → `ONBOARDING_INTRO_COMPLETE_BUTTON_CLICKED` | Click event, not async outcome (Deviation #5) |

### Success Events — Must End "Succeeded"

| Current Name | New Name | Type | Constant |
|---|---|---|---|
| Account Created | Account Create Succeeded | Success | `ACCOUNT_CREATED` → `ACCOUNT_CREATE_SUCCEEDED` |
| Auth Logout Completed | Auth Logout Succeeded | Success | `AUTH_LOGOUT_COMPLETED` → `AUTH_LOGOUT_SUCCEEDED` |
| Auth Email Verify Code Sent | Auth Email Verify Code Send Succeeded | Success | `AUTH_EMAIL_VERIFY_CODE_SENT` → `AUTH_EMAIL_VERIFY_CODE_SEND_SUCCEEDED` |
| Auth Email Verified | Auth Email Verify Succeeded | Success | `AUTH_EMAIL_VERIFIED` → `AUTH_EMAIL_VERIFY_SUCCEEDED` |
| Profile Photo Added | Profile Photo Add Succeeded | Success | `PROFILE_PHOTO_ADDED` → `PROFILE_PHOTO_ADD_SUCCEEDED` |
| Candidate Profile Created | Candidate Profile Create Succeeded | Success | `CANDIDATE_PROFILE_CREATED` → `CANDIDATE_PROFILE_CREATE_SUCCEEDED` |

**Note:** `Profile Photo Upload Failed` (the failure sibling) retains its old name — it has a different object prefix (`Profile Photo Upload` vs `Profile Photo Add`) and a non-conforming `Failed` terminal. This is a pre-existing catalog naming issue documented in `backlog/helix/onboarding-flow-deferred.md`, not fixed in this plan.

### Rejected Events — Must End "Rejected"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Login Failed | Auth Login Rejected | Rejected | User-initiated auth declined by system |
| Auth Email Verify Failed | Auth Email Verify Rejected | Rejected | Wrong code entered by user |

### Error Events — Must End "Errored"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Session Restore Failed | Auth Session Restore Errored | Error | System/network error, not user-caused |
| Auth Refresh Failed | Auth Refresh Errored | Error | Token refresh is a system process |
| Auth Email Verify Code Send Failed | Auth Email Verify Code Send Errored | Error | Server failed to send email |
| Candidate Profile Creation Failed | Candidate Profile Create Errored | Error | Backend portfolio generation failure (Deviation #8) |

---

## Removed Events

Events removed by this plan. Includes old names from renames and events deleted entirely.

| Event | Reason | Replaced By |
|---|---|---|
| Account Created | Renamed | Account Create Succeeded |
| Intro Completed | Renamed | Onboarding Intro Complete Button Clicked |
| Login Started | Renamed | Login Started Button Clicked |
| Auth Logout Completed | Renamed | Auth Logout Succeeded |
| Auth Login Failed | Renamed | Auth Login Rejected |
| Auth Email Verify Code Sent | Renamed | Auth Email Verify Code Send Succeeded |
| Auth Email Verified | Renamed | Auth Email Verify Succeeded |
| Auth Email Verify Failed | Renamed | Auth Email Verify Rejected |
| Auth Email Verify Code Send Failed | Renamed | Auth Email Verify Code Send Errored |
| Auth Session Restore Failed | Renamed | Auth Session Restore Errored |
| Auth Refresh Failed | Renamed | Auth Refresh Errored |
| Handle Claimed | Codebase name, never in catalog | Handle Claim Succeeded (new catalog entry) |
| Handle Claim Failed | Codebase name, never in catalog | Handle Claim Rejected (new catalog entry) |
| Profile Photo Added | Renamed | Profile Photo Add Succeeded |
| Candidate Profile Created | Renamed | Candidate Profile Create Succeeded |
| Candidate Profile Creation Failed | Renamed | Candidate Profile Create Errored |
| Login Cancelled | Dead code | — (old MSAL popup, never called since Clerk migration) |
| Auth Phone Submitted | Dead code | — (phone collection not wired into app router) |
| Auth Phone Submit Failed | Dead code | — (phone collection not wired into app router) |
| Auth Phone Skipped | Dead code | — (phone collection not wired into app router) |
| Candidate Handle Add Succeeded | Never wired | — (catalog name never matched code — code fires Handle Claimed) |
| Candidate Handle Add Rejected | Never wired | — (catalog name never matched code — code fires Handle Claim Failed) |

---

## Existing Event Updates

### Page Viewed Extensions

Pages that previously did not fire Page Viewed. This plan adds Page Viewed to each.

| Page | Route | `current_page_context` value | Notes |
|---|---|---|---|
| Email Verification | `/verify-email` | `onboarding_verify_email` | Skipped for Google/Microsoft OAuth (email pre-verified) |
| Activate Profile | `/candidate/activate` | `candidate_activate_profile` | Interview→signup path only (resume_copied = true) |

Each Page Viewed fires on component mount with standard properties: `current_page_context`, `previous_page_context`, `entry_point`.

**Note:** Create Profile (`/candidate/create-profile`) Page Viewed already fires from ProfileBuilderCards.tsx — no change needed.

### Page Viewed — Attribution on Auth Pages

When `current_page_context` is `auth_signup` or `auth_signin`, Page Viewed additionally sends `$set_once` attribution:

| Property | Type | Values | Description |
|---|---|---|---|
| `$set_once: entry_point` | enum | see entry_point values | First-touch attribution |
| `$set_once: first_referrer` | string | hostname from `document.referrer` or null | HTTP referrer hostname at first visit |
| `$set_once: first_landing_url` | string | `window.location.href` | Full landing URL with query params |

This attribution was moved from Login Started to Page Viewed so it captures attribution even if the user bounces before clicking a login button.

### `current_persona` Super-Property

`current_persona` is now registered as a PostHog super-property via `posthog.register({ current_persona: ... })` inside `identifyUser()`. This means `current_persona` automatically rides on every frontend `capture()` call after login/role assignment, without needing to be manually added to each event. (Deviation #11)

Individual `current_persona` properties were removed from capture() calls where they were manually added (now redundant — the super-property handles it).

### `mode` Property Extension on CreateProfile Events

Existing catalog events on the create-profile page now include `mode: 'onboarding'` during onboarding. The `mode` prop is threaded through the component tree: `CreateProfile.tsx` → `ProfileBuilderCards` → `ResumeDropzone`, `HeadshotUpload`, `LinkEditor`.

| Event | mode value | Notes |
|---|---|---|
| Candidate Resume Upload Button Clicked | `onboarding` | Via ResumeDropzone `mode` prop |
| Candidate Resume Upload Succeeded | `onboarding` | Via resume upload API `?mode=` query param |
| Candidate Resume Upload Rejected | `onboarding` | Via resume upload API `?mode=` query param |
| Candidate Resume Upload Errored | `onboarding` | Via resume upload API `?mode=` query param |
| Candidate Resume Remove Button Clicked | `onboarding` | Via ResumeDropzone `mode` prop |
| LinkedIn Export Learn How Link Clicked | `onboarding` | Via ProfileBuilderCards `mode` prop |
| Add Profile Photo Button Clicked | `onboarding` | Via HeadshotUpload `mode` prop |
| Profile Photo Add Succeeded | `onboarding` | Via HeadshotUpload `mode` prop |
| Profile Photo Upload Failed | `onboarding` | Via HeadshotUpload `mode` prop |
| Candidate Profile Photo Remove Button Clicked | `onboarding` | Via HeadshotUpload `mode` prop |
| Candidate Profile Photo Remove Succeeded | `onboarding` | Via HeadshotUpload `mode` prop |
| Candidate Profile Photo Remove Errored | `onboarding` | Via HeadshotUpload `mode` prop |
| Link Validation Error Shown | `onboarding` | Via LinkEditor `mode` prop |
| Candidate Profile Custom Link Add Succeeded | `onboarding` | Via link API `mode` param |
| Candidate Custom Link Delete Button Clicked | `onboarding` | Via LinkEditor `mode` prop |
| Candidate Custom Link Delete Succeeded | `onboarding` | Via link API `mode` param |
| Candidate Custom Link Delete Errored | `onboarding` | Via link API `mode` param |
| Build Profile Button Clicked | `onboarding` | Via ProfileBuilderCards `mode` prop |
| Candidate Profile Create Succeeded | `onboarding` | Via portfolio API `dto.mode` |
| Candidate Profile Create Errored | `onboarding` | Via portfolio API `dto.mode` |

**Handle Claim events removed from onboarding.** Handle claim during profile creation is an implementation detail of "Build my portfolio", not a user-visible action worth tracking separately. The Settings page retains Handle Claim Succeeded/Rejected for explicit handle-edit flows. (Deviation #4)

**Post-onboarding:** editor and dashboard pages should send `mode: 'editor'` or `mode: 'dashboard'` respectively. This is a future update — existing events continue as-is until they adopt the `mode` property.

### `wizard_mode: 'onboarding'` on Job Wizard Events

When `helix_onboarding_active` is set in sessionStorage (HM onboarding), `getWizardAnalyticsState()` returns `wizard_mode: 'onboarding'` instead of `'create'`. This affects all job wizard events (Job Post Wizard Started, Job Description Evaluated, etc.) and lets dashboards distinguish onboarding-initiated jobs from dashboard-initiated jobs. (Deviation #12)

### Existing Event Fixes

| Event | Change | Detail |
|---|---|---|
| Login Started Button Clicked | Trigger fix | Now fires on production Clerk OAuth and email-code buttons (was dev-login only). Fires from SignUpForm.tsx and SignInForm.tsx. |
| Page Viewed (signup) | Value rename | `current_page_context` changed from `auth_landing` to `auth_signup` for consistency with `auth_signin`. |
| Auth Session Restore Errored | 401 suppression | Suppressed when `status_code === 401` (unauthenticated visitor, no refresh token cookie). Expected state, not an error. (Deviation #13) |

### Property Fixes on Existing Events

#### Properties to Remove

| Event | Property | Reason |
|---|---|---|
| Onboarding Intro Complete Button Clicked (was Intro Completed) | `context_object_type` | Deprecated, was hardcoded to null |
| Onboarding Intro Complete Button Clicked (was Intro Completed) | `context_object_id` | Deprecated, was hardcoded to null |
| `identify()` calls (all backend paths) | `first_surface` ($set_once) | Redundant — derivable from `first_persona` (Deviation #10) |

#### Properties to Rename

| Event | Current Property | New Property | Reason |
|---|---|---|---|
| Auth Login Succeeded | `role` | `current_persona` | `role` is raw enum (HIRING_MANAGER); `current_persona` uses mapped values (hiring_manager) via `ROLE_TO_PERSONA`. |
| Auth Dev Login Succeeded | `role` | `current_persona` | Same as above |
| Auth Session Restore Succeeded | `role` | `current_persona` | Same as above |
| Auth Email Verify Succeeded (was Auth Email Verified) | `role` | `current_persona` | Same as above |
| Account Create Succeeded (was Account Created) | `persona` | `current_persona` | Consistency with all other events (Deviation #9) |
| `identify()` calls (all backend paths) | `role` ($set) | `current_persona` ($set) | Same mapping as event properties |

#### Properties to Add

| Event | Property | Type | Values | Reason |
|---|---|---|---|---|
| Auth Session Restore Errored | `error_detail` | string | error message | Parity with other error events |
| Auth Refresh Errored | `error_detail` | string | error message | Parity with other error events (both authStore.ts and authApi.ts interceptor paths) |
| Auth Email Verify Code Send Errored | `error_detail` | string | error message | Already in catalog but was not in codebase |

**Note:** The original tracking plan also listed `error_detail` additions for Auth Phone Submit Failed and Auth Dev Login Failed. These were skipped — phone events are removed (dead code), and Auth Dev Login Failed references the old name. (Deviation #2)

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Onboarding Persona Card | Persona selection card on onboarding page | Onboarding Persona Card Clicked |
| Onboarding Complete | Full onboarding flow lifecycle | Onboarding Complete Succeeded |
| Account Create | User account creation (rename of Account) | Account Create Succeeded |
| Onboarding Intro Complete Button | Onboarding intro "Let's go" button (rename of Intro) | Onboarding Intro Complete Button Clicked |
| Login Started Button | Auth CTA buttons on signup/signin pages (rename of Login) | Login Started Button Clicked |
| Auth Login | Authentication login lifecycle | Auth Login Rejected |
| Auth Email Verify Code Send | Email OTP dispatch lifecycle | Auth Email Verify Code Send Succeeded, Auth Email Verify Code Send Errored |
| Auth Email Verify | Email verification lifecycle | Auth Email Verify Succeeded, Auth Email Verify Rejected |
| Auth Logout | Logout lifecycle (rename of Auth) | Auth Logout Succeeded |
| Auth Session Restore | Session restore lifecycle | Auth Session Restore Errored |
| Auth Refresh | Token refresh lifecycle | Auth Refresh Errored |
| Handle Claim | Handle claim lifecycle (rename of Handle) | Handle Claim Succeeded, Handle Claim Rejected |
| Profile Photo Add | Profile photo upload lifecycle (rename of Profile Photo) | Profile Photo Add Succeeded |
| Candidate Profile Create | Portfolio creation lifecycle (rename of Candidate Profile) | Candidate Profile Create Succeeded, Candidate Profile Create Errored |

---

## Catalog Updates

New events from this plan to add to `docs/helix/event-catalog.md`:

- [ ] Onboarding Persona Card Clicked → Login & Onboarding Events
- [ ] Onboarding Complete Succeeded → Login & Onboarding Events
- [ ] Handle Claim Succeeded → Prospect Events (catalog cleanup replacing Candidate Handle Add Succeeded)
- [ ] Handle Claim Rejected → Prospect Events (catalog cleanup replacing Candidate Handle Add Rejected)
- [ ] 16 events renamed (old names → Removed Events table)
- [ ] 6 dead/never-wired events removed
- [ ] `mode` property extended with value `onboarding`
- [ ] `wizard_mode` extended with value `onboarding`
- [ ] Page Viewed → add `auth_signup` as `current_page_context` value (replaces `auth_landing`)
- [ ] Page Viewed → 2 new `current_page_context` values: `onboarding_verify_email`, `candidate_activate_profile`
- [ ] `current_persona` registered as super-property (rides on all frontend events)
- [ ] 14 New Standard Objects added

---

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Login / Signup | Login Started Button Clicked | Account Create Succeeded (new user) or Auth Login Succeeded (returning) | Auth Login Rejected | -- |
| Email verification | -- | Auth Email Verify Code Send Succeeded | Auth Email Verify Rejected | Auth Email Verify Code Send Errored |
| Persona selection | Onboarding Persona Card Clicked | Account Create Succeeded | -- | -- |
| Intro completion | Onboarding Intro Complete Button Clicked | -- | -- | -- |
| Resume upload (onboarding) | Candidate Resume Upload Button Clicked | Candidate Resume Upload Succeeded | Candidate Resume Upload Rejected | Candidate Resume Upload Errored |
| Profile photo (onboarding) | Add Profile Photo Button Clicked | Profile Photo Add Succeeded | Profile Photo Upload Failed | -- |
| Profile creation (onboarding) | Build Profile Button Clicked | Candidate Profile Create Succeeded | -- | Candidate Profile Create Errored |
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
| 5 | Friction detection — error rates | Auth Login Rejected, Auth Email Verify Rejected, Auth Email Verify Code Send Errored, Candidate Resume Upload Rejected, Candidate Resume Upload Errored, Profile Photo Upload Failed, Candidate Profile Create Errored | Trend | Breakdown by `error_category` | Platform Health |
| 6 | Traffic source attribution | Page Viewed (filter: `current_page_context` in `auth_signup`, `auth_signin`) | Trend | Breakdown by `$set_once: entry_point`, `$set_once: first_referrer` | Growth |
| 7 | Time to complete onboarding | Onboarding Complete Succeeded | Trend (avg/median) | Breakdown by `current_persona`, `auth_method`; property: `onboarding_duration_seconds` | Growth |
| 8 | Resume upload success rate during onboarding | Candidate Resume Upload Button Clicked → Candidate Resume Upload Succeeded (filter: `mode = onboarding`) | Funnel | Breakdown by `resume_file_type` | Prospect |
| 9 | Profile photo adoption during onboarding | Add Profile Photo Button Clicked → Profile Photo Add Succeeded (filter: `mode = onboarding`) | Funnel | -- | Prospect |
| 10 | Persona exploration behavior | Onboarding Persona Card Clicked | Trend | Breakdown by `action_value` | Growth |
| 11 | Email verification completion rate | Page Viewed (filter: `current_page_context = onboarding_verify_email`) → Auth Email Verify Succeeded | Funnel | -- | Growth |

---

## Funnels

### 1. Full Onboarding Funnel (Professional)

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` or `auth_signin` |
| 2 | Login Started Button Clicked | — |
| 3 | Auth Login Succeeded | — |
| 4 | Page Viewed | `current_page_context` = `onboarding_role_selection` |
| 5 | Account Create Succeeded | `first_persona` = `job_seeker` |
| 6 | Onboarding Intro Complete Button Clicked | — |
| 7 | Page Viewed | `current_page_context` = `candidate_create_profile` |
| 8 | Candidate Resume Upload Succeeded | `mode` = `onboarding` |
| 9 | Build Profile Button Clicked | `mode` = `onboarding` |
| 10 | Candidate Profile Create Succeeded | `mode` = `onboarding` |
| 11 | Onboarding Complete Succeeded | `current_persona` = `job_seeker` |

**Purpose:** End-to-end Professional onboarding conversion. Identify the biggest drop-off points.

### 2. Full Onboarding Funnel (Hiring Manager)

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` or `auth_signin` |
| 2 | Login Started Button Clicked | — |
| 3 | Auth Login Succeeded | — |
| 4 | Account Create Succeeded | `first_persona` = `hiring_manager` |
| 5 | Onboarding Intro Complete Button Clicked | — |
| 6 | Onboarding Complete Succeeded | `current_persona` = `hiring_manager` |

**Purpose:** HM onboarding conversion. Shorter funnel since HM goes directly to job wizard.

### 3. Auth Method Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` in (`auth_signup`, `auth_signin`) |
| 2 | Login Started Button Clicked | — |
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
| 2 | Onboarding Intro Complete Button Clicked | — |
| 3 | Onboarding Complete Succeeded | — |

**Purpose:** Post-account-creation completion rate. Breakdown by `current_persona` to compare personas.

---

## Implementation Notes

### Onboarding State Machine (sessionStorage)

The implementation uses sessionStorage keys to track onboarding state across page navigations:

| Key | Set In | Read By | Purpose |
|---|---|---|---|
| `helix_onboarding_start_ts` | SignUp.tsx / Login.tsx on page load | `maybeFireOnboardingComplete()` | Compute `onboarding_duration_seconds` |
| `helix_onboarding_active` | RoleSelection.tsx after first role assignment | `maybeFireOnboardingComplete()` guard; `getWizardAnalyticsState()` | Gates Onboarding Complete Succeeded; sets `wizard_mode: 'onboarding'` |
| `helix_auth_method` | SignUpForm.tsx / SignInForm.tsx before OAuth redirect | `maybeFireOnboardingComplete()`; RoleSelection.tsx | Auth method for onboarding events |
| `helix_onboarding_complete_fired` | `maybeFireOnboardingComplete()` after firing | `maybeFireOnboardingComplete()` guard | Prevents double-firing |

### `mode` Property Threading

`mode` is threaded through the component tree via React props: `CreateProfile.tsx` passes `mode="onboarding"` to `ProfileBuilderCards`, which passes it to `ResumeDropzone`, `HeadshotUpload`, and `LinkEditor`. Backend endpoints receive `mode` as a query param (`?mode=onboarding`) or DTO field.

### Event Rename Migration

Each rename was coordinated across:
1. `posthogEvents.ts` (frontend constants)
2. `posthog_events.py` (backend constants)
3. PostHog — old event name data persists; new name captures from deploy date
4. Catalog — old name moves to Removed Events table after `/merge-tracking-plan`

### `current_persona` Super-Property

Registered via `posthog.register({ current_persona: mappedPersona })` inside `identifyUser()` in `posthog.ts`. The `ROLE_TO_PERSONA` mapping converts raw role enums to analytics values:
- `PROFESSIONAL` / `JOB_SEEKER` → `job_seeker`
- `HIRING_MANAGER` → `hiring_manager`
- `RECRUITER` → `recruiter`
