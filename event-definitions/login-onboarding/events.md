# Login & Onboarding — Event Catalog

**Flow:** `login_onboarding`
**Last Updated:** April 2026

---

## User Paths

### New User
```
Page Viewed (auth/landing)
  → Login Started (CTA click)
    → [external auth — no events]
      → Page Viewed (onboarding/role_selection)
        → Account Created ("Continue as [Persona]" + server confirms)
          → Page Viewed (onboarding/intro)
            → Intro Completed ("Let's go" click)
              → Page Viewed (home)
```

### Returning User (future — not yet implemented)
```
Page Viewed (auth/landing)
  → Login Started (CTA click)
    → [external auth — no events]
      → Login Succeeded (server confirms returning user)
        → Page Viewed (home)
```

---

## Events — Chronological Order (New User)

| # | Event | Type | SDK | Trigger |
|---|-------|------|-----|---------|
| 1 | Page Viewed | page_view | JS | Auth landing page renders (`/signup`) |
| 2 | Login Started | user_action | JS | User clicks "Continue with Google or Email" |
| 3 | _(external auth)_ | -- | -- | MSAL popup — no events |
| 4 | Page Viewed | page_view | JS | Role selection page renders (`/onboarding/role`) |
| 5 | Account Created | user_action | JS | User clicks "Continue as [Persona]" + server confirms role persisted |
| 6 | Page Viewed | page_view | JS | Intro page renders (`/onboarding/intro`) |
| 7 | Intro Completed | user_action | JS | User clicks "Let's go" |
| 8 | Page Viewed | page_view | JS | Home page renders (`/hiring-manager/job-postings`) |

**Total: 8 events** — 4 page views, 3 user actions, all frontend.

---

## Event Details

### Page Viewed
Single event name, differentiated by `current_page_context` property. Follows PostHog convention.

| current_page_context | URL | entry_point | previous_page_context |
|---------------------|-----|-------------|----------------------|
| `auth/landing` | `/signup` | From `?context=` URL param | `null` |
| `onboarding/role_selection` | `/onboarding/role` | `auth_landing_click_continue_with_google_or_email_button` | `auth/landing` |
| `onboarding/intro` | `/onboarding/intro` | `onboarding_role_selection_click_continue_as_persona_button` | `onboarding/role_selection` |
| `hiring_manager/job_postings` | `/hiring-manager/job-postings` | `onboarding_intro_page_load` | `onboarding/intro` |

### Login Started
- **action_value:** `continue_with_google_or_email_button`
- **component:** `auth_landing_hero_card_cta`
- **entity_type:** `account`
- **Status:** Implemented ✅

### Account Created
- **action_value:** `continue_as_hiring_manager_button` / `continue_as_recruiter_button` / `continue_as_job_seeker_button`
- **component:** `onboarding_role_selection_footer_cta`
- **entity_type:** `onboarding`
- **Status:** To implement

### Intro Completed
- **action_value:** `lets_go_button`
- **component:** `onboarding_intro_footer_cta`
- **entity_type:** `onboarding`
- **Status:** To implement

---

## Constants Being Removed

| Constant | File | Event String | Replaced By | Why Remove |
|----------|------|-------------|-------------|------------|
| `SIGNUP_STARTED` | `posthogEvents.ts:11` | `'Signup Started'` | `LOGIN_STARTED` | Wrong name, hardcoded context |
| `AUTH_LOGIN_STARTED` | `posthogEvents.ts:15` | `'Auth Login Started'` | `LOGIN_STARTED` | Fired too late (after popup), redundant |
| `AUTH_LOGIN_CANCELLED` | `posthogEvents.ts:17` | `'Auth Login Cancelled'` | `LOGIN_CANCELLED` | Rename for consistency with new naming |
| `AUTH_ROLE_UPDATED` | `posthogEvents.ts:25` | `'Auth Role Updated'` | `ACCOUNT_CREATED` | Onboarding role selection now fires Account Created |
| `AUTH_ROLE_UPDATE_FAILED` | `posthogEvents.ts:26` | `'Auth Role Update Failed'` | Error handling in Account Created flow | Same flow |
| `SIGNUP_STARTED` | `posthog_events.py:11` | `'Signup Started'` | Remove | Defined but never fired in backend |
| `ACCOUNT_CREATED` (backend) | `auth/router.py:148-156` | `'Account Created'` | Frontend Account Created | Moving from backend 5s heuristic to frontend role selection |

## Constants Being Added

| Constant | File | Event String |
|----------|------|-------------|
| `LOGIN_STARTED` | `posthogEvents.ts` | `'Login Started'` |
| `ACCOUNT_CREATED` | `posthogEvents.ts` | `'Account Created'` |
| `INTRO_COMPLETED` | `posthogEvents.ts` | `'Intro Completed'` |
| `PAGE_VIEWED` | `posthogEvents.ts` | `'Page Viewed'` |
| `LOGIN_CANCELLED` | `posthogEvents.ts` | `'Login Cancelled'` |

## Constants NOT Changing (separate flows, out of scope)

| Constant | Why keep |
|----------|---------|
| `AUTH_LOGIN_SUCCEEDED` | Still used for returning user auth — will be replaced when old user flow is implemented |
| `AUTH_LOGIN_FAILED` | Still used for auth failures — will be replaced when old user flow is implemented |
| `AUTH_DEV_LOGIN_*` | Dev-only login, separate concern |
| `AUTH_EMAIL_*` | Email verification flow, separate concern |
| `AUTH_PHONE_*` | Phone collection flow, separate concern |
| `AUTH_SESSION_RESTORE_*` | Session management, separate concern |
| `AUTH_REFRESH_FAILED` | Token refresh, separate concern |
| `AUTH_LOGOUT_COMPLETED` | Logout flow, separate concern |

---

## Helix Code References

| Event | File | Function/Location |
|-------|------|-------------------|
| Page Viewed (auth/landing) | `pages/SignUp.tsx` | Component mount |
| Login Started | `pages/SignUp.tsx` | `handleLogin()` — already implemented |
| Page Viewed (role selection) | `pages/RoleSelection.tsx` | Component mount |
| Account Created | `pages/RoleSelection.tsx` | `handleContinue()` — after `updateRole()` succeeds |
| Page Viewed (intro) | `pages/ValueProp.tsx` | Component mount |
| Intro Completed | `pages/ValueProp.tsx` | `handleContinue()` |
| Page Viewed (home) | Home page component | Component mount |
| Backend Account Created (REMOVE) | `backend/app/auth/router.py:148-156` | Remove 5s heuristic block |
