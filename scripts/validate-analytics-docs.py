#!/usr/bin/env python3
"""
Validates consistency across product-scoped analytics markdown documents:
  - event-catalog.md   (Event Catalog)
  - event-schema.md    (Schema)
  - dashboards.md      (Dashboards)

Run:  python scripts/validate-analytics-docs.py --product helix
Exit: 0 = all clear, 1 = errors found, 2 = parse failure
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
TRACKING_PLANS_DIR = REPO_ROOT / "tracking-plans"
LOGS_DIR = REPO_ROOT / "logs"
MAX_LOG_RUNS = 20
PRODUCT_LABELS = {
    "helix": "Helix",
    "recruit": "Recruit",
}

RULE_NAMES = {
    1: "Object coverage",
    2: "Interaction / Started / Result alignment",
    3: "Person property alignment",
    4: "Standard property compliance",
    5: "Funnel event existence",
    6: "Funnel area accuracy",
    7: "Dashboard property existence",
    8: "Dashboard enum accuracy",
    9: "Platform Health alignment",
    10: 'Property Dictionary "Used In"',
    11: "Inline enum consistency",
    12: "Naming conventions",
    13: "Event property coverage",
    14: "No duplicate names",
    15: "Action validity",
    16: "Result terminal form",
    17: "Event type validity",
}

TP_RULE_NAMES = {
    "TP0": "Standard Object declarations",
    "TP1": "Event naming conventions",
    "TP2": "Property naming conventions",
    "TP3": "No duplicate events vs catalog",
    "TP4": "Property coverage (catalog + tracking plan)",
    "TP5": "Standard property compliance",
    "TP6": "Interaction / Started / Result completeness",
    "TP7": "Standard Object usage",
    "TP8": "Funnel event validity",
    "TP9": "Inline enum consistency",
    "TP10": "Action validity",
    "TP11": "Result terminal form",
    "TP12": "Event type validity",
}

NEW_OBJECTS_SECTION = "New Standard Objects"
REMOVED_OBJECTS_SECTION = "Removed Standard Objects"
EVENT_RENAMES_SECTION = "Event Renames"


@dataclass
class TrackingPlanData:
    events: dict = field(default_factory=dict)
    result_pattern: list = field(default_factory=list)
    result_pattern_errors: list = field(default_factory=list)
    funnels: dict = field(default_factory=dict)
    prop_dict: dict = field(default_factory=dict)
    added_objects: dict = field(default_factory=dict)
    removed_objects: dict = field(default_factory=dict)
    declaration_errors: list = field(default_factory=list)


@dataclass
class ProductConfig:
    analytics_platform: str = ""
    allow_empty_catalog: bool = False
    group_property_rules: list = field(default_factory=list)
    area_property_rules: list = field(default_factory=list)
    persona_rules: list = field(default_factory=list)


@dataclass
class ProductPaths:
    product: str
    docs_dir: Path
    catalog_path: Path
    schema_path: Path
    dashboard_path: Path
    shared_event_types_path: Path
    tracking_plans_dir: Path
    log_path: Path
    config: ProductConfig = field(default_factory=ProductConfig)


class ProductPathError(ValueError):
    pass


REQUIRED_PRODUCT_DOCS = ("event-catalog.md", "event-schema.md", "dashboards.md")


def _discovered_products():
    products = []
    if not DOCS_DIR.exists():
        return products
    for p in sorted(DOCS_DIR.iterdir()):
        if p.name == "shared" or not p.is_dir():
            continue
        if all((p / doc).exists() for doc in REQUIRED_PRODUCT_DOCS):
            products.append(p.name)
    return products


def product_paths(product):
    if product == "shared":
        raise ProductPathError('"shared" is reserved and cannot be validated as a product')

    docs_dir = DOCS_DIR / product
    missing = [doc for doc in REQUIRED_PRODUCT_DOCS if not (docs_dir / doc).exists()]
    if missing:
        discovered = _discovered_products()
        listing = ", ".join(discovered) if discovered else "(none)"
        raise ProductPathError(
            f'Unknown or incomplete product "{product}". '
            f"Discovered products: {listing}"
        )

    schema_path = docs_dir / "event-schema.md"
    return ProductPaths(
        product=product,
        docs_dir=docs_dir,
        catalog_path=docs_dir / "event-catalog.md",
        schema_path=schema_path,
        dashboard_path=docs_dir / "dashboards.md",
        shared_event_types_path=DOCS_DIR / "shared" / "naming-and-event-types.md",
        tracking_plans_dir=TRACKING_PLANS_DIR / product,
        log_path=LOGS_DIR / product / "conflicts-log.md",
        config=parse_product_config(schema_path),
    )

# ── Markdown Parsing ─────────────────────────────────────────────────────────


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :]
    return text


def _frontmatter_text(text):
    if not text.startswith("---"):
        return ""
    end = text.find("---", 3)
    if end == -1:
        raise ValueError("Frontmatter starts with --- but has no closing ---")
    return text[3:end].strip("\n")


def _parse_config_scalar(raw):
    value = raw.strip()
    if not value:
        return ""
    if value in ("true", "false"):
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_config_scalar(part.strip()) for part in inner.split(",")]
    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    return value


def _parse_frontmatter_list(lines, start_index, key):
    items = []
    item = None
    i = start_index
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if not line.startswith(" "):
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            if item is not None:
                items.append(item)
            item = {}
            stripped = stripped[2:].strip()
            if stripped:
                if ":" not in stripped:
                    raise ValueError(f"Invalid {key} list item: {line.strip()}")
                field, raw = stripped.split(":", 1)
                item[field.strip()] = _parse_config_scalar(raw)
        else:
            if item is None:
                raise ValueError(f"Invalid {key} list indentation: {line.strip()}")
            if ":" not in stripped:
                raise ValueError(f"Invalid {key} field: {line.strip()}")
            field, raw = stripped.split(":", 1)
            item[field.strip()] = _parse_config_scalar(raw)
        i += 1
    if item is not None:
        items.append(item)
    return items, i


def _validate_config_keys(key, rows, allowed_fields):
    for row in rows:
        unknown = sorted(set(row) - set(allowed_fields))
        if unknown:
            raise ValueError(
                f"Unsupported field(s) in {key}: {', '.join(unknown)}"
            )


def parse_product_config(path):
    """Parse the small, supported config subset from schema frontmatter."""
    text = path.read_text()
    frontmatter = _frontmatter_text(text)
    if not frontmatter:
        return ProductConfig()

    scalar_keys = {"analytics_platform", "allow_empty_catalog"}
    list_keys = {"group_property_rules", "area_property_rules", "persona_rules"}
    config = ProductConfig()
    lines = frontmatter.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith(" "):
            i += 1
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line.strip()}")
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if key in scalar_keys:
            value = _parse_config_scalar(raw)
            if key == "allow_empty_catalog" and not isinstance(value, bool):
                raise ValueError("allow_empty_catalog must be true or false")
            setattr(config, key, value)
            i += 1
            continue
        if key in list_keys:
            if raw:
                raise ValueError(f"{key} must be an indented list")
            rows, i = _parse_frontmatter_list(lines, i + 1, key)
            setattr(config, key, rows)
            continue
        i += 1

    _validate_config_keys(
        "group_property_rules",
        config.group_property_rules,
        {"group", "property", "catalog_warning_types", "tracking_plan_severity"},
    )
    _validate_config_keys(
        "area_property_rules",
        config.area_property_rules,
        {"area_contains", "property", "severity"},
    )
    _validate_config_keys(
        "persona_rules",
        config.persona_rules,
        {"section_contains", "property", "applies_if_in_schema"},
    )
    return config


_PIPE_PLACEHOLDER = "\x00"


def _split_row(line):
    """Split a markdown table row, replacing escaped pipes first."""
    safe = line.replace("\\|", _PIPE_PLACEHOLDER)
    return [c.strip().replace(_PIPE_PLACEHOLDER, "|") for c in safe.split("|")[1:-1]]


def parse_tables(text):
    """Return list of (heading, header_cells, data_rows) for every table."""
    lines = text.split("\n")
    results = []
    heading = ""
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        hm = re.match(r"^(#{1,6})\s+(.+)$", s)
        if hm:
            heading = hm.group(2).strip()
            i += 1
            continue
        if s.startswith("|") and s.endswith("|"):
            header = _split_row(s)
            i += 1
            if i < len(lines):
                sep = lines[i].strip()
                sep_cells = sep.split("|")[1:-1]
                if sep.startswith("|") and all(
                    re.match(r"^[\s:-]+$", c) for c in sep_cells if c.strip()
                ):
                    i += 1
                    rows = []
                    while i < len(lines):
                        rl = lines[i].strip()
                        if rl.startswith("|") and rl.endswith("|"):
                            rows.append(_split_row(rl))
                            i += 1
                        else:
                            break
                    results.append((heading, header, rows))
                    continue
        i += 1
    return results


def _find_table(tables, pattern):
    for h, header, rows in tables:
        if pattern.lower() in h.lower():
            return header, rows
    return None, None


RESULT_PATTERN_HEADING = "Interaction / Started / Result Pattern"
RESULT_PATTERN_REQUIRED_COLUMNS = [
    "Flow",
    "Interaction / Started Event",
    "Success Event",
    "Rejected Event",
]
RESULT_PATTERN_OPTIONAL_COLUMNS = ["Error Event"]
RESULT_PATTERN_EVENT_KEYS = ("interaction_started", "success", "rejected", "error")
RESULT_PATTERN_ROLE_LABELS = {
    "interaction_started": "interaction / started",
    "success": "success",
    "rejected": "rejected",
    "error": "error",
}


def _normalize_table_header(cell):
    return re.sub(r"\s+", " ", cell.strip())


def _result_pattern_column_error(source_label):
    return (
        f'{source_label} "{RESULT_PATTERN_HEADING}" table must use columns: '
        "Flow | Interaction / Started Event | Success Event | Rejected Event "
        "(optional: Error Event)."
    )


def _parse_result_pattern_table(tables, source_label):
    rows_out = []
    errors = []
    found = False

    for heading, header, rows in tables:
        normalized_heading = heading.strip()
        lower_heading = normalized_heading.lower()
        if "intent" in lower_heading and (
            "outcome" in lower_heading or "pattern" in lower_heading
        ):
            errors.append(
                f'{source_label} uses old "Intent vs Outcome" table heading; '
                f'use "{RESULT_PATTERN_HEADING}".'
            )
            continue
        if normalized_heading != RESULT_PATTERN_HEADING:
            continue

        found = True
        normalized_header = [_normalize_table_header(h) for h in header]
        col = {h: i for i, h in enumerate(normalized_header)}
        allowed_columns = set(RESULT_PATTERN_REQUIRED_COLUMNS) | set(
            RESULT_PATTERN_OPTIONAL_COLUMNS
        )
        if (
            any(c not in col for c in RESULT_PATTERN_REQUIRED_COLUMNS)
            or "Intent Event" in col
            or "Failure Event" in col
            or any(c not in allowed_columns for c in normalized_header)
        ):
            errors.append(_result_pattern_column_error(source_label))
            continue

        for row in rows:
            flow = row[col["Flow"]].strip() if col["Flow"] < len(row) else ""
            if not flow or flow.startswith("["):
                continue
            rows_out.append(
                dict(
                    flow=flow,
                    interaction_started=(
                        row[col["Interaction / Started Event"]].strip()
                        if col["Interaction / Started Event"] < len(row)
                        else ""
                    ),
                    success=(
                        row[col["Success Event"]].strip()
                        if col["Success Event"] < len(row)
                        else ""
                    ),
                    rejected=(
                        row[col["Rejected Event"]].strip()
                        if col["Rejected Event"] < len(row)
                        else ""
                    ),
                    error=(
                        row[col["Error Event"]].strip()
                        if "Error Event" in col and col["Error Event"] < len(row)
                        else "--"
                    ),
                )
            )

    if not found and not errors:
        errors.append(
            f'{source_label} is missing "{RESULT_PATTERN_HEADING}" table.'
        )
    return rows_out, errors


def _parse_platform_health_table(tables):
    rows_out = []
    errors = []
    header, rows = _find_table(tables, "Platform Health")
    if rows is None:
        return rows_out, errors

    normalized_header = [_normalize_table_header(h) for h in (header or [])]
    col = {h: i for i, h in enumerate(normalized_header)}
    allowed_columns = set(RESULT_PATTERN_REQUIRED_COLUMNS) | set(
        RESULT_PATTERN_OPTIONAL_COLUMNS
    )
    if (
        any(c not in col for c in RESULT_PATTERN_REQUIRED_COLUMNS)
        or "Intent Event" in col
        or "Failure Event" in col
        or any(c not in allowed_columns for c in normalized_header)
    ):
        errors.append(
            "Platform Health table must use columns: "
            "Flow | Interaction / Started Event | Success Event | Rejected Event "
            "(optional: Error Event)."
        )
        return rows_out, errors

    for row in rows:
        flow = row[col["Flow"]].strip() if col["Flow"] < len(row) else ""
        if not flow or flow.startswith("["):
            continue
        rows_out.append(
            dict(
                flow=flow,
                interaction_started=(
                    row[col["Interaction / Started Event"]].strip()
                    if col["Interaction / Started Event"] < len(row)
                    else ""
                ),
                success=(
                    row[col["Success Event"]].strip()
                    if col["Success Event"] < len(row)
                    else ""
                ),
                rejected=(
                    row[col["Rejected Event"]].strip()
                    if col["Rejected Event"] < len(row)
                    else ""
                ),
                error=(
                    row[col["Error Event"]].strip()
                    if "Error Event" in col and col["Error Event"] < len(row)
                    else "--"
                ),
            )
        )
    return rows_out, errors


def _is_table_separator(line):
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return False
    sep_cells = s.split("|")[1:-1]
    return bool(sep_cells) and all(
        re.match(r"^[\s:-]+$", c) for c in sep_cells if c.strip()
    )


def _heading_match(line):
    return re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)


def _malformed_section_message(section_name):
    if section_name == NEW_OBJECTS_SECTION:
        return (
            'Tracking plan section "New Standard Objects" must use columns: '
            "Object | Entity | Example Events."
        )
    return (
        'Tracking plan section "Removed Standard Objects" must use columns: '
        "Object, optionally followed by Reason."
    )


def _empty_object_message(section_name):
    if section_name == NEW_OBJECTS_SECTION:
        return (
            "## New Standard Objects has a row with an empty Object cell. "
            "Every declaration row must name an object."
        )
    return (
        "## Removed Standard Objects has a row with an empty Object cell. "
        "Every removal row must name an object."
    )


def _find_heading_sections(lines, section_name):
    matches = []
    for i, line in enumerate(lines):
        hm = _heading_match(line)
        if not hm or hm.group(2).strip().lower() != section_name.lower():
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if _heading_match(lines[j]):
                end = j
                break
        matches.append((i + 1, end))
    return matches


def _parse_object_declaration_section(lines, section_name):
    entries = {}
    errors = []

    # Find the first valid markdown table in the section.
    # Allows prose/explanatory text before the table.
    table_start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if i + 1 < len(lines) and _is_table_separator(lines[i + 1]):
                table_start = i
                break

    if table_start is None:
        # Empty section is OK (no declarations). But an active section
        # with prose and no table means the author intended to declare
        # something but forgot the table — error so they fix it.
        if any(line.strip() for line in lines):
            errors.append(_malformed_section_message(section_name))
        return entries, errors

    header = _split_row(lines[table_start].strip())
    if section_name == NEW_OBJECTS_SECTION:
        expected = ["Object", "Entity", "Example Events"]
        if header != expected:
            errors.append(_malformed_section_message(section_name))
            return entries, errors
    else:
        if header not in (["Object"], ["Object", "Reason"]):
            errors.append(_malformed_section_message(section_name))
            return entries, errors

    row_len = len(header)
    i = table_start + 2
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if not (s.startswith("|") and s.endswith("|")):
            break
        row = _split_row(s)
        if len(row) != row_len:
            errors.append(_malformed_section_message(section_name))
            i += 1
            continue
        obj = row[0].strip()
        if not obj:
            errors.append(_empty_object_message(section_name))
            i += 1
            continue
        if obj.startswith("[") and obj.endswith("]"):
            i += 1
            continue
        if obj in entries:
            errors.append(
                f'## {section_name} declares "{obj}" more than once. '
                "Keep a single row per object."
            )
            i += 1
            continue
        if section_name == NEW_OBJECTS_SECTION:
            examples = [e.strip() for e in row[2].split(",") if e.strip()]
            entries[obj] = dict(entity=row[1].strip(), example_events=examples)
        else:
            reason = row[1].strip() if row_len == 2 else ""
            entries[obj] = dict(reason=reason)
        i += 1

    return entries, list(dict.fromkeys(errors))


def _parse_object_declarations(text):
    declaration_text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = declaration_text.splitlines()
    all_errors = []
    parsed = {}

    for section_name in (NEW_OBJECTS_SECTION, REMOVED_OBJECTS_SECTION):
        sections = _find_heading_sections(lines, section_name)
        if len(sections) > 1:
            all_errors.append(
                f'Tracking plan section "{section_name}" appears more than once.'
            )
        if not sections:
            parsed[section_name] = {}
            continue
        start, end = sections[0]
        entries, errors = _parse_object_declaration_section(
            lines[start:end], section_name
        )
        parsed[section_name] = entries
        all_errors.extend(errors)

    return (
        parsed.get(NEW_OBJECTS_SECTION, {}),
        parsed.get(REMOVED_OBJECTS_SECTION, {}),
        all_errors,
    )


def _is_placeholder_cell(value):
    value = value.strip()
    return not value or value in {"--", "—"} or value.startswith("[")


def _normalize_event_type(value):
    raw = value.strip().strip("`")
    if _is_placeholder_cell(raw):
        return None
    aliases = {
        "view": "View",
        "viewed": "View",
        "interaction": "Interaction",
        "clicked": "Interaction",
        "started": "Started",
        "success": "Success",
        "succeeded": "Success",
        "rejected": "Rejected",
        "error": "Error",
        "errored": "Error",
    }
    return aliases.get(raw.lower(), raw)


def _infer_event_type_from_heading(heading):
    h = heading.lower()
    if "interaction" in h:
        return "Interaction"
    if "started" in h:
        return "Started"
    if "success" in h or "succeeded" in h:
        return "Success"
    if "rejected" in h:
        return "Rejected"
    if "error" in h or "errored" in h:
        return "Error"
    if "view" in h:
        return "View"
    return None


def _infer_event_type_from_name(name):
    words = name.split()
    return _normalize_event_type(words[-1]) if words else None


def _parse_event_renames(text):
    """Parse ## Event Renames rows as planned post-merge event names."""
    active_text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    section = _extract_h2_section(active_text, EVENT_RENAMES_SECTION)
    if not section:
        return {}

    renamed_events = {}
    for heading, header, rows in parse_tables(section):
        col = {h.strip().lower(): i for i, h in enumerate(header or [])}
        new_idx = col.get("new name")
        if new_idx is None:
            continue
        old_idx = col.get("current name")
        if old_idx is None:
            old_idx = col.get("old name")

        def _cell(row, key):
            i = col.get(key)
            return row[i].strip() if i is not None and i < len(row) else ""

        for row in rows:
            if new_idx >= len(row):
                continue
            name = row[new_idx].strip()
            if _is_placeholder_cell(name):
                continue

            raw_type = _cell(row, "new type") or _cell(row, "type")
            event_type = (
                _normalize_event_type(raw_type)
                or _infer_event_type_from_heading(heading)
                or _infer_event_type_from_name(name)
            )
            renamed_from = (
                row[old_idx].strip()
                if old_idx is not None and old_idx < len(row)
                else ""
            )
            renamed_events[name] = dict(
                area="",
                type=event_type,
                properties=[],
                inline_enums={},
                group="",
                person_props={},
                group_props={},
                renamed_from=renamed_from,
            )

    return renamed_events


