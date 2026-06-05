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


def run_removal_safety(path):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--check-removal-safety",
            str(path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


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
        self.assertEqual(result.stdout, "")

    def test_blocking_path_outputs_blocking_events(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Voice Session |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Voice Session blocks: Voice Session Started", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_no_removed_section_is_noop(self):
        path = write_tmp_md("# Test\n")
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_missing_file_reports_stderr_only(self):
        fd, tmp_path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        missing = Path(tmp_path)
        missing.unlink()
        result = run_removal_safety(missing)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
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
        self.assertEqual(result.stdout, "")
        self.assertIn("New Standard Objects", result.stderr)
        self.assertIn("must use columns", result.stderr)

    def test_partial_blocking_outputs_only_blocking_object(self):
        path = write_tmp_md(
            """# Test

## Removed Standard Objects
| Object |
|---|
| Voice Session |
| Object With No References |
"""
        )
        self.addCleanup(path.unlink)
        result = run_removal_safety(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Voice Session blocks:", result.stdout)
        self.assertNotIn("Object With No References blocks:", result.stdout)


if __name__ == "__main__":
    unittest.main()
