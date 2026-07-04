# Tracking Plan: [Feature Name]

**Product:** <product>
**Feature:** [Feature area]
**Date:** [Date]
**Related PRD:** [Link to PRD]
**Repo:** —
**Branch:** —
**PR:** —

- [ ] Draft created
- [ ] Validated
- [ ] Codebase implemented
- [ ] Absorbed from codebase
- [ ] Re-validated
- [ ] PR raised
- [ ] PR approved
- [ ] Merged to catalog
- [ ] Squash merged to main

> References: `docs/shared/naming-and-event-types.md`, `docs/<product>/event-schema.md`, and `docs/<product>/event-catalog.md`.

---

## New Events Summary

Overview of all events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| [Object Action] | [Catalog section] | View / Interaction / Started / Success / Rejected / Error | Frontend / Backend | [When this fires] | [Business context — persona, page, what happens when user takes this action] | `prop_1`, `prop_2` | [group type] / -- | `$set_once: prop`, `group(<group>): prop` / -- | Local / Dev / Prod |

---

## Property Details

Detailed property definitions for new events. Properties shared across multiple events are listed once.

| Property | Type | Values | Description |
|---|---|---|---|
| `property_name` | string / enum / number / boolean | [Possible values] | [What this captures] |

---

## Event Specifications

Detailed per-event specs. Initially filled during event design (from screenshots / PRD). Updated in-place after codebase absorption to reflect actuals.

### [Event Name]

| Field | Value |
|---|---|
| **Event** | [Object Action] |
| **Area** | [Catalog section] |
| **Type** | View / Interaction / Started / Success / Rejected / Error |
| **Trigger** | [When this fires] |
| **Source** | Frontend / Backend |
| **Group** | [group type] / — |

| Property | Type | Values | Description |
|---|---|---|---|
| `property_name` | type | [Possible values] | [What this captures] |

---

<!--
## New Standard Objects

Use this section when new events introduce an object that is not yet in
docs/<product>/event-schema.md. Rows use the same shape as the schema table so
/merge-tracking-plan can append them directly.

| Object | Entity | Example Events |
|---|---|---|
| [Object Name] | [Entity represented] | [Object Action], [Object Action] |
-->

---

## Catalog Updates

New events from this plan to add to `docs/<product>/event-catalog.md`:

- [ ] [Event Name] → [Catalog section]
- [ ] New object added to Standard Objects table: [Yes / No]
- [ ] Removed object: [Object Name] — [Reason]

---

## Interaction / Started / Result Pattern

For critical user flows, track the UI interaction or process start separately from the processed result. Each row is one flow with its possible outcomes.

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| [User flow] | [Button Clicked or Flow Started] | [Object Action Succeeded] | [Object Action Rejected] | [Object Action Errored] / -- |

---

## Metrics → Events Mapping

Map events back to success metrics. Fill after events are designed.

| Success Metric | PostHog Event(s) | Insight Type | Breakdown / Filter | Dashboard |
|---|---|---|---|---|
| [What you're measuring] | [Event Name] | funnel / trend / retention / path | [Filters] | [Dashboard name] |

---

## Funnels

Multi-step conversion flows to track. Fill after events are absorbed from the codebase.

| Funnel Name | Steps | Purpose |
|---|---|---|
| [Name] | Step 1 → Step 2 → Step 3 | [What this measures] |