# ── Cell-Level Parsing ───────────────────────────────────────────────────────


def extract_props(cell):
    """
    Return (property_names, inline_enums) from a Properties cell.
    inline_enums: dict mapping prop name -> list of enum values.
    """
    props = []
    enums = {}
    for m in re.finditer(r"`(\w+)`\s*:\s*((?:`[^`]+`\s*\|\s*)*`[^`]+`)", cell):
        p = m.group(1)
        vals = [v.strip().strip("`") for v in m.group(2).split("|")]
        props.append(p)
        enums[p] = vals
    enum_vals = {v for vs in enums.values() for v in vs}
    for m in re.finditer(r"`(\w+)`", cell):
        tok = m.group(1)
        if tok not in props and tok not in enum_vals and re.match(r"^[a-z_]\w*$", tok):
            props.append(tok)
    return list(dict.fromkeys(props)), enums


def parse_property_updates(cell):
    """Return (person_props: {name: method}, group_props: {name: group})."""
    c = cell.strip().strip("`").strip()
    person, groups = {}, {}
    if c in ("--", ""):
        return person, groups
    for m in re.finditer(r"\$set_once:\s*([\w,\s]+)", c):
        for p in m.group(1).split(","):
            p = p.strip()
            if p:
                person[p] = "$set_once"
    for m in re.finditer(r"(?<!\w)\$set:\s*([\w,\s]+)", c):
        for p in m.group(1).split(","):
            p = p.strip()
            if p:
                person[p] = "$set"
    for m in re.finditer(r"group\((\w+)\):\s*([\w,\s]+)", c):
        gn = m.group(1)
        for p in m.group(2).split(","):
            p = p.strip()
            if p:
                groups[p] = gn
    return person, groups


