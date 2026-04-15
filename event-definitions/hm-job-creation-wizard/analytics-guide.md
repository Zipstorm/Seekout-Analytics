# HM Job Creation Wizard — Analytics Guide

**Flow:** `hm_job_creation_wizard`
**Last Updated:** April 2026

---

## Key Questions This Flow Answers

| Question | How to Answer | Events/Properties Used |
|---|---|---|
| What % of users who start the wizard complete it? | Funnel: PV-1 → PV-6 | All page views |
| Where do users drop off most? | Step-by-step funnel breakdown | Page Viewed events grouped by `current_page_context` |
| What % of created jobs ever get published (success page reached)? | `Job Created` count vs PV-6 count | `Job Created`, Page Viewed (success) |
| How many users skip the Sam conversation vs use it? | Compare Skip Sam Clicked vs Sam Chat Modality Selected | UA-5, UA-8, UA-9 |
| Voice vs text — which is more popular? | Breakdown of `modality` property | UA-8 / UA-9 (`modality` enum) |
| How often do users edit/delete AI-generated requirements? | Count of Edit/Delete Requirement Clicked per job | UA-15, UA-16 |
| How often do users edit/delete AI-generated questions? | Count of Edit/Delete Question Clicked per job | UA-23, UA-24 |
| How often do users use the AI refine prompt? | Refine Questions Submitted count per job | UA-26 |
| What prompts do users send to refine questions? | Distribution of `prompt_text` values | UA-26 (`prompt_text`) |
| Do keyboard users behave differently? | Compare `trigger: enter_key` vs `apply_button` / `verify_button` | UA-26, UA-30 (`trigger`) |
| What % of users verify their email vs skip? | Verify Code Submitted vs Skip Verification Clicked | UA-30, UA-31 |
| How many users resume an abandoned wizard? | Continue Setup Clicked count per job_id | UA-39 (count by `job_id`) |
| What % of users share the job from the success page? | Share Button Clicked from `current_page_context = hm_job_creation_wizard/success` | UA-36 |

---

## Funnels

### 1. Full Wizard Completion Funnel

Measures end-to-end completion of the job creation flow.

```
Page Viewed (job_details)
  → Job Wizard Next Clicked (job_details)
    → Job Created (system event)
      → Page Viewed (understanding_the_role)
        → [Skip Sam OR Sam Chat Modality Selected → conversation completes]
          → Page Viewed (role_requirements)
            → Job Wizard Next Clicked (role_requirements)
              → Page Viewed (interview_questions)
                → Job Wizard Next Clicked (interview_questions)
                  → Page Viewed (verify)
                    → [Verify Code Submitted OR Skip Verification Clicked]
                      → Page Viewed (success)
                        → [Job Published — system event]
```

**Drop-off insights:**
- Drop at step 1: User opened wizard but didn't paste/submit JD
- Drop at step 2 (intro): User saw Meet Sam page but didn't proceed
- Drop at step 2b: User selected modality but didn't complete conversation
- Drop at step 3-4: User reviewed AI output but abandoned
- Drop at step 5: User got to publish step but didn't finish

### 2. Sam Conversation Engagement Funnel

```
Page Viewed (understanding_the_role)
  → Start Talking To Sam Clicked
    → Page Viewed (sam_chat_modality_selection)
      → Sam Chat Modality Selected (modality=voice OR text)
        → Voice/Chat Session Started (system event — future scope)
          → Voice/Chat Session Ended (system event — future scope)
```

### 3. Resume Funnel

Measures whether users who abandon the wizard come back.

```
Job Created
  → Job Wizard Close Clicked (any step)
    → [time gap]
      → Continue Setup Clicked
        → Page Viewed (any wizard step)
          → Page Viewed (success) [eventual completion]
```

**Segment by `job_id`** to count distinct sessions per job.

### 4. Email Verification Funnel

```
Page Viewed (verify)
  → Send Code Clicked
    → Verify Code Submitted (success) OR Skip Verification Clicked
      → Page Viewed (success)
```

---

## Segmentation

### By drop-off step

| Last event seen | Where dropped |
|---|---|
| Page Viewed (job_details) only | Never submitted JD |
| Job Wizard Next Clicked (job_details) but no PV-2 | Job creation API failed |
| Page Viewed (understanding_the_role) only | Saw Meet Sam, didn't engage |
| Page Viewed (sam_chat_modality_selection) only | Opened modality picker, didn't pick |
| Page Viewed (role_requirements) only | Reviewed requirements, didn't proceed |
| Page Viewed (interview_questions) only | Reviewed questions, didn't proceed |
| Page Viewed (verify) only | Got to verify, didn't send code or skip |
| Page Viewed (success) | Completed flow |

