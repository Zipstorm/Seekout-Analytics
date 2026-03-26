Merge an approved tracking plan's events into the source-of-truth docs. Follow these steps.

---

## Step 1: Identify the Tracking Plan

Check `tracking-plans/INDEX.md` for plans with status **Approved**.

- If the user specified a feature name, find that plan.
- If multiple plans are approved and none was specified, list them and ask the user which one to merge.
- If no plans have **Approved** status, tell the user and stop.

Read the tracking plan file.

## Step 2: Read the Source-of-Truth Docs

Read before making any changes:

- `docs/event-catalog.md` — Existing events and Property Dictionary
- `docs/event-schema.md` — Standard Objects table
- `docs/dashboards.md` — Dashboard specs and funnels

## Step 3: Merge into Event Catalog

Update `docs/event-catalog.md`:

- Add new events to the correct catalog section (Account, Prospect, Hiring, Viral Loop) with Area, Group, Property Updates, and Status
- Add new properties to the Property Dictionary with type, allowed values (for enums), and Used In
- Do not create duplicate events or properties — if one already exists, update it

## Step 4: Update Schema and Dashboards

- If the tracking plan introduces a new Standard Object, add it to `docs/event-schema.md`
- If the tracking plan introduces new funnels, dashboard panels, or Platform Health flows, update `docs/dashboards.md`

## Step 5: Archive the Tracking Plan

- Move the tracking plan file from `tracking-plans/[feature-name].md` to `tracking-plans/archived/[feature-name].md`
- Update `tracking-plans/INDEX.md`: set the status to **Merged** and update the tracking plan path to `archived/[feature-name].md`

## Step 6: Validate

Run `/validate-analytics` to confirm the merged docs are consistent.

## Step 7: Report

Summarize what was merged:
- Number of new events added
- Number of new properties added
- Any schema or dashboard updates
- Validation result