# ── Document Parsers ─────────────────────────────────────────────────────────


def _extract_h2_section(text, section_name):
    """Extract text between a ## heading and the next ## heading."""
    pattern = r"^##\s+" + re.escape(section_name) + r"\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return ""
    rest = text[match.end():]
    next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
    if next_h2:
        return rest[:next_h2.start()]
    return rest


def _catalog_event_section(text):
    match = re.search(r"^##\s+Event Catalog\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    next_h2 = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    if next_h2:
        return text[match.start() : match.end() + next_h2.start()]
    return text[match.start() :]


def parse_catalog(path):
    """
    Returns:
      events  – dict[name, {...}]
      prop_dict – dict[base_prop, list[{qualifier, type, allowed_values, used_in}]]
      duplicate_events – dict[name, count] for names appearing more than once
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)
    event_tables = parse_tables(_catalog_event_section(text))
    events = {}
    duplicate_events = {}
    for heading, _header, rows in event_tables:
        for row in rows:
            if len(row) < 9:
                continue
            name = row[0].strip()
            if name in events:
                duplicate_events[name] = duplicate_events.get(name, 1) + 1
            props, inline_enums = extract_props(row[5])
            person, grp = parse_property_updates(row[7])
            events[name] = dict(
                area=row[1].strip(),
                type=row[2].strip(),
                section=heading,
                properties=props,
                inline_enums=inline_enums,
                group=row[6].strip(),
                person_props=person,
                group_props=grp,
                status=row[8].strip(),
            )

    prop_dict = {}

    def _add_prop(raw_name, ptype, allowed, used_in):
        clean = re.sub(r"`", "", raw_name).strip()
        m = re.match(r"(\w+)(?:\s*\(([^)]+)\))?", clean)
        if not m:
            return
        base, qual = m.group(1), m.group(2)
        prop_dict.setdefault(base, []).append(
            dict(qualifier=qual, type=ptype, allowed_values=allowed, used_in=used_in)
        )

    _, enum_rows = _find_table(tables, "Enum Properties")
    if enum_rows:
        for r in enum_rows:
            if len(r) >= 5:
                vals = [v.strip().strip("`") for v in r[3].split(",")]
                used = [e.strip() for e in r[4].split(",")]
                _add_prop(r[0].strip().strip("`"), "enum", vals, used)

    for section, ptype, used_idx in [
        ("Array Properties", "array", 4),
        ("Boolean Properties", "boolean", 3),
        ("Numeric Properties", "number", 4),
        ("String Properties", "string", 4),
        ("UUID Properties", "UUID", 4),
    ]:
        _, rows = _find_table(tables, section)
        if rows:
            for r in rows:
                if len(r) > used_idx:
                    raw = r[0].strip().strip("`")
                    used = [e.strip() for e in r[used_idx].split(",")]
                    _add_prop(raw, ptype, [], used)

    return events, prop_dict, duplicate_events


def parse_shared_event_types(path):
    event_types = set()
    if not path.exists():
        return event_types
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)
    _, et_rows = _find_table(tables, "Event Types")
    if et_rows:
        for r in et_rows:
            if r:
                t = r[0].strip().strip("`").strip()
                if t:
                    event_types.add(t)
    return event_types


def parse_schema(path, shared_event_types_path=None):
    """
    Returns:
      std_objects    – dict[obj, {entity, example_events}]
      person_props   – dict[prop, {type, method}]
      std_event_props – dict[prop, {when}]
      result_pattern – list[{flow, interaction_started, success, rejected, error}]
      result_pattern_errors – list[str]
      event_types    – set[str] of allowed event types (empty if table absent)
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)

    std_objects = {}
    _, obj_rows = _find_table(tables, "Standard Objects")
    if obj_rows:
        for r in obj_rows:
            if len(r) >= 3:
                obj = r[0].strip()
                exs = [e.strip() for e in r[2].split(",")]
                std_objects[obj] = dict(entity=r[1].strip(), example_events=exs)

    person_props = {}
    # $set_once sub-table: Property | Type | Values | Set By | Description
    _, pp_once_rows = _find_table(tables, "Immutable, set once")
    if pp_once_rows:
        for r in pp_once_rows:
            if len(r) >= 5:
                prop = r[0].strip().strip("`")
                person_props[prop] = dict(type=r[1].strip(), method="$set_once")
    # $set sub-table: Property | Type | Set By | Description
    _, pp_set_rows = _find_table(tables, "Updated on every login")
    if pp_set_rows:
        for r in pp_set_rows:
            if len(r) >= 4:
                prop = r[0].strip().strip("`")
                person_props[prop] = dict(type=r[1].strip(), method="$set")

    std_event_props = {}
    _, sep_rows = _find_table(tables, "Standard Event Properties")
    if sep_rows:
        for r in sep_rows:
            if len(r) >= 4:
                prop = r[0].strip().strip("`")
                std_event_props[prop] = dict(when=r[3].strip())

    source_label = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
    result_pattern, result_pattern_errors = _parse_result_pattern_table(
        tables, f"{source_label}"
    )

    # Event Types enum (first column -> set of allowed types).
    event_types = set()
    _, et_rows = _find_table(tables, "Event Types")
    if et_rows:
        for r in et_rows:
            if r:
                t = r[0].strip().strip("`").strip()
                if t:
                    event_types.add(t)
    if shared_event_types_path is not None:
        shared_types = parse_shared_event_types(shared_event_types_path)
        if shared_types:
            event_types = shared_types

    return (
        std_objects,
        person_props,
        std_event_props,
        result_pattern,
        result_pattern_errors,
        event_types,
    )


