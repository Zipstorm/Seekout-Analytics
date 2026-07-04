Run the product-aware analytics validator. Syntax:

```text
/validate-analytics --product PRODUCT [tracking-plan]
```

`--product` is required. Do not infer a default product.

## Step 1: Validate Arguments

- Require `--product PRODUCT`.
- Optional positional argument is a tracking-plan path, basename, or file under `tracking-plans/<product>/`.

If `--product` is missing, tell the user to rerun with `/validate-analytics --product PRODUCT [tracking-plan]`.

## Step 2: Run the Validator

Catalog mode:

```bash
python3 scripts/validate-analytics-docs.py --product PRODUCT
```

Tracking-plan mode:

```bash
python3 scripts/validate-analytics-docs.py --product PRODUCT TRACKING_PLAN
```

## Step 3: Report Results

### Catalog mode

If the script exits with code 0:
- Tell the user all 17 rules passed.
- Mention `logs/<product>/conflicts-log.md` was updated.

If the script exits with code 1:
- Show the terminal output.
- Explain the important errors and what files to inspect.
- Mention the log file has the full record.

If the script exits with code 2:
- Show the error message.
- Suggest checking `docs/<product>/event-catalog.md`, `docs/<product>/event-schema.md`, `docs/<product>/dashboards.md`, and `docs/shared/naming-and-event-types.md`.

### Tracking-plan mode

If the script exits with code 0:
- Tell the user all 13 TP rules passed.
- Mention the product catalog context that was loaded.

If the script exits with code 1:
- Show the terminal output.
- Explain each meaningful issue in tracking-plan context.
- Mention the log file has the full record.

If the script exits with code 2:
- Show the error message.
- Suggest checking that the tracking plan exists and follows `templates/tracking-plan.md`.

## Step 4: Handle Warnings

If there are new warnings not already in Known Warnings:

1. List each warning with a number.
2. Ask: "Want to add any of these to Known Warnings? (numbers, 'all', or 'none')"
3. Wait for explicit user approval. Never auto-suppress warnings.
4. For approved warnings, append entries to `## Known Warnings` in `logs/<product>/conflicts-log.md`:

```text
- [RULE_NUMBER] EXACT_WARNING_MESSAGE
  Reason: USER_REASON | Approved: YYYY-MM-DD
```

The first line must match the script's warning text exactly.

## Step 5: Offer Next Steps

If there were errors, ask whether the user wants fixes in the relevant product docs or tracking plan. If all clear, say the product analytics docs or tracking plan are valid.
