# Recruit Onboarding Flow — Screenshot Map

**Captured:** 2026-07-09
**Source:** Manual walkthrough
**Platform:** `app.seekout.io` (product) + `seekout.com` (marketing site)

---

# Flow 1: Returning User — Login

**Entry:** User navigates to `app.seekout.io`

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `01-login-page.png` | `app.seekout.io/signIn?redirect=%2F` | Login page — "Welcome back!" Email/password form, "Remember Me" checkbox, Cloudflare Turnstile captcha. Three CTAs: "Sign In" (purple button), "Sign in with SSO" (link), "Get a free trial" (link under "Don't have an account?"). "Forgot your password?" link. | — | See branching below |

### Branching from Login Page

| User Action | What Happens Next | Next Step |
|---|---|---|
| Clicks "Sign In" | Submits email/password form → auth flow (not yet captured) | TBD — post-login product experience |
| Clicks "Sign in with SSO" | Toggles form to SSO mode (email-only field) | Flow 1b, Step 1 |
| Clicks "Get a free trial" | Navigates to `seekout.com/pricing/` (leaves app, enters marketing site) | Flow 2, Step 1 |
| Clicks "Forgot your password?" | Navigates to `/forgotPassword` (not yet captured) | TBD — password reset flow |

---

# Flow 1b: SSO Login

**Entry:** User clicks "Sign in with SSO" on the login page

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `08-sso-login-page.png` | `app.seekout.io/signIn?redirect=%2F` | SSO login form — "Single Sign On: Use your organization's network to sign in." Email-only field. "Sign In" button (purple), "Sign in without SSO" link, "Get a free trial" link. Same URL as login page — the form toggles between email/password and SSO modes. | — | See branching below |

### Branching from SSO Form

| User Action | What Happens Next | Next Step |
|---|---|---|
| Clicks "Sign In" (SSO form) | Submits email → redirects to organization's SSO provider → auth callback → Auth Login Succeeded/Rejected | TBD — post-login product experience |
| Clicks "Sign in without SSO" | Toggles form back to email/password mode | Flow 1, Step 1 |
| Clicks "Get a free trial" | Navigates to `seekout.com/pricing/` | Flow 2, Step 1 |

---

# Flow 2: New User — Free Trial Signup (via Pricing Page)

**Entry:** User clicks "Get a free trial" from login page, or navigates directly to `seekout.com/pricing/`
**Note:** All pages in this flow are on `seekout.com` (marketing site), NOT `app.seekout.io` (product). Implementation requires PostHog on the marketing site codebase.

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `02-pricing-page.png` | `seekout.com/pricing/` | Pricing page — "Plans that scale with your hiring ambitions". Banner: "Take SeekOut for a test drive: 14 days free" with "Get free trial →" button. Monthly/Annual toggle (Annual shows "Save $360/yr"). 4 plan cards: **SeekOut Recruit Core** ($149/mo, "Start free trial" + "Book a demo" + "See what's included"), **SeekOut Recruit — Sourcing** (Custom, "Book a demo" + "See what's included"), **SeekOut Recruit — Sourcing + Integration** (Custom, "Book a demo" + "See what's included"), **SeekOut Recruit — Full Recruiting Funnel** (Custom, "Book a demo" + "See what's included"). Nav bar: "Sign in" link, "Book a 1:1 demo" button. | — | See branching below |

### Branching from Pricing Page

| User Action | What Happens Next | Next Step |
|---|---|---|
| Clicks "Get free trial →" (banner) | Navigates to `seekout.com/free-trial/` | Flow 2, Step 2 |
| Clicks "Start free trial" (Core plan card) | Navigates to `seekout.com/free-trial/` (same page as above) | Flow 2, Step 2 |
| Clicks "Start free trial →" (top nav) | Navigates to `seekout.com/free-trial/` (same page as above) | Flow 2, Step 2 |
| Clicks "Book a demo" (any plan card) | Navigates to `seekout.com/requestdemo/` | Flow 3, Step 1 |
| Clicks "Book a 1:1 demo" (nav bar) | Navigates to `seekout.com/request-meeting/` | Flow 4, Step 1 |
| Clicks "See what's included" (any plan card) | Expands plan feature details inline (not a navigation) | Stays on pricing page |
| Toggles Monthly ↔ Annual | Switches displayed prices and billing cycle | Stays on pricing page |

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 2 | `03-free-trial-form.png` | `seekout.com/free-trial/` | Free trial signup — "Start your free trial" (14 days, no credit card). Left side: feature list (Unlimited AI-powered searches, Healthcare/Nursing talent pools, AI scorecards, Talent pool insights, Workspace shortlists, Personalized outreach, Export shortlists). Stats: 1B+ profiles, 750+ customers, 50% faster time-to-fill. Right side: form with First Name, Last Name, Business Email, Company Name, Job Title, Country dropdown, reCAPTCHA. "Request free trial" submit button (orange). | Clicks "Request free trial" | TBD — form submission result (not yet captured) |

