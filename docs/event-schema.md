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
4. **No special characters or trailing spaces** — Letters, numbers, and spaces only. No `/`, `&`, `@`, `#` or other special characters.
5. **Separate intent from outcome** — Track the user's action (intent) and whether it succeeded or failed:
   - Intent: `Share Button Clicked`
   - Success: `Job Shared`
   - Failure: `Job Share Failed`
6. **Intent events use present tense** — Intent events follow the pattern
   `[Action] [Object] Button Clicked` where the action is present tense:
   `Share Button Clicked`, `Create Job Button Clicked`,
   `Record Video Button Clicked`. This is exception to the past-tense rule.
7. **Event naming should be descriptive and meaningful** — Event name should represent intent.
   `Account Created`, `Create Job Button Clicked`,
   `Record Video Button Clicked`. This is exception to the past-tense rule.

### Property Names: snake_case

All event and person properties use `snake_case`: `job_id`, `current_persona`, `signup_context`, `share_channel`. No Proper Case or camelCase for properties.

For `current_page_context` and `previous_page_context` values, use underscores for hierarchy: `hm_job_creation_wizard_interview_questions`, `onboarding_role_selection`. URL paths must be transformed to snake_case — strip the leading `/`, replace `/` and `-` with `_` (e.g., `/onboarding/role-selection` → `onboarding_role_selection`).

### Standard Objects

These are the canonical object names for Helix. Always use these exact names in events.

| Object | Entity | Example Events |
|--------|--------|---------------|
| Page | Any meaningful product page/screen | Page Viewed |
| Auth | Authentication and session lifecycle | Auth Login Succeeded, Auth Login Failed, Auth Session Restore Succeeded, Auth Session Restore Failed, Auth Refresh Failed, Auth Logout Completed, Auth Email Verified, Auth Email Verify Failed |
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
| Persona | User persona (hiring_manager, recruiter, job_seeker) | Persona Activated |
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

**Setting job group properties (Python SDK — backend):**

```python
posthog.group_identify('job', str(job.id), {
    'job_title': job.title,
    'job_status': job.status,                        # draft, open, closed, archived
    'job_visibility': job.visibility,                 # private, public
    'job_type': job.type,                             # ai_job_flow (extensible for future types)
    'work_type': job.work_type,                       # remote, hybrid, onsite
    'location': job.location,
    'seniority_level': job.seniority_level,           # junior, mid, senior, staff, etc.
    'hiring_manager_user_id': str(job.hiring_manager_user_id) if job.hiring_manager_user_id else None,
    'created_by_user_id': str(job.created_by_user_id),
    'created_at': job.created_at.isoformat(),
    'is_intro_video_recorded': job.is_intro_video_recorded,
    'team_size': len(job.access_list),                # number of collaborators on the job
    'ats_source': job.ats_source,                     # external ATS integration source
})
```

Call `group_identify` on job creation with all known properties. On subsequent changes (publish, archive, status update, team change), call it again with the updated fields — PostHog merges properties additively, so you only need to send what changed.

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
| `referred_by` | UUID | user ID | Account Created (backend) | User ID of referrer. |

#### `$set` — Updated on every login

| Property | Type | Set By | Description |
|----------|------|--------|-------------|
| `email` | string | `identifyUser()` | User's current email |
| `name` | string | `identifyUser()` | User's current name |
| `org_id` | string | `identifyUser()` | User's current organization ID |
| `org_name` | string | `identifyUser()` | User's current organization name. Resolved from org_id on backend before identify call. |
| `org_domain` | string | `identifyUser()` | User's organization domain (e.g., `seekout.com`). Resolved from org_id on backend before identify call. |
| `current_persona` | enum | `identifyUser()` + persona switch | Active persona — `hiring_manager`, `recruiter`, `job_seeker`. Updated on every login and on persona switch via sidebar toggle. |
| `activated_personas` | array | Persona Activated | All unique personas the user has tried. Grows over time as new personas are activated. |

**Three persona properties, three purposes:** `first_persona` (`$set_once`) preserves what the user originally chose during onboarding. `current_persona` (`$set`) changes whenever the user switches roles. `activated_personas` (`$set`) accumulates every persona the user has tried over time — it only grows, never shrinks.

**Identifying a user (JS SDK — called after auth succeeds):**

```javascript
// In lib/posthog.ts → identifyUser()
const persona = ROLE_TO_PERSONA[user.role] || 'unknown';
posthog.identify(user.id,
  { email: user.email, name: user.name, org_id: user.orgId, org_name: user.orgName, current_persona: persona },  // $set
  { account_created_at: user.createdAt }  // $set_once
);
```

**Setting first-touch attribution (JS SDK — fires on Login Started, before auth):**

```javascript
// In pages/SignUp.tsx → handleLogin()
posthog.capture('Login Started', {
  action: 'click',
  action_value: 'continue_with_google_or_email_button',
  current_page_context: 'auth_landing',
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
```

**Setting first_persona (JS SDK — fires on Account Created, after role selection):**

