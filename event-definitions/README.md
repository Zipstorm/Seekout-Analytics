# Event Definitions

Per-flow event definitions for Helix analytics. Each flow folder contains the complete specification for implementing and analyzing events for a specific user journey.

These flow definitions are the working source for instrumentation. Once a flow is implemented and approved, the events get merged into the canonical [`docs/event-catalog.md`](../docs/event-catalog.md).

## Structure

Each flow folder contains four files:

| File | What it covers |
|------|---------------|
| `events.md` | Event catalog — names, types, sources, triggers, complete inventory |
| `properties.md` | Property dictionary — types, allowed values, page contexts, components |
| `firing-rules.md` | When and why each event fires — full `capture()` code, behavioral proof, drop-off scenarios |
| `analytics-guide.md` | Funnels, segmentation, dashboards, key questions each event answers |

## Conventions

All flows follow these conventions (defined in [`event-type commands/`](../event-type%20commands/)):

- **Event names:** Object-Action, Proper Case (e.g., `Job Wizard Next Clicked`)
- **Property names:** snake_case (e.g., `current_page_context`, `entry_point`)
- **Page views:** Single `PAGE_VIEWED` event constant, differentiated by `current_page_context`
- **User actions:** Each action gets a specific Proper Case event constant + `action`/`action_value` properties
- **Identification:** PostHog SDK auto-captures `distinct_id`, `session_id`, `timestamp`, device props
- **Persona context:** `current_persona` person property (`$set`) is always available — replaces old `role` and `acting_as`

## Flows

| Flow | Folder | Persona | Status | What It Covers |
|------|--------|---------|--------|----------------|
| Login & Onboarding | [`login-onboarding/`](login-onboarding/) | All | In Progress | Auth landing → role selection → intro → first home page arrival |
| Hiring Manager Home | [`hiring-manager-home/`](hiring-manager-home/) | Hiring Manager | In Progress | Job postings dashboard, sidebar nav, persona switch, search/filter |
| HM Job Creation Wizard | [`hm-job-creation-wizard/`](hm-job-creation-wizard/) | Hiring Manager | In Progress | 5-step wizard for creating a job posting (Job details → Sam → Requirements → Questions → Verify → Success) |

## Adding a New Flow

1. Create a new folder under `event-definitions/` named in `kebab-case` (e.g., `recruiter-candidate-review`)
2. Create the four standard files: `events.md`, `properties.md`, `firing-rules.md`, `analytics-guide.md`
3. Use existing flow folders as templates
4. Add an entry to the Flows table above
5. When ready to publish, run `/merge-tracking-plan` to merge events into `docs/event-catalog.md`
