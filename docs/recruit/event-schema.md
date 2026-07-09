---
analytics_platform: posthog
allow_empty_catalog: true
---

# Recruit Analytics Events Schema

**Product:** Recruit
**Analytics Platform:** PostHog
**Last Updated:** June 2026

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

### `$set` — Updated on every login

| Property | Type | Set By | Description |
|----------|------|--------|-------------|

## Standard Event Properties

| Property | Type | Required For | When to Include |
|----------|------|--------------|-----------------|

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|------|-----------------------------|---------------|----------------|-------------|
