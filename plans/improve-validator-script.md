# Improve Validator Object Name Matching

## Summary

Tighten tracking-plan object validation so in-flight tracking plans can declare the Standard Objects they will add or remove at merge time, and update `/merge-tracking-plan` so those declarations are applied when a plan is archived. TP mode should apply strict object-action decomposition to every event, while catalog Rule 1 remains lenient so existing catalog events continue to validate.

## Key Changes

- In `parse_tracking_plan`, parse two optional sibling sections:
  - `## New Standard Objects` with columns `Object | Entity | Example Events`, matching `docs/event-schema.md` so merge can copy rows directly.
  - `## Removed Standard Objects` with column `Object`, optionally followed by `Reason`. `Reason` is reviewer context only and may be omitted entirely or left blank per row.
- For `Removed Standard Objects`, if the table header contains only `Object`, parse single-column rows. If the table header contains `Object | Reason`, parse both columns and allow blank `Reason` cells.
- Section headers are matched case-insensitively. Either section may appear anywhere in the document. A present header followed by no content is valid and empty. A present header followed by a properly formed table header row and zero data rows is also valid and empty. Blank lines between the header and table are allowed; any other non-table content, including paragraphs, broken tables, or partial rows, is a parse failure. Duplicate `New Standard Objects` or `Removed Standard Objects` headers are parse errors.
- Declaration validation runs before per-event validation:
  1. Empty or blank `Object` cells in either section are parse errors.
  2. The same object in both `New Standard Objects` and `Removed Standard Objects` is a parse error.
  3. Removing an object that is not in `schema_objects` and not in `tp_added_objects` is a warning because the removal has no effect.
  4. Adding an object that already exists in `schema_objects` is a warning, not an error.
- Declaration errors do not halt per-event validation. Contradicting objects remain in both `tp_added_objects` and `tp_removed_objects`; because the per-event procedure checks removals first, events using a contradicting object emit removed-object errors alongside the contradiction error. This is intentional so authors see the full impact.
- Add a strict TP-only helper named `_extract_object`. It returns the event name minus the final whitespace-delimited token, or an error when the event has fewer than two tokens. Keep the existing `_object_prefix` helper for legacy catalog Rule 1.
- In TP mode, validate each event with this ordered procedure:
  1. Extract `object = event_name.rsplit(" ", 1)[0]`. If the event has fewer than two tokens, error with `Event name must follow Object-Action format`.
  2. If `object in tp_removed_objects`, emit the removed-object error, even if the object also exists in schema.
  3. Else if `object in schema_objects union tp_added_objects`, pass.
  4. Else emit the unmatched-object error.
- Add a validator subcommand in `scripts/validate-analytics-docs.py`: `--check-removal-safety <tp-path>`.
  - It parses the TP, computes `tp_removed_objects`, then scans `docs/event-catalog.md` for catalog events that still resolve to any removed object under the existing catalog object-resolution behavior: lenient longest-prefix plus the catalog `Button Clicked` carve-out.
  - The orphan check must match catalog Rule 1 today. When the catalog migrates to strict decomposition, update `--check-removal-safety` to match the new catalog resolution.
- Update the repo-confirmed command file `.claude/commands/merge-tracking-plan.md` so `/merge-tracking-plan` consumes `New Standard Objects` and `Removed Standard Objects` when archiving a TP:
  1. Run the full TP validator first: `python3 scripts/validate-analytics-docs.py <tp-path>`. If it exits with errors, report them and halt without editing any file.
  2. Parse the approved TP's `New Standard Objects` and `Removed Standard Objects` sections.
  3. Run `python3 scripts/validate-analytics-docs.py --check-removal-safety <tp-path>` before making schema edits.
  4. If the subcommand exits non-zero with stdout content, print a failure summary listing each object and the catalog events that still reference it, suggest either renaming the affected catalog events or removing the object from `Removed Standard Objects`, then halt without editing any file.
  5. If the subcommand exits non-zero with empty stdout, treat it as malformed input or validator failure: report stderr and halt without editing any file.
  6. If the subcommand exits zero, apply schema edits as a single batch: append each non-redundant `New Standard Objects` row to the end of the Standard Objects table in `docs/event-schema.md` (the last `|`-prefixed row before the next non-table line in that section; skip rows whose object already exists in `docs/event-schema.md`; declaration validation has already emitted a redundant-addition warning for these), and delete each `Removed Standard Objects` row from that table. Do not reorder existing rows.
  7. Continue with the existing merge steps: catalog event/property updates, dashboard updates, archive the TP, and update `tracking-plans/INDEX.md`. Finally, run a post-merge validation with `python3 scripts/validate-analytics-docs.py` (default catalog mode, verifying schema/catalog/dashboard consistency rather than the archived TP) to confirm the schema, catalog, and dashboards remain consistent.
  8. If post-merge validation fails, print the validator output verbatim, state that pre-merge checks did not catch this issue, and halt. Do not attempt to roll back earlier edits; the user resolves the inconsistency manually by inspecting the modified files in a follow-up turn.
