# SeekOut Analytics

Analytics instrumentation, event taxonomy, metric frameworks, tracking plans, and dashboard specs for SeekOut products.

This repository is the source of truth for product analytics. Product-owned docs are namespaced by product, while shared naming rules and event-type taxonomy live once under `docs/shared/`.

## Quick Start

1. Pick a product: `helix` or `recruit`.
2. Read shared rules in [`docs/shared/naming-and-event-types.md`](docs/shared/naming-and-event-types.md).
3. Read the product schema, catalog, and dashboards under `docs/<product>/`.
4. Run validation with an explicit product:

```bash
python3 scripts/validate-analytics-docs.py --product helix
python3 scripts/validate-analytics-docs.py --product recruit
```

## Repository Structure

```text
.
├── docs/
│   ├── shared/naming-and-event-types.md        # Shared naming conventions + Event Types enum
│   ├── helix/                        # Helix catalog, schema, dashboards, metric docs
│   └── recruit/                      # Recruit catalog, schema, dashboards scaffold
├── context/
│   ├── helix/                        # Helix product context copies
│   └── recruit/                      # Recruit product context placeholder
├── tracking-plans/
│   ├── helix/                        # Helix active plans + archived/
│   └── recruit/                      # Recruit active plans + archived/
├── templates/tracking-plan.md        # Shared tracking-plan template
├── scripts/validate-analytics-docs.py
└── logs/
    ├── helix/conflicts-log.md
    └── recruit/conflicts-log.md
```

## Source of Truth

Each product has three canonical analytics documents:

| Path | Purpose |
|------|---------|
| `docs/<product>/event-catalog.md` | Product event taxonomy, property dictionary, implementation status |
| `docs/<product>/event-schema.md` | Product Standard Objects, product properties, PostHog config, validator config |
| `docs/<product>/dashboards.md` | Product dashboard specs, funnel definitions, platform health flows |

Shared rules:

| Path | Purpose |
|------|---------|
| `docs/shared/naming-and-event-types.md` | Shared naming conventions and Event Types enum read by Rule 17 / TP12 |

Helix also has product-specific metric frameworks in `docs/helix/`.

## Validation

`scripts/validate-analytics-docs.py` requires `--product` for every mode. There is no default product.

```bash
python3 scripts/validate-analytics-docs.py --product helix
python3 scripts/validate-analytics-docs.py --product helix helix-code-changes-login-onboarding
python3 scripts/validate-analytics-docs.py --product helix --check-removal-safety tracking-plans/helix/example.md
```

Catalog mode runs 17 rules. Tracking-plan mode runs 13 TP rules. Run history is written to `logs/<product>/conflicts-log.md`.

## Tracking Plan Workflow

```text
PRD / Feature Spec
       |
       v
  Draft Tracking Plan  ->  tracking-plans/<product>/<feature>.md
       |
       v
  Validate             ->  /validate-analytics --product PRODUCT [tracking-plan]
       |
       v
  Review -> Approved
       |
       v
  Merge                ->  /merge-tracking-plan --product PRODUCT [feature-or-plan]
       |
       +-> Events added to docs/<product>/event-catalog.md
       +-> Plan moved to tracking-plans/<product>/archived/
```

## Claude Code Commands

| Command | Description |
|---------|-------------|
| `/create-tracking-plan --product PRODUCT ...` | Generate tracking plans and maintain a product event catalog |
| `/validate-analytics --product PRODUCT [tracking-plan]` | Run the product-aware validator |
| `/merge-tracking-plan --product PRODUCT [feature-or-plan]` | Merge an approved tracking plan into the product catalog, then archive it |

## Key Rules

- Always read `docs/shared/naming-and-event-types.md` and `docs/<product>/event-schema.md` before creating events.
- `docs/<product>/event-catalog.md` is the source of truth for that product's events.
- Reuse existing events and properties before creating new ones.
- Track interaction/start and result separately for critical flows.
- Result event names must use `Succeeded`, `Rejected`, or `Errored`.
- Tracking plans are archived after merge, never deleted.
