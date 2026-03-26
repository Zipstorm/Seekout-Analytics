Run the analytics validator. Supports two modes:

- **Catalog mode** (no arguments): validates the 3 source-of-truth docs against each other (14 rules)
- **Tracking plan mode** (with argument): validates a specific tracking plan against the catalog context (9 TP rules)

## Step 1: Run the Validator

If the user provided arguments (a tracking plan name or path after `/validate-analytics`):

```
python3 scripts/validate-analytics-docs.py $ARGUMENTS
```

If no arguments:

```
python3 scripts/validate-analytics-docs.py
```

## Step 2: Report Results

### Catalog mode

If the script exits with code 0 (all clear):
- Tell the user all 14 rules passed
- Mention the log file was updated

If the script exits with code 1 (errors or warnings found):
- Show the terminal output (errors and warnings) to the user
- For each error, briefly explain what it means and what to fix
- Mention the log file has the full record

If the script exits with code 2 (parse failure):
- Show the error message
- Suggest checking that the 3 analytics docs in `docs/` exist and have the expected markdown table format

### Tracking plan mode

If the script exits with code 0 (all clear):
- Tell the user all 9 TP rules passed
- Mention which catalog context was loaded for reference

If the script exits with code 1 (errors or warnings found):
- Show the terminal output (errors and warnings) to the user
- For each error, explain what it means in the tracking plan context
- Mention the log file has the full record

If the script exits with code 2 (parse failure):
- Show the error message
- Suggest checking that the tracking plan exists and follows the template format (`templates/tracking-plan.md`)

## Step 3: Handle Warnings

If there are **new warnings** (not already in Known Warnings):

1. List each warning with a number
2. Ask: "Want to add any of these to Known Warnings? (numbers, 'all', or 'none')"
3. **Wait for explicit user approval** — never auto-suppress warnings
4. For approved warnings, append entries to the `## Known Warnings` section in `logs/conflicts-log.md` using this exact format:

```
- [RULE_NUMBER] EXACT_WARNING_MESSAGE
  Reason: USER_REASON | Approved: YYYY-MM-DD
```

The first line (`- [N] message` or `- [TP5] message`) must match the script's warning text exactly — this is what the script uses for matching. The `Reason:` line is for human context only.

Ask the user for a short reason for each suppressed warning.

## Step 4: Offer Next Steps

### Catalog mode

If there were errors:
- Ask: "Want me to fix any of these issues in the analytics docs?"
- If the user says yes, read the relevant doc(s) and apply the fixes

If all clear:
- Say: "All 3 analytics docs are in sync."

### Tracking plan mode

If there were errors:
- Ask: "Want me to fix these issues in the tracking plan?"
- If the user says yes, read the tracking plan and apply the fixes

If all clear:
- Say: "Tracking plan [name] is valid against the current catalog. Run `/merge-tracking-plan` when ready to merge."
