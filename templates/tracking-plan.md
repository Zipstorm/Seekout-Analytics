# Tracking Plan: [Feature Name]

**Product:** <product>
**Feature:** [Feature area]  
**Date:** [Date]  
**Related PRD:** [Link to PRD]

> References: `docs/shared/naming-and-event-types.md`, `docs/<product>/event-schema.md`, and `docs/<product>/event-catalog.md`.

---

## Metrics → Events Mapping

Map each PRD success metric to PostHog events.

| Success Metric | Target | PostHog Event(s) | Insight Type | Dashboard |
|---|---|---|---|---|
| [Metric from PRD] | [Target value] | [Event Name] | funnel / trend / retention / path | [Dashboard name] |

---

## New Events

Events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Type | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| [Object Action] | [Product area] | View / Interaction / Started / Success / Rejected / Error | [When this fires] | `property_1`, `property_2` | [group type] / -- | `$set_once: prop`, `group(<group>): prop` / -- |

<!--
## New Standard Objects

Use this section when new events introduce an object that is not yet in
docs/<product>/event-schema.md. Rows use the same shape as the schema table so
/merge-tracking-plan can append them directly.

| Object | Entity | Example Events |
|---|---|---|
| [Object Name] | [Entity represented] | [Object Action], [Object Action] |

## Removed Standard Objects

Use this section when this tracking plan removes or replaces an existing
Standard Object. Reason is optional reviewer context.

| Object | Reason |
|---|---|
| [Object Name] | [Why it is removed or replaced] |
-->

---

## Interaction / Started / Result Pattern

For critical user flows, track the UI interaction or process start separately from the processed result.

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| [User flow] | [Button Clicked or Flow Started] | [Object Action Succeeded] | [Object Action Rejected] | [Object Action Errored] / -- |

---

## Funnels

Multi-step conversion flows to track.

| Funnel Name | Steps | Purpose |
|---|---|---|
| [Name] | Step 1 → Step 2 → Step 3 | [What this measures] |

---

## Property Details

Detailed property definitions for new events.

| Property | Type | Values | Description |
|---|---|---|---|
| `property_name` | string / enum / number / boolean | [Possible values] | [What this captures] |

---

## Catalog Updates

New events from this plan to add to `docs/<product>/event-catalog.md`:

- [ ] [Event Name] → [Catalog section: product-specific section]
- [ ] New object added to Standard Objects table: [Yes / No]