**Notes:**
- Screenshots 03, 04, and 05 all show the same page (`seekout.com/free-trial/`) — reached via different CTAs on the pricing page (banner, Core plan card, and nav bar respectively). The page and form are identical regardless of entry point.

---

# Flow 3: New User — Demo Request (Plan-Specific)

**Entry:** User clicks "Book a demo" under a specific plan card on the pricing page
**Note:** Marketing site page.

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `07-request-demo-page.png` | `seekout.com/requestdemo/` | Book a demo — "AI Recruiting Platform" (SeekOut Recruit focused). Left side: "Best for Recruiters, Sourcers, and TA Leaders" with feature list (Search 1B+ profiles, Screen inbound, Multi-touch outreach, Rediscover ATS, Talent insights). Stats: 1B+ profiles, 750+ customers, 50% faster time-to-fill. Right side: form with First Name, Last Name, Business Email, Company name, Job Title, Phone, Country dropdown. "Book a demo" submit button (orange). | Clicks "Book a demo" | TBD — form submission result (not yet captured) |

---

# Flow 4: New User — Meeting Request (General)

**Entry:** User clicks "Book a 1:1 demo" in the pricing page nav bar
**Note:** Marketing site page. Broader scope than Flow 3 — covers both SeekOut Spot and SeekOut Recruit.

| Step | Screenshot | Route | Screen | User Action | What Happens Next |
|------|-----------|-------|--------|-------------|-------------------|
| 1 | `06-request-meeting-page.png` | `seekout.com/request-meeting/` | Request a meeting — "Unlock Your Fastest Path to Qualified Talent". Left side: two product cards — **SeekOut Spot** (AI Recruiting Service, for Hiring Managers/TA Leaders/CHROs) and **SeekOut Recruit** (AI Recruiting Platform, for Recruiters/Sourcers/TA Leaders) with feature lists. Right side: form with First Name, Last Name, Business Email, Company Name, Job Title, Phone, Country dropdown, "What are you interested in?" dropdown. "Request meeting" submit button (orange). | Clicks "Request meeting" | TBD — form submission result (not yet captured) |

---

# Flows Not Yet Captured

| Flow | Description | Screenshots Needed |
|---|---|---|
| Post-login product experience | What returning users see after successful Sign In or SSO login | App dashboard / landing page |
| Post-trial signup | What happens after "Request free trial" form is submitted — email confirmation, account activation, first-time product login | Confirmation page, activation email, first login |
| SSO redirect + callback | What happens after user submits email on SSO form — redirect to identity provider, callback | SSO provider screens (if visible) |
| Forgot password flow | Password reset from login page | Reset form, email, new password page |
| Post-demo-request | What happens after "Book a demo" or "Request meeting" form is submitted | Confirmation page |

---

# Screenshots Index

| # | File | Screen | Site | Route |
|---|---|---|---|---|
| 01 | `01-login-page.png` | Login page | Product (`app.seekout.io`) | `/signIn` |
| 02 | `02-pricing-page.png` | Pricing page | Marketing (`seekout.com`) | `/pricing/` |
| 03 | `03-free-trial-form.png` | Free trial form (from banner) | Marketing (`seekout.com`) | `/free-trial/` |
| 04 | `04-free-trial-form-from-plan-card.png` | Free trial form (from Core plan) | Marketing (`seekout.com`) | `/free-trial/` |
| 05 | `05-free-trial-form-from-nav.png` | Free trial form (from nav) | Marketing (`seekout.com`) | `/free-trial/` |
| 06 | `06-request-meeting-page.png` | Request a meeting | Marketing (`seekout.com`) | `/request-meeting/` |
| 07 | `07-request-demo-page.png` | Book a demo (Recruit) | Marketing (`seekout.com`) | `/requestdemo/` |
| 08 | `08-sso-login-page.png` | SSO login form | Product (`app.seekout.io`) | `/signIn` (SSO mode) |
