#!/usr/bin/env python3
"""Validate product catalogs against recent PostHog runtime data."""

import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from difflib import get_close_matches

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VALIDATOR_PATH = SCRIPT_DIR / "validate-analytics-docs.py"
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "posthog-projects.json"

EXPECTED_STATUSES = {"Live", "Live (legacy)"}
DEV_STATUSES = {"Dev", "Dev only"}
TYPE_HINT_QUALIFIERS = {"array", "boolean", "bool", "enum", "number", "numeric", "string", "uuid"}
SYSTEM_EVENT_PREFIXES = ("$", "survey ")
MAX_BLOCKS = 50
MAX_FINDING_GROUPS = 4
MAX_FINDINGS_PER_GROUP = 4
MAX_TEXT_CHARS = 280


@dataclass
class PropertySpec:
    name: str
    qualifier: str = ""
    optional: bool = False
    optional_reason: str = ""


@dataclass
class RuntimeEvent:
    name: str
    area: str
    event_type: str
    source: str
    properties: list[PropertySpec]
    inline_enums: dict
    group: str
    status: str
    section: str


@dataclass
class ProductConfig:
    product: str
    host: str
    project_id: str
    api_key_env: str


@dataclass
class Finding:
    severity: str
    rule_id: str
    rule_name: str
    message: str


@dataclass
class ProductRuntimeSummary:
    product: str
    exit_code: int = 0
    expected_event_count: int = 0
    sampled_event_count: int = 0
    skipped: bool = False
    skip_reason: str = ""
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    @property
    def error_count(self):
        return len(self.errors)

    @property
    def warning_count(self):
        return len(self.warnings)


class AutomationError(RuntimeError):
    pass


