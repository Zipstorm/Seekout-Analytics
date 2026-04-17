#!/usr/bin/env python3
"""
Validates consistency across the 3 Helix analytics markdown documents:
  - event-catalog.md   (Event Catalog)
  - event-schema.md    (Schema)
  - dashboards.md      (Dashboards)

Run:  python scripts/validate-analytics-docs.py
Exit: 0 = all clear, 1 = errors found, 2 = parse failure
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
CATALOG_PATH = DOCS_DIR / "event-catalog.md"
SCHEMA_PATH = DOCS_DIR / "event-schema.md"
DASHBOARD_PATH = DOCS_DIR / "dashboards.md"
LOG_PATH = REPO_ROOT / "logs" / "conflicts-log.md"
MAX_LOG_RUNS = 20

RULE_NAMES = {
    1: "Object coverage",
    2: "Intent-Outcome alignment",
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
}

TP_RULE_NAMES = {
    "TP1": "Event naming conventions",
    "TP2": "Property naming conventions",
    "TP3": "No duplicate events vs catalog",
    "TP4": "Property coverage (catalog + tracking plan)",
    "TP5": "Standard property compliance",
    "TP6": "Intent vs Outcome completeness",
    "TP7": "Standard Object usage",
    "TP8": "Funnel event validity",
    "TP9": "Inline enum consistency",
}

# ── Markdown Parsing ─────────────────────────────────────────────────────────


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :]
    return text


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

EVENT_SECTION_KEYS = [
    "login & onboarding",
    "auth lifecycle",
    "auth dev",
    "email verification",
    "phone collection",
    "account & persona",
    "anonymous user",
    "prospect persona",
    "hiring persona",
    "chat websocket",
]


def parse_catalog(path):
    """
    Returns:
      events  – dict[name, {...}]
      prop_dict – dict[base_prop, list[{qualifier, type, allowed_values, used_in}]]
      duplicate_events – dict[name, count] for names appearing more than once
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)
    events = {}
    duplicate_events = {}
    for heading, _header, rows in tables:
        if not any(k in heading.lower() for k in EVENT_SECTION_KEYS):
            continue
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


def parse_schema(path):
    """
    Returns:
      std_objects    – dict[obj, {entity, example_events}]
      person_props   – dict[prop, {type, method}]
      std_event_props – dict[prop, {when}]
      intent_outcome – list[{flow, intent, success, failure}]
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

    intent_outcome = []
    for heading, _h, rows in tables:
        h = heading.lower()
        if "intent" in h and ("outcome" in h or "pattern" in h):
            for r in rows:
                if len(r) >= 4:
                    intent_outcome.append(
                        dict(
                            flow=r[0].strip(),
                            intent=r[1].strip(),
                            success=r[2].strip(),
                            failure=r[3].strip(),
                        )
                    )
            break

    return std_objects, person_props, std_event_props, intent_outcome


def parse_dashboards(path):
    """
    Returns:
      funnels        – dict[name, list[{stage, event, defined_in}]]
      platform_health – list[{flow, intent, success, failure}]
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

    platform_health = []
    _, ph_rows = _find_table(tables, "Platform Health")
    if ph_rows:
        for r in ph_rows:
            if len(r) >= 4:
                platform_health.append(
                    dict(
                        flow=r[0].strip(),
                        intent=r[1].strip(),
                        success=r[2].strip(),
                        failure=r[3].strip(),
                    )
                )

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

    return funnels, platform_health, dashboard_props


def parse_tracking_plan(path):
    """
    Parse a tracking plan markdown file.

    Returns:
      tp_events        – dict[name, {area, properties, inline_enums, group, person_props, group_props}]
      tp_intent_outcome – list[{flow, intent, success, failure}]
      tp_funnels       – dict[name, list[event_name]]
      tp_prop_dict     – dict[prop_name, {type, values}]
    """
    text = strip_frontmatter(path.read_text())
    tables = parse_tables(text)

    # ── New Events table ──
    tp_events = {}
    _, ev_rows = _find_table(tables, "New Events")
    if ev_rows:
        for row in ev_rows:
            if len(row) < 6:
                continue
            name = row[0].strip()
            if not name or name.startswith("["):
                continue
            area = row[1].strip()
            props, inline_enums = extract_props(row[3])
            group = row[4].strip()
            person, grp = parse_property_updates(row[5])
            tp_events[name] = dict(
                area=area,
                properties=props,
                inline_enums=inline_enums,
                group=group,
                person_props=person,
                group_props=grp,
            )

    # ── Intent vs Outcome table ──
    tp_intent_outcome = []
    _, io_rows = _find_table(tables, "Intent vs Outcome")
    if io_rows:
        for row in io_rows:
            if len(row) < 4:
                continue
            flow = row[0].strip()
            if not flow or flow.startswith("["):
                continue
            tp_intent_outcome.append(
                dict(
                    flow=flow,
                    intent=row[1].strip(),
                    success=row[2].strip(),
                    failure=row[3].strip(),
                )
            )

    # ── Funnels table ──
    tp_funnels = {}
    _, fn_rows = _find_table(tables, "Funnels")
    if fn_rows:
        for row in fn_rows:
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

    return tp_events, tp_intent_outcome, tp_funnels, tp_prop_dict


