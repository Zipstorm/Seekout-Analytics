# Login & Onboarding — Analytics Guide

**Flow:** `login_onboarding`
**Last Updated:** April 2026

---

## New User Funnel

```
Page Viewed (auth/landing)
  → Login Started
    → Page Viewed (onboarding/role_selection)
      → Account Created
        → Page Viewed (onboarding/intro)
          → Intro Completed
            → Page Viewed (home)
```

**Drop-off at each step:**

| Step | Drop-off means |
|------|---------------|
| Page Viewed → Login Started | User saw the page but didn't click CTA (bounce) |
| Login Started → Page Viewed (role) | User clicked CTA but didn't complete MSAL auth |
| Page Viewed (role) → Account Created | User saw persona options but didn't commit |
| Account Created → Page Viewed (intro) | Should be ~100% (auto-navigates) |
| Page Viewed (intro) → Intro Completed | User saw intro but didn't click "Let's go" |
| Intro Completed → Page Viewed (home) | Should be ~100% (auto-navigates) |

---

## Key Metrics

### Acquisition

| Metric | Formula | Segment By |
|--------|---------|------------|
| Landing page → CTA rate | `Login Started` / `Page Viewed (auth/landing)` | `entry_point` |
| Auth completion rate | `Page Viewed (role_selection)` / `Login Started` | `entry_point` |
| Signup conversion rate | `Account Created` / `Login Started` | `entry_point`, `first_persona` |

### Onboarding

| Metric | Formula | Segment By |
|--------|---------|------------|
| Role selection rate | `Account Created` / `Page Viewed (role_selection)` | `first_persona` |
| Intro engagement rate | `Intro Completed` / `Page Viewed (intro)` | `first_persona` |
| Full funnel rate | `Page Viewed (home)` / `Page Viewed (auth/landing)` | `entry_point`, `first_persona` |

---

## Questions Each Event Answers

### Page Viewed (auth/landing)
- How many users reach the landing page?
- What's the bounce rate (no Login Started)?

### Login Started
- How many users attempt auth?
- Which entry_point drives the most attempts?
- What % complete auth vs cancel?

### Page Viewed (onboarding/role_selection)
- How many new users reach role selection?
- What's the auth → role selection drop-off?

### Account Created
- What's the most popular first persona?
- Does entry_point correlate with persona choice?
- How many users who see role selection actually commit?

### Page Viewed (onboarding/intro)
- Do all account-created users see the intro?

### Intro Completed
- What % of users actively click "Let's go" vs auto-navigate or close?
- Does intro engagement correlate with first-week retention?

### Page Viewed (home)
- Confirms user reached the product

---

## PostHog Dashboard Setup

### Funnel: New User Signup
Steps:
1. `Page Viewed` where `current_page_context = auth/landing`
2. `Login Started`
3. `Page Viewed` where `current_page_context = onboarding/role_selection`
4. `Account Created`
5. `Page Viewed` where `current_page_context = onboarding/intro`
6. `Intro Completed`

Breakdown by: `entry_point` (person property)

### Trend: Accounts Created
Event: `Account Created`
Breakdown by: `persona`

### Trend: Entry Point Distribution
Event: `Login Started`
Breakdown by: `entry_point` (event property)
