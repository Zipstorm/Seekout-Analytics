# Recruit Backlog

Known issues, deferred events, and future fixes for Recruit analytics.

---

## Deferred Events — Auth Lifecycle (Backend)

These events complete the Interaction → Result pattern for login/auth flows. They are backend events (fired from recruit-api after the server processes the auth request) and should be implemented alongside the frontend interaction events.

| Event | Type | Source | Trigger | Why Deferred |
|---|---|---|---|---|
| Auth Login Succeeded | Success | Backend (recruit-api) | Backend confirms successful email/password or SSO login | Backend event — requires PostHog SDK setup in recruit-api. Currently tracked as Mixpanel `login` event in `Utils.Mixpanel.Login()`. |
| Auth Login Rejected | Rejected | Backend (recruit-api) | Backend returns auth error (wrong password, account locked, etc.) | Same — backend event. No equivalent exists in current Mixpanel tracking. |
| Auth Login Errored | Error | Backend (recruit-api) | Technical failure during auth (database error, service timeout) | Same — backend event. |
| SSO Auth Redirect Started | Started | Frontend (recruit-ui) | User enters email on SSO form and submits → redirects to SAML/SSO provider | Frontend event but depends on SSO form mode toggle (Sign In With SSO Link Clicked). Requires understanding the full SSO redirect flow. |
| Trial Account Created Succeeded | Success | Backend (recruit-api or marketing site backend) | Free trial account is successfully provisioned after "Request free trial" form submit | Cross-system event. Form is on marketing site, account creation may happen in recruit-api. Needs engineering clarity on which backend handles trial provisioning. |
| Trial Account Created Rejected | Rejected | Backend | Trial request rejected (domain limit reached, email already exists, etc.) | Same — depends on trial provisioning backend. |

### Context

The frontend interaction events (Sign In Button Clicked, Sign In With SSO Link Clicked) are in the onboarding tracking plan. These backend result events complete the funnel:

- **Email login:** Sign In Button Clicked → Auth Login Succeeded / Auth Login Rejected / Auth Login Errored
- **SSO login:** Sign In With SSO Link Clicked → SSO Auth Redirect Started → Auth Login Succeeded / Auth Login Rejected
- **Free trial:** Request Free Trial Button Clicked → Trial Account Created Succeeded / Trial Account Created Rejected

### Expected Properties (when implemented)

**Auth Login Succeeded:**
| Property | Type | Description |
|---|---|---|
| `auth_method` | enum (`email`, `sso`, `microsoft`, `google`) | How the user authenticated |
| `sku_id` | string | User's current plan/SKU at login time |
| `organization_id` | string | User's organization |
| `$set: sku_id` | string | Update person property with current SKU |
| `$set: organization_id` | string | Update person property with current org |
| `$set: last_login_at` | ISO date | Last login timestamp |

**Auth Login Rejected:**
| Property | Type | Description |
|---|---|---|
| `auth_method` | enum | How the user attempted to authenticate |
| `rejection_reason` | enum (`invalid_credentials`, `account_locked`, `account_not_found`, `email_not_verified`) | Why the login was rejected |

**Trial Account Created Succeeded:**
| Property | Type | Description |
|---|---|---|
| `sku_id` | string | Trial SKU assigned (e.g., `WORKSPACES_FREE_TRIAL`) |
| `trial_duration_days` | number | Trial length (currently 14 days) |
| `$set_once: trial_start_date` | ISO date | When the trial started |
| `$set_once: trial_sku_id` | string | Original trial SKU (never overwritten) |
| `$set: sku_id` | string | Current SKU |

---

## Deferred Events — Login Page (Frontend)

| Event | Type | Source | Trigger | Why Deferred |
|---|---|---|---|---|
| Forgot Your Password Link Clicked | Interaction | Frontend (recruit-ui) | User clicks "Forgot your password?" on login page | Low priority — tracks password reset intent. Add when password reset flow is documented. |

---

## Deferred Events — Pricing Page (Marketing Site)

| Event | Type | Source | Trigger | Why Deferred |
|---|---|---|---|---|
| See Monthly Pricing Link Clicked | Interaction | Marketing Site | User clicks "See monthly pricing" on the Core plan card | Low priority — minor pricing exploration signal. |

---

## Backend Data Requirements

### Free Trial Signup Data Table

**Requirement:** Store all free trial form submissions in a backend table for reference, independent of analytics events. This provides a queryable record of trial signups with timeline data.

### Current problem: NewUser records auto-delete

The current `POST /api/auth/workspace/register` endpoint in recruit-api creates a NewUser record in CosmosDB with a **60-day TTL**. After 60 days, CosmosDB automatically deletes the record. This means:
- Users who requested a trial but never activated disappear from the database entirely
- No way to measure trial request → activation rate after 60 days
- No permanent record of who requested a trial, when, or from which company

### Recommended fix: Permanent `trial_signups` table

Add a write to a permanent table inside the `POST /api/auth/workspace/register` endpoint (alongside the existing NewUser record). The NewUser record can keep its TTL for the activation flow — this table is purely for analytics and audit.

