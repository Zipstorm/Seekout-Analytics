Merge an approved tracking plan's events into the source-of-truth docs. Follow these steps.

---

## Step 1: Identify the Tracking Plan

Check `tracking-plans/INDEX.md` for plans with status **Approved**.

- If the user specified a feature name, find that plan.
- If multiple plans are approved and none was specified, list them and ask the user which one to merge.
- If no plans have **Approved** status, tell the user and stop.

Read the tracking plan file.

## Step 2: Pre-Validate the Tracking Plan

Before editing any file, run the tracking-plan validator:

```bash
python3 scripts/validate-analytics-docs.py <tracking-plan-path>
```

- If validation exits with errors, report the validator output and stop without editing any file.
- Warnings do not block the merge, but include them in the final summary.

## Step 3: Read the Source-of-Truth Docs

Read before making any changes:

- `docs/event-catalog.md` — Existing events and Property Dictionary
- `docs/event-schema.md` — Standard Objects table
- `docs/dashboards.md` — Dashboard specs and funnels

## Step 4: Check Standard Object Removals

If the tracking plan has `## Removed Standard Objects`, run:

```bash
python3 scripts/validate-analytics-docs.py --check-removal-safety <tracking-plan-path>
```

Interpret the result before editing any file:

- Exit `0`: removals are safe; continue.
- Non-zero exit with stdout lines in the form `<object> blocks: <event_name>`: stop without editing any file. Report each object and blocking catalog event, then tell the user to either rename the affected catalog events or remove the object from `## Removed Standard Objects` and re-approve the plan.
- Non-zero exit with empty stdout: stop without editing any file. Report stderr; this indicates malformed input or validator failure.

## Step 5: Merge Standard Object Declarations

Update `docs/event-schema.md` only after pre-validation and removal-safety checks pass:

- Append each non-redundant `## New Standard Objects` row to the end of the Standard Objects table. Use the same `Object | Entity | Example Events` shape. Append after the last `|`-prefixed row before the next non-table line in that section. Do not reorder existing rows.
- Skip new-object rows whose object already exists in `docs/event-schema.md`; the validator already reports these as redundant declarations.
- Delete each safe `## Removed Standard Objects` row from the Standard Objects table.

## Step 6: Merge into Event Catalog

Update `docs/event-catalog.md`:

- Add new events to the correct catalog section (Account, Prospect, Hiring, Viral Loop) with Area, Group, Property Updates, and Status.
- Add new properties to the Property Dictionary with type, allowed values (for enums), and Used In.
- Do not create duplicate events or properties — if one already exists, update it.

## Step 7: Update Dashboards

If the tracking plan introduces new funnels, dashboard panels, or Platform Health flows, update `docs/dashboards.md`.

## Step 8: Archive the Tracking Plan

- Move the tracking plan file from `tracking-plans/[feature-name].md` to `tracking-plans/archived/[feature-name].md`.
- Update `tracking-plans/INDEX.md`: set the status to **Merged** and update the tracking plan path to `archived/[feature-name].md`.

## Step 9: Post-Merge Validate

Run the catalog-mode validator:

```bash
python3 scripts/validate-analytics-docs.py
```

- If validation passes, continue to the report.
- If validation fails, print the validator output verbatim, state that pre-merge checks did not catch this issue, and stop. Do not attempt to roll back earlier edits. The user resolves the inconsistency manually by inspecting the modified files in a follow-up turn.

## Step 10: Report

Summarize what was merged:

- Number of new events added or updated
- Number of new properties added or updated
- Standard Objects added, skipped as redundant, or removed
- Any dashboard updates
- Final validation result