### By interaction with AI output

| Segment | Definition |
|---|---|
| Pure-AI users | No Edit/Delete Requirement OR Question events between PV-3 and PV-4/5 |
| Tinkerers | 1–3 edit/delete events per job |
| Heavy customizers | 4+ edit/delete events per job |

### By Sam interaction path

| Segment | Path |
|---|---|
| Skipped Sam | UA-5 (Skip Sam Clicked) |
| Voice user | UA-8 (Sam Chat Modality Selected, `modality=voice`) |
| Text user | UA-9 (Sam Chat Modality Selected, `modality=text`) |
| Sam-curious but bailed | UA-4 (Start Talking To Sam Clicked) but no UA-8/UA-9 |

### By session continuity

| Segment | Definition |
|---|---|
| Single-session creators | All events for `job_id` have same `session_id` |
| Multi-session creators | Events for `job_id` span multiple `session_id` values (used Continue Setup) |

---

## Dashboard Recommendations

### Wizard Funnel Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Wizard starts (daily) | Trend | Page Viewed where `current_page_context = 'hm_job_creation_wizard/job_details'` |
| Step-by-step conversion | Funnel | All 6 page views in sequence |
| Step-by-step drop-off | Bar chart | Drop % at each step |
| Time per step | Trend | Median seconds between consecutive page views |
| Wizard completion rate | Single value | PV-6 count / PV-1 count |

### Sam Engagement Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Sam start rate | Single value | UA-4 (Start Talking To Sam Clicked) / PV-2 (Page Viewed understanding_the_role) |
| Skip rate | Single value | UA-5 (Skip Sam Clicked) / PV-2 |
| Modality split | Pie chart | Breakdown of `modality` from UA-8/UA-9 |
| Modality conversion to next step | Funnel | UA-8/UA-9 → PV-3 |

### AI Output Customization Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Avg requirement edits per job | Number | Sum of UA-15+UA-16+UA-17 / distinct `job_id` |
| Avg question edits per job | Number | Sum of UA-23+UA-24+UA-25 / distinct `job_id` |
| Refine prompt usage rate | Single value | Distinct `job_id` with UA-26 / Distinct `job_id` reaching PV-4 |
| Top refine prompts | Word cloud | `prompt_text` values from UA-26 |
| Suggestion chip usage | Bar chart | Count of UA-27 by `chip_label` |

### Resume & Recovery Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Resume rate | Single value | UA-39 (Continue Setup Clicked) count / abandoned jobs (jobs without PV-6) |
| Days to resume | Histogram | Time delta between Close Click and Continue Setup Click |
| Eventual completion after resume | Single value | Jobs with both UA-39 and PV-6 / Jobs with UA-39 |

### Verification Panel

| Metric | Insight Type | Definition |
|---|---|---|
| Verify vs skip split | Pie chart | UA-30 vs UA-31 |
| Verification success rate | Single value | (UA-30 with `trigger=verify_button` or `enter_key`) / UA-29 (Send Code Clicked) |
| Keyboard-driven verify rate | Single value | UA-30 with `trigger=enter_key` / UA-30 total |

---

## Key Insights to Watch

1. **Step 1 → 2 conversion is gated by AI extraction.** If users paste JD but don't see PV-2, the AI extraction may have failed or taken too long.
2. **Sam start rate vs skip rate** is a product signal — if most users skip, the Sam value prop may not be clear.
3. **Heavy customizers** (4+ edits) are signal that AI output quality needs improvement.
4. **Resume rate** is a recovery metric — high resume = users find value but get interrupted; low resume = abandonment is real.
5. **Verification skip rate** matters for candidate trust — high skip means we may need to make verification more compelling.

---

## Cross-Flow Connections

- **Onboarding → Wizard:** New users completing onboarding land on `hiring_manager/job_postings` and may immediately start the wizard. Track conversion via funnel: `Onboarding Completed` → `Page Viewed (hm_job_creation_wizard/job_details)`.
- **Wizard → Share:** Users completing the wizard may share via UA-36 (Share Button Clicked on success). This connects to the viral loop for hiring (Loop 2 in `viral-loop-metrics.md`).
- **Wizard → Team Invite:** Users may invite teammates via UA-37 (Invite Button Clicked). This connects to Team Invite viral loop.
