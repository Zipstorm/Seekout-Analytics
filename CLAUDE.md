# SeekOut Analytics

Analytics instrumentation, event taxonomy, tracking plans, metric frameworks, and dashboard specs for SeekOut products.

## Repository Structure

- `docs/shared/` - shared naming conventions and Event Types enum.
- `docs/<product>/` - product source-of-truth analytics docs: `event-catalog.md`, `event-schema.md`, `dashboards.md`.
- `context/<product>/` - product context dependencies.
- `tracking-plans/<product>/` - active product tracking plans. `archived/` holds completed plans.
- `plans/` - local design docs for PRs with follow-up status tracking.
- `templates/` - reusable templates.
- `scripts/` - validation tooling.
- `logs/<product>/` - validator run history.
- `backlog/<product>/` - known issues and future fixes (naming cleanup, dashboard fixes).

## Source of Truth

For any product, read both shared and product docs:

1. `docs/shared/naming-and-event-types.md` - naming conventions and Event Types enum.
2. `docs/<product>/event-schema.md` - Standard Objects, product properties, PostHog setup, validator config.
3. `docs/<product>/event-catalog.md` - product events and Property Dictionary.
4. `docs/<product>/dashboards.md` - product funnels and dashboard specs.

`docs/<product>/event-catalog.md` is the source of truth for that product's events.

## Context-First Rule

Before generating any analytics document for a product, read:

1. `context/<product>/` context docs or README.
2. `docs/shared/naming-and-event-types.md`.
3. `docs/<product>/event-schema.md`.
4. `docs/<product>/event-catalog.md`.

## Tracking Plan Workflow

1. User provides feature context (PRD excerpt, spec, or description).
2. Generate tracking plan using `templates/tracking-plan.md`.
3. Save to `tracking-plans/<product>/<feature-name>.md`.
4. Add entry to `tracking-plans/<product>/INDEX.md` with PRD link and status **Draft**.
5. Validate with `/validate-analytics --product PRODUCT [tracking-plan]`.
6. Update status in `INDEX.md` as the plan progresses: Draft -> Review -> Approved -> Merged.
7. When user triggers `/merge-tracking-plan --product PRODUCT`, merge approved events into `docs/<product>/event-catalog.md` and update `docs/<product>/event-schema.md` / `docs/<product>/dashboards.md` as needed.
8. After merge, move the tracking plan file to `tracking-plans/<product>/archived/` and mark status as **Merged** in `INDEX.md`.

**Important:** Never auto-merge events into the catalog. Only merge when the user explicitly runs `/merge-tracking-plan`.

### Workflow Enforcement

Every tracking plan has a Workflow checklist (see `templates/tracking-plan.md`). The steps are sequential. Before executing any step, check the tracking plan's Workflow section — if a prior step is unchecked, prompt the user: "Step [name] hasn't been completed yet. Should I do that first?"

Key gates:
- **Before raising a PR:** Re-validated must be checked. Run the validator, record results in the checkbox, then raise the PR.
- **Before `/merge-tracking-plan`:** PR must be approved.
- **Before absorption:** User must confirm the codebase implementation is done (this happens in the product repo, not here).

Never silently skip workflow steps.

## Merge Conflict Resolution

During `/merge-tracking-plan`, the **tracking plan wins** for its own events. The catalog gets updated to match, not the other way around.

- Tracking plan renames an event → update the catalog event name and add old name to Removed Events.
- Tracking plan adds/removes properties on an event → update the catalog event's Properties column.
- Tracking plan extends existing Property Dictionary enums → append new values, don't replace.
- Property Dictionary "Used In" is out of sync after merge → fix the catalog (add missing cross-references), never change the tracking plan.
- Duplicate events after merge → remove the older catalog entry, keep the tracking plan version.
- Pre-existing catalog issues (naming conventions, stale funnels) unrelated to the tracking plan → document in `backlog/<product>/`, don't fix during merge.

## Validation

The validator requires `--product` for catalog mode, tracking-plan mode, and removal-safety mode. There is no default product.

```bash
python3 scripts/validate-analytics-docs.py --product helix
python3 scripts/validate-analytics-docs.py --product helix helix-code-changes-login-onboarding
python3 scripts/validate-analytics-docs.py --product helix --check-removal-safety tracking-plans/helix/example.md
```

Catalog mode runs 17 rules. Tracking-plan mode runs 13 TP rules. Logs are written to `logs/<product>/conflicts-log.md`.

## Naming Rules

- **Events:** Object-Action framework, Proper Case, past-tense action.
- **Properties:** snake_case.
- **Result terminals:** `Succeeded`, `Rejected`, or `Errored`.
- **Event Types:** `View`, `Interaction`, `Started`, `Success`, `Rejected`, `Error`.
- **Standard Objects:** Check `docs/<product>/event-schema.md` before creating new objects.
- **Property Dictionary:** Check `docs/<product>/event-catalog.md` before creating new properties.

## Key Rules

- Reuse existing events and properties before creating new ones.
- Interaction/Started vs Result: for critical flows, track the UI interaction or process start separately from the processed result.
- Product-specific property requirements come from `docs/<product>/event-schema.md` frontmatter.
- Tracking plans are archived to `tracking-plans/<product>/archived/` after merging, never deleted.
- Never place tracking plans in `docs/`.