def load_validator_module():
    spec = importlib.util.spec_from_file_location("analytics_docs_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise AutomationError(f"Unable to load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_posthog_config(path=DEFAULT_CONFIG_PATH):
    if not Path(path).exists():
        return {}
    try:
        data = json.loads(Path(path).read_text())
    except json.JSONDecodeError as exc:
        raise AutomationError(f"PostHog config is not valid JSON: {exc}") from exc
    products = {}
    for row in data.get("products", []):
        product = str(row.get("product", "")).strip()
        if not product:
            raise AutomationError("PostHog config has a product row without product")
        products[product] = ProductConfig(
            product=product,
            host=str(row.get("host", "")).strip().rstrip("/"),
            project_id=str(row.get("project_id", "")).strip(),
            api_key_env=str(row.get("api_key_env", "")).strip(),
        )
    return products


def parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def is_fresh(last_seen_at, now, window_days):
    parsed = parse_iso_datetime(last_seen_at)
    if parsed is None:
        return False
    return parsed >= now - timedelta(days=window_days)


def _qualifier_policy(qualifier):
    q = qualifier.strip().lower()
    if not q:
        return False, ""
    if "optional" in q:
        return True, "optional"
    if q in TYPE_HINT_QUALIFIERS:
        return False, ""
    if " only" in q or q.endswith("only"):
        return True, "scope"
    return False, ""


def parse_properties_cell(validator, cell):
    names, inline_enums = validator.extract_props(cell)
    specs = []
    for name in names:
        qualifier = ""
        pattern = r"`" + re.escape(name) + r"`\s*(?:\(([^)]*)\))?"
        match = re.search(pattern, cell)
        if match:
            qualifier = (match.group(1) or "").strip()
        optional, reason = _qualifier_policy(qualifier)
        specs.append(
            PropertySpec(
                name=name,
                qualifier=qualifier,
                optional=optional,
                optional_reason=reason,
            )
        )
    return specs, inline_enums


def _catalog_event_section(validator, text):
    if hasattr(validator, "_catalog_event_section"):
        return validator._catalog_event_section(text)
    match = re.search(r"^##\s+Event Catalog\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    next_h2 = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    if next_h2:
        return text[match.start() : match.end() + next_h2.start()]
    return text[match.start() :]


def parse_runtime_catalog(validator, catalog_path):
    text = validator.strip_frontmatter(catalog_path.read_text())
    event_tables = validator.parse_tables(_catalog_event_section(validator, text))
    events = {}
    for heading, _header, rows in event_tables:
        for row in rows:
            if len(row) < 9:
                continue
            name = row[0].strip()
            if not name or name.startswith("["):
                continue
            properties, inline_enums = parse_properties_cell(validator, row[5])
            events[name] = RuntimeEvent(
                name=name,
                area=row[1].strip(),
                event_type=row[2].strip(),
                source=row[4].strip(),
                properties=properties,
                inline_enums=inline_enums,
                group=row[6].strip().strip("`"),
                status=row[8].strip(),
                section=heading,
            )
    return events


def parse_removed_events(validator, catalog_path):
    text = validator.strip_frontmatter(catalog_path.read_text())
    tables = validator.parse_tables(text)
    removed = set()
    _header, rows = validator._find_table(tables, "Removed Events")
    if rows:
        for row in rows:
            if not row:
                continue
            name = row[0].strip().strip("`")
            if not name or name.startswith("[") or name.startswith("_("):
                continue
            removed.add(name)
    return removed


def expected_catalog_events(events):
    return {name: event for name, event in events.items() if event.status in EXPECTED_STATUSES}


def slack_escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def truncate(value, limit=MAX_TEXT_CHARS):
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def display_product(product):
    return str(product).replace("-", " ").title()


def product_status(summary):
    if summary.exit_code == 2:
        return ":octagonal_sign: config issue"
    if summary.skipped:
        return ":double_vertical_bar: skipped"
    if summary.error_count:
        return ":x: needs attention"
    if summary.warning_count:
        return ":warning: warnings"
    return ":white_check_mark: clean"


def overall_status(summaries):
    if any(summary.exit_code == 2 for summary in summaries):
        return ":octagonal_sign: config issue"
    if any(summary.error_count for summary in summaries):
        return ":x: needs attention"
    if any(summary.warning_count for summary in summaries):
        return ":warning: warnings"
    return ":white_check_mark: clean"


def finding(severity, rule_id, rule_name, message):
    return Finding(severity=severity, rule_id=rule_id, rule_name=rule_name, message=message)


def add_finding(summary, severity, rule_id, rule_name, message):
    target = summary.errors if severity == "error" else summary.warnings
    target.append(finding(severity, rule_id, rule_name, message))


def grouped_findings(findings):
    groups = {}
    for item in findings:
        key = (item.rule_id, item.rule_name)
        groups.setdefault(key, []).append(item.message)
    return sorted(groups.items(), key=lambda entry: (-len(entry[1]), entry[0][0]))


def findings_text(summary):
    if summary.skipped:
        return summary.skip_reason
    if not summary.errors and not summary.warnings:
        return "All configured runtime checks passed."

    lines = []
    for label, findings in (("Top errors", summary.errors), ("Top warnings", summary.warnings)):
        groups = grouped_findings(findings)
        if not groups:
            continue
        if lines:
            lines.append("")
        lines.append(f"*{label}:*")
        for (rule_id, rule_name), messages in groups[:MAX_FINDING_GROUPS]:
            lines.append(f"- *{slack_escape(rule_id)}: {slack_escape(rule_name)}* ({len(messages)})")
            for message in messages[:MAX_FINDINGS_PER_GROUP]:
                lines.append(f"  - {slack_escape(truncate(message))}")
    return "\n".join(lines)


def section(text, fields=None):
    block = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }
    if fields:
        block["fields"] = [{"type": "mrkdwn", "text": field} for field in fields]
    return block


def github_run_url():
    server_url = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not all((server_url, repository, run_id)):
        return None
    return f"{server_url}/{repository}/actions/runs/{run_id}"


def build_blocks(summaries):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Daily PostHog Catalog Validation",
                "emoji": True,
            },
        }
    ]
    context = f"*Run time:* {timestamp}"
    run_url = github_run_url()
    if run_url:
        context += f" | <{run_url}|View GitHub run>"
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": context}]})
    blocks.append(
        section(
            f"*Overall:* {overall_status(summaries)}\n"
            f"*Products discovered:* {len(summaries)}"
        )
    )
    blocks.append({"type": "divider"})

    for index, summary in enumerate(summaries):
        if len(blocks) > MAX_BLOCKS - 4:
            remaining = len(summaries) - index
            blocks.append(section(f"*{remaining} additional products omitted from Slack.*"))
            break
        fields = [
            f"*Status*\n{product_status(summary)}",
            f"*Expected events*\n{summary.expected_event_count}",
            f"*Sampled events*\n{summary.sampled_event_count}",
            f"*Errors / Warnings*\n{summary.error_count} / {summary.warning_count}",
        ]
        blocks.append(section(f"*{display_product(summary.product)}*", fields=fields))
        blocks.append(section(findings_text(summary)))
        if index != len(summaries) - 1 and len(blocks) < MAX_BLOCKS:
            blocks.append({"type": "divider"})
    return blocks[:MAX_BLOCKS]


