"""Unit tests for the object–action segregation logic in the analytics validator.

The validator script has a dash in its filename, so it is loaded by path via
importlib rather than imported normally.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate-analytics-docs.py"
_spec = importlib.util.spec_from_file_location("validate_analytics_docs", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

# Representative Standard Objects, including nested prefixes to exercise
# longest-prefix and exact-equality matching.
OBJECTS = {
    "Job",
    "Job Wizard",
    "Job Wizard Step",
    "Auth",
    "Interest",
    "Review",
    "Chat",
    "Team Member",
    "Page",
    "Account",
}

ALLOWED_EVENT_TYPES = {"View", "Interaction", "Started", "Success", "Rejected", "Error"}


class ObjectPrefixTests(unittest.TestCase):
    def test_exact_equality(self):
        self.assertEqual(mod._object_prefix("Job Wizard Step", OBJECTS), "Job Wizard Step")

    def test_longest_prefix_wins(self):
        self.assertEqual(
            mod._object_prefix("Job Wizard Step Completed", OBJECTS), "Job Wizard Step"
        )

    def test_unknown_prefix(self):
        self.assertIsNone(mod._object_prefix("Fnord Created", OBJECTS))


class SplitObjectActionTests(unittest.TestCase):
    def test_simple_past_tense(self):
        self.assertEqual(mod._split_object_action("Job Published", OBJECTS), ("Job", "Published"))

    def test_result_event(self):
        self.assertEqual(
            mod._split_object_action("Job Publish Rejected", OBJECTS), ("Job", "Publish Rejected")
        )

    def test_multiword_action(self):
        self.assertEqual(
            mod._split_object_action("Auth Session Restore Succeeded", OBJECTS),
            ("Auth", "Session Restore Succeeded"),
        )

    def test_exact_object_empty_action(self):
        self.assertEqual(
            mod._split_object_action("Job Wizard Step", OBJECTS), ("Job Wizard Step", "")
        )

    def test_unknown_prefix(self):
        self.assertEqual(mod._split_object_action("Fnord Bar", OBJECTS), (None, None))


class CandidateObjectTests(unittest.TestCase):
    def test_result_terminal_drops_two(self):
        self.assertEqual(mod._candidate_object("Pipeline Publish Rejected"), "Pipeline")

    def test_variant_terminal_also_drops_two(self):
        self.assertEqual(mod._candidate_object("Pipeline Publish Error"), "Pipeline")

    def test_plain_event_drops_one(self):
        self.assertEqual(mod._candidate_object("Pipeline Created"), "Pipeline")

    def test_too_short_returns_none(self):
        self.assertIsNone(mod._candidate_object("Publish Rejected"))


class ActionErrorsTests(unittest.TestCase):
    def test_passes_valid_actions(self):
        names = [
            "Review Decision Made",   # irregular past
            "Interest Withdrawn",     # irregular past
            "Job Publish Errored",    # canonical result terminal
            "Share Button Clicked",   # interaction event, skipped
        ]
        self.assertEqual(mod._action_errors(names, OBJECTS), [])

    def test_flags_non_past_tense(self):
        errs = mod._action_errors(["Chat WebSocket Abnormal Close"], OBJECTS)
        self.assertEqual(len(errs), 1)
        self.assertIn("Chat WebSocket Abnormal Close", errs[0])

    def test_flags_garbage_action(self):
        self.assertEqual(len(mod._action_errors(["Job Fnord Xyz"], OBJECTS)), 1)

    def test_flags_only_object(self):
        errs = mod._action_errors(["Job Wizard Step"], OBJECTS)
        self.assertEqual(len(errs), 1)
        self.assertIn("only an object", errs[0])

    def test_skips_variant_terminal(self):
        # Variant result terminals are deferred to Rule 16, not flagged here.
        self.assertEqual(mod._action_errors(["Job Publish Success"], OBJECTS), [])

    def test_skips_unknown_object(self):
        # Unknown object prefix is owned by Rule 1 / TP7, not here.
        self.assertEqual(mod._action_errors(["Fnord Bar"], OBJECTS), [])


class ResultTerminalTests(unittest.TestCase):
    def test_success_wrong_terminal(self):
        errs = mod._result_terminal_errors([("Job Created", "Success")])
        self.assertEqual(len(errs), 1)
        self.assertIn("does not end in", errs[0])

    def test_success_correct(self):
        self.assertEqual(
            mod._result_terminal_errors([("Job Create Succeeded", "Success")]), []
        )

    def test_rejected_correct(self):
        self.assertEqual(
            mod._result_terminal_errors([("Job Share Rejected", "Rejected")]),
            [],
        )

    def test_failed_variant_points_to_rejected(self):
        errs = mod._result_terminal_errors([("Job Share Failed", "Rejected")])
        self.assertEqual(len(errs), 1)
        self.assertIn("Rejected", errs[0])
        self.assertIn("Failed", errs[0])

    def test_started_correct(self):
        self.assertEqual(
            mod._result_terminal_errors([("Job Post Wizard Started", "Started")]),
            [],
        )

    def test_started_wrong_terminal(self):
        errs = mod._result_terminal_errors([("Job Post Wizard Opened", "Started")])
        self.assertEqual(len(errs), 1)
        self.assertIn("Started", errs[0])

    def test_error_variant_terminal(self):
        errs = mod._result_terminal_errors([("Chat WebSocket Error", "Error")])
        self.assertEqual(len(errs), 1)
        self.assertIn("Errored", errs[0])

    def test_error_correct(self):
        self.assertEqual(
            mod._result_terminal_errors([("Chat WebSocket Errored", "Error")]), []
        )

    def test_variant_is_type_independent(self):
        errs = mod._result_terminal_errors([("Job Publish Success", None)])
        self.assertEqual(len(errs), 1)
        self.assertIn("Succeeded", errs[0])

    def test_one_message_per_event(self):
        # Variant check and type check both apply; only one message is emitted.
        errs = mod._result_terminal_errors([("Job Publish Success", "Success")])
        self.assertEqual(len(errs), 1)


class EventTypeTests(unittest.TestCase):
    def test_invalid_types_flagged(self):
        typed = [
            ("A B", "--"),
            ("C D", "user_action"),
            ("E F", "page_view"),
            ("G H", ""),
            ("I J", "Intent"),
            ("K L", "Failure"),
            ("M N", "Lifecycle"),
            ("O P", "Navigation"),
            ("Q R", "State Change"),
        ]
        self.assertEqual(len(mod._event_type_errors(typed, ALLOWED_EVENT_TYPES)), 9)

    def test_all_enum_members_pass(self):
        typed = [(f"Obj{i} Acted", t) for i, t in enumerate(sorted(ALLOWED_EVENT_TYPES))]
        self.assertEqual(mod._event_type_errors(typed, ALLOWED_EVENT_TYPES), [])

    def test_none_type_skipped(self):
        self.assertEqual(mod._event_type_errors([("A B", None)], ALLOWED_EVENT_TYPES), [])

    def test_rule_17_missing_table_does_not_use_duplicate_fallback(self):
        catalog = {"Job Created": {"type": "--"}}
        errs, warns = mod.rule_17(catalog, set())
        self.assertEqual(warns, [])
        self.assertEqual(len(errs), 1)
        self.assertIn("Event Types table not found", errs[0])


class ResultPatternParserTests(unittest.TestCase):
    NEW_TABLE = """## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Sharing | Share Button Clicked | Job Share Succeeded | Job Share Rejected | Chat WebSocket Errored |
