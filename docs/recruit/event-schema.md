---
analytics_platform: posthog
allow_empty_catalog: true
---

# Recruit Analytics Events Schema

**Product:** Recruit
**Analytics Platform:** PostHog
**Last Updated:** July 2026

For shared naming conventions and event types, see [Shared Analytics Naming and Event Types](../shared/naming-and-event-types.md).
For the event catalog and implementation status, see [Recruit Analytics Events Tracker](./event-catalog.md).
For dashboards and funnel mappings, see [Recruit Analytics Dashboards & Funnels](./dashboards.md).

---

## Shared Naming Conventions and Event Types

Naming conventions, property-name casing, and the Event Types enum are shared across products in [Shared Analytics Naming and Event Types](../shared/naming-and-event-types.md). The validator reads the shared Event Types table for Rule 17 / TP12.

## Standard Objects

Add product-specific Standard Objects before introducing events that use them.

| Object | Entity | Example Events |
|--------|--------|----------------|

## Person Properties

### `$set_once` — Immutable, set once per user

| Property | Type | Values | Set By | Description |
|----------|------|--------|--------|-------------|
| `entry_point` | string | `direct`, `email_invite`, `share_link`, `sso_redirect` | Page Viewed (login page) | First-touch attribution — how user originally found Recruit. Derived from `?context=` URL param. |
| `first_referrer` | string | URL or `null` | Page Viewed (login page) | HTTP referrer at first visit (`document.referrer`). |
| `first_landing_url` | string | URL | Page Viewed (login page) | Full landing URL including query params at first visit. |
| `trial_start_date` | ISO date | | Trial Account Created Succeeded | When the free trial was provisioned. Never overwritten. |
| `trial_sku_id` | string | e.g., `WORKSPACES_FREE_TRIAL` | Trial Account Created Succeeded | Original trial SKU. Preserved even after user converts to paid plan. |

### `$set` — Updated on every login or plan change

| Property | Type | Set By | Description |
|----------|------|--------|-------------|
| `email` | string | `identifyUser()` | User's current email |
| `name` | string | `identifyUser()` | User's current name |
| `organization_id` | string | `identifyUser()` | User's current organization ID |
| `sku_id` | string | `identifyUser()`, Plan Changed | User's current plan/SKU. Updated on login and plan changes. |
| `company_name` | string | `identifyUser()` | User's company name |
| `last_login_at` | ISO date | Auth Login Succeeded | Last successful login timestamp |

## Standard Event Properties

| Property | Type | Required For | When to Include |
|----------|------|--------------|-----------------|
| `current_page_context` | string | All frontend events | Always — identifies the page where the event fired |
| `previous_page_context` | string | All frontend events | Always — page the user was on before. `null` if direct entry. |
| `sku_id` | string | All post-auth events | Every event after the user is authenticated. Captures the user's plan at the time of the event. Pre-auth events (login page, marketing site) don't have this. |
| `action` | enum (`click`, `submit`, `toggle`) | All Interaction events | What the user did |
| `action_value` | string | All Interaction events | Exact UI label of the clicked element, in snake_case. Never paraphrased. |
| `entity_type` | string | All Interaction events | Domain the action relates to (e.g., `account`, `pricing`, `workspace`, `search`) |
| `component` | string | All Interaction events | Exact page location of the UI element. Specific enough to locate without seeing the screen. |

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|------|-----------------------------|---------------|----------------|-------------|
