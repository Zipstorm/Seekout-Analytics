Generate tracking plans and maintain PostHog event catalogs for SeekOut products. Produce PM-level artifacts: tracking plans, event specs, dashboard specs, and catalog updates. Do not produce SDK implementation code unless the user explicitly asks.

Syntax:

```text
/create-tracking-plan --product PRODUCT ...
```

`--product` is required. Do not infer a default product.

---

## Process

### Step 1: Read the Analytics Context

Always read before generating anything:

- `docs/shared/naming-and-event-types.md` - shared naming conventions and Event Types.
- `docs/<product>/event-schema.md` - Standard Objects, product properties, PostHog config, validator config.
- `docs/<product>/event-catalog.md` - product event catalog and Property Dictionary.
- `docs/<product>/dashboards.md` - dashboard specs, funnels, Platform Health flows.
- `context/<product>/` - product context docs or README.

Derive product areas and catalog sections from the product's own docs. Do not reuse Helix-only sections for another product.

### Step 2: Understand the Feature

Ask the user for the feature context. They should provide one of:

- A PRD or feature spec.
- A brief description of the feature, success metrics, and key user flows.
- The persona or user segment involved.

Extract success metrics, key flows, involved personas, and whether any Standard Objects or properties need to be added.

### Step 3: Generate the Tracking Plan

Use `templates/tracking-plan.md` and save drafts directly under `tracking-plans/<product>/`.

#### Naming Rules

- **Object-Action framework:** `Object Action`.
- **Proper Case** for event names.
- **snake_case** for properties.
- **Past-tense actions** for normal events.
- **Type taxonomy:** `View`, `Interaction`, `Started`, `Success`, `Rejected`, `Error`.
- **Result terminals:** Success events end `Succeeded`, Rejected events end `Rejected`, Error events end `Errored`.
- Check `docs/<product>/event-schema.md` before creating Standard Objects.
- Check `docs/<product>/event-catalog.md` before creating properties.
- Reuse existing events and properties before creating new ones.

#### Required Checks

- [ ] Every event follows Object-Action with Proper Case.
- [ ] All properties are snake_case.
- [ ] No duplicate events in the product catalog.
- [ ] Interaction/start and result are separated for critical flows.
- [ ] Type values use only the shared Event Types enum.
- [ ] Result events use canonical terminals: `Succeeded`, `Rejected`, `Errored`.
- [ ] Product-specific required properties from `docs/<product>/event-schema.md` frontmatter are satisfied.
- [ ] Property Updates column is filled for person or group mutations.
- [ ] New events are ready to add to `docs/<product>/event-catalog.md`.
- [ ] New properties are ready for the product Property Dictionary.

#### Mapping Metrics to Events

For each success metric, specify:

1. The PostHog events that measure it.
2. The insight type: funnel, trend, retention, or path.
3. Filters or breakdowns needed.
4. Which dashboard it belongs to.

### Step 4: Update the Index

After saving the tracking plan:

- Add an entry to `tracking-plans/<product>/INDEX.md` with feature name, PRD link, status **Draft**, tracking plan path, and date.
- Tell the user: "When this plan is approved, run `/merge-tracking-plan --product PRODUCT` to merge events into the catalog."

**Important:** Do not merge events into `docs/<product>/event-catalog.md` automatically. Merging is a separate step triggered manually by the user.

---

## Tips

- Reuse before creating: add properties to existing events when that answers the product question.
- Track only events that support a decision or a committed dashboard.
- Product-specific requirements live in `docs/<product>/event-schema.md` frontmatter.
- Shared naming and Event Types live in `docs/shared/naming-and-event-types.md`.
