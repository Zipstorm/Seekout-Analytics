# Recruit Backlog

Known issues, deferred events, and future fixes for Recruit analytics.

---

## Events Moved to Tracking Plan

The following events were originally deferred here but are now included in `tracking-plans/recruit/recruit-onboarding-v1.md`. Frontend events will be implemented first, backend events will follow — both are part of the same tracking plan.

| Event | Status | Tracking Plan |
|---|---|---|
| Auth Login Succeeded | In tracking plan | [recruit-onboarding-v1.md](../../tracking-plans/recruit/recruit-onboarding-v1.md) |
| Auth Login Rejected | In tracking plan | Same |
| Auth Login Errored | In tracking plan | Same |
| SSO Sign In Button Clicked | In tracking plan | Same |
| Sign In Without SSO Link Clicked | In tracking plan | Same |
| Trial Account Created Succeeded | In tracking plan | Same |
| Trial Account Request Succeeded | In tracking plan | Same |
| Trial Account Request Rejected | In tracking plan | Same |
| Trial Account Request Errored | In tracking plan | Same |

`auth_method` values in the tracking plan: `email`, `sso`, `impersonate`. Microsoft and Google OAuth are not tracked at this stage.

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

**Requirement:** Store all free trial form submissions in a backend table for reference, independent of analytics events. This provides a queryable record of trial signups with timeline data. Full table schema and write points are documented in [recruit-onboarding-v1.md](../../tracking-plans/recruit/recruit-onboarding-v1.md) under Implementation Notes.

### Current problem: NewUser records auto-delete

The current `POST /api/auth/workspace/register` endpoint in recruit-api creates a NewUser record in CosmosDB with a **60-day TTL**. After 60 days, CosmosDB automatically deletes the record. This means:
- Users who requested a trial but never activated disappear from the database entirely
- No way to measure trial request → activation rate after 60 days
- No permanent record of who requested a trial, when, or from which company

### Recommended fix: Permanent `trial_signups` table

See the tracking plan's Implementation Notes for the full table schema, write points, and analytics unlocked. The `trial_signups` table sits alongside the existing NewUser record — the NewUser record keeps its TTL for the activation flow, the table is permanent for analytics and audit.

### Plan Change Timeline (Event-Level `sku_id`)

Every event should carry `sku_id` as a standard property so the user's plan at the time of any action is permanently recorded. PostHog stores event properties immutably — even if the person's `sku_id` changes later, each historical event retains the `sku_id` it was sent with. This gives you a timeline without needing a separate table.

Example timeline from events:
```
2026-07-09  Page Viewed          sku_id: "WORKSPACES_FREE_TRIAL"   ← user on trial
2026-07-15  Search Executed      sku_id: "WORKSPACES_FREE_TRIAL"   ← still on trial
2026-07-23  Page Viewed          sku_id: "RECRUIT_CORE_ANNUAL"     ← converted to paid
```
