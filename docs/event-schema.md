---
confluence:
  page_id: "1749319717"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Events Schema

**Product:** Helix (SeekOut.ai)  
**Analytics Platform:** PostHog  
**Last Updated:** April 2026

For the event catalog and implementation status, see [Helix Analytics Events Tracker](./event-catalog.md).
For dashboards and funnel mappings, see [Helix Analytics Dashboards & Funnels](./dashboards.md).

---

## Naming Conventions

### Event Names: Object-Action Framework

Every event follows the pattern: **Object Action**

- **Object**: What the user interacted with (e.g., Job, Profile, Interest, Team Member)
- **Action**: What happened, in past tense (e.g., Created, Shared, Viewed, Expressed)
- **Casing**: Proper Case (e.g., `Job Created`, `Interest Expressed`)

**Rules:**

1. **Past-tense verbs only** — Created, Viewed, Submitted, Shared (not Create, View, Submit, Share)
2. **Clear and descriptive** — No generic names like `Action1` or `User Event`. Every name must be meaningful to anyone reading it.
3. **Consistent object names** — Always refer to the same object the same way. Use `Team Member` everywhere, never `TeamMember` or `team member`.
4. **No special characters or trailing spaces** — Letters, numbers, and spaces only. No `/`, `&`, `@`.
5. **Separate intent from outcome** — Track the user's action (intent) and whether it succeeded or failed:
   - Intent: `Share Button Clicked`
   - Success: `Job Shared`
   - Failure: `Job Share Failed`
6. **Intent events use present tense** — Intent events follow the pattern
   `[Action] [Object] Button Clicked` where the action is present tense:
   `Share Button Clicked`, `Create Job Button Clicked`,
   `Record Video Button Clicked`. This is the one exception to the past-tense rule.

### Property Names: snake_case

All event and person properties use `snake_case`: `job_id`, `current_persona`, `signup_context`, `share_channel`. No Proper Case or camelCase for properties.

### Standard Objects

These are the canonical object names for Helix. Always use these exact names in events.

| Object | Entity | Example Events |
|--------|--------|---------------|
| Page | Any meaningful product page/screen | Page Viewed |
| Login | Auth flow initiation | Login Started, Login Cancelled |
| Account | User (account-level actions) | Account Created, Account Activated |
| Intro | Onboarding intro screen | Intro Completed |
| Profile | Prospect's career profile | Profile Created, Profile Section Updated |
| Job | Job posting | Job Created, Job Shared |
| Interest | Expression of Interest | Interest Expressed, Interest Reviewed |
| Review | Interest Review | Review Decision Made |
| Team Member | JobTeamMember | Team Member Invited, Team Member Joined |
| Custom Link | Prospect's named shareable link (general or job-specific) | Custom Link Created, Custom Link Shared |
| Career Coach | AI Career Coach agent | Career Coach Session Started |
| Surface | Prospect/Hiring surface | Surface Activated |
| Job Link | Shared job posting link viewed by anonymous visitors | Job Link Viewed, Job Link Engaged |
| Profile Link | Prospect's shareable profile link viewed by visitors | Profile Link Viewed, Profile Link Engaged |
| Job Wizard | Job creation wizard session | Job Wizard Started |
| Job Wizard Step | Job creation wizard step | Job Wizard Step Completed |
| Voice Session | AI hiring partner conversation | Voice Session Started, Voice Session Ended, Voice Session Setup Failed |
| Intro Video | HM intro video recording | Intro Video Created, Intro Video Deleted |
| Candidate | Candidate in review pipeline | Candidate Viewed, Candidate Tab Viewed, Candidate Recording Played |
| Requirement | AI-generated role requirement | Requirement Modified |
| Question | AI-generated interview question | Question Modified |
| Intro Script | Intro video script | Intro Script Updated |

When introducing a new object, add it to this table before using it in events.

---

## PostHog Setup

### Group Analytics

Every event related to a specific job must include the `job` group.

| Group Type | Helix Entity | Status |
|------------|-------------|--------|
| `job` | Job | Active (Phase 1) |
| `company` | Organization | Reserved (Phase 2) |

**Setting job group properties:**

