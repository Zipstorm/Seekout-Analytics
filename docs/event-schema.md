---
confluence:
  page_id: "1749319717"
  space_id: "Helix"
  parent_id: "1749745665"
---

# Helix Analytics Events Schema

**Product:** Helix (SeekOut.ai)  
**Analytics Platform:** PostHog  
**Last Updated:** March 2026

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

All event and person properties use `snake_case`: `job_id`, `acting_as`, `signup_context`, `share_channel`. No Proper Case or camelCase for properties.

### Standard Objects

These are the canonical object names for Helix. Always use these exact names in events.

| Object | Entity | Example Events |
|--------|--------|---------------|
| Account | User (account-level actions) | Account Created, Account Activated |
| Signup | Signup flow | Signup Started |
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
| Persona | User persona selection | Persona Selected |
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

Set on identify. Describe the user across all events.

| Property | Type | Method | Values | Description |
|----------|------|--------|--------|-------------|
| `signup_context` | enum | `$set_once` | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite` | How user arrived. Immutable. |
| `first_surface` | enum | `$set_once` | `prospect`, `hiring` | First activated surface. Immutable. |
| `activated_surfaces` | array | `$set` | `["prospect"]`, `["prospect", "hiring"]` | Currently activated surfaces. Grows over time. |
| `referred_by` | UUID | `$set_once` | user ID | User ID of referrer. Immutable. |
| `account_created_at` | ISO date | `$set_once` | | Account creation timestamp |
| `persona` | enum | `$set_once` | `hiring_manager`, `recruiter`, `job_seeker` | User persona selected during onboarding. Immutable. |

**Role is NOT a person property.** The same user has different roles on different jobs. Role is always sent as an event property (`acting_as`).

**Identifying a user and setting person properties:**

```javascript
posthog.identify(user.id, {
  $set_once: {
    signup_context: 'job_link',
    first_surface: 'prospect',
    referred_by: referrerUserId,
    account_created_at: new Date().toISOString()
  },
  $set: {
    activated_surfaces: ['prospect']
  }
});
```

### Standard Event Properties

Include on every event where applicable.

| Property | Type | Values | When to Include |
|----------|------|--------|----------------|
| `surface` | enum | `prospect`, `hiring` | All authenticated events (exclude Anonymous User Events and Persona Selected) |
| `acting_as` | enum | `hiring_manager`, `recruiter`, `team_member` | All hiring surface events (except Team Member Joined) |
| `job_id` | UUID | | All job-related events |

**Pre-activation flows:** During onboarding (before surface activation), set
`surface` to the surface the user is currently engaging with. For the job
creation wizard, use `hiring`. For Persona Selected, omit `surface` — persona
selection happens before any surface context exists.

---

## Sample Event Calls

### Prospect surface event

```javascript
posthog.capture('Custom Link Created', {
  surface: 'prospect',
  link_name: 'Google SWE Application',
  is_job_specific: true,
  target_job_title: 'Software Engineer',
  target_company: 'Google'
});
```

### Hiring surface event (with job group and acting_as)

```javascript
posthog.group('job', jobId);
posthog.capture('Team Member Invited', {
  surface: 'hiring',
  acting_as: 'hiring_manager',
  job_id: jobId,
  invited_role_label: 'recruiter',
  invite_method: 'email'
});
```

### Viral loop event (with referral attribution)

```python
posthog.capture(
    distinct_id=new_user.id,
    event='Account Created',
    properties={
        'surface': 'prospect',
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
  surface: 'hiring',
  acting_as: 'hiring_manager',
  job_id: jobId,
  share_source: 'dashboard'
});

// Outcome - success (fired on server confirmation)
posthog.capture('Job Shared', {
  surface: 'hiring',
  acting_as: 'hiring_manager',
  job_id: jobId,
  share_channel: 'email',
  shared_by_user_id: user.id
});

// Outcome - failure (fired on error)
posthog.capture('Job Share Failed', {
  surface: 'hiring',
  acting_as: 'hiring_manager',
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
| Sharing a job | Share Button Clicked | Job Shared | Job Share Failed |
| Expressing interest | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed |
| Inviting team member | Invite Button Clicked | Team Member Invited | Team Member Invite Failed |
| Creating a job | Create Job Button Clicked | Job Created | Job Creation Failed |
| Recording intro video | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed |
| Signing up | Signup Started | Account Created | -- |
