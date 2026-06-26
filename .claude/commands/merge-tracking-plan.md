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

Update `docs/<product>/event-catalog.md`:

- Add new events to the correct product catalog section.
- Add new properties to the Property Dictionary with type, allowed values, and Used In.
- Do not create duplicate events or properties.

## Step 7: Update Dashboards

If the tracking plan introduces new funnels, dashboard panels, or Platform Health flows, update `docs/<product>/dashboards.md`.

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
- New properties added or updated.
- Standard Objects added, skipped, or removed.
- Dashboard updates.
- Final validation result.