def parse_dashboards(path):
    """
    Returns:
      funnels        – dict[name, list[{stage, event, defined_in}]]
      platform_health – list[{flow, interaction_started, success, rejected, error}]
      platform_health_errors – list[str]
      dashboard_props – dict[dashboard, {properties, property_values}]
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)

    funnels = {}
    for heading, _h, rows in tables:
        if "loop" in heading.lower():
            entries = []
            for r in rows:
                if len(r) >= 4:
                    entries.append(
                        dict(
                            stage=r[0].strip(),
                            event=r[2].strip(),
                            defined_in=r[3].strip(),
                        )
                    )
            funnels[heading] = entries

    platform_health, platform_health_errors = _parse_platform_health_table(tables)

    dashboard_props = {}
    sections = re.split(r"^(###\s+.+)$", text, flags=re.MULTILINE)
    for i in range(1, len(sections), 2):
        heading = sections[i].strip().lstrip("#").strip()
        if "dashboard" not in heading.lower():
            continue
        if i + 1 >= len(sections):
            continue
        body = sections[i + 1]
        next_h2 = re.search(r"^##\s", body, re.MULTILINE)
        if next_h2:
            body = body[: next_h2.start()]

        props = re.findall(r"`([a-z_]\w*)`", body)
        prop_values = {}
        for m in re.finditer(r"`([a-z_]\w*)`\s*:\s*([^)\n`]+)", body):
            prop = m.group(1)
            raw = m.group(2).strip().rstrip(")")
            vals = [v.strip() for v in re.split(r"\s*/\s*", raw) if v.strip()]
            if vals:
                prop_values[prop] = vals
        for m in re.finditer(r"`([a-z_]\w*)`\s*\(([^)]+)\)", body):
            prop = m.group(1)
            if prop not in prop_values:
                inner = m.group(2)
                vals = [
                    v.strip()
                    for v in re.split(r"\s*(?:vs\.?|/)\s*", inner)
                    if v.strip()
                ]
                if vals:
                    prop_values[prop] = vals

        dashboard_props[heading] = dict(
            properties=list(set(props)), property_values=prop_values
        )

    return funnels, platform_health, platform_health_errors, dashboard_props


def parse_tracking_plan(path):
    """
    Parse a tracking plan markdown file.

    Returns:
      TrackingPlanData with events, result-pattern rows, funnels, property
      details, object declarations, and declaration parse errors. Each event in
      `.events` carries a `type` key (None when the New Events table has no
      Type column).
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)
    added_objects, removed_objects, declaration_errors = _parse_object_declarations(
        text
    )

    # ── New Events table (header-keyed: tolerant of extra/reordered columns) ──
    tp_events = {}
    ev_header, ev_rows = _find_table(tables, "New Events")
    if ev_rows:
        col = {h.strip().lower(): i for i, h in enumerate(ev_header or [])}
        has_type = "type" in col

        def _cell(row, key):
            i = col.get(key)
            return row[i].strip() if i is not None and i < len(row) else ""

        for row in ev_rows:
            name = _cell(row, "event")
            if not name or name.startswith("["):
                continue
            props, inline_enums = extract_props(_cell(row, "key properties"))
            person, grp = parse_property_updates(_cell(row, "property updates"))
            tp_events[name] = dict(
                area=_cell(row, "area"),
                type=_cell(row, "type") if has_type else None,
                properties=props,
                inline_enums=inline_enums,
                group=_cell(row, "group"),
                person_props=person,
                group_props=grp,
            )

    for name, event in _parse_event_renames(text).items():
        tp_events.setdefault(name, event)

    # ── Interaction / Started / Result Pattern table ──
    tp_result_pattern, tp_result_pattern_errors = _parse_result_pattern_table(
        tables, f"{path}"
    )

    # ── Funnels table ──
    # Supports two formats:
    #   Old: flat table directly under ## Funnels with Funnel Name | Steps | Purpose
    #   New: per-funnel H3 tables with Step | Event | Filter columns
    # Both parsers are scoped to the ## Funnels section only.
    tp_funnels = {}
    funnels_section = _extract_h2_section(text, "Funnels")
    if funnels_section:
        funnels_tables = parse_tables(funnels_section)
        # Old format: look for a table with old-style headers
        OLD_FUNNEL_HEADERS = {"funnel name", "funnel", "steps", "purpose"}
        for heading, header, rows in funnels_tables:
            normalized = {h.strip().lower() for h in header}
            if "steps" in normalized and normalized & {"funnel name", "funnel"}:
                for row in rows:
                    if len(row) < 2:
                        continue
                    fname = row[0].strip()
                    if not fname or fname.startswith("["):
                        continue
                    steps = [
                        s.strip()
                        for s in re.split(r"\s*(?:→|-->|->)\s*", row[1])
                        if s.strip()
                    ]
                    tp_funnels[fname] = steps
                break

    # Fallback: per-funnel step tables (Step | Event | Filter)
    if not tp_funnels and funnels_section:
        for heading, header, rows in funnels_tables:
                normalized = [h.strip().lower() for h in header]
                if "step" in normalized and "event" in normalized:
                    event_col = normalized.index("event")
                    steps = []
                    for row in rows:
                        if event_col < len(row):
                            ev = row[event_col].strip()
                            if ev and not ev.startswith("["):
                                steps.append(ev)
                    if steps:
                        tp_funnels[heading] = steps

    # ── Property Details table ──
    tp_prop_dict = {}
    _, pd_rows = _find_table(tables, "Property Details")
    if pd_rows:
        for row in pd_rows:
            if len(row) < 3:
                continue
            prop = row[0].strip().strip("`")
            if not prop or prop.startswith("["):
                continue
            ptype = row[1].strip()
            values = [v.strip() for v in row[2].split("/") if v.strip()] if row[2].strip() else []
            tp_prop_dict[prop] = dict(type=ptype, values=values)

    return TrackingPlanData(
        events=tp_events,
        result_pattern=tp_result_pattern,
        result_pattern_errors=tp_result_pattern_errors,
        funnels=tp_funnels,
        prop_dict=tp_prop_dict,
        added_objects=added_objects,
        removed_objects=removed_objects,
        declaration_errors=declaration_errors,
    )


# ── Validation Rules ─────────────────────────────────────────────────────────

# Canonical result terminals. "Failed"/"Error"/"Success"/"Failure" are invalid.
RESULT_TERMINALS = {"Succeeded", "Rejected", "Errored"}
# Non-canonical result words -> required canonical form (Rule 16 / TP11).
RESULT_VARIANTS = {
    "Fail": "Rejected", "Fails": "Rejected", "Failed": "Rejected",
    "Failure": "Rejected", "Failures": "Rejected",
    "Succeed": "Succeeded", "Succeeds": "Succeeded", "Success": "Succeeded",
    "Error": "Errored", "Errors": "Errored",
}
IRREGULAR_PAST = {"Made", "Sent", "Withdrawn"}
# Type -> required name terminals (Rule 16 / TP11).
TYPE_TERMINALS = {
    "Started": ("Started",),
    "Success": ("Succeeded",),
    "Rejected": ("Rejected",),
    "Error": ("Errored",),
}


def _object_prefix(event_name, known_objects):
    """Match the longest known object that is a prefix of the event name.
    Exact equality counts — the event is then all object, no action
    (Rule 15 / TP10 flag the missing action)."""
    for obj in sorted(known_objects, key=len, reverse=True):
        if event_name == obj or event_name.startswith(obj + " "):
            return obj
    return None


def _split_object_action(event_name, known_objects):
    """Segregate an event name into (object, action).
    Object = longest known Standard Object prefix (or exact match);
    action = remainder ('' on exact match).
    Returns (None, None) when no known object matches."""
    obj = _object_prefix(event_name, known_objects)
    if not obj:
        return None, None
    return obj, event_name[len(obj):].strip()


def _candidate_object(event_name):
    """Suggest the likely object for an event whose prefix is unknown.
    Result events ('... Publish Rejected') carry a verb-noun before the
    terminal — that word belongs to the ACTION, so drop two words; plain
    events drop only the trailing verb."""
    words = event_name.split()
    if not words:
        return None
    result_words = RESULT_TERMINALS | set(RESULT_VARIANTS)
    drop = 2 if words[-1] in result_words else 1
    return " ".join(words[:-drop]) if len(words) > drop else None


def _unknown_object_error(name):
    """Message for an event whose object prefix is not a known Standard Object,
    with a candidate-object suggestion when one can be derived."""
    msg = f'Event "{name}" uses an object prefix not in Standard Objects table'
    cand = _candidate_object(name)
    if cand:
        msg += (
            f' (likely object: "{cand}" — add it to the product event-schema.md, or '
            f"rename the event; the verb-noun before Succeeded/Rejected/Errored is "
            f"part of the action)"
        )
    return msg


def _is_general_usage(text):
    t = text.strip().lower()
    return (
        t.startswith("all ")
        or "(standard property)" in t
        or "(person property)" in t
        or t == "(person property)"
    )


def _parse_exceptions(when_text):
    """Extract event names from an 'except X, Y' clause in a 'When to Include' cell."""
    m = re.search(r"except\s+(.+?)(?:\s*\)|$)", when_text, re.IGNORECASE)
    if not m:
        return set()
    return {e.strip() for e in m.group(1).split(",")}


def _object_for_interaction_event(event_name, known_objects):
    """Interaction events may use verb-first naming (e.g. 'Share Button Clicked').
    Try to find a known object embedded anywhere in the name."""
    for obj in sorted(known_objects, key=len, reverse=True):
        if f" {obj} " in f" {event_name} ":
            return obj
    return None


def _extract_object(event_name):
    """Strict TP object extraction: event name minus final whitespace token."""
    name = event_name.strip()
    if " " not in name:
        return None
    return name.rsplit(" ", 1)[0]


def validate_object_declarations(added_objects, removed_objects, schema_objects, parse_errors=None):
    errors = list(parse_errors or [])
    warnings = []
    schema_names = set(schema_objects)
    added_names = set(added_objects)
    removed_names = set(removed_objects)

    for obj in sorted(added_names & removed_names):
        errors.append(
            f'Tracking plan declares "{obj}" in both ## New Standard Objects '
            f"and ## Removed Standard Objects. Remove the duplicate or pick one section."
        )

    for obj in sorted(removed_names):
        if obj not in schema_names and obj not in added_names:
            warnings.append(
                f'## Removed Standard Objects lists "{obj}", which is not in '
                f"the product event-schema.md Standard Objects nor declared in "
                f"## New Standard Objects. Removal has no effect."
            )

    for obj in sorted(added_names):
        if obj in schema_names:
            warnings.append(
                f'## New Standard Objects lists "{obj}", which already exists in '
                f"the product event-schema.md Standard Objects. Declaration is redundant."
            )

    return errors, warnings