# ── Validation Rules ─────────────────────────────────────────────────────────


def _object_prefix(event_name, known_objects):
    """Match the longest known object that is a prefix of the event name."""
    for obj in sorted(known_objects, key=len, reverse=True):
        if event_name.startswith(obj + " "):
            return obj
    return None


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


def _object_for_intent_event(event_name, known_objects):
    """Intent events use verb-first naming (e.g. 'Share Button Clicked').
    Try to find a known object embedded anywhere in the name."""
    for obj in sorted(known_objects, key=len, reverse=True):
        if f" {obj} " in f" {event_name} ":
            return obj
    return None


def rule_01(catalog_events, schema_objects):
    """Catalog event object prefixes <-> Schema Standard Objects."""
    errors, warnings = [], []
    found = set()
    for name in catalog_events:
        obj = _object_prefix(name, schema_objects)
        if not obj and name.endswith("Button Clicked"):
            obj = _object_for_intent_event(name, schema_objects)
        if obj:
            found.add(obj)
        elif not name.endswith("Button Clicked"):
            errors.append(
                f'Event "{name}" uses an object prefix not in Standard Objects table'
            )
    for obj in schema_objects:
        if obj not in found:
            warnings.append(
                f'Standard Object "{obj}" has no matching events in Event Catalog'
            )
    return errors, warnings


