# Onboarding Flows — All Personas

**Captured:** 2026-07-05
**Source:** Manual walkthrough (Google OAuth signup)
**Auth method:** Sign up with Google

---

# Flow 1: Professional (Job Seeker) Persona

**Persona selected:** Professional (candidate)

---

## Flow Sequence

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `01-signup-page.png` | `/signup` | Sign up page — "Sign up with Google", "Sign up with Microsoft", work email + "Create account", "Already have an account? Sign in" link | Clicked "Sign up with Google" | Redirects to Google OAuth |
| 2 | `02-google-oauth-chooser.png` | `accounts.google.com` | Google account chooser — "Choose an account to continue to SeekOut" | Selected walkthrough Google account | Redirects back to SeekOut |
| 3 | `03-role-selection-default.png` | `/onboarding/role` | Role selection — "What brings you to SeekOut?" with two cards: "I'm a professional" / "I'm hiring". Continue button disabled. Note: "You can always change this later in settings" | (viewing default state) | — |
| 4 | `04-role-selection-professional-selected.png` | `/onboarding/role` | Professional card selected (purple border). Continue button now says "Continue as a candidate" (enabled, purple) | — | — |
| 5 | `05-role-selection-hiring-expanded.png` | `/onboarding/role` | "I'm hiring" card expanded, showing two sub-options: "Hiring Manager" and "Recruiter" with descriptions. Continue button remains disabled until sub-option selected | (viewing hiring expansion) | — |
| 6 | `06-role-selection-continue-as-candidate.png` | `/onboarding/role` | Professional selected, "Continue as a candidate" button ready | Clicked "Continue as a candidate" | Navigates to intro page |
| 7 | `07-value-prop-intro.png` | `/onboarding/intro` | Value prop page — "Future-ready careers start here". Shows 3-step progress: "How we help" (current) → "Build your portfolio" (next). Three value cards: "AI career coach", "Your data, your call", "Share & track". "Let's go" button at center. **No cancel/back button.** | Clicked "Let's go" | Navigates to create profile |
| 8 | `08-create-profile-empty.png` | `/candidate/create-profile` | Build your portfolio — resume upload (required), profile photo (optional), add links (optional, GitHub default), handle (optional). "Build my portfolio" button disabled. Progress shows step 2: "Build your portfolio" | (viewing empty state) | — |
| 9 | `09-create-profile-resume-uploaded.png` | `/candidate/create-profile` | Resume uploaded: "Netflix - Product manager sample jd.docx" with green check. "Remove" link appears. "Build my portfolio" button now enabled (purple). | Clicked "Build my portfolio" | Shows interstitial |
| 10 | `10-creating-portfolio-interstitial.png` | `/candidate/create-profile` | Modal overlay: "Creating your portfolio — Analyzing your resume. This typically takes about 20 seconds." 4-step progress: Reading your resume (done) → Extracting key highlights (in progress) → Generating your portfolio → Preparing your portfolio editor | (auto-progressing) | Redirects to editor |
| 11 | `11-portfolio-editor-onboarding-complete.png` | `/candidate/editor/:id` | Portfolio editor with generated content. Shows: skills, journey timeline, work experience. Sidebar: "Professional" persona, "Dashboard" nav. Bottom-right: "Finish setup — 1 of 5 complete, 20%" widget suggesting "Upload profile photo" as next. **This marks the end of onboarding.** | Onboarding complete | User is now in the product |

---

## Flow Observations

### Steps NOT seen in this flow (Google OAuth)
- **Email verification** (`/verify-email`) — skipped for Google OAuth (email already verified via Google)
- **Phone collection** (`/onboarding/phone`) — not shown in this flow

### Key UX Details
- **Continue button is dynamic** — text changes based on role selection: "Continue" (disabled) → "Continue as a candidate" / "Continue as a hiring manager" / "Continue as a recruiter"
- **"I'm hiring" expands** to show two sub-options (Hiring Manager, Recruiter) while "I'm a professional" is a single click
- **No back/cancel on intro page** — user must click "Let's go" to proceed
- **Resume is required** — "Build my portfolio" button stays disabled until a resume is uploaded
- **State persists** — closing the tab and reopening returns to `/candidate/create-profile` (cookie/session), confirming portfolio creation is part of the mandatory onboarding flow
- **Portfolio creation is async** — shows a 4-step interstitial while AI processes the resume (~20 seconds)
- **Post-onboarding widget** — "Finish setup" panel suggests remaining profile tasks (photo, etc.) but these are optional

