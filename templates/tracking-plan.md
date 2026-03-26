# Tracking Plan: [Feature Name]

**Product:** Helix (SeekOut.ai)  
**Feature:** [Feature area]  
**Date:** [Date]  
**Related PRD:** [Link to PRD]

> Reference: `docs/event-catalog.md` for naming conventions and existing event catalog.

---

## Metrics → Events Mapping

Map each PRD success metric to PostHog events.

| Success Metric | Target | PostHog Event(s) | Insight Type | Dashboard |
|---|---|---|---|---|
| [Metric from PRD] | [Target value] | [Event Name] | funnel / trend / retention / path | [Dashboard name] |

---

## New Events

Events introduced by this feature. All follow Object-Action, Proper Case.

| Event | Area | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|
| [Object Action] | Account / Prospect / Hiring / Viral Loop | [When this fires] | `property_1`, `property_2` | `job` / -- | `$set_once: prop`, `group(job): prop` / -- |

---

## Intent vs Outcome

For critical user flows, track both the UI interaction and server-confirmed result.

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| [User action] | [Button Clicked] | [Object Actioned] | [Object Action Failed] |

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

New events from this plan to add to `docs/event-catalog.md`:

- [ ] [Event Name] → [Catalog section: Account / Prospect / Hiring / Viral Loop]
- [ ] New object added to Standard Objects table: [Yes / No]
