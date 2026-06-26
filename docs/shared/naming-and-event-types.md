---
analytics_platform: posthog
---

# Shared Analytics Naming and Event Types

These naming conventions and event types apply to every product in this repo.
Product-specific schemas live under `docs/<product>/event-schema.md`.

## Naming Conventions

### Event Names: Object-Action Framework

Every event follows the pattern: **Object Action**

- **Object**: What the user interacted with (e.g., Job, Profile, Interest, Team Member)
- **Action**: What happened, in past tense (e.g., Created, Shared, Viewed, Expressed)
- **Casing**: Proper Case (e.g., `Job Created`, `Interest Expressed`)

**Rules:**

1. **Past-tense verbs only** — Created, Viewed, Submitted, Shared (not Create, View, Submit, Share)
2. **Descriptive and meaningful** — Event name should represent intent. No generic names like `Action1` or `User Event`. Every name must be meaningful to anyone reading it.
   `Account Created`, `Create Job Button Clicked`, `Record Video Button Clicked`.
3. **Consistent object names** — Always refer to the same object the same way. Use `Team Member` everywhere, never `TeamMember` or `team member`.
4. **No special characters or trailing spaces** — Letters, numbers, and spaces only. No `/`, `&`, `@`, `#` or other special characters.
5. **Separate interaction/start from result** — Track the user's action or flow entry separately from the processed result:
   - Interaction: `Share Button Clicked`
   - Started: `Job Post Wizard Started`
   - Success: `Job Share Succeeded`
   - Rejected: `Job Share Rejected`
   - Error: `Chat WebSocket Errored`
6. **Interaction events capture discrete user-triggered actions** — Interaction events often follow the pattern
   `[Action] [Object] Button Clicked` where the action is present tense:
   `Share Button Clicked`, `Create Job Button Clicked`,
   `Record Video Button Clicked`. This is exception to the past-tense rule.
7. **Result events keep the object clean** — in `Job Publish Rejected`, the
   object is `Job` and the action is `Publish Rejected`. The verb-noun before the
   result terminal belongs to the action; never add verb stems (e.g.
   `Job Publish`) to the Standard Objects table. Result terminals are past
   tense: `Succeeded` / `Rejected` / `Errored` — never `Success`, `Failure`,
   `Failed`, or `Error`. Existing events that still use old terminals are
   naming debt for a later rename pass.

### Property Names: snake_case

All event and person properties use `snake_case`: `job_id`, `current_persona`, `signup_context`, `share_channel`. No Proper Case or camelCase for properties.

For `current_page_context` and `previous_page_context` values, use underscores (_) for hierarchy, not slashes (/): `hm_job_creation_wizard_interview_questions`, `onboarding_role_selection`. URL paths must be transformed to snake_case — strip the leading `/`, replace `/` and `-` with `_` (e.g., `/onboarding/role-selection` → `onboarding_role_selection`).

## Event Types

Every event in the catalog **and** in every tracking plan must carry exactly one **Type** from the enum below. `--` is not a valid type. `page_view` / `user_action` describe the *capture mechanism*, not the event type, and are not valid here.

| Type | Meaning | Terminal rule | Examples |
|------|---------|---------------|----------|
| `View` | User saw a page, screen, object, or content without taking action | none | `Page Viewed`, `Job Link Viewed` |
| `Interaction` | Discrete user-triggered action | none | `Share Button Clicked`, `Create Job Button Clicked` |
| `Started` | User entered a multi-step flow, session, or process | name must end `Started` | `Job Post Wizard Started`, `Sam Session Started` |
| `Success` | Action, request, or flow step accepted or completed | name must end `Succeeded` | `Auth Login Succeeded`, `Job Share Succeeded` |
| `Rejected` | Intended action or request did not succeed because the system declined or rejected it | name must end `Rejected` | `Job Share Rejected`, `Auth Login Rejected` |
| `Error` | System or technical fault, not user-caused rejection | name must end `Errored` | `Chat WebSocket Errored` |

This table is the **source of truth** for the event-type enum. The validator (`scripts/validate-analytics-docs.py`) reads it for Rule 17 / TP12 and **errors if it is absent**.