def rule_01(catalog_events, schema_objects):
    """Catalog event object prefixes <-> Schema Standard Objects."""
    errors, warnings = [], []
    found = set()
    for name in catalog_events:
        obj = _object_prefix(name, schema_objects)
        if not obj and name.endswith("Button Clicked"):
            obj = _object_for_interaction_event(name, schema_objects)
        if obj:
            found.add(obj)
        elif not name.endswith("Button Clicked"):
            errors.append(_unknown_object_error(name))
    for obj in schema_objects:
        if obj not in found:
            warnings.append(
                f'Standard Object "{obj}" has no matching events in Event Catalog'
            )
    return errors, warnings


def _iter_result_pattern_events(flow):
    for role in RESULT_PATTERN_EVENT_KEYS:
        cell = flow.get(role, "")
        if cell == "--":
            continue
        if "implicit" in cell.lower():
            continue
        # Split on commas and "or" to get individual event candidates.
        parts = re.split(r",|\bor\b", cell)
        for part in parts:
            ev = part.strip()
            # Strip trailing parenthetical qualifiers like "(new)" / "(returning)".
            ev = re.sub(r"\s*\([^)]*\)\s*$", "", ev).strip()
            # Strip markdown emphasis.
            ev = ev.strip("*").strip()
            if not ev or ev == "--":
                continue
            yield role, ev


def rule_02(schema_result_pattern, schema_result_pattern_errors, catalog_events):
    """Schema Interaction / Started / Result events must exist in catalog.

    Schema cells may be placeholders (`*(implicit — ...)*`) or compound values
    (`A, B` / `A (new) or B (returning)`). Split on commas and " or ", strip
    parenthetical qualifiers, and skip implicit placeholders.
    """
    errors, warnings = list(schema_result_pattern_errors), []
    for flow in schema_result_pattern:
        for role, ev in _iter_result_pattern_events(flow):
            if ev not in catalog_events:
                errors.append(
                    f'Result pattern table: "{ev}" '
                    f'({RESULT_PATTERN_ROLE_LABELS[role]} for "{flow["flow"]}") '
                    f"not found in Event Catalog"
                )
    return errors, warnings


def rule_03(schema_person, catalog_events):
    """Schema person properties match catalog $set/$set_once operations."""
    errors, warnings = [], []
    catalog_ops = {}
    for _name, ev in catalog_events.items():
        for prop, method in ev["person_props"].items():
            catalog_ops.setdefault(prop, set()).add(method)
    for prop, info in schema_person.items():
        method = info["method"]
        if prop not in catalog_ops:
            warnings.append(
                f'Person property `{prop}` ({method}) defined in Schema but '
                f"no catalog event sets it via Property Updates"
            )
        elif method not in catalog_ops[prop]:
            errors.append(
                f'Person property `{prop}` is {method} in Schema but catalog '
                f"uses {catalog_ops[prop]}"
            )
    for prop, methods in catalog_ops.items():
        if prop not in schema_person:
            warnings.append(
                f'Catalog sets person property `{prop}` via {methods} but it '
                f"is not in Schema Person Properties table"
            )
    return errors, warnings


def _csv_set(value):
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    if not value:
        return set()
    return {v.strip() for v in str(value).split(",") if v.strip()}


def _area_rule_message(area_contains, name, prop, include_loop=False):
    label = area_contains.capitalize()
    subject = f"{label} loop event" if include_loop else f"{label} event"
    return f'{subject} "{name}" missing standard property `{prop}`'


def _append_by_severity(rule, errors, warnings, message):
    if rule.get("severity") == "warning":
        warnings.append(message)
    else:
        errors.append(message)


def rule_04(catalog_events, schema_evt_props, config=None):
    """Standard event properties from product config and schema.

    Area rules intentionally run in catalog mode as well as tracking-plan mode
    so product-wide required properties stay consistent after merge.
    """
    errors, warnings = [], []
    config = config or ProductConfig()
    schema_exceptions = {
        prop: _parse_exceptions(info.get("when", ""))
        for prop, info in schema_evt_props.items()
    }
    for name, ev in catalog_events.items():
        section = ev["section"].lower()
        props = ev["properties"]
        group = ev["group"].strip("`")

        for rule in config.persona_rules:
            prop = rule.get("property", "")
            if not prop:
                continue
            if rule.get("applies_if_in_schema") is True and prop not in schema_evt_props:
                continue
            section_contains = str(rule.get("section_contains", "")).lower()
            if (
                section_contains
                and section_contains in section
                and prop not in props
                and name not in schema_exceptions.get(prop, set())
            ):
                label = section_contains.capitalize()
                errors.append(
                    f'{label} event "{name}" missing standard property `{prop}`'
                )

        for rule in config.group_property_rules:
            if group != rule.get("group"):
                continue
            prop = rule.get("property", "")
            if not prop or prop in props:
                continue
            warning_types = _csv_set(rule.get("catalog_warning_types"))
            if ev["type"] in warning_types:
                warnings.append(
                    f'Job-grouped {ev["type"].lower()} event "{name}" missing '
                    f"`{prop}` (may be intentional for creation flow)"
                )
            else:
                errors.append(
                    f'Job-grouped event "{name}" missing standard property `{prop}`'
                )

        for rule in config.area_property_rules:
            prop = rule.get("property", "")
            area_contains = str(rule.get("area_contains", "")).lower()
            if area_contains and area_contains in ev["area"].lower() and prop not in props:
                _append_by_severity(
                    rule,
                    errors,
                    warnings,
                    _area_rule_message(area_contains, name, prop),
                )
    return errors, warnings


def rule_05(funnels, catalog_events):
    """Every event in funnel tables must exist in catalog."""
    errors, warnings = [], []
    for fname, stages in funnels.items():
        for s in stages:
            if s["event"] not in catalog_events:
                errors.append(
                    f'Funnel "{fname}": event "{s["event"]}" '
                    f'(stage: {s["stage"]}) not found in Event Catalog'
                )
    return errors, warnings


def rule_06(funnels, catalog_events):
    """Funnel 'Defined In' must match actual catalog section for each event."""
    errors, warnings = [], []
    for fname, stages in funnels.items():
        for s in stages:
            ev = s["event"]
            if ev not in catalog_events:
                continue
            actual = catalog_events[ev]["section"]
            di = s["defined_in"]
            if di.lower() not in actual.lower() and actual.lower() not in di.lower():
                errors.append(
                    f'Funnel "{fname}": "{ev}" says Defined In '
                    f'"{di}" but catalog section is "{actual}"'
                )
    return errors, warnings


def rule_07(dashboard_props, prop_dict):
    """Backtick-referenced properties in dashboards must exist in Property Dictionary."""
    errors, warnings = [], []
    known = set(prop_dict.keys())
    for dash, info in dashboard_props.items():
        for prop in info["properties"]:
            if prop not in known:
                errors.append(
                    f'{dash}: references `{prop}` not found in Property Dictionary'
                )
    return errors, warnings


def rule_08(dashboard_props, prop_dict):
    """Inline enum values in dashboard descriptions must match Property Dictionary."""
    errors, warnings = [], []
    for dash, info in dashboard_props.items():
        for prop, values in info.get("property_values", {}).items():
            if prop not in prop_dict:
                continue
            allowed = set()
            for entry in prop_dict[prop]:
                allowed.update(entry["allowed_values"])
            if not allowed:
                continue
            for val in values:
                if val not in allowed:
                    errors.append(
                        f'{dash}: `{prop}` value "{val}" not in '
                        f"allowed values {sorted(allowed)}"
                    )
    return errors, warnings


def _result_pattern_tuple(row):
    return (
        row.get("interaction_started", ""),
        row.get("success", ""),
        row.get("rejected", ""),
        row.get("error", "--"),
    )


def _format_result_tuple(row_tuple):
    cells = list(row_tuple)
    if cells[-1] == "--":
        cells = cells[:-1]
    return " / ".join(cells)


def rule_09(dash_ph, dash_ph_errors, schema_result_pattern):
    """Dashboard Platform Health table must match Schema result rows."""
    errors, warnings = list(dash_ph_errors), []

    schema_with_result = [
        r
        for r in schema_result_pattern
        if r.get("rejected") != "--" or r.get("error", "--") != "--"
    ]
    dash_set = {_result_pattern_tuple(r) for r in dash_ph}
    schema_set = {_result_pattern_tuple(r) for r in schema_with_result}
    for t in dash_set - schema_set:
        errors.append(
            f"Platform Health row ({_format_result_tuple(t)}) "
            f"not in Schema Interaction / Started / Result table"
        )
    for t in schema_set - dash_set:
        errors.append(
            f"Schema Interaction / Started / Result row ({_format_result_tuple(t)}) "
            f"not in Dashboard Platform Health table"
        )
    return errors, warnings


def rule_10(catalog_events, prop_dict):
    """Property Dictionary 'Used In' must match actual event property references."""
    errors, warnings = [], []
    actual_usage = {}
    for ev_name, ev in catalog_events.items():
        for prop in ev["properties"]:
            actual_usage.setdefault(prop, set()).add(ev_name)

    for prop, entries in prop_dict.items():
        skip = False
        declared = set()
        for entry in entries:
            for ui in entry["used_in"]:
                if _is_general_usage(ui):
                    skip = True
                    break
                declared.add(ui)
            if skip:
                break
        if skip:
            continue

        actual = actual_usage.get(prop, set())
        for ev in sorted(actual - declared):
            errors.append(
                f'`{prop}` is used in "{ev}" but not listed in '
                f'Property Dictionary "Used In"'
            )
        for ev in sorted(declared - actual):
            if ev in catalog_events:
                errors.append(
                    f'`{prop}` lists "{ev}" in "Used In" but '
                    f"that event does not reference this property"
                )
            else:
                errors.append(
                    f'`{prop}` lists "{ev}" in "Used In" but '
                    f"that event does not exist in the catalog"
                )
    return errors, warnings