"""

    OLD_TABLE = """## Intent vs Outcome

| Flow | Intent Event | Success Event | Failure Event |
|---|---|---|---|
| Sharing | Share Button Clicked | Job Shared | Job Share Failed |
"""

    def test_new_result_pattern_shape_parses(self):
        rows, errors = mod._parse_result_pattern_table(
            mod.parse_tables(self.NEW_TABLE),
            "test",
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["interaction_started"], "Share Button Clicked")
        self.assertEqual(rows[0]["success"], "Job Share Succeeded")
        self.assertEqual(rows[0]["rejected"], "Job Share Rejected")
        self.assertEqual(rows[0]["error"], "Chat WebSocket Errored")

    def test_old_result_pattern_shape_rejected(self):
        rows, errors = mod._parse_result_pattern_table(
            mod.parse_tables(self.OLD_TABLE),
            "test",
        )
        self.assertEqual(rows, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("Intent vs Outcome", errors[0])

    def test_platform_health_uses_new_columns(self):
        text = """### Platform Health Dashboard

| Flow | Interaction / Started Event | Success Event | Rejected Event |
|---|---|---|---|
| Sharing | Share Button Clicked | Job Share Succeeded | Job Share Rejected |
"""
        rows, errors = mod._parse_platform_health_table(mod.parse_tables(text))
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rejected"], "Job Share Rejected")

    def test_rule_09_compares_new_keys(self):
        row = {
            "flow": "Sharing",
            "interaction_started": "Share Button Clicked",
            "success": "Job Share Succeeded",
            "rejected": "Job Share Rejected",
            "error": "--",
        }
        errors, warnings = mod.rule_09([row], [], [row])
        self.assertEqual(warnings, [])
        self.assertEqual(errors, [])


class ParseTrackingPlanTests(unittest.TestCase):
    NEW_FORMAT = """# Tracking Plan: Test

## New Events

| Event | Area | Type | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Job Created | Hiring | Success | server confirms | `job_id`, `surface` | `job` | -- |
"""

    # No Type column, plus an extra Source column between Trigger and Key
    # Properties — the real-world shape of hm-job-creation-wizard-v2.md.
    OLD_FORMAT = """# Tracking Plan: Test

