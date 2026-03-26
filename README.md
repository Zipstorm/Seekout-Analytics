# SeekOut Analytics

Analytics instrumentation, event taxonomy, metric frameworks, and dashboards for **Helix** ([SeekOut.ai](https://seekout.ai)).

This repository is the single source of truth for all product analytics — event definitions, naming conventions, tracking plans, metric models, and dashboard specs. It is designed to be used with **Claude Code** for AI-assisted analytics workflows.

## Quick Start

1. **Understand the product** — Read [`context/product-overview.md`](context/product-overview.md) for personas, surfaces, and product vision.
2. **Learn the schema** — Read [`docs/event-schema.md`](docs/event-schema.md) for naming conventions, standard objects, and PostHog configuration.
3. **Browse existing events** — Read [`docs/event-catalog.md`](docs/event-catalog.md), the master event taxonomy and property dictionary.

## Repository Structure

```
.
├── docs/                   # Source-of-truth analytics documents
│   ├── event-catalog.md        # Master event taxonomy & property dictionary
│   ├── event-schema.md         # Naming conventions, standard objects, PostHog config
│   ├── dashboards.md           # Dashboard specs & funnel definitions
│   ├── viral-loop-metrics.md   # K-factor decomposition for 4 viral loops
│   ├── network-quantification.md  # Network health metrics (Size, Liquidity, Activation, Bridging)
│   └── tiered-metric-diagrams.md  # 3-tier metric hierarchy (Mermaid diagrams)
├── context/                # Product context dependencies
│   ├── product-overview.md     # Product vision, personas, surfaces
│   ├── entity-relationship-model.md  # Database entities → Standard Objects
│   ├── network-model.md        # Graph structure & viral loop definitions
│   └── prospect-structure.md   # Portfolio & link data structures
├── tracking-plans/         # Per-feature tracking plans (working documents)
│   ├── INDEX.md                # Status tracker (Draft → Review → Approved → Merged)
│   └── archived/               # Completed & merged tracking plans
├── templates/              # Reusable templates
│   └── tracking-plan.md       # Template for new feature tracking plans
├── scripts/                # Validation tooling
│   └── validate-analytics-docs.py  # 14-rule cross-document consistency checker
└── logs/                   # Validator run history
    └── conflicts-log.md
```

## Source of Truth

The 3 canonical analytics documents in `docs/`:

| Document | Purpose |
|----------|---------|
| [`event-catalog.md`](docs/event-catalog.md) | Master event taxonomy, property dictionary, implementation status |
| [`event-schema.md`](docs/event-schema.md) | Naming conventions, standard objects, PostHog config, sample code |
| [`dashboards.md`](docs/dashboards.md) | Dashboard specs, funnel definitions, platform health flows |

Supporting metric frameworks:

| Document | Purpose |
|----------|---------|
| [`viral-loop-metrics.md`](docs/viral-loop-metrics.md) | 4 viral loops with K-factor decomposition |
| [`network-quantification.md`](docs/network-quantification.md) | Network health metrics (Helix Size, Liquidity, Activation, Bridging) |
| [`tiered-metric-diagrams.md`](docs/tiered-metric-diagrams.md) | 3-tier metric hierarchy with Mermaid diagrams |

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Events | Object-Action, Proper Case, past tense verbs | `Job Created`, `Interest Expressed` |
| Properties | snake_case | `signup_context`, `referrer_user_id` |

Always check `event-schema.md` for standard objects and `event-catalog.md` for existing properties before creating new ones.

## Tracking Plan Workflow

```
PRD / Feature Spec
       │
       ▼
  Draft Tracking Plan  ──→  tracking-plans/[feature].md
       │
       ▼
  Validate  ──────────────→  /validate-analytics
       │
       ▼
  Review → Approved
       │
       ▼
  Merge  ─────────────────→  /merge-tracking-plan
       │
       ├──→  Events added to docs/event-catalog.md
       └──→  Plan moved to tracking-plans/archived/
```

## Claude Code Commands

This repo is built for use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Available commands:

| Command | Description |
|---------|-------------|
| `/posthog-analytics` | Generate tracking plans and maintain the event catalog |
| `/validate-analytics` | Run the 14-rule cross-document consistency validator |
| `/merge-tracking-plan` | Merge an approved tracking plan into the catalog, then archive it |

## Validation

The validator (`scripts/validate-analytics-docs.py`) enforces 14 consistency rules across all analytics documents — checking event coverage, property compliance, naming conventions, and funnel definitions. Run history is logged to `logs/conflicts-log.md`.

## Analytics Platform

Events are instrumented via **PostHog**. See [`docs/event-schema.md`](docs/event-schema.md) for PostHog configuration, standard property objects, and implementation code samples.

## Key Rules

- `docs/event-catalog.md` is the **single source of truth** for all events
- Reuse existing events and properties before creating new ones
- Track both **intent and outcome** for critical flows (UI click + server confirmation)
- Viral attribution: sharing chain events must carry `referrer_user_id`
- `acting_as` is required on all hiring surface events
- Tracking plans are **archived after merge** — never deleted
