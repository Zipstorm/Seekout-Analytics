# Helix Dashboard & Funnel Fixes Backlog

**Created:** 2026-07-04
**Source:** Post-merge validation of job-seeker-interview-v2

These issues predate the v2 merge and involve dashboard/funnel references that are out of sync with the catalog.

---

## Rule 9 — Platform Health / Schema mismatch (9 errors)

Platform Health dashboard rows don't match the Schema Interaction / Started / Result Pattern table. The rows exist in both places but the validator detects format or column differences.

**Action:** Audit both tables and ensure exact column/value alignment. May be a column count mismatch (Platform Health has 5 columns, Schema table may have 4 in some rows).

---

## Rule 6 — Funnel area labels (6 errors)

Funnel definitions use old "Surface" terminology instead of current "Persona Events" section names.

| Funnel | Event | Says | Should Be |
|---|---|---|---|
| Job Sharing Loop | Job Shared | Hiring Surface | Hiring Persona Events |
| Job Sharing Loop | Account Created | Account & Surface | Login & Onboarding Events |
| Job Sharing Loop | Account Activated | Account & Surface | Account & Persona Events |
| Profile Sharing Loop | Custom Link Shared | Prospect Surface | Prospect Persona Events |
| Profile Sharing Loop | Account Created | Account & Surface | Login & Onboarding Events |
| Profile Sharing Loop | Account Activated | Account & Surface | Account & Persona Events |

**Action:** Update `docs/helix/dashboards.md` funnel definitions to use current catalog section names.

---

## Rule 5 — Missing funnel events (2 errors)

| Funnel | Missing Event | Issue |
|---|---|---|
| Job Sharing Loop | Signup Started | Event was removed (replaced by Login Started) in April 2026 |
| Profile Sharing Loop | Signup Started | Same |

**Action:** Replace `Signup Started` with `Login Started` in both funnel definitions, or remove the stage if it no longer applies.