### Onboarding Completion Definition
For **Professional** persona: onboarding is complete when the user lands on the portfolio editor page (`/candidate/editor/:id`) after the AI generates their first portfolio from their resume.

### Possible Alternate Paths (not yet captured)
- **Email signup** path → may include email verification and phone collection steps
- **Interview → signup** path → candidate who did an anonymous interview, then signs up to claim it
- **Sign in** path → returning user via `/signin`

---

# Flow 2: Hiring Manager Persona

**Persona selected:** Hiring Manager
**Captured:** 2026-07-05

## Flow Sequence

Shared steps 1–3 are identical to Professional (signup page, Google OAuth, role selection default). This flow diverges at role selection.

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 3b | `12-hm-role-selection-hiring-manager.png` | `/onboarding/role` | "I'm hiring" card expanded, "Hiring Manager" sub-option selected (purple border). Continue button says "Continue as a hiring manager" (enabled, purple). | Clicked "Continue as a hiring manager" | Navigates to intro page |
| 4 | `13-hm-value-prop-intro.png` | `/onboarding/intro` | Value prop page — "Stop reading resumes, start meeting the right people." Different content from Professional: shows Network → Candidates → AI Screening → Top Candidates pipeline. Four value cards: "You're in control", "Fairness through AI", "Candidates prefer it", "Time saved". "Let's go" button. **No 2-step progress bar** (unlike Professional which shows "How we help" → "Build your portfolio"). **No cancel/back button.** | Clicked "Let's go" | Navigates to job post wizard |
| 5 | `14-hm-create-job-posting-wizard.png` | `/hiring-manager/job-posting` | Create job posting wizard — step 1 "Job details". 5-step progress: Job details → Understanding the role → Role requirements → Interview questions → Verify. "Tell us about your role" with JD paste/URL field. **Has X (close) button in top-right corner** — user can skip/cancel. | Clicked X (close) | Navigates to job postings dashboard |
| 6 | `15-hm-job-postings-dashboard.png` | `/hiring-manager/job-postings` | Jobs dashboard — "Let's find your first great hire". Empty state with "+ Create job" CTA. Sidebar shows "Hiring Manager" persona, "Job postings" nav. **This marks the end of onboarding for HM.** | Onboarding complete | User is now in the product |

## Flow Observations

### Key Differences from Professional
- **Value prop content is persona-specific** — HM sees hiring-focused messaging ("Stop reading resumes"), Professional sees career-focused ("Future-ready careers start here")
- **No 2-step progress bar** — Professional shows "How we help → Build your portfolio" progress. HM intro page has no progress indicator.
- **Job post wizard is skippable** — HM can close the wizard with X button and land on the job postings dashboard. Professional MUST complete portfolio creation (no cancel/skip option).
- **Onboarding is shorter for HM** — Role selection → Intro → (optional job wizard) → Dashboard. Only 3 mandatory steps vs 5+ for Professional.

### Onboarding Completion Definition
For **Hiring Manager** persona: onboarding is complete when the user lands on the job postings dashboard (`/hiring-manager/job-postings`). The job post wizard is shown during onboarding but is **skippable** — creating a job during onboarding is optional.

### Analytics Implications
- Job post wizard events during onboarding should carry `wizard_mode: 'onboarding'` to distinguish from later job creation
- If user completes the wizard during onboarding, both the job creation events AND Onboarding Complete Succeeded fire
- If user skips (X button), only Onboarding Complete Succeeded fires — need to track the skip action
- Need to track: what % of HMs create their first job during onboarding vs later

---

## Flow 2b: Hiring Manager — Job Post Wizard During Onboarding

This sub-flow documents what happens when the HM chooses to complete the job post wizard during onboarding instead of dismissing it.

**Captured:** 2026-07-05

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `16-hm-wizard-step1-jd-pasted.png` | `/hiring-manager/job-posting` | Step 1: Job details — JD text pasted. "Evaluating your job description" progress bar shows AI extracting role details. Next button available. | Pasted JD, clicked "Next" | Goes to step 2 |
| 2 | `17-hm-wizard-step2-understanding-role.png` | `/hiring-manager/job-postings/:jobId` | Step 2: Understanding the role — "Meet Sam, your AI hiring assistant". Two options: "Voice chat" (selected) and "Text chat". Also has "Skip and let Sam generate the screening questions" link. Back button available. | Skipped (clicked "Skip and let Sam generate...") | Goes to step 3 |
| 3 | `18-hm-wizard-step3-role-requirements.png` | `/hiring-manager/job-postings/:jobId/role-requirements` | Step 3: Role requirements — AI-drafted yes/no questions (Compensation, Work arrangement). Each editable/deletable. "+ Add question" CTA. Back button available. | Clicked "Next" without editing | Goes to step 4 |
| 4 | `19-hm-wizard-step4-interview-questions.png` | `/hiring-manager/job-postings/:jobId/questions` | Step 4: Your screening questions — 3 AI-generated interview questions with edit/delete. "+ Add question" CTA. "Confirm candidate identity" toggle (unchecked). Back button available. | Clicked "Next" without editing | Goes to step 5 |
| 5 | `20-hm-wizard-step5-verify.png` | `/hiring-manager/job-postings/:jobId/verify` | Step 5: Verify — "Show candidates this is a real opportunity". Work email verification with "Send code" button. "Maybe later" link to skip verification. Back button available. | Clicked "Maybe later" | Goes to success page |
| 6 | `21-hm-wizard-success-page.png` | `/hiring-manager/job-postings/:jobId/success` | Success page — "You built it, now share it". Shows job summary (title, ~19 min, 3 screening questions, AI interview). Next steps: 1. Preview, 2. "Share interview" (Required to get applicants), 3. "Invite teammates". "Go to job posting page" link at bottom. Sidebar shows job in "Recent". **This is the landing page after completing the wizard during onboarding.** | Onboarding complete (wizard path) | User is now in the product |

### Key Observations — Wizard Completion Path
- **5 wizard steps:** Job details → Understanding the role → Role requirements → Interview questions → Verify
- **"Understanding the role" (step 2) is skippable** — "Skip and let Sam generate" link bypasses the AI chat
- **Verify step (step 5) is skippable** — "Maybe later" link skips email domain verification
- **Success page is the terminal** — shows the created job with next actions (Preview, Share, Invite teammates)
- **All existing job wizard events fire during this flow** — they already exist in the catalog (Job Post Wizard Started, Job Post Wizard Job Details Completed, etc.)
- **`wizard_mode: 'onboarding'` should be verified in backlog** — these events already exist in dev branch; verifying/documenting `wizard_mode` is a separate scope item, not part of the v1 onboarding tracking plan

### Onboarding Completion — Wizard Path
For HMs who complete the wizard during onboarding, the Onboarding Complete Succeeded event should fire on the success page (`/hiring-manager/job-postings/:jobId/success`). This is different from HMs who skip (who land on the job postings dashboard).

---

# Flow 3: Recruiter Persona

**Persona selected:** Recruiter
**Captured:** 2026-07-05

## Flow Sequence

