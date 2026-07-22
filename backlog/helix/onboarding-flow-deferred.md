# Onboarding Flow — Deferred Items

**Created:** 2026-07-05
**Source:** Onboarding flow audit (`plans/helix-onboarding-flow-audit.md`) and tracking plan (`tracking-plans/helix/2026-07-05-onboarding-flow-v1.md`)
**Decision:** These items were identified during the onboarding flow audit but deferred to avoid expanding the scope of the v1 tracking plan. Each item is separately scoped, with pickup timing noted below.

---

## 1. Job Post Wizard Dismissed During Onboarding

**What:** Track when an HM user clicks the X (close) button on the job post wizard during onboarding, skipping job creation entirely.

**Why this matters:** During the HM onboarding walkthrough (2026-07-05), we observed that the job post wizard is shown after the intro page but is skippable via an X button. Professional users MUST create a portfolio (no skip option), but HMs can skip. Tracking the skip lets us measure:
- What % of HMs create their first job during onboarding vs skip to dashboard
- Whether HMs who skip during onboarding come back to create a job (and how long it takes)
- If the wizard placement during onboarding is actually helpful or just friction

**Proposed event:** `Job Post Wizard Dismissed` (Type: Interaction) with `wizard_mode: 'onboarding'`, `current_page_context`, `step_name` (which wizard step they were on when they dismissed)

**When to pick up:** After the v1 onboarding tracking plan is merged and we have baseline data on the core funnel. It can be bundled with other job wizard improvements.

---

## 2. Persona-Specific Intro Page Content Tracking

**What:** The intro/value prop page (`/onboarding/intro`) shows different content per persona — Professional sees "Future-ready careers start here" with career-focused value cards, HM sees "Stop reading resumes, start meeting the right people" with hiring-focused value cards. Currently the `Intro Completed` event doesn't capture which content variant was shown.

**Why this matters:** If we A/B test intro page content per persona, we need to know which variant the user saw. Also useful for understanding if the intro content influences onboarding completion rates.

**Proposed change:** Add `intro_variant` or `intro_content_version` property to Intro Completed (→ Intro Complete Succeeded after rename).

**When to pick up:** When the product team considers A/B testing intro page content, or when we have enough baseline data to compare completion rates across personas.

---

## 3. Email Signup Path — Email Verification + Phone Collection Flow

**What:** The onboarding walkthrough used Google OAuth, which skips email verification and phone collection entirely. The email signup path (`Create account` with work email) likely includes:
- `/verify-email` — email verification with OTP code
- `/onboarding/phone` — phone number collection (skippable)

These pages have events (Auth Email Verify *, Auth Phone *) but no Page Viewed. The v1 tracking plan adds Page Viewed to these pages, but the actual flow has not been walked through and screenshotted.

**Why this matters:** Without walking the email path, we don't know if there are additional screens, modals, or edge cases (e.g., what happens if OTP expires? Is there a resend limit UI?). The Page Viewed additions in the tracking plan are based on code analysis, not visual confirmation.

**Action needed:** Walk through the email signup path and capture screenshots. Update `context/helix/screenshots/onboarding/WORKFLOW.md` with the email-specific flow.

**When to pick up:** Before implementing the Page Viewed additions for email verification and phone collection pages. Low priority since Google/Microsoft OAuth is likely the dominant path.

---

## 4. Interview → Signup → Onboarding Path

**What:** A candidate who completes an anonymous AI interview can sign up from the interview completion page. This path has special routing:
- If `resume_copied = true` → `/candidate/activate` (ActivateProfile interstitial)
- Otherwise → `/candidate/create-profile` (standard onboarding)

The claim logic is in `candidateInterviewSignup.ts`. ActivateProfile.tsx has no `capture()` calls.

**Why this matters:** This is a high-value conversion path (interview → signup). Understanding how many interview candidates complete onboarding vs drop off is critical for the candidate funnel.

**Proposed events:**
- Page Viewed on ActivateProfile (`candidate_activate_profile`)
- `mode: 'interview_claim'` to distinguish from standard onboarding
- Track whether the claim was successful (already in `Candidate Interview Claimed`)