```javascript
posthog.group('job', jobId, {
  job_title: job.title,
  job_status: job.status,
  job_visibility: job.visibility,
  hiring_manager_user_id: job.hiringManagerUserId,
  created_by_user_id: job.createdByUserId,
  created_at: job.createdAt,
  has_intro_video: false // set true by Intro Video Created, false by Intro Video Deleted
});
```

### Person Properties

Describe the user across all events. Set via `$set_once` (immutable, first value wins) or `$set` (updated on every login).

#### `$set_once` — Immutable, set once per user

| Property | Type | Values | Set By | Description |
|----------|------|--------|--------|-------------|
| `entry_point` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct` | Login Started, Account Created | First-touch attribution — how user originally found Helix. Derived from `?context=` URL param. |
| `first_referrer` | string | URL or null | Login Started | HTTP referrer at first visit (`document.referrer`). |
| `first_landing_url` | string | URL | Login Started | Full landing URL including query params at first visit. |
| `first_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Account Created | First persona chosen during onboarding. Never changes even if user switches role later. |
| `account_created_at` | ISO date | | Account Created | Account creation timestamp. |
| `signup_context` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct` | Account Created (backend) | How user arrived. Same values as `entry_point`. |
| `referred_by` | UUID | user ID | Account Created (backend) | User ID of referrer. |
| `activated_surfaces` | array | `["prospect"]`, `["prospect", "hiring"]` | Surface Activated | Currently activated surfaces. Grows over time. Uses `$set` (not `$set_once`). |

#### `$set` — Updated on every login

| Property | Type | Set By | Description |
|----------|------|--------|-------------|
| `email` | string | `identifyUser()` | User's current email |
| `name` | string | `identifyUser()` | User's current name |
| `org_id` | string | `identifyUser()` | User's current organization ID |
| `current_persona` | enum | `identifyUser()` + persona switch | Active persona — `hiring_manager`, `recruiter`, `job_seeker`. Updated on every login and on persona switch via sidebar toggle. Replaces the old `role` person property and `acting_as` event property. |

**Persona is NOT an immutable person property.** The same user can switch personas. `current_persona` (`$set`) reflects their current state. `first_persona` (`$set_once`) preserves what they originally chose during onboarding.

**Identifying a user (JS SDK — called after auth succeeds):**

```javascript
// In lib/posthog.ts → identifyUser()
const persona = ROLE_TO_PERSONA[user.role] || 'unknown';
posthog.identify(user.id,
  { email: user.email, name: user.name, org_id: user.orgId, current_persona: persona },  // $set
  { account_created_at: user.createdAt }  // $set_once
);
```

**Setting first-touch attribution (JS SDK — fires on Login Started, before auth):**

```javascript
// In pages/SignUp.tsx → handleLogin()
posthog.capture('Login Started', {
  action: 'click',
  action_value: 'continue_with_google_or_email_button',
  current_page_context: 'auth/landing',
  entry_point: entryPoint,
  entity_type: 'account',
  component: 'auth_landing_hero_card_cta',
  $set_once: {
    entry_point: entryPoint,
    first_referrer: document.referrer || null,
    first_landing_url: window.location.href,
  },
});
```

**Setting first_persona (JS SDK — fires on Account Created, after role selection):**

```javascript
// In pages/RoleSelection.tsx → handleContinue()
posthog.capture('Account Created', {
  action: 'click',
  action_value: 'continue_as_hiring_manager_button',
  current_page_context: 'onboarding/role_selection',
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  persona: 'hiring_manager',
  signup_context: entryPoint,
  $set_once: {
    first_persona: 'hiring_manager',
    entry_point: entryPoint,
    account_created_at: new Date().toISOString(),
  },
});
```

### Standard Event Properties

Include on every event where applicable.

| Property | Type | Values | When to Include |
|----------|------|--------|----------------|
| `job_id` | UUID | | All job-related events |

> **Note:** `acting_as` and `surface` have been removed as standard event properties. The user's active persona is now tracked via the `current_persona` person property (`$set`), which is automatically available on all events — this replaces `acting_as`. The surface context is derivable from `current_persona` (hiring_manager/recruiter → hiring, job_seeker → prospect) — this replaces `surface`.

---

## Sample Event Calls

### Login & onboarding events (JS SDK — frontend)

```javascript
// Page Viewed — fires on page mount
posthog.capture('Page Viewed', {
  current_page_context: 'auth/landing',
  previous_page_context: null,
  entry_point: 'direct',
});