```javascript
// In pages/RoleSelection.tsx → handleContinue()
posthog.capture('Account Created', {
  action: 'click',
  action_value: 'continue_as_hiring_manager_button',  // or continue_as_recruiter_button, continue_as_job_seeker_button
  current_page_context: 'onboarding_role_selection',
  previous_page_context: previousPageContext,  // stored from last page view, transformed to snake_case
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  context_object_type: null,
  context_object_id: null,
  persona,
  $set_once: {
    first_persona: persona,
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

> **Note:** The user's active persona is tracked via the `current_persona` person property (`$set`), which is automatically available on all events. No need to pass persona per-event.

---

## Sample Event Calls

### Login & onboarding events (JS SDK — frontend)

```javascript
// getPreviousPageContext() returns the last page viewed, transformed to snake_case.
// On first page load (no previous page), it returns null.

// Page Viewed — fires on page mount
posthog.capture('Page Viewed', {
  current_page_context: 'auth_landing',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
});

// Login Started — fires on CTA click, before auth
const searchParams = new URLSearchParams(window.location.search);
const entryPoint = searchParams.get('context') || 'direct';

posthog.capture('Login Started', {
  action: 'click',
  action_value: 'continue_with_google_or_email_button',
  current_page_context: 'auth_landing',
  previous_page_context: getPreviousPageContext(),
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
  action_value: 'continue_as_hiring_manager_button',  // or continue_as_recruiter_button, continue_as_job_seeker_button
  current_page_context: 'onboarding_role_selection',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  entity_type: 'onboarding',
  component: 'onboarding_role_selection_footer_cta',
  context_object_type: null,
  context_object_id: null,
  persona: 'hiring_manager',
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
  current_page_context: 'onboarding_intro',
  previous_page_context: getPreviousPageContext(),
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
  { email: user.email, name: user.name, org_id: user.orgId, org_name: user.orgName, current_persona: persona },  // $set
  { account_created_at: user.createdAt }  // $set_once
);
```

### Prospect event (Python SDK — backend)

```python
posthog.capture(
    event='Custom Link Created',
    distinct_id=str(user.id),
    properties={
        'link_type': 'general',
        'link_name': 'Google SWE Application',
        'is_job_specific': True,
    }
)
```

### Hiring event with job group (Python SDK — backend)

```python
posthog.capture(
    event='Team Member Invited',
    distinct_id=str(user.user_id),
    properties={
        'job_id': str(job_id),
        'invited_role_label': 'hiring_manager',
        'invite_method': 'email',
    },
    groups={'job': str(job_id)},
)
```

### Viral loop attribution — setting referred_by (Python SDK — backend)

```python
# When a referred user signs up, set referred_by as a person property
posthog.capture(
    event='$set',
    distinct_id=str(new_user.id),
    properties={
        '$set_once': {'referred_by': str(referrer_user_id)},
    }
)
```

### Intent vs outcome pair

```javascript
// Intent (fired on button click — frontend)
posthog.capture('Share Button Clicked', {
  action: 'click',
  action_value: 'share_job_button',
  current_page_context: 'hiring_manager_job_postings',
  previous_page_context: null,
  entry_point: null,
  entity_type: 'job',
  component: 'job_card',
  context_object_type: 'job',
  context_object_id: jobId,
});
```

```python
# Outcome - success (fired on server confirmation — backend)
posthog.capture(
    event='Job Shared',
    distinct_id=str(user.user_id),
    properties={
        'job_id': str(job_id),
        'shared_by_user_id': str(user.user_id),
        'share_channel': 'email',
    },
    groups={'job': str(job_id)},
)

# Outcome - failure (fired on error — backend)
posthog.capture(
    event='Job Share Failed',
    distinct_id=str(user.user_id),
    properties={
        'job_id': str(job_id),
        'error_reason': str(e),
    },
    groups={'job': str(job_id)},
)
```

---

## Intent vs Outcome Pattern

For critical flows, track the UI interaction (intent) and the server-confirmed result (outcome) as separate events. This isolates frontend UX issues from backend failures in funnel analysis.

| Flow | Intent Event | Success Event | Failure Event |
|------|-------------|---------------|---------------|
| Login / Signup | Login Started | Account Created (new) or Auth Login Succeeded (returning) | Login Cancelled, Auth Login Failed |
| Sharing a job | Share Button Clicked | Job Shared | Job Share Failed |
| Expressing interest | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed |
| Inviting team member | Invite Button Clicked | Team Member Invited | Team Member Invite Failed |
| Creating a job | Create Job Button Clicked | Job Created | Job Creation Failed |
| Switching persona | Persona Switch Chevron Clicked | Persona Switched | -- |
| Phone collection | Auth Phone Submitted | *(implicit — accepted)* | Auth Phone Submit Failed |
| Email verification | Auth Email Verify Code Sent | Auth Email Verified | Auth Email Verify Failed |
| Session restore | *(implicit — on app load)* | Auth Session Restore Succeeded | Auth Session Restore Failed |
| Recording intro video | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed |
