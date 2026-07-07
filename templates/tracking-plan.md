# Tracking Plan: [Feature Name]

**Product:** <product>
**Feature:** [Feature area]
**Date:** [Date]
**Related PRD:** [Link to PRD]
**Repo:** —
**Branch:** —
**PR:** —
**Status:** Draft

## Status History

| Status | Date | Trigger |
|---|---|---|
| Draft | [Date] | Plan created |

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

> References: `docs/shared/naming-and-event-types.md`, `docs/<product>/event-schema.md`, and `docs/<product>/event-catalog.md`.

---

<!--
## Scope

Use this section when the plan touches existing events (renames, removals, property
fixes) in addition to — or instead of — new events. Summarize the plan's full
scope so reviewers can see the blast radius at a glance. Skip for simple
new-events-only plans.

1. **Adds N new events** — [brief description]
2. **Renames N events** — [naming rule being applied]
3. **Removes N events** — [reason: dead code, superseded, etc.]
4. **Fixes properties on N events** — [what kind of fixes]
5. **Extends [Event Name] to N new pages** — [which pages]

### Supersedes

This plan supersedes `tracking-plans/<product>/[old-plan].md` (status: [status],
[date], [reason it was never completed]). That plan should be archived after this
one is merged.
-->

---

## New Events Summary

Overview of all events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| [Object Action] | [Catalog section] | View / Interaction / Started / Success / Rejected / Error | Frontend / Backend | [When this fires] | [Business context — persona, page, what happens when user takes this action] | `prop_1`, `prop_2` | [group type] / -- | `$set_once: prop`, `group(<group>): prop` / -- | Local / Dev / Prod |

---

## Property Details

Detailed property definitions for new or modified events. Properties shared across multiple events are listed once.

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
## Event Renames

Use this section when existing events need renaming to comply with naming rules
from `docs/shared/naming-and-event-types.md`. Organize by terminal type so
reviewers can verify the naming rule applied to each rename.

### Success Events — Must End "Succeeded"

| Current Name | New Name | Type | Constant |
|---|---|---|---|
| [Old Name] | [New Name] | Success | `OLD_CONSTANT` → `NEW_CONSTANT` |

### Rejected Events — Must End "Rejected"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| [Old Name] | [New Name] | Rejected | [Why Rejected not Errored] |

### Error Events — Must End "Errored"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| [Old Name] | [New Name] | Error | [Why Errored not Rejected] |
-->

---

<!--
## Removed Events

Events removed by this plan. Includes old names from renames (replaced by new
name) and events being deleted entirely (dead code, superseded, never wired).

| Event | Reason | Replaced By |
|---|---|---|
| [Old Event Name] | Renamed / Dead code / Superseded / Never wired | [New Event Name] / — |
-->

---

<!--
## Existing Event Updates

Use this section when the plan modifies existing catalog events without renaming
them. Covers: extending events to new pages, fixing triggers or properties,
adding new properties (like `mode`), moving `$set_once` attribution, etc.

Each sub-section is optional — include only what applies.

### Page Viewed Extensions

Pages that currently do not fire Page Viewed. This plan adds Page Viewed to each.

| Page | Route | `current_page_context` value | Notes |
|---|---|---|---|
| [Page name] | [/route] | [value] | [Conditions, e.g. "skipped for OAuth"] |

### Existing Event Property Extensions

Existing catalog events that gain new properties (e.g., `mode` for
onboarding/post-onboarding distinction) or get wired to additional pages.

| Event | Change | New Properties | Notes |
|---|---|---|---|
| [Event Name] | Wired on [Page] / Added `mode` / etc. | `prop_1`, `prop_2` | [Context] |

### Existing Event Fixes

Production fixes, trigger changes, or `$set_once` attribution moves on existing events.

| Event | Change | Detail |
|---|---|---|
| [Event Name] | Trigger fix / `$set_once` move / property value rename | [What changed and why] |

### Property Fixes on Existing Events

Property additions, removals, or renames on existing events.

#### Properties to Remove

| Event | Property | Reason |
|---|---|---|
| [Event Name] | `property` | [Why removing] |

#### Properties to Rename

| Event | Current Property | New Property | Reason |
|---|---|---|---|
| [Event Name] | `old_prop` | `new_prop` | [Why renaming] |

#### Properties to Add

| Event | Property | Type | Values | Reason |
|---|---|---|---|---|
| [Event Name] | `prop` | type | [values] | [Why adding] |
-->

---

## New Standard Objects

Use this section when new events introduce an object that is not yet in
docs/<product>/event-schema.md. Rows use the same shape as the schema table so
/merge-tracking-plan can append them directly.

| Object | Entity | Example Events |
|---|---|---|
| [Object Name] | [Entity represented] | [Object Action], [Object Action] |

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

### [Funnel Name]

| Step | Event | Filter |
|---|---|---|
| 1 | [Event Name] | [Property filter or —] |
| 2 | [Event Name] | [Property filter or —] |
| 3 | [Event Name] | [Property filter or —] |

**Purpose:** [What this funnel measures]

<!--
## Implementation Notes

Use this section for developer-facing guidance when the plan has non-obvious
implementation requirements: cross-repo coordination, sessionStorage state,
SDK integration points, migration batching strategy, etc. Skip for plans
where the Event Specifications are sufficient for implementation.

### [Topic]

[Implementation detail]
-->
