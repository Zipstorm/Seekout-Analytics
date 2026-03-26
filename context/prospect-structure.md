# Helix - Prospect/Job-Seeker Side Structure

**Product:** Helix (SeekOut.ai)
**Last Updated:** March 2026

---

## Model: Portfolio + Applications

On the prospect/job-seeker side we follow this structure:

| Entity | Cardinality | Description |
|--------|-------------|-------------|
| **Portfolio** | Exactly 1 per user (mutable) | The prospect's living profile. Contains resume content (Typst source), extras (photo, video, GitHub, links), and selected template. Edited directly via natural language. |
| **Application** | Many per user (immutable snapshots) | Created each time the prospect shares their portfolio. Freezes resume content and extras at share time. Can be tailored for a specific job or shared as-is. Each application has a unique tracking link. |

### Relationships

- User → **exactly 1 Portfolio** (mutable, primary entity)
- Portfolio → **many Applications** (immutable snapshots, created at share time)

---

## Portfolio

The portfolio is the prospect's home — a single, living profile they maintain and improve over time.

| Field | Description |
|-------|-------------|
| `typst_source` | Resume content in Typst intermediate format (LLM-editable) |
| `template_id` | Selected premium template (chosen during onboarding) |
| `profile_photo` | Optional display photo |
| `video_intro` | Optional recorded intro video |
| `github_url` | Optional GitHub profile link |
| `external_links` | Optional additional portfolio/project links |

**Key behaviors:**
- Created during onboarding after resume conversion + mandatory first edit
- Edited post-onboarding via natural language chat (agentic LLM pattern)
- Structural/ATS fixes are auto-applied; content changes are always prospect-initiated via NL
- Existing applications are unaffected by portfolio edits (they are immutable snapshots)

---

## Applications

An application is an immutable snapshot created each time the prospect shares their portfolio. It is the record of what was shared, when, and how it performed.

| Field | Description |
|-------|-------------|
| `name` | User-provided or auto-generated as "[Company] — [Role]" from JD |
| `tracking_link` | System-generated unique URL for sharing and tracking |
| `is_tailored` | Whether JD-based tailoring was applied |
| `date` | Creation timestamp |
| `company` | From JD or user input |
| `job_details` | JD text, role, company (if tailored) |
| `recruiter_link` | Recruiter context if originated from a joblink |
| `frozen_resume` | Compiled PDF + Typst source + structured data at share time |
| `frozen_extras` | Photo, video, links as of share time |
| `activity_feed` | Views, clicks, time spent by viewers (live-updating) |

**Key behaviors:**
- Fully immutable after creation — nothing editable except the name
- Both tailored and as-is shares create tracked applications
- Re-sharing for the same job creates a new application (no deduplication)
- Unique tracking links enable per-application analytics

### Tailored vs As-Is

| Type | Created when | Content |
|------|-------------|---------|
| **Tailored** | Prospect provides a JD during the share flow | Resume automatically tailored against a rubric scorecard derived from the JD. Reframes existing experience, reorders sections, mirrors JD language — but never fabricates. |
| **As-is** | Prospect shares without a specific job | Current portfolio content frozen as a snapshot. Prospect provides a name for tracking. |

---

## Resume Conversion Pipeline

Prospects upload PDF resumes during onboarding. The system converts them to the editable Typst format:

1. **PDF parsing** — vision-based extraction of resume content
2. **Diagnosis** — AI identifies 2-3 specific issues (ATS compatibility, weak bullets, formatting)
3. **Template selection** — prospect chooses from 2-3 premium templates
4. **Conversion** — LLM converts content to Typst using chosen template; auto-fixes structural issues
5. **Mandatory first edit** — NL editor with diagnosis-based starter prompts; prospect makes their first edit

After this pipeline, the portfolio is created from the converted + edited content plus extras.

---

## Tailoring Pipeline

When a prospect shares for a specific job:

1. **JD extraction** — scrape URL or accept pasted text
2. **Rubric scorecard** — LLM creates 6-10 weighted criteria from the JD
3. **Tailored Typst** — LLM tailors the portfolio's Typst source against the rubric
4. **Preview** — prospect reviews the tailored version
5. **Application created** — immutable snapshot with tailored content and tracking link

---

## Implications

- A prospect maintains exactly one portfolio — no multi-portfolio management overhead
- The portfolio is always current; the system handles tailoring for each opportunity
- Applications provide a complete history of every share with engagement tracking
- Editing is natural language-driven (agentic LLM pattern with `update_resume` and `ask_clarification` tools)
- The prospect's job: keep the portfolio up to date. The system's job: tailor it for each opportunity.

---

## Where This Is Used

- **Product/UX:** Portfolio view (editing, sharing), Applications page (tracking), onboarding wizard (conversion)
- **Data model:** [Entity-Relationship Model](./entity-relationship-model.md) (Portfolio and Application entities)
- **Network/graph:** [Network Model](./network-model.md) (Portfolio and Application nodes)
- **Analytics:** Events and dashboards for applications — see [analytics-posthog.md](./analytics/analytics-posthog.md)

---

*Entity model defined in the [Portfolio Tailoring solution design](../../../projects/Helix%20-%20Portfolio%20Tailoring/solution-design.md).*