- Missing add/remove sections: valid. Malformed object-section tables: parse failure.
- Update `templates/tracking-plan.md` with commented-out stubs for `New Standard Objects` and `Removed Standard Objects`.
- Add `__pycache__/` to `.gitignore` as one-line housekeeping so local bytecode output is not tracked.

## Messages

- Unmatched object error:
  `Event "Foo Bar Created": object "Foo Bar" is not in docs/event-schema.md Standard Objects or this plan's ## New Standard Objects section. Either rename the event to use a registered object, or declare "Foo Bar" in ## New Standard Objects.`
- Removed object error:
  `Event "Foo Bar Created": object "Foo Bar" is listed in ## Removed Standard Objects. Rename the event, or remove "Foo Bar" from the removal list.`
- Malformed `New Standard Objects` section error:
  `Tracking plan section "New Standard Objects" must use columns: Object | Entity | Example Events.`
- Malformed `Removed Standard Objects` section error:
  `Tracking plan section "Removed Standard Objects" must use columns: Object, optionally followed by Reason.`
- Add/remove contradiction error:
  `Tracking plan declares "Foo Bar" in both ## New Standard Objects and ## Removed Standard Objects. Remove the duplicate or pick one section.`
- No-op removal warning:
  `## Removed Standard Objects lists "Foo Bar", which is not in docs/event-schema.md Standard Objects nor declared in ## New Standard Objects. Removal has no effect.`
- Empty `New Standard Objects` Object cell error:
  `## New Standard Objects has a row with an empty Object cell. Every declaration row must name an object.`
- Empty `Removed Standard Objects` Object cell error:
  `## Removed Standard Objects has a row with an empty Object cell. Every removal row must name an object.`

## Subcommand Contract

- Invocation: `python3 scripts/validate-analytics-docs.py --check-removal-safety <tp-path>`
- Exit code: `0` when every `Removed Standard Objects` entry is safe to delete because no catalog events resolve to it; non-zero when at least one removal would orphan a catalog event.
- Stdout: one line per blocking event in the form `<object> blocks: <event_name>`. Stdout is empty when nothing blocks.
- Stderr: parse failures, missing files, and other validator errors use existing stderr conventions.
- Malformed input behavior:
  - If `<tp-path>` does not exist, is not readable, or is not a markdown file, exit non-zero, print the error to stderr, and leave stdout empty.
  - If the TP's `New Standard Objects` or `Removed Standard Objects` sections fail declaration validation, exit non-zero, print the relevant declaration error messages to stderr, and leave stdout empty.
  - Consumers distinguish blocked removals from malformed input by checking stdout: non-empty stdout with non-zero exit means blocking-removal output; empty stdout with non-zero exit means malformed input or validator failure, and stderr is the report source.

## Strictness Boundary

TP mode applies strict object-action decomposition uniformly. There is no TP-mode `Button Clicked` carve-out: `Proceed Button Clicked` extracts object `Proceed Button`, which must be registered in schema or declared in `New Standard Objects`. Catalog Rule 1 keeps the lenient longest-prefix logic and existing `Button Clicked` carve-out so pre-existing events under atomic objects like `Auth`, `Profile`, and `Voice Session` continue to validate. Bringing the catalog in line with the strict rule is a separate cleanup.

## Known Consequences

- Do not update `tracking-plans/hm-job-creation-wizard-v2.md` in this PR.
- Until the v2 TP follow-up lands, `/validate-analytics` will fail when run against `tracking-plans/hm-job-creation-wizard-v2.md` because strict decomposition surfaces existing object-name gaps. This is expected. The follow-up should either declare compound objects in `New Standard Objects` or rename the affected events.

## Expected v2 Behavior

When `/validate-analytics` runs against `tracking-plans/hm-job-creation-wizard-v2.md` after this PR lands, the following parsed New Events should error with the unmatched-object message unless the TP follow-up declares the extracted object or renames the event. This list is illustrative runtime output, not a unit-test fixture; the v2 file may shift before the follow-up lands.

- `Create Job Button Clicked` -> `Create Job Button`
- `Job Post Wizard Started` -> `Job Post Wizard`
- `Job Post Wizard Job Details Completed` -> `Job Post Wizard Job Details`
- `Job Posting Draft Created` -> `Job Posting Draft`
- `Job Creation Failed` -> `Job Creation`
- `Job Post Wizard Intake Mode Selected` -> `Job Post Wizard Intake Mode`
- `Sam Session Started` / `Sam Session Ended` -> `Sam Session`
- `Job Post Wizard Role Requirements Completed` -> `Job Post Wizard Role Requirements`
- `Requirement Add Button Clicked` -> `Requirement Add Button`
- `Job Post Wizard Interview Questions Completed` -> `Job Post Wizard Interview Questions`
- `Question Add Button Clicked` -> `Question Add Button`
- `Screening Configuration Saved` -> `Screening Configuration`
- `Job Verification Code Send Button Clicked` -> `Job Verification Code Send Button`
- `Job Post Wizard Verification Completed` / `Job Post Wizard Verification Skipped` -> `Job Post Wizard Verification`
- `Job Post Wizard Back Button Clicked` -> `Job Post Wizard Back Button`
- `Job Posting Verified` / `Job Posting Published` -> `Job Posting`
- `Archive Job Button Clicked` -> `Archive Job Button`
- `Job Status Changed` -> `Job Status`
- `Share Button Clicked` -> `Share Button`
- `Job Share Failed` -> `Job Share`
- `Team Member Invite Failed` -> `Team Member Invite`

