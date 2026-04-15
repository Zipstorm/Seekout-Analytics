# Hiring Manager Home — Property Dictionary

**Flow:** `hiring_manager_home`
**Last Updated:** April 2026

---

## New Person Property: `current_persona`

### Why this property exists

`first_persona` (`$set_once`) captures what the user chose during onboarding — it never changes. But users can switch personas (e.g., Hiring Manager ↔ Recruiter via the sidebar toggle). We need `current_persona` (`$set`) to know which persona is active at any given time.

### Definition

| Property | Type | Scope | Allowed Values | Set By | Description |
|---|---|---|---|---|---|
| `current_persona` | enum | person (`$set`) | `hiring_manager`, `recruiter`, `job_seeker` | `identifyUser()` on login + persona switch | The persona the user currently has selected. Updated on every login and on persona switch. |

### How it differs from existing persona-related properties

| Property | Scope | Changes? | Purpose | Example Use |
|---|---|---|---|---|
| `first_persona` | person (`$set_once`) | Never | What user chose at onboarding (attribution, cohort analysis) | "What % of users who signed up as HM are still active?" |
| `persona` | event | Per event | Persona at the moment of a specific event (e.g., Account Created) | "Which persona was selected during onboarding?" |
| `current_persona` | person (`$set`) | On every login + switch | Active persona right now (segmentation, dashboards, live state) | "How many active HMs do we have today?" / "Did this user switch from recruiter to HM?" |

### `current_persona` allowed values

| Value | UI Label (sidebar) | When set |
|---|---|---|
| `hiring_manager` | "Hiring Manager" | User is on hiring manager surface |
| `recruiter` | "Recruiter" | User is on recruiter surface |
| `job_seeker` | "Job Seeker" | User is on job seeker surface |

### Implementation

**On login (update `identifyUser()`):**

```javascript
// In lib/posthog.ts → identifyUser()
posthog.identify(user.id,
  {
    email: user.email,
    name: user.name,
    org_id: user.orgId,
    current_persona: user.currentPersona  // NEW — replaces role and acting_as
  },
  { account_created_at: user.createdAt }
);
```

**On persona switch (sidebar toggle, no re-login needed):**

```javascript
// When user switches persona via sidebar
posthog.people.set({ current_persona: newPersona });
```

---

## Event Properties — Page Viewed (hiring_manager/job_postings)

### Required Properties

| Property | Type | Value | Description |
|---|---|---|---|
| `current_page_context` | string | `hiring_manager/job_postings` | Page identifier |

### Conditional Properties (dynamic per user journey)

| Property | Type | Possible Values | Description |
|---|---|---|---|
| `previous_page_context` | string or null | `onboarding/intro`, `auth/landing`, `null`, `hiring_manager/job_postings` | Previous page — see firing-rules.md for derivation logic |
| `entry_point` | string or null | `onboarding_intro_click_lets_go_button`, `auth_landing_login_redirect`, `direct_url`, `browser_reload` | How user arrived — see firing-rules.md for derivation logic |
| `context_object_type` | null | `null` | Home page is not scoped to a specific business object |

---

## Auto-Captured Properties (PostHog SDK)

Automatically included on every event. Do NOT set manually.

| Property | Description |
|---|---|
| `$current_url` | Full page URL (`/hiring-manager/job-postings`) |
| `$referrer` | HTTP referrer |
| `$browser` | Browser name |
| `$os` | Operating system |
| `$device_type` | desktop / mobile / tablet |
| `$screen_height` / `$screen_width` | Screen dimensions |
| `timestamp` | Event timestamp |
| `$session_id` | Session identifier |
| `distinct_id` | Identified user ID |
