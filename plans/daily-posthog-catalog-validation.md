# Daily PostHog Catalog Runtime Validation

## Context

The repository already validates analytics docs daily with
`scripts/run-daily-validation.py` and posts the static validator digest to Slack.
That validator confirms catalog/schema/dashboard consistency, but it does not verify
whether implemented catalog events are actually showing up in PostHog with the
expected properties and sample values.

This plan adds a separate daily PostHog runtime check across configured products.
The check compares product catalogs against PostHog event definitions, property
definitions, and recent event samples.

## Decisions

- **Workflow:** separate GitHub Actions workflow and Slack message from the existing
  static docs validator.
- **Products:** use one PostHog project per product.
- **Event scope:** check catalog rows with status `Live` or `Live (legacy)` only.
  Ignore `Dev`, `Dev only`, `Not Started`, and removed rows for expected-event
  coverage.
- **Freshness window:** an expected event counts as showing up if it appears in the
  last 7 days. `last_seen_at = null` is an error; old-but-present `last_seen_at`
  is a warning so rare-but-implemented events do not train people to ignore the
  digest.
- **Property strictness:** non-optional catalog properties must have a key on
  sampled rows, even if the value is blank. A missing key is an error.
- **Qualifier policy:** `(optional)` means the key may be absent; type hints such
  as `(boolean)` do not affect optionality; scope notes such as `(login page only)`
  or `(interview landing page only)` mean optional-by-scope unless an explicit
  override says otherwise.
- **Value rules:** validate declared catalog property types only. Do not infer
  date/range/cardinality rules from property names.
- **API strategy:** use PostHog event/property definition APIs for metadata and
  bounded HogQL queries only for recent runtime property/value samples.
- **Automation status:** PostHog drift is Slack-only. The GitHub Actions job should
  fail only for automation/config/auth failures.
- **Report hygiene:** report sanitized summaries only. Do not print raw IDs, emails,
  URLs, names, or free-text payloads.

## Approach

Create a stdlib-only Python script that reuses the existing markdown/table and
catalog parsing helpers from `scripts/validate-analytics-docs.py` where they are
safe, but adds a runtime-specific Properties-cell parser that preserves
per-property qualifiers. The current `extract_props` helper only returns
backticked names and drops markers such as `(optional)` and `(login page only)`,
so it cannot be the source of truth for runtime optionality.

The script loads non-secret PostHog project mappings from repo config, reads
personal API keys from environment variables, queries PostHog, and posts a
sanitized Slack digest.

Use a small committed config file such as `config/posthog-projects.json`:

```json
{
  "products": [
    {
      "product": "helix",
      "host": "https://us.posthog.com",
      "project_id": "12345",
      "api_key_env": "POSTHOG_HELIX_PERSONAL_API_KEY"
    }
  ]
}
```

Secrets stay in GitHub Actions. The committed config contains only product names,
regional host URLs, project IDs, and the environment variable names that hold the
personal API keys. The key should be owned by a designated shared/admin analytics
PostHog account, documented with the secret setup; rotate it in PostHog and the
matching GitHub Actions secret.

Use a layered API flow:

1. Fetch event definitions in bulk and use `last_seen_at` for event existence and
   freshness decisions.
2. Fetch property definitions as a cheap project-global pre-filter only.
3. Run bounded HogQL sampling only for events that are fresh enough for
   property/value validation. If an event definition says an event is fresh but
   the sampling query returns zero rows, report that as a metadata/sample
   mismatch.

## Checks

1. **API and config health**
   Verify product config, host, project ID, personal API key, auth headers, and
   pagination before running catalog checks.

2. **Event definition coverage**
   For every expected catalog event, verify the exact event name exists in the
   PostHog event definitions API. Treat `last_seen_at = null` as an error and
   old-but-present `last_seen_at` as a warning.

3. **Event drift**
   Report product-looking PostHog events that are not in the catalog, near-miss
   event names, removed events still firing, and dev-only events seen in production.

