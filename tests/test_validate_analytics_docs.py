import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-analytics-docs.py"

spec = importlib.util.spec_from_file_location("validate_analytics_docs", SCRIPT_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write_tmp_md(body):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tmp.write(body)
    tmp.close()
    return Path(tmp.name)


def run_removal_safety(path, product="helix"):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--product",
            product,
            "--check-removal-safety",
            str(path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def stdout_without_banner(result):
    lines = result.stdout.splitlines()
    if lines and lines[0].startswith("Validating product: "):
        return "\n".join(lines[1:]) + ("\n" if len(lines) > 1 else "")
    return result.stdout


class TrackingPlanObjectValidationTests(unittest.TestCase):
    def test_extract_object(self):
        self.assertEqual(
            validator._extract_object("Job Wizard Step Completed"),
            "Job Wizard Step",
        )
        self.assertIsNone(validator._extract_object("Created"))

    def test_exact_match_and_short_prefix_rejection(self):
        events = {
            "Job Wizard Step Completed": {},
            "Job Post Created": {},
        }
        schema = {"Job": {}, "Job Wizard Step": {}}
        errors, warnings = validator.tp_rule_07(events, schema)
        self.assertFalse(warnings)
        self.assertEqual(len(errors), 1)
        self.assertIn('object "Job Post"', errors[0])

    def test_strict_rule_rejects_longest_prefix_match(self):
        errors, _ = validator.tp_rule_07({"Foo Bar Created": {}}, {"Foo": {}})
        self.assertEqual(len(errors), 1)
        self.assertIn('object "Foo Bar"', errors[0])

    def test_button_clicked_has_no_tp_carveout(self):
        errors, _ = validator.tp_rule_07({"Proceed Button Clicked": {}}, {})
        self.assertEqual(len(errors), 1)
        self.assertIn('object "Proceed Button"', errors[0])

    def test_declared_new_object_allows_event(self):
        errors, _ = validator.tp_rule_07(
            {"Sam Session Started": {}},
            {},
            {"Sam Session": {"entity": "Sam", "example_events": []}},
            {},
        )
        self.assertEqual(errors, [])

        errors, _ = validator.tp_rule_07({"Sam Session Started": {}}, {})
        self.assertEqual(len(errors), 1)
        self.assertIn('object "Sam Session"', errors[0])

    def test_removed_object_precedes_schema_membership(self):
        errors, _ = validator.tp_rule_07(
            {"Sam Session Started": {}},
            {"Sam Session": {}},
            {},
            {"Sam Session": {"reason": ""}},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("## Removed Standard Objects", errors[0])

    def test_single_word_event_errors(self):
        errors, _ = validator.tp_rule_07({"Created": {}}, {})
        self.assertEqual(
            errors,
            ['Event "Created": Event name must follow Object-Action format'],
        )


class DeclarationValidationTests(unittest.TestCase):
    def test_duplicate_addition_warns(self):
        errors, warnings = validator.validate_object_declarations(
            {"Job": {"entity": "Job", "example_events": []}},
            {},
            {"Job": {}},
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("already exists", warnings[0])

    def test_contradiction_errors_and_cascades_to_removed_event(self):
        added = {"Foo Bar": {"entity": "Foo", "example_events": []}}
        removed = {"Foo Bar": {"reason": ""}}
        declaration_errors, _ = validator.validate_object_declarations(
            added, removed, {}
        )
        event_errors, _ = validator.tp_rule_07(
            {"Foo Bar Created": {}}, {}, added, removed
        )
        self.assertEqual(len(declaration_errors), 1)
        self.assertIn("both ## New Standard Objects", declaration_errors[0])
        self.assertEqual(len(event_errors), 1)
        self.assertIn("## Removed Standard Objects", event_errors[0])

    def test_noop_removal_warns(self):
        errors, warnings = validator.validate_object_declarations(
            {}, {"Foo Bar": {"reason": ""}}, {}
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("Removal has no effect", warnings[0])

    def test_new_standard_objects_empty_object_cell_errors(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects
| Object | Entity | Example Events |
|---|---|---|
|  | Entity | Event Created |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertIn("empty Object cell", data.declaration_errors[0])
        self.assertIn("New Standard Objects", data.declaration_errors[0])

    def test_removed_standard_objects_header_and_empty_cell_errors(self):
        malformed_path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Reason |
|---|
| cleanup |
"""
        )
        empty_path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object | Reason |
|---|---|
|  | cleanup |
"""
        )
        self.addCleanup(malformed_path.unlink)
        self.addCleanup(empty_path.unlink)

        malformed = validator.parse_tracking_plan(malformed_path)
        empty = validator.parse_tracking_plan(empty_path)

        self.assertIn("Removed Standard Objects", malformed.declaration_errors[0])
        self.assertIn("must use columns", malformed.declaration_errors[0])
        self.assertIn("empty Object cell", empty.declaration_errors[0])
        self.assertIn("Removed Standard Objects", empty.declaration_errors[0])

    def test_removed_reason_column_is_optional(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Voice Session |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(data.declaration_errors, [])
        self.assertEqual(data.removed_objects["Voice Session"]["reason"], "")

    def test_empty_sections_and_malformed_content(self):
        bare = write_tmp_md(
            """# Test

## New Standard Objects

## New Events
"""
        )
        zero_rows = write_tmp_md(
            """# Test

## New Standard Objects
| Object | Entity | Example Events |
|---|---|---|

## New Events
"""
        )
        paragraph = write_tmp_md(
            """# Test

## New Standard Objects

This should be a table.
"""
        )
        duplicate = write_tmp_md(
            """# Test

## New Standard Objects

## New Standard Objects
"""
        )
        for path in (bare, zero_rows, paragraph, duplicate):
            self.addCleanup(path.unlink)

        self.assertEqual(validator.parse_tracking_plan(bare).declaration_errors, [])
        self.assertEqual(
            validator.parse_tracking_plan(zero_rows).declaration_errors, []
        )
        self.assertIn(
            "must use columns",
            validator.parse_tracking_plan(paragraph).declaration_errors[0],
        )
        self.assertIn(
            "appears more than once",
            validator.parse_tracking_plan(duplicate).declaration_errors[0],
        )

    def test_duplicate_object_in_section_errors(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects
| Object | Entity | Example Events |
|---|---|---|
| Sam Session | Sam | Sam Session Started |
| Sam Session | User | Sam Session Ended |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.declaration_errors), 1)
        self.assertIn("more than once", data.declaration_errors[0])
        self.assertIn("Sam Session", data.declaration_errors[0])
        # First declaration is preserved, duplicate is skipped
        self.assertEqual(data.added_objects["Sam Session"]["entity"], "Sam")

    def test_commented_template_sections_are_ignored(self):
        path = write_tmp_md(
            """# Test

<!--
## New Standard Objects

Template helper text.

| Object | Entity | Example Events |
|---|---|---|
| [Object Name] | [Entity represented] | [Object Action] |

## Removed Standard Objects

| Object | Reason |
|---|---|
| [Object Name] | [Why it is removed] |
-->
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(data.declaration_errors, [])
        self.assertEqual(data.added_objects, {})
        self.assertEqual(data.removed_objects, {})


class RemovalSafetySubcommandTests(unittest.TestCase):
    def test_happy_path_no_catalog_references(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Object With No References |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stdout_without_banner(result), "")

    def test_blocking_path_outputs_blocking_events(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Auth |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Auth blocks: Auth Login Succeeded", stdout_without_banner(result))
        self.assertEqual(result.stderr, "")

    def test_no_removed_section_is_noop(self):
        path = write_tmp_md("# Test\n")
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stdout_without_banner(result), "")

    def test_missing_file_reports_stderr_only(self):
        fd, tmp_path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        missing = Path(tmp_path)
        missing.unlink()
        result = run_removal_safety(missing)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(stdout_without_banner(result), "")
        self.assertIn("Tracking plan not found", result.stderr)

    def test_parse_error_reports_stderr_only(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects
| Object | Entity |
|---|---|
| Foo | Entity |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(stdout_without_banner(result), "")
        self.assertIn("New Standard Objects", result.stderr)
        self.assertIn("must use columns", result.stderr)

    def test_partial_blocking_outputs_only_blocking_object(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Auth |
| Object With No References |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 1)
        stdout = stdout_without_banner(result)
        self.assertIn("Auth blocks:", stdout)
        self.assertNotIn("Object With No References blocks:", stdout)


class ProductCatalogParserTests(unittest.TestCase):
    def test_event_catalog_slice_excludes_property_dictionary_and_removed_events(self):
        path = write_tmp_md(
            """# Test

## Event Catalog

### Account Events

| Event | Area | Type | Trigger | Source | Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|
| Account Created | Account | Success | Created | Frontend | `account_id` | -- | -- | Live |

## Property Dictionary

### Enum Properties

| Property | Type | Description | Values | Used In |
|---|---|---|---|---|
| Fake Removed Event | Area | Type | Trigger | Source |

## Removed Events

| Event | Area | Type | Trigger | Source | Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|
| Removed Event | Account | Success | Old | Frontend | -- | -- | -- | Removed |
"""
        )
        self.addCleanup(path.unlink)
        events, prop_dict, _ = validator.parse_catalog(path)
        self.assertEqual(set(events), {"Account Created"})
        self.assertIn("Fake", prop_dict)

    def test_shared_event_types_override_product_fallback(self):
        product = write_tmp_md(
            """# Product

## Event Types
| Type | Meaning |
|---|---|
| `ProductOnly` | Product fallback |
"""
        )
        shared = write_tmp_md(
            """# Shared

## Event Types
| Type | Meaning |
|---|---|
| `SharedOnly` | Shared source |
"""
        )
        self.addCleanup(product.unlink)
        self.addCleanup(shared.unlink)

        *_, product_types = validator.parse_schema(product)
        *_, shared_types = validator.parse_schema(product, shared)

        self.assertEqual(product_types, {"ProductOnly"})
        self.assertEqual(shared_types, {"SharedOnly"})


class ProductConfigTests(unittest.TestCase):
    def test_parse_supported_frontmatter_config(self):
        path = write_tmp_md(
            """---
confluence:
  page_id: "123"
analytics_platform: posthog
allow_empty_catalog: true
group_property_rules:
  - group: job
    property: job_id
    catalog_warning_types: [Interaction, Rejected]
    tracking_plan_severity: warning
area_property_rules:
  - area_contains: viral
    property: referrer_user_id
persona_rules:
  - section_contains: hiring
    property: acting_as
    applies_if_in_schema: true
---

# Schema
"""
        )
        self.addCleanup(path.unlink)
        config = validator.parse_product_config(path)
        self.assertEqual(config.analytics_platform, "posthog")
        self.assertTrue(config.allow_empty_catalog)
        self.assertEqual(config.group_property_rules[0]["group"], "job")
        self.assertEqual(
            config.group_property_rules[0]["catalog_warning_types"],
            ["Interaction", "Rejected"],
        )
        self.assertTrue(config.persona_rules[0]["applies_if_in_schema"])

    def test_config_rejects_bad_boolean_and_unknown_rule_field(self):
        bad_bool = write_tmp_md(
            """---
allow_empty_catalog: yes
---
"""
        )
        bad_field = write_tmp_md(
            """---
group_property_rules:
  - group: job
    property: job_id
    surprise: nope
---
"""
        )
        self.addCleanup(bad_bool.unlink)
        self.addCleanup(bad_field.unlink)

        with self.assertRaisesRegex(ValueError, "allow_empty_catalog"):
            validator.parse_product_config(bad_bool)
        with self.assertRaisesRegex(ValueError, "Unsupported field"):
            validator.parse_product_config(bad_field)

    def test_no_config_product_specific_rules_emit_no_findings(self):
        event = {
            "Job Created": {
                "section": "Hiring Events",
                "properties": [],
                "group": "job",
                "type": "Success",
                "area": "Viral Loop",
            }
        }
        errors, warnings = validator.rule_04(event, {"acting_as": {"when": ""}}, validator.ProductConfig())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        tp_errors, tp_warnings = validator.tp_rule_05(event, {}, validator.ProductConfig())
        self.assertEqual(tp_errors, [])
        self.assertEqual(tp_warnings, [])

    def test_area_property_rule_severity_warning_is_honored(self):
        config = validator.ProductConfig(
            area_property_rules=[
                {
                    "area_contains": "viral",
                    "property": "referrer_user_id",
                    "severity": "warning",
                }
            ]
        )
        event = {
            "Custom Link Shared": {
                "section": "Prospect Events",
                "properties": [],
                "group": "--",
                "type": "Success",
                "area": "Viral Loop",
            }
        }

        errors, warnings = validator.rule_04(event, {}, config)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("referrer_user_id", warnings[0])

        tp_errors, tp_warnings = validator.tp_rule_05(event, {}, config)
        self.assertEqual(tp_errors, [])
        self.assertEqual(len(tp_warnings), 1)
        self.assertIn("referrer_user_id", tp_warnings[0])


class ProductCliTests(unittest.TestCase):
    def run_script(self, *args):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_product_is_required(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("--product", result.stderr)

    def test_bogus_product_lists_discovered_products(self):
        result = self.run_script("--product", "bogus")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Discovered products", result.stderr)
        self.assertIn("helix", result.stderr)

    def test_product_paths_resolves_helix_namespaced_paths(self):
        paths = validator.product_paths("helix")
        self.assertEqual(paths.catalog_path, REPO_ROOT / "docs" / "helix" / "event-catalog.md")
        self.assertEqual(paths.schema_path, REPO_ROOT / "docs" / "helix" / "event-schema.md")
        self.assertEqual(paths.dashboard_path, REPO_ROOT / "docs" / "helix" / "dashboards.md")
        self.assertEqual(paths.shared_event_types_path, REPO_ROOT / "docs" / "shared" / "naming-and-event-types.md")
        self.assertEqual(paths.tracking_plans_dir, REPO_ROOT / "tracking-plans" / "helix")
        self.assertEqual(paths.log_path, REPO_ROOT / "logs" / "helix" / "conflicts-log.md")

    def test_recruit_empty_scaffold_validates(self):
        result = self.run_script("--product", "recruit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All clear", result.stdout)


class ObjectDeclarationProseTests(unittest.TestCase):
    """Prose before the declaration table should not cause errors."""

    def test_prose_before_new_standard_objects_table(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects

Use this section when new events introduce an object that is not yet in
docs/helix/event-schema.md.

| Object | Entity | Example Events |
|---|---|---|
| Sam Session | Sam | Sam Session Started |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(data.declaration_errors, [])
        self.assertIn("Sam Session", data.added_objects)
        self.assertEqual(data.added_objects["Sam Session"]["entity"], "Sam")

    def test_placeholder_rows_are_skipped(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects

Use this section when new events introduce an object.

| Object | Entity | Example Events |
|---|---|---|
| [Object Name] | [Entity represented] | [Object Action], [Object Action] |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(data.declaration_errors, [])
        self.assertEqual(data.added_objects, {})

    def test_prose_before_removed_standard_objects_table(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects

Objects removed by this plan.

| Object | Reason |
|---|---|
| Voice Session | Deprecated |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(data.declaration_errors, [])
        self.assertIn("Voice Session", data.removed_objects)

    def test_malformed_table_after_prose_still_errors(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects

Some explanation text.

| Object | Entity |
|---|---|
| Foo | Bar |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.declaration_errors), 1)
        self.assertIn("must use columns", data.declaration_errors[0])

    def test_prose_only_new_standard_objects_errors(self):
        path = write_tmp_md(
            """# Test

## New Standard Objects

Voice Session should be added as a new object.
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.declaration_errors), 1)
        self.assertIn("must use columns", data.declaration_errors[0])

    def test_prose_only_removed_standard_objects_errors(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects

Remove Voice Session because it is deprecated.
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.declaration_errors), 1)
        self.assertIn("must use columns", data.declaration_errors[0])


class FunnelParserScopingTests(unittest.TestCase):
    """New per-funnel step tables should only be parsed inside ## Funnels."""

    def test_step_tables_inside_funnels_section_are_parsed(self):
        path = write_tmp_md(
            """# Test

## New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Account Create Succeeded | Account | Success | Backend | Account created | New user | `auth_method` | -- | -- | Not Started |

## Funnels

### Signup Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | `current_page_context` = `auth_signup` |
| 2 | Login Started | — |
| 3 | Account Create Succeeded | — |

### Auth Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Login Started | — |
| 2 | Auth Login Succeeded | — |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.funnels), 2)
        self.assertIn("Signup Funnel", data.funnels)
        self.assertIn("Auth Funnel", data.funnels)
        self.assertEqual(
            data.funnels["Signup Funnel"],
            ["Page Viewed", "Login Started", "Account Create Succeeded"],
        )

    def test_step_event_table_outside_funnels_section_is_ignored(self):
        path = write_tmp_md(
            """# Test

## New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Account Create Succeeded | Account | Success | Backend | Account created | New user | `auth_method` | -- | -- | Not Started |

## Implementation Notes

### Migration Steps

| Step | Event | Action |
|---|---|---|
| 1 | Account Created | Rename to Account Create Succeeded |
| 2 | Auth Login Failed | Rename to Auth Login Rejected |

## Funnels

### Signup Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | — |
| 2 | Account Create Succeeded | — |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.funnels), 1)
        self.assertIn("Signup Funnel", data.funnels)
        self.assertNotIn("Migration Steps", data.funnels)

    def test_old_flat_funnel_format_still_works(self):
        path = write_tmp_md(
            """# Test

## New Events Summary

| Event | Area | Type | Source | Trigger | Context | Key Properties | Group | Property Updates | Status |
|---|---|---|---|---|---|---|---|---|---|
| Foo Created | Account | Success | Backend | Created | New | `id` | -- | -- | Not Started |

## Funnels

| Funnel Name | Steps | Purpose |
|---|---|---|
| Signup | Page Viewed → Login Started → Foo Created | Measures signup |
"""
        )
        self.addCleanup(path.unlink)
        data = validator.parse_tracking_plan(path)
        self.assertEqual(len(data.funnels), 1)
        self.assertEqual(
            data.funnels["Signup"],
            ["Page Viewed", "Login Started", "Foo Created"],
        )


if __name__ == "__main__":
    unittest.main()