Shared steps 1–3 are identical to Professional/HM (signup page, Google OAuth, role selection default). This flow diverges at role selection.

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 3b | `22-recruiter-role-selection.png` | `/onboarding/role` | "I'm hiring" card expanded, "Recruiter" sub-option selected (purple border). Continue button says "Continue as a recruiter" (enabled, purple). | Clicked "Continue as a recruiter" | Navigates to intro page |
| 4 | `23-recruiter-value-prop-intro.png` | `/onboarding/intro` | Value prop page — "Stop wasting time on bad applicants, focus on the ones that matter." Different content from HM: pipeline shows ATS → Candidates apply → AI evaluates & screens → Top candidates. Same four value cards as HM but with recruiter-specific copy ("Nothing goes out without your sign-off. No candidate gets contacted behind your back." / "Every applicant gets a real conversation against the same rubric — no more keyword-soup resume triage." / "Review 50 applicants today..."). "Let's go" button. **No progress bar, no cancel/back button.** | Clicked "Let's go" | Navigates to ATS check wizard |
| 5 | `24-recruiter-ats-check-wizard.png` | `/recruiter/ai-job-flow/ats-check` | "Create job posting" wizard — step 1 "Job details". 4-step progress: Job details → Intake meeting → Screening setup → Review rubric. "How are you sourcing for this role?" with two cards: "Network referrals" / "Inbound from your ATS". Cancel button and X button available — **user can skip.** | Clicked X (close) | Navigates to job postings dashboard |
| 6 | `25-recruiter-job-postings-dashboard.png` | `/recruiter/ai-job-flows` | Job Postings dashboard — "Let's find your first great hire". Empty state with "+ Select job" CTA. Sidebar shows "Recruiter" persona, "Job postings" nav. **This marks the end of onboarding for Recruiter.** | Onboarding complete | User is now in the product |

## Flow Observations

### Key Differences from HM
- **Intro page content is recruiter-specific** — "Stop wasting time on bad applicants" (HM sees "Stop reading resumes"). Pipeline illustration shows ATS as the source (HM shows Network).
- **Different wizard** — Recruiter gets a 4-step ATS-focused wizard (Job details → Intake meeting → Screening setup → Review rubric) vs HM's 5-step wizard (Job details → Understanding the role → Role requirements → Interview questions → Verify)
- **Has both Cancel button AND X button** — HM wizard only has X. Recruiter wizard has an explicit Cancel text button.
- **Dashboard CTA differs** — Recruiter sees "+ Select job" (implies importing from ATS). HM sees "+ Create job" (implies creating from scratch).
- **Dashboard route differs** — Recruiter lands on `/recruiter/ai-job-flows`, HM lands on `/hiring-manager/job-postings`

### Similarities with HM
- Same intro page structure (value cards, "Let's go" button, no progress bar)
- Job creation wizard is **skippable** (same as HM)
- Onboarding ends on the job postings dashboard when wizard is skipped (same as HM)

### Onboarding Completion Definition
For **Recruiter** persona: onboarding is complete when the user lands on the job postings dashboard (`/recruiter/ai-job-flows`). The ATS check wizard is shown during onboarding but is **skippable**. If the user completes the wizard, onboarding ends on the success page (flow not yet captured — see `backlog/helix/onboarding-flow-deferred.md` item #11).

---

# Summary: Onboarding Flows Comparison

| Aspect | Professional | Hiring Manager | Recruiter |
|--------|-------------|----------------|-----------|
| **Intro headline** | "Future-ready careers start here" | "Stop reading resumes, start meeting the right people" | "Stop wasting time on bad applicants, focus on the ones that matter" |
| **Progress bar on intro** | Yes (2-step: How we help → Build your portfolio) | No | No |
| **Post-intro flow** | Create profile (mandatory) | Job post wizard (skippable) | ATS check wizard (skippable) |
| **Post-intro route** | `/candidate/create-profile` | `/hiring-manager/job-posting` | `/recruiter/ai-job-flow/ats-check` |
| **Can skip post-intro step?** | No — must upload resume and build portfolio | Yes — X button on wizard | Yes — X button and Cancel button on wizard |
| **Wizard steps** | N/A (single page) | 5 steps: JD → Understanding role → Requirements → Questions → Verify | 4 steps: Job details → Intake meeting → Screening setup → Review rubric |
| **Terminal (skip path)** | N/A | Job postings dashboard (`/hiring-manager/job-postings`) | Job postings dashboard (`/recruiter/ai-job-flows`) |
| **Terminal (complete path)** | Portfolio editor (`/candidate/editor/:id`) | Wizard success page (`/hiring-manager/job-postings/:jobId/success`) | TBD (see backlog item #11) |
| **Mandatory steps** | 5+ (signup → auth → role → intro → create profile → portfolio) | 3 (signup → auth → role → intro → dashboard) | 3 (signup → auth → role → intro → dashboard) |