def rule_11(catalog_events, prop_dict):
    """Inline enum values in event rows must match Property Dictionary allowed values."""
    errors, warnings = [], []
    for ev_name, ev in catalog_events.items():
        for prop, inline_vals in ev["inline_enums"].items():
            if prop not in prop_dict:
                continue
            allowed = set()
            for entry in prop_dict[prop]:
                allowed.update(entry["allowed_values"])
            if not allowed:
                continue
            for val in inline_vals:
                if val not in allowed:
                    errors.append(
                        f'"{ev_name}": inline value "{val}" for `{prop}` '
                        f"not in allowed values {sorted(allowed)}"
                    )
    return errors, warnings


def rule_12(catalog_events, prop_dict):
    """Event names must be Proper Case; property names must be snake_case."""
    errors, warnings = [], []
    for name in catalog_events:
        for word in name.split():
            if word[0] != word[0].upper():
                warnings.append(
                    f'Event "{name}": word "{word}" should be capitalized (Proper Case)'
                )
                break
    for prop in prop_dict:
        if not re.match(r"^[a-z][a-z0-9_]*$", prop) and not prop.startswith("$"):
            warnings.append(f'Property "{prop}" is not snake_case')
    return errors, warnings


def rule_13(catalog_events, prop_dict):
    """Every property in event rows must have a Property Dictionary entry."""
    errors, warnings = [], []
    known = set(prop_dict.keys())
    for ev_name, ev in catalog_events.items():
        for prop in ev["properties"]:
            if prop not in known:
                errors.append(
                    f'"{ev_name}": property `{prop}` has no entry '
                    f"in Property Dictionary"
                )
    return errors, warnings


def rule_14(duplicate_events, prop_dict):
    """No duplicate event names; no duplicate property dictionary entries."""
    errors, warnings = [], []
    for name, count in duplicate_events.items():
        errors.append(f'Event name "{name}" appears {count} times in the catalog')
    for prop, entries in prop_dict.items():
        seen = set()
        for entry in entries:
            key = (prop, entry["qualifier"])
            if key in seen:
                label = f"`{prop}` ({entry['qualifier']})" if entry["qualifier"] else f"`{prop}`"
                errors.append(
                    f"Property Dictionary has duplicate entry for {label}"
                )
            seen.add(key)
    return errors, warnings


def _action_errors(event_names, known_objects):
    """Shared Rule 15 / TP10 logic — syntactic action validity only.
    Splits object from action, requires a non-empty action whose final word is
    past tense (ends 'ed') or an allowed irregular. No semantics, no allow-list.
    """
    errors = []
    for name in event_names:
        if name.endswith("Button Clicked"):        # interaction events may be verb-first
            continue
        last_word = name.split()[-1]
        if last_word in RESULT_VARIANTS:            # Rule 16 owns the better message
            continue
        obj, action = _split_object_action(name, known_objects)
        if obj is None:                             # Rule 1 / TP7 owns this error
            continue
        if not action:
            errors.append(f'Event "{name}" is only an object — missing an action')
            continue
        last = action.split()[-1]
        if not (last.endswith("ed") or last in IRREGULAR_PAST):
            errors.append(
                f'Event "{name}": action "{action}" must end in a past-tense verb '
                f"(Created, Started, Succeeded, Rejected, Errored)"
            )
    return errors


def _result_terminal_errors(typed_events):
    """Shared Rule 16 / TP11 logic — type-driven terminal form.
    typed_events: iterable of (event_name, event_type). Flags non-canonical
    trailing words type-independently, then enforces the type's required
    terminal. One message per event."""
    errors = []
    for name, etype in typed_events:
        last = name.split()[-1]
        if last in RESULT_VARIANTS:                 # type-independent; one message per event
            errors.append(
                f'Result event "{name}" must end with "{RESULT_VARIANTS[last]}", '
                f'not "{last}" (result terminals are Succeeded/Rejected/Errored)'
            )
            continue
        allowed = TYPE_TERMINALS.get(etype)
        if allowed and last not in allowed:
            errors.append(
                f'Event "{name}" has Type {etype} but does not end in '
                + " / ".join(allowed)
            )
    return errors


def _event_type_errors(typed_events, allowed_types):
    """Shared Rule 17 / TP12 row-level logic. None type => missing column,
    handled at the table level, not here."""
    errors = []
    for name, etype in typed_events:
        if etype is None:
            continue
        if etype not in allowed_types:
            errors.append(
                f'Event "{name}" has Type "{etype}" — must be one of: '
                + ", ".join(sorted(allowed_types))
            )
    return errors


def _missing_enum_error(schema_event_types):
    """Shared/product Event Types table is the source of truth."""
    if schema_event_types:
        return []
    return [
        "Event Types table not found in docs/shared/naming-and-event-types.md or "
        "the product event-schema.md — it is the source of truth for the "
        "event type enum"
    ]


def rule_15(catalog_events, schema_objects):
    """Action validity: every catalog event needs a syntactically valid action."""
    return _action_errors(catalog_events, schema_objects), []


def rule_16(catalog_events):
    """Result terminal form: type-driven canonical terminals."""
    return _result_terminal_errors(
        (n, ev["type"]) for n, ev in catalog_events.items()
    ), []


def rule_17(catalog_events, schema_event_types):
    """Event type validity: every catalog row's Type is a member of the enum."""
    errors = _missing_enum_error(schema_event_types)
    if schema_event_types:
        errors += _event_type_errors(
            ((n, ev["type"]) for n, ev in catalog_events.items()), schema_event_types
        )
    return errors, []


# ── Tracking Plan Validation Rules ────────────────────────────────────────────


def tp_rule_00(declaration_errors, declaration_warnings):
    """Validate New/Removed Standard Object declarations."""
    return list(declaration_errors), list(declaration_warnings)


def tp_rule_01(tp_events):
    """Event names must be Proper Case and Object-Action (2+ words)."""
    errors, warnings = [], []
    for name in tp_events:
        words = name.split()
        if len(words) < 2:
            errors.append(
                f'Event "{name}" must follow Object-Action format (at least 2 words)'
            )
            continue
        for word in words:
            if word[0] != word[0].upper():
                errors.append(
                    f'Event "{name}": word "{word}" should be capitalized (Proper Case)'
                )
                break
    return errors, warnings


def tp_rule_02(tp_events, tp_prop_dict):
    """Property names must be snake_case."""
    errors, warnings = [], []
    checked = set()
    for ev in tp_events.values():
        for prop in ev["properties"]:
            if prop in checked or prop.startswith("$"):
                continue
            checked.add(prop)
            if not re.match(r"^[a-z][a-z0-9_]*$", prop):
                errors.append(f'Property `{prop}` is not snake_case')
    for prop in tp_prop_dict:
        if prop in checked or prop.startswith("$"):
            continue
        checked.add(prop)
        if not re.match(r"^[a-z][a-z0-9_]*$", prop):
            errors.append(f'Property `{prop}` in Property Details is not snake_case')
    return errors, warnings


def tp_rule_03(tp_events, catalog_events):
    """No new event should duplicate an existing catalog event."""
    errors, warnings = [], []
    for name in tp_events:
        if name in catalog_events:
            errors.append(
                f'Event "{name}" already exists in the catalog '
                f'(section: {catalog_events[name]["section"]})'
            )
    return errors, warnings


def tp_rule_04(tp_events, prop_dict, tp_prop_dict):
    """Every property in new events must exist in catalog Property Dictionary or tracking plan Property Details."""
    errors, warnings = [], []
    catalog_known = set(prop_dict.keys())
    tp_known = set(tp_prop_dict.keys())
    for ev_name, ev in tp_events.items():
        for prop in ev["properties"]:
            if prop.startswith("$"):
                continue
            if prop not in catalog_known and prop not in tp_known:
                errors.append(
                    f'"{ev_name}": property `{prop}` not found in catalog '
                    f"Property Dictionary or tracking plan Property Details"
                )
    return errors, warnings


def tp_rule_05(tp_events, schema_evt_props, config=None):
    """Standard property compliance from product config."""
    errors, warnings = [], []
    config = config or ProductConfig()
    for name, ev in tp_events.items():
        area = ev["area"].lower()
        props = ev["properties"]
        group = ev["group"].strip("`")

        for rule in config.group_property_rules:
            if group != rule.get("group"):
                continue
            prop = rule.get("property", "")
            if not prop or prop in props:
                continue
            if rule.get("tracking_plan_severity") == "warning":
                warnings.append(
                    f'Job-grouped event "{name}" missing `{prop}` '
                    f"(may be intentional for creation flow)"
                )
            else:
                errors.append(
                    f'Job-grouped event "{name}" missing standard property `{prop}`'
                )

        for rule in config.area_property_rules:
            prop = rule.get("property", "")
            area_contains = str(rule.get("area_contains", "")).lower()
            if area_contains and area_contains in area and prop not in props:
                _append_by_severity(
                    rule,
                    errors,
                    warnings,
                    _area_rule_message(area_contains, name, prop, include_loop=True),
                )

    return errors, warnings


def tp_rule_06(tp_result_pattern, tp_result_pattern_errors, tp_events, catalog_events):
    """All result-pattern events must exist in catalog or tracking plan."""
    errors, warnings = list(tp_result_pattern_errors), []
    all_known = set(catalog_events.keys()) | set(tp_events.keys())
    for flow in tp_result_pattern:
        for role, ev in _iter_result_pattern_events(flow):
            if ev not in all_known:
                errors.append(
                    f'Result pattern: "{ev}" '
                    f'({RESULT_PATTERN_ROLE_LABELS[role]} for "{flow["flow"]}") '
                    f"not found in catalog or tracking plan"
                )
    return errors, warnings


