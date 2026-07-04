# Helix Naming Cleanup Backlog

**Created:** 2026-07-04
**Source:** Post-merge validation of job-seeker-interview-v2

These issues predate the v2 merge and require codebase changes (renaming events in both Helix code and the analytics catalog).

---

## Rule 16 — Result terminal form (68 errors)

Events with `Type = Success` must end in `Succeeded`, `Rejected` events in `Rejected`, and error events in `Errored`. These pre-existing events use old naming:

### Success events not ending in "Succeeded"

| Event | Current Name | Suggested Rename |
|---|---|---|
| Login Cancelled | Login Cancelled | Login Cancelled Succeeded (or reclassify Type) |
| Account Created | Account Created | Account Create Succeeded |
| Intro Completed | Intro Completed | Intro Complete Succeeded |
| Auth Logout Completed | Auth Logout Completed | Auth Logout Succeeded |
| Auth Email Verify Code Sent | Auth Email Verify Code Sent | Auth Email Verify Code Send Succeeded |
| Auth Email Verified | Auth Email Verified | Auth Email Verify Succeeded |
| Auth Phone Submitted | Auth Phone Submitted | Auth Phone Submit Succeeded |
| Auth Phone Skipped | Auth Phone Skipped | Auth Phone Skip Succeeded |
| Job Posting Draft Created | Job Posting Draft Created | Job Posting Draft Create Succeeded |
| Job Description Evaluated | Job Description Evaluated | Job Description Evaluate Succeeded |
| Job Description Field Edited | Job Description Field Edited | Job Description Field Edit Succeeded |
| Screening Configuration Saved | Screening Configuration Saved | Screening Configuration Save Succeeded |
| Job Posting Verified | Job Posting Verified | Job Posting Verify Succeeded |
| Job Posting Published | Job Posting Published | Job Posting Publish Succeeded |
| Job Shared | Job Shared | Job Share Succeeded |
| Job Status Changed | Job Status Changed | Job Status Change Succeeded |
| Profile Section Updated | Profile Section Updated | Profile Section Update Succeeded |
| Custom Link Shared | Custom Link Shared | Custom Link Share Succeeded |
| Profile Photo Added | Profile Photo Added | Profile Photo Add Succeeded |
| And ~20 more wizard step / hiring events... | | |

### Failed events (should be "Rejected" or "Errored")

| Event | Current Name | Suggested Rename |
|---|---|---|
| Auth Login Failed | Auth Login Failed | Auth Login Rejected |
| Auth Session Restore Failed | Auth Session Restore Failed | Auth Session Restore Rejected |
| Auth Refresh Failed | Auth Refresh Failed | Auth Refresh Rejected |
| Auth Dev Login Failed | Auth Dev Login Failed | Auth Dev Login Rejected |
| Auth Email Verify Code Send Failed | Auth Email Verify Code Send Failed | Auth Email Verify Code Send Rejected |
| Auth Email Verify Failed | Auth Email Verify Failed | Auth Email Verify Rejected |
| Auth Phone Submit Failed | Auth Phone Submit Failed | Auth Phone Submit Rejected |
| Job Creation Failed | Job Creation Failed | Job Create Rejected |
| Job Description Evaluation Failed | Job Description Evaluation Failed | Job Description Evaluate Rejected |
| Sam Session Setup Failed | Sam Session Setup Failed | Sam Session Setup Rejected |
| Job Share Failed | Job Share Failed | Job Share Rejected |
| Team Member Invite Failed | Team Member Invite Failed | Team Member Invite Rejected |
| Intro Video Creation Failed | Intro Video Creation Failed | Intro Video Create Rejected |
| Profile Photo Upload Failed | Profile Photo Upload Failed | Profile Photo Upload Rejected |
| Candidate Profile Creation Failed | Candidate Profile Creation Failed | Candidate Profile Create Rejected |
| Resume Upload Failed | Resume Upload Failed | Already split into Candidate Resume Upload Rejected + Errored in v2 codebase |

### v1 events still using old names in codebase

These were renamed in the v2 tracking plan's "Modifications to Existing Events" but the v1 catalog entries still have the old names until the codebase is updated:

- Resume Upload Failed (v1 still live alongside v2 split)
- Profile Photo Upload Failed (v1 still live)
- Candidate Profile Creation Failed (v1 still live)

---

## Rule 15 — Chat WebSocket naming (1 error)

| Event | Issue |
|---|---|
| Chat WebSocket Abnormal Close | Action "WebSocket Abnormal Close" doesn't end in past-tense verb |

---

## Rule 4 — Missing standard property (1 error)

| Event | Issue |
|---|---|
| Share Button Clicked | Job-grouped interaction event missing `job_id` (may be intentional for creation flow) |