// Login Started — fires on CTA click, before auth
const searchParams = new URLSearchParams(window.location.search);
const entryPoint = searchParams.get('context') || 'direct';

posthog.capture('Login Started', {
  action: 'click',
  action_value: 'continue_with_google_or_email_button',
  current_page_context: 'auth/landing',
  previous_page_context: null,
  entry_point: entryPoint,
  entity_type: 'account',
  component: 'auth_landing_hero_card_cta',
  context_object_type: null,
  context_object_id: null,
  $set_once: {
    entry_point: entryPoint,
    first_referrer: document.referrer || null,
    first_landing_url: window.location.href,
  },
});

// Account Created — fires after role selection + server confirms
posthog.capture('Account Created', {
  action: 'click',
  action_value: 'continue_as_hiring_manager_button',
  current_page_context: 'onboarding/role_selection',
  previous_page_context: 'auth/landing',
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  context_object_type: null,
  context_object_id: null,
  persona: 'hiring_manager',
  signup_context: entryPoint,
  auth_method: 'google',
  $set_once: {
    first_persona: 'hiring_manager',
    entry_point: entryPoint,
    account_created_at: new Date().toISOString(),
  },
});

// Intro Completed — fires on "Let's go" click
posthog.capture('Intro Completed', {
  action: 'click',
  action_value: 'lets_go_button',
  current_page_context: 'onboarding/intro',
  previous_page_context: 'onboarding/role_selection',
  entry_point: null,
  entity_type: 'onboarding',
  component: 'onboarding_intro_footer_cta',
  context_object_type: null,
  context_object_id: null,
});
```

### Identifying a user (JS SDK — after auth succeeds)

```javascript
// Called in identifyUser() after login/session restore
// Uses positional args: (distinctId, $set, $set_once)
const persona = ROLE_TO_PERSONA[user.role] || 'unknown';
posthog.identify(user.id,
  { email: user.email, name: user.name, org_id: user.orgId, current_persona: persona },
  { account_created_at: user.createdAt }
);
```

### Prospect event

```javascript
posthog.capture('Custom Link Created', {
  link_name: 'Google SWE Application',
  is_job_specific: true,
  target_job_title: 'Software Engineer',
  target_company: 'Google'
});
```

### Hiring event (with job group)

```javascript
posthog.group('job', jobId);
posthog.capture('Team Member Invited', {
  job_id: jobId,
  invited_role_label: 'recruiter',
  invite_method: 'email'
});
```

### Viral loop event — Python SDK (backend)

```python
# Python SDK uses $set/$set_once inside properties dict
posthog.capture(
    event='Account Created',
    distinct_id=str(new_user.id),
    properties={
        'signup_context': 'job_link',
        'referred_by': referrer_user_id,
        'referrer_job_id': job_id,
        '$set_once': {'referred_by': referrer_user_id}
    }
)
```

### Intent vs outcome pair

```javascript
// Intent (fired on button click)
posthog.capture('Share Button Clicked', {
  job_id: jobId,
  share_source: 'dashboard'
});

// Outcome - success (fired on server confirmation)
posthog.capture('Job Shared', {
  job_id: jobId,
  share_channel: 'email',
  shared_by_user_id: user.id
});

// Outcome - failure (fired on error)
posthog.capture('Job Share Failed', {
  job_id: jobId,
  error_reason: 'network_error',
  error_category: 'network'
});
```

---

## Intent vs Outcome Pattern

For critical flows, track the UI interaction (intent) and the server-confirmed result (outcome) as separate events. This isolates frontend UX issues from backend failures in funnel analysis.

| Flow | Intent Event | Success Event | Failure Event |
|------|-------------|---------------|---------------|
| Login / Signup | Login Started | Account Created (new) or Login Succeeded (returning) | Login Cancelled, Login Failed |
| Sharing a job | Share Button Clicked | Job Shared | Job Share Failed |
| Expressing interest | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed |
| Inviting team member | Invite Button Clicked | Team Member Invited | Team Member Invite Failed |
| Creating a job | Create Job Button Clicked | Job Created | Job Creation Failed |
| Recording intro video | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed |
