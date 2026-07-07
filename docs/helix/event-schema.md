---
confluence:
  page_id: "1749319717"
  space_id: "Helix"
  parent_id: "1749745665"
analytics_platform: posthog
group_property_rules:
  - group: job
    property: job_id
    catalog_warning_types: [Interaction, Rejected]
    tracking_plan_severity: warning
area_property_rules:
  - area_contains: viral
    property: referrer_user_id
persona_rules:
  - section_contains: hiring
    property: acting_as
    applies_if_in_schema: true
---

# Helix Analytics Events Schema

**Product:** Helix (SeekOut.ai)  
**Analytics Platform:** PostHog  
**Last Updated:** July 2026

For the event catalog and implementation status, see [Helix Analytics Events Tracker](./event-catalog.md).
For dashboards and funnel mappings, see [Helix Analytics Dashboards & Funnels](./dashboards.md).
For shared naming conventions and event types, see [Shared Analytics Naming and Event Types](../shared/naming-and-event-types.md).

---

## Shared Naming Conventions and Event Types

Naming conventions, property-name casing, and the Event Types enum are shared across products in [Shared Analytics Naming and Event Types](../shared/naming-and-event-types.md). The validator reads the shared Event Types table for Rule 17 / TP12.

## Standard Objects

These are the canonical object names for Helix. Always use these exact names in events.

| Object | Entity | Example Events |
|--------|--------|---------------|
| Page | Any meaningful product page/screen | Page Viewed |
| Auth | Authentication and session lifecycle | Auth Login Succeeded, Auth Login Rejected, Auth Session Restore Succeeded, Auth Session Restore Errored |
| Login Started Button | Auth CTA buttons on signup/signin pages | Login Started Button Clicked |
| Account | User (account-level actions) | Account Activated |
| Account Create | User account creation | Account Create Succeeded |
| Onboarding Intro Complete Button | Onboarding intro "Let's go" button | Onboarding Intro Complete Button Clicked |
| Onboarding Persona Card | Persona selection card on onboarding page | Onboarding Persona Card Clicked |
| Onboarding Complete | Full onboarding flow lifecycle | Onboarding Complete Succeeded |
| Auth Login | Authentication login lifecycle | Auth Login Rejected |
| Auth Email Verify Code Send | Email OTP dispatch lifecycle | Auth Email Verify Code Send Succeeded, Auth Email Verify Code Send Errored |
| Auth Email Verify | Email verification lifecycle | Auth Email Verify Succeeded, Auth Email Verify Rejected |
| Auth Logout | Logout lifecycle | Auth Logout Succeeded |
| Auth Session Restore | Session restore lifecycle | Auth Session Restore Errored |
| Auth Refresh | Token refresh lifecycle | Auth Refresh Errored |
| Profile | Prospect's career profile | Profile Section Updated |
| Job | Job posting | Job Posting Draft Created, Job Shared |
| Interest | Expression of Interest | Interest Expressed, Interest Reviewed |
| Review | Interest Review | Review Decision Made |
| Team Member | JobTeamMember | Team Member Invited, Team Member Joined |
| Custom Link | Prospect's named shareable link (general or job-specific) | Custom Link Added, Custom Link Shared |
| Career Coach | AI Career Coach agent | Career Coach Session Started |
| Persona | User persona (hiring_manager, recruiter, job_seeker) | Switch Persona Button Clicked, Persona Updated |
| Job Link | Shared job posting link viewed by anonymous visitors | Job Link Viewed, Job Link Engaged |
| Profile Link | Prospect's shareable profile link viewed by visitors | Profile Link Viewed, Profile Link Engaged |
| Job Post Wizard | Job creation wizard session | Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Description Evaluated, Job Description Evaluation Failed, Job Description Details Toggled, Job Description Field Edited, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Post Wizard Back Button Clicked |
| Job Posting | Job posting lifecycle (draft, verified, published) | Job Posting Draft Created, Job Posting Verified, Job Posting Published |
| Job Description | Job description content | Job Description Evaluated, Job Description Evaluation Failed |
| Job Description Details | Extracted job description details card | Job Description Details Toggled |
| Job Description Field | Editable AI-extracted field | Job Description Field Edited |
| Sam Session | AI hiring partner session lifecycle | Sam Session Started, Sam Session Setup Failed, Sam Session Ended |
| Role Requirement | Role requirement question | Role Requirement Deleted, Role Requirement Edited, Role Requirement Added |
| Screening Question | Interview screening question | Screening Question Deleted, Screening Question Edited, Screening Question Added |
| Success Page Share | Share section on wizard success page | Success Page Share Button Clicked |
| Job Share Message | Share message content | Job Share Message AI Refined, Job Share Message Copied |
| Job Share Channel | Share distribution channel | Job Share Channel Clicked |
| Invite Teammates | Invite teammates action on success page | Invite Teammates Button Clicked |
| Team Member Invite | Team member invitation | Team Member Invite Sent |
| Job Posting Page | Job posting detail page link | Job Posting Page Link Clicked |
| Job Verification Code | Email verification code | Job Verification Code Send Button Clicked |
| Screening Configuration | Job screening setup | Screening Configuration Saved |
| Intro Video | HM intro video recording | Intro Video Created, Intro Video Deleted |
| Candidate | Candidate in review pipeline | Candidate Viewed, Candidate Tab Viewed, Candidate Recording Played |
| Requirement | AI-generated role requirement | Requirement Add Button Clicked |
| Question | AI-generated interview question | Question Add Button Clicked |
| Intro Script | Intro video script | Intro Script Updated |
| Chat | Chat/WebSocket connection for messaging | Chat WebSocket Connected, Chat WebSocket Error |
| Profile Photo | User's profile headshot image | Add Profile Photo Button Clicked, Profile Photo Upload Failed, Candidate Profile Photo Remove Button Clicked |
| Profile Photo Add | Profile photo upload lifecycle | Profile Photo Add Succeeded |
| LinkedIn Export | LinkedIn export help link | LinkedIn Export Learn How Link Clicked |
| Build Profile | AI profile generation process | Build Profile Button Clicked |
| Candidate Profile Create | Portfolio creation lifecycle | Candidate Profile Create Succeeded, Candidate Profile Create Errored |
| Handle Claim | Handle claim lifecycle | Handle Claim Succeeded, Handle Claim Rejected |
| Candidate Previous Resume Select Button | Previous resume select CTA | Candidate Previous Resume Select Button Clicked |
| Candidate Custom Link Delete | Custom link deletion lifecycle | Candidate Custom Link Delete Succeeded, Candidate Custom Link Delete Errored |
| Candidate Custom Link Delete Button | Custom link delete CTA | Candidate Custom Link Delete Button Clicked |
| Candidate Profile Overview Load | Profile overview load state | Candidate Profile Overview Load Succeeded |
| Candidate Profile Tab | Editor tab navigation | Candidate Profile Tab Switched |
| Candidate Resume Download | Resume download action | Candidate Resume Download Succeeded |
| Candidate Portfolio Publish | Portfolio publish lifecycle | Candidate Portfolio Publish Succeeded, Candidate Portfolio Publish Errored |
| Candidate Portfolio Publish Button | Portfolio publish CTA | Candidate Portfolio Publish Button Clicked |
| Candidate Portfolio Unpublish | Portfolio unpublish lifecycle | Candidate Portfolio Unpublish Succeeded |
| Candidate Portfolio Unpublish Button | Portfolio unpublish CTA | Candidate Portfolio Unpublish Button Clicked |
| Change Profile Photo Button | Change profile photo CTA | Change Profile Photo Button Clicked |
| Candidate Profile Photo Remove | Profile photo removal lifecycle | Candidate Profile Photo Remove Succeeded, Candidate Profile Photo Remove Errored |
| Candidate Profile Photo Remove Button | Profile photo remove CTA | Candidate Profile Photo Remove Button Clicked |
| Candidate Portfolio Create Button | Portfolio creation CTA on dashboard | Candidate Portfolio Create Button Clicked |
| Candidate Portfolio Rename | Portfolio rename lifecycle | Candidate Portfolio Rename Succeeded |
| Candidate Portfolio Rename Button | Portfolio rename CTA | Candidate Portfolio Rename Button Clicked |
| Candidate Portfolio Delete | Portfolio delete lifecycle | Candidate Portfolio Delete Succeeded |
| Candidate Portfolio Delete Button | Portfolio delete CTA | Candidate Portfolio Delete Button Clicked |
| Candidate Resume Upload | Resume upload in create-profile context | Candidate Resume Upload Button Clicked, Candidate Resume Upload Succeeded, Candidate Resume Upload Rejected, Candidate Resume Upload Errored |
| Candidate Resume Remove Button | Resume remove CTA | Candidate Resume Remove Button Clicked |
| Candidate Profile Custom Link Add | Custom link add lifecycle | Candidate Profile Custom Link Add Succeeded |
| Get Started Interview Button | Interview landing CTA | Get Started Interview Button Clicked |
| Candidate Interview Info Next Button | Interview info form CTA | Candidate Interview Info Next Button Clicked |
| What To Expect Link | Interview info expander | What To Expect Link Clicked |
| Candidate Interview Resume Next Button | Resume step CTA | Candidate Interview Resume Next Button Clicked |
| Candidate Interview Resume Upload | Resume upload lifecycle in interview | Candidate Interview Resume Upload Succeeded, Candidate Interview Resume Upload Errored |
| Open Identity Check Link | Open identity check CTA | Open Identity Check Link Clicked |
| Refresh Status Button | Refresh identity check status CTA | Refresh Status Button Clicked |
| Candidate Interview Identity Verification | Third-party identity verification lifecycle | Candidate Interview Identity Verification Succeeded, Candidate Interview Identity Verification Errored, Candidate Interview Identity Verification Rejected |
| Candidate Interview Identity Verification Auto Redirect | Auto-redirect after verification | Candidate Interview Identity Verification Auto Redirect Succeeded, Candidate Interview Identity Verification Auto Redirect Errored, Candidate Interview Identity Verification Auto Redirect Rejected |
| Candidate Interview Identity Verification Continue Button | Continue after verification CTA | Candidate Interview Identity Verification Continue Button Clicked |
| Candidate Interview Privacy Email Link | Privacy email link | Candidate Interview Privacy Email Link Clicked |
| Candidate Interview Persona Privacy Policy Link | Persona privacy policy link | Candidate Interview Persona Privacy Policy Link Clicked |
| Candidate Interview Screening Response Next Button | Screening next CTA | Candidate Interview Screening Response Next Button Clicked |
| Candidate Interview Screening Response Submit | Screening response submission | Candidate Interview Screening Response Submit Succeeded |
| Candidate Interview Screening Response Save And Review Button | Screening save-and-review CTA | Candidate Interview Screening Response Save And Review Button Clicked |
| Allow Device Access Button | Camera/mic permission CTA | Allow Device Access Button Clicked |
| Device Access Grant | Camera/mic grant result | Device Access Grant Succeeded |
| Device Access | Camera/mic permission rejection | Device Access Rejected |
| Candidate Interview Start Button | Start interview CTA | Candidate Interview Start Button Clicked |
| Candidate Interview | Anonymous AI screening interview session | Candidate Interview Started |
| Candidate Interview Question Answer | Per-question answer result | Candidate Interview Question Answer Succeeded |
| Candidate Interview Question Restart | Question restart lifecycle | Candidate Interview Question Restart Succeeded, Candidate Interview Question Restart Errored |
| Candidate Interview Question Restart Button | Question restart CTA | Candidate Interview Question Restart Button Clicked |
| Candidate Interview Question Skip | Question skip lifecycle | Candidate Interview Question Skip Succeeded, Candidate Interview Question Skip Errored, Candidate Interview Question Skip Rejected |
| Candidate Interview Question Skip Button | Question skip CTA | Candidate Interview Question Skip Button Clicked |
| Candidate Interview Screening Response Edit Button | Screening answer edit link | Candidate Interview Screening Response Edit Button Clicked |
| Candidate Interview Review Answer Button | Answer skipped question on review | Candidate Interview Review Answer Button Clicked |
| Candidate Interview Retake Question Button | Retake question on review | Candidate Interview Retake Question Button Clicked |
| Candidate Interview Review Answer Expand | Answer card expand on review | Candidate Interview Review Answer Expand Clicked |
| Candidate Interview Answers Submit | End-of-recording submission | Candidate Interview Answers Submit Succeeded |
| Candidate Interview Answer Retake | Retake completion result | Candidate Interview Answer Retake Succeeded |
| Candidate Interview Screening Response Edit | Screening edit completion | Candidate Interview Screening Response Edit Succeeded |
| Candidate Interview Submit | Full interview submission lifecycle | Candidate Interview Submit Succeeded, Candidate Interview Submit Rejected |

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
| `entry_point` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct` | Page Viewed (auth page) | First-touch attribution — how user originally found Helix. Derived from `?context=` URL param. Set on auth page so even abandoners are attributed. |
| `first_referrer` | string | URL or null | Page Viewed (auth page) | HTTP referrer at first visit (`document.referrer`). |
| `first_landing_url` | string | URL | Page Viewed (auth page) | Full landing URL including query params at first visit. |
| `first_persona` | enum | `hiring_manager`, `recruiter`, `job_seeker` | Account Create Succeeded, Onboarding Complete Succeeded | First persona chosen during onboarding. Never changes even if user switches role later. |
| `account_created_at` | ISO date | | Account Create Succeeded | Account creation timestamp. |
| `referred_by` | UUID | user ID | Account Create Succeeded (backend) | User ID of referrer. |
| `signup_context` | enum | `job_link`, `direct_prospect`, `direct_hiring`, `team_invite`, `direct` | Team Member Joined | Signup context captured when an invited team member first joins a job. |

#### `$set` — Updated on every login

| Property | Type | Set By | Description |
|----------|------|--------|-------------|
| `email` | string | `identifyUser()` | User's current email |
| `name` | string | `identifyUser()` | User's current name |
| `role` | string | `identifyUser()` | User's current role enum (e.g., `HIRING_MANAGER`, `RECRUITER`, `PROFESSIONAL`) |
| `org_id` | string | `identifyUser()` | User's current organization ID |
| `current_persona` | enum | Account Create Succeeded, Persona Updated, `identifyUser()`, `posthog.register()` (super-property) | Active persona — `hiring_manager`, `recruiter`, `job_seeker`. Set on account creation, updated on persona switch and every login. Also registered as a PostHog super-property via `posthog.register()` inside `identifyUser()`, so it automatically rides on every frontend `capture()` call. |
| `activated_personas` | array | Account Create Succeeded, Persona Updated | All unique personas the user has ever been in. Seeded with `[current_persona]` on Account Create Succeeded, grows as user switches personas via Persona Updated. DB column and PostHog person property are now in sync. |

**Three persona properties, three purposes:** `first_persona` (`$set_once`) preserves what the user originally chose during onboarding. `current_persona` (`$set`) is set on Account Create Succeeded and `identifyUser()` (every login), updated on persona switch via Persona Updated, and registered as a super-property via `posthog.register()` so it rides on all frontend events. `activated_personas` (`$set`) is seeded with `[current_persona]` on Account Create Succeeded and accumulates every persona the user has tried via Persona Updated — it only grows, never shrinks. Both DB column and PostHog person property stay in sync.

**Identifying a user (JS SDK — called after auth succeeds):**

```javascript
// In lib/posthog.ts → identifyUser()
const currentPersona = user.role ? (ROLE_TO_PERSONA[user.role] ?? 'unknown') : null;
posthog.identify(user.id,
  { email: user.email, name: user.name, role: user.role, org_id: user.orgId, current_persona: currentPersona },  // $set
  { account_created_at: user.createdAt }  // $set_once
);
```

**Setting first-touch attribution (JS SDK — fires on Page Viewed for auth pages, before any interaction):**

```javascript
// In pages/SignUp.tsx — Page Viewed on mount
posthog.capture('Page Viewed', {
  current_page_context: 'auth_signup',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  $set_once: {
    entry_point: entryPoint,
    first_referrer: document.referrer || null,
    first_landing_url: window.location.href,
  },
});
```

**Setting first_persona (JS SDK — fires on Account Create Succeeded, after role selection):**

```javascript
// In pages/RoleSelection.tsx → handleContinue()
posthog.capture('Account Create Succeeded', {
  current_persona: 'hiring_manager',  // or 'recruiter', 'job_seeker'
  auth_method: 'google',  // or 'microsoft', 'email'
  $set: {
    current_persona: 'hiring_manager',
    activated_personas: ['hiring_manager'],
  },
  $set_once: {
    first_persona: 'hiring_manager',
    account_created_at: new Date().toISOString(),
  },
});
```

### Standard Event Properties

Include on every event where applicable.

| Property | Type | Values | When to Include |
|----------|------|--------|----------------|
| `current_page_context` | string | snake_case page identifier | All frontend events |
| `previous_page_context` | string | snake_case page identifier or null | All frontend events |
| `entity_type` | string | `account`, `onboarding`, `job`, `persona`, etc. | All frontend events (`user_action` and `page_view`) |
| `action` | enum | `click`, `submit`, `toggle` | All `user_action` events |
| `action_value` | string | exact UI button/link text in snake_case | All `user_action` events |
| `component` | string | snake_case UI container identifier | All `user_action` events |
| `job_id` | UUID | alphanumeric or number | All job-related events |

> **Note:** The user's active persona is tracked via the `current_persona` person property (`$set`). Backend events also include `current_persona` as an explicit event property to guarantee availability without `$set` propagation delay.

---

## Sample Event Calls

### Login & onboarding events (JS SDK — frontend)

```javascript
// getPreviousPageContext() returns the last page viewed, transformed to snake_case.
// On first page load (no previous page), it returns null.

