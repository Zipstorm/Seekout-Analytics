# SeekOut Analytics

Analytics instrumentation, event taxonomy, metric frameworks, and dashboards for Helix (SeekOut.ai).

## Repository Structure

- `docs/` — Source-of-truth analytics documents (event catalog, schema, dashboards, metrics)
- `context/` — Product context dependencies (entity model, network model, product overview)
- `tracking-plans/` — Per-feature tracking plans (working documents). `INDEX.md` tracks PRD links and status. `archived/` holds completed plans.
- `plans/` — Design docs for PRs with follow-up status tracking. Update statuses as follow-ups are completed.
- `scripts/` — Validation tooling
- `templates/` — Reusable templates
- `logs/` — Validator run history

## Source of Truth

The 3 canonical analytics documents live in `docs/`:

1. **`event-catalog.md`** — Master event taxonomy, property dictionary, implementation status. This is THE source of truth for all Helix analytics events.
2. **`event-schema.md`** — Naming conventions, standard objects, PostHog config, sample code.
3. **`dashboards.md`** — Dashboard specs, funnel definitions, platform health flows.

Supporting metric framework docs (also in `docs/`):
- `viral-loop-metrics.md` — 4 viral loops with K-factor decomposition
- `network-quantification.md` — Network health metrics (Helix Size, Liquidity, Activation, Bridging)
- `tiered-metric-diagrams.md` — 3-tier metric hierarchy with Mermaid diagrams

## Context-First Rule

Before generating any analytics document, read:
1. `context/product-overview.md` — Product vision, personas, surfaces
2. `docs/event-schema.md` — Naming conventions and standard objects
3. `docs/event-catalog.md` — Existing events and property dictionary

## Tracking Plan Workflow

1. User provides feature context (PRD excerpt, spec, or description)
2. Generate tracking plan using `templates/tracking-plan.md`
3. Save to `tracking-plans/[feature-name].md`
4. Add entry to `tracking-plans/INDEX.md` with PRD link and status **Draft**
5. Validate with `/validate-analytics`
6. Update status in `INDEX.md` as the plan progresses (Draft → Review → Approved → Merged)
7. When user triggers `/merge-tracking-plan`, merge approved events into `docs/event-catalog.md` and update `docs/event-schema.md` / `docs/dashboards.md` as needed
8. After merge, move the tracking plan file to `tracking-plans/archived/` and mark status as **Merged** in `INDEX.md`

**Important:** Never auto-merge events into the catalog. Only merge when the user explicitly runs `/merge-tracking-plan`.

## Naming Conventions

- **Events:** Object-Action framework, Proper Case (e.g., `Job Created`, `Interest Expressed`)
- **Properties:** snake_case (e.g., `signup_context`, `referrer_user_id`)
- **Verbs:** Past tense only (Created, Viewed, Shared, Submitted)
- **Standard Objects:** Check `docs/event-schema.md` before creating new objects
- **Property Dictionary:** Check `docs/event-catalog.md` before creating new properties

## Commands

- `/posthog-analytics` — Generate tracking plans and maintain the event catalog
- `/validate-analytics` — Run the 17-rule cross-document consistency validator
- `/merge-tracking-plan` — Manually merge an approved tracking plan's events into `docs/event-catalog.md` (and update schema/dashboards as needed), then archive the plan

## Product Context

The `context/` folder contains product structure docs that analytics events are built on. These are copies from the PM OS repo — update them when the originals change (rare, ~1-2x per quarter):

- `entity-relationship-model.md` — Database entities that map to Standard Objects
- `network-model.md` — Graph structure and viral loop definitions
- `prospect-structure.md` — Portfolio and link data structures (Loop 4)
- `product-overview.md` — Personas, surfaces, product vision

## Key Rules

- `docs/event-catalog.md` is the single source of truth for all events
- Tracking plans are archived to `tracking-plans/archived/` after merging — never deleted
- Never place tracking plans in `docs/`
- Reuse existing events and properties before creating new ones
- Intent vs outcome: for critical flows, always track both the UI click and server-confirmed result
- Viral attribution: any sharing chain event must carry `referrer_user_id`
- `acting_as` required on all hiring surface events (role is per-event, never a person property)