def tp_rule_07(tp_events, schema_objects, added_objects=None, removed_objects=None):
    """Event object must match effective Standard Objects using strict TP parsing."""
    errors, warnings = [], []
    added = set(added_objects or {})
    removed = set(removed_objects or {})
    known = set(schema_objects) | added
    for name in tp_events:
        obj = _extract_object(name)
        if not obj:
            errors.append(f'Event "{name}": Event name must follow Object-Action format')
        elif obj in removed:
            errors.append(
                f'Event "{name}": object "{obj}" is listed in '
                f"## Removed Standard Objects. Rename the event, or remove "
                f'"{obj}" from the removal list.'
            )
        elif obj not in known:
            errors.append(
                f'Event "{name}": object "{obj}" is not in '
                f"the product event-schema.md Standard Objects or this plan's "
                f'## New Standard Objects section. Either rename the event to use '
                f'a registered object, or declare "{obj}" in ## New Standard Objects.'
            )
    return errors, warnings


def tp_rule_08(tp_funnels, tp_events, catalog_events):
    """Funnel step events must exist in catalog or tracking plan."""
    errors, warnings = [], []
    all_known = set(catalog_events.keys()) | set(tp_events.keys())
    for fname, steps in tp_funnels.items():
        for step in steps:
            if step not in all_known:
                errors.append(
                    f'Funnel "{fname}": step "{step}" not found in '
                    f"catalog or tracking plan"
                )
    return errors, warnings


def tp_rule_09(tp_events, prop_dict):
    """Inline enum values in tracking plan events must match catalog Property Dictionary."""
    errors, warnings = [], []
    for ev_name, ev in tp_events.items():
        for prop, inline_vals in ev["inline_enums"].items():
            if prop not in prop_dict:
                continue
            allowed = set()
            for entry in prop_dict[prop]:
                allowed.update(entry["allowed_values"])
            if not allowed:
                continue
            for val in inline_vals:
                if val not in allowed:
                    errors.append(
                        f'"{ev_name}": inline value "{val}" for `{prop}` '
                        f"not in catalog allowed values {sorted(allowed)}"
                    )
    return errors, warnings


def tp_rule_10(tp_events, schema_objects):
    """Action validity: every new event needs a syntactically valid action."""
    return _action_errors(tp_events, schema_objects), []


def tp_rule_11(tp_events):
    """Result terminal form: type-driven canonical terminals.
    With no Type column, type is None — the variant-terminal name check still
    runs, but no type-driven terminal is enforced."""
    return _result_terminal_errors(
        (n, ev.get("type")) for n, ev in tp_events.items()
    ), []


def tp_rule_12(tp_events, schema_event_types):
    """Event type validity: New Events table must carry a valid Type per row."""
    errors = _missing_enum_error(schema_event_types)
    if tp_events and all(ev.get("type") is None for ev in tp_events.values()):
        errors.append(
            'New Events table has no "Type" column — add one '
            "(see templates/tracking-plan.md)"
        )
    else:
        if schema_event_types:
            errors += _event_type_errors(
                ((n, ev.get("type") or "--") for n, ev in tp_events.items()),
                schema_event_types,
            )
    return errors, []


# ── Logging ──────────────────────────────────────────────────────────────────

def log_header(product):
    label = PRODUCT_LABELS.get(product, product.replace("-", " ").title())
    return (
        f"# {label} Analytics Docs - Validation Log\n\n"
        "Auto-generated by `scripts/validate-analytics-docs.py`.  \n"
        f"Each run validates consistency across the 3 {label} analytics documents.\n\n"
        "## Known Warnings\n\n"
        "Reviewed and suppressed. Remove a line to re-surface it.\n"
    )


def load_known_warnings(log_path):
    """Parse known (suppressed) warnings from the log file."""
    known = set()
    if not log_path.exists():
        return known
    text = log_path.read_text()
    kw_match = re.search(r"^## Known Warnings\s*\n", text, re.MULTILINE)
    if not kw_match:
        return known
    kw_text = text[kw_match.end() :]
    end = re.search(r"^(?:## |---)", kw_text, re.MULTILINE)
    if end:
        kw_text = kw_text[: end.start()]
    for m in re.finditer(r"^- \[(\w+)\] (.+)$", kw_text, re.MULTILINE):
        rid = m.group(1)
        rid = int(rid) if rid.isdigit() else rid
        known.add((rid, m.group(2).strip()))
    return known