**Suggested table: `trial_signups`**

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `first_name` | string | From form |
| `last_name` | string | From form |
| `business_email` | string | From form |
| `company_name` | string | From form |
| `job_title` | string | From form |
| `country` | string | From form |
| `email_domain` | string | Extracted from business_email — useful for domain-level analysis |
| `sku_id` | string | Trial SKU assigned (`workspaces-free-trial`) |
| `activation_status` | enum | `pending` → `activated` → `expired`. Updated when user activates (clicks link + sets password) or when 60 days pass without activation. |
| `requested_at` | timestamp | When the trial was requested (form submit time) |
| `activated_at` | timestamp | When the user activated (clicked link + set password). `null` if not yet activated. |
| `activation_link_expires_at` | timestamp | `requested_at` + 60 days. When the activation link expires. |
| `trial_start_date` | timestamp | Same as `activated_at` — trial clock starts when they activate, not when they request. |
| `trial_end_date` | timestamp | `activated_at` + 14 days. `null` if not activated. |
| `converted_to_paid` | boolean | Whether user converted to a paid plan. Default `false`. |
| `converted_at` | timestamp | When user converted. `null` if not converted. |
| `paid_sku_id` | string | Paid plan SKU after conversion. `null` if not converted. |
| `user_id` | UUID | recruit-api user ID. `null` until activation (user record doesn't exist until they activate). |
| `rejection_reason` | string | If the request was rejected (domain limit, email exists, etc.). `null` if accepted. |
| `created_at` | timestamp | Row creation time |

**Where to write:**
- **On trial request** (inside `POST /api/auth/workspace/register`): Create row with `activation_status: pending` (or `rejected` if validation fails).
- **On activation** (inside `POST /api/auth/register` when `shortId` matches a free trial): Update row to `activation_status: activated`, set `activated_at`, `trial_start_date`, `trial_end_date`, `user_id`.
- **On plan conversion** (when SKU changes from `workspaces-free-trial` to a paid SKU): Update `converted_to_paid`, `converted_at`, `paid_sku_id`.

**Analytics this unlocks:**

| Question | How to Answer |
|---|---|
| How many people requested a trial this month? | `COUNT(*) WHERE requested_at IN month` |
| What % of trial requests actually activate? | `COUNT(activated) / COUNT(*)` |
| How long does it take to activate after requesting? | `AVG(activated_at - requested_at)` |
| Which companies requested trials but never activated? | `WHERE activation_status = 'pending' OR 'expired'` |
| What % of activated trials convert to paid? | `COUNT(converted_to_paid = true) / COUNT(activated)` |
| How long from activation to paid conversion? | `AVG(converted_at - activated_at)` |
| Which domains hit the 10-user domain limit? | `GROUP BY email_domain WHERE rejection_reason = 'domain_limit_reached'` |

### How the free trial flow actually works (for context)

```
Marketing site form (seekout.com/free-trial/)
    ↓ form submit
Zapier webhook (middleman — has the server API key)
    ↓ POST /api/auth/workspace/register
recruit-api
    ├── Validates email, domain limits, existing accounts
    ├── Creates NewUser record in CosmosDB (60-day TTL)
    ├── ★ PROPOSED: Also writes to trial_signups table (permanent)
    ├── Returns activation link to Zapier
    ↓
Zapier sends activation email to user
    ↓ user clicks link
seekout.com/completeSignUp?code={shortId}
    ↓ user sets password
POST /api/auth/register (creates full account, logs user in)
    ├── ★ PROPOSED: Updates trial_signups row (activated_at, user_id)
    ├── Fires Mixpanel signup event (existing, stays)
    └── ★ PROPOSED: Fires PostHog Trial Account Created Succeeded (new)
```

**Note on HubSpot:** The recruit-api codebase has HubSpot integration code (portal ID, form ID, API key) but the actual call is **commented out**. HubSpot may host the marketing form itself and trigger the Zapier webhook — but this happens outside the recruit-api codebase.

**Why this matters for analytics:**
- PostHog person properties ($set) only store the current value — if `sku_id` changes from trial to paid, you lose the trial history
- This table preserves the full timeline: trial request → activation → paid conversion (or churn)
- Can be joined with PostHog data via `user_id` or `business_email` for combined analysis

### Plan Change Timeline (Event-Level `sku_id`)

Every event should carry `sku_id` as a standard property so the user's plan at the time of any action is permanently recorded. PostHog stores event properties immutably — even if the person's `sku_id` changes later, each historical event retains the `sku_id` it was sent with. This gives you a timeline without needing a separate table.

Example timeline from events:
```
2026-07-09  Page Viewed          sku_id: "WORKSPACES_FREE_TRIAL"   ← user on trial
2026-07-15  Search Executed      sku_id: "WORKSPACES_FREE_TRIAL"   ← still on trial
2026-07-23  Page Viewed          sku_id: "RECRUIT_CORE_ANNUAL"     ← converted to paid
```