def fallback_text(summaries):
    parts = [
        f"{summary.product}: {product_status(summary)} "
        f"({summary.error_count} errors, {summary.warning_count} warnings)"
        for summary in summaries
    ]
    return f"Daily PostHog Catalog Validation - {overall_status(summaries)} - " + "; ".join(parts)


def build_payload(summaries):
    return {"text": fallback_text(summaries), "blocks": build_blocks(summaries)}


def post_to_slack(webhook_url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            if response.status < 200 or response.status >= 300:
                raise AutomationError(f"Slack webhook returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AutomationError(f"Slack webhook returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AutomationError(f"Slack webhook request failed: {exc.reason}") from exc


class PostHogClient:
    def __init__(self, host, project_id, api_key, timeout=30):
        if not host:
            raise AutomationError("PostHog host is required")
        if not project_id:
            raise AutomationError("PostHog project_id is required")
        if not api_key:
            raise AutomationError("PostHog personal API key is required")
        self.host = host.rstrip("/")
        self.project_id = project_id
        self.api_key = api_key
        self.timeout = timeout

    def _request_json(self, method, url, payload=None):
        data = None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AutomationError(f"PostHog API returned HTTP {exc.code}: {detail[:300]}") from exc
        except urllib.error.URLError as exc:
            raise AutomationError(f"PostHog API request failed: {exc.reason}") from exc
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise AutomationError(f"PostHog API returned invalid JSON: {exc}") from exc

    def project_url(self, path, params=None):
        url = f"{self.host}/api/projects/{urllib.parse.quote(str(self.project_id))}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def get_paginated(self, path, params=None):
        url = self.project_url(path, params or {})
        results = []
        while url:
            page = self._request_json("GET", url)
            if not isinstance(page, dict) or "results" not in page:
                raise AutomationError(f"PostHog paginated response missing results for {path}")
            results.extend(page.get("results") or [])
            url = page.get("next")
        return results

    def query(self, hogql, name):
        payload = {"query": {"kind": "HogQLQuery", "query": hogql}, "name": name}
        return self._request_json("POST", self.project_url("query/"), payload)


def quote_hogql_string(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def query_event_samples(client, event_name, window_days, sample_limit):
    hogql = (
        "select event, timestamp, properties "
        "from events "
        f"where event = {quote_hogql_string(event_name)} "
        f"and timestamp >= now() - interval {int(window_days)} day "
        "order by timestamp desc "
        f"limit {int(sample_limit)}"
    )
    response = client.query(hogql, f"daily catalog sample: {event_name}")
    return normalize_query_results(response)


def normalize_query_results(response):
    rows = response.get("results") if isinstance(response, dict) else None
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return rows
    columns = response.get("columns") or response.get("types") or []
    normalized_columns = []
    for column in columns:
        if isinstance(column, dict):
            normalized_columns.append(column.get("name") or column.get("key"))
        else:
            normalized_columns.append(str(column))
    if not normalized_columns:
        normalized_columns = ["event", "timestamp", "properties"]
    out = []
    for row in rows:
        if isinstance(row, (list, tuple)):
            out.append({normalized_columns[i]: value for i, value in enumerate(row) if i < len(normalized_columns)})
    return out


def property_definition_names(client):
    rows = client.get_paginated(
        "property_definitions/",
        {"type": "event", "exclude_core_properties": "true", "limit": 500},
    )
    return {row.get("name") for row in rows if row.get("name")}


def event_definitions_by_name(client):
    rows = client.get_paginated(
        "event_definitions/",
        {"exclude_hidden": "false", "exclude_stale": "false", "limit": 500},
    )
    return {row.get("name"): row for row in rows if row.get("name")}


def is_system_event(name):
    lower = str(name).lower()
    return lower.startswith(SYSTEM_EVENT_PREFIXES)


def is_blank(value):
    return value is None or value == ""


def safe_sample_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if len(text) <= 40 and re.match(r"^[A-Za-z0-9_. -]+$", text) and "@" not in text and "://" not in text:
        return text
    return f"<redacted {type(value).__name__}>"


def prop_dictionary_entry(prop_dict, name):
    entries = prop_dict.get(name) or []
    if not entries:
        return None, set()
    types = {entry.get("type", "").strip().lower() for entry in entries}
    allowed = set()
    for entry in entries:
        allowed.update(value for value in entry.get("allowed_values", []) if value)
    if "enum" in types:
        return "enum", allowed
    if "boolean" in types:
        return "boolean", allowed
    if "number" in types or "numeric" in types:
        return "number", allowed
    if "array" in types:
        return "array", allowed
    if "uuid" in types:
        return "uuid", allowed
    if "string" in types:
        return "string", allowed
    return next(iter(types), ""), allowed


def validate_value(prop_name, value, prop_type, allowed_values):
    if is_blank(value) or not prop_type:
        return None
    if prop_type == "enum":
        if str(value) not in allowed_values:
            return f"`{prop_name}` value {safe_sample_value(value)} is not in allowed values"
        return None
    if prop_type == "boolean" and not isinstance(value, bool):
        return f"`{prop_name}` expected boolean, saw {type(value).__name__}"
    if prop_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        return f"`{prop_name}` expected number, saw {type(value).__name__}"
    if prop_type == "array" and not isinstance(value, list):
        return f"`{prop_name}` expected array, saw {type(value).__name__}"
    if prop_type == "uuid":
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError, AttributeError):
            return f"`{prop_name}` expected UUID-shape value, saw {safe_sample_value(value)}"
    return None


def schema_required_properties(schema_event_props, event):
    required = set()
    source = event.source.lower()
    event_type = event.event_type
    for prop, info in schema_event_props.items():
        when = info.get("when", "").lower()
        if "all frontend events" in when and "frontend" in source:
            required.add(prop)
        if "all `user_action` events" in when and event_type == "Interaction":
            required.add(prop)
        if prop == "job_id" and event.group == "job":
            required.add(prop)
    if event.group == "job":
        required.add("job_id")
    return required


def required_property_names(schema_event_props, event):
    names = {spec.name for spec in event.properties if not spec.optional}
    names.update(schema_required_properties(schema_event_props, event))
    return names


def catalog_property_names(events):
    names = set()
    for event in events.values():
        names.update(spec.name for spec in event.properties)
    return names


def collect_event_drift(summary, catalog_events, event_defs, removed_events, now, window_days):
    catalog_names = set(catalog_events)
    expected_names = set(expected_catalog_events(catalog_events))

    for name in sorted(expected_names - set(event_defs)):
        matches = get_close_matches(name, event_defs.keys(), n=2, cutoff=0.82)
        suffix = f" Near matches: {', '.join(matches)}." if matches else ""
        add_finding(summary, "error", "event_definition", "Event definition coverage", f'"{name}" is missing from PostHog event definitions.{suffix}')

    for name, event in expected_catalog_events(catalog_events).items():
        definition = event_defs.get(name)
        if not definition:
            continue
        last_seen_at = definition.get("last_seen_at")
        if not last_seen_at:
            add_finding(summary, "error", "event_definition", "Event definition coverage", f'"{name}" has no last_seen_at in PostHog')
        elif not is_fresh(last_seen_at, now, window_days):
            add_finding(summary, "warning", "event_freshness", "Event freshness", f'"{name}" last seen at {last_seen_at}, outside the {window_days}-day window')

    unexpected = []
    for name, definition in event_defs.items():
        if name in catalog_names or is_system_event(name):
            continue
        if is_fresh(definition.get("last_seen_at"), now, window_days):
            unexpected.append(name)
    for name in sorted(unexpected)[:20]:
        add_finding(summary, "warning", "event_drift", "Uncataloged PostHog event", f'"{name}" is recent in PostHog but not in the catalog')

    for name in sorted(removed_events):
        definition = event_defs.get(name)
        if definition and is_fresh(definition.get("last_seen_at"), now, window_days):
            add_finding(summary, "warning", "removed_event", "Removed event still firing", f'"{name}" is listed as removed but was recently seen')

    for name, event in catalog_events.items():
        if event.status not in DEV_STATUSES:
            continue
        definition = event_defs.get(name)
        if definition and is_fresh(definition.get("last_seen_at"), now, window_days):
            add_finding(summary, "warning", "dev_event", "Dev event seen in production", f'"{name}" has status {event.status} but was recently seen')


def fresh_expected_events(expected_events, event_defs, now, window_days):
    out = {}
    for name, event in expected_events.items():
        definition = event_defs.get(name)
        if definition and is_fresh(definition.get("last_seen_at"), now, window_days):
            out[name] = event
    return out


def validate_samples(summary, event, samples, prop_dict, schema_event_props):
    required = required_property_names(schema_event_props, event)
    optional = {spec.name for spec in event.properties if spec.optional}
    for row in samples:
        properties = row.get("properties")
        if isinstance(properties, str):
            try:
                properties = json.loads(properties)
            except json.JSONDecodeError:
                properties = {}
        if not isinstance(properties, dict):
            properties = {}
        for prop in sorted(required):
            if prop not in properties:
                add_finding(summary, "error", "property_presence", "Required key presence", f'"{event.name}" sample is missing required key `{prop}`')
        for spec in event.properties:
            if spec.name not in properties:
                continue
            prop_type, allowed = prop_dictionary_entry(prop_dict, spec.name)
            error = validate_value(spec.name, properties.get(spec.name), prop_type, allowed)
            if error:
                rule = "enum_drift" if prop_type == "enum" else "value_type"
                name = "Enum drift" if prop_type == "enum" else "Declared type validation"
                add_finding(summary, "error", rule, name, f'"{event.name}": {error}')
        for prop in sorted(required - {spec.name for spec in event.properties} - optional):
            if prop not in properties:
                continue
            prop_type, allowed = prop_dictionary_entry(prop_dict, prop)
            error = validate_value(prop, properties.get(prop), prop_type, allowed)
            if error:
                rule = "enum_drift" if prop_type == "enum" else "value_type"
                name = "Enum drift" if prop_type == "enum" else "Declared type validation"
                add_finding(summary, "error", rule, name, f'"{event.name}": {error}')


def validate_product(product, validator, config, args, now):
    paths = validator.product_paths(product)
    catalog_events = parse_runtime_catalog(validator, paths.catalog_path)
    _catalog_events, prop_dict, _duplicates = validator.parse_catalog(paths.catalog_path)
    removed_events = parse_removed_events(validator, paths.catalog_path)
    (
        _std_objects,
        _person_props,
        schema_event_props,
        _result_pattern,
        _result_pattern_errors,
        _event_types,
    ) = validator.parse_schema(paths.schema_path, paths.shared_event_types_path)

    expected = expected_catalog_events(catalog_events)
    summary = ProductRuntimeSummary(product=product, expected_event_count=len(expected))
    if not catalog_events and paths.config.allow_empty_catalog:
        summary.skipped = True
        summary.skip_reason = "Catalog is intentionally empty for this product."
        return summary
    if not expected:
        summary.skipped = True
        summary.skip_reason = "No Live or Live (legacy) catalog events to check."
        return summary
    if config is None or not config.project_id:
        summary.skipped = True
        summary.skip_reason = "No PostHog project_id configured for this product."
        add_finding(summary, "warning", "config", "PostHog config", summary.skip_reason)
        return summary
    if not config.host:
        raise AutomationError(f"{product}: PostHog host is required when project_id is configured")
    if not config.api_key_env:
        raise AutomationError(f"{product}: api_key_env is required when project_id is configured")
    api_key = os.environ.get(config.api_key_env)
    if not api_key:
        raise AutomationError(f"{product}: environment variable {config.api_key_env} is required")

    client = PostHogClient(config.host, config.project_id, api_key)
    event_defs = event_definitions_by_name(client)
    collect_event_drift(summary, catalog_events, event_defs, removed_events, now, args.window_days)

    property_defs = property_definition_names(client)
    for prop in sorted(catalog_property_names(expected)):
        if prop.startswith("$"):
            continue
        if prop not in property_defs:
            add_finding(summary, "warning", "property_definition", "Property definition pre-filter", f"`{prop}` is used by expected catalog events but is not in PostHog event property definitions")

    fresh_events = fresh_expected_events(expected, event_defs, now, args.window_days)
    for name, event in sorted(fresh_events.items()):
        samples = query_event_samples(client, name, args.window_days, args.sample_limit)
        if not samples:
            add_finding(summary, "warning", "sample_mismatch", "Runtime sampling consistency", f'"{name}" is fresh by event definition but HogQL returned zero sample rows')
            continue
        summary.sampled_event_count += 1
        validate_samples(summary, event, samples, prop_dict, schema_event_props)
    return summary


def automation_summary(product, message):
    return ProductRuntimeSummary(
        product=product,
        exit_code=2,
        expected_event_count=0,
        errors=[
            finding("error", "automation", "Validator automation", message),
        ],
    )


def discover_products(validator):
    products = validator._discovered_products()
    if not products:
        raise AutomationError("No analytics products discovered")
    return products


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate product catalogs against recent PostHog runtime data.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print Slack JSON and skip posting.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to PostHog project config JSON.")
    parser.add_argument("--window-days", type=int, default=7, help="Freshness and sampling window in days.")
    parser.add_argument("--sample-limit", type=int, default=20, help="Maximum HogQL sample rows per event.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.window_days <= 0:
        raise AutomationError("--window-days must be positive")
    if args.sample_limit <= 0:
        raise AutomationError("--sample-limit must be positive")

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not args.dry_run and not webhook_url:
        raise AutomationError("SLACK_WEBHOOK_URL is required unless --dry-run is set")

    validator = load_validator_module()
    products = discover_products(validator)
    configs = load_posthog_config(args.config)
    now = datetime.now(timezone.utc)

    summaries = []
    automation_failed = False
    for product in products:
        try:
            summaries.append(validate_product(product, validator, configs.get(product), args, now))
        except Exception as exc:
            automation_failed = True
            summaries.append(automation_summary(product, str(exc)))

    payload = build_payload(summaries)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
    else:
        post_to_slack(webhook_url, payload)
    return 1 if automation_failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
