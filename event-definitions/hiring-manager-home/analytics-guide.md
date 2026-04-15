# Hiring Manager Home — Analytics Guide

**Flow:** `hiring_manager_home`
**Last Updated:** April 2026

---

## Key Questions This Page Answers

| Question | How to Answer | Events/Properties Used |
|---|---|---|
| How many users land on the HM home page daily? | Trend: Page Viewed where `current_page_context` = `hiring_manager/job_postings` | Page Viewed, `current_page_context` |
| Where do users come from when they reach the home page? | Breakdown by `previous_page_context` | Page Viewed, `previous_page_context` |
| What % of new users complete onboarding and reach home? | Funnel: Account Created → Page Viewed (home) | Account Created, Page Viewed |
| How many users switched personas from their original choice? | Filter: `first_persona` ≠ `current_persona` | `first_persona`, `current_persona` |
| What is the active persona distribution right now? | Breakdown by `current_persona` (person property) | `current_persona` |

---

## Funnels

### 1. Onboarding → Home Conversion (New Users)

Measures whether new users who create an account actually reach the home page.

```
Account Created
  → Page Viewed (current_page_context = 'hiring_manager/job_postings')
```

**Segmentation:** By `first_persona`, `auth_method`, `entry_point`

**What drop-off means:** User created account (persona persisted) but never loaded the home page in the same session. They likely dropped off at the intro page or had an app load failure.

### 2. Full Onboarding Funnel (New Users)

```
Page Viewed (auth/landing)
  → Login Started
    → Page Viewed (onboarding/role_selection)
      → Account Created
        → Page Viewed (onboarding/intro)
          → Intro Completed
            → Page Viewed (hiring_manager/job_postings)
```

### 3. Login → Home Conversion (Returning Users)

```
Login Started
  → Login Succeeded
    → Page Viewed (current_page_context = 'hiring_manager/job_postings')
```

**What drop-off means:** Auth succeeded but home page never loaded — app failure, immediate tab close, or redirect issue.

---

## Segmentation

### By `previous_page_context`

| Segment | What It Tells You |
|---|---|
| `onboarding/intro` | New users completing onboarding for the first time |
| `auth/landing` | Returning users + new users who re-logged after skipping intro |
| `null` | Direct URL / bookmark users (already authenticated) |

### By `current_persona`

| Segment | What It Tells You |
|---|---|
| `hiring_manager` | Users actively on the HM surface |
| `recruiter` | Users who switched to recruiter (if applicable) |
| `job_seeker` | Users who switched to job seeker (if applicable) |

### By `current_persona` vs `first_persona`

| Combo | Meaning |
|---|---|
| `first_persona` = `hiring_manager`, `current_persona` = `hiring_manager` | Stayed in original persona |
| `first_persona` = `recruiter`, `current_persona` = `hiring_manager` | Switched from recruiter to HM |
| `first_persona` = `hiring_manager`, `current_persona` = `recruiter` | Switched from HM to recruiter |

This helps answer: "Are users switching personas? Which direction? Does switching correlate with activation?"

---

## Dashboard Recommendations

### Home Page Health Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Daily home page views | Trend | Count of Page Viewed where `current_page_context` = `hiring_manager/job_postings` |
| Unique daily visitors | Trend | Unique `distinct_id` on above |
| New vs returning split | Stacked bar | Segment by `previous_page_context` (`onboarding/intro` = new, `auth/landing` = returning) |
| Entry point distribution | Pie chart | Breakdown by `entry_point` |

### Persona Switching Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Active persona distribution | Pie chart | Breakdown by `current_persona` (person property) |
| Persona switch rate | Trend | Users where `current_persona` ≠ `first_persona` / total users |
| Switch direction | Table | Cross-tab of `first_persona` × `current_persona` |