def rule_02(schema_io, catalog_events):
    """Schema Intent vs Outcome events must exist in catalog.

    Schema cells may be placeholders (`*(implicit — ...)*`) or compound values
    (`A, B` / `A (new) or B (returning)`). Split on commas and " or ", strip
    parenthetical qualifiers, and skip implicit placeholders.
    """
    errors, warnings = [], []
    for flow in schema_io:
        for role in ("intent", "success", "failure"):
            cell = flow[role]
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
                if ev not in catalog_events:
                    errors.append(
                        f'Intent-Outcome table: "{ev}" ({role} for '
                        f'"{flow["flow"]}") not found in Event Catalog'
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


def rule_04(catalog_events, schema_evt_props):
    """Standard event properties (per Schema): enforce only what Schema still defines.

    acting_as was removed from Schema in favor of the `current_persona` person
    property ($set), so we skip the hiring acting_as check unless Schema
    explicitly reinstates it.
    """
    errors, warnings = [], []
    acting_as_in_schema = "acting_as" in schema_evt_props
    acting_as_when = schema_evt_props.get("acting_as", {}).get("when", "")
    acting_as_exceptions = _parse_exceptions(acting_as_when)
    for name, ev in catalog_events.items():
        section = ev["section"].lower()
        props = ev["properties"]
        if (
            acting_as_in_schema
            and "hiring" in section
            and "acting_as" not in props
            and name not in acting_as_exceptions
        ):
            errors.append(
                f'Hiring event "{name}" missing standard property `acting_as`'
            )
        group = ev["group"].strip("`")
        if group == "job" and "job_id" not in props:
            if ev["type"] in ("Intent", "Failure"):
                warnings.append(
                    f'Job-grouped {ev["type"].lower()} event "{name}" missing '
                    f"`job_id` (may be intentional for creation flow)"
                )
            else:
                errors.append(
                    f'Job-grouped event "{name}" missing standard property `job_id`'
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


def rule_09(dash_ph, schema_io):
    """Dashboard Platform Health table must match Schema Intent vs Outcome (for flows with failures)."""
    errors, warnings = [], []

    def _event_tuple(row):
        return (row["intent"], row["success"], row["failure"])

    schema_with_failure = [r for r in schema_io if r["failure"] != "--"]
    dash_set = {_event_tuple(r) for r in dash_ph}
    schema_set = {_event_tuple(r) for r in schema_with_failure}
    for t in dash_set - schema_set:
        errors.append(
            f"Platform Health row ({t[0]} / {t[1]} / {t[2]}) "
            f"not in Schema Intent-Outcome table"
        )
    for t in schema_set - dash_set:
        errors.append(
            f"Schema Intent-Outcome row ({t[0]} / {t[1]} / {t[2]}) "
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


# ── Tracking Plan Validation Rules ────────────────────────────────────────────


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


def tp_rule_05(tp_events, schema_evt_props):
    """Standard property compliance: acting_as, job_id, surface, referrer_user_id."""
    errors, warnings = [], []
    acting_as_when = schema_evt_props.get("acting_as", {}).get("when", "")
    acting_as_exceptions = _parse_exceptions(acting_as_when)
    for name, ev in tp_events.items():
        area = ev["area"].lower()
        props = ev["properties"]
        group = ev["group"].strip("`")

        # surface required on all events
        if "surface" not in props:
            errors.append(f'Event "{name}" missing standard property `surface`')

        # acting_as required on hiring events
        if (
            "hiring" in area
            and "acting_as" not in props
            and name not in acting_as_exceptions
        ):
            errors.append(
                f'Hiring event "{name}" missing standard property `acting_as`'
            )

        # job_id required on job-grouped events
        if group == "job" and "job_id" not in props:
            warnings.append(
                f'Job-grouped event "{name}" missing `job_id` '
                f"(may be intentional for creation flow)"
            )

        # referrer_user_id required on viral loop events
        if "viral" in area and "referrer_user_id" not in props:
            errors.append(
                f'Viral loop event "{name}" missing standard property `referrer_user_id`'
            )

    return errors, warnings


def tp_rule_06(tp_intent_outcome, tp_events, catalog_events):
    """All events in Intent vs Outcome table must exist in catalog or tracking plan."""
    errors, warnings = [], []
    all_known = set(catalog_events.keys()) | set(tp_events.keys())
    for flow in tp_intent_outcome:
        for role in ("intent", "success", "failure"):
            ev = flow[role]
            if ev == "--" or not ev:
                continue
            if ev not in all_known:
                errors.append(
                    f'Intent vs Outcome: "{ev}" ({role} for '
                    f'"{flow["flow"]}") not found in catalog or tracking plan'
                )
    return errors, warnings


def tp_rule_07(tp_events, schema_objects):
    """Event object prefix must match a recognized Standard Object."""
    errors, warnings = [], []
    for name in tp_events:
        obj = _object_prefix(name, schema_objects)
        if not obj and name.endswith("Button Clicked"):
            obj = _object_for_intent_event(name, schema_objects)
        if not obj and not name.endswith("Button Clicked"):
            errors.append(
                f'Event "{name}" uses an object prefix not in Standard Objects table'
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


# ── Logging ──────────────────────────────────────────────────────────────────

LOG_HEADER = (
    "# Helix Analytics Docs — Validation Log\n\n"
    "Auto-generated by `scripts/validate-analytics-docs.py`.  \n"
    "Each run validates consistency across the 3 Helix analytics documents.\n\n"
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


def write_log(all_errors, all_warnings, suppressed_count=0, mode_label=None, rule_names=None):
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

    if LOG_PATH.exists():
        existing = LOG_PATH.read_text()
    else:
        existing = LOG_HEADER

    parts = re.split(r"(?=\n---\n\n## Run:)", existing)
    header = parts[0]
    runs = parts[1:] if len(parts) > 1 else []
    runs.append(new_entry)
    if len(runs) > MAX_LOG_RUNS:
        runs = runs[-MAX_LOG_RUNS:]
    LOG_PATH.write_text(header + "".join(runs) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def _run_rules(rules, known, rule_names, mode_label=None):
    """Run a list of (rule_id, fn, args) rules, suppress known warnings, log, and exit."""
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

    write_log(all_errors, all_warnings, suppressed, mode_label=mode_label, rule_names=rule_names)

    ec = sum(len(e) for e in all_errors.values())
    wc = sum(len(w) for w in all_warnings.values())

    if ec == 0 and wc == 0:
        msg = f"All clear — {len(rule_names)} validation rules passed."
        if suppressed:
            msg += f" ({suppressed} known warnings suppressed)"
        print(msg)
        print(f"Log: {LOG_PATH.relative_to(REPO_ROOT)}")
        sys.exit(0)

    if ec:
        print(f"\n--- ERRORS ({ec}) ---")
        for rid in sorted(all_errors, key=str):
            for e in all_errors[rid]:
                print(f"  [Rule {rid}: {rule_names[rid]}] {e}")

    if wc:
        print(f"\n--- WARNINGS ({wc}) ---")
        for rid in sorted(all_warnings, key=str):
            for w in all_warnings[rid]:
                print(f"  [Rule {rid}: {rule_names[rid]}] {w}")

    if suppressed:
        print(f"\n({suppressed} known warnings suppressed)")

    print(f"\nLog updated: {LOG_PATH.relative_to(REPO_ROOT)}")
    sys.exit(1 if ec else 0)


def validate_catalog():
    """Validate consistency across the 3 source-of-truth docs."""
    for p in (CATALOG_PATH, SCHEMA_PATH, DASHBOARD_PATH):
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(2)

    catalog_events, prop_dict, dup_events = parse_catalog(CATALOG_PATH)
    schema_objects, schema_person, schema_evt_props, schema_io = parse_schema(
        SCHEMA_PATH
    )
    funnels, dash_ph, dash_props = parse_dashboards(DASHBOARD_PATH)

    if not catalog_events:
        print("ERROR: No events parsed from catalog", file=sys.stderr)
        sys.exit(2)

    known = load_known_warnings(LOG_PATH)

    rules = [
        (1, rule_01, (catalog_events, schema_objects)),
        (2, rule_02, (schema_io, catalog_events)),
        (3, rule_03, (schema_person, catalog_events)),
        (4, rule_04, (catalog_events, schema_evt_props)),
        (5, rule_05, (funnels, catalog_events)),
        (6, rule_06, (funnels, catalog_events)),
        (7, rule_07, (dash_props, prop_dict)),
        (8, rule_08, (dash_props, prop_dict)),
        (9, rule_09, (dash_ph, schema_io)),
        (10, rule_10, (catalog_events, prop_dict)),
        (11, rule_11, (catalog_events, prop_dict)),
        (12, rule_12, (catalog_events, prop_dict)),
        (13, rule_13, (catalog_events, prop_dict)),
        (14, rule_14, (dup_events, prop_dict)),
    ]

    _run_rules(rules, known, RULE_NAMES)


def validate_tracking_plan(tp_path):
    """Validate a tracking plan against catalog and schema context."""
    if not tp_path.exists():
        print(f"ERROR: Tracking plan not found: {tp_path}", file=sys.stderr)
        sys.exit(2)

    for p in (CATALOG_PATH, SCHEMA_PATH):
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(2)

    catalog_events, prop_dict, _ = parse_catalog(CATALOG_PATH)
    schema_objects, _, schema_evt_props, _ = parse_schema(SCHEMA_PATH)
    tp_events, tp_io, tp_funnels, tp_prop_dict = parse_tracking_plan(tp_path)

    if not tp_events:
        print("ERROR: No events parsed from tracking plan", file=sys.stderr)
        sys.exit(2)

    known = load_known_warnings(LOG_PATH)
    plan_name = tp_path.stem

    rules = [
        ("TP1", tp_rule_01, (tp_events,)),
        ("TP2", tp_rule_02, (tp_events, tp_prop_dict)),
        ("TP3", tp_rule_03, (tp_events, catalog_events)),
        ("TP4", tp_rule_04, (tp_events, prop_dict, tp_prop_dict)),
        ("TP5", tp_rule_05, (tp_events, schema_evt_props)),
        ("TP6", tp_rule_06, (tp_io, tp_events, catalog_events)),
        ("TP7", tp_rule_07, (tp_events, schema_objects)),
        ("TP8", tp_rule_08, (tp_funnels, tp_events, catalog_events)),
        ("TP9", tp_rule_09, (tp_events, prop_dict)),
    ]

    _run_rules(rules, known, TP_RULE_NAMES, mode_label=f"Tracking Plan: {plan_name}")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        candidate = Path(arg)
        if not candidate.exists():
            candidate = REPO_ROOT / "tracking-plans" / f"{arg}.md"
        if not candidate.exists():
            candidate = REPO_ROOT / "tracking-plans" / arg
        if not candidate.exists():
            candidate = REPO_ROOT / arg
        validate_tracking_plan(candidate)
    else:
        validate_catalog()


if __name__ == "__main__":
    main()