// Page Viewed — fires on page mount (auth pages also set $set_once attribution)
posthog.capture('Page Viewed', {
  current_page_context: 'auth_signup',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  $set_once: {
    entry_point: entryPoint,
    first_referrer: document.referrer || null,
    first_landing_url: window.location.href,
  },
});

// Login Started Button Clicked — fires on CTA click, before auth
const searchParams = new URLSearchParams(window.location.search);
const entryPoint = searchParams.get('context') || 'direct';

posthog.capture('Login Started Button Clicked', {
  action: 'click',
  action_value: 'sign_up_with_google_button',
  current_page_context: 'auth_signup',
  previous_page_context: getPreviousPageContext(),
  entry_point: entryPoint,
  auth_method: 'google',
  entity_type: 'account',
  component: 'auth_signup_card_cta',
});

// Account Create Succeeded — fires after role selection + server confirms
posthog.capture('Account Create Succeeded', {
  current_persona: 'hiring_manager',
  auth_method: 'google',
  $set: {
    current_persona: 'hiring_manager',
    activated_personas: ['hiring_manager'],
  },
  $set_once: {
    first_persona: 'hiring_manager',
    account_created_at: new Date().toISOString(),
  },
});

// Onboarding Intro Complete Button Clicked — fires on "Let's go" click
posthog.capture('Onboarding Intro Complete Button Clicked', {
  action: 'click',
  action_value: 'lets_go_button',
  current_page_context: 'onboarding_intro',
  previous_page_context: getPreviousPageContext(),
  entity_type: 'onboarding',
  component: 'onboarding_intro_footer_cta',
});
```

### Identifying a user (JS SDK — after auth succeeds)

```javascript
// Called in identifyUser() after login/session restore
// Uses positional args: (distinctId, $set, $set_once)
const currentPersona = user.role ? (ROLE_TO_PERSONA[user.role] ?? 'unknown') : null;
posthog.identify(user.id,
  { email: user.email, name: user.name, role: user.role, org_id: user.orgId, current_persona: currentPersona },  // $set
  { account_created_at: user.createdAt }  // $set_once
);
// Register current_persona as a super-property so it rides on all subsequent capture() calls
posthog.register({ current_persona: currentPersona });
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

