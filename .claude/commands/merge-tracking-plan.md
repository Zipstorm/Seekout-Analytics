Merge an approved product tracking plan into the source-of-truth docs. Syntax:

```text
/merge-tracking-plan --product PRODUCT [feature-or-plan]
```

`--product` is required. Do not infer a default product.

---

## Step 1: Identify the Tracking Plan

Check `tracking-plans/<product>/INDEX.md` for plans with status **Approved**.

- If the user specified a feature name or plan path, resolve it under `tracking-plans/<product>/`.
- If multiple plans are approved and none was specified, list them and ask which one to merge.
- If no plans have **Approved** status, tell the user and stop.

Read the tracking plan file.

## Step 2: Pre-Validate the Tracking Plan

Before editing any file, run:

```bash
python3 scripts/validate-analytics-docs.py --product PRODUCT TRACKING_PLAN
```

- If validation exits with errors, report the validator output and stop without editing any file.
- Warnings do not block the merge, but include them in the final summary.

## Step 3: Read the Source-of-Truth Docs

Read before making changes:

- `docs/shared/naming-and-event-types.md` - shared naming conventions and Event Types.
- `docs/<product>/event-catalog.md` - existing events and Property Dictionary.
- `docs/<product>/event-schema.md` - Standard Objects and product config.
- `docs/<product>/dashboards.md` - dashboard specs and funnels.

## Step 4: Check Standard Object Removals

If the tracking plan has `## Removed Standard Objects`, run:

```bash
python3 scripts/validate-analytics-docs.py --product PRODUCT --check-removal-safety TRACKING_PLAN
```

Interpret the result before editing any file:

- Exit `0`: removals are safe; continue.
- Non-zero exit with stdout lines in the form `<object> blocks: <event_name>`: stop without editing any file. Report each object and blocking catalog event.
- Non-zero exit with empty stdout: stop without editing any file. Report stderr.

## Step 5: Merge Standard Object Declarations

Update `docs/<product>/event-schema.md` only after pre-validation and removal-safety checks pass:

- Append each non-redundant `## New Standard Objects` row to the Standard Objects table.
- Skip new-object rows whose object already exists in `docs/<product>/event-schema.md`.
- Delete each safe `## Removed Standard Objects` row from the Standard Objects table.
- Do not edit `docs/shared/naming-and-event-types.md` unless the approved plan explicitly changes shared naming or Event Types.

## Step 6: Merge into Event Catalog

Update `docs/<product>/event-catalog.md` using the structured tracking-plan sections as the source of truth. Treat `## Catalog Updates` as a checklist/summary only; if it conflicts with the detailed sections, stop and ask the user which source is correct.

Apply event changes in this order:

1. `## Event Renames`
   - For each row with `Current Name` / `New Name`, rename the existing catalog row in place. Do not add a second row with the new name while leaving the old one behind.
   - Update the catalog Type from `New Type` or `Type` when present.
   - Preserve existing Area, Source, Group, Status, Trigger, Properties, and Property Updates unless the tracking plan's Event Specifications or `## Existing Event Updates` explicitly changes them.
   - Update Property Dictionary `Used In` references from the old event name to the new event name.
   - If `Current Name` is missing but `New Name` already exists, treat the row as already migrated only after confirming the existing row matches the plan. Otherwise stop and report the mismatch.

2. `## Removed Events`
   - For rows whose Reason is `Renamed`, verify `Replaced By` exists in the catalog after the rename step, then delete the old event row if it is still present.
   - For rows whose Reason is `Dead code`, `Superseded`, `Never wired`, or equivalent, delete the event row if present. If it is absent, report it as skipped rather than recreating it.
   - Remove deleted event names from Property Dictionary `Used In`, schema result-pattern rows, dashboard funnels, dashboard metrics, and Platform Health references unless the plan says to keep historical documentation.

3. `## New Events Summary` plus matching Event Specifications
   - Add genuinely new events to the correct product catalog section.
   - Use Event Specifications for detailed Trigger, Properties, Group, and Property Updates when the summary row is abbreviated.
   - Do not create duplicate events. If the event already exists, update it only when the tracking plan explicitly describes it as an existing-event update.

4. `## Existing Event Updates`
   - Apply property additions/removals, trigger/source/status fixes, page-view extensions, and Property Updates changes to existing catalog rows.
   - For Page Viewed extensions, update the Page Viewed row and the relevant `current_page_context` Property Dictionary values.
   - For property extensions such as `mode` or `wizard_mode`, update both the event rows and the Property Dictionary allowed values / `Used In` references.

5. `## Property Details`
   - Add new properties to the Property Dictionary with type, allowed values, description, and Used In.
   - Extend existing property enum values without removing current values unless the plan explicitly says to remove them.
   - Keep `Used In` synchronized with new, renamed, removed, and updated events.

## Step 7: Update Schema and Dashboards

- If the tracking plan changes `## Interaction / Started / Result Pattern`, update the matching table in `docs/<product>/event-schema.md`.
- Replace old event names with renamed event names across schema result-pattern rows and dashboard references.
- If the tracking plan introduces or changes funnels, dashboard panels, metrics mappings, or Platform Health flows, update `docs/<product>/dashboards.md`.
- Keep dashboard filters aligned with any property enum changes made during Step 6.

## Step 8: Archive the Tracking Plan

- Move the tracking plan file from `tracking-plans/<product>/<feature-name>.md` to `tracking-plans/<product>/archived/<feature-name>.md`.
- Update `tracking-plans/<product>/INDEX.md`: set status to **Merged** and update the tracking plan path to `archived/<feature-name>.md`.

## Step 9: Post-Merge Validate

Run:

```bash
python3 scripts/validate-analytics-docs.py --product PRODUCT
```

If validation fails, print the validator output, state that pre-merge checks did not catch this issue, and stop. Do not roll back earlier edits unless the user explicitly asks.

## Step 10: Report

Summarize:

- New events added or updated.
- Events renamed.
- Events removed or skipped because they were already absent.
- New properties added or updated.
- Existing event updates applied.
- Standard Objects added, skipped, or removed.
- Schema and dashboard updates.
- Final validation result.