**When to pick up:** After the v1 onboarding tracking plan is merged. This is a separate user journey that deserves its own tracking plan or an extension to v1.

---

## 5. Onboarding Time-Per-Step Breakdown

**What:** The v1 tracking plan captures `onboarding_duration_seconds` on the terminal `Onboarding Complete Succeeded` event. But it doesn't break down time spent on each individual step (e.g., how long on role selection vs intro vs create profile).

**Why this matters:** If we see high drop-off at a specific step, knowing the time spent on that step before dropping off helps distinguish "confused and stuck" from "distracted and left". Also helps identify if any step is unexpectedly slow.

**Proposed approach:** Add `step_duration_seconds` to Page Viewed events on onboarding pages. Compute as `Date.now() - sessionStorage timestamp` set when the page first mounted. For intermediate steps, emit the previous step duration on the NEXT page's Page Viewed. For terminal steps, flush the final duration on completion or abort so the last step is captured even without another onboarding Page Viewed.

**When to pick up:** After we have baseline funnel data from v1. This is an enhancement that adds implementation complexity (sessionStorage timestamp management per step).

---

## 6. "Finish Setup" Widget Tracking (Professional Post-Onboarding)

**What:** After Professional onboarding completes, the portfolio editor shows a "Finish setup — 1 of 5 complete, 20%" widget in the bottom-right corner suggesting next steps (upload profile photo, etc.). These are optional post-onboarding actions.

**Why this matters:** Tracking engagement with this widget would show:
- What % of users interact with it
- Which suggested actions get completed
- Whether completing suggested actions correlates with retention

**Proposed events:** Widget interaction events (clicked, dismissed, step completed). These are post-onboarding, not onboarding itself.

**When to pick up:** When the product team wants to optimize the post-onboarding activation flow. Separate from the core onboarding tracking plan.

---

## 7. Returning User / Sign-In Path