## Test Plan

- Add stdlib `unittest` coverage; do not introduce new runtime dependencies.
- Cover exact-match decomposition without TP declarations:
  - `Job Wizard Step Completed` extracts `Job Wizard Step` and passes because `Job Wizard Step` is in schema.
  - `Job Post Created` extracts `Job Post` and errors when only `Job` is registered.
- Cover strict rule vs longest-prefix explicitly: `Foo Bar Created` errors when only `Foo` is registered.
- Cover no TP-mode `Button Clicked` carve-out: `Proceed Button Clicked` extracts `Proceed Button` and errors unless `Proceed Button` is registered or declared.
- Cover `New Standard Objects`: declared `Sam Session` makes `Sam Session Started` pass; without the declaration it errors.
- Cover `Removed Standard Objects`: removing `Sam Session` makes `Sam Session Started` error with the removed-object message, even when the test fixture also lists `Sam Session` in `schema_objects`, verifying removal precedence over schema membership.
- Cover duplicate additions: declaring `Job` in `New Standard Objects` while `Job` is already in schema produces a warning, not an error.
- Cover declaration contradictions: declaring `Foo Bar` in both `New Standard Objects` and `Removed Standard Objects` errors with the contradiction message.
- Cover contradiction cascade: declaring `Foo Bar` in both sections and using `Foo Bar Created` produces both the contradiction error and the removed-object event error.
- Cover no-op removals: declaring `Foo Bar` in `Removed Standard Objects` when it is not in schema or `New Standard Objects` produces a warning, not an error.
- Cover empty Object cells in `New Standard Objects`: a declaration row with an empty `Object` column errors with the empty-cell-New message.
- Cover Removed-side parse errors: a `Removed Standard Objects` section with a missing `Object` column header errors with the malformed-Removed message, and a row with an empty `Object` cell errors with the empty-cell-Removed message.
- Cover optional `Reason`: a `Removed Standard Objects` section with only an `Object` column parses successfully and treats each row's reason as empty.
- Cover single-word events: `Created` errors with `Event name must follow Object-Action format`.
- Cover parser behavior: absent sections are valid; bare header is valid; header plus table-header-row and zero data rows is valid; header plus non-table content is a parse failure; duplicate headers or wrong/missing columns produce parse failures.
- Cover `--check-removal-safety` happy path: a TP that removes an object with no catalog references exits 0 with empty stdout.
- Cover `--check-removal-safety` blocking path: a TP that removes an object referenced by catalog events exits non-zero and prints one line per blocking event using `<object> blocks: <event_name>`.
- Cover `--check-removal-safety` no-op path: a TP without a `Removed Standard Objects` section exits 0 with empty stdout.
- Cover `--check-removal-safety` missing-file path: a nonexistent TP path exits non-zero, prints to stderr, and leaves stdout empty.
- Cover `--check-removal-safety` parse-error path: a malformed `New Standard Objects` table exits non-zero with the malformed-section message on stderr and empty stdout.
- Cover `--check-removal-safety` partial-blocking path: a TP removing two objects where only one is referenced prints only the blocking object's event lines and exits non-zero.
- Run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest`.

## Non-Goals

- Manual edits to `docs/event-schema.md` are out of scope. The only path that mutates the schema in this PR is the updated `/merge-tracking-plan` flow consuming declared add/remove sections.
- Do not change or remove the `Button Clicked` carve-out in catalog Rule 1. The carve-out does not exist in TP mode.
- Do not update `tracking-plans/hm-job-creation-wizard-v2.md`; that is a follow-up PR.
- Do not add token normalization for backticks, markdown emphasis, or whitespace.
- Do not add the schema example-event round-trip rule in this PR.

## Follow-Ups

- v2 TP cleanup: declare compound objects in `tracking-plans/hm-job-creation-wizard-v2.md` or rename affected events so it passes strict TP validation.
- Catalog migration: register compound objects such as `Auth Login`, `Auth Session Restore`, `Profile Section`, and `Voice Session Setup` so Rule 1 can later adopt strict decomposition.
- Separate catalog cleanup PR: backfill `Share Button`, `Invite Button`, and `Record Video Button` as Standard Objects, then remove the `Button Clicked` carve-out in catalog Rule 1.
- Separate schema-consistency PR: verify each Standard Object row's example events resolve back to that object.