## New Events

| Event | Area | Trigger | Source | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Job Created | Hiring | server confirms | Backend | `job_id`, `surface` | `job` | -- |
"""

    def _parse(self, body):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(body)
            path = Path(f.name)
        try:
            return mod.parse_tracking_plan(path)
        finally:
            path.unlink()

    def test_new_format_populates_type(self):
        events = self._parse(self.NEW_FORMAT).events
        self.assertIn("Job Created", events)
        self.assertEqual(events["Job Created"]["type"], "Success")
        # Header-keyed: properties read from the Key Properties column.
        self.assertIn("job_id", events["Job Created"]["properties"])

    def test_old_format_type_none(self):
        events = self._parse(self.OLD_FORMAT).events
        self.assertIn("Job Created", events)
        self.assertIsNone(events["Job Created"]["type"])
        # Header-keying reads Key Properties correctly despite the extra Source column.
        self.assertIn("job_id", events["Job Created"]["properties"])

    def test_old_format_tp12_missing_column(self):
        events = self._parse(self.OLD_FORMAT).events
        errs, _ = mod.tp_rule_12(events, ALLOWED_EVENT_TYPES)
        self.assertTrue(any('no "Type" column' in e for e in errs))

    def test_new_format_tp12_passes(self):
        events = self._parse(self.NEW_FORMAT).events
        errs, _ = mod.tp_rule_12(events, ALLOWED_EVENT_TYPES)
        self.assertEqual(errs, [])

    def test_event_renames_are_parsed_as_planned_events(self):
        body = """# Tracking Plan: Test

## Event Renames

### Type Reclassification — Started/Success → Interaction

| Current Name | New Name | Old Type | New Type | Constant |
|---|---|---|---|---|
| Login Started | Login Started Button Clicked | Started | Interaction | `LOGIN_STARTED` → `LOGIN_STARTED_BUTTON_CLICKED` |
| [Old Name] | [New Name] | Success | Interaction | `OLD` → `NEW` |

### Success Events — Must End "Succeeded"

| Current Name | New Name | Type | Constant |
|---|---|---|---|
| Account Created | Account Create Succeeded | Success | `ACCOUNT_CREATED` → `ACCOUNT_CREATE_SUCCEEDED` |

### Rejected Events — Must End "Rejected"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Login Failed | Auth Login Rejected | Rejected | User-caused |

### Error Events — Must End "Errored"

| Current Name | New Name | Type | Rationale |
|---|---|---|---|
| Auth Refresh Failed | Auth Refresh Errored | Error | System-caused |
"""
        events = self._parse(body).events
        self.assertEqual(events["Login Started Button Clicked"]["type"], "Interaction")
        self.assertEqual(events["Account Create Succeeded"]["type"], "Success")
        self.assertEqual(events["Auth Login Rejected"]["type"], "Rejected")
        self.assertEqual(events["Auth Refresh Errored"]["type"], "Error")
        self.assertEqual(
            events["Account Create Succeeded"]["renamed_from"], "Account Created"
        )
        self.assertNotIn("[New Name]", events)

    def test_renamed_events_satisfy_result_pattern_and_funnel_checks(self):
        body = """# Tracking Plan: Test

## Event Renames

### Type Reclassification — Started/Success → Interaction

| Current Name | New Name | Old Type | New Type | Constant |
|---|---|---|---|---|
| Login Started | Login Started Button Clicked | Started | Interaction | `LOGIN_STARTED` → `LOGIN_STARTED_BUTTON_CLICKED` |

### Success Events — Must End "Succeeded"

| Current Name | New Name | Type | Constant |
|---|---|---|---|
| Account Created | Account Create Succeeded | Success | `ACCOUNT_CREATED` → `ACCOUNT_CREATE_SUCCEEDED` |

## Interaction / Started / Result Pattern

| Flow | Interaction / Started Event | Success Event | Rejected Event | Error Event |
|---|---|---|---|---|
| Login / Signup | Login Started Button Clicked | Account Create Succeeded | -- | -- |

## Funnels

### Signup Funnel

| Step | Event | Filter |
|---|---|---|
| 1 | Page Viewed | — |
| 2 | Login Started Button Clicked | — |
| 3 | Account Create Succeeded | — |
"""
        data = self._parse(body)
        catalog_events = {"Page Viewed": {"section": "Navigation"}}

        result_errors, _ = mod.tp_rule_06(
            data.result_pattern,
            data.result_pattern_errors,
            data.events,
            catalog_events,
        )
        funnel_errors, _ = mod.tp_rule_08(
            data.funnels,
            data.events,
            catalog_events,
        )

        self.assertEqual(result_errors, [])
        self.assertEqual(funnel_errors, [])


if __name__ == "__main__":
    unittest.main()