**What:** The v1 tracking plan focuses on new user signup. Returning users go through `/signin` → auth → dashboard. The sign-in path has different routing logic (no role selection, no intro, goes directly to the user's landing route based on their role).

**Why this matters:** Understanding returning user behavior (login frequency, auth method, session restore rates) is important for retention analytics.

**When to pick up:** After v1 onboarding is instrumented. The auth lifecycle events (Auth Login Succeeded, Auth Session Restore Succeeded) already cover the basics. A separate "returning user" tracking plan could add Page Viewed on the sign-in page and track login frequency patterns.

---

## 8. Verify `wizard_mode: 'onboarding'` on Job Wizard Events

**What:** The existing job post wizard events (Job Post Wizard Started, Job Post Wizard Job Details Completed, Job Post Wizard Intake Mode Selected, Job Post Wizard Role Requirements Completed, Job Post Wizard Interview Questions Completed, Job Post Wizard Verification Completed, Job Post Wizard Verification Skipped, Job Posting Draft Created, Job Posting Verified, Job Posting Published, etc.) should consistently carry `wizard_mode: 'onboarding'` when the wizard is initiated during the HM onboarding flow.

**Why this matters:** During the HM onboarding walkthrough (2026-07-05), we confirmed that the job post wizard is launched directly after the intro page. HMs can either complete the wizard (5 steps: JD → Understanding role → Requirements → Questions → Verify → Success) or dismiss it via the X button. Adding `wizard_mode: 'onboarding'` lets us:
- Measure what % of HMs create a job during onboarding vs return later
- Compare wizard completion rates for onboarding vs dashboard-initiated jobs
- Separate onboarding friction from general wizard friction in funnel analysis

**Why deferred:** The v1 tracking plan records the intended `wizard_mode` behavior for the HM wizard path. This backlog item is for verifying the shipped implementation and expanding the catalog/dashboard documentation after baseline onboarding events are merged. This is separate from the job seeker create-profile flow, which uses the generic `mode` property.

**Affected events (all existing, all need `wizard_mode` verified/documented):**
- Job Post Wizard Started
- Job Post Wizard Job Details Completed
- Job Description Evaluated / Job Description Evaluation Failed
- Job Post Wizard Intake Mode Selected
- Sam Session Started / Sam Session Ended / Sam Session Setup Failed
- Job Post Wizard Role Requirements Completed
- Job Post Wizard Interview Questions Completed
- Job Post Wizard Verification Completed / Job Post Wizard Verification Skipped
- Job Posting Draft Created
- Screening Configuration Saved
- Job Posting Verified
- Job Posting Published
- All Role Requirement and Screening Question CRUD events

**`wizard_mode` values:** `onboarding` (wizard launched during onboarding), `create` (wizard launched from job postings dashboard via "+ Create job" button)

**When to pick up:** After v1 onboarding tracking plan is merged. Can be bundled with backlog item #1 (Job Post Wizard Dismissed) since both touch the wizard component.

**Screenshots reference:** `context/helix/screenshots/onboarding/16-*.png` through `21-*.png`

---

## 9. Replace OAuth Screenshots with Sanitized Captures — **Done**

**What:** The original `02-google-oauth-chooser.png` showed personal Gmail accounts and another person's email. Replaced with a sanitized capture showing only the office email (`@seekout.com`).

**Done:** 2026-07-07

---

## 10. Profile Photo Upload Failed — Split Object Family + Stale Terminal

**What:** `Profile Photo Added` was renamed to `Profile Photo Add Succeeded` in the onboarding v1 plan, but the failure sibling `Profile Photo Upload Failed` was not renamed. This creates a split object family (`Profile Photo Add` vs `Profile Photo Upload`) and leaves a non-conforming `Failed` terminal.

**Correct name:** `Profile Photo Add Rejected` or `Profile Photo Add Errored` (depending on whether the failure is user-caused or system-caused).

**Why deferred:** Pre-existing catalog naming issue, not part of the onboarding v1 scope. Per CLAUDE.md: "pre-existing catalog naming issues unrelated to the tracking plan → document in backlog, don't fix during merge."

**When to pick up:** During the next naming cleanup sprint (see `backlog/helix/naming-cleanup.md`).

---

## 11. Recruiter Wizard-Completion Terminal Undefined

**What:** `Onboarding Complete Succeeded` lists `current_page_context` values for Professional, HM-skip, HM-wizard-complete, and Recruiter-skip paths. But the Recruiter-completes-ATS-wizard path is undefined — `WORKFLOW.md` marks this terminal as "TBD (not yet captured)."

**Impact:** If a Recruiter completes the ATS wizard during onboarding, `Onboarding Complete Succeeded` may fire with an unlisted `current_page_context` value or may not fire at all.

**When to pick up:** When the Recruiter wizard-completion flow is walked through and screenshotted. Add the terminal `current_page_context` value to the Onboarding Complete Succeeded spec and update the `WORKFLOW.md`.

---

## 12. Onboarding Complete Succeeded — Update Status from Dev to Live

**What:** `Onboarding Complete Succeeded` is listed as status `Dev` in `docs/helix/event-catalog.md`, but the PostHog runtime validator confirms it is firing in production (flagged as "Dev event seen in production" on 2026-07-22).

**Why this matters:** The event is used in the live "New-User Onboarding Funnel" on the Adoption & Engagement dashboard (PostHog insight 9871327). Leaving it as `Dev` causes the validator to emit a warning on every run, and downstream consumers may incorrectly ignore it.

**Action:** Update the event's Status column from `Dev` to `Live` in `docs/helix/event-catalog.md`. This touches the event-catalog source of truth, so it should go through a tracking plan update or a dedicated catalog fix PR.

**When to pick up:** Next catalog maintenance pass or tracking plan that touches onboarding events.

---

## How to Use This Backlog

- Each item is independently scoped, but some items depend on the v1 tracking plan merge or additional validation before pickup
- When picking up an item, create a tracking plan (or extend an existing one) and reference this backlog item
- After an item is implemented, mark it as **Done** with the tracking plan reference and date
- Items may become obsolete if the product changes — review periodically