def write_log(paths, all_errors, all_warnings, suppressed_count=0, mode_label=None, rule_names=None):
    if rule_names is None:
        rule_names = RULE_NAMES
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    error_count = sum(len(e) for e in all_errors.values())
    warn_count = sum(len(w) for w in all_warnings.values())

    heading = f"## Run: {now}"
    if mode_label:
        heading += f" — {mode_label}"
    lines = ["", "---", "", heading, ""]

    if error_count == 0 and warn_count == 0:
        lines += ["**Result: All clear**", "", f"All {len(rule_names)} validation rules passed."]
        if suppressed_count:
            lines.append(
                f"\n*({suppressed_count} known warning"
                f'{"s" if suppressed_count != 1 else ""} suppressed)*'
            )
    else:
        parts = []
        if error_count:
            parts.append(f'{error_count} error{"s" if error_count != 1 else ""}')
        if warn_count:
            parts.append(f'{warn_count} warning{"s" if warn_count != 1 else ""}')
        lines += [f"**Result: {', '.join(parts)}**", ""]

        if error_count:
            lines.append("### Errors")
            lines.append("")
            for rid in sorted(all_errors):
                for e in all_errors[rid]:
                    lines.append(f"- **[Rule {rid}]** {e}")
            lines.append("")

        if warn_count:
            lines.append("### Warnings")
            lines.append("")
            for rid in sorted(all_warnings):
                for w in all_warnings[rid]:
                    lines.append(f"- **[Rule {rid}]** {w}")
            lines.append("")

        if suppressed_count:
            lines.append(
                f"*({suppressed_count} known warning"
                f'{"s" if suppressed_count != 1 else ""} suppressed)*'
            )
            lines.append("")

    new_entry = "\n".join(lines)

    paths.log_path.parent.mkdir(parents=True, exist_ok=True)
    if paths.log_path.exists():
        existing = paths.log_path.read_text()
    else:
        existing = log_header(paths.product)

    parts = re.split(r"(?=\n---\n\n## Run:)", existing)
    header = parts[0]
    runs = parts[1:] if len(parts) > 1 else []
    runs.append(new_entry)
    if len(runs) > MAX_LOG_RUNS:
        runs = runs[-MAX_LOG_RUNS:]
    paths.log_path.write_text(header + "".join(runs) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def _group_findings(findings, rule_names):
    grouped = []
    for rid in sorted(findings, key=str):
        items = list(findings[rid])
        grouped.append(
            {
                "rule_id": rid,
                "rule_name": rule_names[rid],
                "count": len(items),
                "items": items,
            }
        )
    return grouped


def _summary_result(paths, all_errors, all_warnings, suppressed, rule_names):
    ec = sum(len(e) for e in all_errors.values())
    wc = sum(len(w) for w in all_warnings.values())
    return {
        "product": paths.product,
        "exit_code": 1 if ec else 0,
        "rule_count": len(rule_names),
        "error_count": ec,
        "warning_count": wc,
        "suppressed_warning_count": suppressed,
        "errors": _group_findings(all_errors, rule_names),
        "warnings": _group_findings(all_warnings, rule_names),
    }


def config_error_summary(product, message, rule_count=None):
    if rule_count is None:
        rule_count = len(RULE_NAMES)
    return {
        "product": product,
        "exit_code": 2,
        "rule_count": rule_count,
        "error_count": 1,
        "warning_count": 0,
        "suppressed_warning_count": 0,
        "errors": [
            {
                "rule_id": "config",
                "rule_name": "Configuration",
                "count": 1,
                "items": [message],
            }
        ],
        "warnings": [],
    }


def compute_result(paths, rules, known, rule_names):
    """Run rules, suppress known warnings, and return structured findings."""
    all_errors, all_warnings = {}, {}
    for rid, fn, args in rules:
        errs, warns = fn(*args)
        if errs:
            all_errors[rid] = errs
        if warns:
            all_warnings[rid] = warns

    suppressed = 0
    for rid in list(all_warnings):
        before = len(all_warnings[rid])
        all_warnings[rid] = [
            w for w in all_warnings[rid] if (rid, w) not in known
        ]
        suppressed += before - len(all_warnings[rid])
        if not all_warnings[rid]:
            del all_warnings[rid]

    return _summary_result(paths, all_errors, all_warnings, suppressed, rule_names), all_errors, all_warnings


def emit_text_result(paths, result, stream):
    if result["error_count"] == 0 and result["warning_count"] == 0:
        msg = f"All clear — {result['rule_count']} validation rules passed."
        if result["suppressed_warning_count"]:
            msg += f" ({result['suppressed_warning_count']} known warnings suppressed)"
        print(msg, file=stream)
        print(f"Log: {paths.log_path.relative_to(REPO_ROOT)}", file=stream)
        return

    if result["error_count"]:
        print(f"\n--- ERRORS ({result['error_count']}) ---", file=stream)
        for group in result["errors"]:
            for e in group["items"]:
                print(
                    f"  [Rule {group['rule_id']}: {group['rule_name']}] {e}",
                    file=stream,
                )

    if result["warning_count"]:
        print(f"\n--- WARNINGS ({result['warning_count']}) ---", file=stream)
        for group in result["warnings"]:
            for w in group["items"]:
                print(
                    f"  [Rule {group['rule_id']}: {group['rule_name']}] {w}",
                    file=stream,
                )

    if result["suppressed_warning_count"]:
        print(f"\n({result['suppressed_warning_count']} known warnings suppressed)", file=stream)

    print(f"\nLog updated: {paths.log_path.relative_to(REPO_ROOT)}", file=stream)


def emit_json_result(result):
    json.dump(result, sys.stdout, sort_keys=True)
    print()


def _run_rules(paths, rules, known, rule_names, mode_label=None, json_summary=False):
    """Run validation rules, write logs, emit output, and return the intended exit code."""
    result, all_errors, all_warnings = compute_result(paths, rules, known, rule_names)
    write_log(paths, all_errors, all_warnings, result["suppressed_warning_count"], mode_label=mode_label, rule_names=rule_names)

    stream = sys.stderr if json_summary else sys.stdout
    emit_text_result(paths, result, stream)
    if json_summary:
        emit_json_result(result)
    return result["exit_code"]


def _resolve_tracking_plan_path(paths, arg):
    candidate = Path(arg)
    if candidate.exists():
        return candidate
    for alt in (
        paths.tracking_plans_dir / f"{arg}.md",
        paths.tracking_plans_dir / arg,
        TRACKING_PLANS_DIR / f"{arg}.md",
        TRACKING_PLANS_DIR / arg,
        REPO_ROOT / arg,
    ):
        if alt.exists():
            return alt
    return candidate


def _catalog_object_for_event(event_name, schema_objects):
    obj = _object_prefix(event_name, schema_objects)
    if not obj and event_name.endswith("Button Clicked"):
        obj = _object_for_interaction_event(event_name, schema_objects)
    return obj


def removal_safety_blockers(removed_objects, catalog_events, schema_objects):
    blockers = []
    removed = set(removed_objects)
    if not removed:
        return blockers
    for event_name in catalog_events:
        obj = _catalog_object_for_event(event_name, schema_objects)
        if obj in removed:
            blockers.append((obj, event_name))
    return sorted(blockers)


def check_removal_safety(paths, tp_path):
    if not tp_path.exists():
        print(f"ERROR: Tracking plan not found: {tp_path}", file=sys.stderr)
        return 2
    if not tp_path.is_file() or tp_path.suffix.lower() != ".md":
        print(f"ERROR: Tracking plan must be a markdown file: {tp_path}", file=sys.stderr)
        return 2

    for p in (paths.catalog_path, paths.schema_path):
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            return 2

    catalog_events, _, _ = parse_catalog(paths.catalog_path)
    schema_objects, _, _, _, _, _ = parse_schema(paths.schema_path, paths.shared_event_types_path)
    tp_data = parse_tracking_plan(tp_path)
    declaration_errors, declaration_warnings = validate_object_declarations(
        tp_data.added_objects,
        tp_data.removed_objects,
        schema_objects,
        tp_data.declaration_errors,
    )
    if declaration_errors:
        for error in declaration_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    for warning in declaration_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    blockers = removal_safety_blockers(
        tp_data.removed_objects, catalog_events, schema_objects
    )
    for obj, event_name in blockers:
        print(f"{obj} blocks: {event_name}")
    return 1 if blockers else 0


def emit_config_error(paths, message, json_summary=False):
    print(f"ERROR: {message}", file=sys.stderr)
    result = config_error_summary(paths.product, message)
    if json_summary:
        emit_json_result(result)
    return result["exit_code"]


def validate_catalog(paths, json_summary=False):
    """Validate consistency across the 3 source-of-truth docs."""
    for p in (paths.catalog_path, paths.schema_path, paths.dashboard_path):
        if not p.exists():
            return emit_config_error(paths, f"File not found: {p}", json_summary)

    catalog_events, prop_dict, dup_events = parse_catalog(paths.catalog_path)
    (
        schema_objects,
        schema_person,
        schema_evt_props,
        schema_result_pattern,
        schema_result_pattern_errors,
        schema_event_types,
    ) = parse_schema(paths.schema_path, paths.shared_event_types_path)
    funnels, dash_ph, dash_ph_errors, dash_props = parse_dashboards(paths.dashboard_path)

    if not catalog_events and not paths.config.allow_empty_catalog:
        return emit_config_error(paths, "No events parsed from catalog", json_summary)

    known = load_known_warnings(paths.log_path)

    rules = [
        (1, rule_01, (catalog_events, schema_objects)),
        (2, rule_02, (schema_result_pattern, schema_result_pattern_errors, catalog_events)),
        (3, rule_03, (schema_person, catalog_events)),
        (4, rule_04, (catalog_events, schema_evt_props, paths.config)),
        (5, rule_05, (funnels, catalog_events)),
        (6, rule_06, (funnels, catalog_events)),
        (7, rule_07, (dash_props, prop_dict)),
        (8, rule_08, (dash_props, prop_dict)),
        (9, rule_09, (dash_ph, dash_ph_errors, schema_result_pattern)),
        (10, rule_10, (catalog_events, prop_dict)),
        (11, rule_11, (catalog_events, prop_dict)),
        (12, rule_12, (catalog_events, prop_dict)),
        (13, rule_13, (catalog_events, prop_dict)),
        (14, rule_14, (dup_events, prop_dict)),
        (15, rule_15, (catalog_events, schema_objects)),
        (16, rule_16, (catalog_events,)),
        (17, rule_17, (catalog_events, schema_event_types)),
    ]

    return _run_rules(paths, rules, known, RULE_NAMES, json_summary=json_summary)


def validate_tracking_plan(paths, tp_path):
    """Validate a tracking plan against catalog and schema context."""
    if not tp_path.exists():
        print(f"ERROR: Tracking plan not found: {tp_path}", file=sys.stderr)
        return 2

    for p in (paths.catalog_path, paths.schema_path):
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            return 2

    catalog_events, prop_dict, _ = parse_catalog(paths.catalog_path)
    schema_objects, _, schema_evt_props, _, _, schema_event_types = parse_schema(
        paths.schema_path, paths.shared_event_types_path
    )
    tp_data = parse_tracking_plan(tp_path)

    if not tp_data.events:
        print("ERROR: No events parsed from tracking plan", file=sys.stderr)
        return 2

    known = load_known_warnings(paths.log_path)
    plan_name = tp_path.stem
    declaration_errors, declaration_warnings = validate_object_declarations(
        tp_data.added_objects,
        tp_data.removed_objects,
        schema_objects,
        tp_data.declaration_errors,
    )

    rules = [
        ("TP0", tp_rule_00, (declaration_errors, declaration_warnings)),
        ("TP1", tp_rule_01, (tp_data.events,)),
        ("TP2", tp_rule_02, (tp_data.events, tp_data.prop_dict)),
        ("TP3", tp_rule_03, (tp_data.events, catalog_events)),
        ("TP4", tp_rule_04, (tp_data.events, prop_dict, tp_data.prop_dict)),
        ("TP5", tp_rule_05, (tp_data.events, schema_evt_props, paths.config)),
        (
            "TP6",
            tp_rule_06,
            (
                tp_data.result_pattern,
                tp_data.result_pattern_errors,
                tp_data.events,
                catalog_events,
            ),
        ),
        (
            "TP7",
            tp_rule_07,
            (
                tp_data.events,
                schema_objects,
                tp_data.added_objects,
                tp_data.removed_objects,
            ),
        ),
        ("TP8", tp_rule_08, (tp_data.funnels, tp_data.events, catalog_events)),
        ("TP9", tp_rule_09, (tp_data.events, prop_dict)),
        ("TP10", tp_rule_10, (tp_data.events, schema_objects)),
        ("TP11", tp_rule_11, (tp_data.events,)),
        ("TP12", tp_rule_12, (tp_data.events, schema_event_types)),
    ]

    return _run_rules(paths, rules, known, TP_RULE_NAMES, mode_label=f"Tracking Plan: {plan_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate product-scoped analytics docs and tracking plans."
    )
    parser.add_argument(
        "--product",
        required=True,
        help="Product namespace under docs/ (for example: helix, recruit).",
    )
    parser.add_argument(
        "--check-removal-safety",
        metavar="TP",
        help="Check whether removed Standard Objects are still referenced by catalog events.",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Emit a catalog validation summary as JSON on stdout; human output goes to stderr.",
    )
    parser.add_argument(
        "tracking_plan",
        nargs="?",
        help="Tracking plan path, basename, or file under tracking-plans/<product>/.",
    )
    args = parser.parse_args()

    if args.check_removal_safety and args.tracking_plan:
        parser.error("tracking_plan positional cannot be combined with --check-removal-safety")
    if args.json_summary and (args.check_removal_safety or args.tracking_plan):
        parser.error("--json-summary is only supported for catalog validation")

    try:
        paths = product_paths(args.product)
    except ProductPathError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        if args.json_summary:
            message = str(exc)
            print(f"ERROR: {message}", file=sys.stderr)
            emit_json_result(config_error_summary(args.product, message))
            sys.exit(2)
        parser.error(str(exc))

    stream = sys.stderr if args.json_summary else sys.stdout
    print(f"Validating product: {paths.product}", file=stream)
    if args.check_removal_safety:
        tp_path = _resolve_tracking_plan_path(paths, args.check_removal_safety)
        sys.exit(check_removal_safety(paths, tp_path))
    if args.tracking_plan:
        sys.exit(validate_tracking_plan(paths, _resolve_tracking_plan_path(paths, args.tracking_plan)))
    else:
        sys.exit(validate_catalog(paths, json_summary=args.json_summary))


if __name__ == "__main__":
    main()
