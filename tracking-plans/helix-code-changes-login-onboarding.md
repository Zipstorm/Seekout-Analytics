# Helix Code Changes — Login & Onboarding Events

**Repo:** helix → `helix-app/frontend/src/`
**Purpose:** Align PostHog event capture calls with the updated event schema.
**Last Updated:** April 2026

---

## 1. Page Viewed

**File:** `pages/SignUp.tsx` (and other login/onboarding pages firing Page Viewed)

**Move `$set_once` from Login Started to Page Viewed:**

The `$set_once` for attribution properties should fire on Page Viewed (not Login Started) so we capture attribution even if the user bounces before clicking login.

| Property | Type | Value | Notes |
|----------|------|-------|-------|
| `entry_point` | `$set_once` | from `?context=` URL param or `'direct'` | Currently set as `$set_once` on Login Started — move here. |
| `first_referrer` | `$set_once` | `document.referrer` or `null` | Currently set as `$set_once` on Login Started — move here. |
| `first_landing_url` | `$set_once` | `window.location.href` | Currently set as `$set_once` on Login Started — move here. |

**No removals needed.**

---

## 2. Login Started

**File:** `pages/SignUp.tsx`

**Remove these from the capture call:**

| Property | Reason |
|----------|--------|
| `context_object_type` | Removed from schema. Not needed for login events. |
| `context_object_id` | Removed from schema. Not needed for login events. |
| `$set_once` block | Attribution `$set_once` (`entry_point`, `first_referrer`, `first_landing_url`) moved to Page Viewed. Remove the entire `$set_once` from this event. |

---

## 3. Account Created

**File:** `pages/RoleSelection.tsx`

**Remove these from the capture call:**

| Property | Reason |
|----------|--------|
| `context_object_type` | Removed from schema. Not needed for onboarding events. |
| `context_object_id` | Removed from schema. Not needed for onboarding events. |
| `signup_context` | Replaced by `entry_point` (already present in the capture call). |

**Rename:**

| Current | New | Reason |
|---------|-----|--------|
| `persona` | `first_persona` | Align with schema naming. Schema defines `first_persona` ($set_once), `current_persona` ($set), and `activated_personas` ($set). No generic `persona` property. |

**Add:**

| Property | Type | Value | Notes |
|----------|------|-------|-------|
| `auth_method` | event property | `'google'`, `'email'`, etc. | How the user authenticated. Not currently in the capture call. |
| `referred_by` | event property + `$set_once` | referrer user ID or `null` | User ID of referrer if user arrived via a referral link. Add as both event property and `$set_once`. |

**Update `$set_once`:** Change from `first_persona, entry_point, account_created_at` to `first_persona, account_created_at, referred_by` (remove `entry_point` — now set on Page Viewed).

---

## 4. Intro Completed

**File:** `pages/ValueProp.tsx`

**Remove these from the capture call:**

| Property | Reason |
|----------|--------|
| `context_object_type` | Removed from schema. Not needed for onboarding events. |
| `context_object_id` | Removed from schema. Not needed for onboarding events. |

**Add:**

| Property | Type | Value | Notes |
|----------|------|-------|-------|
| `auth_method` | event property | `'google'`, `'email'`, etc. | How the user authenticated. Needs to be passed through from the auth step. |

**Note:** `previous_page_context` and `entry_point` are already in the code — they were just missing from the catalog (now fixed).

---

## 5. Auth Login Succeeded

**File:** `stores/authStore.ts`

**Remove:**

| Property | Reason |
|----------|--------|
| `role` | No `role` property in schema. `current_persona` is already set as a person property via `identifyUser()` — redundant as an event property. |

---

## 6. Auth Session Restore Succeeded

**File:** `stores/authStore.ts`

**Remove:**

| Property | Reason |
|----------|--------|
| `role` | Same as above — `current_persona` person property covers this. |

---

## 7. Auth Dev Login Succeeded

**File:** `stores/authStore.ts`

**Remove:**

| Property | Reason |
|----------|--------|
| `role` | Same as above — `current_persona` person property covers this. |

---

## 8. Auth Dev Login Failed

**File:** `stores/authStore.ts`

**Add:**

| Property | Value | Notes |
|----------|-------|-------|
| `error_detail` | error message string | Add error message alongside existing `status_code`. |

---

## 9. Auth Email Verify Code Send Failed

**File:** `stores/authStore.ts`

**Add:**

| Property | Value | Notes |
|----------|-------|-------|
| `error_detail` | error message string | Add error message alongside existing `status_code`. |

---

## 10. Auth Email Verified

**File:** `stores/authStore.ts`

**Remove:**

| Property | Reason |
|----------|--------|
| `role` | No `role` property in schema. `current_persona` person property covers this. |

---

## 11. Auth Email Verify Failed

**File:** `stores/authStore.ts`

**Add:**

| Property | Value | Notes |
|----------|-------|-------|
| `error_detail` | error message string | Add alongside existing `status_code` and `attempts_remaining`. |

---

## 12. Auth Phone Submitted

**File:** `pages/PhoneCollection.tsx`

**Remove:**

| Property | Reason |
|----------|--------|
| `has_role` | Not in schema. Not useful. |

**Add:**

| Property | Value | Notes |
|----------|-------|-------|
| `phone_length` | number | Length of phone number submitted. |
| `country_code` | string | Country code of phone number (e.g., `+1`). |

---

## 13. Auth Phone Submit Failed

**File:** `pages/PhoneCollection.tsx`

**Add:**

| Property | Value | Notes |
|----------|-------|-------|
| `error_detail` | error message string | Add alongside existing `status_code`. |

---

## 14. Auth Phone Skipped

**File:** `pages/PhoneCollection.tsx`

**Remove:**

| Property | Reason |
|----------|--------|
| `has_role` | Not in schema. `current_persona` person property covers this. |

---

## Summary of Changes

### Login & Onboarding Events

| Event | Remove | Rename | Add |
|-------|--------|--------|-----|
| Page Viewed | -- | -- | `$set_once: entry_point, first_referrer, first_landing_url` |
| Login Started | `context_object_type`, `context_object_id`, `$set_once` block | -- | -- |
| Account Created | `context_object_type`, `context_object_id`, `signup_context`, `entry_point` from `$set_once` | `persona` → `first_persona` | `auth_method`, `referred_by` (event prop + `$set_once`) |
| Intro Completed | `context_object_type`, `context_object_id` | -- | `auth_method` |

### Auth Lifecycle Events

| Event | Remove | Add |
|-------|--------|-----|
| Auth Login Succeeded | `role` | -- |
| Auth Session Restore Succeeded | `role` | -- |
| Auth Dev Login Succeeded | `role` | -- |
| Auth Dev Login Failed | -- | `error_detail` |
| Auth Email Verify Code Send Failed | -- | `error_detail` |
| Auth Email Verified | `role` | -- |
| Auth Email Verify Failed | -- | `error_detail` |
| Auth Phone Submitted | `has_role` | `phone_length`, `country_code` |
| Auth Phone Submit Failed | -- | `error_detail` |
| Auth Phone Skipped | `has_role` | -- |
