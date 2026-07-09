# Tracking Plan: Recruit Onboarding Flow

**Product:** Recruit
**Feature:** Onboarding (login, signup, first-time setup)
**Date:** 2026-07-09
**Related PRD:** —
**Repo:** recruit-ui (frontend), recruit-api (backend)
**Branch:** recruit-onboarding-v1
**PR:** [#42](https://github.com/Zipstorm/Seekout-Analytics/pull/42)
**Status:** Draft

## Status History

| Status | Date | Trigger |
|---|---|---|
| Draft | 2026-07-09 | Plan created |

## Workflow

- [x] Draft created
- [x] Validated
- [x] PR raised (draft review — pre-implementation)
- [ ] Codebase implemented
- [ ] Absorbed from codebase
- [ ] Re-validated
- [ ] PR approved
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/recruit/event-schema.md`, and `docs/recruit/event-catalog.md`.

---

## Scope

1. **21 distinct event names** — Login page (6 frontend), Pricing page (5 marketing site), Free trial form (2 marketing site), Request meeting (2 marketing site), Request demo (1 marketing site), Backend auth lifecycle (7 backend). Page Viewed is reused across 5 page contexts.
2. **Backend data pipeline** — `trial_signups` table for permanent trial signup records
3. More events will be added as additional onboarding screens are documented

> **Note:** Events on the pricing, free trial, request meeting, and request demo pages fire on `seekout.com` (marketing site), NOT `app.seekout.io` (product). Implementation will require PostHog setup on the marketing site codebase separately from recruit-ui. The same PostHog project must be used, and cross-site identity must be handled by passing the PostHog `distinct_id` as a URL parameter (e.g., `seekout.com/pricing/?ph_id=abc123`) when users navigate from `app.seekout.io` to `seekout.com`. Without this handoff, PostHog will treat the same user as two separate people across sites, and cross-site funnels will not work. See Implementation Notes for details.
>
> **Migration note:** Existing Mixpanel events stay as-is. New PostHog events fire in parallel alongside them. No Mixpanel events are removed or modified. Frontend events will be implemented first, backend events will follow in the same tracking plan — they are not separate initiatives.

---

## New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Page Viewed | Navigation | View | Frontend | User lands on a meaningful page | Reusable — fires on every page. `current_page_context` distinguishes pages. Auth pages also set first-touch attribution. | `current_page_context`, `previous_page_context`, `entry_point` (auth pages) | -- | `$set_once: entry_point, first_referrer, first_landing_url` (login page only) | Local |
| Sign In Button Clicked | Auth | Interaction | Frontend | User clicks "Sign In" button to submit email/password login | Returning user initiating credential-based login. Fires on form submit, not on successful auth. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Sign In With SSO Link Clicked | Auth | Interaction | Frontend | User clicks "Sign in with SSO" link | User switching to SSO auth mode. Toggles the form to SSO email input. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Get A Free Trial Link Clicked | Auth | Interaction | Frontend | User clicks "Get a free trial" link | New user CTA — navigates to external pricing page (`seekout.com/pricing`). Indicates trial acquisition intent from login page. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| SSO Sign In Button Clicked | Auth | Interaction | Frontend | User clicks "Sign In" button on the SSO form to initiate SSO redirect | User has entered email on SSO form and is submitting to start SSO authentication. This is the actual SSO initiation, not just the toggle. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Sign In Without SSO Link Clicked | Auth | Interaction | Frontend | User clicks "Sign in without SSO" to switch back to email/password form | User toggling back from SSO mode to standard login. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Pricing Billing Toggle Clicked | Pricing | Interaction | Marketing Site | User toggles between Monthly and Annual billing | Captures billing preference. Affects displayed prices and "Save $360/yr" badge visibility. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Start Free Trial Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Start free trial" or "Get free trial" on pricing page | Multiple CTAs lead to the same free trial form. `component` distinguishes which CTA was clicked. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `pricing_plan`, `billing_cycle` | -- | -- | Local |
| Book A Demo Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Book a demo" under a pricing plan card | Navigates to `seekout.com/requestdemo/`. `pricing_plan` captures which plan they're interested in. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `pricing_plan`, `billing_cycle` | -- | -- | Local |
| Book One To One Demo Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Book a 1:1 demo" in the nav bar | Navigates to `seekout.com/request-meeting/` (broader form with product interest dropdown). Different destination from plan-level "Book a demo". | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| See Whats Included Link Clicked | Pricing | Interaction | Marketing Site | User clicks "See what's included" under a pricing plan card | Expands plan feature details inline. `pricing_plan` captures which plan. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `pricing_plan`, `billing_cycle` | -- | -- | Local |
| Request Free Trial Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Request free trial" on the free trial form page | Form submit on `seekout.com/free-trial/`. User has filled in name, email, company, job title, country. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Request Meeting Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Request meeting" on the request-meeting form page | Form submit on `seekout.com/request-meeting/`. Includes product interest dropdown. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component`, `product_interest` | -- | -- | Local |
| Book A Demo Form Button Clicked | Pricing | Interaction | Marketing Site | User clicks "Book a demo" on the request-demo form page | Form submit on `seekout.com/requestdemo/`. SeekOut Recruit focused. | `action`, `action_value`, `current_page_context`, `previous_page_context`, `entity_type`, `component` | -- | -- | Local |
| Auth Login Succeeded | Auth | Success | Backend (recruit-api) | Backend confirms successful login (email, SSO, or impersonate) | Completes the Sign In Button Clicked → result pattern. Fires for all auth methods. | `auth_method`, `sku_id`, `organization_id` | -- | `$set: sku_id, organization_id, email, name, company_name, last_login_at` | Local |
| Auth Login Rejected | Auth | Rejected | Backend (recruit-api) | Backend returns auth error (wrong password, locked account, etc.) | User-caused login failure. Not a technical error. | `auth_method`, `rejection_reason` | -- | -- | Local |
| Auth Login Errored | Auth | Error | Backend (recruit-api) | Technical failure during auth (database error, service timeout) | System failure, not user-caused. | `auth_method`, `error_category`, `error_detail` | -- | -- | Local |
| Trial Account Created Succeeded | Auth | Success | Backend (recruit-api) | User clicks activation link, sets password, account is created | Fires at `POST /api/auth/register` when a free trial user activates. Not when the form is submitted — when the user actually activates via the email link. | `sku_id`, `trial_duration_days`, `organization_id`, `signup_source` | -- | `$set: sku_id, email, name, company_name`; `$set_once: trial_start_date, trial_sku_id` | Local |
| Trial Account Request Succeeded | Auth | Success | Backend (recruit-api) | recruit-api accepts the trial request and creates NewUser record | Fires at `POST /api/auth/workspace/register` when validation passes and the NewUser record is created. Before the user activates — just confirms the request was accepted. | `signup_source` | -- | -- | Local |
| Trial Account Request Rejected | Auth | Rejected | Backend (recruit-api) | recruit-api rejects the trial request | Domain limit reached, email already exists, active license, etc. | `trial_rejection_reason`, `signup_source` | -- | -- | Local |
| Trial Account Request Errored | Auth | Error | Backend (recruit-api) | Technical failure processing the trial request | Service unavailable, database error. | `error_category`, `error_detail` | -- | -- | Local |

---

## Property Details

Properties shared across multiple events are listed once. These follow the same standard property structure as Helix — ensuring cross-product consistency.

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | snake_case page identifier | Page where the event fired. Route path transformed to snake_case (e.g., `/signIn` → `sign_in`). All frontend events. |
| `previous_page_context` | string | snake_case page identifier or `null` | Page the user was on before navigating here. `null` if direct entry / external referrer. All frontend events. |
| `sku_id` | string | `WORKSPACES_FREE_TRIAL`, `RECRUIT_CORE_ANNUAL`, `RECRUIT_SOURCING_MONTHLY` | User's current plan/SKU at the time the event fires. All post-auth events. Pre-auth events (login page, marketing site) will not have this. |
| `action` | enum | `click`, `submit`, `toggle` | What the user did. All Interaction type events. |
| `action_value` | string | exact UI label in snake_case | Exact button/link text the user clicked, in snake_case. Never paraphrased. All Interaction type events. |
| `entity_type` | string | `account`, `pricing`, `meeting` | Domain the action relates to. All Interaction type events. |
| `component` | string | see per-event specs | Exact page location of the UI element — specific enough to locate without seeing the screen. All Interaction type events. |
| `entry_point` | string | `direct`, `email_invite`, `share_link`, `sso_redirect` | How the user arrived at the platform. Derived from a `?context=` URL param (to be added). Page Viewed on auth pages only. |
| `auth_method` | enum | `email`, `sso`, `impersonate` | How the user authenticated. `impersonate` is for staff testing customer accounts. Auth Login events only. |
| `rejection_reason` | enum | `invalid_credentials`, `account_locked`, `account_not_found`, `email_not_verified` | Why a login was rejected. Auth Login Rejected only. |
| `error_category` | enum | `database`, `service_unavailable`, `internal` | Category of technical failure. Auth Login Errored and Trial Account Request Errored. |
| `error_detail` | string | error message | Specific error, sanitized — no PII. Auth Login Errored and Trial Account Request Errored. |
| `organization_id` | string | UUID | User's organization ID. Auth Login Succeeded and Trial Account Created Succeeded. |
| `signup_source` | enum | `pricing_page`, `direct` | Where the trial signup originated. Trial Account Created Succeeded, Trial Account Request Succeeded, and Trial Account Request Rejected. |
| `trial_duration_days` | number | `14` | Trial length in days. Trial Account Created Succeeded only. |
| `pricing_plan` | enum | `seekout_recruit_core`, `seekout_recruit_sourcing`, `seekout_recruit_sourcing_integration`, `seekout_recruit_full_recruiting_funnel` | Which pricing plan card the user interacted with. Pricing page events only. |
| `billing_cycle` | enum | `monthly`, `annual` | Which billing toggle was active when the user clicked. Pricing page events only. |
| `product_interest` | enum | `recruiting_tools`, `recruiting_services`, `both` | Value selected in "What are you interested in?" dropdown. Request Meeting Button Clicked only. |
| `trial_rejection_reason` | enum | `domain_limit_reached`, `email_already_exists`, `active_free_trial`, `free_trial_completed`, `active_license`, `invalid_email` | Why a trial request was rejected. Trial Account Request Rejected only. |

---

## Event Specifications

### Page Viewed

| Field | Value |
|---|---|
| **Event** | Page Viewed |
| **Area** | Navigation |
| **Type** | View |
| **Trigger** | User lands on `/signIn` (login page loads) |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `sign_in` | Identifies this as the login page |
| `previous_page_context` | string | varies | Page before this one. `null` for direct / external entry. |
| `entry_point` | string | `direct`, `email_invite`, `share_link`, `sso_redirect` | How user arrived at the platform. Derived from `?context=` URL param. `direct` if no param. |

**Property Updates (login page only):**
- `$set_once: entry_point` — first-touch attribution, never overwritten
- `$set_once: first_referrer` — `document.referrer` at first visit
- `$set_once: first_landing_url` — full landing URL including query params

**Notes:**
- Page Viewed is a reusable event — fires on every meaningful page across the app, with `current_page_context` distinguishing pages. Same pattern as Helix.
- The login page is pre-auth, so this fires for anonymous users. PostHog uses an anonymous `distinct_id` until login, then merges via `posthog.identify()`.
- `entry_point` and `$set_once` properties only fire on auth pages (login, signup). Other pages fire Page Viewed with just `current_page_context` and `previous_page_context`.

---

### Sign In Button Clicked

| Field | Value |
|---|---|
| **Event** | Sign In Button Clicked |
| **Area** | Auth |
| **Type** | Interaction |
| **Trigger** | User clicks the "Sign In" button (form submit for email/password login) |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the button |
| `action_value` | string | `sign_in` | Exact button label "Sign In" in snake_case |
| `current_page_context` | string | `sign_in` | Login page |
| `previous_page_context` | string | varies | Page before login page |
| `entity_type` | string | `account` | Auth/account domain |
| `component` | string | `login_form_submit_button` | Submit button inside the email/password login form |

**Notes:**
- Fires on form submit, not on successful authentication. Backend fires Auth Login Succeeded / Rejected / Errored after processing.
- Currently tracked as `useraction` with `actionLabel: 'Sign In'` — the new event replaces that.

---

### Sign In With SSO Link Clicked

| Field | Value |
|---|---|
| **Event** | Sign In With SSO Link Clicked |
| **Area** | Auth |
| **Type** | Interaction |
| **Trigger** | User clicks "Sign in with SSO" link below the Sign In button |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the link |
| `action_value` | string | `sign_in_with_sso` | Exact link label "Sign in with SSO" in snake_case |
| `current_page_context` | string | `sign_in` | Login page |
| `previous_page_context` | string | varies | Page before login page |
| `entity_type` | string | `account` | Auth/account domain |
| `component` | string | `login_form_sso_toggle_link` | SSO toggle link below the submit button in the login form |

**Notes:**
- This toggles the form to SSO mode (email-only field). It does not initiate the SSO redirect — that happens on the SSO form's submit.
- Currently tracked as `useraction` with `actionLabel: 'Sign in with SSO'`.

---

### Get A Free Trial Link Clicked

| Field | Value |
|---|---|
| **Event** | Get A Free Trial Link Clicked |
| **Area** | Auth |
| **Type** | Interaction |
| **Trigger** | User clicks "Get a free trial" link in "Don't have an account?" section |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the link |
| `action_value` | string | `get_a_free_trial` | Exact link label "Get a free trial" in snake_case |
| `current_page_context` | string | `sign_in` | Login page |
| `previous_page_context` | string | varies | Page before login page |
| `entity_type` | string | `account` | Auth/account domain |
| `component` | string | `login_page_free_trial_cta` | Free trial link at the bottom of the login page, below the form |

**Notes:**
- Navigates to external marketing site (`seekout.com/pricing`) — user leaves the app.
- Currently no tracking exists for this link.

---

### SSO Sign In Button Clicked

| Field | Value |
|---|---|
| **Event** | SSO Sign In Button Clicked |
| **Area** | Auth |
| **Type** | Interaction |
| **Trigger** | User clicks "Sign In" button on the SSO form (submits email, initiates SSO redirect to organization's identity provider) |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the button |
| `action_value` | string | `sign_in` | Exact button label "Sign In" in snake_case |
| `current_page_context` | string | `sign_in` | Login page (SSO mode) |
| `previous_page_context` | string | varies | Page before login page |
| `entity_type` | string | `account` | Auth/account domain |
| `component` | string | `login_sso_form_submit_button` | Submit button inside the SSO email form |

**Notes:**
- This is different from Sign In Button Clicked (email/password form). `component` distinguishes them: `login_form_submit_button` vs `login_sso_form_submit_button`.
- After this fires, the browser redirects to the organization's SSO provider. The result comes back via `Auth Login Succeeded` (`auth_method: sso`).

---

### Sign In Without SSO Link Clicked

| Field | Value |
|---|---|
| **Event** | Sign In Without SSO Link Clicked |
| **Area** | Auth |
| **Type** | Interaction |
| **Trigger** | User clicks "Sign in without SSO" link to switch back to email/password form |
| **Source** | Frontend |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the link |
| `action_value` | string | `sign_in_without_sso` | Exact link label "Sign in without SSO" in snake_case |
| `current_page_context` | string | `sign_in` | Login page (SSO mode) |
| `previous_page_context` | string | varies | Page before login page |
| `entity_type` | string | `account` | Auth/account domain |
| `component` | string | `login_sso_form_toggle_link` | Toggle link to switch back to email/password form |

---

### Page Viewed — Pricing Page

| Field | Value |
|---|---|
| **Event** | Page Viewed |
| **Area** | Navigation |
| **Type** | View |
| **Trigger** | User lands on `seekout.com/pricing/` |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Previous page. `sign_in` if arriving from login page "Get a free trial" link. |

**Notes:**
- Same Page Viewed event, different `current_page_context`. Marketing site implementation.

---

### Pricing Billing Toggle Clicked

| Field | Value |
|---|---|
| **Event** | Pricing Billing Toggle Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User toggles between "Monthly" and "Annual" billing on pricing page |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `toggle` | User toggled the billing switch |
| `action_value` | string | `monthly` or `annual` | The billing option the user switched TO |
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Page before pricing page |
| `entity_type` | string | `pricing` | Pricing domain |
| `component` | string | `pricing_billing_toggle` | Monthly/Annual toggle above plan cards |

---

### Start Free Trial Button Clicked

| Field | Value |
|---|---|
| **Event** | Start Free Trial Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks any "Start free trial" or "Get free trial" CTA on the pricing page |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the button |
| `action_value` | string | `start_free_trial` or `get_free_trial` | Exact button label in snake_case. "Start free trial" on plan card, "Get free trial" on banner. |
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Page before pricing page |
| `entity_type` | string | `pricing` | Pricing domain |
| `component` | string | `pricing_banner_free_trial_cta`, `pricing_core_plan_free_trial_button`, `pricing_nav_free_trial_button` | Which CTA was clicked. Banner = top "Take SeekOut for a test drive" banner. Core plan = button inside Core plan card. Nav = top navigation bar button. |
| `pricing_plan` | enum | `seekout_recruit_core` or `null` | `seekout_recruit_core` when clicked from plan card. `null` when clicked from banner or nav (not plan-specific). |
| `billing_cycle` | enum | `monthly`, `annual` | Which billing toggle was active when clicked |

**Notes:**
- All 3 CTAs navigate to the same destination: `seekout.com/free-trial/`.
- `component` distinguishes which CTA was used. `pricing_plan` is only set for the plan card button.

---

### Book A Demo Button Clicked

| Field | Value |
|---|---|
| **Event** | Book A Demo Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "Book a demo" under a pricing plan card |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the button |
| `action_value` | string | `book_a_demo` | Exact button label "Book a demo" in snake_case |
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Page before pricing page |
| `entity_type` | string | `pricing` | Pricing domain |
| `component` | string | `pricing_core_plan_demo_button`, `pricing_sourcing_plan_demo_button`, `pricing_sourcing_integration_plan_demo_button`, `pricing_full_funnel_plan_demo_button` | Which plan card's "Book a demo" was clicked |
| `pricing_plan` | enum | `seekout_recruit_core`, `seekout_recruit_sourcing`, `seekout_recruit_sourcing_integration`, `seekout_recruit_full_recruiting_funnel` | Which plan the user is interested in |
| `billing_cycle` | enum | `monthly`, `annual` | Which billing toggle was active when clicked |

**Notes:**
- Navigates to `seekout.com/requestdemo/` (SeekOut Recruit focused demo form).
- `pricing_plan` is the key analytical property — tells you which plan drives the most demo interest.

---

### Book One To One Demo Button Clicked

| Field | Value |
|---|---|
| **Event** | Book One To One Demo Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "Book a 1:1 demo" in the pricing page nav bar |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the button |
| `action_value` | string | `book_a_1_1_demo` | Exact button label "Book a 1:1 demo" in snake_case |
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Page before pricing page |
| `entity_type` | string | `pricing` | Pricing domain |
| `component` | string | `pricing_nav_demo_button` | "Book a 1:1 demo" button in the top navigation bar |

**Notes:**
- Navigates to `seekout.com/request-meeting/` — different destination from plan-level "Book a demo" (`seekout.com/requestdemo/`).
- The request-meeting form has a broader scope (includes SeekOut Spot and SeekOut Recruit) and a "What are you interested in?" dropdown.
- No `pricing_plan` because this is not plan-specific.

---

### See Whats Included Link Clicked

| Field | Value |
|---|---|
| **Event** | See Whats Included Link Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "See what's included" under a pricing plan card |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `click` | User clicked the link |
| `action_value` | string | `see_whats_included` | Exact link label "See what's included" in snake_case |
| `current_page_context` | string | `pricing` | Pricing page |
| `previous_page_context` | string | varies | Page before pricing page |
| `entity_type` | string | `pricing` | Pricing domain |
| `component` | string | `pricing_core_plan_included_link`, `pricing_sourcing_plan_included_link`, `pricing_sourcing_integration_plan_included_link`, `pricing_full_funnel_plan_included_link` | Which plan card's "See what's included" was clicked |
| `pricing_plan` | enum | `seekout_recruit_core`, `seekout_recruit_sourcing`, `seekout_recruit_sourcing_integration`, `seekout_recruit_full_recruiting_funnel` | Which plan the user wants to see details for |
| `billing_cycle` | enum | `monthly`, `annual` | Which billing toggle was active when clicked |

---

### Page Viewed — Free Trial Form

| Field | Value |
|---|---|
| **Event** | Page Viewed |
| **Area** | Navigation |
| **Type** | View |
| **Trigger** | User lands on `seekout.com/free-trial/` |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `free_trial` | Free trial form page |
| `previous_page_context` | string | `pricing` | User came from pricing page |

---

### Request Free Trial Button Clicked

| Field | Value |
|---|---|
| **Event** | Request Free Trial Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "Request free trial" button on the free trial form page |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `submit` | User submitted the form |
| `action_value` | string | `request_free_trial` | Exact button label "Request free trial" in snake_case |
| `current_page_context` | string | `free_trial` | Free trial form page |
| `previous_page_context` | string | `pricing` | User came from pricing page |
| `entity_type` | string | `account` | Account creation domain |
| `component` | string | `free_trial_form_submit_button` | Submit button inside the free trial signup form |

**Notes:**
- Form fields: First Name, Last Name, Business Email, Company Name, Job Title, Country.
- This is the final conversion step for trial signups originating from the pricing page.

---

### Page Viewed — Request Meeting

| Field | Value |
|---|---|
| **Event** | Page Viewed |
| **Area** | Navigation |
| **Type** | View |
| **Trigger** | User lands on `seekout.com/request-meeting/` |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `request_meeting` | Request meeting form page |
| `previous_page_context` | string | `pricing` | User came from pricing page nav |

---

### Request Meeting Button Clicked

| Field | Value |
|---|---|
| **Event** | Request Meeting Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "Request meeting" button on the request-meeting form page |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `submit` | User submitted the form |
| `action_value` | string | `request_meeting` | Exact button label "Request meeting" in snake_case |
| `current_page_context` | string | `request_meeting` | Request meeting form page |
| `previous_page_context` | string | `pricing` | User came from pricing page |
| `entity_type` | string | `meeting` | Meeting/sales domain |
| `component` | string | `request_meeting_form_submit_button` | Submit button inside the request meeting form |
| `product_interest` | enum | `recruiting_tools`, `recruiting_services`, `both` | Value selected in "What are you interested in?" dropdown |

**Notes:**
- Form fields: First Name, Last Name, Business Email, Company Name, Job Title, Phone, Country, "What are you interested in?" dropdown.

---

### Page Viewed — Request Demo

| Field | Value |
|---|---|
| **Event** | Page Viewed |
| **Area** | Navigation |
| **Type** | View |
| **Trigger** | User lands on `seekout.com/requestdemo/` |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `current_page_context` | string | `request_demo` | Request demo form page |
| `previous_page_context` | string | `pricing` | User came from pricing plan card |

---

### Book A Demo Form Button Clicked

| Field | Value |
|---|---|
| **Event** | Book A Demo Form Button Clicked |
| **Area** | Pricing |
| **Type** | Interaction |
| **Trigger** | User clicks "Book a demo" button on the request-demo form page |
| **Source** | Marketing Site |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `action` | enum | `submit` | User submitted the form |
| `action_value` | string | `book_a_demo` | Exact button label "Book a demo" in snake_case |
| `current_page_context` | string | `request_demo` | Request demo form page |
| `previous_page_context` | string | `pricing` | User came from pricing page |
| `entity_type` | string | `pricing` | Pricing/sales domain |
| `component` | string | `request_demo_form_submit_button` | Submit button inside the Recruit demo form |

**Notes:**
- SeekOut Recruit focused form — only Recruit product info shown.
- Form fields: First Name, Last Name, Business Email, Company name, Job Title, Phone, Country.

---

### Auth Login Succeeded

| Field | Value |
|---|---|
| **Event** | Auth Login Succeeded |
| **Area** | Auth |
| **Type** | Success |
| **Trigger** | Backend confirms successful authentication (email/password, SSO, or impersonation) |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `auth_method` | enum | `email`, `sso`, `impersonate` | How the user authenticated |
| `sku_id` | string | e.g., `WORKSPACES_FREE_TRIAL` | User's current plan at login time |
| `organization_id` | string | UUID | User's organization |

**Property Updates:**
- `$set: sku_id` — current plan
- `$set: organization_id` — current org
- `$set: email` — current email
- `$set: name` — current name
- `$set: company_name` — current company
- `$set: last_login_at` — login timestamp

**Notes:**
- One event for all auth methods — `auth_method` distinguishes them.
- Existing Mixpanel: `login` event via `Utils.Mixpanel.Login(req, me, type)` — stays as-is, this PostHog event fires in parallel.
- `impersonate` fires when SeekOut staff test customer accounts via `/api/auth/impersonate`.

---

### Auth Login Rejected

| Field | Value |
|---|---|
| **Event** | Auth Login Rejected |
| **Area** | Auth |
| **Type** | Rejected |
| **Trigger** | Backend returns auth error — user-caused (not technical failure) |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `auth_method` | enum | `email`, `sso` | How the user attempted to authenticate |
| `rejection_reason` | enum | `invalid_credentials`, `account_locked`, `account_not_found`, `email_not_verified` | Why the login was rejected |

**Notes:**
- Fires on the anonymous user's `distinct_id` since they haven't successfully authenticated. PostHog will merge identities if they later succeed.
- No Mixpanel equivalent — this is a new event.

---

### Auth Login Errored

| Field | Value |
|---|---|
| **Event** | Auth Login Errored |
| **Area** | Auth |
| **Type** | Error |
| **Trigger** | Technical failure during auth (database error, service timeout) — not user-caused |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `auth_method` | enum | `email`, `sso` | How the user attempted to authenticate |
| `error_category` | enum | `database`, `service_unavailable`, `internal` | Category of technical failure |
| `error_detail` | string | error message | Specific error (sanitized, no PII) |

**Notes:**
- Distinct from Auth Login Rejected — this is a system failure, not a wrong password.
- No Mixpanel equivalent — this is a new event.

---

### Trial Account Created Succeeded

| Field | Value |
|---|---|
| **Event** | Trial Account Created Succeeded |
| **Area** | Auth |
| **Type** | Success |
| **Trigger** | User clicks activation link from email, sets password, and account is created |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `sku_id` | string | `WORKSPACES_FREE_TRIAL` | Trial SKU assigned |
| `trial_duration_days` | number | `14` | Trial length |
| `organization_id` | string | UUID or `null` | Org if assigned at signup |
| `signup_source` | enum | `pricing_page`, `direct` | Where the signup originated |

**Property Updates:**
- `$set_once: trial_start_date` — when trial was activated (never overwritten)
- `$set_once: trial_sku_id` — original trial SKU (preserved after conversion to paid)
- `$set: sku_id` — current plan (`WORKSPACES_FREE_TRIAL`)
- `$set: email` — user's email
- `$set: name` — user's name
- `$set: company_name` — user's company

**Notes:**
- Fires at `POST /api/auth/register` when a free trial user activates — NOT when the form is submitted on the marketing site.
- The timeline is: form submit → Zapier → recruit-api creates NewUser record → email sent → user clicks link → **this event fires**.
- Existing Mixpanel: `signup` event via `Utils.Mixpanel.SignUp(req, me, 'email')` — stays as-is, this PostHog event fires in parallel.

---

### Trial Account Request Succeeded

| Field | Value |
|---|---|
| **Event** | Trial Account Request Succeeded |
| **Area** | Auth |
| **Type** | Success |
| **Trigger** | recruit-api accepts the trial request, creates NewUser record, and returns activation link to Zapier |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `signup_source` | enum | `pricing_page`, `direct` | Where the signup originated |

**Notes:**
- Fires at `POST /api/auth/workspace/register` after validation passes.
- This is NOT when the user activates — it confirms the backend accepted the request and created the NewUser record.
- The activation email is sent by Zapier after this event fires.

---

### Trial Account Request Rejected

| Field | Value |
|---|---|
| **Event** | Trial Account Request Rejected |
| **Area** | Auth |
| **Type** | Rejected |
| **Trigger** | recruit-api rejects the trial request during validation |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `trial_rejection_reason` | enum | `domain_limit_reached`, `email_already_exists`, `active_free_trial`, `free_trial_completed`, `active_license`, `invalid_email` | Why the trial request was rejected |
| `signup_source` | enum | `pricing_page`, `direct` | Where the signup originated |

**Notes:**
- Fires at `POST /api/auth/workspace/register` when any validation check fails.
- Maps to existing Zapier error codes: `ZAPIER_ERROR_DOMAIN_LIMIT_REACHED`, `ZAPIER_ERROR_ACTIVE_FREE_TRIAL`, etc.

---

### Trial Account Request Errored

| Field | Value |
|---|---|
| **Event** | Trial Account Request Errored |
| **Area** | Auth |
| **Type** | Error |
| **Trigger** | Technical failure while processing the trial request |
| **Source** | Backend (recruit-api) |
| **Group** | — |

| Property | Type | Values | Description |
|---|---|---|---|
| `error_category` | enum | `database`, `service_unavailable`, `internal` | Category of technical failure |
| `error_detail` | string | error message | Specific error (sanitized, no PII) |

**Notes:**
- Fires at `POST /api/auth/workspace/register` on technical failures.
- Maps to existing Zapier error code: `ZAPIER_ERROR_SERVICE_UNAVAILABLE`.

---

## New Standard Objects

| Object | Entity | Example Events |
|---|---|---|
| Page | A distinct screen/view in the app or marketing site | Page Viewed |
| Sign In Button | Email/password login submit CTA | Sign In Button Clicked |
| Sign In With SSO Link | SSO auth mode toggle | Sign In With SSO Link Clicked |
| Get A Free Trial Link | Trial signup CTA on login page | Get A Free Trial Link Clicked |
| Pricing Billing Toggle | Monthly/Annual billing switch on pricing page | Pricing Billing Toggle Clicked |
| Start Free Trial Button | Free trial CTAs on pricing page | Start Free Trial Button Clicked |
| Book A Demo Button | Plan-level demo CTAs on pricing page | Book A Demo Button Clicked |
| Book One To One Demo Button | Nav bar demo CTA on pricing page | Book One To One Demo Button Clicked |
| See Whats Included Link | Plan feature detail expanders on pricing page | See Whats Included Link Clicked |
| Request Free Trial Button | Free trial form submit CTA | Request Free Trial Button Clicked |
| Request Meeting Button | Request meeting form submit CTA | Request Meeting Button Clicked |
| Book A Demo Form Button | Request demo form submit CTA | Book A Demo Form Button Clicked |
| Auth Login | Authentication lifecycle | Auth Login Succeeded, Auth Login Rejected, Auth Login Errored |
| SSO Sign In Button | SSO form submit CTA | SSO Sign In Button Clicked |
| Sign In Without SSO Link | SSO mode toggle back to email/password | Sign In Without SSO Link Clicked |
| Trial Account Created | Trial account activation lifecycle | Trial Account Created Succeeded |
| Trial Account Request | Trial request processing lifecycle | Trial Account Request Succeeded, Trial Account Request Rejected, Trial Account Request Errored |

---

## Catalog Updates

- [ ] Page Viewed → Navigation section
- [ ] Sign In Button Clicked → Auth section
- [ ] Sign In With SSO Link Clicked → Auth section
- [ ] Get A Free Trial Link Clicked → Auth section
- [ ] Auth Login Succeeded → Auth section
- [ ] Auth Login Rejected → Auth section
- [ ] Auth Login Errored → Auth section
- [ ] SSO Sign In Button Clicked → Auth section
- [ ] Sign In Without SSO Link Clicked → Auth section
- [ ] Trial Account Created Succeeded → Auth section
- [ ] Trial Account Request Succeeded → Auth section
- [ ] Trial Account Request Rejected → Auth section
- [ ] Trial Account Request Errored → Auth section
- [ ] Pricing Billing Toggle Clicked → Pricing section
- [ ] Start Free Trial Button Clicked → Pricing section
- [ ] Book A Demo Button Clicked → Pricing section
- [ ] Book One To One Demo Button Clicked → Pricing section
- [ ] See Whats Included Link Clicked → Pricing section
- [ ] Request Free Trial Button Clicked → Pricing section
- [ ] Request Meeting Button Clicked → Pricing section
- [ ] Book A Demo Form Button Clicked → Pricing section

---

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Email/password login | Sign In Button Clicked | Auth Login Succeeded | Auth Login Rejected | Auth Login Errored |
| SSO login | SSO Sign In Button Clicked | Auth Login Succeeded | Auth Login Rejected | Auth Login Errored |
| Free trial request | Request Free Trial Button Clicked | Trial Account Request Succeeded | Trial Account Request Rejected | Trial Account Request Errored |
| Free trial activation | Trial Account Request Succeeded | Trial Account Created Succeeded | -- | -- |

---

## Metrics → Events Mapping

| Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|
| Login page traffic | Page Viewed (`current_page_context = sign_in`) | Trend | Breakdown by `entry_point` | Auth & Onboarding |
| Login method preference | Sign In Button Clicked, Sign In With SSO Link Clicked | Trend | Compare event counts over time | Auth & Onboarding |
| Login success rate | Auth Login Succeeded vs Auth Login Rejected | Trend | Breakdown by `auth_method` | Auth & Onboarding |
| Login failure reasons | Auth Login Rejected | Trend | Breakdown by `rejection_reason` | Auth & Onboarding |
| Trial interest from login page | Get A Free Trial Link Clicked | Trend | -- | Auth & Onboarding |
| First-touch attribution | Page Viewed (`entry_point`) | Funnel | Breakdown by `entry_point` | Auth & Onboarding |
| Pricing page traffic | Page Viewed (`current_page_context = pricing`) | Trend | -- | Pricing & Conversion |
| Billing cycle preference | Start Free Trial Button Clicked, Book A Demo Button Clicked | Trend | Breakdown by `billing_cycle` | Pricing & Conversion |
| Plan-level demo interest | Book A Demo Button Clicked | Trend | Breakdown by `pricing_plan` | Pricing & Conversion |
| Plan feature exploration | See Whats Included Link Clicked | Trend | Breakdown by `pricing_plan` | Pricing & Conversion |
| Trial signup conversion | Start Free Trial Button Clicked → Request Free Trial Button Clicked | Funnel | -- | Pricing & Conversion |
| Trial activation rate | Request Free Trial Button Clicked → Trial Account Created Succeeded | Funnel | -- | Pricing & Conversion |
| Demo request conversion | Book A Demo Button Clicked → Book A Demo Form Button Clicked | Funnel | Use pricing page click step for plan breakdown | Pricing & Conversion |
| Trial request acceptance rate | Trial Account Request Succeeded vs Trial Account Request Rejected | Trend | Breakdown by `trial_rejection_reason` | Pricing & Conversion |
| Users by plan | Any event | Trend | Breakdown by `sku_id` | Platform Health |

---

## Funnels

### Login Page → Successful Sign In

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context = sign_in` |
| 2 | Sign In Button Clicked | — |
| 3 | Auth Login Succeeded | `auth_method = email` |

**Purpose:** End-to-end login success rate. Drop between step 2 and 3 = failed login attempts.

### Login Page → Free Trial Activation (Full Funnel)

| Step | Event | Filter |
|---|---|---|
| 1 | Get A Free Trial Link Clicked | — |
| 2 | Page Viewed | `current_page_context = pricing` |
| 3 | Start Free Trial Button Clicked | — |
| 4 | Page Viewed | `current_page_context = free_trial` |
| 5 | Request Free Trial Button Clicked | — |
| 6 | Trial Account Request Succeeded | — |
| 7 | Trial Account Created Succeeded | — |

**Purpose:** End-to-end conversion from login page trial interest to activated account. Step 5→6 drop = form submitted but backend rejected. Step 6→7 drop = request accepted but user never clicked activation email.

### Pricing Page → Demo Request by Plan

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context = pricing` |
| 2 | Book A Demo Button Clicked | — |
| 3 | Page Viewed | `current_page_context = request_demo` |
| 4 | Book A Demo Form Button Clicked | — |

**Purpose:** Demo request conversion. Breakdown by `pricing_plan` to see which plans drive the most demo requests.

---

## Implementation Notes

### Free Trial Signup Architecture

The free trial form on `seekout.com/free-trial/` does not call recruit-api directly. The flow uses Zapier as a secure middleman:

```
seekout.com/free-trial/             Zapier                    recruit-api
┌───────────────────────┐      ┌──────────────┐      ┌─────────────────────────┐
│ User fills form,      │      │              │      │ POST /api/auth/         │
│ clicks "Request       │─────▶│  Webhook     │─────▶│ workspace/register      │
│ free trial"           │      │              │ API  │                         │
│                       │      │              │ key  │ • Validates email        │
│ Marketing site form   │      │              │      │ • Checks domain limit   │
│ (HubSpot or similar)  │      │              │      │ • Creates NewUser record │
└───────────────────────┘      └──────┬───────┘      │ • Returns activation    │
                                      │              │   link + shortId        │
                                      │◀─────────────┘                         │
                                      │                                        │
                                ┌─────▼────────┐                               │
                                │ Sends email  │                               │
                                │ to user with │                               │
                                │ activation   │                               │
                                │ link         │                               │
                                └─────┬────────┘                               │
                                      │                                        │
                                ┌─────▼──────────────────────┐                 │
                                │ User clicks link:          │                 │
                                │ seekout.com/completeSignUp  │                 │
                                │ ?code={shortId}            │                 │
                                └─────┬──────────────────────┘                 │
                                      │                                        │
                                ┌─────▼──────────────────────┐                 │
                                │ POST /api/auth/register    │◀────────────────┘
                                │ • Sets password            │
                                │ • Creates full account     │
                                │ • Logs user in             │
                                │ • SKU: workspaces-free-trial│
                                │                            │
                                │ ★ PostHog: Trial Account   │
                                │   Created Succeeded fires  │
                                │   HERE                     │
                                └────────────────────────────┘
```

**Why Zapier is in the middle:**
- The marketing site form is public — it cannot hold the recruit-api server API key securely
- Zapier holds the API key and acts as a secure bridge between the marketing site and recruit-api
- Zapier also handles sending the activation email (recruit-api doesn't send emails in this flow)
- Zapier can trigger other downstream actions (Salesforce lead, Slack notification, etc.)

### Backend Data Pipeline: `trial_signups` Table

**Problem:** The current NewUser records in CosmosDB have a 60-day TTL and auto-delete. Users who request a trial but never activate disappear entirely — no way to measure trial request → activation rate after 60 days.

**Solution:** Add a permanent `trial_signups` table alongside the existing NewUser record. The NewUser record keeps its TTL for the activation flow. The `trial_signups` table is permanent and provides analytics.

**Table schema:**

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `first_name` | string | From form |
| `last_name` | string | From form |
| `business_email` | string | From form |
| `company_name` | string | From form |
| `job_title` | string | From form |
| `country` | string | From form |
| `email_domain` | string | Extracted from business_email — for domain-level analysis |
| `sku_id` | string | Trial SKU (`workspaces-free-trial`) |
| `activation_status` | enum | `pending` → `activated` → `expired` |
| `requested_at` | timestamp | When the trial was requested |
| `activated_at` | timestamp | When the user activated (clicked link + set password). `null` if not activated. |
| `activation_link_expires_at` | timestamp | `requested_at` + 60 days |
| `trial_start_date` | timestamp | Same as `activated_at` — trial starts when they activate |
| `trial_end_date` | timestamp | `activated_at` + 14 days. `null` if not activated. |
| `converted_to_paid` | boolean | Whether user converted to a paid plan |
| `converted_at` | timestamp | When user converted. `null` if not converted. |
| `paid_sku_id` | string | Paid plan SKU after conversion. `null` if not converted. |
| `user_id` | UUID | recruit-api user ID. `null` until activation. |
| `rejection_reason` | string | If request was rejected (domain limit, email exists). `null` if accepted. |
| `created_at` | timestamp | Row creation time |

**Where to write:**
- **On trial request** (`POST /api/auth/workspace/register`): Insert row with `activation_status: pending`
- **On activation** (`POST /api/auth/register` with free trial shortId): Update to `activation_status: activated`, set `activated_at`, `trial_start_date`, `trial_end_date`, `user_id`
- **On plan conversion** (SKU change from trial to paid): Update `converted_to_paid`, `converted_at`, `paid_sku_id`

**Key analytics this unlocks:**

| Question | Query |
|---|---|
| Trial request → activation rate | `COUNT(activated) / COUNT(*)` |
| Time to activate after requesting | `AVG(activated_at - requested_at)` |
| Companies that requested but never activated | `WHERE activation_status IN ('pending', 'expired')` |
| Trial → paid conversion rate | `COUNT(converted_to_paid = true) / COUNT(activated)` |
| Time from activation to paid conversion | `AVG(converted_at - activated_at)` |

### Cross-Site Identity Handoff

> **⚠️ Requires engineering review before implementation.** The approach below is a design proposal. Two specific concerns need eng validation: (1) passing `distinct_id` in URLs can leak via `Referer` headers if the user navigates to a third-party site, and (2) the correct PostHog SDK method for linking two anonymous sessions across domains may be `posthog.alias()` rather than `posthog.identify()` — `identify()` is intended for linking anonymous sessions to known user IDs, while `alias()` links two anonymous IDs without needing to know who the person is. Eng should evaluate PostHog's cross-domain stitching options and recommend the safest approach.

**Problem:** When a user clicks "Get a free trial" on `app.seekout.io/signIn` and navigates to `seekout.com/pricing/`, PostHog on each site assigns a separate anonymous ID. Without an explicit handoff, PostHog treats them as two different users and cross-site funnels break.

**Proposed solution:** Append the PostHog `distinct_id` as a URL parameter when navigating cross-site.

**Where to implement:**
- **Login page → Pricing page:** When `Get A Free Trial Link Clicked` fires, the link should include `?ph_id={posthog.get_distinct_id()}`. Example: `seekout.com/pricing/?ph_id=abc123`.
- **Marketing site pages:** On page load, read `ph_id` from URL params and call `posthog.alias(ph_id)` to link the anonymous marketing site session to the app session. *(Eng to confirm: `alias()` vs `identify()` vs PostHog's native cross-domain config.)*
- **Zapier → recruit-api:** Pass the `ph_id` from the form submission through to the `POST /api/auth/workspace/register` request, so the activation link can include it: `seekout.com/completeSignUp?code={shortId}&ph_id={ph_id}`.
- **Activation page:** On the completeSignUp page, read `ph_id` and call the appropriate PostHog linking method before firing any events.

**User-visible change:** A query parameter (`?ph_id=abc123`) is added to cross-site URLs. This is standard analytics practice and has no visual impact on the page.

**Privacy consideration:** The `ph_id` value in the URL is a PostHog anonymous ID (not PII), but it can leak via browser `Referer` headers if the user navigates to external sites from the marketing page. Eng should assess whether this is acceptable or if an alternative mechanism (e.g., first-party cookie sharing, PostHog's built-in cross-domain linking) is preferable.