### Interaction vs result pair

```javascript
// Interaction (fired on button click — frontend)
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
# Result - success (fired on server confirmation — backend)
posthog.capture(
    event='Job Share Succeeded',
    distinct_id=str(user.user_id),
    properties={
        'job_id': str(job_id),
        'shared_by_user_id': str(user.user_id),
        'share_channel': 'email',
    },
    groups={'job': str(job_id)},
)

# Result - rejected (fired when the system rejects the request — backend)
posthog.capture(
    event='Job Share Rejected',
    distinct_id=str(user.user_id),
    properties={
        'job_id': str(job_id),
        'error_reason': str(e),
        'error_category': 'network',  # network, permission, validation, server, timeout
    },
    groups={'job': str(job_id)},
)
```

---

## Interaction / Started / Result Pattern

For critical flows, track the UI interaction or process start separately from the processed result. This isolates frontend UX issues from rejected requests and technical errors in funnel analysis.

Current catalog examples that still use old result terminals or non-result names are deferred rename debt. New or renamed result events must use `Succeeded`, `Rejected`, or `Errored`.

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|------|-----------------------------|---------------|----------------|-------------|
| Login / Signup | Login Started Button Clicked | Account Create Succeeded (new) or Auth Login Succeeded (returning) | Auth Login Rejected | -- |
| Sharing a job | Share Button Clicked | Job Shared | Job Share Failed | -- |
| Expressing interest | Express Interest Button Clicked | Interest Expressed | Interest Expression Failed | -- |
| Inviting team member | Invite Button Clicked | Team Member Invited | Team Member Invite Failed | -- |
| Creating a job (wizard start) | Create Job Button Clicked, Job Post Wizard Started | -- | -- | -- |
| Creating a job (draft save) | Job Post Wizard Job Details Completed | Job Posting Draft Created | Job Creation Failed | -- |
| Email verification (job) | Job Verification Code Send Button Clicked | Job Posting Verified | -- | -- |
| Publishing a job (verified) | Job Post Wizard Verification Completed | Job Posting Published | -- | -- |
| Publishing a job (skipped) | Job Post Wizard Verification Skipped | Job Posting Published | -- | -- |
| Email verification | -- | Auth Email Verify Code Send Succeeded | Auth Email Verify Rejected | Auth Email Verify Code Send Errored |
| Session restore | *(implicit — on app load)* | Auth Session Restore Succeeded | -- | Auth Session Restore Errored |
| Recording intro video | Record Video Button Clicked | Intro Video Created | Intro Video Creation Failed | -- |
| Persona switch | Switch Persona Button Clicked | Persona Updated | Persona Update Failed | -- |
| Resume upload | Candidate Resume Upload Button Clicked | Candidate Resume Upload Succeeded | Candidate Resume Upload Rejected | Candidate Resume Upload Errored |
| Profile photo upload | Add Profile Photo Button Clicked | Profile Photo Add Succeeded | Profile Photo Upload Failed | -- |
| Profile creation | Build Profile Button Clicked | Candidate Profile Create Succeeded | -- | Candidate Profile Create Errored |
| Persona selection | Onboarding Persona Card Clicked | Account Create Succeeded | -- | -- |
| Intro completion | Onboarding Intro Complete Button Clicked | -- | -- | -- |
| Onboarding completion | -- | Onboarding Complete Succeeded | -- | -- |
| Publish portfolio | Candidate Portfolio Publish Button Clicked | Candidate Portfolio Publish Succeeded | -- | Candidate Portfolio Publish Errored |
| Unpublish portfolio | Candidate Portfolio Unpublish Button Clicked | Candidate Portfolio Unpublish Succeeded | -- | -- |
| Rename portfolio | Candidate Portfolio Rename Button Clicked | Candidate Portfolio Rename Succeeded | -- | -- |
| Delete portfolio | Candidate Portfolio Delete Button Clicked | Candidate Portfolio Delete Succeeded | -- | -- |
| Remove profile photo (editor) | Candidate Profile Photo Remove Button Clicked | Candidate Profile Photo Remove Succeeded | -- | Candidate Profile Photo Remove Errored |
| Delete custom link | Candidate Custom Link Delete Button Clicked | Candidate Custom Link Delete Succeeded | -- | Candidate Custom Link Delete Errored |
| Identity verification | Open Identity Check Link Clicked | Candidate Interview Identity Verification Succeeded | Candidate Interview Identity Verification Rejected | Candidate Interview Identity Verification Errored |
| Device access | Allow Device Access Button Clicked | Device Access Grant Succeeded | Device Access Rejected | -- |
| Start interview | Candidate Interview Start Button Clicked | Candidate Interview Started | -- | -- |
| Restart question | Candidate Interview Question Restart Button Clicked | Candidate Interview Question Restart Succeeded | -- | Candidate Interview Question Restart Errored |
| Skip question | Candidate Interview Question Skip Button Clicked | Candidate Interview Question Skip Succeeded | Candidate Interview Question Skip Rejected | Candidate Interview Question Skip Errored |
| Screening response edit | Candidate Interview Screening Response Edit Button Clicked | Candidate Interview Screening Response Edit Succeeded | -- | -- |
| Submit interview | -- | Candidate Interview Submit Succeeded | Candidate Interview Submit Rejected | -- |

> **Exception:** `Sam Session Setup Failed` captures voice setup rejection separately from `Sam Session Started`, which is start-only.