4. **Property definition pre-filter**
   For every catalog property used by expected events, verify the key exists
   somewhere in PostHog property definitions where PostHog exposes it. This is a
   project-global weak signal only; per-event key presence is authoritative in the
   runtime sampling check.

5. **Runtime sampling consistency**
   For fresh expected events, run bounded HogQL sampling to gather rows for
   property/value validation. Do not run a separate per-event presence probe; if
   event definitions say an event is fresh but the sampling query returns zero
   rows, report a metadata/sample mismatch.

6. **Runtime key presence**
   On sampled rows, verify required keys are present. Blank values pass when the
   key exists; missing keys fail. Required keys come from catalog Properties,
   qualifier policy, applicable schema standard-event properties, and `job_id`
   when `Group = job`.

7. **Runtime declared-type validation**
   Validate sampled values against the declared Property Dictionary buckets only:
   enum membership, boolean, numeric, array, UUID-shape, and string presence. Do
   not infer ISO-date, non-negative, range, rate, or cardinality rules from names.

8. **Enum drift**
   Use property definitions and selective HogQL sampling to report observed enum
   values that are outside catalog allowlists.

9. **Slack reporting**
   Include per-product totals, missing events, stale events, bad or missing
   properties, invalid enum values, and sanitized examples. Keep raw sample values
   out of Slack.

## Explicitly Out Of Scope

- No group/person update verification.
- No frontend/backend source sanity inference.
- No raw sample value reporting.
- No failure of the GitHub Actions job for analytics drift.
- No name-based value heuristics. If range/date validation is needed later, add
  first-class catalog type buckets before validating it.

## Files To Modify Or Create

- **Create** `config/posthog-projects.json` for non-secret product-to-PostHog
  mappings.
- **Create** `scripts/run-posthog-catalog-validation.py` for the PostHog runtime
  validator.
- **Create** `.github/workflows/daily-posthog-catalog-validation.yml` for the
  scheduled daily check.
- **Reuse** safe markdown/catalog parsing helpers from
  `scripts/validate-analytics-docs.py`, but add a dedicated qualifier-aware
  Properties-cell parser for runtime validation.
- **Optionally extend** Slack rendering helpers by copying only the small formatting
  patterns needed from `scripts/run-daily-validation.py`; keep the two workflows
  separate and label the copied block with a keep-in-sync comment.

## Verification

1. Unit-test catalog filtering: `Live` and `Live (legacy)` are included; `Dev`,
   `Dev only`, `Not Started`, and removed statuses are excluded from expected-event
   coverage.
2. Unit-test PostHog pagination, auth/config failures, and malformed API responses
   with mocked HTTP responses.
3. Unit-test qualifier parsing for `(optional)`, type hints such as `(boolean)`,
   and scope notes such as `(login page only)`.
4. Unit-test required key presence: present blank values pass, missing keys fail,
   optional/scope-optional keys may be absent, and `job_id` is required when
   `Group = job`.
5. Unit-test HogQL result validation for metadata/sample mismatches, missing keys,
   bad enum values, bad declared scalar types, UUID-shape fields, and sanitized
   report output.
6. Run the script in `--dry-run` mode with fixture API responses and verify the
   Slack payload contains product summaries but no raw PII-like values.
7. Keep the existing static analytics validator tests green.
8. After secrets are configured, manually dispatch the new workflow and confirm the
   Slack digest posts while the existing daily docs validator remains independent.

## Assumptions

- Each product maps to one PostHog project.
- Recruit currently has an intentionally empty catalog and should skip/pass until
  events are added.
- PostHog API keys are personal API keys stored as GitHub Actions secrets.
- The PostHog personal API key is owned by a designated shared/admin analytics
  PostHog account, not an individual contributor account; rotation happens in
  PostHog and the matching GitHub Actions secret.
- PostHog private endpoints require the correct regional host and use pagination via
  `next`.
- HogQL usage is bounded to compact daily checks, not bulk export.

## Status

- **Implemented** - added config scaffold, runtime validator script, separate
  workflow, and focused tests. Helix will remain skipped until its PostHog
  `project_id` and matching GitHub Actions secret are configured.
